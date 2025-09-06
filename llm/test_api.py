"""
Тесты для API клиента Ollama
"""

import json
import unittest
from unittest.mock import Mock, patch

from api import AnalysisResult, OllamaClient


class TestOllamaClient(unittest.TestCase):
    """Тесты для OllamaClient"""

    def setUp(self):
        """Настройка тестов"""
        self.client = OllamaClient("http://localhost:11434")

    def test_init(self):
        """Тест инициализации клиента"""
        client = OllamaClient("http://test.com")
        self.assertEqual(client.base_url, "http://test.com")
        self.assertIsNotNone(client.session)

    @patch("requests.Session.post")
    def test_analyze_text_success(self, mock_post):
        """Тест успешного анализа текста"""
        # Мокаем ответ от Ollama
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": json.dumps(
                {"is_match": True, "confidence": 0.85, "summary": "Текст соответствует критерию"}
            )
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Выполняем анализ
        result = self.client.analyze_text(text="Тестовый текст", criterion_text="Тестовый критерий")

        # Проверяем результат
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.is_match)
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(result.summary, "Текст соответствует критерию")
        self.assertEqual(result.model_name, "llama3:8b")
        # В моке время выполнения может быть 0, поэтому проверяем только тип
        self.assertIsInstance(result.latency_ms, int)

    @patch("requests.Session.post")
    def test_analyze_text_invalid_json(self, mock_post):
        """Тест анализа с некорректным JSON ответом"""
        # Мокаем ответ с некорректным JSON
        mock_response = Mock()
        mock_response.json.return_value = {"response": "некорректный json"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Выполняем анализ
        result = self.client.analyze_text(text="Тестовый текст", criterion_text="Тестовый критерий")

        # Проверяем fallback значения
        self.assertFalse(result.is_match)
        self.assertEqual(result.confidence, 0.0)
        self.assertIn("Ошибка анализа", result.summary)

    @patch("requests.Session.post")
    def test_analyze_text_confidence_bounds(self, mock_post):
        """Тест границ confidence"""
        # Мокаем ответ с confidence вне границ
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": json.dumps(
                {"is_match": True, "confidence": 1.5, "summary": "Тест"}  # Больше 1.0
            )
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Выполняем анализ
        result = self.client.analyze_text(text="Тестовый текст", criterion_text="Тестовый критерий")

        # Проверяем, что confidence ограничен
        self.assertEqual(result.confidence, 1.0)

    @patch("requests.Session.get")
    def test_health_check_success(self, mock_get):
        """Тест успешной проверки здоровья"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.client.health_check()
        self.assertTrue(result)

    @patch("requests.Session.get")
    def test_health_check_failure(self, mock_get):
        """Тест неудачной проверки здоровья"""
        mock_get.side_effect = Exception("Connection error")

        result = self.client.health_check()
        self.assertFalse(result)

    @patch("requests.Session.get")
    def test_get_models_success(self, mock_get):
        """Тест получения списка моделей"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3:8b", "size": 1234567890},
                {"name": "llama3:70b", "size": 9876543210},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        models = self.client.get_models()
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["name"], "llama3:8b")

        # Проверяем, что был вызван правильный URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("/api/tags", call_args[0][0])


if __name__ == "__main__":
    unittest.main()
