"""
Кастомный RQ Worker для передачи job_id в задачи
"""

import logging
import os
import sys
from typing import Any

from rq import Worker
from rq.job import Job
from rq.queue import Queue

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class CustomWorker(Worker):
    """Кастомный worker, который передает job_id в задачи"""

    def perform_job(self, job: Job, queue: "Queue") -> Any:
        """
        Выполнение задачи с передачей job_id

        Args:
            job: Задача для выполнения
            queue: Очередь задач

        Returns:
            Результат выполнения задачи
        """
        # Получаем функцию и аргументы
        func = job.func
        args = job.args or []
        kwargs = job.kwargs or {}

        # Если это задача анализа текста, добавляем job_id
        if func.__name__ == "analyze_text_task":
            kwargs["job_id"] = job.id
            logger.info(f"Добавляем job_id {job.id} в задачу {func.__name__}")

        # Выполняем задачу с обновленными аргументами
        return func(*args, **kwargs)
