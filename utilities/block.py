"""
块管理器
"""
from typing import List, Optional
from .common import logger


class BlockManager:
    """块管理类"""

    def __init__(self, api_client):
        self.api = api_client

    def get_block_attributes(self, block_id: str) -> Optional[dict]:
        """
        获取指定块的属性

        :param block_id: 块ID
        :return: 属性字典
        """
        payload = {"id": block_id}
        return self.api.call_api("/api/attr/getBlockAttrs", payload)



    def get_child_blocks(self, block_id: str) -> List[dict]:
        """
        获取指定块的子块

        :param block_id: 块ID
        :return: 子块列表
        """
        logger.debug(f'获取子块: {block_id}')
        result = self.api.call_api('/api/block/getChildBlocks', {'id': block_id})
        return result if result is not None else []

    def get_first_paragraph_id(self, doc_id: str) -> Optional[str]:
        """
        使用SQL查询获取文档的第一个段落块ID

        :param doc_id: 文档块ID
        :return: 第一个段落块的ID，如果找不到则返回None
        """
        # 首先尝试查找段落块
        payload = {"stmt": f"SELECT id FROM blocks WHERE parent_id = '{doc_id}' AND type = 'p' LIMIT 1"}
        data = self.api.call_api("/api/query/sql", payload)
        if data and len(data) > 0:
            return data[0]["id"]

        # 如果没有段落块，尝试查找其他类型的块
        payload = {"stmt": f"SELECT id FROM blocks WHERE parent_id = '{doc_id}' AND type IN ('h', 'list', 'blockquote') LIMIT 1"}
        data = self.api.call_api("/api/query/sql", payload)
        if data and len(data) > 0:
            logger.info(f"文档 {doc_id} 没有段落块，使用其他类型的块: {data[0]['id']}")
            return data[0]["id"]

        # 如果还是没有，尝试查找任何子块
        payload = {"stmt": f"SELECT id FROM blocks WHERE parent_id = '{doc_id}' LIMIT 1"}
        data = self.api.call_api("/api/query/sql", payload)
        if data and len(data) > 0:
            logger.info(f"文档 {doc_id} 没有常规块，使用第一个子块: {data[0]['id']}")
            return data[0]["id"]

        # 最后，如果文档是空的，可以直接在文档块本身添加内容
        logger.info(f"文档 {doc_id} 似乎是空的，将直接在文档块添加内容")
        return doc_id

    def get_block_markdown(self, block_id: str) -> Optional[str]:
        """
        使用SQL查询获取块的markdown内容

        :param block_id: 块ID
        :return: 块的markdown内容，如果找不到则返回None
        """
        payload = {"stmt": f"SELECT markdown FROM blocks WHERE id = '{block_id}'"}
        data = self.api.call_api("/api/query/sql", payload)
        if data and len(data) > 0:
            return data[0]["markdown"]
        return None

    def prepend_metadata_to_block(self, block_id: str, metadata: str) -> bool:
        """
        将元数据添加到指定块的开头

        :param block_id: 目标块ID
        :param metadata: 要添加的元数据字符串
        :return: 是否成功
        """
        logger.info(f"正在向块 {block_id} 添加元数据...")

        payload = {
            "dataType": "markdown",
            "data": metadata,
            "nextID": block_id,
            "parentID": "",
            "previousID": ""
        }

        result = self.api.call_api("/api/block/insertBlock", payload)
        return result is not None