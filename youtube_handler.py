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
        
        if os.path.exists('cookies.txt'):
            self.ydl_opts['cookiefile'] = 'cookies.txt'

    async def get_video_info(self, url: str) -> Optional[Dict]:
        try:
            opts = self.ydl_opts.copy()
            opts['extract_flat'] = True
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                duration = info.get('duration', 0)
                
                formats = []
                available_formats = info.get('formats', [])
                
                seen_resolutions = set()
                for fmt in available_formats:
                    height = fmt.get('height')
                    if height and height not in seen_resolutions:
                        seen_resolutions.add(height)
                        
                        format_id = fmt.get('format_id', '')
                        ext = fmt.get('ext', 'mp4')
                        
                        if height == 360:
                            formats.append({
                                'format_id': '18',
                                'ext': ext,
                                'resolution': '360p',
                                'filesize': fmt.get('filesize') or fmt.get('filesize_approx')
                            })
                        elif height == 720:
                            formats.append({
                                'format_id': '22',
                                'ext': ext,
                                'resolution': '720p',
                                'filesize': fmt.get('filesize') or fmt.get('filesize_approx')
                            })
                        elif height == 1080:
                            formats.append({
                                'format_id': '37',
                                'ext': ext,
                                'resolution': '1080p',
                                'filesize': fmt.get('filesize') or fmt.get('filesize_approx')
                            })
                
                if len(formats) < 3:
                    formats = [
                        {'format_id': '18', 'ext': 'mp4', 'resolution': '360p'},
                        {'format_id': '22', 'ext': 'mp4', 'resolution': '720p'},
                        {'format_id': '37', 'ext': 'mp4', 'resolution': '1080p'},
                    ]
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title', 'Unknown')[:100],
                    'duration': duration,
                    'thumbnail': info.get('thumbnail'),
                    'formats': formats[:8]
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    async def download_video(self, url: str, format_id: str, quality: str = "medium") -> Optional[str]:
        try:
            os.makedirs("downloads", exist_ok=True)
            output_path = "downloads/%(id)s.%(ext)s"
            
            opts = {
                'quiet': True,
                'no_warnings': True,
                'format': format_id,
                'outtmpl': output_path,
                'max_filesize': 2 * 1024 * 1024 * 1024,
            }
            
            if os.path.exists('cookies.txt'):
                opts['cookiefile'] = 'cookies.txt'
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    filename = ydl.prepare_filename(info)
                    if os.path.exists(filename):
                        return filename
                    
                    mp4_file = filename.rsplit('.', 1)[0] + '.mp4'
                    if os.path.exists(mp4_file):
                        return mp4_file
                    
                    webm_file = filename.rsplit('.', 1)[0] + '.webm'
                    if os.path.exists(webm_file):
                        return webm_file
                
                for ext in ['mp4', 'webm', 'mkv', 'flv']:
                    test_file = f"downloads/test.{ext}"
                    if os.path.exists(test_file):
                        return test_file
                        
            return None
                
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None

youtube_dl = YouTubeDownloader()