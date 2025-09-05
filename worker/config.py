"""
Конфигурация для worker сервиса
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Redis настройки
    redis_url: str = "redis://redis:6379/0"
    
    # PostgreSQL настройки
    postgres_url: str = "postgresql://postgres:postgres@pg:5432/pharma_analysis"
    
    # ClickHouse настройки
    clickhouse_url: str = "http://ch:8123"
    clickhouse_database: str = "default"
    
    # Ollama настройки
    ollama_url: str = "http://llm:11434"
    ollama_model: str = "llama3:8b"
    num_ctx: int = 8192
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 512
    
    # Worker настройки
    worker_concurrency: int = 1
    task_timeout: int = 300  # секунды
    
    # Логирование
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Создаем глобальный экземпляр настроек
settings = Settings()
