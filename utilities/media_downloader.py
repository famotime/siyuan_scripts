"""
媒体文件下载器模块
支持图片、视频、音频等媒体文件的异步下载
"""

import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any, List, Set, Tuple
import logging
import re
import hashlib
import mimetypes
from urllib.parse import urljoin, urlparse, unquote

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = logging.getLogger(__name__)


class MediaDownloader:
    """媒体文件下载器"""

    def __init__(self, base_dir: Path, max_workers: int = 5):
        """
        初始化媒体下载器

        :param base_dir: 基础目录
        :param max_workers: 最大并发下载数
        """
        self.base_dir = base_dir
        self.media_dir = base_dir / "media"
        self.media_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers

        # 支持的媒体类型
        self.supported_image_types = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico'}
        self.supported_video_types = {'.mp4', '.webm', '.ogg', '.avi', '.mov', '.wmv', '.flv'}
        self.supported_audio_types = {'.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac'}

        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }

    def get_file_extension(self, url: str, content_type: str = None) -> str:
        """
        获取文件扩展名

        :param url: 文件URL
        :param content_type: MIME类型
        :return: 文件扩展名
        """
        # 从URL获取扩展名
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        ext = Path(path).suffix.lower()

        if ext and ext in (self.supported_image_types | self.supported_video_types | self.supported_audio_types):
            return ext

        # 从Content-Type获取扩展名
        if content_type:
            ext = mimetypes.guess_extension(content_type.split(';')[0])
            if ext:
                return ext.lower()

        # 默认扩展名
        if content_type:
            if content_type.startswith('image/'):
                return '.jpg'
            elif content_type.startswith('video/'):
                return '.mp4'
            elif content_type.startswith('audio/'):
                return '.mp3'

        return '.bin'

    def generate_filename(self, url: str, content_type: str = None) -> str:
        """
        生成唯一的文件名

        :param url: 原始URL
        :param content_type: MIME类型
        :return: 文件名
        """
        # 使用URL的哈希值生成唯一文件名
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
        ext = self.get_file_extension(url, content_type)

        # 尝试从URL获取有意义的文件名
        parsed_url = urlparse(url)
        original_name = Path(unquote(parsed_url.path)).stem
        if original_name and len(original_name) > 0 and original_name != '/':
            # 清理文件名
            clean_name = re.sub(r'[^\w\-_.]', '_', original_name)[:30]
            return f"{clean_name}_{url_hash}{ext}"

        return f"media_{url_hash}{ext}"

    async def download_media_async(self, session: aiohttp.ClientSession, url: str, base_url: str = "") -> Optional[Tuple[str, str]]:
        """
        异步下载单个媒体文件

        :param session: aiohttp会话
        :param url: 媒体文件URL
        :param base_url: 基础URL
        :return: (本地文件路径, 相对路径) 或 None
        """
        try:
            # 处理相对URL
            if base_url:
                full_url = urljoin(base_url, url)
            else:
                full_url = url

            # logger.info(f"下载媒体文件: {full_url}")

            async with session.get(full_url, headers=self.headers) as response:
                if response.status != 200:
                    logger.warning(f"下载失败，状态码: {response.status}, URL: {full_url}")
                    return None

                content_type = response.headers.get('content-type', '')

                # 检查是否为支持的媒体类型
                if not self.is_supported_media_type(content_type, full_url):
                    # logger.info(f"跳过不支持的媒体类型: {content_type}, URL: {full_url}")
                    return None

                # 生成文件名
                filename = self.generate_filename(full_url, content_type)
                file_path = self.media_dir / filename

                # 如果文件已存在，直接返回
                if file_path.exists():
                    # logger.info(f"文件已存在，跳过下载: {filename}")
                    return str(file_path), f"media/{filename}"

                # 下载文件
                content = await response.read()

                # 验证文件大小
                if len(content) < 100:  # 太小的文件可能不是有效媒体
                    logger.warning(f"文件太小，可能无效: {len(content)} bytes, URL: {full_url}")
                    return None

                # 保存文件
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)

                # logger.info(f"媒体文件已保存: {filename} ({len(content)} bytes)")

                # 如果是图片，尝试验证和优化
                if content_type.startswith('image/') and HAS_PIL:
                    try:
                        # 验证图片
                        with Image.open(file_path) as img:
                            # 可以在这里添加图片优化逻辑
                            pass
                    except Exception as e:
                        logger.warning(f"图片验证失败: {filename}, 错误: {e}")

                return str(file_path), f"media/{filename}"

        except Exception as e:
            logger.error(f"下载媒体文件失败: {url}, 错误: {e}")
            return None

    def is_supported_media_type(self, content_type: str, url: str) -> bool:
        """
        检查是否为支持的媒体类型

        :param content_type: MIME类型
        :param url: 文件URL
        :return: 是否支持
        """
        # 检查Content-Type
        if content_type:
            if (content_type.startswith('image/') or
                content_type.startswith('video/') or
                content_type.startswith('audio/')):
                return True

        # 检查文件扩展名
        ext = Path(urlparse(url).path).suffix.lower()
        return ext in (self.supported_image_types | self.supported_video_types | self.supported_audio_types)

    async def download_media_batch(self, urls: List[str], base_url: str = "") -> Dict[str, str]:
        """
        批量下载媒体文件

        :param urls: 媒体文件URL列表
        :param base_url: 基础URL
        :return: URL到本地路径的映射
        """
        url_to_local = {}

        if not urls:
            return url_to_local

        # 创建异步会话
        connector = aiohttp.TCPConnector(limit=self.max_workers)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 创建下载任务
            tasks = []
            for url in urls:
                task = asyncio.create_task(self.download_media_async(session, url, base_url))
                tasks.append((url, task))

            # 执行下载
            for original_url, task in tasks:
                try:
                    result = await task
                    if result:
                        local_path, relative_path = result
                        url_to_local[original_url] = relative_path
                except Exception as e:
                    logger.error(f"下载任务失败: {original_url}, 错误: {e}")

        return url_to_local