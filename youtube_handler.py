import yt_dlp
import os
import asyncio
from typing import Optional, Dict

class YouTubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'force_generic_extractor': False,
            'cookiefile': None,
            # Nuevas opciones para evitar detección
            'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
            'format_sort': ['res:720', 'codec:h264'],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'extractor_retries': 3,
            'fragment_retries': 3,
            'retry_sleep_functions': {'fragment': lambda n: 2},
            'extractor_args': {'youtubetab': {'skip': ['webpage']}},
            'sleep_interval_requests': 1,
            'sleep_interval': 2,
            'max_sleep_interval': 5,
        }

    async def get_video_info(self, url: str) -> Optional[Dict]:
        """Obtiene información del video de YouTube"""
        try:
            opts = self.ydl_opts.copy()
            opts['extract_flat'] = True
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = []
                
                for f in info.get('formats', []):
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        format_id = f.get('format_id', '')
                        # Solo incluir formatos mp4 simples
                        if format_id.isdigit() or 'mp4' in f.get('ext', ''):
                            formats.append({
                                'format_id': format_id,
                                'ext': f.get('ext', 'mp4'),
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
        """Descarga video de YouTube en la calidad especificada"""
        try:
            output_path = f"downloads/yt_{hash(url)}_%(id)s.%(ext)s"
            os.makedirs("downloads", exist_ok=True)
            
            ydl_opts = {
                'format': f'{format_id}+bestaudio[ext=m4a]/best',
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'extractor_retries': 5,
                'fragment_retries': 5,
                'retry_sleep': 3,
                'sleep_interval': 2,
                'max_sleep_interval': 5,
                'throttledratelimit': 1000000,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['hls', 'dash']
                    }
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Buscar el archivo descargado
                if os.path.exists(filename):
                    return filename
                elif os.path.exists(filename.replace('.webm', '.mp4')):
                    return filename.replace('.webm', '.mp4')
                elif os.path.exists(filename.replace('.mkv', '.mp4')):
                    return filename.replace('.mkv', '.mp4')
                    
            return None
            
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None

youtube_dl = YouTubeDownloader()
