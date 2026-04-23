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
            opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'extract_info口味': True,
            }
            
            if os.path.exists('cookies.txt'):
                opts['cookiefile'] = 'cookies.txt'
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                duration = info.get('duration', 0)
                formats = []
                
                seen_formats = set()
                
                for fmt in info.get('formats', []):
                    format_id = fmt.get('format_id', '')
                    ext = fmt.get('ext', 'mp4')
                    height = fmt.get('height')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    
                    if format_id in seen_formats:
                        continue
                    
                    if height:
                        key = f"{height}p_{ext}"
                        if key not in seen_formats:
                            seen_formats.add(key)
                            formats.append({
                                'format_id': format_id,
                                'ext': ext,
                                'resolution': f"{height}p",
                                'filesize': filesize,
                                'tbr': fmt.get('tbr', 0),
                                'vcodec': fmt.get('vcodec', 'none'),
                                'acodec': fmt.get('acodec', 'none'),
                            })
                
                formats.sort(key=lambda x: int(x['resolution'].replace('p', '')) if x['resolution'].replace('p', '').isdigit() else 0)
                
                if len(formats) > 12:
                    formats = formats[:12]
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title', 'Unknown')[:100],
                    'duration': duration,
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'formats': formats
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    async def download_video(self, url: str, format_id: str = None, quality: str = "720p") -> Optional[str]:
        try:
            os.makedirs("downloads", exist_ok=True)
            
            opts = {
                'quiet': True,
                'no_warnings': True,
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'merge_output_format': 'mp4',
            }
            
            if os.path.exists('cookies.txt'):
                opts['cookiefile'] = 'cookies.txt'
            
            if format_id:
                opts['format'] = format_id
            else:
                height = quality.replace('p', '')
                opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    filename = ydl.prepare_filename(info)
                    if os.path.exists(filename):
                        return filename
                    
                    for ext in ['mp4', 'webm', 'mkv', 'flv', 'avi', 'mov']:
                        test_file = f"downloads/test.{ext}"
                        if os.path.exists(test_file):
                            return test_file
                    
                    files = os.listdir('downloads')
                    for f in files:
                        if info.get('id') in f:
                            return os.path.join('downloads', f)
            
            return None
                
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None

    async def get_formats_list(self, info: Dict) -> List[Dict]:
        formats = []
        
        resolution_files = {}
        
        for fmt in info.get('formats', []):
            height = fmt.get('height')
            if not height:
                continue
            
            resolution = f"{height}p"
            if resolution not in resolution_files:
                resolution_files[resolution] = {
                    'format_id': fmt.get('format_id'),
                    'ext': fmt.get('ext', 'mp4'),
                    'resolution': resolution,
                    'filesize': fmt.get('filesize') or fmt.get('filesize_approx', 0),
                }
        
        for res, data in sorted(resolution_files.items(), key=lambda x: int(x[0].replace('p', ''))):
            formats.append(data)
        
        return formats[:10]

youtube_dl = YouTubeDownloader()