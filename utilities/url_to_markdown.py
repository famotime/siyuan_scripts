"""
URL转Markdown转换器
整合各个模块提供完整的转换功能
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import re
from functools import partial
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

try:
    from .web_downloader import WebDownloader
    from .html_converter import HTMLConverter
    from .media_downloader import MediaDownloader
    from .clipboard_manager import ClipboardManager
    from .special_site_handler import SpecialSiteHandler
except ImportError:
    from web_downloader import WebDownloader
    from html_converter import HTMLConverter
    from media_downloader import MediaDownloader
    from clipboard_manager import ClipboardManager
    from special_site_handler import SpecialSiteHandler

logger = logging.getLogger(__name__)


class URLToMarkdownConverter:
    """URL转Markdown转换器"""

    def __init__(self, output_dir: str = "output", converter_lib: str = "auto"):
        """
        初始化转换器

        :param output_dir: 输出目录
        :param converter_lib: 转换库选择 ("markdownify", "html2text", "auto")
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 初始化各个组件
        self.web_downloader = WebDownloader()
        self.html_converter = HTMLConverter(converter_lib)
        self.media_downloader = MediaDownloader(self.output_dir)
        self.clipboard_manager = ClipboardManager()
        self.special_site_handler = SpecialSiteHandler()
        self.url_timeout_seconds = 60
        self.last_error: Dict[str, str] = {}
        self._tracking_query_params = {
            "timestamp",
            "req_id",
            "req_id_new",
            "share_did",
            "share_uid",
            "share_token",
            "use_new_style",
            "from",
            "source",
            "wid",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "spm",
            "fbclid",
            "gclid",
            "yclid",
        }

    def _set_last_error(self, code: str, message: str, stage: str = "") -> None:
        """记录最近一次转换错误信息，便于批处理回退。"""
        self.last_error = {
            "code": code,
            "message": message,
            "stage": stage,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _remaining_seconds(self, start_time: float) -> float:
        """返回当前URL剩余处理预算秒数。"""
        return self.url_timeout_seconds - (time.monotonic() - start_time)

    async def _run_blocking_with_timeout(self, func, *args, timeout: float):
        """在线程池执行阻塞函数，并受限于剩余预算。"""
        loop = asyncio.get_running_loop()
        return await asyncio.wait_for(loop.run_in_executor(None, partial(func, *args)), timeout=timeout)

    def _format_failed_url_note(self, item: Dict[str, str]) -> str:
        """格式化失败URL的人工复核条目。"""
        failed_url = item.get('url', '')
        lines = [
            "[待人工验证]",
            f"时间: {item.get('timestamp', '')}",
            f"URL: [{failed_url}]({failed_url})" if failed_url else "URL: ",
            f"错误: {item.get('message', '')}",
        ]
        if item.get("stage"):
            lines.append(f"阶段: {item['stage']}")
        return "\n".join(lines)

    def _save_collected_notes(self, collected_notes: List[str], failed_items: List[Dict[str, str]]) -> None:
        """将碎笔记内容与失败URL条目统一写入碎笔记文件。"""
        sections: List[str] = []
        if collected_notes:
            sections.extend(collected_notes)
        if failed_items:
            sections.extend([self._format_failed_url_note(item) for item in failed_items])

        if not sections:
            return

        md_content = "\n\n%%%\n\n".join(sections)
        collected_notes_filename = f"碎笔记{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        collected_notes_filename = self.get_unique_filename(collected_notes_filename)
        collected_notes_md_path = self.output_dir / collected_notes_filename
        collected_notes_md_path.write_text(md_content, encoding='utf-8')
        logger.info(f"Markdown文件已保存: {collected_notes_md_path}")

    def _build_dedup_key(self, raw_url: str) -> str:
        """构建URL去重键，合并同一资源的不同分享参数链接。"""
        try:
            parsed = urlparse(raw_url.strip())
        except Exception:
            return raw_url.strip()

        host = parsed.netloc.lower()
        path = parsed.path.rstrip("/")
        query_items = parse_qsl(parsed.query, keep_blank_values=False)

        if "toutiao.com" in host:
            article_match = re.search(r"/article/(\d+)", path)
            if article_match:
                return f"toutiao:article:{article_match.group(1)}"

            query_map = {k: v for k, v in query_items}
            for key in ("group_id", "article_id", "item_id"):
                if query_map.get(key):
                    return f"toutiao:article:{query_map[key]}"

        filtered_query = []
        for key, value in query_items:
            key_lower = key.lower()
            if key_lower in self._tracking_query_params:
                continue
            if key_lower.startswith("utm_"):
                continue
            filtered_query.append((key, value))

        filtered_query.sort()
        normalized_query = urlencode(filtered_query, doseq=True)
        normalized_path = path or "/"

        return urlunparse((
            parsed.scheme.lower(),
            host,
            normalized_path,
            "",
            normalized_query,
            "",
        ))

    def _deduplicate_urls(self, urls: List[str]) -> List[str]:
        """按原顺序去重URL，避免重复处理。"""
        seen = set()
        deduplicated_urls: List[str] = []

        for url in urls:
            dedup_key = self._build_dedup_key(url)
            if dedup_key in seen:
                logger.info(f"跳过重复URL: {url}")
                continue
            seen.add(dedup_key)
            deduplicated_urls.append(url)

        return deduplicated_urls

    def _unwrap_image_links_for_x(self, html_content: str, source_url: str) -> str:
        """X帖子场景下，将仅包裹图片的链接解包为纯图片，避免Markdown出现图片外链包装。"""
        try:
            domain = (urlparse(source_url).netloc or "").lower()
            if "x.com" not in domain and "twitter.com" not in domain:
                return html_content
        except Exception:
            return html_content

        # 常见格式：<a href="..."><img ...></a> 或 <a ...><picture>...<img ...></picture></a>
        pattern = re.compile(
            r"<a\b[^>]*>\s*((?:<picture\b[^>]*>.*?</picture>|<img\b[^>]*>))\s*</a>",
            re.IGNORECASE | re.DOTALL,
        )
        return pattern.sub(r"\1", html_content)

    def _strip_markdown_image_wrappers_for_x(self, markdown_content: str, source_url: str) -> str:
        """X帖子场景下，把[![...](img)](link)压平为![...](img)。"""
        try:
            domain = (urlparse(source_url).netloc or "").lower()
            if "x.com" not in domain and "twitter.com" not in domain:
                return markdown_content
        except Exception:
            return markdown_content

        # [![alt](img)](link) -> ![alt](img)
        pattern = re.compile(
            r"\[\s*!\[([^\]]*)\]\(([^)\n]+)\)\s*\]\(([^)\n]+)\)",
            re.IGNORECASE,
        )
        return pattern.sub(r"![\1](\2)", markdown_content)

    def generate_filename(self, title: str, url: str) -> str:
        """
        生成文件名

        :param title: 网页标题
        :param url: 网页URL
        :return: 安全的文件名
        """
        # 改进的文件名清理逻辑，保留更多有意义的标点符号
        filename = title

        # 第一步：替换文件系统不允许的字符为安全字符
        # Windows/Linux/macOS 文件名不能包含的字符: \ / : * ? " < > |
        invalid_chars = {
            '\\': '＼',  # 反斜杠 -> 全角反斜杠
            '/': '／',   # 斜杠 -> 全角斜杠
            ':': '：',   # 冒号 -> 中文冒号
            '*': '＊',   # 星号 -> 全角星号
            '?': '？',   # 问号 -> 中文问号
            '"': '＂',   # 双引号 -> 全角双引号
            '<': '＜',   # 小于号 -> 全角小于号
            '>': '＞',   # 大于号 -> 全角大于号
            '|': '｜'    # 竖线 -> 全角竖线
        }

        for invalid_char, replacement in invalid_chars.items():
            filename = filename.replace(invalid_char, replacement)

        # 第二步：处理连续的空格和特殊字符
        # 将多个连续空格替换为单个空格
        filename = re.sub(r'\s+', ' ', filename)

        # 第三步：清理首尾空格和特殊字符
        filename = filename.strip(' .-_')

        # 第四步：如果标题为空或太短，使用URL的域名
        if not filename or len(filename) < 3:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            filename = parsed_url.netloc.replace('.', '-')

        # 第五步：限制文件名长度（考虑中文字符）
        if len(filename) > 80:  # 增加长度限制，因为中文字符占用更多空间
            filename = filename[:80]
            # 确保不在中文字符中间截断
            if len(filename.encode('utf-8')) > len(filename):
                # 包含中文字符，更保守地截断
                filename = filename[:60]

        # 第六步：再次清理可能的尾部字符
        filename = filename.strip(' .-_')

        # 第七步：添加文件扩展名
        filename = f"{filename}.md"

        return filename

    def get_unique_filename(self, filename: str) -> str:
        """
        获取唯一的文件名，如果文件已存在则自动添加数字后缀

        :param filename: 原始文件名
        :return: 唯一的文件名
        """
        output_path = self.output_dir / filename

        # 如果文件不存在，直接返回原文件名
        if not output_path.exists():
            return filename

        # 文件已存在，生成带数字后缀的文件名
        base_name = filename.rsplit('.', 1)[0]  # 去掉扩展名
        extension = filename.rsplit('.', 1)[-1]  # 获取扩展名

        counter = 1
        while True:
            new_filename = f"{base_name}_{counter}.{extension}"
            new_path = self.output_dir / new_filename

            if not new_path.exists():
                return new_filename

            counter += 1

            # 防止无限循环，最多尝试100次
            if counter > 100:
                # 如果还是重复，添加时间戳
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"{base_name}_{timestamp}.{extension}"

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
        # header_parts = [f"# {page_info['title']}", ""]
        header_parts = [f"", ""]

        # 添加元数据
        metadata = [
            f"**原始链接：** [{url}]({url})",
            f"**保存时间：** {current_time}",
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
        full_document = '\n'.join(header_parts) + '\n' + markdown_content

        return full_document

    async def convert_url_to_markdown(self, url: str, output_filename: str = None, download_media: bool = True) -> Optional[Path]:
        """
        将URL转换为Markdown文件

        :param url: 要转换的URL
        :param output_filename: 输出文件名（可选）
        :param download_media: 是否下载媒体文件
        :return: 输出文件路径，失败时返回None
        """
        self.last_error = {}
        start_time = time.monotonic()

        try:
            # 检查是否需要特殊处理
            if self.special_site_handler.can_handle(url):
                logger.info(f"使用特殊处理器处理: {url}")
                remaining = self._remaining_seconds(start_time)
                if remaining <= 0:
                    self._set_last_error("TIMEOUT_TOTAL", f"超时：单URL处理超过{self.url_timeout_seconds}秒", "special_handler")
                    return None

                special_result = await self._run_blocking_with_timeout(
                    self.special_site_handler.get_content,
                    url,
                    timeout=remaining
                )

                if special_result:
                    html_content = special_result['html_content']
                    page_info = {
                        'title': special_result['title'],
                        'description': special_result['description'],
                        'author': special_result['author'],
                        'publish_time': special_result['publish_time']
                    }
                else:
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc.lower()
                    special_error = getattr(self.special_site_handler, "last_error", None)

                    if "toutiao.com" in domain:
                        if special_error:
                            self.last_error = special_error
                        else:
                            self._set_last_error("DYNAMIC_PAGE_UNRESOLVED", "动态页面未成功解析，已转人工处理", "special_handler")
                        logger.warning("特殊处理器未成功解析今日头条内容，转人工处理")
                        return None

                    logger.warning("特殊处理器处理失败，回退到普通方式")
                    remaining = self._remaining_seconds(start_time)
                    if remaining <= 0:
                        self._set_last_error("TIMEOUT_TOTAL", f"超时：单URL处理超过{self.url_timeout_seconds}秒", "web_fetch")
                        return None

                    html_content = await self._run_blocking_with_timeout(
                        self.web_downloader.fetch_webpage,
                        url,
                        timeout=remaining
                    )
                    if not html_content:
                        if special_error:
                            self.last_error = special_error
                        else:
                            self._set_last_error("FETCH_FAILED", "网页内容抓取失败", "web_fetch")
                        return None
                    if self.web_downloader._is_js_redirect_page(html_content):
                        special_error = getattr(self.special_site_handler, "last_error", None)
                        if special_error:
                            self.last_error = special_error
                        else:
                            self._set_last_error("DYNAMIC_PAGE_UNRESOLVED", "动态页面未成功解析，已转人工处理", "web_fetch")
                        return None
                    page_info = self.web_downloader.extract_page_info(html_content)
            else:
                # 获取网页内容
                remaining = self._remaining_seconds(start_time)
                if remaining <= 0:
                    self._set_last_error("TIMEOUT_TOTAL", f"超时：单URL处理超过{self.url_timeout_seconds}秒", "web_fetch")
                    return None

                html_content = await self._run_blocking_with_timeout(
                    self.web_downloader.fetch_webpage,
                    url,
                    timeout=remaining
                )
                if not html_content:
                    self._set_last_error("FETCH_FAILED", "网页内容抓取失败", "web_fetch")
                    return None

                # 检查是否是JavaScript重定向页面
                if self.web_downloader._is_js_redirect_page(html_content):
                    logger.warning(f"检测到JavaScript重定向页面: {url}")
                    
                    # 如果检测到重定向页面，且URL是今日头条，尝试使用特殊处理器
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc.lower()
                    
                    if 'toutiao.com' in domain and self.special_site_handler.can_handle(url):
                        logger.info("检测到今日头条链接且为JavaScript重定向页面，尝试使用Playwright处理...")
                        remaining = self._remaining_seconds(start_time)
                        if remaining <= 0:
                            self._set_last_error("TIMEOUT_TOTAL", f"超时：单URL处理超过{self.url_timeout_seconds}秒", "special_handler")
                            return None

                        special_result = await self._run_blocking_with_timeout(
                            self.special_site_handler.get_content,
                            url,
                            timeout=remaining
                        )
                        
                        if special_result:
                            logger.info("✅ 使用Playwright成功获取内容")
                            html_content = special_result['html_content']
                            page_info = {
                                'title': special_result['title'],
                                'description': special_result['description'],
                                'author': special_result['author'],
                                'publish_time': special_result['publish_time']
                            }
                        else:
                            logger.warning("Playwright处理失败，转人工处理")
                            special_error = getattr(self.special_site_handler, "last_error", None)
                            if special_error:
                                self.last_error = special_error
                            else:
                                self._set_last_error("DYNAMIC_PAGE_UNRESOLVED", "动态页面未成功解析，已转人工处理", "special_handler")
                            logger.info(self.special_site_handler.get_installation_guide())
                            return None
                    else:
                        # 不是今日头条或其他特殊网站，只提示
                        page_info = self.web_downloader.extract_page_info(html_content)
                        logger.info(self.special_site_handler.get_installation_guide())
                else:
                    # 正常页面，直接提取信息
                    page_info = self.web_downloader.extract_page_info(html_content)

            # logger.info(f"页面标题: {page_info['title']}")

            # 下载媒体文件
            media_mapping = {}
            if download_media:
                # logger.info("开始下载媒体文件...")
                media_urls = self.html_converter.extract_media_urls(html_content, url)
                # logger.info(f"发现 {len(media_urls)} 个媒体文件")

                if media_urls:
                    remaining = self._remaining_seconds(start_time)
                    if remaining <= 0:
                        self._set_last_error("TIMEOUT_TOTAL", f"超时：单URL处理超过{self.url_timeout_seconds}秒", "media_download")
                        return None
                    media_mapping = await asyncio.wait_for(
                        self.media_downloader.download_media_batch(media_urls, url),
                        timeout=remaining
                    )
                    # logger.info(f"成功下载 {len(media_mapping)} 个媒体文件")
                # else:
                #     logger.warning("未发现任何媒体文件URL")

            # 清理HTML内容
            clean_html = self.html_converter.clean_html_for_conversion(html_content, source_url=url)
            clean_html = self._unwrap_image_links_for_x(clean_html, url)

            # 转换为Markdown
            markdown_content = self.html_converter.convert_html_to_markdown(clean_html)
            markdown_content = self._strip_markdown_image_wrappers_for_x(markdown_content, url)

            # 更新媒体链接
            if media_mapping:
                markdown_content = self.html_converter.update_media_links(markdown_content, media_mapping)

            # 生成文件名
            if not output_filename:
                output_filename = self.generate_filename(page_info['title'], url)

            # 确保文件名唯一，避免覆盖
            output_filename = self.get_unique_filename(output_filename)
            output_path = self.output_dir / output_filename

            # 构建完整文档
            full_markdown = self.build_markdown_document(page_info, url, markdown_content)

            # 保存文件
            output_path.write_text(full_markdown, encoding='utf-8')
            logger.info(f"Markdown文件已保存: {output_path}")
            self.last_error = {}
            return output_path

        except asyncio.TimeoutError:
            self._set_last_error("TIMEOUT_TOTAL", f"超时：单URL处理超过{self.url_timeout_seconds}秒", "timeout_guard")
            logger.error(f"转换超时: {url}")
            return None
        except Exception as e:
            if not self.last_error:
                self._set_last_error("CONVERT_ERROR", str(e), "convert")
            logger.error(f"转换过程出错: {e}")
            return None

    async def convert_urls_from_clipboard(self, download_media: bool = True) -> List[Path]:
        """
        从剪贴板读取URL并批量转换为Markdown文件

        :param download_media: 是否下载媒体文件
        :return: 成功转换的文件路径列表
        """
        urls, collected_notes = self.clipboard_manager.read_urls_from_clipboard()
        items = [{"url": url} for url in urls]
        return await self.convert_url_items(items, download_media=download_media, collected_notes=collected_notes)

    def load_url_items_from_file(self, input_path: str) -> List[Dict[str, str]]:
        payload_path = Path(input_path)
        raw_content = payload_path.read_text(encoding="utf-8")
        stripped = raw_content.strip()
        if not stripped:
            return []

        if payload_path.suffix.lower() == ".json" or stripped.startswith("{") or stripped.startswith("["):
            payload = json.loads(stripped)
            if isinstance(payload, dict):
                items = payload.get("items", [])
            elif isinstance(payload, list):
                items = payload
            else:
                raise ValueError("URL批处理文件格式无效")

            normalized_items = []
            for item in items:
                if isinstance(item, str):
                    normalized_items.append({"url": item})
                    continue
                url = (item.get("url") or "").strip()
                if not url:
                    continue
                normalized_items.append(
                    {
                        "url": url,
                        "title": (item.get("title") or "").strip(),
                    }
                )
            return normalized_items

        return [{"url": line.strip()} for line in stripped.splitlines() if line.strip()]

    async def convert_urls_from_file(self, input_path: str, download_media: bool = True) -> List[Path]:
        items = self.load_url_items_from_file(input_path)
        return await self.convert_url_items(items, download_media=download_media)

    async def convert_url_items(
        self,
        items: List[Dict[str, str]],
        download_media: bool = True,
        collected_notes: Optional[List[str]] = None,
    ) -> List[Path]:
        deduplicated_items: List[Dict[str, str]] = []
        seen_urls = set()
        for item in items:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            normalized = self._build_dedup_key(url)
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)
            deduplicated_items.append(
                {
                    "url": url,
                    "title": (item.get("title") or "").strip(),
                }
            )

        successful_files = []
        failed_items: List[Dict[str, str]] = []
        if deduplicated_items:
            for i, item in enumerate(deduplicated_items, 1):
                url = item["url"]
                try:
                    # 检查是否是飞书链接，如果是则显示特殊提示
                    if url.startswith("https://waytoagi.feishu.cn/"):
                        logger.info(f"\n[{i}/{len(deduplicated_items)}] 正在处理飞书链接: {url}")
                        logger.info("  🔍 检测飞书链接，将自动提取微信原文链接...")
                    else:
                        logger.info(f"\n[{i}/{len(deduplicated_items)}] 正在转换: {url}")

                    output_filename = None
                    if item.get("title"):
                        output_filename = self.generate_filename(item["title"], url)

                    # 转换URL为Markdown，不指定文件名，让系统自动生成
                    result_path = await self.convert_url_to_markdown(
                        url=url,
                        output_filename=output_filename,
                        download_media=download_media
                    )

                    if result_path:
                        successful_files.append(result_path)
                        file_size = result_path.stat().st_size
                        # logger.info(f"    ✓ 转换成功! 文件: {result_path.name} ({file_size:,} 字节)")
                    else:
                        logger.error(f"    ✗ 转换失败: {url}")
                        last_error = self.last_error or {}
                        failed_items.append({
                            "url": url,
                            "message": last_error.get("message", "转换失败，未返回具体错误"),
                            "stage": last_error.get("stage", ""),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        })

                except Exception as e:
                    logger.error(f"    ✗ 转换出错: {url}, 错误: {e}")
                    failed_items.append({
                        "url": url,
                        "message": str(e),
                        "stage": "batch_loop",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })

            logger.info(f"\n批量转换完成! 成功: {len(successful_files)}/{len(deduplicated_items)}")
        else:
            logger.warning("没有找到有效的URL")

        self._save_collected_notes(collected_notes or [], failed_items)
        return successful_files

    def is_clipboard_available(self) -> bool:
        """检查剪贴板功能是否可用"""
        return self.clipboard_manager.is_available()
