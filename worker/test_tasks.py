"""
Тесты для задач worker
"""

import unicodedata
import unittest
from unittest.mock import Mock, patch

from tasks import analyze_text_task, compute_hash, health_check_task, normalize_text


class TestTextNormalization(unittest.TestCase):
    """Тесты нормализации текста"""

    def test_normalize_text_whitespace(self):
        """Тест нормализации пробелов"""
        text = "  много   пробелов  "
        normalized = normalize_text(text)
        self.assertEqual(normalized, "много пробелов")

    def test_normalize_text_unicode(self):
        """Тест нормализации Unicode"""
        # Создаем текст с разными Unicode формами
        text = "тест" + unicodedata.normalize("NFD", "тест")
        normalized = normalize_text(text)
        # Нормализация сначала убирает пробелы, потом приводит к NFC
        expected = unicodedata.normalize("NFC", "тесттест")
        self.assertEqual(normalized, expected)

    def test_normalize_text_empty(self):
        """Тест нормализации пустого текста"""
        text = ""
        normalized = normalize_text(text)
        self.assertEqual(normalized, "")

    def test_normalize_text_single_word(self):
        """Тест нормализации одного слова"""
        text = "слово"
        normalized = normalize_text(text)
        self.assertEqual(normalized, "слово")


class TestHashComputation(unittest.TestCase):
    """Тесты вычисления хеша"""

    def test_compute_hash_consistent(self):
        """Тест консистентности хеша"""
        text = "тестовый текст"
        hash1 = compute_hash(text)
        hash2 = compute_hash(text)
        self.assertEqual(hash1, hash2)

    def test_compute_hash_different_texts(self):
        """Тест разных хешей для разных текстов"""
        text1 = "первый текст"
        text2 = "второй текст"
        hash1 = compute_hash(text1)
        hash2 = compute_hash(text2)
        self.assertNotEqual(hash1, hash2)

    def test_compute_hash_whitespace_insensitive(self):
        """Тест нечувствительности к пробелам"""
        text1 = "текст с пробелами"
        text2 = "  текст   с   пробелами  "
        hash1 = compute_hash(text1)
        hash2 = compute_hash(text2)
        self.assertEqual(hash1, hash2)

    def test_compute_hash_format(self):
        """Тест формата хеша"""
        text = "тест"
        hash_value = compute_hash(text)
        # SHA-256 хеш должен быть 64 символа в hex
        self.assertEqual(len(hash_value), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in hash_value))


class TestAnalyzeTextTask(unittest.TestCase):
    """Тесты задачи анализа текста"""

    @patch("tasks.postgres_manager")
    @patch("tasks.clickhouse_manager")
    @patch("tasks.OllamaClient")
    def test_analyze_text_success(self, mock_ollama, mock_ch, mock_pg):
        """Тест успешного анализа текста"""
        # Мокаем PostgreSQL
        mock_pg.get_source_by_hash.return_value = None
        mock_pg.get_active_criteria.return_value = [
            Mock(id="test_criterion", criterion_text="Тестовый критерий", threshold=0.5)
        ]
        mock_pg.create_source.return_value = Mock(id="test_source_id")

        # Мокаем ClickHouse
        mock_ch.insert_event.return_value = True

        # Мокаем Ollama
        mock_client = Mock()
        mock_client.health_check.return_value = True
        mock_client.analyze_text.return_value = Mock(
            is_match=True,
            confidence=0.8,
            summary="Текст соответствует критерию",
            model_name="llama3:8b",
            latency_ms=1500,
        )
        mock_ollama.return_value = mock_client

        # Выполняем задачу
        result = analyze_text_task("Тестовый текст для анализа")

        # Проверяем результат
        self.assertEqual(result["status"], "success")
        self.assertIn("source_hash", result)
        self.assertEqual(result["total_events"], 1)
        self.assertEqual(result["matches"], 1)
        self.assertEqual(result["avg_confidence"], 0.8)

    @patch("tasks.postgres_manager")
    def test_analyze_text_already_processed(self, mock_pg):
        """Тест пропуска уже обработанного текста"""
        # Мокаем существующий источник
        mock_pg.get_source_by_hash.return_value = Mock(id="existing_source")

        # Выполняем задачу
        result = analyze_text_task("Уже обработанный текст")

        # Проверяем результат
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "already_processed")

    @patch("tasks.postgres_manager")
    def test_analyze_text_force_recheck(self, mock_pg):
        """Тест принудительной перепроверки"""
        # Мокаем существующий источник
        mock_pg.get_source_by_hash.return_value = Mock(id="existing_source")
        mock_pg.get_active_criteria.return_value = [
            Mock(id="test_criterion", criterion_text="Тестовый критерий", threshold=0.5)
        ]
        mock_pg.create_source.return_value = Mock(id="test_source_id")

        # Мокаем остальные компоненты
        with (
            patch("tasks.clickhouse_manager") as mock_ch,
            patch("tasks.OllamaClient") as mock_ollama,
        ):

            mock_ch.insert_event.return_value = True
            mock_client = Mock()
            mock_client.health_check.return_value = True
            mock_client.analyze_text.return_value = Mock(
                is_match=False,
                confidence=0.3,
                summary="Текст не соответствует",
                model_name="llama3:8b",
                latency_ms=1200,
            )
            mock_ollama.return_value = mock_client

            # Выполняем задачу с force_recheck=True
            result = analyze_text_task("Текст для перепроверки", force_recheck=True)

            # Проверяем результат
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["matches"], 0)

    @patch("tasks.postgres_manager")
    def test_analyze_text_no_criteria(self, mock_pg):
        """Тест отсутствия активных критериев"""
        # Мокаем отсутствие критериев
        mock_pg.get_source_by_hash.return_value = None
        mock_pg.get_active_criteria.return_value = []
        mock_pg.create_source.return_value = Mock(id="test_source_id")

        # Выполняем задачу
        result = analyze_text_task("Текст без критериев")

        # Проверяем результат
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["reason"], "no_active_criteria")

    @patch("tasks.postgres_manager")
    def test_analyze_text_llm_unavailable(self, mock_pg):
        """Тест недоступности LLM"""
        # Мокаем PostgreSQL
        mock_pg.get_source_by_hash.return_value = None
        mock_pg.get_active_criteria.return_value = [
            Mock(id="test_criterion", criterion_text="Тестовый критерий")
        ]
        mock_pg.create_source.return_value = Mock(id="test_source_id")

        # Мокаем недоступный LLM
        with patch("tasks.OllamaClient") as mock_ollama:
            mock_client = Mock()
            mock_client.health_check.return_value = False
            mock_ollama.return_value = mock_client

            # Выполняем задачу
            result = analyze_text_task("Текст с недоступным LLM")

            # Проверяем результат
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["reason"], "llm_unavailable")


class TestHealthCheckTask(unittest.TestCase):
    """Тесты задачи проверки здоровья"""

    @patch("tasks.postgres_manager")
    @patch("tasks.clickhouse_manager")
    @patch("tasks.OllamaClient")
    def test_health_check_all_healthy(self, mock_ollama, mock_ch, mock_pg):
        """Тест проверки здоровья всех сервисов"""
        # Мокаем здоровые сервисы
        # fmt: off
        mock_cursor = (
            mock_pg.get_connection.return_value.__enter__.return_value
            .cursor.return_value.__enter__.return_value
        )
        # fmt: on
        mock_cursor.execute.return_value = None
        mock_ch.client.execute.return_value = None

        mock_client = Mock()
        mock_client.health_check.return_value = True
        mock_ollama.return_value = mock_client

        # Выполняем health check
        result = health_check_task()

        # Проверяем результат
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["postgres"])
        self.assertTrue(result["clickhouse"])
        self.assertTrue(result["llm"])
        self.assertIn("timestamp", result)

    @patch("tasks.postgres_manager")
    @patch("tasks.clickhouse_manager")
    @patch("tasks.OllamaClient")
    def test_health_check_postgres_failure(self, mock_ollama, mock_ch, mock_pg):
        """Тест ошибки PostgreSQL"""
        # Мокаем ошибку PostgreSQL
        mock_pg.get_connection.side_effect = Exception("Connection failed")
        mock_ch.client.execute.return_value = None

        mock_client = Mock()
        mock_client.health_check.return_value = True
        mock_ollama.return_value = mock_client

        # Выполняем health check
        result = health_check_task()

        # Проверяем результат
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["postgres"])
        self.assertTrue(result["clickhouse"])
        self.assertTrue(result["llm"])


if __name__ == "__main__":
    unittest.main()
