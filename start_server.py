import os
import sys
import subprocess
from pathlib import Path

def find_python():
    """Находит правильный Python (из venv или системный)"""
    # Проверяем venv в текущей директории
    venv_python = Path(__file__).parent / 'venv' / 'bin' / 'python3'
    if venv_python.exists():
        return str(venv_python)
    
    # Проверяем venv/python (Windows)
    venv_python_win = Path(__file__).parent / 'venv' / 'Scripts' / 'python.exe'
    if venv_python_win.exists():
        return str(venv_python_win)
    
    # Используем системный Python
    return sys.executable

def check_dependencies(python_exe):
    """Проверяет наличие необходимых зависимостей"""
    try:
        result = subprocess.run(
            [python_exe, '-c', 'import yt_dlp'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def main():
    """Главная функция"""
    print("=" * 60)
    print("YouTube Audio Downloader - Веб-сервер")
    print("=" * 60)
    print()
    
    # Находим Python
    python_exe = find_python()
    is_venv = 'venv' in python_exe
    
    if is_venv:
        print("✓ Используется виртуальное окружение")
        print(f"  Python: {python_exe}")
    else:
        print("⚠ Используется системный Python")
        print(f"  Python: {python_exe}")
        print("  Рекомендуется использовать venv")
    
    print()
    
    # Проверяем зависимости
    print("Проверка зависимостей...")
    if check_dependencies(python_exe):
        print("✓ yt-dlp установлен")
    else:
        print("❌ yt-dlp не найден!")
        print("  Установите: pip install yt-dlp")
        if is_venv:
            print(f"  Или: {python_exe} -m pip install yt-dlp")
        print()
        response = input("Продолжить без yt-dlp? (y/n): ").strip().lower()
        if response != 'y':
            sys.exit(1)
    
    print()
    print("Запуск сервера...")
    print()
    
    # Запускаем server.py
    server_path = Path(__file__).parent / 'server.py'
    try:
        subprocess.run([python_exe, str(server_path)] + sys.argv[1:])
    except KeyboardInterrupt:
        print("\n\nОстановка сервера...")
        sys.exit(0)

if __name__ == '__main__':
    main()

