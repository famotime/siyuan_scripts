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
import re
from urllib.parse import unquote
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

        self.headers = {
            "Content-Type": "application/json"
        }

        # 如果有token则添加认证头
        if self.api_token:
            self.headers["Authorization"] = f"Token {self.api_token}"

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
            logger.info(f"成功创建文档: {path} -> {data}")
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


class MarkdownImporter:
    """Markdown文件导入器"""

    def __init__(self, api_client: SiyuanAPI):
        self.api = api_client
        self.notebook_manager = NotebookManager(api_client)
        self.document_manager = DocumentManager(api_client)
        self.media_manager = MediaManager(api_client)

    def convert_soft_breaks_to_hard_breaks(self, content: str) -> str:
        """
        将Markdown文档中的软回车转换为硬回车

        软回车：单个换行符（\n），在Markdown中通常不产生换行效果
        硬回车：两个换行符（\n\n）或行末加两个空格+换行符，在Markdown中产生真正的换行

        :param content: 原始Markdown内容
        :return: 转换后的Markdown内容
        """
        logger.info("开始转换软回车为硬回车")

        # 按行分割内容
        lines = content.split('\n')
        processed_lines = []

        i = 0
        in_code_block = False

        while i < len(lines):
            current_line = lines[i]

            # 检查是否进入或退出代码块
            stripped_line = current_line.strip()
            if stripped_line.startswith('```'):
                in_code_block = not in_code_block
                processed_lines.append(current_line)
                i += 1
                continue

            # 如果在代码块内，直接添加行，不做任何转换
            if in_code_block:
                processed_lines.append(current_line)
                i += 1
                continue

            # 跳过空行（已经是硬回车）
            if not current_line.strip():
                processed_lines.append(current_line)
                i += 1
                continue

            # 跳过特殊Markdown语法行，这些不需要转换
            # 标题行（# ## ### 等）
            if stripped_line.startswith('#'):
                processed_lines.append(current_line)
                i += 1
                continue

            # 列表项（- * + 或数字列表）
            if (stripped_line.startswith(('- ', '* ', '+ ')) or
                (stripped_line and stripped_line[0].isdigit() and '. ' in stripped_line[:10])):
                processed_lines.append(current_line)
                i += 1
                continue

            # 引用行（>）
            if stripped_line.startswith('>'):
                processed_lines.append(current_line)
                i += 1
                continue

            # 表格行（包含 |）
            if '|' in stripped_line:
                processed_lines.append(current_line)
                i += 1
                continue

            # 水平分割线（--- 或 ***）
            if stripped_line in ('---', '***', '___') or all(c in '-*_' for c in stripped_line):
                processed_lines.append(current_line)
                i += 1
                continue

            # 普通文本行，检查是否需要转换软回车
            # 如果当前行不是空行，且下一行也不是空行，且下一行不是特殊语法行
            # 则在当前行后添加空行（转换为硬回车）
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                # 如果下一行是空行，说明已经是硬回车，不需要处理
                if not next_line:
                    processed_lines.append(current_line)
                    i += 1
                    continue

                # 检查下一行是否是特殊语法行
                next_is_special = (
                    next_line.startswith('#') or  # 标题
                    next_line.startswith(('- ', '* ', '+ ')) or  # 列表
                    (next_line and next_line[0].isdigit() and '. ' in next_line[:10]) or  # 数字列表
                    next_line.startswith('```') or  # 代码块
                    next_line.startswith('>') or  # 引用
                    '|' in next_line or  # 表格
                    next_line in ('---', '***', '___') or  # 分割线
                    all(c in '-*_' for c in next_line if next_line)  # 分割线
                )

                # 如果下一行是特殊语法行，不添加空行
                if next_is_special:
                    processed_lines.append(current_line)
                else:
                    # 普通文本行之间添加空行（转换为硬回车）
                    processed_lines.append(current_line)
                    processed_lines.append('')  # 添加空行

            else:
                # 最后一行，直接添加
                processed_lines.append(current_line)

            i += 1

        result = '\n'.join(processed_lines)

        # 统计转换的数量
        original_line_count = len(content.split('\n'))
        new_line_count = len(result.split('\n'))
        added_lines = new_line_count - original_line_count

        if added_lines > 0:
            logger.info(f"✅ 软回车转换完成，添加了 {added_lines} 个硬回车")
        else:
            logger.info("📝 未发现需要转换的软回车")

        return result

    def process_markdown_media(self, content: str, md_file_path: Path) -> str:
        """
        处理Markdown文件中的媒体文件引用，上传到思源笔记并更新链接

        :param content: Markdown内容
        :param md_file_path: MD文件的路径（用于解析相对路径）
        :return: 处理后的Markdown内容
        """
        processed_content = content
        md_dir = md_file_path.parent
        upload_count = 0

        logger.info(f"开始处理文件中的媒体链接: {md_file_path.name}")

        # 使用贪婪匹配，正确处理路径中的括号
        patterns = [
            # 图片格式：![alt](path) - 贪婪匹配到最后的)
            (r'!\[([^\]]*)\]\((.+\.(?:png|jpg|jpeg|gif|svg|webp|bmp|ico))\)', 'image'),
            # 媒体文件链接格式
            (r'(?<!)!\[([^\]]*)\]\((.+\.(?:mp3|mp4|mov|avi|wav|m4a|aac|ogg|flac|mkv|webm|wmv|flv))\)', 'media'),
        ]

        for pattern, media_type_hint in patterns:
            matches = list(re.finditer(pattern, processed_content, re.IGNORECASE | re.MULTILINE))
            logger.info(f"找到 {len(matches)} 个 {media_type_hint} 链接匹配")

            # 从后往前替换，避免位置偏移
            for match in reversed(matches):
                try:
                    full_match = match.group(0)
                    alt_text = match.group(1) if len(match.groups()) >= 1 and match.group(1) else ""
                    media_path = match.group(2) if len(match.groups()) >= 2 and match.group(2) else ""

                    if not media_path:
                        logger.debug(f"跳过无效匹配: {full_match}")
                        continue

                    logger.debug(f"处理链接: {full_match}")
                    logger.debug(f"Alt文本: '{alt_text}'")
                    logger.debug(f"媒体路径: {media_path}")
                except IndexError as e:
                    logger.warning(f"正则表达式匹配组错误: {e}")
                    continue

                # 跳过明显是表格内容的匹配（通过检查前后文）
                match_start = max(0, match.start() - 50)
                match_end = min(len(processed_content), match.end() + 50)

                # 更安全的表格检查方法
                try:
                    before_context = processed_content[match_start:match.start()]
                    after_context = processed_content[match.end():match_end]

                    # 如果周围有表格标记，跳过
                    if '|' in before_context[-10:] or '|' in after_context[:10]:
                        logger.debug(f"跳过表格中的引用: {media_path}")
                        continue
                except Exception as e:
                    logger.debug(f"表格检查失败，继续处理: {e}")
                    # 如果检查失败，继续处理

                # 解码URL编码的路径
                try:
                    media_path = unquote(media_path)
                except Exception as e:
                    logger.warning(f"URL解码失败: {media_path}, 错误: {e}")

                # 跳过网络链接
                if media_path.startswith(('http://', 'https://', 'ftp://')):
                    logger.debug(f"跳过网络链接: {media_path}")
                    continue

                # 处理相对路径
                if not os.path.isabs(media_path):
                    full_media_path = md_dir / media_path
                else:
                    full_media_path = Path(media_path)

                # 标准化路径
                try:
                    full_media_path = full_media_path.resolve()
                    logger.info(f"解析后的完整路径: {full_media_path}")
                except Exception as e:
                    logger.warning(f"路径解析失败: {media_path}, 错误: {e}")
                    continue

                # 检查文件是否存在且是媒体文件
                if full_media_path.exists() and self.media_manager.is_media_file(str(full_media_path)):
                    logger.info(f"发现媒体文件: {full_media_path.name}")

                    # 上传媒体文件
                    uploaded_path = self.media_manager.upload_asset(str(full_media_path))

                    if uploaded_path:
                        # 替换链接
                        media_type = self.media_manager.get_media_type(str(full_media_path))

                        if media_type == 'image':
                            # 保持原有的格式，只替换路径部分
                            new_link = f'![{alt_text}]({uploaded_path})'
                        else:
                            # 音频和视频文件
                            new_link = f'[{alt_text or full_media_path.name}]({uploaded_path})'

                        # 执行替换 - 使用简单字符串替换而不是正则表达式
                        try:
                            processed_content = processed_content.replace(full_match, new_link)
                            upload_count += 1
                            logger.info(f"✅ 已更新媒体链接: {media_path} -> {uploaded_path}")
                        except Exception as replace_error:
                            logger.error(f"字符串替换失败: {replace_error}")
                            logger.debug(f"原始匹配: {repr(full_match)}")
                            logger.debug(f"新链接: {repr(new_link)}")
                            continue
                    else:
                        logger.warning(f"❌ 媒体文件上传失败: {full_media_path}")
                else:
                    if not full_media_path.exists():
                        logger.warning(f"⚠️ 媒体文件不存在: {full_media_path}")
                    elif not self.media_manager.is_media_file(str(full_media_path)):
                        logger.debug(f"跳过非媒体文件: {full_media_path}")

        if upload_count > 0:
            logger.info(f"🎉 成功上传并更新了 {upload_count} 个媒体文件的链接")
        else:
            logger.info("未找到需要上传的媒体文件")

        return processed_content

    def import_md_files(self, md_folder: str, notebook_name: str, parent_folder: str = None, upload_media: bool = True, convert_soft_breaks: bool = True) -> dict:
        """
        批量导入MD文件到思源笔记

        :param md_folder: MD文件夹路径
        :param notebook_name: 目标笔记本名称
        :param parent_folder: 父文件夹名称（可选）
        :param upload_media: 是否上传媒体文件
        :param convert_soft_breaks: 是否将软回车转换为硬回车
        :return: 导入结果统计
        """
        md_path = Path(md_folder)
        if not md_path.exists():
            logger.error(f"MD文件夹不存在: {md_folder}")
            return {"success": 0, "error": 1, "message": "文件夹不存在"}

        # 获取或创建笔记本
        notebook_id = self.notebook_manager.find_or_create_notebook(notebook_name)
        if not notebook_id:
            logger.error(f"无法获取或创建笔记本: {notebook_name}")
            return {"success": 0, "error": 1, "message": "笔记本创建失败"}

        logger.info(f"使用笔记本: {notebook_name} ({notebook_id})")

        # 如果指定了父文件夹，先检查是否已存在，若不存在则创建父文档
        if parent_folder:
            self._create_parent_folder(notebook_id, parent_folder)

        # 获取所有MD文件
        md_files = list(md_path.glob("*.md"))
        if not md_files:
            logger.warning(f"在 {md_folder} 中未找到任何MD文件")
            return {"success": 0, "error": 0, "message": "未找到MD文件"}

        logger.info(f"找到 {len(md_files)} 个MD文件")
        if upload_media:
            logger.info("启用媒体文件上传功能")

        success_count = 0
        error_count = 0
        total_media_uploaded = 0

        for md_file in md_files:
            try:
                # 读取MD文件内容
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 转换软回车为硬回车（如果启用）
                if convert_soft_breaks:
                    content = self.convert_soft_breaks_to_hard_breaks(content)

                # 处理媒体文件（如果启用）
                if upload_media:
                    original_content = content
                    content = self.process_markdown_media(content, md_file)
                    # 简单统计媒体文件数量变化
                    if content != original_content:
                        total_media_uploaded += content.count('assets/') - original_content.count('assets/')

                # 使用文件名作为文档标题
                title = md_file.stem

                # 构建文档路径
                if parent_folder:
                    # 处理多级路径，确保路径格式正确
                    clean_parent_folder = parent_folder.strip().strip('/')
                    doc_path = f"/{clean_parent_folder}/{title}"
                else:
                    doc_path = f"/{title}"

                # 创建文档
                doc_id = self.document_manager.create_doc_with_md(
                    notebook_id=notebook_id,
                    path=doc_path,
                    markdown=content
                )

                if doc_id:
                    logger.info(f"成功导入: {title}")
                    success_count += 1
                else:
                    logger.error(f"导入失败: {title}")
                    error_count += 1

            except Exception as e:
                logger.error(f"导入失败 {md_file.name}: {e}")
                error_count += 1

        result = {
            "success": success_count,
            "error": error_count,
            "total": len(md_files),
            "media_uploaded": total_media_uploaded if upload_media else 0,
            "message": f"导入完成！成功: {success_count}, 失败: {error_count}"
        }

        if upload_media and total_media_uploaded > 0:
            result["message"] += f", 媒体文件: {total_media_uploaded}"

        logger.info(result["message"])
        return result

    def _create_parent_folder(self, notebook_id: str, parent_folder: str) -> Optional[str]:
        """检查父文件夹是否存在，如果不存在则创建（支持多级路径）"""
        # 标准化路径，确保以/开头，去掉末尾的/
        parent_path = parent_folder.strip()
        if not parent_path.startswith('/'):
            parent_path = f"/{parent_path}"
        parent_path = parent_path.rstrip('/')

        # 先检查完整路径的父文档是否已存在
        existing_ids = self.document_manager.get_ids_by_hpath(parent_path, notebook_id)

        if existing_ids:
            logger.info(f"父文档已存在: {parent_path} -> {existing_ids[0]}")
            return existing_ids[0]

        # 如果路径包含多级，需要递归创建父级目录
        path_parts = [part for part in parent_path.split('/') if part]

        if len(path_parts) > 1:
            # 递归创建上级目录
            parent_path_parts = path_parts[:-1]
            upper_parent_path = '/' + '/'.join(parent_path_parts)

            logger.info(f"检查上级路径: {upper_parent_path}")
            self._create_parent_folder(notebook_id, upper_parent_path)

        # 创建当前级别的文档
        try:
            # 获取当前级别的文件夹名
            folder_name = path_parts[-1] if path_parts else parent_folder

            doc_id = self.document_manager.create_doc_with_md(
                notebook_id=notebook_id,
                path=parent_path,
                markdown=f"# {folder_name}\n\n这是导入文档的集合文件夹。"
            )

            if doc_id:
                logger.info(f"创建父文档: {parent_path} -> {doc_id}")
                return doc_id
            else:
                logger.error(f"创建父文档失败: {parent_path}")
                return None

        except Exception as e:
            logger.warning(f"创建父文档时出错: {e}")
            # 再次尝试检查是否已存在（可能是并发创建或API延迟）
            existing_ids = self.document_manager.get_ids_by_hpath(parent_path, notebook_id)
            if existing_ids:
                logger.info(f"父文档已存在（重新检查）: {parent_path} -> {existing_ids[0]}")
                return existing_ids[0]
            return None


class MediaManager:
    """媒体文件管理类"""

    def __init__(self, api_client: SiyuanAPI):
        self.api = api_client
        # 支持的媒体文件扩展名
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.ico'}
        self.audio_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}
        self.video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.wmv', '.flv'}
        self.all_media_extensions = self.image_extensions | self.audio_extensions | self.video_extensions

    def upload_asset(self, file_path: str, assets_dir: str = "/assets/") -> Optional[str]:
        """
        上传资源文件到思源笔记

        :param file_path: 本地文件路径
        :param assets_dir: 资源文件存储目录
        :return: 上传后的资源路径，失败返回None
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"文件不存在: {file_path}")
                return None

            # 准备multipart表单数据
            with open(file_path, 'rb') as f:
                files = {
                    'file[]': (file_path.name, f, 'application/octet-stream')
                }

                data = {
                    'assetsDirPath': assets_dir
                }

                # 准备请求头（不包含Content-Type，让requests自动设置）
                headers = {}
                if self.api.api_token:
                    headers['Authorization'] = f'Token {self.api.api_token}'

                # 发送上传请求
                response = requests.post(
                    f"{self.api.api_url}/api/asset/upload",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60
                )

            response.raise_for_status()
            result = response.json()

            if result.get('code') != 0:
                logger.error(f"上传文件失败: {result.get('msg', '未知错误')}")
                return None

            # 获取上传后的文件路径
            succ_map = result.get('data', {}).get('succMap', {})
            if file_path.name in succ_map:
                uploaded_path = succ_map[file_path.name]
                logger.info(f"成功上传文件: {file_path.name} -> {uploaded_path}")
                return uploaded_path
            else:
                logger.error(f"上传失败，文件不在成功列表中: {file_path.name}")
                logger.debug(f"API返回结果: {result}")
                return None

        except Exception as e:
            logger.error(f"上传文件时出错: {e}")
            return None

    def is_media_file(self, file_path: str) -> bool:
        """判断是否为媒体文件"""
        return Path(file_path).suffix.lower() in self.all_media_extensions

    def get_media_type(self, file_path: str) -> str:
        """获取媒体文件类型"""
        ext = Path(file_path).suffix.lower()
        if ext in self.image_extensions:
            return 'image'
        elif ext in self.audio_extensions:
            return 'audio'
        elif ext in self.video_extensions:
            return 'video'
        else:
            return 'unknown'


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