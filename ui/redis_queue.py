"""
Модуль для работы с очередями Redis
Отправка задач на анализ текста
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import redis
from rq import Queue

from config import settings

logger = logging.getLogger(__name__)


class QueueManager:
    """Менеджер для работы с очередями Redis"""
    
    def __init__(self):
        """Инициализация подключения к Redis"""
        self.redis_conn = redis.from_url(settings.redis_url)
        self.queue = Queue('text_analysis', connection=self.redis_conn)
    
    def enqueue_text_analysis(self, 
                            text: str, 
                            source_url: Optional[str] = None,
                            source_date: Optional[str] = None,
                            force_recheck: bool = False) -> Dict[str, Any]:
        """
        Постановка задачи анализа текста в очередь
        
        Args:
            text: Текст для анализа
            source_url: URL источника
            source_date: Дата источника
            force_recheck: Принудительная перепроверка
            
        Returns:
            Информация о задаче
        """
        try:
            # Проверяем подключение к Redis
            self.redis_conn.ping()
            
            # Создаем задачу
            job = self.queue.enqueue(
                'tasks.analyze_text_task',
                args=(text, source_url, source_date, force_recheck),
                job_timeout=300,  # 5 минут
                result_ttl=3600,  # 1 час
                failure_ttl=7200  # 2 часа
            )
            
            logger.info(f"Задача {job.id} поставлена в очередь")
            
            return {
                'status': 'enqueued',
                'job_id': job.id,
                'queue_position': len(self.queue),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка постановки задачи в очередь: {e}")
            return {
                'status': 'error',
                'reason': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Получение статуса задачи
        
        Args:
            job_id: ID задачи
            
        Returns:
            Статус задачи
        """
        try:
            job = self.queue.fetch_job(job_id)
            
            if job is None:
                return {
                    'status': 'not_found',
                    'job_id': job_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            result = {
                'job_id': job_id,
                'status': job.get_status(),
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'ended_at': job.ended_at.isoformat() if job.ended_at else None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Добавляем результат если задача завершена
            if job.is_finished:
                result['result'] = job.result
            elif job.is_failed:
                result['error'] = str(job.exc_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса задачи: {e}")
            return {
                'status': 'error',
                'job_id': job_id,
                'reason': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_queue_info(self) -> Dict[str, Any]:
        """
        Получение информации о очереди
        
        Returns:
            Информация о очереди
        """
        try:
            return {
                'queue_name': self.queue.name,
                'queue_length': len(self.queue),
                'workers': len(self.queue.workers),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о очереди: {e}")
            return {
                'status': 'error',
                'reason': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def clear_queue(self) -> Dict[str, Any]:
        """
        Очистка очереди
        
        Returns:
            Результат очистки
        """
        try:
            cleared_jobs = self.queue.empty()
            logger.info(f"Очередь очищена, удалено {cleared_jobs} задач")
            
            return {
                'status': 'cleared',
                'cleared_jobs': cleared_jobs,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Ошибка очистки очереди: {e}")
            return {
                'status': 'error',
                'reason': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_job_progress(self, job_id: str) -> Dict[str, Any]:
        """
        Получение промежуточных результатов выполнения задачи
        
        Args:
            job_id: ID задачи
            
        Returns:
            Данные о прогрессе выполнения
        """
        try:
            # Проверяем подключение к Redis
            self.redis_conn.ping()
            
            # Получаем данные о прогрессе из Redis
            key = f"job_progress:{job_id}"
            progress_data = self.redis_conn.get(key)
            
            if progress_data is None:
                return {
                    'status': 'not_found',
                    'job_id': job_id,
                    'reason': 'no_progress_data',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Парсим JSON данные
            try:
                progress = json.loads(progress_data)
                progress['job_id'] = job_id
                progress['timestamp'] = datetime.utcnow().isoformat()
                return progress
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга данных прогресса: {e}")
                return {
                    'status': 'error',
                    'job_id': job_id,
                    'reason': 'invalid_progress_data',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Ошибка получения прогресса задачи: {e}")
            return {
                'status': 'error',
                'job_id': job_id,
                'reason': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Глобальный экземпляр менеджера очередей
queue_manager = QueueManager()
