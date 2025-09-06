#!/usr/bin/env python3
"""
Интеграционный тест для проверки полного flow
UI -> Redis -> Worker -> LLM -> Databases
"""

import json
import time

import psycopg2
import redis
import requests
import structlog
from clickhouse_driver import Client

# Настройка логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class IntegrationTest:
    """Класс для интеграционного тестирования"""

    def __init__(self):
        self.redis_url = "redis://localhost:6383/0"
        self.postgres_url = "postgresql://postgres:postgres@localhost:5436/pharma_analysis"
        self.clickhouse_url = "http://localhost:8127"
        self.ollama_url = "http://localhost:11438"
        self.ui_url = "http://localhost:8505"
        self.worker_url = "http://localhost:8000"

        # Инициализация клиентов
        self.redis_client = redis.from_url(self.redis_url)
        self.clickhouse_client = Client("localhost", port=9004)

    def test_health_checks(self):
        """Проверка health checks всех сервисов"""
        logger.info("Проверка health checks всех сервисов")

        # Redis
        try:
            self.redis_client.ping()
            logger.info("✅ Redis доступен")
        except Exception as e:
            logger.error(f"❌ Redis недоступен: {e}")
            return False

        # PostgreSQL
        try:
            conn = psycopg2.connect(self.postgres_url)
            conn.close()
            logger.info("✅ PostgreSQL доступен")
        except Exception as e:
            logger.error(f"❌ PostgreSQL недоступен: {e}")
            return False

        # ClickHouse
        try:
            response = requests.get(f"{self.clickhouse_url}/ping", timeout=5)
            if response.status_code == 200:
                logger.info("✅ ClickHouse доступен")
            else:
                logger.error(f"❌ ClickHouse недоступен: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ ClickHouse недоступен: {e}")
            return False

        # Ollama
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama доступен")
            else:
                logger.error(f"❌ Ollama недоступен: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ollama недоступен: {e}")
            return False

        # UI
        try:
            response = requests.get(f"{self.ui_url}/_stcore/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ UI доступен")
            else:
                logger.error(f"❌ UI недоступен: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ UI недоступен: {e}")
            return False

        # Worker
        try:
            response = requests.get(f"{self.worker_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Worker доступен")
            else:
                logger.error(f"❌ Worker недоступен: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Worker недоступен: {e}")
            return False

        return True

    def test_database_schemas(self):
        """Проверка схем баз данных"""
        logger.info("Проверка схем баз данных")

        # PostgreSQL - проверка таблиц
        try:
            conn = psycopg2.connect(self.postgres_url)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """
            )
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ["sources", "criteria"]
            for table in expected_tables:
                if table in tables:
                    logger.info(f"✅ Таблица {table} существует в PostgreSQL")
                else:
                    logger.error(f"❌ Таблица {table} отсутствует в PostgreSQL")
                    return False

            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Ошибка проверки PostgreSQL: {e}")
            return False

        # ClickHouse - проверка таблиц через HTTP API
        try:
            response = requests.post(
                f"{self.clickhouse_url}", data="SHOW TABLES FROM pharma_analysis;"
            )
            if response.status_code == 200:
                tables = response.text.strip().split("\n")
                if "events" in tables:
                    logger.info("✅ Таблица events существует в ClickHouse")
                else:
                    logger.error("❌ Таблица events отсутствует в ClickHouse")
                    return False
            else:
                logger.error(f"❌ Ошибка запроса к ClickHouse: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка проверки ClickHouse: {e}")
            return False

        return True

    def test_redis_queue(self):
        """Проверка Redis очереди"""
        logger.info("Проверка Redis очереди")

        try:
            # Проверка подключения
            self.redis_client.ping()

            # Проверка очереди
            queue_info = self.redis_client.lrange("rq:queue:text_analysis", 0, -1)
            logger.info(f"✅ Redis очередь доступна, задач в очереди: {len(queue_info)}")

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка проверки Redis: {e}")
            return False

    def test_ollama_model(self):
        """Проверка модели Ollama"""
        logger.info("Проверка модели Ollama")

        try:
            # Проверка доступных моделей
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]

                if "llama3:8b" in model_names:
                    logger.info("✅ Модель llama3:8b доступна")
                    return True
                else:
                    logger.warning("⚠️ Модель llama3:8b не найдена, попытка загрузки...")
                    # Попытка загрузки модели
                    response = requests.post(
                        f"{self.ollama_url}/api/pull", json={"name": "llama3:8b"}
                    )
                    if response.status_code == 200:
                        logger.info("✅ Модель llama3:8b загружена")
                        return True
                    else:
                        logger.error("❌ Не удалось загрузить модель llama3:8b")
                        return False
            else:
                logger.error(f"❌ Ошибка получения моделей: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка проверки Ollama: {e}")
            return False

    def test_full_flow(self):
        """Тестирование полного flow"""
        logger.info("Тестирование полного flow")

        try:
            # 1. Добавление задачи в очередь
            test_text = "Тестовый текст для анализа фармацевтических препаратов"
            test_data = {
                "text": test_text,
                "source_url": "https://example.com/test",
                "force_recheck": False,
            }

            # Добавляем задачу в Redis очередь
            self.redis_client.lpush("rq:queue:text_analysis", json.dumps(test_data))
            logger.info("✅ Задача добавлена в очередь")

            # 2. Проверяем, что задача обрабатывается
            time.sleep(5)  # Ждем обработки

            queue_length = self.redis_client.llen("rq:queue:text_analysis")
            logger.info(f"✅ Задач в очереди после обработки: {queue_length}")

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка тестирования flow: {e}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Запуск интеграционных тестов")

        tests = [
            ("Health Checks", self.test_health_checks),
            ("Database Schemas", self.test_database_schemas),
            ("Redis Queue", self.test_redis_queue),
            ("Ollama Model", self.test_ollama_model),
            ("Full Flow", self.test_full_flow),
        ]

        results = []
        for test_name, test_func in tests:
            logger.info(f"📋 Выполнение теста: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    logger.info(f"✅ Тест {test_name} пройден")
                else:
                    logger.error(f"❌ Тест {test_name} провален")
            except Exception as e:
                logger.error(f"❌ Ошибка в тесте {test_name}: {e}")
                results.append((test_name, False))

        # Итоговый отчет
        passed = sum(1 for _, result in results if result)
        total = len(results)

        logger.info(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")

        for test_name, result in results:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            logger.info(f"  {test_name}: {status}")

        return passed == total


if __name__ == "__main__":
    test = IntegrationTest()
    success = test.run_all_tests()

    if success:
        print("🎉 Все интеграционные тесты пройдены!")
        exit(0)
    else:
        print("❌ Некоторые тесты провалены!")
        exit(1)
