"""
Модуль для работы с базами данных
PostgreSQL и ClickHouse
"""

import logging
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from clickhouse_driver import Client
from datetime import datetime
import uuid

from config import settings
from models import Source, Criterion, Event

logger = logging.getLogger(__name__)


class PostgresManager:
    """Менеджер для работы с PostgreSQL"""
    
    def __init__(self):
        """Инициализация подключения к PostgreSQL"""
        self.connection_string = settings.postgres_url
    
    def get_connection(self):
        """Получение соединения с базой данных"""
        return psycopg2.connect(self.connection_string)
    
    def get_source_by_hash(self, source_hash: str) -> Optional[Source]:
        """Получение источника по хешу"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM sources WHERE source_hash = %s",
                    (source_hash,)
                )
                result = cur.fetchone()
                if result:
                    return Source.from_dict(dict(result))
                return None
    
    def create_source(self, source: Source) -> Source:
        """Создание нового источника"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO sources (id, source_hash, source_url, source_date, 
                                       ingest_ts, force_recheck, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_hash) DO UPDATE SET
                        updated_at = NOW(),
                        force_recheck = EXCLUDED.force_recheck
                    RETURNING *
                """, (
                    str(source.id), source.source_hash, source.source_url,
                    source.source_date, source.ingest_ts, source.force_recheck,
                    source.created_at, source.updated_at
                ))
                result = cur.fetchone()
                conn.commit()
                return Source.from_dict(dict(result))
    
    def get_active_criteria(self) -> List[Criterion]:
        """Получение активных критериев"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM criteria WHERE is_active = TRUE")
                results = cur.fetchall()
                return [Criterion.from_dict(dict(row)) for row in results]
    
    def get_criterion_by_id(self, criterion_id: str) -> Optional[Criterion]:
        """Получение критерия по ID"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM criteria WHERE id = %s",
                    (criterion_id,)
                )
                result = cur.fetchone()
                if result:
                    return Criterion.from_dict(dict(result))
                return None


class ClickHouseManager:
    """Менеджер для работы с ClickHouse"""
    
    def __init__(self):
        """Инициализация подключения к ClickHouse"""
        # Извлекаем хост из URL (убираем http:// и порт)
        host = settings.clickhouse_url.replace('http://', '').split(':')[0]
        self.client = Client(
            host=host,
            database=settings.clickhouse_database,
            port=9000
        )
    
    def insert_event(self, event: Event) -> bool:
        """Вставка события в ClickHouse"""
        try:
            data = event.to_dict()
            
            # Преобразуем datetime в строку для ClickHouse
            if data['ingest_ts']:
                data['ingest_ts'] = data['ingest_ts'].isoformat()
            if data['source_date']:
                data['source_date'] = data['source_date'].isoformat()
            if data['created_at']:
                data['created_at'] = data['created_at'].isoformat()
            
            self.client.execute("""
                INSERT INTO events (
                    event_id, source_hash, source_url, source_date, ingest_ts,
                    criterion_id, criterion_text, is_match, confidence, summary,
                    model_name, latency_ms, created_at
                ) VALUES
            """, [(
                data['event_id'], data['source_hash'], data['source_url'],
                data['source_date'], data['ingest_ts'], data['criterion_id'],
                data['criterion_text'], data['is_match'], data['confidence'],
                data['summary'], data['model_name'], data['latency_ms'],
                data['created_at']
            )])
            
            logger.info(f"Событие {event.event_id} сохранено в ClickHouse")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения события в ClickHouse: {e}")
            return False
    
    def get_events_by_source(self, source_hash: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение событий по источнику"""
        try:
            result = self.client.execute("""
                SELECT * FROM events 
                WHERE source_hash = %s 
                ORDER BY ingest_ts DESC 
                LIMIT %s
            """, (source_hash, limit))
            
            # Преобразуем результат в список словарей
            columns = ['event_id', 'source_hash', 'source_url', 'source_date', 
                      'ingest_ts', 'criterion_id', 'criterion_text', 'is_match',
                      'confidence', 'summary', 'model_name', 'latency_ms', 'created_at']
            
            return [dict(zip(columns, row)) for row in result]
            
        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []
    
    def get_criteria_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получение статистики по критериям"""
        try:
            result = self.client.execute("""
                SELECT 
                    criterion_id,
                    count() as total_events,
                    sum(is_match) as matches,
                    avg(confidence) as avg_confidence,
                    avg(latency_ms) as avg_latency_ms
                FROM events 
                WHERE ingest_ts >= now() - INTERVAL %s DAY
                GROUP BY criterion_id
                ORDER BY total_events DESC
            """, (days,))
            
            columns = ['criterion_id', 'total_events', 'matches', 
                      'avg_confidence', 'avg_latency_ms']
            
            return [dict(zip(columns, row)) for row in result]
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return []


# Глобальные экземпляры менеджеров
postgres_manager = PostgresManager()
clickhouse_manager = ClickHouseManager()
