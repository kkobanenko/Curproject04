"""
Конфигурация pytest с общими фикстурами
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch
import redis
import psycopg2
from clickhouse_driver import Client

# Фикстуры для тестирования

@pytest.fixture
def mock_redis():
    """Мок Redis клиента"""
    with patch('redis.Redis') as mock:
        mock_instance = Mock()
        mock.from_url.return_value = mock_instance
        mock_instance.ping.return_value = True
        mock_instance.lpush.return_value = 1
        mock_instance.lrange.return_value = []
        mock_instance.llen.return_value = 0
        yield mock_instance

@pytest.fixture
def mock_postgres():
    """Мок PostgreSQL соединения"""
    with patch('psycopg2.connect') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        
        # Создаем мок для cursor с контекстным менеджером
        cursor_mock = Mock()
        cursor_mock.__enter__ = Mock(return_value=cursor_mock)
        cursor_mock.__exit__ = Mock(return_value=None)
        cursor_mock.execute = Mock(return_value=None)
        cursor_mock.fetchall = Mock(return_value=[])
        
        mock_instance.cursor.return_value = cursor_mock
        mock_instance.close = Mock()
        
        yield mock_instance

@pytest.fixture
def mock_postgres_manager():
    """Мок PostgreSQL менеджера"""
    with patch('ui.database.postgres_manager') as mock:
        mock_instance = Mock()
        
        # Мок для get_connection с контекстным менеджером
        conn_mock = Mock()
        conn_mock.__enter__ = Mock(return_value=conn_mock)
        conn_mock.__exit__ = Mock(return_value=None)
        
        cursor_mock = Mock()
        cursor_mock.__enter__ = Mock(return_value=cursor_mock)
        cursor_mock.__exit__ = Mock(return_value=None)
        cursor_mock.execute = Mock(return_value=None)
        cursor_mock.fetchall = Mock(return_value=[])
        cursor_mock.fetchone = Mock(return_value=None)
        
        conn_mock.cursor.return_value = cursor_mock
        mock_instance.get_connection.return_value = conn_mock
        
        # Мок для методов менеджера
        mock_instance.get_source_by_hash.return_value = None
        mock_instance.create_source.return_value = Mock(id=1)
        mock_instance.get_active_criteria.return_value = []
        mock_instance.save_event.return_value = True
        
        yield mock_instance

@pytest.fixture
def mock_clickhouse():
    """Мок ClickHouse клиента"""
    with patch('clickhouse_driver.Client') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        mock_instance.execute.return_value = []
        yield mock_instance

@pytest.fixture
def mock_clickhouse_manager():
    """Мок ClickHouse менеджера"""
    with patch('ui.database.clickhouse_manager') as mock:
        mock_instance = Mock()
        mock_instance.insert_event.return_value = True
        yield mock_instance

@pytest.fixture
def mock_ollama():
    """Мок Ollama API"""
    with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
        # Мок для health check
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}
        
        # Мок для анализа текста
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "model": "llama3:8b",
            "created_at": "2024-12-30T19:30:00Z",
            "response": "Этот текст соответствует критериям фармацевтического анализа.",
            "done": True,
            "context": [1, 2, 3],
            "total_duration": 1500000000,
            "load_duration": 500000000,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 800000000,
            "eval_count": 20,
            "eval_duration": 1200000000
        }
        
        yield mock_get, mock_post

@pytest.fixture
def sample_text_data():
    """Образец текстовых данных для тестирования"""
    return {
        "text": "Аспирин является эффективным препаратом для лечения головной боли.",
        "source_url": "https://example.com/aspirin",
        "source_date": "2024-12-30"
    }

@pytest.fixture
def sample_criteria():
    """Образец критериев для тестирования"""
    return [
        {
            "criterion_id": "crit_001",
            "criterion_text": "Препарат для лечения головной боли",
            "is_active": True
        },
        {
            "criterion_id": "crit_002", 
            "criterion_text": "Противовоспалительное средство",
            "is_active": True
        }
    ]

@pytest.fixture
def sample_events():
    """Образец событий для тестирования"""
    return [
        {
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "source_hash": "abc123",
            "source_url": "https://example.com/1",
            "criterion_id": "crit_001",
            "is_match": True,
            "confidence": 0.85,
            "summary": "Текст соответствует критерию",
            "model_name": "llama3:8b",
            "latency_ms": 1500
        },
        {
            "event_id": "550e8400-e29b-41d4-a716-446655440001",
            "source_hash": "def456",
            "source_url": "https://example.com/2",
            "criterion_id": "crit_002",
            "is_match": False,
            "confidence": 0.25,
            "summary": "Текст не соответствует критерию",
            "model_name": "llama3:8b",
            "latency_ms": 1200
        }
    ]

@pytest.fixture
def temp_db_file():
    """Временный файл для тестовой базы данных"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"test": "data"}, f)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def mock_streamlit():
    """Мок Streamlit функций"""
    with patch('streamlit.set_page_config'), \
         patch('streamlit.markdown'), \
         patch('streamlit.sidebar'), \
         patch('streamlit.selectbox'), \
         patch('streamlit.text_area'), \
         patch('streamlit.text_input'), \
         patch('streamlit.date_input'), \
         patch('streamlit.checkbox'), \
         patch('streamlit.button'), \
         patch('streamlit.success'), \
         patch('streamlit.error'), \
         patch('streamlit.info'), \
         patch('streamlit.warning'), \
         patch('streamlit.dataframe'), \
         patch('streamlit.plotly_chart'), \
         patch('streamlit.metric'), \
         patch('streamlit.progress'), \
         patch('streamlit.empty'):
        yield
