-- DDL для инициализации ClickHouse схемы
-- Создает таблицу событий для аналитики

-- Создаем базу данных если не существует
CREATE DATABASE IF NOT EXISTS pharma_analysis;

-- Используем базу данных
USE pharma_analysis;

-- Таблица событий (аналитика)
CREATE TABLE IF NOT EXISTS events (
    event_id UUID,
    source_hash String,
    source_url Nullable(String),
    source_date Nullable(DateTime64(3)),
    ingest_ts DateTime64(3),
    criterion_id String,
    criterion_text String,
    is_match UInt8,
    confidence Float32,
    summary String,
    model_name String,
    latency_ms UInt32,
    created_at DateTime64(3) DEFAULT now64()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(ingest_ts)
ORDER BY (ingest_ts, source_hash)
SETTINGS index_granularity = 8192;

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_events_criterion_id ON events(criterion_id) TYPE bloom_filter GRANULARITY 1;
CREATE INDEX IF NOT EXISTS idx_events_is_match ON events(is_match) TYPE bloom_filter GRANULARITY 1;
CREATE INDEX IF NOT EXISTS idx_events_source_hash ON events(source_hash) TYPE bloom_filter GRANULARITY 1;

-- Комментарии к таблице
ALTER TABLE events COMMENT COLUMN event_id = 'Уникальный идентификатор события';
ALTER TABLE events COMMENT COLUMN source_hash = 'SHA-256 хеш нормализованного текста';
ALTER TABLE events COMMENT COLUMN is_match = 'Флаг соответствия критерию (0/1)';
ALTER TABLE events COMMENT COLUMN confidence = 'Уверенность модели (0.0-1.0)';
ALTER TABLE events COMMENT COLUMN latency_ms = 'Время выполнения анализа в миллисекундах';
