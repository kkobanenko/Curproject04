# Документация переменных окружения

## 📋 Обзор

Этот документ описывает все переменные окружения, используемые в системе анализа фармацевтических текстов. Все настройки можно изменить через файл `.env` или переменные окружения Docker.

## 🗄️ База данных

### PostgreSQL

| Переменная | Описание | Значение по умолчанию | Обязательная |
|------------|----------|----------------------|--------------|
| `POSTGRES_DB` | Имя базы данных | `pharma_analysis` | ✅ |
| `POSTGRES_USER` | Пользователь БД | `postgres` | ✅ |
| `POSTGRES_PASSWORD` | Пароль БД | `postgres` | ✅ |
| `POSTGRES_URL` | Полный URL подключения | `postgresql://postgres:postgres@pg:5436/pharma_analysis` | ✅ |

**Пример настройки:**
```bash
POSTGRES_DB=pharma_analysis
POSTGRES_USER=pharma_user
POSTGRES_PASSWORD=secure_password_123
POSTGRES_URL=postgresql://pharma_user:secure_password_123@pg:5436/pharma_analysis
```

**Примечания:**
- URL должен соответствовать настройкам пользователя и пароля
- Порт 5436 используется для избежания конфликтов с локальным PostgreSQL
- База данных автоматически создается при первом запуске

### ClickHouse

| Переменная | Описание | Значение по умолчанию | Обязательная |
|------------|----------|----------------------|--------------|
| `CLICKHOUSE_URL` | HTTP URL ClickHouse | `http://ch:8127` | ✅ |
| `CLICKHOUSE_DB` | Имя базы данных | `pharma_analysis` | ✅ |
| `CLICKHOUSE_USER` | Пользователь БД | `default` | ❌ |
| `CLICKHOUSE_PASSWORD` | Пароль БД | (пустой) | ❌ |

**Пример настройки:**
```bash
CLICKHOUSE_URL=http://ch:8127
CLICKHOUSE_DB=pharma_analysis
CLICKHOUSE_USER=analytics_user
CLICKHOUSE_PASSWORD=clickhouse_password
```

**Примечания:**
- ClickHouse работает без пароля по умолчанию
- Порт 8127 используется для HTTP API
- Порт 9004 используется для native протокола

## 🔄 Redis

| Переменная | Описание | Значение по умолчанию | Обязательная |
|------------|----------|----------------------|--------------|
| `REDIS_URL` | URL подключения к Redis | `redis://redis:6383/0` | ✅ |
| `REDIS_PASSWORD` | Пароль Redis | (не установлен) | ❌ |
| `REDIS_MAXMEMORY` | Максимальная память | `256mb` | ❌ |

**Пример настройки:**
```bash
REDIS_URL=redis://redis:6383/0
REDIS_PASSWORD=redis_secure_password
REDIS_MAXMEMORY=1gb
```

**Примечания:**
- Redis используется для очередей задач и кэширования
- Порт 6383 используется для избежания конфликтов
- База данных 0 используется по умолчанию

## 🤖 Ollama LLM

| Переменная | Описание | Значение по умолчанию | Обязательная |
|------------|----------|----------------------|--------------|
| `OLLAMA_URL` | URL Ollama сервиса | `http://llm:11438` | ✅ |
| `OLLAMA_MODEL` | Модель для анализа | `llama3:8b` | ✅ |
| `OLLAMA_NUM_PARALLEL` | Количество параллельных запросов | `4` | ❌ |
| `OLLAMA_MAX_LOADED_MODELS` | Максимум загруженных моделей | `1` | ❌ |

### Параметры генерации

| Переменная | Описание | Значение по умолчанию | Диапазон |
|------------|----------|----------------------|----------|
| `NUM_CTX` | Размер контекста | `8192` | 512-32768 |
| `TEMPERATURE` | Креативность (0-1) | `0.7` | 0.0-2.0 |
| `TOP_P` | Nucleus sampling | `0.9` | 0.0-1.0 |
| `TOP_K` | Top-K sampling | `40` | 1-100 |
| `MAX_TOKENS` | Максимум токенов в ответе | `512` | 1-4096 |

**Пример настройки:**
```bash
OLLAMA_URL=http://llm:11438
OLLAMA_MODEL=llama3:8b
NUM_CTX=8192
TEMPERATURE=0.7
TOP_P=0.9
TOP_K=40
MAX_TOKENS=512
```

**Примечания:**
- Модель llama3:8b требует ~4.7GB RAM
- Порт 11438 используется для избежания конфликтов
- Модель автоматически загружается при первом запуске

## 📝 Логирование

| Переменная | Описание | Значение по умолчанию | Варианты |
|------------|----------|----------------------|----------|
| `LOG_LEVEL` | Уровень логирования | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `LOG_FORMAT` | Формат логов | `json` | json, text |
| `LOG_FILE` | Файл для логов | (stdout) | путь к файлу |

**Пример настройки:**
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/app.log
```

**Примечания:**
- JSON формат рекомендуется для продакшена
- DEBUG уровень может замедлить работу
- Логи также выводятся в Docker logs

## ⚙️ Обработка задач

| Переменная | Описание | Значение по умолчанию | Обязательная |
|------------|----------|----------------------|--------------|
| `WORKER_CONCURRENCY` | Количество worker процессов | `1` | ❌ |
| `TASK_TIMEOUT` | Таймаут задачи (секунды) | `300` | ❌ |
| `QUEUE_NAME` | Имя очереди задач | `text_analysis` | ❌ |
| `RESULT_TTL` | TTL результатов в Redis (секунды) | `3600` | ❌ |

**Пример настройки:**
```bash
WORKER_CONCURRENCY=2
TASK_TIMEOUT=600
QUEUE_NAME=pharma_analysis_queue
RESULT_TTL=7200
```

**Примечания:**
- Увеличение WORKER_CONCURRENCY повышает производительность
- TASK_TIMEOUT должен быть больше времени обработки LLM
- RESULT_TTL определяет время хранения промежуточных результатов

## 🌐 Сетевые настройки

### Порты сервисов

| Сервис | Внешний порт | Внутренний порт | Описание |
|--------|--------------|-----------------|----------|
| UI | 8505 | 8501 | Streamlit веб-интерфейс |
| Worker | 8000 | 8000 | API worker сервиса |
| Redis | 6383 | 6379 | Redis сервер |
| PostgreSQL | 5436 | 5432 | PostgreSQL сервер |
| ClickHouse HTTP | 8127 | 8123 | ClickHouse HTTP API |
| ClickHouse Native | 9004 | 9000 | ClickHouse native протокол |
| Ollama | 11438 | 11434 | Ollama LLM сервис |

**Изменение портов:**
```bash
# В docker-compose.yml измените секцию ports:
services:
  ui:
    ports:
      - "8506:8501"  # Измените 8505 на 8506
```

## 🔒 Безопасность

### Продакшен настройки

| Переменная | Описание | Рекомендация |
|------------|----------|--------------|
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | Используйте сложный пароль |
| `REDIS_PASSWORD` | Пароль Redis | Установите пароль |
| `SECRET_KEY` | Секретный ключ приложения | Генерируйте случайный ключ |
| `ALLOWED_HOSTS` | Разрешенные хосты | Ограничьте доступ |

**Пример продакшен настроек:**
```bash
# Безопасные пароли
POSTGRES_PASSWORD=Ph4rm4_S3cur3_P@ssw0rd_2024!
REDIS_PASSWORD=R3d1s_S3cur3_P@ssw0rd_2024!

# Секретный ключ (сгенерируйте свой)
SECRET_KEY=your-super-secret-key-here-32-chars-min

# Ограничение доступа
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

## 📊 Мониторинг

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `HEALTH_CHECK_INTERVAL` | Интервал health checks (секунды) | `30` |
| `METRICS_ENABLED` | Включить метрики | `true` |
| `PROMETHEUS_PORT` | Порт для Prometheus метрик | `9090` |

**Пример настройки мониторинга:**
```bash
HEALTH_CHECK_INTERVAL=30
METRICS_ENABLED=true
PROMETHEUS_PORT=9090
```

## 🚀 Развертывание

### Docker Compose

Все переменные окружения автоматически передаются в контейнеры через `docker-compose.yml`:

```yaml
services:
  ui:
    environment:
      - REDIS_URL=${REDIS_URL}
      - POSTGRES_URL=${POSTGRES_URL}
      - CLICKHOUSE_URL=${CLICKHOUSE_URL}
      - OLLAMA_URL=${OLLAMA_URL}
```

### Kubernetes

Для развертывания в Kubernetes используйте ConfigMap и Secret:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pharma-config
data:
  POSTGRES_DB: "pharma_analysis"
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
---
apiVersion: v1
kind: Secret
metadata:
  name: pharma-secrets
type: Opaque
data:
  POSTGRES_PASSWORD: <base64-encoded-password>
  REDIS_PASSWORD: <base64-encoded-password>
```

## 🔧 Отладка

### Проверка переменных

```bash
# Проверка переменных в контейнере
docker-compose exec ui env | grep POSTGRES
docker-compose exec worker env | grep OLLAMA

# Проверка подключений
docker-compose exec ui python -c "import os; print(os.getenv('POSTGRES_URL'))"
```

### Частые проблемы

1. **Неправильные URL**:
   ```bash
   # Проверьте формат URL
   POSTGRES_URL=postgresql://user:password@host:port/database
   REDIS_URL=redis://host:port/database
   ```

2. **Конфликты портов**:
   ```bash
   # Проверьте занятые порты
   ./pre-flight.sh
   ```

3. **Недостаток памяти**:
   ```bash
   # Увеличьте лимиты Docker
   docker-compose up -d --scale worker=1
   ```

## 📋 Чек-лист настройки

### ✅ Обязательные переменные

- [ ] `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- [ ] `REDIS_URL`
- [ ] `CLICKHOUSE_URL`, `CLICKHOUSE_DB`
- [ ] `OLLAMA_URL`, `OLLAMA_MODEL`

### ✅ Рекомендуемые настройки

- [ ] Изменить пароли по умолчанию
- [ ] Настроить логирование
- [ ] Установить таймауты задач
- [ ] Настроить мониторинг

### ✅ Продакшен настройки

- [ ] Сложные пароли
- [ ] HTTPS сертификаты
- [ ] Ограничение доступа
- [ ] Резервное копирование
- [ ] Мониторинг и алерты

---

**Версия документации**: 1.0.0  
**Дата обновления**: 2024-12-30  
**Статус**: ✅ Полная документация
