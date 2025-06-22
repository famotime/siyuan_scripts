"""
文档管理器
"""
from typing import List, Optional
from .common import logger


class DocumentManager:
    """文档管理类"""

    def __init__(self, api_client):
        self.api = api_client

    def create_doc_with_md(self, notebook_id: str, path: str, markdown: str) -> Optional[str]:
        """
        通过Markdown创建文档

        :param notebook_id: 笔记本ID
        :param path: 文档路径
        :param markdown: Markdown内容
        :return: 创建的文档ID，失败返回None
        """
        logger.info(f"正在创建文档: {path}")
        data = self.api.call_api("/api/filetree/createDocWithMd", {
            "notebook": notebook_id,
            "path": path,
            "markdown": markdown
        })

        if data:
            # logger.info(f"成功创建文档: {path} -> {data}")
            return data

        logger.error(f"创建文档失败: {path}")
        return None

    def get_docs_in_path(self, notebook_id: str, doc_path: str) -> List[str]:
        """
        获取指定笔记本和路径下的所有文档

        :param notebook_id: 笔记本ID
        :param doc_path: 文档路径
        :return: 文档ID列表
        """
        logger.info(f"正在从笔记本 '{notebook_id}' 的路径 '{doc_path}' 获取文档...")

        # 标准化路径格式
        normalized_path = doc_path.strip('/')
        if normalized_path:
            normalized_path = '/' + normalized_path
        else:
            normalized_path = '/'

        # 使用SQL查询获取指定路径下的文档IDs
        sql_query = f"""
        SELECT id
        FROM blocks
        WHERE box = '{notebook_id}' AND type = 'd'
        AND (hpath = '{normalized_path}' OR hpath LIKE '{normalized_path}/%')
        ORDER BY created LIMIT 5000
        """

        data = self.api.call_api("/api/query/sql", {"stmt": sql_query})

        if data and len(data) > 0:
            doc_ids = [row["id"] for row in data]
            logger.info(f"成功找到 {len(doc_ids)} 个文档")
            return doc_ids
        else:
            logger.warning(f"路径 '{doc_path}' 未找到文档")
            return []

    def get_notebook_docs_by_sql(self, notebook_id: str) -> List[str]:
        """
        通过SQL查询获取指定笔记本下的所有文档块

        :param notebook_id: 笔记本ID
        :return: 文档ID列表
        """
        logger.info(f'正在通过SQL查询获取笔记本 {notebook_id} 下的文档...')

        sql = f"SELECT id, content FROM blocks WHERE box = '{notebook_id}' AND type = 'd' ORDER BY created"
        logger.info(f'执行SQL: {sql}')

        data = self.api.call_api('/api/query/sql', {'stmt': sql})

        if data:
            doc_ids = [doc['id'] for doc in data]
            logger.info(f'通过SQL查询找到 {len(data)} 个文档')
            return doc_ids

        logger.warning('SQL查询未找到文档')
        return []

    def get_ids_by_hpath(self, hpath: str, notebook_id: str) -> List[str]:
        """
        根据人类可读路径获取文档IDs

        :param hpath: 人类可读路径
        :param notebook_id: 笔记本ID
        :return: 文档ID列表
        """
        logger.info(f'正在获取路径 "{hpath}" 下的文档IDs (笔记本: {notebook_id})')

        data = self.api.call_api('/api/filetree/getIDsByHPath', {
            'path': hpath,
            'notebook': notebook_id
        })

        if data:
            logger.info(f'找到 {len(data)} 个文档ID: {data}')
            return data

        return []

    def get_doc_tree(self, notebook_id: str, path: str = "/") -> List[dict]:
        """
        通过API获取指定笔记本的文档树结构

        :param notebook_id: 笔记本ID
        :param path: 路径
        :return: 文档树数据
        """
        logger.info(f'正在获取笔记本 {notebook_id} 的文档树结构...')

        data = self.api.call_api('/api/filetree/listDocTree', {
            'notebook': notebook_id,
            'path': path
        })

        if data:
            tree_data = data.get('tree', [])
            logger.info(f'获取到文档树，包含 {len(tree_data)} 个根节点')
            return tree_data

        return []