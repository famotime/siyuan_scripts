"""
思源笔记操作工具包
提供API客户端和各种管理器的便捷导入接口
"""

from .api_client import SiyuanAPI
from .notebook import NotebookManager
from .document import DocumentManager
from .block import BlockManager
from .file_manager import FileManager
from .tree_processor import TreeProcessor
from .markdown_importer import MarkdownImporter
from .media_manager import MediaManager
from .common import setup_logging, DEFAULT_API_URL, DEFAULT_API_TOKEN
from .sql_queries import (
    COMMON_QUERIES, TABLE_QUERIES,
    get_query_by_name, get_all_query_names,
    get_table_query_by_name, get_all_table_query_names,
    get_specific_tag_query, get_custom_attribute_query
)

# URL转Markdown相关模块
from .web_downloader import WebDownloader
from .html_converter import HTMLConverter
from .media_downloader import MediaDownloader
from .clipboard_manager import ClipboardManager
from .url_to_markdown import URLToMarkdownConverter

# 便捷函数
def create_siyuan_client(api_url: str = None, api_token: str = None) -> SiyuanAPI:
    """创建思源API客户端"""
    return SiyuanAPI(api_url, api_token)

def create_managers(api_client: SiyuanAPI = None):
    """创建管理器实例"""
    if api_client is None:
        api_client = create_siyuan_client()

    notebook_manager = NotebookManager(api_client)
    document_manager = DocumentManager(api_client)
    block_manager = BlockManager(api_client)

    return notebook_manager, document_manager, block_manager

def create_media_manager(api_client: SiyuanAPI = None) -> MediaManager:
    """创建媒体管理器实例"""
    if api_client is None:
        api_client = create_siyuan_client()

    return MediaManager(api_client)

def create_markdown_importer(api_client: SiyuanAPI = None) -> MarkdownImporter:
    """创建Markdown导入器实例"""
    if api_client is None:
        api_client = create_siyuan_client()

    return MarkdownImporter(api_client)

def create_url_to_markdown_converter(output_dir: str = "output", converter_lib: str = "auto") -> URLToMarkdownConverter:
    """创建URL转Markdown转换器实例"""
    return URLToMarkdownConverter(output_dir, converter_lib)

__all__ = [
    # 思源笔记相关
    'SiyuanAPI',
    'NotebookManager',
    'DocumentManager',
    'BlockManager',
    'FileManager',
    'TreeProcessor',
    'MarkdownImporter',
    'MediaManager',
    'setup_logging',
    'DEFAULT_API_URL',
    'DEFAULT_API_TOKEN',
    'create_siyuan_client',
    'create_managers',
    'create_media_manager',
    'create_markdown_importer',

    # SQL查询相关
    'COMMON_QUERIES',
    'TABLE_QUERIES',
    'get_query_by_name',
    'get_all_query_names',
    'get_table_query_by_name',
    'get_all_table_query_names',
    'get_specific_tag_query',
    'get_custom_attribute_query',

    # URL转Markdown相关
    'WebDownloader',
    'HTMLConverter',
    'MediaDownloader',
    'ClipboardManager',
    'URLToMarkdownConverter',
    'create_url_to_markdown_converter'
]