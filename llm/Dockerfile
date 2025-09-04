FROM ollama/ollama:latest

# Устанавливаем дополнительные инструменты для health check
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Копируем конфигурацию модели
COPY models/ /root/.ollama/models/

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем скрипты инициализации
COPY init.sh /app/
RUN chmod +x /app/init.sh

# Expose порт
EXPOSE 11434

# Запускаем Ollama
CMD ["ollama", "serve"]
