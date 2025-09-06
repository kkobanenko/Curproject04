"""
Сервис для поиска и обработки медицинских новостей
Поддерживает различные источники: PubMed, BioMCP, Web Search
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List

from database import PostgresManager
from models import News

logger = logging.getLogger(__name__)


class NewsService:
    """Сервис для работы с медицинскими новостями"""

    def __init__(self):
        """Инициализация сервиса"""
        self.postgres_manager = PostgresManager()

    def search_medical_news(
        self, query: str, sources: List[str], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Поиск медицинских новостей через различные источники

        Args:
            query: Поисковый запрос
            sources: Список источников для поиска ['pubmed', 'web_search', 'biomcp']
            limit: Максимальное количество результатов на источник
        """
        all_news = []

        for source in sources:
            try:
                if source == "pubmed":
                    news_items = self._search_pubmed(query, limit)
                elif source == "biomcp":
                    news_items = self._search_biomcp(query, limit)
                elif source == "web_search":
                    news_items = self._search_web(query, limit)
                else:
                    logger.warning(f"Неизвестный источник: {source}")
                    continue

                all_news.extend(news_items)
                logger.info(f"Найдено {len(news_items)} новостей из источника {source}")

            except Exception as e:
                logger.error(f"Ошибка поиска в источнике {source}: {e}")
                continue

        logger.info(f"Всего найдено {len(all_news)} новостей из всех источников")
        return all_news

    def _search_pubmed(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Поиск в PubMed через BioMCP"""
        try:
            # Используем BioMCP для поиска в PubMed
            # Это будет реализовано через MCP инструменты
            logger.info(f"Поиск в PubMed по запросу: {query}")

            # Здесь будет вызов BioMCP инструментов
            # Пока возвращаем пустой список
            return []

        except Exception as e:
            logger.error(f"Ошибка поиска в PubMed: {e}")
            return []

    def _search_biomcp(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Поиск через BioMCP (статьи и клинические исследования)"""
        try:
            logger.info(f"Поиск через BioMCP по запросу: {query}")

            # Здесь будет вызов BioMCP инструментов
            # Пока возвращаем пустой список
            return []

        except Exception as e:
            logger.error(f"Ошибка поиска через BioMCP: {e}")
            return []

    def _search_web(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Поиск медицинских новостей через веб-поиск"""
        try:
            # Импортируем web_search здесь, чтобы избежать циклических импортов
            from web_search import web_search

            # Формируем поисковый запрос с медицинскими терминами
            medical_query = f"{query} медицинские новости клинические исследования 2024"

            logger.info(f"Поиск медицинских новостей по запросу: {medical_query}")

            # Выполняем поиск
            search_results = web_search(medical_query)

            if not search_results or not search_results.get("results"):
                logger.warning("Результаты поиска новостей не найдены")
                return []

            # Обрабатываем результаты поиска
            news_items = []
            # Ограничиваем количество
            results = search_results["results"][:limit]

            for result in results:
                try:
                    # Извлекаем информацию из результата поиска
                    title = result.get("title", "Без заголовка")
                    url = result.get("url", "")
                    content = result.get("text", "")

                    # Очищаем и форматируем контент
                    content = self._clean_content(content)

                    # Проверяем, что новость еще не была сохранена
                    existing_news = self.postgres_manager.get_news_by_url(url)
                    if existing_news:
                        logger.info(f"Новость уже существует: {url}")
                        continue

                    # Создаем объект новости
                    news = News(
                        title=title,
                        url=url,
                        # Первый килобайт
                        content=content[:1024] if content else None,
                        source="web_search",
                        search_query=query,
                        published_date=datetime.utcnow(),  # Используем текущую дату
                    )

                    # Сохраняем новость в базу данных
                    if self.postgres_manager.create_news(news):
                        news_items.append(
                            {
                                "id": str(news.id),
                                "title": news.title,
                                "url": news.url,
                                "content": news.content,
                                "source": news.source,
                                "search_query": news.search_query,
                                "created_at": news.created_at,
                            }
                        )
                        logger.info(f"Новость сохранена: {news.title}")
                    else:
                        logger.error(f"Ошибка сохранения новости: {news.title}")

                except Exception as e:
                    logger.error(f"Ошибка обработки результата поиска: {e}")
                    continue

            return news_items

        except Exception as e:
            logger.error(f"Ошибка поиска медицинских новостей: {e}")
            return []

    def _clean_content(self, content: str) -> str:
        """Очистка и форматирование контента новости"""
        if not content:
            return ""

        # Удаляем лишние пробелы и переносы строк
        content = re.sub(r"\s+", " ", content)

        # Удаляем HTML теги (если есть)
        content = re.sub(r"<[^>]+>", "", content)

        # Ограничиваем длину контента
        if len(content) > 1024:
            content = content[:1021] + "..."

        return content.strip()

    def get_available_sources(self) -> List[Dict[str, str]]:
        """Получение списка доступных источников новостей"""
        return [
            {
                "id": "web_search",
                "name": "Web Search",
                "description": "Поиск новостей через веб-поиск",
            },
            {
                "id": "medical_journals",
                "name": "Медицинские журналы",
                "description": "Поиск в медицинских журналах (планируется)",
            },
            {
                "id": "news_agencies",
                "name": "Новостные агентства",
                "description": "Поиск в новостных агентствах (планируется)",
            },
        ]

    def get_news_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение истории найденных новостей"""
        return self.postgres_manager.get_news(limit)
