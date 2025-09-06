# MVP Платформа Анализа Фармацевтических Текстов

## 📋 Описание проекта

Система для автоматического анализа фармацевтических текстов с использованием LLM (Large Language Model) для определения соответствия заданным критериям. Платформа включает веб-интерфейс, очередь задач, базы данных и интеграцию с Ollama для обработки естественного языка.

## 🏗️ Архитектура системы

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│     UI      │───▶│    Redis    │───▶│   Worker    │
│  Streamlit   │    │   Queue     │    │   RQ        │
│   Port 8505  │    │  Port 6383  │    │  Port 8000  │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │ PostgreSQL  │    │   Ollama    │
                   │   OLTP      │    │    LLM      │
                   │  Port 5436  │    │  Port 11438 │
                   └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │ ClickHouse  │    │   Events   │
                   │   OLAP      │    │  Analytics │
                   │  Port 8127  │    │            │
                   └─────────────┘    └─────────────┘
```

### Компоненты системы

- **UI (Streamlit)**: Веб-интерфейс для ввода текстов и просмотра результатов
- **Worker (RQ)**: Обработчик задач в фоновом режиме
- **Redis**: Очередь задач и кэширование промежуточных результатов
- **PostgreSQL**: Хранение источников и критериев анализа
- **ClickHouse**: Аналитические данные и события
- **Ollama**: LLM сервис с моделью llama3:8b

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Минимум 8GB RAM (для модели llama3:8b)
- Свободные порты: 8505, 6383, 5436, 8127, 9004, 11438

### 1. Клонирование и настройка

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd Curproject04

# Скопируйте файл с переменными окружения
cp env.example .env

# Проверьте доступность портов
chmod +x pre-flight.sh
./pre-flight.sh
```

### 2. Запуск системы

```bash
# Запустите все сервисы
docker-compose up -d

# Проверьте статус сервисов
docker-compose ps

# Просмотрите логи
docker-compose logs -f
```

### 3. Доступ к приложению

- **Веб-интерфейс**: http://localhost:8505
- **API Worker**: http://localhost:8000
- **Redis**: localhost:6383
- **PostgreSQL**: localhost:5436
- **ClickHouse**: localhost:8127
- **Ollama**: localhost:11438

## 📖 Использование

### Веб-интерфейс

1. **Анализ текста**:
   - Введите текст для анализа
   - Укажите URL источника (опционально)
   - Нажмите "Отправить на анализ"

2. **Просмотр результатов**:
   - Используйте кнопку "🔄 Обновить статус" для получения промежуточных результатов
   - Перейдите в раздел "История" для просмотра всех анализов
   - Используйте фильтры для поиска конкретных результатов

3. **Аналитика**:
   - Раздел "Статистика" содержит графики и метрики
   - Интерактивные графики Plotly для визуализации данных

### API Worker

```bash
# Проверка здоровья сервиса
curl http://localhost:8000/health

# Получение статуса задачи
curl http://localhost:8000/task-status/{task_id}
```

## ⚙️ Конфигурация

### Переменные окружения

Основные настройки в файле `.env`:

```bash
# База данных
POSTGRES_DB=pharma_analysis
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_URL=postgresql://postgres:postgres@pg:5436/pharma_analysis

# Redis
REDIS_URL=redis://redis:6383/0

# ClickHouse
CLICKHOUSE_URL=http://ch:8127
CLICKHOUSE_DB=pharma_analysis

# Ollama LLM
OLLAMA_URL=http://llm:11438
OLLAMA_MODEL=llama3:8b
NUM_CTX=8192
TEMPERATURE=0.7
TOP_P=0.9
TOP_K=40
MAX_TOKENS=512

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=json

# Обработка задач
WORKER_CONCURRENCY=1
TASK_TIMEOUT=300
```

### Настройка портов

Если порты заняты, измените их в `docker-compose.yml`:

```yaml
services:
  ui:
    ports:
      - "8505:8501"  # Измените 8505 на свободный порт
  redis:
    ports:
      - "6383:6379"  # Измените 6383 на свободный порт
  # ... и так далее для других сервисов
```

## 🧪 Тестирование

### Запуск всех тестов

```bash
# Запуск полного набора тестов
python run_tests.py

# Или отдельные категории
python -m pytest tests/test_integration.py -v
python -m pytest tests/test_load.py -v
python -m pytest tests/test_security.py -v
```

### Типы тестов

- **Unit тесты**: Тестирование отдельных компонентов
- **Integration тесты**: Тестирование взаимодействия сервисов
- **Load тесты**: Тестирование производительности
- **Security тесты**: Проверка безопасности

## 📊 Мониторинг и логирование

### Health Checks

Все сервисы имеют встроенные health checks:

```bash
# Проверка статуса всех сервисов
docker-compose ps

# Детальная проверка здоровья
docker-compose exec ui curl -f http://localhost:8501/_stcore/health
docker-compose exec worker python -c "import redis; redis.Redis.from_url('redis://redis:6379/0').ping()"
```

### Логирование

- **Формат**: JSON (structlog)
- **Уровни**: INFO, ERROR, WARNING
- **Ротация**: Автоматическая через Docker

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f ui
docker-compose logs -f worker
```

## 🔧 Устранение неполадок

### Частые проблемы

1. **Порты заняты**:
   ```bash
   # Проверьте занятые порты
   ./pre-flight.sh
   
   # Найдите процесс, использующий порт
   lsof -i :8505
   ```

2. **Модель не загружается**:
   ```bash
   # Проверьте статус Ollama
   curl http://localhost:11438/api/tags
   
   # Принудительная загрузка модели
   curl -X POST http://localhost:11438/api/pull -d '{"name": "llama3:8b"}'
   ```

3. **База данных не инициализируется**:
   ```bash
   # Пересоздайте volumes
   docker-compose down -v
   docker-compose up -d
   ```

4. **Worker не обрабатывает задачи**:
   ```bash
   # Проверьте статус Redis
   docker-compose exec redis redis-cli ping
   
   # Проверьте очередь задач
   docker-compose exec redis redis-cli llen text_analysis
   ```

### Очистка системы

```bash
# Остановка всех сервисов
docker-compose down

# Удаление всех данных (ОСТОРОЖНО!)
docker-compose down -v

# Пересборка образов
docker-compose build --no-cache
```

## 📈 Производительность

### Рекомендуемые ресурсы

- **CPU**: 4+ ядра
- **RAM**: 8GB+ (4.7GB для модели llama3:8b)
- **Диск**: 20GB+ свободного места
- **Сеть**: Стабильное подключение для загрузки модели

### Оптимизация

1. **Масштабирование Worker**:
   ```yaml
   # В docker-compose.yml
   worker:
     deploy:
       replicas: 3  # Запуск нескольких worker'ов
   ```

2. **Настройка Redis**:
   ```bash
   # Увеличение памяти Redis
   REDIS_MAXMEMORY=1gb
   ```

3. **Оптимизация ClickHouse**:
   ```sql
   -- Настройка индексов для быстрых запросов
   CREATE INDEX idx_criteria_id ON events (criteria_id);
   ```

## 🔒 Безопасность

### Рекомендации для продакшена

1. **Аутентификация**: Добавить систему входа
2. **HTTPS**: Использовать SSL сертификаты
3. **Сетевая безопасность**: Настроить firewall
4. **Резервное копирование**: Автоматические бэкапы БД
5. **Мониторинг**: Prometheus + Grafana

### Переменные для продакшена

```bash
# Измените пароли по умолчанию
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password

# Настройте логирование
LOG_LEVEL=WARNING
LOG_FORMAT=json
```

## 📚 API Документация

### Worker API

#### GET /health
Проверка здоровья сервиса

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-30T19:30:00Z",
  "version": "1.0.0"
}
```

#### GET /task-status/{task_id}
Получение статуса задачи

**Параметры:**
- `task_id` (string): ID задачи

**Ответ:**
```json
{
  "task_id": "99c4702c-21eb-4564-8e34-d946ecc3349b",
  "status": "completed",
  "result": {
    "is_match": 1,
    "confidence": 0.9,
    "summary": "Текст соответствует критерию...",
    "latency_ms": 33055
  }
}
```

### Ollama API

#### POST /api/generate
Генерация текста с помощью LLM

**Тело запроса:**
```json
{
  "model": "llama3:8b",
  "prompt": "Проанализируйте текст...",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 512
  }
}
```

## 🤝 Разработка

### Структура проекта

```
Curproject04/
├── ui/                 # Streamlit приложение
├── worker/             # RQ Worker сервис
├── llm/               # Ollama конфигурация
├── db/                # Миграции и схемы БД
├── tests/             # Тесты
├── docker-compose.yml # Конфигурация Docker
├── pre-flight.sh      # Скрипт проверки портов
└── README.md          # Документация
```

### Добавление новых критериев

1. Добавьте критерий в PostgreSQL:
   ```sql
   INSERT INTO criteria (name, description, pattern) 
   VALUES ('Новый критерий', 'Описание', 'regex_pattern');
   ```

2. Обновите логику анализа в `worker/tasks.py`

### Расширение функциональности

1. **Новые типы анализа**: Добавьте функции в `worker/tasks.py`
2. **Дополнительные метрики**: Расширьте схему ClickHouse
3. **Новые визуализации**: Добавьте графики в `ui/app.py`

## 🚀 CI/CD Pipeline

Проект использует GitHub Actions для автоматизации процессов разработки и деплоя.

### Автоматические процессы

- ✅ **Проверка качества кода** - линтинг, форматирование, безопасность
- ✅ **Unit тесты** - тестирование отдельных компонентов
- ✅ **Integration тесты** - тестирование взаимодействия сервисов
- ✅ **Security тесты** - проверка безопасности и уязвимостей
- ✅ **Сборка Docker образов** - автоматическая сборка и публикация
- ✅ **Деплой** - автоматический деплой на production/staging

### Локальная разработка

```bash
# Запуск полного CI/CD pipeline локально
./scripts/ci-local.sh

# Запуск конкретных этапов
./scripts/ci-local.sh --stage code-quality
./scripts/ci-local.sh --stage unit-tests
./scripts/ci-local.sh --stage integration-tests

# Очистка и запуск
./scripts/ci-local.sh --cleanup
```

### Статус CI/CD

[![CI/CD Pipeline](https://github.com/kkobanenko/Curproject04/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/kkobanenko/Curproject04/actions)

### Подробная документация

📖 **[Полное руководство по CI/CD](CI_CD_GUIDE.md)** - подробные инструкции по настройке и использованию

## 📞 Поддержка

### Полезные команды

```bash
# Проверка статуса системы
docker-compose ps

# Просмотр использования ресурсов
docker stats

# Очистка неиспользуемых образов
docker system prune -a

# Экспорт логов
docker-compose logs > system.log

# Локальный CI/CD pipeline
./scripts/ci-local.sh --help
```

### Контакты

- **Документация**: Этот README и [CI_CD_GUIDE.md](CI_CD_GUIDE.md)
- **Issues**: Создайте issue в репозитории
- **Логи**: Проверьте логи через `docker-compose logs`
- **CI/CD**: Проверьте статус в [GitHub Actions](https://github.com/kkobanenko/Curproject04/actions)

## 📄 Лицензия

Проект разработан для внутреннего использования. Все права защищены.

---

**Версия документации**: 1.0.0  
**Дата обновления**: 2024-12-30  
**Статус проекта**: ✅ Готов к продакшену
