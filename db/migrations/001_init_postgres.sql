-- Миграция 001: Инициализация PostgreSQL схемы
-- Создает таблицы для источников и критериев

-- Включаем расширение для UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица источников (OLTP)
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_hash TEXT UNIQUE NOT NULL,
    source_url TEXT NULL,
    source_date TIMESTAMPTZ NULL,
    ingest_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    force_recheck BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Таблица критериев
CREATE TABLE IF NOT EXISTS criteria (
    id TEXT PRIMARY KEY,
    criterion_text TEXT NOT NULL,
    criteria_version INT NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    threshold REAL NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_sources_hash ON sources(source_hash);
CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(source_url);
CREATE INDEX IF NOT EXISTS idx_sources_date ON sources(source_date);
CREATE INDEX IF NOT EXISTS idx_sources_ingest_ts ON sources(ingest_ts);

CREATE INDEX IF NOT EXISTS idx_criteria_active ON criteria(is_active);
CREATE INDEX IF NOT EXISTS idx_criteria_version ON criteria(criteria_version);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_sources_updated_at 
    BEFORE UPDATE ON sources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_criteria_updated_at 
    BEFORE UPDATE ON criteria 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Seed данные: начальный критерий
INSERT INTO criteria (id, criterion_text, criteria_version, is_active, threshold) 
VALUES (
    'molecules_pretrial_v1',
    'Идет ли речь о предварительных испытаниях молекул (МНН) из списка: интерферон человеческий, гиотриф, фулвестрант?',
    1,
    TRUE,
    0.7
) ON CONFLICT (id) DO NOTHING;

-- Комментарии к таблицам
COMMENT ON TABLE sources IS 'Таблица источников текста для анализа';
COMMENT ON TABLE criteria IS 'Таблица критериев для анализа текста';
COMMENT ON COLUMN sources.source_hash IS 'SHA-256 хеш нормализованного текста';
COMMENT ON COLUMN sources.force_recheck IS 'Флаг принудительной перепроверки';
COMMENT ON COLUMN criteria.threshold IS 'Порог уверенности для срабатывания критерия';
