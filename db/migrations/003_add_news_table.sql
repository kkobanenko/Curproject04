-- Миграция для добавления таблицы новостей
-- Создание таблицы news для хранения медицинских новостей

CREATE TABLE IF NOT EXISTS news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    url TEXT,
    content TEXT,
    source VARCHAR(100) NOT NULL,
    search_query TEXT NOT NULL,
    published_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для оптимизации поиска
CREATE INDEX IF NOT EXISTS idx_news_source ON news(source);
CREATE INDEX IF NOT EXISTS idx_news_search_query ON news(search_query);
CREATE INDEX IF NOT EXISTS idx_news_created_at ON news(created_at);
CREATE INDEX IF NOT EXISTS idx_news_published_date ON news(published_date);

-- Создание уникального индекса по URL для предотвращения дублирования
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_url_unique ON news(url) WHERE url IS NOT NULL;

-- Комментарии к таблице и колонкам
COMMENT ON TABLE news IS 'Таблица для хранения медицинских новостей';
COMMENT ON COLUMN news.id IS 'Уникальный идентификатор новости';
COMMENT ON COLUMN news.title IS 'Заголовок новости';
COMMENT ON COLUMN news.url IS 'URL источника новости';
COMMENT ON COLUMN news.content IS 'Содержимое новости (первый килобайт)';
COMMENT ON COLUMN news.source IS 'Источник новости (pubmed, web_search, etc.)';
COMMENT ON COLUMN news.search_query IS 'Поисковый запрос, по которому была найдена новость';
COMMENT ON COLUMN news.published_date IS 'Дата публикации новости';
COMMENT ON COLUMN news.created_at IS 'Дата создания записи в системе';
COMMENT ON COLUMN news.updated_at IS 'Дата последнего обновления записи';
