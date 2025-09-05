-- Миграция 002: Добавление поля text в таблицу sources
-- Сохраняет первый килобайт текста для возможности просмотра

-- Добавляем поле text в таблицу sources
ALTER TABLE sources ADD COLUMN IF NOT EXISTS text TEXT NULL;

-- Добавляем комментарий к полю
COMMENT ON COLUMN sources.text IS 'Первый килобайт исходного текста для просмотра';

-- Создаем индекс для оптимизации поиска по тексту (опционально)
CREATE INDEX IF NOT EXISTS idx_sources_text ON sources USING gin(to_tsvector('russian', text)) WHERE text IS NOT NULL;
