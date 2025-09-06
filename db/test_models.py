"""
Тесты для моделей базы данных
"""

import unittest
import uuid
from datetime import datetime

from models import CriteriaStats, Criterion, Event, Source, SourceStats


class TestSource(unittest.TestCase):
    """Тесты для модели Source"""

    def test_source_creation(self):
        """Тест создания источника"""
        source = Source(
            source_hash="test_hash_123",
            source_url="https://example.com",
            source_date=datetime(2024, 1, 1),
        )

        self.assertIsNotNone(source.id)
        self.assertEqual(source.source_hash, "test_hash_123")
        self.assertEqual(source.source_url, "https://example.com")
        self.assertEqual(source.source_date, datetime(2024, 1, 1))
        self.assertFalse(source.force_recheck)
        self.assertIsNotNone(source.created_at)
        self.assertIsNotNone(source.updated_at)

    def test_source_to_dict(self):
        """Тест преобразования в словарь"""
        source = Source(source_hash="test_hash_456", source_url="https://test.com")

        data = source.to_dict()

        self.assertIn("id", data)
        self.assertEqual(data["source_hash"], "test_hash_456")
        self.assertEqual(data["source_url"], "https://test.com")
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_source_from_dict(self):
        """Тест создания из словаря"""
        test_id = str(uuid.uuid4())
        test_date = datetime(2024, 1, 1)

        data = {
            "id": test_id,
            "source_hash": "test_hash_789",
            "source_url": "https://from-dict.com",
            "source_date": test_date,
            "force_recheck": True,
            "created_at": test_date,
            "updated_at": test_date,
        }

        source = Source.from_dict(data)

        self.assertEqual(str(source.id), test_id)
        self.assertEqual(source.source_hash, "test_hash_789")
        self.assertEqual(source.source_url, "https://from-dict.com")
        self.assertEqual(source.source_date, test_date)
        self.assertTrue(source.force_recheck)


class TestCriterion(unittest.TestCase):
    """Тесты для модели Criterion"""

    def test_criterion_creation(self):
        """Тест создания критерия"""
        criterion = Criterion(
            id="test_criterion_1", criterion_text="Тестовый критерий", threshold=0.8
        )

        self.assertEqual(criterion.id, "test_criterion_1")
        self.assertEqual(criterion.criterion_text, "Тестовый критерий")
        self.assertEqual(criterion.threshold, 0.8)
        self.assertTrue(criterion.is_active)
        self.assertEqual(criterion.criteria_version, 1)

    def test_criterion_to_dict(self):
        """Тест преобразования в словарь"""
        criterion = Criterion(
            id="test_criterion_2", criterion_text="Другой критерий", threshold=0.7
        )

        data = criterion.to_dict()

        self.assertEqual(data["id"], "test_criterion_2")
        self.assertEqual(data["criterion_text"], "Другой критерий")
        self.assertEqual(data["threshold"], 0.7)
        self.assertTrue(data["is_active"])

    def test_criterion_from_dict(self):
        """Тест создания из словаря"""
        data = {
            "id": "test_criterion_3",
            "criterion_text": "Критерий из словаря",
            "criteria_version": 2,
            "is_active": False,
            "threshold": 0.9,
        }

        criterion = Criterion.from_dict(data)

        self.assertEqual(criterion.id, "test_criterion_3")
        self.assertEqual(criterion.criterion_text, "Критерий из словаря")
        self.assertEqual(criterion.criteria_version, 2)
        self.assertFalse(criterion.is_active)
        self.assertEqual(criterion.threshold, 0.9)


class TestEvent(unittest.TestCase):
    """Тесты для модели Event"""

    def test_event_creation(self):
        """Тест создания события"""
        event = Event(
            source_hash="event_hash_123",
            criterion_id="criterion_1",
            criterion_text="Критерий события",
            is_match=True,
            confidence=0.85,
            summary="Событие соответствует критерию",
            model_name="llama3:8b",
            latency_ms=1500,
        )

        self.assertIsNotNone(event.event_id)
        self.assertEqual(event.source_hash, "event_hash_123")
        self.assertEqual(event.criterion_id, "criterion_1")
        self.assertTrue(event.is_match)
        self.assertEqual(event.confidence, 0.85)
        self.assertEqual(event.model_name, "llama3:8b")
        self.assertEqual(event.latency_ms, 1500)

    def test_event_to_dict(self):
        """Тест преобразования в словарь"""
        event = Event(
            source_hash="event_hash_456", criterion_id="criterion_2", is_match=False, confidence=0.3
        )

        data = event.to_dict()

        self.assertIn("event_id", data)
        self.assertEqual(data["source_hash"], "event_hash_456")
        self.assertEqual(data["criterion_id"], "criterion_2")
        self.assertEqual(data["is_match"], 0)  # ClickHouse формат
        self.assertEqual(data["confidence"], 0.3)

    def test_event_from_dict(self):
        """Тест создания из словаря"""
        test_id = str(uuid.uuid4())

        data = {
            "event_id": test_id,
            "source_hash": "event_hash_789",
            "criterion_id": "criterion_3",
            "criterion_text": "Критерий из словаря",
            "is_match": 1,  # ClickHouse формат
            "confidence": 0.95,
            "summary": "Отличное совпадение",
            "model_name": "llama3:8b",
            "latency_ms": 2000,
        }

        event = Event.from_dict(data)

        self.assertEqual(str(event.event_id), test_id)
        self.assertEqual(event.source_hash, "event_hash_789")
        self.assertEqual(event.criterion_id, "criterion_3")
        self.assertTrue(event.is_match)
        self.assertEqual(event.confidence, 0.95)
        self.assertEqual(event.latency_ms, 2000)


class TestStats(unittest.TestCase):
    """Тесты для статистических моделей"""

    def test_criteria_stats(self):
        """Тест статистики по критериям"""
        stats = CriteriaStats(
            criterion_id="test_criterion",
            date=datetime(2024, 1, 1),
            total_events=100,
            matches=25,
            avg_confidence=0.75,
            avg_latency_ms=1200,
        )

        self.assertEqual(stats.criterion_id, "test_criterion")
        self.assertEqual(stats.total_events, 100)
        self.assertEqual(stats.matches, 25)
        self.assertEqual(stats.match_rate, 25.0)  # 25%
        self.assertEqual(stats.avg_confidence, 0.75)
        self.assertEqual(stats.avg_latency_ms, 1200)

    def test_source_stats(self):
        """Тест статистики по источникам"""
        stats = SourceStats(
            source_hash="test_source",
            source_url="https://example.com",
            date=datetime(2024, 1, 1),
            total_events=50,
            matches=10,
            avg_confidence=0.6,
        )

        self.assertEqual(stats.source_hash, "test_source")
        self.assertEqual(stats.source_url, "https://example.com")
        self.assertEqual(stats.total_events, 50)
        self.assertEqual(stats.matches, 10)
        self.assertEqual(stats.match_rate, 20.0)  # 20%
        self.assertEqual(stats.avg_confidence, 0.6)

    def test_stats_zero_division(self):
        """Тест деления на ноль в статистике"""
        stats = CriteriaStats(
            criterion_id="empty_criterion",
            date=datetime(2024, 1, 1),
            total_events=0,
            matches=0,
            avg_confidence=0.0,
            avg_latency_ms=0,
        )

        self.assertEqual(stats.match_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
