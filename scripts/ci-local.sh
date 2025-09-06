#!/bin/bash
# Скрипт для локального запуска CI/CD pipeline
# Позволяет запустить все этапы CI/CD локально перед push в репозиторий

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_message() {
    echo -e "${BLUE}[CI-LOCAL]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция для проверки наличия команды
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "Команда '$1' не найдена. Установите её для продолжения."
        exit 1
    fi
}

# Функция для проверки портов
check_ports() {
    print_message "Проверка доступности портов..."
    
    # Порты для тестов
    TEST_PORTS=(8506 8001 6384 5437 8128 9005 11439)
    
    for port in "${TEST_PORTS[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_warning "Порт $port занят. Остановите процесс или измените конфигурацию."
            lsof -Pi :$port -sTCP:LISTEN
        else
            print_success "Порт $port свободен"
        fi
    done
}

# Функция для очистки тестовых данных
cleanup_test_data() {
    print_message "Очистка тестовых данных..."
    
    # Остановка тестовых контейнеров
    docker-compose -f .github/workflows/docker-compose.test.yml down -v 2>/dev/null || true
    
    # Удаление тестовых образов
    docker images | grep pharma-analysis | grep test | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
    
    print_success "Тестовые данные очищены"
}

# Функция для установки зависимостей
install_dependencies() {
    print_message "Установка зависимостей для CI/CD..."
    
    # Проверка наличия Python
    check_command python3
    check_command pip3
    
    # Установка инструментов разработки
    pip3 install --upgrade pip
    pip3 install flake8 black isort mypy bandit safety pytest pytest-cov pytest-mock
    
    print_success "Зависимости установлены"
}

# Этап 1: Проверка качества кода
stage_code_quality() {
    print_message "🔍 Этап 1: Проверка качества кода"
    
    # Проверка форматирования
    print_message "Проверка форматирования кода (Black)..."
    black --check --diff ui/ worker/ llm/ db/ tests/ || {
        print_error "Код не соответствует стандартам форматирования"
        print_message "Запустите: black ui/ worker/ llm/ db/ tests/"
        return 1
    }
    
    # Проверка импортов
    print_message "Проверка сортировки импортов (isort)..."
    isort --check-only --diff ui/ worker/ llm/ db/ tests/ || {
        print_error "Импорты не отсортированы"
        print_message "Запустите: isort ui/ worker/ llm/ db/ tests/"
        return 1
    }
    
    # Линтинг
    print_message "Линтинг кода (Flake8)..."
    flake8 ui/ worker/ llm/ db/ tests/ --max-line-length=100 --ignore=E203,W503 || {
        print_error "Найдены ошибки линтинга"
        return 1
    }
    
    # Проверка типов
    print_message "Проверка типов (mypy)..."
    mypy ui/ worker/ llm/ db/ --ignore-missing-imports || {
        print_warning "Найдены проблемы с типами (продолжаем)"
    }
    
    # Проверка безопасности
    print_message "Проверка безопасности (Bandit)..."
    bandit -r ui/ worker/ llm/ db/ -ll || {
        print_warning "Найдены потенциальные проблемы безопасности (продолжаем)"
    }
    
    # Проверка уязвимостей в зависимостях
    print_message "Проверка уязвимостей в зависимостях (Safety)..."
    safety check || {
        print_warning "Найдены уязвимости в зависимостях (продолжаем)"
    }
    
    print_success "Этап 1 завершен успешно"
}

# Этап 2: Unit тесты
stage_unit_tests() {
    print_message "🧪 Этап 2: Unit тесты"
    
    # Установка зависимостей для тестов
    pip3 install -r ui/requirements.txt
    pip3 install -r worker/requirements.txt
    pip3 install requests pytest-httpx
    pip3 install psycopg2-binary clickhouse-driver
    
    # Unit тесты для UI
    print_message "Unit тесты для UI..."
    python3 -m pytest ui/test_app.py ui/test_clickhouse.py -v --tb=short || {
        print_error "Unit тесты UI провалены"
        return 1
    }
    
    # Unit тесты для Worker
    print_message "Unit тесты для Worker..."
    python3 -m pytest worker/test_tasks.py -v --tb=short || {
        print_error "Unit тесты Worker провалены"
        return 1
    }
    
    # Unit тесты для LLM
    print_message "Unit тесты для LLM..."
    python3 -m pytest llm/test_api.py -v --tb=short || {
        print_error "Unit тесты LLM провалены"
        return 1
    }
    
    # Unit тесты для DB
    print_message "Unit тесты для DB..."
    python3 -m pytest db/test_models.py -v --tb=short || {
        print_error "Unit тесты DB провалены"
        return 1
    }
    
    print_success "Этап 2 завершен успешно"
}

# Этап 3: Integration тесты
stage_integration_tests() {
    print_message "🔗 Этап 3: Integration тесты"
    
    # Запуск тестовых сервисов
    print_message "Запуск тестовых сервисов..."
    docker-compose -f .github/workflows/docker-compose.test.yml --profile test up -d
    
    # Ожидание готовности сервисов
    print_message "Ожидание готовности сервисов..."
    sleep 30
    
    # Проверка здоровья сервисов
    print_message "Проверка здоровья сервисов..."
    
    # Redis
    docker-compose -f .github/workflows/docker-compose.test.yml exec -T redis-test redis-cli ping || {
        print_error "Redis не готов"
        return 1
    }
    
    # PostgreSQL
    docker-compose -f .github/workflows/docker-compose.test.yml exec -T pg-test pg_isready -U postgres -d pharma_analysis_test || {
        print_error "PostgreSQL не готов"
        return 1
    }
    
    # ClickHouse
    docker-compose -f .github/workflows/docker-compose.test.yml exec -T ch-test wget --no-verbose --tries=1 --spider http://127.0.0.1:8123/ping || {
        print_error "ClickHouse не готов"
        return 1
    }
    
    # Ollama
    docker-compose -f .github/workflows/docker-compose.test.yml exec -T llm-test curl -f http://127.0.0.1:11434/api/tags || {
        print_error "Ollama не готов"
        return 1
    }
    
    # Запуск integration тестов
    print_message "Запуск integration тестов..."
    python3 -m pytest tests/test_integration.py -v --tb=short || {
        print_error "Integration тесты провалены"
        return 1
    }
    
    # Запуск полного набора тестов
    print_message "Запуск полного набора тестов..."
    python3 run_tests.py || {
        print_error "Полный набор тестов провален"
        return 1
    }
    
    print_success "Этап 3 завершен успешно"
}

# Этап 4: Security тесты
stage_security_tests() {
    print_message "🔒 Этап 4: Security тесты"
    
    # Запуск security тестов
    print_message "Запуск security тестов..."
    python3 -m pytest tests/test_security.py -v --tb=short || {
        print_error "Security тесты провалены"
        return 1
    }
    
    print_success "Этап 4 завершен успешно"
}

# Этап 5: Сборка Docker образов
stage_build_images() {
    print_message "🐳 Этап 5: Сборка Docker образов"
    
    # Сборка UI образа
    print_message "Сборка UI образа..."
    docker build -t pharma-analysis-ui:test ./ui || {
        print_error "Ошибка сборки UI образа"
        return 1
    }
    
    # Сборка Worker образа
    print_message "Сборка Worker образа..."
    docker build -t pharma-analysis-worker:test ./worker || {
        print_error "Ошибка сборки Worker образа"
        return 1
    }
    
    # Сборка LLM образа
    print_message "Сборка LLM образа..."
    docker build -t pharma-analysis-llm:test ./llm || {
        print_error "Ошибка сборки LLM образа"
        return 1
    }
    
    print_success "Этап 5 завершен успешно"
}

# Функция для отображения справки
show_help() {
    echo "Использование: $0 [ОПЦИИ]"
    echo ""
    echo "Опции:"
    echo "  --help, -h          Показать эту справку"
    echo "  --stage STAGE       Запустить только указанный этап"
    echo "  --cleanup           Очистить тестовые данные перед запуском"
    echo "  --no-cleanup        Не очищать тестовые данные после завершения"
    echo "  --quick             Быстрый режим (пропустить некоторые проверки)"
    echo ""
    echo "Доступные этапы:"
    echo "  code-quality        Проверка качества кода"
    echo "  unit-tests          Unit тесты"
    echo "  integration-tests   Integration тесты"
    echo "  security-tests      Security тесты"
    echo "  build-images        Сборка Docker образов"
    echo "  all                 Все этапы (по умолчанию)"
    echo ""
    echo "Примеры:"
    echo "  $0                                    # Запустить все этапы"
    echo "  $0 --stage code-quality              # Только проверка кода"
    echo "  $0 --cleanup --stage integration-tests # Очистить и запустить integration тесты"
}

# Основная функция
main() {
    # Параметры по умолчанию
    STAGE="all"
    CLEANUP_BEFORE=false
    CLEANUP_AFTER=true
    QUICK_MODE=false
    
    # Обработка аргументов командной строки
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --stage)
                STAGE="$2"
                shift 2
                ;;
            --cleanup)
                CLEANUP_BEFORE=true
                shift
                ;;
            --no-cleanup)
                CLEANUP_AFTER=false
                shift
                ;;
            --quick)
                QUICK_MODE=true
                shift
                ;;
            *)
                print_error "Неизвестная опция: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Заголовок
    echo "=========================================="
    echo "🚀 ЛОКАЛЬНЫЙ CI/CD PIPELINE"
    echo "=========================================="
    echo "Этап: $STAGE"
    echo "Очистка перед запуском: $CLEANUP_BEFORE"
    echo "Очистка после завершения: $CLEANUP_AFTER"
    echo "Быстрый режим: $QUICK_MODE"
    echo "=========================================="
    
    # Проверка зависимостей
    check_command docker
    check_command docker-compose
    check_command python3
    check_command pip3
    
    # Очистка перед запуском
    if [ "$CLEANUP_BEFORE" = true ]; then
        cleanup_test_data
    fi
    
    # Проверка портов
    check_ports
    
    # Установка зависимостей
    install_dependencies
    
    # Запуск этапов
    case $STAGE in
        "code-quality")
            stage_code_quality
            ;;
        "unit-tests")
            stage_unit_tests
            ;;
        "integration-tests")
            stage_integration_tests
            ;;
        "security-tests")
            stage_security_tests
            ;;
        "build-images")
            stage_build_images
            ;;
        "all")
            stage_code_quality
            stage_unit_tests
            stage_integration_tests
            stage_security_tests
            stage_build_images
            ;;
        *)
            print_error "Неизвестный этап: $STAGE"
            show_help
            exit 1
            ;;
    esac
    
    # Очистка после завершения
    if [ "$CLEANUP_AFTER" = true ]; then
        cleanup_test_data
    fi
    
    # Итоговое сообщение
    echo "=========================================="
    print_success "🎉 ВСЕ ЭТАПЫ ЗАВЕРШЕНЫ УСПЕШНО!"
    echo "=========================================="
    echo "Ваш код готов к push в репозиторий!"
    echo "Запустите: git add . && git commit -m 'feat: your changes' && git push"
    echo "=========================================="
}

# Запуск основной функции
main "$@"
