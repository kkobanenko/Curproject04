FROM ollama/ollama:latest

# Устанавливаем curl (bash уже есть в Ubuntu)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Копируем скрипт инициализации
COPY init_models.sh /init_models.sh
RUN chmod +x /init_models.sh

# Создаем entrypoint скрипт
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo '/bin/ollama serve &' >> /entrypoint.sh && \
    echo 'sleep 5' >> /entrypoint.sh && \
    echo '/init_models.sh' >> /entrypoint.sh && \
    echo 'wait' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Используем entrypoint вместо CMD
ENTRYPOINT ["/entrypoint.sh"]