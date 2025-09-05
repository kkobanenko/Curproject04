"""
Модуль для работы с базами данных в UI
PostgreSQL и ClickHouse
"""

import logging
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from clickhouse_driver import Client
from datetime import datetime, timedelta
import pandas as pd

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
    
    def get_sources(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение списка источников"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM sources 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (limit,))
                results = cur.fetchall()
                return [dict(row) for row in results]
    
    def get_source_by_hash(self, source_hash: str) -> Optional[Dict[str, Any]]:
        """Получение источника по хешу"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM sources WHERE source_hash = %s",
                    (source_hash,)
                )
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
    
    def get_criteria(self) -> List[Dict[str, Any]]:
        """Получение всех критериев"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM criteria ORDER BY id")
                results = cur.fetchall()
                return [dict(row) for row in results]
    
    def get_active_criteria(self) -> List[Dict[str, Any]]:
        """Получение активных критериев"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM criteria WHERE is_active = TRUE ORDER BY id")
                results = cur.fetchall()
                return [dict(row) for row in results]


class ClickHouseManager:
    """Менеджер для работы с ClickHouse"""
    
    def __init__(self):
        """Инициализация подключения к ClickHouse"""
        # Извлекаем хост из URL (убираем http:// и порт)
        host = settings.clickhouse_url.replace('http://', '').split(':')[0]
        self.client = Client(
            host=host,
            database=settings.clickhouse_database,
            port=9000  # Native protocol port
        )
    
    def get_events_by_source(self, source_hash: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение событий по источнику"""
        try:
            result = self.client.execute(f"""
                SELECT * FROM events 
                WHERE source_hash = '{source_hash}' 
                ORDER BY ingest_ts DESC 
                LIMIT {limit}
            """)
            
            # Преобразуем результат в список словарей
            columns = ['event_id', 'source_hash', 'source_url', 'source_date', 
                      'ingest_ts', 'criterion_id', 'criterion_text', 'is_match',
                      'confidence', 'summary', 'model_name', 'latency_ms', 'created_at']
            
            return [dict(zip(columns, row)) for row in result]
            
        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение последних событий"""
        try:
            result = self.client.execute(f"""
                SELECT * FROM events 
                ORDER BY ingest_ts DESC 
                LIMIT {limit}
            """)
            
            columns = ['event_id', 'source_hash', 'source_url', 'source_date', 
                      'ingest_ts', 'criterion_id', 'criterion_text', 'is_match',
                      'confidence', 'summary', 'model_name', 'latency_ms', 'created_at']
            
            events = []
            for row in result:
                event = dict(zip(columns, row))
                # Преобразуем типы данных
                if event['is_match'] is not None:
                    event['is_match'] = int(event['is_match'])
                if event['confidence'] is not None:
                    event['confidence'] = float(event['confidence'])
                if event['latency_ms'] is not None:
                    event['latency_ms'] = int(event['latency_ms'])
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Ошибка получения последних событий: {e}")
            return []
    
    def get_criteria_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получение статистики по критериям"""
        try:
            result = self.client.execute(f"""
                SELECT 
                    criterion_id,
                    count() as total_events,
                    sum(is_match) as matches,
                    avg(confidence) as avg_confidence,
                    avg(latency_ms) as avg_latency_ms
                FROM events 
                WHERE ingest_ts >= now() - INTERVAL {days} DAY
                GROUP BY criterion_id
                ORDER BY total_events DESC
            """)
            
            columns = ['criterion_id', 'total_events', 'matches', 
                      'avg_confidence', 'avg_latency_ms']
            
            return [dict(zip(columns, row)) for row in result]
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return []
    
    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Получение ежедневной статистики"""
        try:
            result = self.client.execute(f"""
                SELECT 
                    toDate(ingest_ts) as date,
                    count() as total_events,
                    sum(is_match) as matches,
                    avg(confidence) as avg_confidence,
                    avg(latency_ms) as avg_latency_ms
                FROM events 
                WHERE ingest_ts >= now() - INTERVAL {days} DAY
                GROUP BY date
                ORDER BY date DESC
            """)
            
            columns = ['date', 'total_events', 'matches', 
                      'avg_confidence', 'avg_latency_ms']
            
            return [dict(zip(columns, row)) for row in result]
            
        except Exception as e:
            logger.error(f"Ошибка получения ежедневной статистики: {e}")
            return []


# Глобальные экземпляры менеджеров
postgres_manager = PostgresManager()
clickhouse_manager = ClickHouseManager()
