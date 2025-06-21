"""
思源笔记API操作的通用函数库
包含API调用、文档操作、数据处理等常用功能
"""
import requests
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 默认配置
DEFAULT_API_URL = os.getenv("SIYUAN_API_URL", "http://127.0.0.1:6806")
DEFAULT_API_TOKEN = os.getenv("SIYUAN_API_TOKEN")

# 配置日志
def setup_logging(level=logging.INFO):
    """配置日志系统"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()


class SiyuanAPI:
    """思源笔记API操作类"""

    def __init__(self, api_url: str = None, api_token: str = None):
        """
        初始化API客户端

        :param api_url: API地址
        :param api_token: API Token
        """
        self.api_url = api_url or DEFAULT_API_URL
        self.api_token = api_token or DEFAULT_API_TOKEN

        if not self.api_token:
            raise ValueError("API Token未设置，请检查环境变量SIYUAN_API_TOKEN或传入api_token参数")

        self.headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }

    def call_api(self, api_path: str, payload: dict = None) -> Optional[dict]:
        """
        调用思源笔记API的通用函数

        :param api_path: API路径，例如 "/api/notebook/lsNotebooks"
        :param payload: 请求体数据 (dict)
        :return: 成功则返回API响应的data部分，否则返回None
        """
        try:
            if payload is None:
                payload = {}

            response = requests.post(
                f"{self.api_url}{api_path}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            json_response = response.json()

            if json_response.get("code") != 0:
                logger.error(f"调用API {api_path} 出错: {json_response.get('msg')}")
                return None

            return json_response.get("data")

        except requests.exceptions.RequestException as e:
            logger.error(f"请求API {api_path} 失败: {e}")
            return None

    def make_api_request(self, endpoint: str, data: dict = None) -> dict:
        """
        统一的API请求处理函数（兼容旧版本函数名）

        :param endpoint: API端点
        :param data: 请求数据
        :return: API响应数据
        """
        try:
            if data is None:
                data = {}

            resp = requests.post(
                f'{self.api_url}{endpoint}',
                headers=self.headers,
                json=data
            )
            resp.raise_for_status()
            result = resp.json()

            if result['code'] != 0:
                raise Exception(f'API请求失败 [{endpoint}]: {result}')

            return result['data']

        except requests.exceptions.RequestException as e:
            logger.error(f'网络请求错误 [{endpoint}]: {e}')
            raise
        except Exception as e:
            logger.error(f'API调用错误 [{endpoint}]: {e}')
            raise


class NotebookManager:
    """笔记本管理类"""

    def __init__(self, api_client: SiyuanAPI):
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

    def get_notebook_id_by_name(self, name: str) -> Optional[str]:
        """
        根据笔记本名称获取笔记本ID

        :param name: 笔记本名称
        :return: 笔记本ID，如果找不到则返回None
        """
        logger.info(f"正在获取笔记本 '{name}' 的ID...")
        notebooks = self.list_notebooks()

        for notebook in notebooks:
            notebook_id = notebook["id"]
            notebook_name = notebook["name"]
            notebook_closed = notebook["closed"]

            if notebook_name == name:
                logger.info(f"找到笔记本 '{name}' 的ID: {notebook_id}")
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


class DocumentManager:
    """文档管理类"""

    def __init__(self, api_client: SiyuanAPI):
        self.api = api_client

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
        ORDER BY created
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


class BlockManager:
    """块管理类"""

    def __init__(self, api_client: SiyuanAPI):
        self.api = api_client

    def get_block_attributes(self, block_id: str) -> Optional[dict]:
        """
        获取指定块的属性

        :param block_id: 块ID
        :return: 属性字典
        """
        payload = {"id": block_id}
        return self.api.call_api("/api/attr/getBlockAttrs", payload)

    def get_block_attrs(self, block_id: str) -> dict:
        """
        获取指定块的属性（兼容旧版本函数名）

        :param block_id: 块ID
        :return: 属性字典
        """
        logger.debug(f'获取块属性: {block_id}')
        return self.api.make_api_request('/api/attr/getBlockAttrs', {'id': block_id})

    def get_child_blocks(self, block_id: str) -> List[dict]:
        """
        获取指定块的子块

        :param block_id: 块ID
        :return: 子块列表
        """
        logger.debug(f'获取子块: {block_id}')
        return self.api.make_api_request('/api/block/getChildBlocks', {'id': block_id})

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


class FileManager:
    """文件管理类"""

    @staticmethod
    def load_json_file(file_path: str) -> Dict[str, Any]:
        """
        加载JSON文件

        :param file_path: 文件路径
        :return: JSON数据
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"错误：找不到文件 {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"错误：解析JSON文件 {file_path} 时出错: {e}")
            return {}

    @staticmethod
    def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
        """
        保存数据到JSON文件

        :param data: 要保存的数据
        :param file_path: 文件路径
        :return: 是否成功保存
        """
        try:
            output_file = Path(file_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"数据已保存到: {file_path}")
            return True

        except Exception as e:
            logger.error(f"错误：保存文件时出错: {e}")
            return False


class TreeProcessor:
    """树结构处理类"""

    @staticmethod
    def is_leaf_node(node: Any) -> bool:
        """
        判断是否为叶子节点（即docguid字典）

        :param node: 节点数据
        :return: 是否为叶子节点
        """
        return isinstance(node, dict) and all(
            not isinstance(v, dict) for v in node.values()
        )

    @staticmethod
    def count_documents(tree: Dict[str, Any]) -> int:
        """
        递归计算文档数量

        :param tree: 文档树
        :return: 文档数量
        """
        count = 0
        for key, value in tree.items():
            if isinstance(value, str):
                # 这是一个docGuid-title对
                count += 1
            elif isinstance(value, dict):
                if '__self__' in value:
                    # 这是一个有自身GUID的目录，先计算自身
                    count += TreeProcessor.count_documents(value['__self__'])
                    # 再递归计算子目录中的文档数量
                    remaining_items = {k: v for k, v in value.items() if k != '__self__'}
                    count += TreeProcessor.count_documents(remaining_items)
                else:
                    # 递归计算子目录中的文档数量
                    count += TreeProcessor.count_documents(value)
        return count


# 便捷函数，用于快速创建API客户端和管理器
def create_siyuan_client(api_url: str = None, api_token: str = None) -> SiyuanAPI:
    """创建思源API客户端"""
    return SiyuanAPI(api_url, api_token)

def create_managers(api_client: SiyuanAPI = None) -> Tuple[NotebookManager, DocumentManager, BlockManager]:
    """创建管理器实例"""
    if api_client is None:
        api_client = create_siyuan_client()

    notebook_manager = NotebookManager(api_client)
    document_manager = DocumentManager(api_client)
    block_manager = BlockManager(api_client)

    return notebook_manager, document_manager, block_manager