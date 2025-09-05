"""
API клиент для работы с Ollama LLM сервисом
Предоставляет интерфейс для анализа текста по критериям
"""

import json
import time
import logging
from typing import Dict, Any, Optional
import requests
from dataclasses import dataclass

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Результат анализа текста"""
    is_match: bool
    confidence: float
    summary: str
    model_name: str
    latency_ms: int


class OllamaClient:
    """Клиент для работы с Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Инициализация клиента
        
        Args:
            base_url: URL Ollama сервиса
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 120  # Увеличиваем таймаут до 2 минут
        
    def _make_request(self, endpoint: str, data: Dict[str, Any] = None, method: str = "POST") -> Dict[str, Any]:
        """
        Выполнение запроса к Ollama API
        
        Args:
            endpoint: API endpoint
            data: Данные для запроса
            method: HTTP метод (GET или POST)
            
        Returns:
            Ответ от API
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            else:
                response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Ollama: {e}")
            raise
    
    def analyze_text(self, 
                    text: str, 
                    criterion_text: str,
                    model: str = "llama3:8b",
                    temperature: float = 0.7,
                    top_p: float = 0.9,
                    top_k: int = 40,
                    max_tokens: int = 512) -> AnalysisResult:
        """
        Анализ текста по заданному критерию
        
        Args:
            text: Текст для анализа
            criterion_text: Текст критерия на русском языке
            model: Название модели
            temperature: Температура генерации
            top_p: Top-p параметр
            top_k: Top-k параметр
            max_tokens: Максимальное количество токенов
            
        Returns:
            Результат анализа
        """
        start_time = time.time()
        
        # Формируем промпт для анализа
        system_prompt = """Ты - эксперт по анализу текстов на русском языке. 
Твоя задача - определить, соответствует ли текст заданному критерию.

Отвечай строго в формате JSON:
{
    "is_match": true/false,
    "confidence": 0.0-1.0,
    "summary": "краткое объяснение на русском языке"
}

is_match - соответствует ли текст критерию
confidence - уверенность в ответе (0.0-1.0)
summary - краткое объяснение на русском языке"""

        user_prompt = f"""Критерий: {criterion_text}

Текст для анализа: {text}

Проанализируй текст и определи, соответствует ли он критерию."""

        # Данные для запроса к Ollama
        request_data = {
            "model": model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "keep_alive": "5m",  # Держим модель в памяти 5 минут
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "num_predict": max_tokens
            }
        }
        
        try:
            # Выполняем запрос
            response = self._make_request("/api/generate", request_data)
            
            # Извлекаем ответ
            response_text = response.get("response", "")
            
            # Парсим JSON ответ
            try:
                result_data = json.loads(response_text)
                is_match = result_data.get("is_match", False)
                confidence = float(result_data.get("confidence", 0.0))
                summary = result_data.get("summary", "")
                
                # Проверяем валидность confidence
                confidence = max(0.0, min(1.0, confidence))
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Ошибка парсинга JSON ответа: {e}")
                # Fallback значения
                is_match = False
                confidence = 0.0
                summary = "Ошибка анализа ответа модели"
            
            # Вычисляем время выполнения
            latency_ms = int((time.time() - start_time) * 1000)
            
            return AnalysisResult(
                is_match=is_match,
                confidence=confidence,
                summary=summary,
                model_name=model,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            logger.error(f"Ошибка анализа текста: {e}")
            # Возвращаем результат с ошибкой
            latency_ms = int((time.time() - start_time) * 1000)
            return AnalysisResult(
                is_match=False,
                confidence=0.0,
                summary=f"Ошибка анализа: {str(e)}",
                model_name=model,
                latency_ms=latency_ms
            )
    
    def health_check(self) -> bool:
        """
        Проверка здоровья сервиса
        
        Returns:
            True если сервис работает
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка health check: {e}")
            return False
    
    def get_models(self) -> list:
        """
        Получение списка доступных моделей
        
        Returns:
            Список моделей
        """
        try:
            response = self._make_request("/api/tags", method="GET")
            return response.get("models", [])
        except Exception as e:
            logger.error(f"Ошибка получения моделей: {e}")
            return []
