"""
Модуль для работы с базами данных
PostgreSQL и ClickHouse
"""

import logging
from typing import Any, Dict, List, Optional

import psycopg2
from clickhouse_driver import Client
from config import settings
from models import Criterion, Event, Source
from psycopg2.extras import RealDictCursor

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
                cur.execute("SELECT * FROM sources WHERE source_hash = %s", (source_hash,))
                result = cur.fetchone()
                if result:
                    return Source.from_dict(dict(result))
                return None

    def create_source(self, source: Source) -> Source:
        """Создание нового источника"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO sources (id, source_hash, source_url, source_date, text,
                                       ingest_ts, force_recheck, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_hash) DO UPDATE SET
                        updated_at = NOW(),
                        force_recheck = EXCLUDED.force_recheck,
                        text = EXCLUDED.text
                    RETURNING *
                """,
                    (
                        str(source.id),
                        source.source_hash,
                        source.source_url,
                        source.source_date,
                        source.text,
                        source.ingest_ts,
                        source.force_recheck,
                        source.created_at,
                        source.updated_at,
                    ),
                )
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
                cur.execute("SELECT * FROM criteria WHERE id = %s", (criterion_id,))
                result = cur.fetchone()
                if result:
                    return Criterion.from_dict(dict(result))
                return None


class ClickHouseManager:
    """Менеджер для работы с ClickHouse"""

    def __init__(self):
        """Инициализация подключения к ClickHouse"""
        # Извлекаем хост из URL (убираем http:// и порт)
        host = settings.clickhouse_url.replace("http://", "").split(":")[0]
        self.client = Client(host=host, database=settings.clickhouse_database, port=9000)

    def insert_event(self, event: Event) -> bool:
        """Вставка события в ClickHouse"""
        try:
            data = event.to_dict()

            # Добавляем отладочную информацию
            logger.info(
                f"data['source_date'] type: {type(data['source_date'])}, "
                f"value: {data['source_date']}"
            )
            logger.info(
                f"data['ingest_ts'] type: {type(data['ingest_ts'])}, value: {data['ingest_ts']}"
            )
            logger.info(
                f"data['created_at'] type: {type(data['created_at'])}, value: {data['created_at']}"
            )

            # Проверяем все поля на строки
            for key, value in data.items():
                if isinstance(value, str) and key in ["source_date", "ingest_ts", "created_at"]:
                    logger.warning(f"Поле {key} является строкой: {value}")

            # Преобразуем datetime в формат, который понимает ClickHouse
            from datetime import datetime

            if data["ingest_ts"] and hasattr(data["ingest_ts"], "isoformat"):
                # Преобразуем в datetime с микросекундами для DateTime64(3)
                if isinstance(data["ingest_ts"], datetime):
                    data["ingest_ts"] = data["ingest_ts"]
                else:
                    data["ingest_ts"] = datetime.fromisoformat(
                        data["ingest_ts"].replace("Z", "+00:00")
                    )

            if data["source_date"] and hasattr(data["source_date"], "isoformat"):
                if isinstance(data["source_date"], datetime):
                    data["source_date"] = data["source_date"]
                else:
                    data["source_date"] = datetime.fromisoformat(
                        data["source_date"].replace("Z", "+00:00")
                    )

            if data["created_at"] and hasattr(data["created_at"], "isoformat"):
                if isinstance(data["created_at"], datetime):
                    data["created_at"] = data["created_at"]
                else:
                    data["created_at"] = datetime.fromisoformat(
                        data["created_at"].replace("Z", "+00:00")
                    )

            # Добавляем логирование после преобразования
            logger.info(f"После преобразования - data['source_date']: {data['source_date']}")
            logger.info(f"После преобразования - data['ingest_ts']: {data['ingest_ts']}")
            logger.info(f"После преобразования - data['created_at']: {data['created_at']}")

            # Логируем весь data для отладки
            logger.info(f"Полный data для вставки: {data}")

            try:
                logger.info("Пытаемся выполнить INSERT в ClickHouse...")

                # Используем HTTP API для вставки

                import requests

                # Формируем данные для вставки
                insert_data = {
                    "event_id": data["event_id"],
                    "source_hash": data["source_hash"],
                    "source_url": data["source_url"] or "",
                    "source_date": (
                        data["source_date"].strftime("%Y-%m-%d %H:%M:%S")
                        if data["source_date"]
                        else None
                    ),
                    "ingest_ts": data["ingest_ts"].strftime("%Y-%m-%d %H:%M:%S"),
                    "criterion_id": data["criterion_id"],
                    "criterion_text": data["criterion_text"],
                    "is_match": data["is_match"],
                    "confidence": data["confidence"],
                    "summary": data["summary"],
                    "model_name": data["model_name"],
                    "latency_ms": data["latency_ms"],
                    "created_at": data["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                }

                # Формируем SQL запрос
                sql = f"""
                INSERT INTO events (
                    event_id, source_hash, source_url, source_date, ingest_ts,
                    criterion_id, criterion_text, is_match, confidence, summary,
                    model_name, latency_ms, created_at
                ) VALUES (
                    '{insert_data['event_id']}', '{insert_data['source_hash']}',
                    '{insert_data['source_url']}',
                    {f"'{insert_data['source_date']}'" if insert_data['source_date'] else 'NULL'},
                    '{insert_data['ingest_ts']}', '{insert_data['criterion_id']}',
                    '{insert_data['criterion_text'].replace("'", "''")}',
                    {insert_data['is_match']}, {insert_data['confidence']},
                    '{insert_data['summary'].replace("'", "''")}',
                    '{insert_data['model_name']}', {insert_data['latency_ms']},
                    '{insert_data['created_at']}'
                )
                """

                # Отправляем запрос через HTTP API
                response = requests.post(
                    f"{settings.clickhouse_url}/",
                    params={"query": sql},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code == 200:
                    logger.info("INSERT в ClickHouse выполнен успешно через HTTP API!")
                else:
                    logger.error(f"Ошибка HTTP API: {response.status_code} - {response.text}")
                    raise Exception(f"HTTP API error: {response.status_code}")

            except Exception as e:
                logger.error(f"Ошибка при выполнении INSERT в ClickHouse: {e}")
                logger.error(f"Тип ошибки: {type(e)}")
                logger.error(f"Детали ошибки: {str(e)}")
                raise

            logger.info(f"Событие {event.event_id} сохранено в ClickHouse")
            return True

        except Exception as e:
            logger.error(f"Ошибка сохранения события в ClickHouse: {e}")
            return False

    def get_events_by_source(self, source_hash: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение событий по источнику"""
        try:
            result = self.client.execute(
                """
                SELECT * FROM events
                WHERE source_hash = %s
                ORDER BY ingest_ts DESC
                LIMIT %s
            """,
                (source_hash, limit),
            )

            # Преобразуем результат в список словарей
            columns = [
                "event_id",
                "source_hash",
                "source_url",
                "source_date",
                "ingest_ts",
                "criterion_id",
                "criterion_text",
                "is_match",
                "confidence",
                "summary",
                "model_name",
                "latency_ms",
                "created_at",
            ]

            return [dict(zip(columns, row)) for row in result]

        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []

    def get_criteria_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получение статистики по критериям"""
        try:
            result = self.client.execute(
                """
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
            """,
                (days,),
            )

            columns = [
                "criterion_id",
                "total_events",
                "matches",
                "avg_confidence",
                "avg_latency_ms",
            ]

            return [dict(zip(columns, row)) for row in result]

        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return []


# Глобальные экземпляры менеджеров
postgres_manager = PostgresManager()
clickhouse_manager = ClickHouseManager()
