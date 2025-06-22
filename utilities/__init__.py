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

__all__ = [
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
    'create_markdown_importer'
]