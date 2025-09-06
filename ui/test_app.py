"""
Тесты для UI приложения
"""

import unittest

import pandas as pd


class TestDataProcessing(unittest.TestCase):
    """Тесты обработки данных"""

    def test_dataframe_creation_from_events(self):
        """Тест создания DataFrame из событий"""
        events = [
            {
                "criterion_id": "test_criterion_1",
                "is_match": True,
                "confidence": 0.8,
                "summary": "Совпадение найдено",
                "latency_ms": 1500,
            },
            {
                "criterion_id": "test_criterion_2",
                "is_match": False,
                "confidence": 0.3,
                "summary": "Совпадение не найдено",
                "latency_ms": 1200,
            },
        ]

        try:
            df = pd.DataFrame(events)
            self.assertEqual(len(df), 2)
            self.assertEqual(df["criterion_id"].iloc[0], "test_criterion_1")
            self.assertTrue(df["is_match"].iloc[0])
            self.assertFalse(df["is_match"].iloc[1])
        except Exception as e:
            self.fail(f"Создание DataFrame вызвало ошибку: {e}")

    def test_dataframe_filtering(self):
        """Тест фильтрации DataFrame"""
        events = [
            {
                "criterion_id": "test_criterion_1",
                "is_match": True,
                "confidence": 0.8,
                "summary": "Совпадение найдено",
            },
            {
                "criterion_id": "test_criterion_2",
                "is_match": False,
                "confidence": 0.3,
                "summary": "Совпадение не найдено",
            },
            {
                "criterion_id": "test_criterion_3",
                "is_match": True,
                "confidence": 0.9,
                "summary": "Отличное совпадение",
            },
        ]

        df = pd.DataFrame(events)

        # Фильтруем только совпадения
        matches_only = df[df["is_match"]]

        self.assertEqual(len(matches_only), 2)
        self.assertTrue(all(matches_only["is_match"]))

    def test_dataframe_metrics_calculation(self):
        """Тест вычисления метрик из DataFrame"""
        events = [
            {
                "criterion_id": "test_criterion_1",
                "is_match": True,
                "confidence": 0.8,
                "latency_ms": 1500,
            },
            {
                "criterion_id": "test_criterion_2",
                "is_match": False,
                "confidence": 0.3,
                "latency_ms": 1200,
            },
            {
                "criterion_id": "test_criterion_3",
                "is_match": True,
                "confidence": 0.9,
                "latency_ms": 1800,
            },
        ]

        df = pd.DataFrame(events)

        # Вычисляем метрики
        total_events = len(df)
        matches = df["is_match"].sum()
        avg_confidence = df["confidence"].mean()
        avg_latency = df["latency_ms"].mean()

        self.assertEqual(total_events, 3)
        self.assertEqual(matches, 2)
        self.assertAlmostEqual(avg_confidence, 0.67, places=2)
        self.assertAlmostEqual(avg_latency, 1500.0, places=1)


class TestDataValidation(unittest.TestCase):
    """Тесты валидации данных"""

    def test_valid_event_data(self):
        """Тест валидных данных события"""
        event = {
            "criterion_id": "test_criterion_1",
            "is_match": True,
            "confidence": 0.8,
            "summary": "Совпадение найдено",
            "latency_ms": 1500,
        }

        # Проверяем наличие обязательных полей
        required_fields = ["criterion_id", "is_match", "confidence", "summary", "latency_ms"]
        for field in required_fields:
            self.assertIn(field, event)

        # Проверяем типы данных
        self.assertIsInstance(event["criterion_id"], str)
        self.assertIsInstance(event["is_match"], bool)
        self.assertIsInstance(event["confidence"], float)
        self.assertIsInstance(event["summary"], str)
        self.assertIsInstance(event["latency_ms"], int)

        # Проверяем диапазоны значений
        self.assertGreaterEqual(event["confidence"], 0.0)
        self.assertLessEqual(event["confidence"], 1.0)
        self.assertGreaterEqual(event["latency_ms"], 0)

    def test_invalid_confidence_values(self):
        """Тест некорректных значений уверенности"""
        invalid_events = [
            {"confidence": -0.1},  # Отрицательное значение
            {"confidence": 1.1},  # Больше 1.0
            {"confidence": "invalid"},  # Не число
        ]

        for event in invalid_events:
            with self.assertRaises((ValueError, TypeError)):
                # Попытка создать DataFrame с некорректными данными
                df = pd.DataFrame([event])
                # Проверка диапазона
                if df["confidence"].iloc[0] < 0 or df["confidence"].iloc[0] > 1:
                    raise ValueError("Confidence out of range")


class TestDataTransformation(unittest.TestCase):
    """Тесты преобразования данных"""

    def test_date_conversion(self):
        """Тест конвертации дат"""
        events_with_dates = [
            {"ingest_ts": "2024-01-01 10:00:00", "criterion_id": "test_1", "is_match": True},
            {"ingest_ts": "2024-01-02 11:00:00", "criterion_id": "test_2", "is_match": False},
        ]

        df = pd.DataFrame(events_with_dates)

        # Конвертируем строки дат в datetime
        df["ingest_ts"] = pd.to_datetime(df["ingest_ts"])

        # Проверяем, что конвертация прошла успешно
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["ingest_ts"]))

        # Проверяем, что даты корректные
        self.assertEqual(df["ingest_ts"].dt.year.iloc[0], 2024)
        self.assertEqual(df["ingest_ts"].dt.month.iloc[0], 1)
        self.assertEqual(df["ingest_ts"].dt.day.iloc[0], 1)

    def test_boolean_conversion(self):
        """Тест конвертации булевых значений"""
        events_with_ints = [
            {"criterion_id": "test_1", "is_match": 1, "confidence": 0.8},  # ClickHouse формат
            {"criterion_id": "test_2", "is_match": 0, "confidence": 0.3},  # ClickHouse формат
        ]

        df = pd.DataFrame(events_with_ints)

        # Конвертируем int в bool
        df["is_match"] = df["is_match"].astype(bool)

        # Проверяем конвертацию
        self.assertTrue(df["is_match"].iloc[0])
        self.assertFalse(df["is_match"].iloc[1])


if __name__ == "__main__":
    unittest.main()
