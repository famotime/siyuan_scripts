"""
HTML转Markdown转换器模块
支持多种转换库和媒体文件处理
"""

import logging
import re
import html
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse
from pathlib import Path

try:
    from bs4 import BeautifulSoup, Comment
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

logger = logging.getLogger(__name__)


class CustomMarkdownConverter(markdownify.MarkdownConverter):
    """
    自定义MarkdownConverter，将div标签转换为换行
    """
    def convert_div(self, el, text, convert_as_inline=False, **kwargs):
        """将div标签转换为换行"""
        # 检查div是否只包含空白内容、br标签或HTML实体
        if not text.strip():
            # 检查原始元素是否包含br标签或只包含空白字符/HTML实体
            original_text = el.get_text(strip=True) if hasattr(el, 'get_text') else ''
            has_br = el.find('br') is not None if hasattr(el, 'find') else False

            # 如果div中包含br标签，或者原始文本为空（可能包含&nbsp;等HTML实体）
            if has_br or not original_text:
                # 返回两个换行（产生空行效果）
                return '\n\n'
            else:
                # 如果div为空，返回一个换行
                return '\n'
        # 如果div内容不为空，在内容前后添加换行
        return f'\n{text}\n'


class HTMLConverter:
    """HTML转Markdown转换器"""

    def __init__(self, converter_lib: str = "auto"):
        """
        初始化转换器

        :param converter_lib: 转换库选择 ("markdownify", "html2text", "auto")
        """
        # 选择转换库
        self.converter_lib = self._select_converter_lib(converter_lib)
        logger.info(f"使用转换库: {self.converter_lib}")

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

            # 提取图片 - 支持多种属性
            for img in soup.find_all('img'):
                # 尝试多种可能的图片URL属性
                src_attrs = ['src', 'data-src', 'data-original', 'data-lazy-src', 'data-actualsrc', 'data-url']
                for attr in src_attrs:
                    src = img.get(attr)
                    if src and src.strip():
                        # 跳过base64图片和无效链接
                        if not src.startswith('data:') and len(src) > 10:
                            full_url = urljoin(base_url, src.strip())
                            media_urls.add(full_url)
                            logger.debug(f"提取到图片URL ({attr}): {full_url}")

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
            # 使用正则表达式提取 - 支持更多属性
            img_patterns = [
                r'<img[^>]*src=["\']([^"\']*)["\']',
                r'<img[^>]*data-src=["\']([^"\']*)["\']',
                r'<img[^>]*data-original=["\']([^"\']*)["\']',
                r'<img[^>]*data-lazy-src=["\']([^"\']*)["\']',
                r'<img[^>]*data-actualsrc=["\']([^"\']*)["\']'
            ]

            for pattern in img_patterns:
                for match in re.finditer(pattern, html_content, re.IGNORECASE):
                    src = match.group(1).strip()
                    if src and not src.startswith('data:') and len(src) > 10:
                        full_url = urljoin(base_url, src)
                        media_urls.add(full_url)

            video_pattern = r'<video[^>]*src=["\']([^"\']*)["\']'
            for match in re.finditer(video_pattern, html_content, re.IGNORECASE):
                full_url = urljoin(base_url, match.group(1))
                media_urls.add(full_url)

        # logger.info(f"总共提取到 {len(media_urls)} 个媒体URL")
        return list(media_urls)

    def clean_html_for_conversion(self, html_content: str, source_url: str = "") -> str:
        """
        清理HTML内容用于转换

        :param html_content: 原始HTML
        :param source_url: 源URL，用于站点特定的内容提取策略
        :return: 清理后的HTML
        """
        if not HAS_BS4:
            return self._clean_html_simple(html_content)

        soup = BeautifulSoup(html_content, 'html.parser')

        # 首先处理懒加载图片：将data-src等属性移动到src
        for img in soup.find_all('img'):
            # 检查是否有懒加载属性但没有src或src为空
            current_src = img.get('src')
            if not current_src or current_src.strip() == '' or current_src.startswith('data:'):
                # 尝试从懒加载属性获取真实URL
                lazy_attrs = ['data-src', 'data-original', 'data-lazy-src', 'data-actualsrc', 'data-url']
                for attr in lazy_attrs:
                    lazy_src = img.get(attr)
                    if lazy_src and lazy_src.strip() and not lazy_src.startswith('data:'):
                        img['src'] = lazy_src.strip()
                        logger.debug(f"将 {attr} 移动到 src: {lazy_src[:50]}...")
                        break

        # 微信公众号专用预处理
        is_weixin = self._is_weixin_url(source_url)
        if is_weixin:
            self._clean_weixin_specific(soup)

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
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 尝试提取主要内容
        main_content = None

        # 微信公众号专用选择器（优先匹配）
        weixin_selectors = [
            '#js_content',                    # 微信文章正文主容器
            '.rich_media_content',            # 富媒体内容区域
            '#page-content',                  # 页面内容区域
            '.rich_media_area_primary_inner', # 主内容区内层
        ]

        # 通用选择器
        generic_selectors = [
            'main', 'article', '[role="main"]',
            '.content', '#content', '.main', '#main',
            '.post-content', '.entry-content', '.article-content',
            '.post-body', '.entry-body'
        ]

        # 根据URL类型选择优先的选择器列表
        content_selectors = weixin_selectors + generic_selectors if is_weixin else generic_selectors + weixin_selectors

        for selector in content_selectors:
            element = soup.select_one(selector)
            if element and len(element.get_text().strip()) > 200:
                main_content = element
                logger.info(f"使用选择器 '{selector}' 提取到主要内容")
                break

        if main_content:
            return str(main_content)
        else:
            # 如果没有找到主要内容，使用body
            body = soup.find('body')
            return str(body) if body else str(soup)

    @staticmethod
    def _is_weixin_url(url: str) -> bool:
        """判断是否为微信公众号URL"""
        if not url:
            return False
        return 'mp.weixin.qq.com' in url

    @staticmethod
    def _clean_weixin_specific(soup: 'BeautifulSoup') -> None:
        """微信公众号页面专用清理：移除广告、推荐等非正文元素"""
        # 移除微信特有的非正文区域
        noise_selectors = [
            '#js_pc_qr_code',             # PC端二维码引导
            '#content_bottom_area',        # 底部区域
            '.reward_area',                # 赞赏区域
            '#js_profile_qrcode',         # 公众号二维码
            '.rich_media_tool',            # 工具栏
            '#js_toobar3',                 # 底部工具栏
            '.qr_code_pc',                # PC二维码
            '#js_share_source',           # 分享来源
            '.rich_media_area_extra',     # 额外区域（推荐关注等）
            '#js_tags_preview_toast',     # 标签预览
            '.function_mod',              # 功能模块
            '#js_read_area3',             # 阅读区域3（底部推荐阅读）
            '.reward_area_primary',       # 赞赏主区域
            '#js_reward_area',            # 赞赏区域
            '.rich_media_area_ft',        # 底部区域
            '#js_toobar',                 # 工具栏
            '.media_tool_meta',           # 媒体工具元信息
            '.article-tag-card',          # 文章标签卡片
            '.rich_media_title_wrp',      # 标题包装器（保留标题本身）
            # 赞赏弹窗区域（Playwright 渲染后的实际选择器）
            '.reward_dialog',             # 赞赏弹窗
            '.discuss_more_dialog_wrp',   # 讨论弹窗
            '.author_profile-info',       # 作者信息卡（弹窗内）
            '.author_profile-pay_area',   # 支付区域
            '.author_profile-articles',   # 作品列表
            '.dialog-pay',                # 支付弹窗
        ]
        for selector in noise_selectors:
            for element in soup.select(selector):
                element.decompose()
        # 移除 role=dialog 的元素（赞赏弹窗等）
        for element in soup.find_all(attrs={"role": "dialog"}):
            element.decompose()
        # 移除 visibility:hidden 的元素
        for element in soup.find_all(style=re.compile(r'visibility\s*:\s*hidden')):
            element.decompose()

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
            # 使用自定义的转换器处理div标签
            converter = CustomMarkdownConverter(
                heading_style=markdownify.ATX,
                bullets='-',
                strong_tag='**',
                em_tag='*'
            )
            markdown_content = converter.convert(html_content)
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
        # 支持多种图片属性的转换
        img_patterns = [
            # 有alt属性的图片
            (r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)'),
            # data-src属性的图片（懒加载）
            (r'<img[^>]*data-src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)'),
            (r'<img[^>]*data-src=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)'),
            # data-original属性的图片
            (r'<img[^>]*data-original=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)'),
            (r'<img[^>]*data-original=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)'),
            # 普通src属性的图片
            (r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)')
        ]

        for pattern, replacement in img_patterns:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

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

        if not media_mapping:
            return content

        logger.info(f"开始替换媒体链接，映射数量: {len(media_mapping)}")

        for original_url, local_path in media_mapping.items():
            # 记录替换前的内容
            before_count = content.count(original_url)
            
            # 如果URL中没有出现，尝试处理URL编码和变体
            if before_count == 0:
                # 尝试URL编码变体
                encoded_variants = [
                    original_url.replace(' ', '%20'),
                    original_url.replace(' ', '+'),
                    original_url.replace('%20', ' '),
                    original_url.replace('+', ' '),
                ]
                for variant in encoded_variants:
                    if variant in content:
                        content = content.replace(variant, local_path)
                        logger.debug(f"替换URL变体: {variant[:50]}... -> {local_path}")
                        break

            # 多种格式的链接替换
            replacements = [
                # Markdown图片格式: ![alt](url)
                (f"]({original_url})", f"]({local_path})"),
                # Markdown图片格式（带空格）: ![alt]( url )
                (f"]( {original_url} )", f"]({local_path})"),
                # HTML img标签 src属性
                (f'src="{original_url}"', f'src="{local_path}"'),
                (f"src='{original_url}'", f"src='{local_path}'"),
                (f'src={original_url}', f'src={local_path}'),
                # HTML img标签 data-src属性（懒加载）
                (f'data-src="{original_url}"', f'data-src="{local_path}"'),
                (f"data-src='{original_url}'", f"data-src='{local_path}'"),
                # HTML img标签 data-original属性
                (f'data-original="{original_url}"', f'data-original="{local_path}"'),
                (f"data-original='{original_url}'", f"data-original='{local_path}'"),
                # 直接替换URL（作为最后手段）
                (original_url, local_path)
            ]

            replaced_count = 0
            for old_pattern, new_pattern in replacements:
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    replaced_count += content.count(new_pattern) - content.count(old_pattern)
                    # 只替换一次，避免重复替换
                    break

            if replaced_count > 0 or before_count > 0:
                logger.info(f"已替换图片链接: {original_url[:60]}... -> {local_path}")
            else:
                logger.warning(f"未找到可替换的链接: {original_url[:60]}...")

        return content