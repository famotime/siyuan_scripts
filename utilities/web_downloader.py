"""
网页下载器模块
负责获取网页内容并提取页面信息
"""

import requests
import logging
import re
import html
import gzip
import zlib
from typing import Optional, Dict
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import brotli
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

logger = logging.getLogger(__name__)


class WebDownloader:
    """网页下载器"""

    def __init__(self):
        """初始化网页下载器"""
        # 请求头设置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

        # 针对特定网站的特殊请求头
        self.site_specific_headers = {
            'toutiao.com': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
        }

    def _get_site_specific_headers(self, url: str) -> Dict[str, str]:
        """获取针对特定网站的请求头"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        # 检查是否有针对该域名的特殊请求头
        for site_pattern, headers in self.site_specific_headers.items():
            if site_pattern in domain:
                return {**self.headers, **headers}

        return self.headers

    def _decompress_content(self, content: bytes, encoding: str) -> bytes:
        """解压缩内容"""
        try:
            if encoding == 'gzip':
                return gzip.decompress(content)
            elif encoding == 'deflate':
                return zlib.decompress(content)
            elif encoding == 'br' and HAS_BROTLI:
                return brotli.decompress(content)
            else:
                return content
        except Exception as e:
            logger.warning(f"解压缩失败 ({encoding}): {e}")
            return content

    def _detect_encoding(self, content: bytes, response_encoding: str = None) -> str:
        """检测内容编码"""
        # 首先尝试响应头中的编码
        if response_encoding and response_encoding.lower() not in ['iso-8859-1', 'ascii']:
            return response_encoding

        # 使用chardet检测
        if HAS_CHARDET:
            detected = chardet.detect(content)
            if detected['encoding'] and detected['confidence'] > 0.7:
                return detected['encoding']

        # 尝试从HTML meta标签中提取编码
        try:
            content_str = content.decode('utf-8', errors='ignore')
            charset_match = re.search(r'<meta[^>]*charset[="\s]*([^">\s]+)', content_str, re.IGNORECASE)
            if charset_match:
                return charset_match.group(1)
        except:
            pass

        # 按优先级尝试常见编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin-1']
        for encoding in encodings:
            try:
                content.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue

        return 'utf-8'  # 默认使用UTF-8

    def _extract_wechat_original_link(self, content: str) -> Optional[str]:
        """
        从飞书页面内容中提取微信公众号原文链接

        :param content: 网页HTML内容
        :return: 微信公众号原文链接，如果没有找到则返回None
        """
        try:
            # 匹配各种可能的原文链接格式，使用更精确的正则表达式
            patterns = [
                r"""原文链接[：:]\s*(https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+)""",
                r"""原文链接\s*[：:]\s*(https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+)""",
                r"""原文链接\s+[：:]\s*(https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+)""",
                r"""原文链接[：:]\s*(https://mp\.weixin\.qq\.com/s\?[^"'\s<>]+)""",
                r"""原文链接\s*[：:]\s*(https://mp\.weixin\.qq\.com/s\?[^"'\s<>]+)""",
                r"""原文链接\s+[：:]\s*(https://mp\.weixin\.qq\.com/s\?[^"'\s<>]+)""",
            ]

            wechat_patterns = [
                r"https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+",  # 短链接格式
                r"""https://mp\.weixin\.qq\.com/s\?[^"'\s<>]+""",    # 长链接格式
            ]

            lines = content.split('\n')[:10]

            def normalize_link(raw_link: str) -> str:
                """清洗HTML中的原文链接，移除转义符和冗余片段"""
                cleaned = html.unescape(raw_link.strip())
                cleaned = cleaned.replace('\u200b', '').replace('\u00a0', '')
                if '#wechat_redirect' in cleaned:
                    cleaned = cleaned.split('#wechat_redirect', 1)[0]
                cleaned = cleaned.rstrip('?')
                return cleaned

            def add_candidate(raw_link: str, candidates: list, seen: set):
                cleaned = normalize_link(raw_link)
                if not cleaned:
                    return
                if '...' in cleaned or cleaned.endswith('...'):
                    return
                if cleaned not in seen:
                    seen.add(cleaned)
                    candidates.append(cleaned)

            def select_best_link(candidates: list) -> Optional[str]:
                if not candidates:
                    return None

                def is_short_form(link: str) -> bool:
                    return link.startswith('https://mp.weixin.qq.com/s/') and '?' not in link

                def is_long_enough(link: str) -> bool:
                    return len(link) > 40

                short_links = [link for link in candidates if is_short_form(link) and is_long_enough(link)]
                if short_links:
                    return short_links[0]

                query_links = [link for link in candidates if link.startswith('https://mp.weixin.qq.com/s?') and is_long_enough(link)]
                if query_links:
                    return query_links[0]

                long_links = [link for link in candidates if is_long_enough(link)]
                if long_links:
                    return long_links[0]

                return candidates[0]

            candidates = []
            seen_links = set()

            # 优先在前10行中尝试收集候选链接
            for line in lines:
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        add_candidate(match.group(1), candidates, seen_links)

            # 如果前10行未找到足够信息，则扫描整个页面
            for pattern in wechat_patterns:
                matches = re.findall(pattern, content)
                for link in matches:
                    add_candidate(link, candidates, seen_links)

            if candidates:
                original_url = select_best_link(candidates)
                if original_url:
                    logger.info(f"在飞书页面中找到微信公众号原文链接: {original_url}")
                    return original_url

            return None

        except Exception as e:
            logger.error(f"提取微信原文链接时出错: {e}")
            return None

    def fetch_webpage(self, url: str) -> Optional[str]:
        """
        获取网页内容

        :param url: 网页URL
        :return: 网页HTML内容，失败时返回None
        """
        try:
            # 检查是否是飞书链接，如果是则先尝试提取原文链接
            if url.startswith("https://waytoagi.feishu.cn/"):
                logger.info(f"检测到飞书链接，尝试提取微信公众号原文链接: {url}")

                # 先获取飞书页面内容
                headers = self._get_site_specific_headers(url)
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()

                # 获取原始内容并解码
                raw_content = response.content
                content_encoding = response.headers.get('Content-Encoding', '').lower()
                if content_encoding:
                    raw_content = self._decompress_content(raw_content, content_encoding)

                detected_encoding = self._detect_encoding(raw_content, response.encoding)
                try:
                    feishu_content = raw_content.decode(detected_encoding)
                except UnicodeDecodeError:
                    try:
                        feishu_content = raw_content.decode('utf-8', errors='replace')
                    except:
                        feishu_content = raw_content.decode('latin-1')

                # 尝试提取微信原文链接
                original_url = self._extract_wechat_original_link(feishu_content)

                if original_url:
                    logger.info(f"  ✅ 找到微信原文链接: {original_url}")
                    logger.info(f"  🔄 重定向到原文链接获取内容...")
                    # 递归调用，使用原文链接获取内容
                    return self.fetch_webpage(original_url)
                else:
                    logger.info("  ❌ 未找到微信公众号原文链接，使用飞书页面内容")
                    return feishu_content

            # 获取针对特定网站的请求头
            headers = self._get_site_specific_headers(url)

            # logger.info(f"正在获取网页内容: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # 获取原始内容
            raw_content = response.content

            # 处理压缩内容
            content_encoding = response.headers.get('Content-Encoding', '').lower()
            if content_encoding:
                raw_content = self._decompress_content(raw_content, content_encoding)

            # 检测编码
            detected_encoding = self._detect_encoding(raw_content, response.encoding)

            # 解码内容
            try:
                content = raw_content.decode(detected_encoding)
            except UnicodeDecodeError:
                # 如果检测的编码失败，尝试UTF-8
                try:
                    content = raw_content.decode('utf-8', errors='replace')
                except:
                    content = raw_content.decode('latin-1')

            # 检查是否是JavaScript重定向页面（如今日头条）
            if self._is_js_redirect_page(content):
                logger.warning(f"检测到JavaScript重定向页面: {url}")
                logger.info("提示: 如果安装了 Playwright，程序会自动使用它处理此类页面")
                # 注意：实际的特殊处理逻辑在url_to_markdown.py中通过special_site_handler实现

            # logger.info(f"成功获取网页内容，大小: {len(content)} 字符")
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"获取网页失败: {e}")
            return None

    def _is_js_redirect_page(self, content: str) -> bool:
        """
        检测是否是JavaScript重定向页面
        
        今日头条等网站会返回一个包含大量JavaScript代码的页面，
        而不是实际的HTML内容。这个方法用于检测这种情况。
        """
        # 检查内容长度和特征
        if len(content) < 1000:
            return False

        # 检查是否主要包含JavaScript代码而缺少实际内容
        js_indicators = [
            'window._$jsvmprt',
            'var glb;',
            'function(b,e,f)',
            'typeof window?global:window',
            '_$jsvmprt=function',
            '<script>var glb'
        ]

        js_count = sum(1 for indicator in js_indicators if indicator in content)

        # 检查是否缺少实际的HTML内容结构
        html_indicators = [
            '<article',
            '<main',
            '<div class="content',
            '<div class="article',
            '<p>',
            '<body><script>',  # 如果body标签后直接是script，可能是重定向页面
        ]
        html_count = sum(1 for indicator in html_indicators if indicator in content)
        
        # 检查body标签是否为空或只包含script
        import re
        body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.IGNORECASE | re.DOTALL)
        if body_match:
            body_content = body_match.group(1).strip()
            # 如果body内容主要是script标签，可能是重定向页面
            if body_content and len(body_content) > 0:
                script_ratio = len(re.findall(r'<script', body_content, re.IGNORECASE)) / max(len(re.findall(r'<[^>]+>', body_content)), 1)
                if script_ratio > 0.7:  # 如果超过70%的标签是script，可能是重定向页面
                    return True

        # 如果检测到多个JavaScript指示器且缺少HTML内容，判定为重定向页面
        return js_count >= 2 and html_count == 0

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
