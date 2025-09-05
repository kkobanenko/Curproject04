"""
Модуль с задачами для RQ worker
Обработка текста и анализ по критериям
"""

import hashlib
import logging
import unicodedata
import json
import redis
from typing import Dict, Any, List
from datetime import datetime

from config import settings
from database import postgres_manager, clickhouse_manager
from models import Source, Event
from api import OllamaClient

logger = logging.getLogger(__name__)


def save_progress_to_redis(job_id: str, progress_data: Dict[str, Any]) -> None:
    """
    Сохранение промежуточных результатов анализа в Redis
    
    Args:
        job_id: ID задачи
        progress_data: Данные о прогрессе
    """
    try:
        redis_conn = redis.from_url(settings.redis_url)
        key = f"job_progress:{job_id}"
        
        # Сохраняем данные с TTL 1 час
        redis_conn.setex(key, 3600, json.dumps(progress_data, default=str))
        logger.info(f"Прогресс задачи {job_id} сохранен в Redis")
        
    except Exception as e:
        logger.error(f"Ошибка сохранения прогресса в Redis: {e}")


def normalize_text(text: str) -> str:
    """
    Нормализация текста для создания хеша
    
    Args:
        text: Исходный текст
        
    Returns:
        Нормализованный текст
    """
    # Убираем лишние пробелы
    normalized = ' '.join(text.split())
    
    # Приводим к Unicode NFC форме
    normalized = unicodedata.normalize('NFC', normalized)
    
    return normalized


def compute_hash(text: str) -> str:
    """
    Вычисление SHA-256 хеша нормализованного текста
    
    Args:
        text: Исходный текст
        
    Returns:
        SHA-256 хеш в hex формате
    """
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def analyze_text_task(text: str, 
                     source_url: str = None, 
                     source_date: str = None,
                     force_recheck: bool = False,
                     job_id: str = None) -> Dict[str, Any]:
    """
    Основная задача анализа текста
    
    Args:
        text: Текст для анализа
        source_url: URL источника (опционально)
        source_date: Дата источника (опционально)
        force_recheck: Принудительная перепроверка
        job_id: ID задачи для отслеживания прогресса
        
    Returns:
        Результат обработки
    """
    logger.info(f"Начинаем анализ текста (длина: {len(text)} символов)")
    
    try:
        # Вычисляем хеш текста
        source_hash = compute_hash(text)
        logger.info(f"Вычислен хеш: {source_hash}")
        
        # Проверяем существование источника
        existing_source = postgres_manager.get_source_by_hash(source_hash)
        
        # Если источник уже существует и не требуется перепроверка
        if existing_source and not force_recheck:
            logger.info(f"Источник {source_hash} уже существует, пропускаем анализ")
            return {
                'status': 'skipped',
                'source_hash': source_hash,
                'reason': 'already_processed'
            }
        
        # Создаем или обновляем источник
        # Сохраняем первый килобайт текста для возможности просмотра
        text_preview = text[:1024] if text else None
        
        source = Source(
            source_hash=source_hash,
            source_url=source_url,
            source_date=datetime.fromisoformat(source_date) if source_date else None,
            text=text_preview,
            force_recheck=force_recheck
        )
        
        saved_source = postgres_manager.create_source(source)
        logger.info(f"Источник сохранен: {saved_source.id}")
        
        # Получаем активные критерии
        criteria = postgres_manager.get_active_criteria()
        logger.info(f"Найдено {len(criteria)} активных критериев")
        
        if not criteria:
            logger.warning("Нет активных критериев для анализа")
            return {
                'status': 'error',
                'source_hash': source_hash,
                'reason': 'no_active_criteria'
            }
        
        # Инициализируем LLM клиент
        llm_client = OllamaClient(settings.ollama_url)
        
        # Проверяем доступность LLM
        if not llm_client.health_check():
            logger.error("LLM сервис недоступен")
            return {
                'status': 'error',
                'source_hash': source_hash,
                'reason': 'llm_unavailable'
            }
        
        # Анализируем текст по каждому критерию
        events = []
        total_criteria = len(criteria)
        
        for i, criterion in enumerate(criteria):
            logger.info(f"Анализируем по критерию: {criterion.id} ({i+1}/{total_criteria})")
            
            # Сохраняем начальный прогресс
            if job_id:
                progress_data = {
                    'status': 'analyzing',
                    'current_criterion': criterion.id,
                    'criterion_text': criterion.criterion_text,
                    'progress': f"{i+1}/{total_criteria}",
                    'completed_criteria': i,
                    'total_criteria': total_criteria,
                    'timestamp': datetime.utcnow().isoformat()
                }
                save_progress_to_redis(job_id, progress_data)
            
            # Выполняем анализ
            result = llm_client.analyze_text(
                text=text,
                criterion_text=criterion.criterion_text,
                model=settings.ollama_model,
                temperature=settings.temperature,
                top_p=settings.top_p,
                top_k=settings.top_k,
                max_tokens=settings.max_tokens
            )
            
            # Проверяем порог уверенности
            is_match = result.is_match
            if criterion.threshold and result.confidence < criterion.threshold:
                is_match = False
                logger.info(f"Уверенность {result.confidence} ниже порога {criterion.threshold}")
            
            # Сохраняем результат анализа
            if job_id:
                progress_data = {
                    'status': 'analyzing',
                    'current_criterion': criterion.id,
                    'criterion_text': criterion.criterion_text,
                    'progress': f"{i+1}/{total_criteria}",
                    'completed_criteria': i,
                    'total_criteria': total_criteria,
                    'current_result': {
                        'criterion_id': criterion.id,
                        'is_match': is_match,
                        'confidence': result.confidence,
                        'summary': result.summary,
                        'latency_ms': result.latency_ms,
                        'model_name': result.model_name
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                save_progress_to_redis(job_id, progress_data)
            
            # Создаем событие
            logger.info(f"source_date type: {type(source.source_date)}, value: {source.source_date}")
            event = Event(
                source_hash=source_hash,
                source_url=source_url,
                source_date=source.source_date,  # Уже datetime объект
                criterion_id=criterion.id,
                criterion_text=criterion.criterion_text,
                is_match=is_match,
                confidence=result.confidence,
                summary=result.summary,
                model_name=result.model_name,
                latency_ms=result.latency_ms
            )
            logger.info(f"event.source_date type: {type(event.source_date)}, value: {event.source_date}")
            
            # Сохраняем событие в ClickHouse
            if clickhouse_manager.insert_event(event):
                events.append(event)
                logger.info(f"Событие {event.event_id} сохранено")
            else:
                logger.error(f"Ошибка сохранения события {event.event_id}")
        
        # Подсчитываем статистику
        total_events = len(events)
        matches = sum(1 for e in events if e.is_match)
        avg_confidence = sum(e.confidence for e in events) / total_events if total_events > 0 else 0
        
        logger.info(f"Анализ завершен: {matches}/{total_events} совпадений")
        
        return {
            'status': 'success',
            'source_hash': source_hash,
            'total_events': total_events,
            'matches': matches,
            'avg_confidence': avg_confidence,
            'events': [
                {
                    'event_id': str(e.event_id),
                    'criterion_id': e.criterion_id,
                    'is_match': e.is_match,
                    'confidence': e.confidence,
                    'summary': e.summary,
                    'latency_ms': e.latency_ms
                }
                for e in events
            ]
        }
        
    except Exception as e:
        logger.error(f"Ошибка анализа текста: {e}", exc_info=True)
        return {
            'status': 'error',
            'source_hash': source_hash if 'source_hash' in locals() else None,
            'reason': str(e)
        }


def health_check_task() -> Dict[str, Any]:
    """
    Задача проверки здоровья системы
    
    Returns:
        Статус здоровья системы
    """
    try:
        # Проверяем PostgreSQL
        pg_healthy = False
        try:
            with postgres_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    pg_healthy = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
        
        # Проверяем ClickHouse
        ch_healthy = False
        try:
            clickhouse_manager.client.execute("SELECT 1")
            ch_healthy = True
        except Exception as e:
            logger.error(f"ClickHouse health check failed: {e}")
        
        # Проверяем LLM
        llm_healthy = False
        try:
            llm_client = OllamaClient(settings.ollama_url)
            llm_healthy = llm_client.health_check()
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
        
        return {
            'status': 'success',
            'postgres': pg_healthy,
            'clickhouse': ch_healthy,
            'llm': llm_healthy,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'error',
            'reason': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
