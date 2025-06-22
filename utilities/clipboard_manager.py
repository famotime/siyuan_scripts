"""
剪贴板管理器模块
负责从剪贴板读取URL列表
"""

import logging
from typing import List

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

logger = logging.getLogger(__name__)


class ClipboardManager:
    """剪贴板管理器"""

    def __init__(self):
        """初始化剪贴板管理器"""
        if not HAS_PYPERCLIP:
            logger.error("pyperclip库未安装，无法读取剪贴板内容")

    def is_available(self) -> bool:
        """检查剪贴板功能是否可用"""
        return HAS_PYPERCLIP

    def read_urls_from_clipboard(self) -> List[str]:
        """
        从剪贴板读取URL列表

        :return: URL列表
        """
        if not HAS_PYPERCLIP:
            logger.error("pyperclip库未安装，无法读取剪贴板内容")
            return []

        try:
            clipboard_content = pyperclip.paste()
            if not clipboard_content:
                logger.warning("剪贴板为空")
                return []

            # 按行分割内容，支持%%%分隔符
            if "%%%" in clipboard_content:
                lines = clipboard_content.strip().split('%%%')
            else:
                lines = clipboard_content.strip().split('\n')

            urls = []
            collected_notes = []
            for line in lines:
                line = line.strip()
                # 简单的URL验证
                if line and (line.startswith('http://') or line.startswith('https://')):
                    urls.append(line)
                elif line:
                    collected_notes.append(line)

            logger.info(f"从剪贴板读取到 {len(urls)} 个有效URL")
            return urls, collected_notes

        except Exception as e:
            logger.error(f"读取剪贴板失败: {e}")
            return []

    def write_to_clipboard(self, content: str) -> bool:
        """
        写入内容到剪贴板

        :param content: 要写入的内容
        :return: 是否成功
        """
        if not HAS_PYPERCLIP:
            logger.error("pyperclip库未安装，无法写入剪贴板")
            return False

        try:
            pyperclip.copy(content)
            logger.info("内容已写入剪贴板")
            return True
        except Exception as e:
            logger.error(f"写入剪贴板失败: {e}")
            return False