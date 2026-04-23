import yt_dlp
import os
from typing import Optional, Dict, List

class YouTubeDownloader:
    def __init__(self):
        pass

    async def get_video_info(self, url: str) -> Optional[Dict]:
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
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
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    vcodec = fmt.get('vcodec', 'none')
                    acodec = fmt.get('acodec', 'none')
                    
                    has_video = vcodec != 'none'
                    has_audio = acodec != 'none'
                    
                    if height and height not in seen:
                        seen.add(height)
                        formats.append({
                            'format_id': format_id,
                            'resolution': f"{height}p",
                            'filesize': filesize,
                            'combined': has_video and has_audio,
                        })
                
                formats.sort(key=lambda x: int(x['resolution'].replace('p', '')))
                formats = formats[:10]
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title', 'Unknown')[:100],
                    'duration': duration,
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
            }
            
            if format_id == 'bestaudio':
                opts['format'] = 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio'
            elif quality:
                height = quality.replace('p', '')
                opts['format'] = f'best[height<={height}][ext=mp4]/best[height<={height}]/best'
            else:
                opts['format'] = 'best'
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    video_id = info.get('id', '')
                    files = [f for f in os.listdir('downloads') if f.startswith(video_id)]
                    if files:
                        return os.path.join('downloads', files[0])
            
            return None
                
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None

youtube_dl = YouTubeDownloader()