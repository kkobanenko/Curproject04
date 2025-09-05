#!/usr/bin/env python3
"""
Тест соединения с ClickHouse
"""

import requests
import sys

def test_clickhouse():
    """Тестирование соединения с ClickHouse"""
    
    # URL для ClickHouse
    url = "http://ch:8123"
    
    try:
        # Проверяем ping
        response = requests.get(f"{url}/ping")
        print(f"Ping status: {response.status_code}")
        print(f"Ping response: {response.text}")
        
        # Проверяем запрос к базе данных
        response = requests.get(f"{url}/", params={
            'query': 'SELECT COUNT(*) FROM events',
            'database': 'pharma_analysis'
        })
        print(f"Query status: {response.status_code}")
        print(f"Query response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_clickhouse()
    sys.exit(0 if success else 1)
