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
        await self.init_session()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return None
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                title_elem = soup.find('h1', {'class': 'title'}) or soup.find('h1')
                version_elem = soup.find('span', {'itemprop': 'version'})
                size_elem = soup.find('span', {'class': 'detail-sdk'})
                
                download_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if 'download' in href.lower() and ('apk' in href.lower() or 'd.apkpure.com' in href):
                        if href.startswith('//'):
                            href = 'https:' + href
                        elif not href.startswith('http'):
                            href = 'https://apkpure.com' + href
                        download_links.append(href)
                
                package_name = self.extract_package_name(url)
                
                if not title_elem:
                    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
                    title = title_match.group(1) if title_match else 'Unknown'
                else:
                    title = title_elem.text.strip()
                
                if not version_elem:
                    version_match = re.search(r'version["\s:=]+([^"<&\n]+)', html)
                    version = version_match.group(1).strip() if version_match else 'Unknown'
                else:
                    version = version_elem.text.strip()
                
                if not size_elem:
                    size_match = re.search(r'(\d+\.?\d*\s*[MGT]B)', html)
                    size = size_match.group(1) if size_match else 'Unknown'
                else:
                    size = size_elem.text.strip()
                
                return {
                    'title': title,
                    'version': version,
                    'size': size,
                    'download_links': download_links[:5] if download_links else [],
                    'package_name': package_name
                }
                
        except Exception as e:
            print(f"Error extracting APK info: {e}")
            return None
            
    def extract_package_name(self, url: str):
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) >= 2:
            for part in path_parts:
                if '.' in part and len(part) > 4:
                    return part
        
        match = re.search(r'/([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*)/', parsed.path)
        if match:
            return match.group(1)
        
        params = parse_qs(parsed.query)
        if 'package' in params:
            return params['package'][0]
        
        return 'unknown'
        
    async def download_apk(self, url: str) -> str:
        await self.init_session()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/vnd.android.package-archive,*/*',
                'Referer': 'https://apkpure.com/'
            }
            
            os.makedirs("downloads", exist_ok=True)
            
            if 'd.apkpure.com' in url:
                filename = f"downloads/apk_{hash(url)}.apk"
                
                async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=300)) as response:
                    if response.status == 200:
                        async with aiofiles.open(filename, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        return filename
            else:
                info = await self.extract_apkpure_info(url)
                if info and info['download_links']:
                    download_url = info['download_links'][0]
                    
                    package = info.get('package_name', 'unknown')
                    version = info.get('version', 'unknown')
                    filename = f"downloads/{package}_{version}.apk"
                    
                    async with self.session.get(download_url, headers=headers, timeout=aiohttp.ClientTimeout(total=300)) as response:
                        if response.status == 200:
                            async with aiofiles.open(filename, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                            return filename
            
            return None
            
        except Exception as e:
            print(f"Error downloading APK: {e}")
            return None

apk_dl = APKDownloader()