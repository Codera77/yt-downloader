#!/bin/bash
# Автоматический запуск сервера с виртуальным окружением

cd "$(dirname "$0")"

echo "============================================================"
echo "Запуск YouTube Audio Downloader - Веб-сервер"
echo "============================================================"
echo ""

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Ошибка: Python3 не найден!"
    exit 1
fi

# Активируем виртуальное окружение если оно есть
if [ -d "venv" ]; then
    echo "✓ Активация виртуального окружения..."
    source venv/bin/activate
    
    # Проверяем, что yt-dlp установлен
    if ! python3 -c "import yt_dlp" 2>/dev/null; then
        echo "⚠ Предупреждение: yt-dlp не найден в venv"
        echo "  Установите: pip install yt-dlp"
    fi
else
    echo "⚠ Виртуальное окружение не найдено"
    echo "  Рекомендуется создать: python3 -m venv venv"
fi

echo ""
echo "Запуск сервера..."
echo ""

# Запускаем сервер
python3 server.py

