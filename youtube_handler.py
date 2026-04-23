import yt_dlp
import os
from typing import Optional, Dict, List

class YouTubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

    async def get_video_info(self, url: str) -> Optional[Dict]:
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                duration = info.get('duration', 0)
                formats = []
                seen = set()
                
                for fmt in info.get('formats', []):
                    height = fmt.get('height')
                    format_id = fmt.get('format_id', '')
                    ext = fmt.get('ext', 'mp4')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    vcodec = fmt.get('vcodec', 'none')
                    acodec = fmt.get('acodec', 'none')
                    
                    if height and height not in seen:
                        seen.add(height)
                        formats.append({
                            'format_id': format_id,
                            'ext': ext,
                            'resolution': f"{height}p",
                            'filesize': filesize,
                            'vcodec': vcodec,
                            'acodec': acodec,
                        })
                
                formats.sort(key=lambda x: int(x['resolution'].replace('p', '')))
                formats = formats[:12]
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title', 'Unknown')[:100],
                    'duration': duration,
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'formats': formats
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    async def download_video(self, url: str, format_id: str = None, quality: str = "720p") -> Optional[str]:
        try:
            os.makedirs("downloads", exist_ok=True)
            
            opts = {
                'quiet': False,
                'no_warnings': True,
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'merge_output_format': 'mp4',
            }
            
            if format_id:
                if format_id == 'bestaudio':
                    opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
                else:
                    opts['format'] = f'{format_id}+bestaudio/{format_id}'
            else:
                height = quality.replace('p', '')
                opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    filename = ydl.prepare_filename(info)
                    if os.path.exists(filename):
                        return filename
                    
                    files = [f for f in os.listdir('downloads') if f.startswith(info.get('id', ''))]
                    if files:
                        return os.path.join('downloads', files[0])
            
            return None
                
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None

youtube_dl = YouTubeDownloader()