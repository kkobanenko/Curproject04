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
from models import Source, Criterion, Event, News

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
    
    def create_criterion(self, criterion: Criterion) -> Dict[str, Any]:
        """Создание нового критерия"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO criteria (id, criterion_text, criteria_version, is_active, threshold, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    criterion.id,
                    criterion.criterion_text,
                    criterion.criteria_version,
                    criterion.is_active,
                    criterion.threshold,
                    criterion.created_at,
                    criterion.updated_at
                ))
                result = cur.fetchone()
                conn.commit()
                return dict(result)
    
    def update_criterion(self, criterion_id: str, criterion_text: str = None, 
                        is_active: bool = None, threshold: float = None) -> Dict[str, Any]:
        """Обновление критерия"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Формируем динамический запрос
                updates = []
                params = []
                
                if criterion_text is not None:
                    updates.append("criterion_text = %s")
                    params.append(criterion_text)
                
                if is_active is not None:
                    updates.append("is_active = %s")
                    params.append(is_active)
                
                if threshold is not None:
                    updates.append("threshold = %s")
                    params.append(threshold)
                
                if not updates:
                    # Если нет изменений, просто возвращаем текущий критерий
                    cur.execute("SELECT * FROM criteria WHERE id = %s", (criterion_id,))
                    result = cur.fetchone()
                    return dict(result) if result else None
                
                # Добавляем обновление времени
                updates.append("updated_at = %s")
                params.append(datetime.utcnow())
                
                # Добавляем ID критерия
                params.append(criterion_id)
                
                query = f"""
                    UPDATE criteria 
                    SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING *
                """
                
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
    
    def delete_criterion(self, criterion_id: str) -> bool:
        """Удаление критерия"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM criteria WHERE id = %s", (criterion_id,))
                conn.commit()
                return cur.rowcount > 0
    
    def get_criterion_by_id(self, criterion_id: str) -> Optional[Dict[str, Any]]:
        """Получение критерия по ID"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM criteria WHERE id = %s", (criterion_id,))
                result = cur.fetchone()
                return dict(result) if result else None
    
    # Методы для работы с новостями
    def create_news(self, news: News) -> bool:
        """Создание новой новости"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO news (id, title, url, content, source, search_query, published_date, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(news.id),
                        news.title,
                        news.url,
                        news.content,
                        news.source,
                        news.search_query,
                        news.published_date,
                        news.created_at,
                        news.updated_at
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Ошибка создания новости: {e}")
            return False
    
    def get_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение списка новостей"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM news 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (limit,))
                    results = cur.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Ошибка получения новостей: {e}")
            return []
    
    def get_news_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Получение новости по URL"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM news WHERE url = %s", (url,))
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Ошибка получения новости по URL: {e}")
            return None
    
    def get_news_by_source(self, source: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение новостей по источнику"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM news 
                        WHERE source = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (source, limit))
                    results = cur.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Ошибка получения новостей по источнику: {e}")
            return []
    
    def get_news_by_search_query(self, search_query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение новостей по поисковому запросу"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM news 
                        WHERE search_query ILIKE %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (f"%{search_query}%", limit))
                    results = cur.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Ошибка получения новостей по запросу: {e}")
            return []
    
    def delete_news(self, news_id: str) -> bool:
        """Удаление новости"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM news WHERE id = %s", (news_id,))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка удаления новости: {e}")
            return False


class ClickHouseManager:
    """Менеджер для работы с ClickHouse"""
    
    def __init__(self):
        """Инициализация подключения к ClickHouse"""
        import requests
        self.base_url = settings.clickhouse_url
        self.database = settings.clickhouse_database
        self.session = requests.Session()
    
    def get_events_by_source(self, source_hash: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение событий по источнику"""
        try:
            query = f"""
                SELECT * FROM events 
                WHERE source_hash = '{source_hash}' 
                ORDER BY ingest_ts DESC 
                LIMIT {limit}
            """
            
            response = self.session.get(
                f"{self.base_url}/",
                params={
                    'query': query,
                    'database': self.database,
                    'format': 'JSONEachRow'
                }
            )
            response.raise_for_status()
            
            # Парсим JSON ответ
            import json
            lines = response.text.strip().split('\n')
            events = []
            
            for line in lines:
                if line.strip():
                    event = json.loads(line)
                    # Преобразуем типы данных
                    if event.get('is_match') is not None:
                        event['is_match'] = int(event['is_match'])
                    if event.get('confidence') is not None:
                        event['confidence'] = float(event['confidence'])
                    if event.get('latency_ms') is not None:
                        event['latency_ms'] = int(event['latency_ms'])
                    events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение последних событий"""
        try:
            query = f"""
                SELECT * FROM events 
                ORDER BY ingest_ts DESC 
                LIMIT {limit}
            """
            
            response = self.session.get(
                f"{self.base_url}/",
                params={
                    'query': query,
                    'database': self.database
                }
            )
            response.raise_for_status()
            
            # Парсим TSV ответ
            lines = response.text.strip().split('\n')
            if not lines:
                return []
            
            # Первая строка - заголовки
            headers = ['event_id', 'source_hash', 'source_url', 'source_date', 
                      'ingest_ts', 'criterion_id', 'criterion_text', 'is_match',
                      'confidence', 'summary', 'model_name', 'latency_ms', 'created_at']
            events = []
            
            for line in lines:
                if line.strip():
                    values = line.split('\t')
                    if len(values) >= len(headers):
                        event = dict(zip(headers, values))
                        
                        # Преобразуем типы данных
                        if event.get('is_match') is not None and event['is_match'] != '\\N':
                            event['is_match'] = int(event['is_match'])
                        if event.get('confidence') is not None and event['confidence'] != '\\N':
                            event['confidence'] = float(event['confidence'])
                        if event.get('latency_ms') is not None and event['latency_ms'] != '\\N':
                            event['latency_ms'] = int(event['latency_ms'])
                        
                        # Заменяем \N на None
                        for key, value in event.items():
                            if value == '\\N':
                                event[key] = None
                        
                        events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Ошибка получения последних событий: {e}")
            return []
    
    def get_criteria_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получение статистики по критериям"""
        try:
            query = f"""
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
            """
            
            response = self.session.get(
                f"{self.base_url}/",
                params={
                    'query': query,
                    'database': self.database
                }
            )
            response.raise_for_status()
            
            # Парсим TSV ответ
            lines = response.text.strip().split('\n')
            if not lines:
                return []
            
            # Заголовки для статистики
            headers = ['criterion_id', 'total_events', 'matches', 'avg_confidence', 'avg_latency_ms']
            stats = []
            
            for line in lines:
                if line.strip():
                    values = line.split('\t')
                    if len(values) >= len(headers):
                        stat = dict(zip(headers, values))
                        
                        # Преобразуем типы данных
                        if stat.get('total_events') is not None and stat['total_events'] != '\\N':
                            stat['total_events'] = int(stat['total_events'])
                        if stat.get('matches') is not None and stat['matches'] != '\\N':
                            stat['matches'] = int(stat['matches'])
                        if stat.get('avg_confidence') is not None and stat['avg_confidence'] != '\\N':
                            stat['avg_confidence'] = float(stat['avg_confidence'])
                        if stat.get('avg_latency_ms') is not None and stat['avg_latency_ms'] != '\\N':
                            stat['avg_latency_ms'] = float(stat['avg_latency_ms'])
                        
                        # Заменяем \N на None
                        for key, value in stat.items():
                            if value == '\\N':
                                stat[key] = None
                        
                        stats.append(stat)
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return []
    
    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Получение ежедневной статистики"""
        try:
            query = f"""
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
            """
            
            response = self.session.get(
                f"{self.base_url}/",
                params={
                    'query': query,
                    'database': self.database
                }
            )
            response.raise_for_status()
            
            # Парсим TSV ответ
            lines = response.text.strip().split('\n')
            if not lines:
                return []
            
            # Заголовки для ежедневной статистики
            headers = ['date', 'total_events', 'matches', 'avg_confidence', 'avg_latency_ms']
            stats = []
            
            for line in lines:
                if line.strip():
                    values = line.split('\t')
                    if len(values) >= len(headers):
                        stat = dict(zip(headers, values))
                        
                        # Преобразуем типы данных
                        if stat.get('total_events') is not None and stat['total_events'] != '\\N':
                            stat['total_events'] = int(stat['total_events'])
                        if stat.get('matches') is not None and stat['matches'] != '\\N':
                            stat['matches'] = int(stat['matches'])
                        if stat.get('avg_confidence') is not None and stat['avg_confidence'] != '\\N':
                            stat['avg_confidence'] = float(stat['avg_confidence'])
                        if stat.get('avg_latency_ms') is not None and stat['avg_latency_ms'] != '\\N':
                            stat['avg_latency_ms'] = float(stat['avg_latency_ms'])
                        
                        # Заменяем \N на None
                        for key, value in stat.items():
                            if value == '\\N':
                                stat[key] = None
                        
                        stats.append(stat)
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения ежедневной статистики: {e}")
            return []


# Глобальные экземпляры менеджеров
postgres_manager = PostgresManager()
clickhouse_manager = ClickHouseManager()
