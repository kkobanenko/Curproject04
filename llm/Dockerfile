FROM ollama/ollama:latest

# Устанавливаем curl (bash уже есть в Ubuntu)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Копируем скрипт инициализации
COPY init_models.sh /init_models.sh
RUN chmod +x /init_models.sh

# Создаем entrypoint скрипт с ограничением CPU ядер
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo '# Устанавливаем ограничение на количество CPU ядер' >> /entrypoint.sh && \
    echo 'export OLLAMA_NUM_PARALLEL=${OLLAMA_NUM_PARALLEL:-4}' >> /entrypoint.sh && \
    echo 'export OLLAMA_MAX_LOADED_MODELS=${OLLAMA_MAX_LOADED_MODELS:-1}' >> /entrypoint.sh && \
    echo 'echo "🚀 Запуск Ollama с ограничением: ${OLLAMA_NUM_PARALLEL} параллельных потоков"' >> /entrypoint.sh && \
    echo '/bin/ollama serve &' >> /entrypoint.sh && \
    echo 'sleep 5' >> /entrypoint.sh && \
    echo '/init_models.sh' >> /entrypoint.sh && \
    echo 'wait' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Используем entrypoint вместо CMD
ENTRYPOINT ["/entrypoint.sh"]