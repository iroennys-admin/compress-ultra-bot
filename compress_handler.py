import subprocess
import os
import asyncio
from config import FFMPEG_SETTINGS

class VideoCompressor:
    def __init__(self):
        self.active_compressions = {}
        
    async def compress_video(self, input_path: str, output_path: str, quality: str = "medium"):
        """Comprime video usando FFmpeg"""
        try:
            settings = FFMPEG_SETTINGS.get(quality, FFMPEG_SETTINGS["medium"])
            
            cmd = [
                'ffmpeg', '-i', input_path,
                *settings.split(),
                '-y',  # Sobrescribir archivo si existe
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.active_compressions[input_path] = process
            
            stdout, stderr = await process.communicate()
            
            del self.active_compressions[input_path]
            
            if process.returncode == 0 and os.path.exists(output_path):
                original_size = os.path.getsize(input_path)
                compressed_size = os.path.getsize(output_path)
                compression_ratio = (1 - compressed_size / original_size) * 100
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'compression_ratio': round(compression_ratio, 2)
                }
            else:
                return {'success': False, 'error': stderr.decode()}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    async def cancel_compression(self, input_path: str):
        """Cancela compresión en curso"""
        if input_path in self.active_compressions:
            process = self.active_compressions[input_path]
            process.terminate()
            del self.active_compressions[input_path]
            return True
        return False

compressor = VideoCompressor()
