import yt_dlp
import os
import asyncio
from typing import Optional, Dict
import random

class YouTubeDownloader:
    def __init__(self):
        # Solución de GitHub para evitar detección
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'user_agent': random.choice(self.user_agents),
            # Solución de GitHub: usar cliente móvil
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                    'skip': ['dash', 'hls']
                }
            },
            # Evitar rate limiting
            'sleep_interval': random.randint(3, 7),
            'max_sleep_interval': 10,
            'sleep_interval_requests': random.randint(2, 5),
        }

    async def get_video_info(self, url: str) -> Optional[Dict]:
        """Obtiene información del video de YouTube"""
        try:
            opts = self.ydl_opts.copy()
            opts['extract_flat'] = True
            opts['user_agent'] = random.choice(self.user_agents)
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = []
                
                # Solo formatos de video con audio
                for f in info.get('formats', []):
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        format_id = f.get('format_id', '')
                        # Priorizar mp4
                        if 'mp4' in f.get('ext', ''):
                            formats.append({
                                'format_id': format_id,
                                'ext': f.get('ext', 'mp4'),
                                'resolution': f.get('resolution', 'unknown'),
                                'filesize': f.get('filesize', 0),
                                'format_note': f.get('format_note', ''),
                                'fps': f.get('fps', 0)
                            })
                
                # Si no hay mp4, agregar otros formatos
                if not formats:
                    for f in info.get('formats', []):
                        if f.get('vcodec') != 'none':
                            formats.append({
                                'format_id': f.get('format_id', ''),
                                'ext': f.get('ext', 'unknown'),
                                'resolution': f.get('resolution', 'unknown'),
                                'filesize': f.get('filesize', 0),
                                'format_note': f.get('format_note', ''),
                                'fps': f.get('fps', 0)
                            })
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title', 'Unknown')[:100],
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail'),
                    'formats': formats[:8]
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    async def download_video(self, url: str, format_id: str, quality: str) -> Optional[str]:
        """Descarga video de YouTube con máxima compatibilidad"""
        try:
            video_id = url.split('=')[-1] if '=' in url else url.split('/')[-1]
            output_path = f"downloads/{video_id}.mp4"
            os.makedirs("downloads", exist_ok=True)
            
            ydl_opts = {
                'format': f'{format_id}+bestaudio[ext=m4a]/best',
                'outtmpl': output_path.replace('.mp4', ''),
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'user_agent': random.choice(self.user_agents),
                'extractor_retries': 10,
                'fragment_retries': 10,
                'retry_sleep': 5,
                'sleep_interval': random.randint(5, 10),
                'max_sleep_interval': 15,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android'],
                        'skip': ['hls', 'dash']
                    }
                },
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4'
                }]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            # Buscar el archivo descargado
            possible_paths = [
                output_path,
                f"downloads/{video_id}.mp4",
                f"downloads/{video_id}.mkv",
                f"downloads/{video_id}.webm"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
                    
            # Buscar cualquier archivo con el ID
            for file in os.listdir("downloads"):
                if video_id in file:
                    return os.path.join("downloads", file)
                    
            return None
            
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None

youtube_dl = YouTubeDownloader()
