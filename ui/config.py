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
    postgres_db: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    
    # ClickHouse настройки
    clickhouse_url: str = "http://ch:8123"
    clickhouse_database: str = "default"
    clickhouse_db: Optional[str] = None
    
    # Ollama настройки
    ollama_url: Optional[str] = None
    ollama_model: Optional[str] = None
    num_ctx: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    
    # Worker настройки
    worker_url: str = "http://localhost:8000"
    worker_concurrency: Optional[int] = None
    task_timeout: Optional[int] = None
    
    # UI настройки
    page_title: str = "Анализ фармацевтических текстов"
    page_icon: str = "💊"
    
    # Логирование
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Игнорируем дополнительные поля


# Создаем глобальный экземпляр настроек
settings = Settings()
