#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Веб-сервер для YouTube Audio Downloader
Обрабатывает запросы от веб-интерфейса
"""

import os
import sys
import json
import socket
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Импортируем класс из main.py
from main import YouTubeAudioDownloader


class DownloadHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов"""
    
    def do_OPTIONS(self):
        """Обработка CORS preflight запросов"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Обработка GET запросов (отдача HTML и статических файлов)"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/' or path == '/index.html':
            self.serve_file('index.html', 'text/html')
        elif path == '/download':
            # API endpoint для проверки статуса
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ready'}).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Обработка POST запросов (скачивание видео)"""
        if self.path == '/download':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
            except (ValueError, TypeError):
                self.send_error_response('Неверный Content-Length')
                return
            
            if content_length == 0:
                self.send_error_response('Пустое тело запроса')
                return
            
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                url = data.get('url', '').strip()
                
                if not url:
                    self.send_error_response('URL не может быть пустым')
                    return
                
                # Запускаем скачивание в отдельном потоке
                thread = threading.Thread(target=self.download_video, args=(url,))
                thread.daemon = True
                thread.start()
                
                # Отправляем ответ сразу
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'started',
                    'message': 'Скачивание началось...'
                }).encode())
                
            except json.JSONDecodeError:
                self.send_error_response('Неверный формат данных')
            except Exception as e:
                self.send_error_response(f'Ошибка: {str(e)}')
        else:
            self.send_error(404)
    
    def download_video(self, url):
        """Скачивание видео в отдельном потоке"""
        try:
            downloader = YouTubeAudioDownloader()
            result = downloader.download_audio(url)
            if result:
                print(f"\n✓ Скачивание завершено: {result}")
            else:
                print(f"\n✗ Ошибка при скачивании: {url}")
        except Exception as e:
            print(f"\n✗ Ошибка: {str(e)}")
    
    def send_error_response(self, message):
        """Отправка ошибки клиенту"""
        self.send_response(400)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.end_headers()
        self.wfile.write(json.dumps({
            'status': 'error',
            'message': message
        }).encode())
    
    def serve_file(self, filename, content_type):
        """Отдача статического файла"""
        try:
            file_path = os.path.join(os.path.dirname(__file__), filename)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404)
        except Exception as e:
            self.send_error(500)
    
    def log_message(self, format, *args):
        """Отключаем логирование в консоль"""
        pass


def find_available_port(start_port=8000, max_attempts=10):
    """Находит свободный порт, начиная с start_port"""
    for offset in range(max_attempts):
        port = start_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(('', port))
                return port
            except OSError:
                continue
    raise OSError(f"Не удалось найти свободный порт в диапазоне {start_port}-{start_port + max_attempts - 1}")


def run_server(port=8000):
    """Запуск веб-сервера"""
    actual_port = find_available_port(port)
    if actual_port != port:
        print(f"⚠ Порт {port} занят, используется порт {actual_port}")

    server_address = ('', actual_port)
    httpd = HTTPServer(server_address, DownloadHandler)
    
    print("=" * 60)
    print("YouTube Audio Downloader - Веб-сервер")
    print("=" * 60)
    print(f"\nСервер запущен на http://localhost:{actual_port}")
    print(f"Откройте в браузере: http://localhost:{actual_port}")
    print("\nНажмите Ctrl+C для остановки сервера\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nОстановка сервера...")
        httpd.shutdown()


if __name__ == '__main__':
    # Проверяем, запущен ли из venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Виртуальное окружение активно")
    else:
        # Проверяем, есть ли venv рядом
        venv_path = Path(__file__).parent / 'venv'
        if venv_path.exists():
            print("⚠ Внимание: Виртуальное окружение найдено, но не активировано")
            print("  Рекомендуется запускать через: ./start_server.sh или python3 start_server.py")
    
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Неверный номер порта, используется порт 8000")
    
    run_server(port)
