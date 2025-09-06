#!/usr/bin/env python3
"""
Тесты для импорта модулей и измерения покрытия кода
"""

import os
import sys
import unittest

# Добавляем пути к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "db"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "llm"))


class TestImports(unittest.TestCase):
    """Тесты для импорта модулей"""

    def test_db_models_import(self):
        """Тест импорта db.models"""
        from db.models import CriteriaStats, Criterion, Event, Source, SourceStats

        # Проверяем, что классы существуют
        self.assertTrue(hasattr(Source, "__init__"))
        self.assertTrue(hasattr(Criterion, "__init__"))
        self.assertTrue(hasattr(Event, "__init__"))
        self.assertTrue(hasattr(SourceStats, "__init__"))
        self.assertTrue(hasattr(CriteriaStats, "__init__"))

    def test_llm_api_import(self):
        """Тест импорта llm.api"""
        from llm.api import AnalysisResult, OllamaClient

        # Проверяем, что классы существуют
        self.assertTrue(hasattr(OllamaClient, "__init__"))
        self.assertTrue(hasattr(AnalysisResult, "__init__"))

        # Создаем экземпляр клиента
        client = OllamaClient("http://test.com")
        self.assertEqual(client.base_url, "http://test.com")

    def test_worker_modules_import(self):
        """Тест импорта worker модулей"""
        # Переходим в директорию worker для импорта
        original_path = sys.path.copy()
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "worker"))

        try:
            import config
            import models
            import tasks

            # Проверяем, что модули импортированы
            self.assertTrue(hasattr(tasks, "normalize_text"))
            self.assertTrue(hasattr(tasks, "compute_hash"))
            self.assertTrue(hasattr(models, "Source"))
            self.assertTrue(hasattr(config, "Settings"))

        finally:
            sys.path = original_path


if __name__ == "__main__":
    unittest.main()
