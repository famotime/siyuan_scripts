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
import logging
from pathlib import Path
from functions import create_siyuan_client, create_managers

# --- 用户配置 ---
# 需要处理的笔记本名称
# NOTEBOOK_NAME = "QuincyZou"
NOTEBOOK_NAME = "剪藏笔记本"
# 需要处理的文档所在路径，比如 "/Documents"
# DOC_PATH = "/我的草稿"
DOC_PATH = "/知识点滴"
# --- 配置结束 ---

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def process_documents():
    """
    处理文档，添加元数据的主函数
    """
    # 初始化统计变量
    stats = {
        'total_docs': 0,          # 总文档数
        'success': 0,             # 成功添加元数据的文档数
        'skipped_no_attrs': 0,    # 跳过（无属性获取失败）
        'skipped_no_metadata': 0, # 跳过（无需要添加的元数据）
        'skipped_exists': 0,      # 跳过（已存在元数据）
        'skipped_no_paragraph': 0,# 跳过（无法获取第一个段落）
        'failed': 0               # 添加元数据失败
    }

    try:
        # 创建API客户端和管理器
        api_client = create_siyuan_client()
        notebook_manager, document_manager, block_manager = create_managers(api_client)

        # 获取笔记本ID
        notebook_id = notebook_manager.get_notebook_id_by_name(NOTEBOOK_NAME)
        if not notebook_id:
            logging.error(f"未找到笔记本: {NOTEBOOK_NAME}")
            return stats

        # 获取指定路径下的文档
        doc_ids = document_manager.get_docs_in_path(notebook_id, DOC_PATH)
        if not doc_ids:
            logging.warning(f"在路径 {DOC_PATH} 下未找到文档")
            return stats

        stats['total_docs'] = len(doc_ids)
        logging.info(f"找到 {stats['total_docs']} 个文档需要处理")

        # 处理每个文档
        for doc_id in doc_ids:
            attributes = block_manager.get_block_attributes(doc_id)
            if not attributes:
                logging.warning(f"未能获取文档 {doc_id} 的属性，跳过。")
                stats['skipped_no_attrs'] += 1
                continue

            doc_name = attributes.get("title", "未知名称")
            logging.info(f"\n--- 开始处理文档: {doc_name} ({doc_id}) ---")

            # 获取自定义属性
            custom_title = attributes.get("custom-title", "")
            custom_abstract = attributes.get("custom-abstract", "")
            custom_url = attributes.get("custom-url", "")
            custom_tags = attributes.get("custom-tags", "")
            custom_created = attributes.get("custom-created", "")
            custom_accessed = attributes.get("custom-accessed", "")
            custom_modified = attributes.get("custom-modified", "")

            # 检查是否有需要添加的元数据
            if not any([custom_title, custom_abstract, custom_url, custom_tags, custom_created, custom_accessed, custom_modified]):
                logging.info(f"文档 {doc_id} 没有需要添加的元数据属性，跳过。")
                stats['skipped_no_metadata'] += 1
                continue

            # 构建元数据字符串
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

            # 获取第一个段落块ID
            first_paragraph_id = block_manager.get_first_paragraph_id(doc_id)
            if not first_paragraph_id:
                logging.warning(f"文档 {doc_id} 无法获取第一个段落ID，跳过。")
                stats['skipped_no_paragraph'] += 1
                continue

            # 检查是否已存在元数据
            current_content = api_client.call_api("/api/block/getBlockKramdown", {"id": doc_id})
            if current_content and current_content.get("kramdown") and "为知笔记迁移文档" in current_content["kramdown"]:
                logging.info(f"文档 {doc_id} 似乎已包含元数据，跳过。")
                stats['skipped_exists'] += 1
                continue

            # 添加元数据
            if block_manager.prepend_metadata_to_block(first_paragraph_id, metadata_string):
                logging.info(f"成功为文档 {doc_id} 添加元数据。")
                stats['success'] += 1
            else:
                logging.error(f"为文档 {doc_id} 添加元数据失败。")
                stats['failed'] += 1

    except Exception as e:
        logging.error(f"处理文档时发生错误: {e}")
        raise

    # 打印统计结果
    print_statistics(stats)
    return stats


def print_statistics(stats):
    """
    打印处理结果统计信息

    :param stats: 统计数据字典
    """
    logging.info("\n" + "="*50)
    logging.info("处理结果统计")
    logging.info("="*50)
    logging.info(f"总文档数量: {stats['total_docs']}")
    logging.info(f"成功处理: {stats['success']}")
    logging.info(f"跳过（无法获取属性）: {stats['skipped_no_attrs']}")
    logging.info(f"跳过（无需添加的元数据）: {stats['skipped_no_metadata']}")
    logging.info(f"跳过（已存在元数据）: {stats['skipped_exists']}")
    logging.info(f"跳过（无法获取段落）: {stats['skipped_no_paragraph']}")
    logging.info(f"处理失败: {stats['failed']}")

    # 计算跳过总数
    total_skipped = (stats['skipped_no_attrs'] + stats['skipped_no_metadata'] +
                    stats['skipped_exists'] + stats['skipped_no_paragraph'])
    logging.info(f"跳过总数: {total_skipped}")

    # 计算成功率
    if stats['total_docs'] > 0:
        success_rate = (stats['success'] / stats['total_docs']) * 100
        logging.info(f"成功率: {success_rate:.1f}%")

    logging.info("="*50)


if __name__ == "__main__":
    stats = process_documents()
    logging.info("所有文档处理完毕。")