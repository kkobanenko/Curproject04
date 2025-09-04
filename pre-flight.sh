#!/bin/bash

# Pre-flight скрипт для проверки доступности портов
# Проверяет, что все необходимые порты свободны перед запуском

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Проверка доступности портов...${NC}"

# Список портов для проверки
PORTS=(
    8505  # UI (Streamlit)
    6383  # Redis
    5436  # PostgreSQL
    8127  # ClickHouse HTTP
    9004  # ClickHouse Native
    11438 # Ollama
)

# Функция проверки порта
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Порт $port уже занят${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Порт $port свободен${NC}"
        return 0
    fi
}

# Проверяем все порты
failed_ports=()
for port in "${PORTS[@]}"; do
    if ! check_port $port; then
        failed_ports+=($port)
    fi
done

# Выводим результат
if [ ${#failed_ports[@]} -eq 0 ]; then
    echo -e "${GREEN}🎉 Все порты свободны! Можно запускать docker-compose up${NC}"
    exit 0
else
    echo -e "${RED}❌ Следующие порты заняты: ${failed_ports[*]}${NC}"
    echo -e "${YELLOW}💡 Освободите порты или измените конфигурацию в docker-compose.yml${NC}"
    exit 1
fi
