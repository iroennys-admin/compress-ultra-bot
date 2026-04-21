# Configuración automática de YouTube para el bot
import os

# Detectar si hay cookies disponibles
COOKIES_FILE = "cookies.txt"
YTDLP_CONFIG = "yt-dlp.conf"

def get_ytdlp_options():
    """Retorna las opciones óptimas para yt-dlp"""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'skip': ['dash', 'hls']
            }
        },
        'user_agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36',
        'extractor_retries': 5,
        'fragment_retries': 5,
        'sleep_interval': 2,
        'max_sleep_interval': 8,
    }
    
    # Usar cookies si existen
    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE
    
    return opts
