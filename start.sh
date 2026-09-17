#!/bin/bash
# Скрипт для запуска веб-сервера YouTube Downloader
# Использует start_server.sh для автоматической активации venv

cd "$(dirname "$0")"

# Используем новый скрипт, если он существует
if [ -f "start_server.sh" ]; then
    bash start_server.sh "$@"
else
    # Fallback на старый способ
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    python3 server.py "$@"
fi

