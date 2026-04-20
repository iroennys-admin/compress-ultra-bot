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
            'cookiefile': None,  # No necesita cookies
        }

    async def get_video_info(self, url: str) -> Optional[Dict]:
        """Obtiene información del video de YouTube"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = []
                
                for f in info.get('formats', []):
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        formats.append({
                            'format_id': f.get('format_id'),
                            'ext': f.get('ext'),
                            'resolution': f.get('resolution'),
                            'filesize': f.get('filesize', 0),
                            'format_note': f.get('format_note', ''),
                            'fps': f.get('fps', 0)
                        })
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'formats': formats[:10]  # Limitar a 10 formatos
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    async def download_video(self, url: str, format_id: str, quality: str) -> Optional[str]:
        """Descarga video de YouTube en la calidad especificada"""
        try:
            output_path = f"downloads/{url.split('=')[-1]}_{quality}.mp4"
            os.makedirs("downloads", exist_ok=True)
            
            ydl_opts = {
                'format': format_id,
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4'
                }]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            if os.path.exists(output_path):
                return output_path
            return None
            
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None

youtube_dl = YouTubeDownloader()
