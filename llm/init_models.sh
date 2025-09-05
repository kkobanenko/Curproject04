#!/bin/bash

# Скрипт для автоматической загрузки моделей Ollama
# Этот скрипт запускается при инициализации контейнера Ollama

echo "🚀 Инициализация Ollama - загрузка моделей..."

# Ждем запуска Ollama сервера
echo "⏳ Ожидание запуска Ollama сервера..."
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "   Ollama сервер еще не готов, ждем..."
    sleep 5
done

echo "✅ Ollama сервер запущен!"

# Загружаем модель llama3:8b
echo "📥 Загрузка модели llama3:8b..."
ollama pull llama3:8b

# Проверяем, что модель загружена
echo "🔍 Проверка загруженных моделей..."
MODELS=$(ollama list)
echo "Загруженные модели:"
echo "$MODELS"

# Проверяем, что модель llama3:8b доступна
if echo "$MODELS" | grep -q "llama3:8b"; then
    echo "✅ Модель llama3:8b успешно загружена!"
else
    echo "❌ Ошибка: модель llama3:8b не найдена!"
    exit 1
fi

# Загружаем модель в память с keep_alive для немедленного использования
echo "🧠 Загрузка модели llama3:8b в память..."
curl -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{
        "model": "llama3:8b",
        "prompt": "test",
        "stream": false,
        "keep_alive": "10m"
    }' > /dev/null 2>&1

# Проверяем, что модель загружена в память
echo "🔍 Проверка загруженных в память моделей..."
LOADED_MODELS=$(curl -s http://localhost:11434/api/ps | grep -o '"name":"[^"]*"' | wc -l)
if [ "$LOADED_MODELS" -gt 0 ]; then
    echo "✅ Модель успешно загружена в память!"
    curl -s http://localhost:11434/api/ps | grep -o '"name":"[^"]*"'
else
    echo "⚠️ Модель не загружена в память, но будет загружена при первом запросе"
fi

echo "🎉 Инициализация Ollama завершена успешно!"
