"""
Интеграционные тесты для полного flow
UI -> Redis -> Worker -> LLM -> Databases
"""

import os
import sys
from unittest.mock import patch

# Добавляем пути к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ui"))


class TestFullFlow:
    """Тесты полного flow системы"""

    def test_text_analysis_flow(
        self, mock_redis, mock_postgres, mock_clickhouse, mock_ollama, sample_text_data
    ):
        """Тест полного flow анализа текста"""
        with patch(
            "sys.path", sys.path + [os.path.join(os.path.dirname(__file__), "..", "worker")]
        ):
            # Импортируем модули после добавления путей
            from tasks import analyze_text_task

            # Создаем запрос
            text = sample_text_data["text"]
            source_url = sample_text_data["source_url"]
            source_date = sample_text_data["source_date"]

            # Выполняем анализ
            result = analyze_text_task(text, source_url, source_date)

            # Проверяем результат
            assert result is not None
            assert "status" in result
            assert "source_hash" in result

    def test_error_handling(self, mock_redis, mock_postgres, mock_clickhouse, mock_ollama):
        """Тест обработки ошибок"""
        with patch(
            "sys.path", sys.path + [os.path.join(os.path.dirname(__file__), "..", "worker")]
        ):
            from tasks import analyze_text_task

            # Тест с пустым текстом
            result = analyze_text_task("", "https://example.com", "2024-12-30")

            # Должен вернуть результат с ошибкой
            assert result is not None
            assert "status" in result

    def test_concurrent_processing(
        self, mock_redis, mock_postgres, mock_clickhouse, mock_ollama, sample_text_data
    ):
        """Тест конкурентной обработки"""
        import threading

        with patch(
            "sys.path", sys.path + [os.path.join(os.path.dirname(__file__), "..", "worker")]
        ):
            from tasks import analyze_text_task

            results = []
            errors = []

            def process_text(text_id):
                try:
                    text = f"{sample_text_data['text']} {text_id}"
                    source_url = f"{sample_text_data['source_url']}/{text_id}"
                    result = analyze_text_task(text, source_url, "2024-12-30")
                    results.append(result)
                except Exception as e:
                    errors.append(e)

            # Запускаем 5 потоков
            threads = []
            for i in range(5):
                thread = threading.Thread(target=process_text, args=(i,))
                threads.append(thread)
                thread.start()

            # Ждем завершения
            for thread in threads:
                thread.join()

            # Проверяем результаты
            assert len(results) == 5
            assert len(errors) == 0

    def test_data_consistency(
        self, mock_redis, mock_postgres, mock_clickhouse, mock_ollama, sample_text_data
    ):
        """Тест консистентности данных"""
        with patch(
            "sys.path", sys.path + [os.path.join(os.path.dirname(__file__), "..", "worker")]
        ):
            from tasks import analyze_text_task, compute_hash, normalize_text

            # Проверяем нормализацию
            normalized = normalize_text(sample_text_data["text"])
            assert normalized is not None
            assert len(normalized) > 0

            # Проверяем хеширование
            text_hash = compute_hash(normalized)
            assert text_hash is not None
            assert len(text_hash) == 64  # SHA-256

            # Проверяем полный анализ
            result = analyze_text_task(
                sample_text_data["text"],
                sample_text_data["source_url"],
                sample_text_data["source_date"],
            )
            assert result["source_hash"] == text_hash

    def test_performance_metrics(
        self, mock_redis, mock_postgres, mock_clickhouse, mock_ollama, sample_text_data
    ):
        """Тест метрик производительности"""
        import time

        with patch(
            "sys.path", sys.path + [os.path.join(os.path.dirname(__file__), "..", "worker")]
        ):
            from tasks import analyze_text_task

            start_time = time.time()

            result = analyze_text_task(
                sample_text_data["text"],
                sample_text_data["source_url"],
                sample_text_data["source_date"],
            )

            end_time = time.time()
            processing_time = end_time - start_time

            # Проверяем метрики
            assert processing_time < 5.0  # Не более 5 секунд
            assert result is not None
            assert "status" in result


class TestHealthChecks:
    """Тесты проверки здоровья сервисов"""

    def test_redis_health(self, mock_redis):
        """Тест здоровья Redis"""
        assert mock_redis.ping() is True

    def test_postgres_health(self, mock_postgres):
        """Тест здоровья PostgreSQL"""
        cursor = mock_postgres.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchall() == []

    def test_clickhouse_health(self, mock_clickhouse):
        """Тест здоровья ClickHouse"""
        result = mock_clickhouse.execute("SELECT 1")
        assert result == []


class TestDataFlow:
    """Тесты потока данных"""

    def test_text_normalization(self):
        """Тест нормализации текста"""
        with patch(
            "sys.path", sys.path + [os.path.join(os.path.dirname(__file__), "..", "worker")]
        ):
            from tasks import normalize_text

            # Тест с различными символами
            text = "Тест  тест   тест"
            normalized = normalize_text(text)
            assert normalized == "Тест тест тест"

    def test_hash_calculation(self):
        """Тест вычисления хеша"""
        with patch(
            "sys.path", sys.path + [os.path.join(os.path.dirname(__file__), "..", "worker")]
        ):
            from tasks import compute_hash

            text = "Тестовый текст"
            hash1 = compute_hash(text)
            hash2 = compute_hash(text)

            # Одинаковый текст должен давать одинаковый хеш
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA-256

    def test_event_serialization(self, sample_events):
        """Тест сериализации событий"""
        import json

        for event in sample_events:
            # Проверяем, что событие можно сериализовать в JSON
            json_str = json.dumps(event)
            assert json_str is not None

            # Проверяем, что можно десериализовать обратно
            deserialized = json.loads(json_str)
            assert deserialized == event
