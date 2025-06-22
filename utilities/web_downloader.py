"""
网页下载器模块
负责获取网页内容并提取页面信息
"""

import requests
import logging
import re
import html
from typing import Optional, Dict
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

logger = logging.getLogger(__name__)


class WebDownloader:
    """网页下载器"""

    def __init__(self):
        """初始化网页下载器"""
        # 请求头设置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def fetch_webpage(self, url: str) -> Optional[str]:
        """
        获取网页内容

        :param url: 网页URL
        :return: 网页HTML内容，失败时返回None
        """
        try:
            # logger.info(f"正在获取网页内容: {url}")

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

            # logger.info(f"成功获取网页内容，大小: {len(response.text)} 字符")
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