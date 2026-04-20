import aiohttp
import aiofiles
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

class APKDownloader:
    def __init__(self):
        self.session = None
        
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close_session(self):
        if self.session:
            await self.session.close()
            
    async def extract_apkpure_info(self, url: str):
        """Extrae información del APK desde APKPure"""
        await self.init_session()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Extraer información básica
                title_elem = soup.find('h1', {'class': 'title'}) or soup.find('h1')
                version_elem = soup.find('span', {'itemprop': 'version'})
                size_elem = soup.find('span', {'class': 'detail-sdk'})
                
                # Buscar link de descarga
                download_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if 'download' in href.lower() and 'apk' in href.lower():
                        download_links.append(href)
                
                return {
                    'title': title_elem.text.strip() if title_elem else 'Unknown',
                    'version': version_elem.text.strip() if version_elem else 'Unknown',
                    'size': size_elem.text.strip() if size_elem else 'Unknown',
                    'download_links': download_links[:5],
                    'package_name': self.extract_package_name(url)
                }
                
        except Exception as e:
            print(f"Error extracting APK info: {e}")
            return None
            
    def extract_package_name(self, url: str):
        """Extrae el nombre del paquete de la URL"""
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        
        # Buscar patrón de nombre de paquete
        for part in path_parts:
            if '.' in part and len(part) > 5:
                return part
                
        # Intentar de query params
        params = parse_qs(parsed.query)
        return params.get('package', ['unknown'])[0]
        
    async def download_apk(self, url: str) -> str:
        """Descarga APK desde APKPure"""
        await self.init_session()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/vnd.android.package-archive,*/*',
                'Referer': 'https://apkpure.com/'
            }
            
            # Si es URL directa de descarga
            if 'd.apkpure.com' in url:
                filename = f"downloads/apk_{hash(url)}.apk"
                os.makedirs("downloads", exist_ok=True)
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        async with aiofiles.open(filename, 'wb') as f:
                            await f.write(await response.read())
                        return filename
            else:
                # Extraer info y buscar link de descarga
                info = await self.extract_apkpure_info(url)
                if info and info['download_links']:
                    download_url = info['download_links'][0]
                    if not download_url.startswith('http'):
                        download_url = f"https://apkpure.com{download_url}"
                    
                    filename = f"downloads/{info['package_name']}_{info['version']}.apk"
                    os.makedirs("downloads", exist_ok=True)
                    
                    async with self.session.get(download_url, headers=headers) as response:
                        if response.status == 200:
                            async with aiofiles.open(filename, 'wb') as f:
                                await f.write(await response.read())
                            return filename
                            
            return None
            
        except Exception as e:
            print(f"Error downloading APK: {e}")
            return None

apk_dl = APKDownloader()
