import yt_dlp
import os
from typing import Optional, Dict

class YouTubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt',
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],  # Usar cliente web que no requiere PO Token
                    'skip': ['dash', 'hls']
                }
            }
        }

    async def get_video_info(self, url: str) -> Optional[Dict]:
        try:
            opts = self.ydl_opts.copy()
            opts['extract_flat'] = True
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                formats = [
                    {'format_id': '18', 'ext': 'mp4', 'resolution': '360p'},
                    {'format_id': '22', 'ext': 'mp4', 'resolution': '720p'},
                    {'format_id': '37', 'ext': 'mp4', 'resolution': '1080p'},
                ]
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title', 'Unknown')[:100],
                    'duration': info.get('duration', 0),
                    'formats': formats
                }
        except Exception as e:
            print(f"Error: {e}")
            return None

    async def download_video(self, url: str, format_id: str, quality: str) -> Optional[str]:
        try:
            os.makedirs("downloads", exist_ok=True)
            output_path = "downloads/%(id)s.%(ext)s"
            
            opts = self.ydl_opts.copy()
            opts['format'] = format_id
            opts['outtmpl'] = output_path
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if os.path.exists(filename):
                    return filename
                    
                # Buscar con extensión .mp4
                mp4_file = filename.rsplit('.', 1)[0] + '.mp4'
                if os.path.exists(mp4_file):
                    return mp4_file
                    
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None

youtube_dl = YouTubeDownloader()
