import os
import sys
import re
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Ошибка: библиотека yt-dlp не установлена.")
    print("Установите её командой: pip install yt-dlp")
    sys.exit(1)


class YouTubeAudioDownloader:
    """Класс для скачивания аудио из YouTube"""
    
    def __init__(self, output_dir="downloads"):
        """
        Инициализация загрузчика
        
        Args:
            output_dir: Директория для сохранения файлов
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def sanitize_filename(self, filename):
        """
        Очистка имени файла от недопустимых символов
        
        Args:
            filename: Исходное имя файла
            
        Returns:
            Очищенное имя файла
        """
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', ' ', filename)
        filename = filename.strip()
        if len(filename) > 200:
            filename = filename[:200]
        return filename
    
    def progress_hook(self, d):
        """
        Callback функция для отображения прогресса загрузки
        
        Args:
            d: Словарь с информацией о прогрессе
        """
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                percent = (downloaded / total) * 100
                downloaded_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                print(f"\rПрогресс: {percent:.1f}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)", end='', flush=True)
            else:
                print(f"\rСкачивание... {downloaded / (1024 * 1024):.1f} MB", end='', flush=True)
                
        elif d['status'] == 'finished':
            print(f"\rОбработка аудио...", end='', flush=True)
    
    def download_audio(self, url):
        """
        Скачивание аудио из YouTube видео
        
        Args:
            url: URL YouTube видео
            
        Returns:
            Путь к скачанному файлу или None в случае ошибки
        """
        if not self.is_valid_youtube_url(url):
            print("Ошибка: Неверный URL YouTube видео")
            return None
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            # Avoid android_sdkless — often causes HTTP 403 on media URLs.
            # Let yt-dlp pick current defaults minus that client.
            'extractor_args': {
                'youtube': {
                    'player_client': ['default', '-android_sdkless'],
                }
            },
            # Fetch EJS challenge solver components when needed
            'remote_components': ['ejs:github'],
            'retries': 5,
            'fragment_retries': 5,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Получение информации о видео...")
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'video')
                
                print(f"\nВидео: {video_title}")
                print(f"Длительность: {self.format_duration(info.get('duration', 0))}")
                print(f"Начинаю скачивание...\n")
                
                ydl.download([url])
                
                sanitized_title = self.sanitize_filename(video_title)
                output_file = self.output_dir / f"{sanitized_title}.mp3"
                
                if output_file.exists():
                    file_size = output_file.stat().st_size / (1024 * 1024)
                    print(f"\n✓ Успешно! Файл сохранён: {output_file}")
                    print(f"  Размер: {file_size:.2f} MB")
                    return str(output_file)
                else:
                    mp3_files = list(self.output_dir.glob("*.mp3"))
                    if mp3_files:
                        latest_file = max(mp3_files, key=lambda p: p.stat().st_mtime)
                        file_size = latest_file.stat().st_size / (1024 * 1024)
                        print(f"\n✓ Успешно! Файл сохранён: {latest_file}")
                        print(f"  Размер: {file_size:.2f} MB")
                        return str(latest_file)
                    else:
                        print("\nОшибка: Файл не найден после скачивания")
                        return None
                        
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            print(f"\nОшибка при скачивании: {error_msg}")
            
            if "403" in error_msg or "Forbidden" in error_msg:
                print("\n⚠ Ошибка 403: YouTube заблокировал запрос")
                print("Попробуйте:")
                print("  1. Обновить yt-dlp: pip3 install --upgrade yt-dlp")
                print("  2. Подождать несколько минут и попробовать снова")
                print("  3. Проверить интернет-соединение")
            elif "not available on this app" in error_msg.lower() or "watch on the latest version" in error_msg.lower():
                print("\n⚠ Требуется обновление yt-dlp")
                print("Эта ошибка означает, что ваша версия yt-dlp устарела.")
                print("Выполните:")
                print("  pip3 install --upgrade yt-dlp")
                print("Затем попробуйте снова.")
            elif "Private video" in error_msg or "unavailable" in error_msg.lower():
                print("Видео недоступно или приватное")
            elif "Sign in" in error_msg:
                print("Требуется авторизация для доступа к видео")
            elif "Video unavailable" in error_msg:
                print("Видео недоступно (возможно, удалено или заблокировано)")
            
            return None
        except Exception as e:
            print(f"\nНеожиданная ошибка: {str(e)}")
            return None
    
    def is_valid_youtube_url(self, url):
        """
        Проверка валидности URL YouTube
        
        Args:
            url: URL для проверки
            
        Returns:
            True если URL валидный, False иначе
        """
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in youtube_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def format_duration(self, seconds):
        """
        Форматирование длительности в читаемый вид
        
        Args:
            seconds: Длительность в секундах
            
        Returns:
            Отформатированная строка
        """
        if not seconds:
            return "Неизвестно"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"


def main():
    """Главная функция программы"""
    print("=" * 60)
    print("YouTube Audio Downloader")
    print("=" * 60)
    print()
    
    try:
        import yt_dlp
        version = yt_dlp.version.__version__
        print(f"yt-dlp версия: {version}")
        try:
            from packaging import version as pkg_version
            if pkg_version.parse(version) < pkg_version.parse("2024.12.13"):
                print("⚠ ВАЖНО: Ваша версия yt-dlp устарела!")
                print("  Текущая версия может не работать с некоторыми видео.")
                print("  Обновите: pip3 install --upgrade yt-dlp")
                print()
        except ImportError:
            if version < "2024.12":
                print("⚠ ВАЖНО: Рекомендуется обновить yt-dlp")
                print("  Выполните: pip3 install --upgrade yt-dlp")
                print()
    except Exception:
        pass
    
    print("Проверка зависимостей...")
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              timeout=5)
        if result.returncode != 0:
            print("⚠ Предупреждение: FFmpeg не найден или не работает корректно")
            print("  Установите FFmpeg для конвертации в MP3")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠ Предупреждение: FFmpeg не найден")
        print("  Установите FFmpeg для конвертации в MP3")
        print("  Windows: https://ffmpeg.org/download.html")
        print("  Linux: sudo apt install ffmpeg (Ubuntu/Debian)")
        print("         sudo yum install ffmpeg (CentOS/RHEL)")
    except Exception:
        pass
    
    print()
    
    downloader = YouTubeAudioDownloader()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Введите URL YouTube видео: ").strip()
    
    if not url:
        print("Ошибка: URL не может быть пустым")
        sys.exit(1)
    
    result = downloader.download_audio(url)
    
    if result:
        print("\n" + "=" * 60)
        print("Готово!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("Ошибка при скачивании")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

