"""
Основной файл worker сервиса
RQ worker для обработки задач анализа текста
"""

import os
import sys
import logging
import structlog
from flask import Flask, jsonify
from rq import Worker, Queue, Connection
from redis import Redis
import threading
import time

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from tasks import analyze_text_task, health_check_task

# Настройка логирования
if settings.log_format == "json":
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
else:
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)


class HealthCheckServer:
    """Простой HTTP сервер для health check"""
    
    def __init__(self, port=8000):
        self.port = port
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """Настройка маршрутов"""
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            try:
                # Выполняем health check
                result = health_check_task()
                return jsonify(result)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return jsonify({
                    'status': 'error',
                    'reason': str(e),
                    'timestamp': time.time()
                }), 500
        
        @self.app.route('/')
        def root():
            """Корневой endpoint"""
            return jsonify({
                'service': 'pharma-analysis-worker',
                'status': 'running',
                'timestamp': time.time()
            })
    
    def start(self):
        """Запуск сервера"""
        logger.info(f"Запускаем health check сервер на порту {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)


def start_health_server():
    """Запуск health check сервера в отдельном потоке"""
    health_server = HealthCheckServer()
    health_server.start()


def main():
    """Основная функция worker"""
    logger.info("Запуск worker сервиса")
    
    # Запускаем health check сервер в отдельном потоке
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Подключаемся к Redis
    redis_conn = Redis.from_url(settings.redis_url)
    
    try:
        # Проверяем подключение к Redis
        redis_conn.ping()
        logger.info("Подключение к Redis установлено")
    except Exception as e:
        logger.error(f"Ошибка подключения к Redis: {e}")
        sys.exit(1)
    
    # Создаем очередь
    queue = Queue('text_analysis', connection=redis_conn)
    
    # Создаем worker
    worker = Worker(
        [queue],
        connection=redis_conn,
        name=f'pharma-worker-{os.getpid()}'
    )
    
    logger.info(f"Worker {worker.name} запущен")
    logger.info(f"Ожидаем задачи в очереди: {queue.name}")
    logger.info(f"Таймаут задач: {settings.task_timeout} секунд")
    
    try:
        # Запускаем worker
        worker.work(
            with_scheduler=True,
            logging_level=getattr(logging, settings.log_level)
        )
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка worker: {e}", exc_info=True)
    finally:
        logger.info("Worker остановлен")


if __name__ == '__main__':
    main()
