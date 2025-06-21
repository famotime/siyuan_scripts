"""
对思源笔记指定的笔记本和目录下的文档，添加元数据：
1. 逐个读取指定目录下的文档，获取文档的属性值；
2. 将custom-title、custom-abstract、custom-url、custom-tags、custom-created、custom-accessed、custom-modified属性值插入到本文档的第一个块中，作为元数据；
3. 插入内容示例：
为知笔记迁移文档自定义属性：
title: custom-title
url: [custom-url](custom-url)
tags: custom-tags
created: custom-created
accessed: custom-accessed
modified: custom-modified
"""
import requests
import logging
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# --- 用户配置 ---
# 思源笔记 API 地址，从 .env 文件中读取，默认为本地地址
SIYUAN_API_URL = os.getenv("SIYUAN_API_URL", "http://127.0.0.1:6806")
# 思源笔记 API Token, 从 .env 文件中自动读取
SIYUAN_API_TOKEN = os.getenv("SIYUAN_API_TOKEN")
# 需要处理的笔记本名称
NOTEBOOK_NAME = "剪藏笔记本"
# 需要处理的文档所在路径，比如 "/Documents"
# DOC_PATH = "/测试思源API"  # 支持带斜杠的路径格式
DOC_PATH = "/兴趣爱好/AIGC"  # 支持带斜杠的路径格式
# --- 配置结束 ---

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API 请求头
HEADERS = {
    "Authorization": f"Token {SIYUAN_API_TOKEN}",
    "Content-Type": "application/json"
}


def call_siyuan_api(api_path, payload):
    """
    调用思源笔记 API 的通用函数

    :param api_path: API 路径，例如 "/api/notebook/lsNotebooks"
    :param payload: 请求体数据 (dict)
    :return: 成功则返回 API 响应的 data 部分，否则返回 None
    """
    try:
        response = requests.post(f"{SIYUAN_API_URL}{api_path}", headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        json_response = response.json()
        if json_response.get("code") != 0:
            logging.error(f"调用 API {api_path} 出错: {json_response.get('msg')}")
            return None
        return json_response.get("data")
    except requests.exceptions.RequestException as e:
        logging.error(f"请求 API {api_path} 失败: {e}")
        return None


def get_notebook_id_by_name(name):
    """
    根据笔记本名称获取笔记本 ID

    :param name: 笔记本名称
    :return: 笔记本 ID，如果找不到则返回 None
    """
    logging.info(f"正在获取笔记本 '{name}' 的 ID...")
    data = call_siyuan_api("/api/notebook/lsNotebooks", {})
    if data and "notebooks" in data:
        for notebook in data["notebooks"]:
            if notebook["name"] == name:
                logging.info(f"找到笔记本 '{name}' 的 ID: {notebook['id']}")
                return notebook["id"]
    logging.error(f"未能找到名为 '{name}' 的笔记本。")
    return None


def get_docs_in_path(notebook_id, doc_path):
    """
    获取指定笔记本和路径下的所有文档

    :param notebook_id: 笔记本 ID
    :param doc_path: 文档路径
    :return: 文档ID列表
    """
    logging.info(f"正在从笔记本 '{notebook_id}' 的路径 '{doc_path}' 获取文档...")

    # 标准化路径格式，确保以斜杠开头，但不以斜杠结尾
    normalized_path = doc_path.strip('/')
    if normalized_path:
        normalized_path = '/' + normalized_path
    else:
        normalized_path = '/'

    # 使用SQL查询获取指定路径下的文档IDs
    # 严格匹配：路径本身 OR 以"路径/"开头的子路径
    sql_query = f"""
    SELECT id
    FROM blocks
    WHERE box = '{notebook_id}' AND type = 'd'
    AND (hpath = '{normalized_path}' OR hpath LIKE '{normalized_path}/%')
    ORDER BY created
    """

    # logging.info(f"使用SQL查询获取文档IDs: {sql_query}")
    data = call_siyuan_api("/api/query/sql", {"stmt": sql_query})

    if data and len(data) > 0:
        # 提取文档ID列表
        doc_ids = [row["id"] for row in data]
        logging.info(f"成功找到 {len(doc_ids)} 个文档。")
        return doc_ids
    else:
        logging.warning(f"路径 '{doc_path}' 未找到文档")
        return []


def get_block_attributes(block_id):
    """
    获取指定块的属性

    :param block_id: 块 ID
    :return: 属性字典
    """
    payload = {"id": block_id}
    return call_siyuan_api("/api/attr/getBlockAttrs", payload)


def get_first_paragraph_id(doc_id):
    """
    使用 SQL 查询获取文档的第一个段落块 ID

    :param doc_id: 文档块 ID
    :return: 第一个段落块的 ID，如果找不到则返回 None
    """
    # 首先尝试查找段落块
    payload = {"stmt": f"SELECT id FROM blocks WHERE parent_id = '{doc_id}' AND type = 'p' LIMIT 1"}
    data = call_siyuan_api("/api/query/sql", payload)
    if data and len(data) > 0:
        return data[0]["id"]

    # 如果没有段落块，尝试查找其他类型的块（如标题块）
    payload = {"stmt": f"SELECT id FROM blocks WHERE parent_id = '{doc_id}' AND type IN ('h', 'list', 'blockquote') LIMIT 1"}
    data = call_siyuan_api("/api/query/sql", payload)
    if data and len(data) > 0:
        logging.info(f"文档 {doc_id} 没有段落块，使用其他类型的块: {data[0]['id']}")
        return data[0]["id"]

    # 如果还是没有，尝试查找任何子块
    payload = {"stmt": f"SELECT id FROM blocks WHERE parent_id = '{doc_id}' LIMIT 1"}
    data = call_siyuan_api("/api/query/sql", payload)
    if data and len(data) > 0:
        logging.info(f"文档 {doc_id} 没有常规块，使用第一个子块: {data[0]['id']}")
        return data[0]["id"]

    # 最后，如果文档是空的，可以直接在文档块本身添加内容
    logging.info(f"文档 {doc_id} 似乎是空的，将直接在文档块添加内容")
    return doc_id


def get_block_markdown(block_id):
    """
    使用 SQL 查询获取块的 markdown 内容

    :param block_id: 块 ID
    :return: 块的 markdown 内容，如果找不到则返回 None
    """
    payload = {"stmt": f"SELECT markdown FROM blocks WHERE id = '{block_id}'"}
    data = call_siyuan_api("/api/query/sql", payload)
    if data and len(data) > 0:
        return data[0]["markdown"]
    return None


def prepend_metadata_to_block(block_id, metadata):
    """
    将元数据添加到指定块的开头

    :param block_id: 目标块 ID
    :param metadata: 要添加的元数据字符串
    :return: API 响应
    """
    logging.info(f"正在向块 {block_id} 添加元数据...")

    # 直接使用 insertBlock API，以段落形式插入，避免格式化问题
    payload = {
        "dataType": "markdown",
        "data": metadata,
        "nextID": block_id,
        "parentID": "",
        "previousID": ""
    }
    result = call_siyuan_api("/api/block/insertBlock", payload)

    if result is not None:
        return result

def process_documents():
    """
    处理文档，添加元数据的主函数
    """
    notebook_id = get_notebook_id_by_name(NOTEBOOK_NAME)
    if not notebook_id:
        return

    doc_ids = get_docs_in_path(notebook_id, DOC_PATH)
    if not doc_ids:
        return

    for doc_id in doc_ids:
        attributes = get_block_attributes(doc_id)
        if not attributes:
            logging.warning(f"未能获取文档 {doc_id} 的属性，跳过。")
            continue

        doc_name = attributes.get("title", "未知名称")
        logging.info(f"\n--- 开始处理文档: {doc_name} ({doc_id}) ---")
        custom_title = attributes.get("custom-title", "")
        custom_abstract = attributes.get("custom-abstract", "")
        custom_url = attributes.get("custom-url", "")
        custom_tags = attributes.get("custom-tags", "")
        custom_created = attributes.get("custom-created", "")
        custom_accessed = attributes.get("custom-accessed", "")
        custom_modified = attributes.get("custom-modified", "")

        if not any([custom_title, custom_abstract, custom_url, custom_tags, custom_created, custom_accessed, custom_modified]):
            logging.info(f"文档 {doc_id} 没有需要添加的元数据属性，跳过。")
            continue

        metadata_parts = ["为知笔记迁移文档自定义属性："]
        if custom_title:
            metadata_parts.append(f"title: {custom_title}")
        if custom_abstract:
            metadata_parts.append(f"abstract: {custom_abstract}")
        if custom_url:
            metadata_parts.append(f"url: [{custom_url}]({custom_url})")
        if custom_tags:
            metadata_parts.append(f"tags: {custom_tags}")
        if custom_created:
            metadata_parts.append(f"created: {custom_created}")
        if custom_accessed:
            metadata_parts.append(f"accessed: {custom_accessed}")
        if custom_modified:
            metadata_parts.append(f"modified: {custom_modified}")

        metadata_string = "\n".join(["> " + part for part in metadata_parts]) + "\n\n"

        first_paragraph_id = get_first_paragraph_id(doc_id)
        if not first_paragraph_id:
            continue

        # 检查是否已存在元数据
        current_content = call_siyuan_api("/api/block/getBlockKramdown", {"id": doc_id})["kramdown"]
        if current_content and "为知笔记迁移文档" in current_content:
             logging.info(f"文档 {doc_id} 似乎已包含元数据，跳过。")
             continue

        result = prepend_metadata_to_block(first_paragraph_id, metadata_string)
        if result is not None:
            logging.info(f"成功为文档 {doc_id} 添加元数据。")
        else:
            logging.error(f"为文档 {doc_id} 添加元数据失败。")


if __name__ == "__main__":
    process_documents()
    logging.info("所有文档处理完毕。")