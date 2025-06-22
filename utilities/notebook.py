"""
笔记本管理器
"""
from typing import List, Tuple, Optional
from .common import logger


class NotebookManager:
    """笔记本管理类"""

    def __init__(self, api_client):
        self.api = api_client

    def list_notebooks(self) -> List[Tuple[str, str]]:
        """
        获取所有笔记本列表

        :return: 笔记本(ID, 名称)的列表
        """
        logger.info("正在获取笔记本列表...")
        data = self.api.call_api("/api/notebook/lsNotebooks")

        if data and "notebooks" in data:
            notebooks = data["notebooks"]
            logger.info(f"找到 {len(notebooks)} 个笔记本")
            return notebooks

        logger.warning("未找到笔记本")
        return []

    def create_notebook(self, name: str) -> Optional[str]:
        """
        创建新笔记本

        :param name: 笔记本名称
        :return: 笔记本ID，失败返回None
        """
        logger.info(f"正在创建笔记本: {name}")
        data = self.api.call_api("/api/notebook/createNotebook", {"name": name})

        if data and "notebook" in data:
            notebook_id = data["notebook"]["id"]
            logger.info(f"成功创建笔记本: {name} -> {notebook_id}")
            return notebook_id

        logger.error(f"创建笔记本失败: {name}")
        return None

    def find_or_create_notebook(self, name: str) -> Optional[str]:
        """
        查找或创建笔记本

        :param name: 笔记本名称
        :return: 笔记本ID，失败返回None
        """
        # 先查找是否已存在
        notebook_id = self.get_notebook_id_by_name(name)
        if notebook_id:
            return notebook_id

        # 如果不存在，创建新的
        return self.create_notebook(name)

    def get_notebook_id_by_name(self, name: str) -> Optional[str]:
        """
        根据笔记本名称获取笔记本ID

        :param name: 笔记本名称
        :return: 笔记本ID，如果找不到则返回None
        """
        # logger.info(f"正在获取笔记本 '{name}' 的ID...")
        notebooks = self.list_notebooks()

        for notebook in notebooks:
            notebook_id = notebook["id"]
            notebook_name = notebook["name"]
            notebook_closed = notebook["closed"]

            if notebook_name == name:
                # logger.info(f"找到笔记本 '{name}' 的ID: {notebook_id}")
                return notebook_id

        logger.error(f"未能找到名为 '{name}' 的笔记本")
        return None

    def get_notebook_name(self, notebook_id: str) -> str:
        """
        根据笔记本ID获取笔记本名称

        :param notebook_id: 笔记本ID
        :return: 笔记本名称
        """
        notebooks = self.list_notebooks()
        for notebook in notebooks:
            if notebook["id"] == notebook_id:
                return notebook["name"]
        return f'未知笔记本-{notebook_id}'

    def open_notebook(self, notebook_id: str) -> bool:
        """
        打开指定的笔记本

        :param notebook_id: 笔记本ID
        :return: 是否成功打开
        """
        logger.info(f'正在打开笔记本: {notebook_id}')
        result = self.api.call_api('/api/notebook/openNotebook', {'notebook': notebook_id})

        if result is not None:
            logger.info('笔记本已打开')
            return True

        logger.error('打开笔记本失败')
        return False