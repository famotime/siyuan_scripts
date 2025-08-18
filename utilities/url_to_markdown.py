"""
URL转Markdown转换器
整合各个模块提供完整的转换功能
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import re

from .web_downloader import WebDownloader
from .html_converter import HTMLConverter
from .media_downloader import MediaDownloader
from .clipboard_manager import ClipboardManager
from .special_site_handler import SpecialSiteHandler

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
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            filename = parsed_url.netloc.replace('.', '-')

        # 限制文件名长度
        if len(filename) > 50:
            filename = filename[:50]

        base_filename = filename
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

            # 防止无限循环，最多尝试1000次
            if counter > 1000:
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
        header_parts = [f"# {page_info['title']}", ""]

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
        try:
            # 检查是否需要特殊处理
            if self.special_site_handler.can_handle(url):
                logger.info(f"使用特殊处理器处理: {url}")
                special_result = self.special_site_handler.get_content(url)

                if special_result:
                    html_content = special_result['html_content']
                    page_info = {
                        'title': special_result['title'],
                        'description': special_result['description'],
                        'author': special_result['author'],
                        'publish_time': special_result['publish_time']
                    }
                else:
                    logger.warning("特殊处理器处理失败，回退到普通方式")
                    html_content = self.web_downloader.fetch_webpage(url)
                    if not html_content:
                        return None
                    page_info = self.web_downloader.extract_page_info(html_content)
            else:
                # 获取网页内容
                html_content = self.web_downloader.fetch_webpage(url)
                if not html_content:
                    return None

                # 提取页面信息
                page_info = self.web_downloader.extract_page_info(html_content)

                # 检查是否是JavaScript重定向页面
                if self.web_downloader._is_js_redirect_page(html_content):
                    logger.warning(f"检测到JavaScript重定向页面，建议安装selenium处理: {url}")
                    logger.info(self.special_site_handler.get_installation_guide())

            # logger.info(f"页面标题: {page_info['title']}")

            # 下载媒体文件
            media_mapping = {}
            if download_media:
                # logger.info("开始下载媒体文件...")
                media_urls = self.html_converter.extract_media_urls(html_content, url)
                # logger.info(f"发现 {len(media_urls)} 个媒体文件")

                if media_urls:
                    media_mapping = await self.media_downloader.download_media_batch(media_urls, url)
                    # logger.info(f"成功下载 {len(media_mapping)} 个媒体文件")
                # else:
                #     logger.warning("未发现任何媒体文件URL")

            # 清理HTML内容
            clean_html = self.html_converter.clean_html_for_conversion(html_content)

            # 转换为Markdown
            markdown_content = self.html_converter.convert_html_to_markdown(clean_html)

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

            return output_path

        except Exception as e:
            logger.error(f"转换过程出错: {e}")
            return None

    async def convert_urls_from_clipboard(self, download_media: bool = True) -> List[Path]:
        """
        从剪贴板读取URL并批量转换为Markdown文件

        :param download_media: 是否下载媒体文件
        :return: 成功转换的文件路径列表
        """
        urls, collected_notes = self.clipboard_manager.read_urls_from_clipboard()

        if collected_notes:
            md_content = "\n\n%%%\n\n".join(collected_notes)
            # 保存文件
            collected_notes_filename = f"碎笔记{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            collected_notes_filename = self.get_unique_filename(collected_notes_filename)
            collected_notes_md_path = self.output_dir / collected_notes_filename
            collected_notes_md_path.write_text(md_content, encoding='utf-8')
            logger.info(f"Markdown文件已保存: {collected_notes_md_path}")

        # logger.info(f"开始批量转换 {len(urls)} 个URL...")
        successful_files = []
        if urls:
            for i, url in enumerate(urls, 1):
                try:
                    # 检查是否是飞书链接，如果是则显示特殊提示
                    if url.startswith("https://waytoagi.feishu.cn/"):
                        logger.info(f"\n[{i}/{len(urls)}] 正在处理飞书链接: {url}")
                        logger.info("  🔍 检测飞书链接，将自动提取微信原文链接...")
                    else:
                        logger.info(f"\n[{i}/{len(urls)}] 正在转换: {url}")

                    # 转换URL为Markdown，不指定文件名，让系统自动生成
                    result_path = await self.convert_url_to_markdown(
                        url=url,
                        output_filename=None,  # 使用网页标题自动生成文件名
                        download_media=download_media
                    )

                    if result_path:
                        successful_files.append(result_path)
                        file_size = result_path.stat().st_size
                        # logger.info(f"    ✓ 转换成功! 文件: {result_path.name} ({file_size:,} 字节)")
                    else:
                        logger.error(f"    ✗ 转换失败: {url}")

                except Exception as e:
                    logger.error(f"    ✗ 转换出错: {url}, 错误: {e}")

            logger.info(f"\n批量转换完成! 成功: {len(successful_files)}/{len(urls)}")
        else:
            logger.warning("没有从剪贴板找到有效的URL")

        return successful_files

    def is_clipboard_available(self) -> bool:
        """检查剪贴板功能是否可用"""
        return self.clipboard_manager.is_available()