import asyncio
import os
import gzip
import zipfile
import tarfile
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional

class FileCompressor:
    def __init__(self):
        self.temp_dir = "downloads"
        self.output_dir = "compressed"
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self.active_compressions = {}
        
    async def compress_file(self, input_path: str, output_path: str = None, method: str = 'gzip') -> Dict:
        try:
            if not os.path.exists(input_path):
                return {'success': False, 'error': 'Archivo no encontrado'}
            
            original_size = os.path.getsize(input_path)
            filename = Path(input_path).name
            
            if output_path is None:
                suffixes = {'gzip': '.gz', 'zip': '.zip', 'tar': '.tar.gz', 'brotli': '.br', 'zstd': '.zst'}
                ext = suffixes.get(method, '.gz')
                output_path = os.path.join(self.output_dir, filename + ext)
            
            os.makedirs(os.path.dirname(output_path) or self.output_dir, exist_ok=True)
            
            loop = asyncio.get_event_loop()
            
            if method == 'gzip':
                result = await loop.run_in_executor(None, self._compress_gzip, input_path, output_path)
            elif method == 'zip':
                result = await loop.run_in_executor(None, self._compress_zip, input_path, output_path)
            elif method == 'tar':
                result = await loop.run_in_executor(None, self._compress_tar, input_path, output_path)
            elif method == 'brotli':
                result = await loop.run_in_executor(None, self._compress_brotli, input_path, output_path)
            elif method == 'zstd':
                return self._compress_gzip(input_path, output_path)  # Fallback to gzip
            else:
                result = await loop.run_in_executor(None, self._compress_gzip, input_path, output_path)
            
            if result.get('success') and os.path.exists(result['output_path']):
                result['original_size'] = original_size
                result['compressed_size'] = os.path.getsize(result['output_path'])
                result['compression_ratio'] = round((1 - result['compressed_size'] / original_size) * 100, 2) if original_size > 0 else 0
                result['original_filename'] = filename
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _compress_gzip(self, input_path: str, output_path: str) -> Dict:
        with open(input_path, 'rb') as f:
            data = f.read()
        compressed = gzip.compress(data, compresslevel=9)
        with open(output_path, 'wb') as f:
            f.write(compressed)
        return {'success': True, 'output_path': output_path, 'method': 'gzip'}
    
    def _compress_zip(self, input_path: str, output_path: str) -> Dict:
        if not output_path.endswith('.zip'):
            output_path += '.zip'
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.write(input_path, Path(input_path).name)
        return {'success': True, 'output_path': output_path, 'method': 'zip'}
    
    def _compress_tar(self, input_path: str, output_path: str) -> Dict:
        if not output_path.endswith('.tar.gz'):
            output_path += '.tar.gz'
        with tarfile.open(output_path, 'w:gz') as tar:
            tar.add(input_path, arcname=Path(input_path).name)
        return {'success': True, 'output_path': output_path, 'method': 'tar.gz'}
    
    def _compress_brotli(self, input_path: str, output_path: str) -> Dict:
        try:
            import brotli
            with open(input_path, 'rb') as f:
                data = f.read()
            compressed = brotli.compress(data, quality=11)
            with open(output_path, 'wb') as f:
                f.write(compressed)
            return {'success': True, 'output_path': output_path, 'method': 'brotli'}
        except ImportError:
            return self._compress_gzip(input_path, output_path)
    
    def _compress_zstd(self, input_path: str, output_path: str) -> Dict:
        try:
            import zstandard as zstd
            with open(input_path, 'rb') as f:
                data = f.read()
            cctx = zstd.ZstdCompressor(level=19)
            with open(output_path, 'wb') as f:
                f.write(cctx.compress(data))
            return {'success': True, 'output_path': output_path, 'method': 'zstd'}
        except ImportError:
            return self._compress_gzip(input_path, output_path)
    
    async def decompress_file(self, input_path: str, output_dir: str = None) -> Dict:
        try:
            if not os.path.exists(input_path):
                return {'success': False, 'error': 'Archivo no encontrado'}
            
            if output_dir is None:
                output_dir = self.temp_dir
            os.makedirs(output_dir, exist_ok=True)
            
            file_ext = Path(input_path).suffix.lower()
            
            if len(Path(input_path).suffixes) > 1:
                ext = ''.join(Path(input_path).suffixes[-2:])
            else:
                ext = file_ext
            
            loop = asyncio.get_event_loop()
            
            if file_ext == '.gz' or '.gz' in input_path:
                return await loop.run_in_executor(None, self._decompress_gzip, input_path, output_dir)
            elif file_ext == '.zip':
                return await loop.run_in_executor(None, self._decompress_zip, input_path, output_dir)
            elif ext in ['.tar', '.tar.gz', '.tgz'] or '.tar.gz' in input_path:
                return await loop.run_in_executor(None, self._decompress_tar, input_path, output_dir)
            elif file_ext == '.br':
                return await loop.run_in_executor(None, self._decompress_brotli, input_path, output_dir)
            else:
                return {'success': False, 'error': f'Formato no soportado: {file_ext}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _decompress_gzip(self, input_path: str, output_dir: str) -> Dict:
        filename = Path(input_path).name
        if filename.endswith('.gz'):
            for ext in ['.tar.gz', '.tar.gzip']:
                if filename.endswith(ext):
                    filename = filename[:-7]
                    break
            else:
                filename = filename[:-3]
        output_path = os.path.join(output_dir, filename)
        with gzip.open(input_path, 'rb') as f:
            data = f.read()
        with open(output_path, 'wb') as f:
            f.write(data)
        return {'success': True, 'output_path': output_path, 'method': 'gzip', 'original_size': os.path.getsize(input_path), 'decompressed_size': len(data)}
    
    def _decompress_zip(self, input_path: str, output_dir: str) -> Dict:
        extracted = []
        with zipfile.ZipFile(input_path, 'r') as zf:
            zf.extractall(output_dir)
            extracted = [os.path.join(output_dir, n) for n in zf.namelist()]
        return {'success': True, 'output_paths': extracted, 'method': 'zip'}
    
    def _decompress_tar(self, input_path: str, output_dir: str) -> Dict:
        extracted = []
        with tarfile.open(input_path, 'r:*') as tar:
            tar.extractall(output_dir)
            extracted = [os.path.join(output_dir, m.name) for m in tar.getmembers()]
        return {'success': True, 'output_paths': extracted, 'method': 'tar'}
    
    def _decompress_brotli(self, input_path: str, output_dir: str) -> Dict:
        import brotli
        filename = Path(input_path).name.replace('.br', '')
        output_path = os.path.join(output_dir, filename)
        with open(input_path, 'rb') as f:
            data = brotli.decompress(f.read())
        with open(output_path, 'wb') as f:
            f.write(data)
        return {'success': True, 'output_path': output_path, 'method': 'brotli'}
    
    def _decompress_zstd(self, input_path: str, output_dir: str) -> Dict:
        import zstandard as zstd
        filename = Path(input_path).name.replace('.zst', '')
        output_path = os.path.join(output_dir, filename)
        dctx = zstd.ZstdDecompressor()
        with open(input_path, 'rb') as f:
            with open(output_path, 'wb') as f_out:
                f_out.write(dctx.decompress(f.read()))
        return {'success': True, 'output_path': output_path, 'method': 'zstd'}
    
    async def compress_multiple_methods(self, input_path: str) -> Dict:
        try:
            if not os.path.exists(input_path):
                return {'success': False, 'error': 'Archivo no encontrado'}
            
            original_size = os.path.getsize(input_path)
            filename = Path(input_path).stem
            results = []
            
            available_methods = ['gzip', 'zip', 'tar']
            
            for method in available_methods:
                output_path = os.path.join(self.output_dir, f"{filename}_{method}")
                result = await self.compress_file(input_path, output_path, method)
                if result.get('success'):
                    results.append({
                        'method': result['method'],
                        'output_path': result['output_path'],
                        'size': result.get('compressed_size', 0),
                        'ratio': result.get('compression_ratio', 0)
                    })
            
            best = min(results, key=lambda x: x['size']) if results else None
            
            return {
                'success': True,
                'original_size': original_size,
                'results': results,
                'best_method': best['method'] if best else None,
                'best_ratio': best['ratio'] if best else 0,
                'best_output': best['output_path'] if best else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

file_compressor = FileCompressor()