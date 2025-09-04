"""
Конфигурация для UI сервиса
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Redis настройки
    redis_url: str = "redis://localhost:6379/0"
    
    # PostgreSQL настройки
    postgres_url: str = "postgresql://postgres:postgres@localhost:5432/pharma_analysis"
    
    # ClickHouse настройки
    clickhouse_url: str = "http://localhost:8123"
    clickhouse_database: str = "pharma_analysis"
    
    # Worker настройки
    worker_url: str = "http://localhost:8000"
    
    # UI настройки
    page_title: str = "Анализ фармацевтических текстов"
    page_icon: str = "💊"
    
    # Логирование
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Создаем глобальный экземпляр настроек
settings = Settings()
