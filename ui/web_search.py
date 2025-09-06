"""
Простой модуль для веб-поиска
Временная реализация для демонстрации функциональности
"""

import logging
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


def web_search(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Простой веб-поиск через DuckDuckGo API

    Args:
        query: Поисковый запрос
        limit: Максимальное количество результатов

    Returns:
        Словарь с результатами поиска
    """
    try:
        logger.info(f"Выполняем веб-поиск по запросу: {query}")

        # Используем DuckDuckGo Instant Answer API
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}

        # Выполняем запрос
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Формируем результаты в нужном формате
        results = []

        # Добавляем основной результат, если есть
        if data.get("Abstract"):
            results.append(
                {
                    "title": data.get("Heading", "Результат поиска"),
                    "url": data.get("AbstractURL", ""),
                    "text": data.get("Abstract", ""),
                    "source": "DuckDuckGo",
                }
            )

        # Добавляем связанные темы
        for topic in data.get("RelatedTopics", [])[: limit - 1]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(
                    {
                        "title": (
                            topic.get("FirstURL", "").split("/")[-1]
                            if topic.get("FirstURL")
                            else "Связанная тема"
                        ),
                        "url": topic.get("FirstURL", ""),
                        "text": topic.get("Text", ""),
                        "source": "DuckDuckGo",
                    }
                )

        # Если результатов мало, добавляем заглушки для демонстрации
        while len(results) < min(limit, 5):
            results.append(
                {
                    "title": f"Медицинская новость по теме: {query}",
                    "url": f"https://example.com/news/{len(results)+1}",
                    "text": (
                        f'Это демонстрационный результат поиска по теме "{query}". '
                        f"В реальной реализации здесь будет актуальная медицинская информация."
                    ),
                    "source": "Demo",
                }
            )

        return {"results": results[:limit], "query": query, "total_results": len(results)}

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка веб-поиска: {e}")
        # Возвращаем демонстрационные результаты при ошибке
        return {
            "results": [
                {
                    "title": f'Демо: Медицинская новость по теме "{query}"',
                    "url": "https://example.com/demo-news",
                    "text": (
                        f'Это демонстрационный результат поиска по теме "{query}". '
                        f"В реальной реализации здесь будет актуальная медицинская "
                        f"информация из PubMed, медицинских журналов и других источников."
                    ),
                    "source": "Demo",
                }
            ],
            "query": query,
            "total_results": 1,
        }
    except Exception as e:
        logger.error(f"Неожиданная ошибка веб-поиска: {e}")
        return {"results": [], "query": query, "total_results": 0}
