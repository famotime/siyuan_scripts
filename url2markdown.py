"""
将输入的Web页面链接转换为Markdown文档
基于成熟的库实现，支持媒体文件本地保存
"""

import requests
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any, List, Set, Tuple
import logging
import re
import html
from urllib.parse import urljoin, urlparse, unquote
from datetime import datetime
import mimetypes
import hashlib

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import markdownify
    HAS_MARKDOWNIFY = True
except ImportError:
    HAS_MARKDOWNIFY = False

try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

            logger.info(f"下载媒体文件: {full_url}")

            async with session.get(full_url, headers=self.headers) as response:
                if response.status != 200:
                    logger.warning(f"下载失败，状态码: {response.status}, URL: {full_url}")
                    return None

                content_type = response.headers.get('content-type', '')

                # 检查是否为支持的媒体类型
                if not self.is_supported_media_type(content_type, full_url):
                    logger.info(f"跳过不支持的媒体类型: {content_type}, URL: {full_url}")
                    return None

                # 生成文件名
                filename = self.generate_filename(full_url, content_type)
                file_path = self.media_dir / filename

                # 如果文件已存在，直接返回
                if file_path.exists():
                    logger.info(f"文件已存在，跳过下载: {filename}")
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

                logger.info(f"媒体文件已保存: {filename} ({len(content)} bytes)")

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


class AdvancedWebToMarkdownConverter:
    """高级Web页面转Markdown转换器"""

    def __init__(self, output_dir: str = "output", converter_lib: str = "auto"):
        """
        初始化转换器

        :param output_dir: 输出目录
        :param converter_lib: 转换库选择 ("markdownify", "html2text", "auto")
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 选择转换库
        self.converter_lib = self._select_converter_lib(converter_lib)
        logger.info(f"使用转换库: {self.converter_lib}")

        # 初始化媒体下载器
        self.media_downloader = MediaDownloader(self.output_dir)

        # 请求头设置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def _select_converter_lib(self, preference: str) -> str:
        """选择可用的转换库"""
        if preference == "markdownify" and HAS_MARKDOWNIFY:
            return "markdownify"
        elif preference == "html2text" and HAS_HTML2TEXT:
            return "html2text"
        elif preference == "auto":
            if HAS_MARKDOWNIFY:
                return "markdownify"
            elif HAS_HTML2TEXT:
                return "html2text"
            else:
                return "builtin"
        else:
            return "builtin"

    def fetch_webpage(self, url: str) -> Optional[str]:
        """
        获取网页内容

        :param url: 网页URL
        :return: 网页HTML内容，失败时返回None
        """
        try:
            logger.info(f"正在获取网页内容: {url}")

            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # 尝试检测编码
            if response.encoding == 'ISO-8859-1' or response.encoding is None:
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
                for encoding in encodings:
                    try:
                        response.encoding = encoding
                        content = response.text
                        content.encode('utf-8')
                        break
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        continue
                else:
                    response.encoding = 'utf-8'

            logger.info(f"成功获取网页内容，大小: {len(response.text)} 字符")
            return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"获取网页失败: {e}")
            return None

    def extract_page_info(self, html_content: str) -> Dict[str, str]:
        """
        提取页面基本信息

        :param html_content: HTML内容
        :return: 页面信息字典
        """
        if not HAS_BS4:
            logger.warning("BeautifulSoup未安装，使用简单解析")
            return self._extract_page_info_simple(html_content)

        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取标题
        title = "未知标题"
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
        else:
            h1_tag = soup.find('h1')
            if h1_tag:
                title = h1_tag.get_text().strip()

        # 清理标题
        title = re.sub(r'\s+', ' ', title)

        # 提取描述
        description = ""
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            description = desc_tag.get('content').strip()
        else:
            og_desc_tag = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc_tag and og_desc_tag.get('content'):
                description = og_desc_tag.get('content').strip()

        # 提取作者
        author = ""
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag and author_tag.get('content'):
            author = author_tag.get('content').strip()

        # 提取发布时间
        publish_time = ""
        time_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish_date"]',
            'time[datetime]',
            '.publish-time',
            '.date'
        ]

        for selector in time_selectors:
            element = soup.select_one(selector)
            if element:
                if element.get('content'):
                    publish_time = element.get('content')
                elif element.get('datetime'):
                    publish_time = element.get('datetime')
                else:
                    publish_time = element.get_text().strip()
                break

        return {
            'title': title,
            'description': description,
            'author': author,
            'publish_time': publish_time
        }

    def _extract_page_info_simple(self, html_content: str) -> Dict[str, str]:
        """简单的页面信息提取（不使用BeautifulSoup）"""
        # 提取标题
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "未知标题"
        title = html.unescape(re.sub(r'\s+', ' ', title))

        # 提取描述
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
        description = html.unescape(desc_match.group(1).strip()) if desc_match else ""

        return {
            'title': title,
            'description': description,
            'author': "",
            'publish_time': ""
        }

    def extract_media_urls(self, html_content: str, base_url: str) -> List[str]:
        """
        提取页面中的媒体文件URL

        :param html_content: HTML内容
        :param base_url: 基础URL
        :return: 媒体文件URL列表
        """
        media_urls = set()

        if HAS_BS4:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 提取图片
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    full_url = urljoin(base_url, src)
                    media_urls.add(full_url)

            # 提取视频
            for video in soup.find_all('video'):
                src = video.get('src')
                if src:
                    full_url = urljoin(base_url, src)
                    media_urls.add(full_url)

                # 提取video标签内的source
                for source in video.find_all('source'):
                    src = source.get('src')
                    if src:
                        full_url = urljoin(base_url, src)
                        media_urls.add(full_url)

            # 提取音频
            for audio in soup.find_all('audio'):
                src = audio.get('src')
                if src:
                    full_url = urljoin(base_url, src)
                    media_urls.add(full_url)

                # 提取audio标签内的source
                for source in audio.find_all('source'):
                    src = source.get('src')
                    if src:
                        full_url = urljoin(base_url, src)
                        media_urls.add(full_url)
        else:
            # 使用正则表达式提取
            img_pattern = r'<img[^>]*src=["\']([^"\']*)["\']'
            for match in re.finditer(img_pattern, html_content, re.IGNORECASE):
                full_url = urljoin(base_url, match.group(1))
                media_urls.add(full_url)

            video_pattern = r'<video[^>]*src=["\']([^"\']*)["\']'
            for match in re.finditer(video_pattern, html_content, re.IGNORECASE):
                full_url = urljoin(base_url, match.group(1))
                media_urls.add(full_url)

        return list(media_urls)

    def clean_html_for_conversion(self, html_content: str) -> str:
        """
        清理HTML内容用于转换

        :param html_content: 原始HTML
        :return: 清理后的HTML
        """
        if not HAS_BS4:
            return self._clean_html_simple(html_content)

        soup = BeautifulSoup(html_content, 'html.parser')

        # 移除不需要的标签
        unwanted_tags = [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            'noscript', 'iframe', 'object', 'embed', 'form',
            'button', 'input', 'select', 'textarea'
        ]

        for tag_name in unwanted_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # 移除注释
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 尝试提取主要内容
        main_content = None
        content_selectors = [
            'main', 'article', '[role="main"]',
            '.content', '#content', '.main', '#main',
            '.post-content', '.entry-content', '.article-content',
            '.post-body', '.entry-body'
        ]

        for selector in content_selectors:
            element = soup.select_one(selector)
            if element and len(element.get_text().strip()) > 200:
                main_content = element
                break

        if main_content:
            return str(main_content)
        else:
            # 如果没有找到主要内容，使用body
            body = soup.find('body')
            return str(body) if body else str(soup)

    def _clean_html_simple(self, html_content: str) -> str:
        """简单的HTML清理"""
        unwanted_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<style[^>]*>.*?</style>',
            r'<nav[^>]*>.*?</nav>',
            r'<header[^>]*>.*?</header>',
            r'<footer[^>]*>.*?</footer>',
            r'<aside[^>]*>.*?</aside>',
            r'<!--.*?-->',
        ]

        content = html_content
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)

        return content

    def convert_html_to_markdown(self, html_content: str) -> str:
        """
        将HTML转换为Markdown

        :param html_content: HTML内容
        :return: Markdown内容
        """
        if self.converter_lib == "markdownify":
            return self._convert_with_markdownify(html_content)
        elif self.converter_lib == "html2text":
            return self._convert_with_html2text(html_content)
        else:
            return self._convert_builtin(html_content)

    def _convert_with_markdownify(self, html_content: str) -> str:
        """使用markdownify转换"""
        try:
            markdown_content = markdownify.markdownify(
                html_content,
                heading_style=markdownify.ATX,
                bullets='-',
                strong_tag='**',
                em_tag='*'
            )
            return self._clean_markdown(markdown_content)
        except Exception as e:
            logger.error(f"markdownify转换失败: {e}")
            return self._convert_builtin(html_content)

    def _convert_with_html2text(self, html_content: str) -> str:
        """使用html2text转换"""
        try:
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0  # 不限制行宽
            h.unicode_snob = True
            h.skip_internal_links = True

            markdown_content = h.handle(html_content)
            return self._clean_markdown(markdown_content)
        except Exception as e:
            logger.error(f"html2text转换失败: {e}")
            return self._convert_builtin(html_content)

    def _convert_builtin(self, html_content: str) -> str:
        """内置转换方法"""
        content = html_content

        # 处理标题
        for i in range(6, 0, -1):
            content = re.sub(rf'<h{i}[^>]*>(.*?)</h{i}>', rf'{"#" * i} \1\n\n', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理段落
        content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理格式
        content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理链接
        content = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理图片
        content = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)', content, flags=re.IGNORECASE)
        content = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)', content, flags=re.IGNORECASE)

        # 处理列表
        content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<[uo]l[^>]*>(.*?)</[uo]l>', r'\1\n', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理代码
        content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```\n', content, flags=re.IGNORECASE | re.DOTALL)

        # 处理换行
        content = re.sub(r'<br[^>]*/?>', '\n', content, flags=re.IGNORECASE)
        content = re.sub(r'<hr[^>]*/?>', '\n---\n', content, flags=re.IGNORECASE)

        # 移除剩余HTML标签
        content = re.sub(r'<[^>]+>', '', content)

        return self._clean_markdown(content)

    def _clean_markdown(self, markdown_content: str) -> str:
        """清理Markdown内容"""
        # 解码HTML实体
        content = html.unescape(markdown_content)

        # 规范化空白字符
        content = re.sub(r'[ \t]+', ' ', content)
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

        # 清理行
        lines = []
        for line in content.split('\n'):
            lines.append(line.rstrip())

        content = '\n'.join(lines).strip()
        return content

    def update_media_links(self, markdown_content: str, media_mapping: Dict[str, str]) -> str:
        """
        更新Markdown中的媒体链接为本地路径

        :param markdown_content: 原始Markdown内容
        :param media_mapping: URL到本地路径的映射
        :return: 更新后的Markdown内容
        """
        content = markdown_content

        for original_url, local_path in media_mapping.items():
            # 更新图片链接
            content = content.replace(f"]({original_url})", f"]({local_path})")
            content = content.replace(f'src="{original_url}"', f'src="{local_path}"')
            content = content.replace(f"src='{original_url}'", f"src='{local_path}'")

        return content

    def generate_filename(self, title: str, url: str) -> str:
        """
        生成文件名

        :param title: 网页标题
        :param url: 网页URL
        :return: 安全的文件名
        """
        # 清理标题作为文件名
        filename = re.sub(r'[^\w\s\-_.]', '', title)
        filename = re.sub(r'[-\s]+', '-', filename)
        filename = filename.strip('-')

        # 如果标题为空或太短，使用URL的域名
        if not filename or len(filename) < 3:
            parsed_url = urlparse(url)
            filename = parsed_url.netloc.replace('.', '-')

        # 限制文件名长度
        if len(filename) > 50:
            filename = filename[:50]

        # 添加时间戳避免重复
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename}_{timestamp}"

        return f"{filename}.md"

    def build_markdown_document(self, page_info: Dict[str, str], url: str, markdown_content: str) -> str:
        """
        构建完整的Markdown文档

        :param page_info: 页面信息
        :param url: 原始URL
        :param markdown_content: 转换后的内容
        :return: 完整的Markdown文档
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 构建文档头部
        header_parts = [f"# {page_info['title']}", ""]

        # 添加元数据
        metadata = [
            f"**原始链接：** {url}",
            f"**转换时间：** {current_time}",
        ]

        if page_info['description']:
            metadata.append(f"**描述：** {page_info['description']}")

        if page_info['author']:
            metadata.append(f"**作者：** {page_info['author']}")

        if page_info['publish_time']:
            metadata.append(f"**发布时间：** {page_info['publish_time']}")

        header_parts.extend(metadata)
        header_parts.extend(["", "---", ""])

        # 组合完整文档
        full_document = '\n'.join(header_parts) + markdown_content

        return full_document

    async def convert_url_to_markdown(self, url: str, output_filename: str = None, download_media: bool = True) -> Optional[Path]:
        """
        将URL转换为Markdown文件

        :param url: 要转换的URL
        :param output_filename: 输出文件名（可选）
        :param download_media: 是否下载媒体文件
        :return: 输出文件路径，失败时返回None
        """
        try:
            # 获取网页内容
            html_content = self.fetch_webpage(url)
            if not html_content:
                return None

            # 提取页面信息
            page_info = self.extract_page_info(html_content)
            logger.info(f"页面标题: {page_info['title']}")

            # 下载媒体文件
            media_mapping = {}
            if download_media:
                logger.info("开始下载媒体文件...")
                media_urls = self.extract_media_urls(html_content, url)
                logger.info(f"发现 {len(media_urls)} 个媒体文件")

                if media_urls:
                    media_mapping = await self.media_downloader.download_media_batch(media_urls, url)
                    logger.info(f"成功下载 {len(media_mapping)} 个媒体文件")

            # 清理HTML内容
            clean_html = self.clean_html_for_conversion(html_content)

            # 转换为Markdown
            markdown_content = self.convert_html_to_markdown(clean_html)

            # 更新媒体链接
            if media_mapping:
                markdown_content = self.update_media_links(markdown_content, media_mapping)

            # 生成文件名
            if not output_filename:
                output_filename = self.generate_filename(page_info['title'], url)

            output_path = self.output_dir / output_filename

            # 构建完整文档
            full_markdown = self.build_markdown_document(page_info, url, markdown_content)

            # 保存文件
            output_path.write_text(full_markdown, encoding='utf-8')
            logger.info(f"Markdown文件已保存: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"转换过程出错: {e}")
            return None


async def main():
    """
    主函数 - 提供使用示例
    """
    print("=== URL转Markdown转换器使用示例 ===\n")

    # 示例URL列表（可以根据需要修改）
    demo_urls = [
        ("https://www.yuque.com/siyuannote/docs/go7uom#04ea747f", "思源笔记数据库.md")
    ]

    # 创建转换器实例
    converter = AdvancedWebToMarkdownConverter(output_dir="demo_output")

    print("开始转换示例网页...\n")

    success_count = 0
    total_count = len(demo_urls)

    for i, (url, filename) in enumerate(demo_urls, 1):
        print(f"[{i}/{total_count}] 正在转换: {url}")
        print(f"    输出文件: {filename}")

        try:
            # 转换网页为Markdown
            result_path = await converter.convert_url_to_markdown(
                url=url,
                output_filename=filename,
                download_media=True  # 下载媒体文件
            )

            if result_path:
                file_size = result_path.stat().st_size
                print(f"    ✓ 转换成功! 文件大小: {file_size:,} 字节")
                success_count += 1

                # 检查媒体文件
                media_dir = converter.output_dir / "media"
                if media_dir.exists():
                    media_files = list(media_dir.glob("*"))
                    if media_files:
                        print(f"    📁 下载了 {len(media_files)} 个媒体文件")
            else:
                print("    ✗ 转换失败")

        except Exception as e:
            print(f"    ✗ 转换出错: {e}")

        print()  # 空行分隔

    # 总结
    print("=" * 50)
    print(f"转换完成! 成功: {success_count}/{total_count}")
    print(f"输出目录: {converter.output_dir.absolute()}")

    # 显示输出目录内容
    if converter.output_dir.exists():
        markdown_files = list(converter.output_dir.glob("*.md"))
        media_dir = converter.output_dir / "media"

        print(f"\n生成的Markdown文件:")
        for md_file in markdown_files:
            size = md_file.stat().st_size
            print(f"  📄 {md_file.name} ({size:,} 字节)")

        if media_dir.exists():
            media_files = list(media_dir.glob("*"))
            if media_files:
                print(f"\n下载的媒体文件: {len(media_files)} 个")
                print(f"  📁 媒体目录: {media_dir}")

    print("\n使用说明:")
    print("1. 可以直接导入 AdvancedWebToMarkdownConverter 类")
    print("2. 支持自定义输出目录和文件名")
    print("3. 支持选择不同的转换库 (markdownify, html2text, auto)")
    print("4. 支持开启/关闭媒体文件下载")
    print("\n示例代码:")
    print("""
    from url2markdown import AdvancedWebToMarkdownConverter
    import asyncio

    async def convert_webpage():
        converter = AdvancedWebToMarkdownConverter(output_dir="my_output")
        result = await converter.convert_url_to_markdown(
            "https://example.com/",
            "example.md",
            download_media=True
        )
        return result

    # 运行转换
    asyncio.run(convert_webpage())
    """)


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())