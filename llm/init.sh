#!/bin/bash

# Скрипт инициализации для загрузки модели Llama 8B
# Запускается при первом старте контейнера

set -e

echo "🚀 Инициализация Ollama..."

# Ждем запуска Ollama сервиса
echo "⏳ Ожидание запуска Ollama сервиса..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "   Ollama еще не готов, ждем..."
    sleep 2
done

echo "✅ Ollama сервис запущен"

# Проверяем, есть ли уже модель llama3:8b
if ollama list | grep -q "llama3:8b"; then
    echo "✅ Модель llama3:8b уже загружена"
else
    echo "📥 Загрузка модели llama3:8b..."
    ollama pull llama3:8b
    echo "✅ Модель llama3:8b загружена"
fi

echo "🎉 Инициализация завершена"
