"""
基于思源笔记API，将文件夹下的md文件导入到思源笔记

使用说明：
1. 确保思源笔记正在运行
2. 在思源笔记的 设置 > 关于 中查看并复制API token（如果需要）
3. 如需要token，请设置环境变量 SIYUAN_API_TOKEN 或在 .env 文件中配置
4. 运行脚本：python create_notes_from_md.py
"""

import os
import logging
from pathlib import Path

# 导入通用函数库
from utilities import (
    setup_logging,
    create_siyuan_client,
    create_markdown_importer,
    NotebookManager
)

# 配置日志
logger = setup_logging()

# 默认配置
DEFAULT_MD_FOLDER = Path("H:/为知笔记导出MD备份/My Emails")
DEFAULT_NOTEBOOK_NAME = "剪藏笔记本"
DEFAULT_PARENT_FOLDER = "/Web收集箱/urls2markdown"


def test_connection(api_client):
    """测试与思源笔记的连接"""
    try:
        notebook_manager = NotebookManager(api_client)
        notebooks = notebook_manager.list_notebooks()
        logger.info(f"成功连接到思源笔记（{api_client.api_url}），发现 {len(notebooks)} 个笔记本")
        return True
    except Exception as e:
        logger.error(f"连接思源笔记失败，请确保思源笔记正在运行: {e}")
        return False


def main(md_folder=DEFAULT_MD_FOLDER, notebook_name=DEFAULT_NOTEBOOK_NAME, parent_folder=DEFAULT_PARENT_FOLDER, upload_media=True, convert_soft_breaks=True):
    """主函数"""
    try:
        # 获取配置
        api_token = os.getenv("SIYUAN_API_TOKEN", "")
        api_url = os.getenv("SIYUAN_API_URL")

        logger.info("=== 思源笔记 MD 文件导入工具 ===")
        logger.info(f"MD文件夹: {md_folder}")
        logger.info(f"目标笔记本: {notebook_name}")
        logger.info(f"父文件夹: {parent_folder}")
        logger.info(f"上传媒体文件: {'是' if upload_media else '否'}")
        logger.info(f"转换软回车: {'是' if convert_soft_breaks else '否'}")

        # 创建API客户端
        api_client = create_siyuan_client(api_url=api_url, api_token=api_token)

        # 测试连接
        if not test_connection(api_client):
            return

        # 检查MD文件夹是否存在
        md_path = Path(md_folder)
        if not md_path.exists():
            logger.error(f"MD文件夹不存在: {md_folder}")
            logger.info("请确保文件夹路径正确，或者修改配置")
            return

        # 创建Markdown导入器
        importer = create_markdown_importer(api_client)

        # 执行导入
        logger.info("开始导入MD文件...")
        result = importer.import_md_files(
            md_folder=md_folder,
            notebook_name=notebook_name,
            parent_folder=parent_folder,
            upload_media=upload_media,
            convert_soft_breaks=convert_soft_breaks
        )

        # 显示结果
        logger.info("=== 导入结果 ===")
        logger.info(f"总文件数: {result.get('total', 0)}")
        logger.info(f"成功导入: {result.get('success', 0)}")
        logger.info(f"导入失败: {result.get('error', 0)}")
        if upload_media and result.get('media_uploaded', 0) > 0:
            logger.info(f"媒体文件: {result.get('media_uploaded', 0)} 个")
        # logger.info(result.get('message', '导入完成'))

        if result.get('success', 0) > 0:
            logger.info(f"✅ 成功导入 {result['success']} 个文件到「{notebook_name}」{parent_folder}\n")
            # if upload_media and result.get('media_uploaded', 0) > 0:
            #     logger.info(f"📎 成功上传 {result['media_uploaded']} 个媒体文件")

        if result.get('error', 0) > 0:
            logger.warning(f"⚠️ 有 {result['error']} 个文件导入失败，请检查日志")

    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        logger.error("如果问题持续存在，请检查：")
        logger.error("1. 思源笔记是否正在运行")
        logger.error("2. API地址是否正确")
        logger.error("3. API Token是否有效（如果需要）")
        logger.error("4. 媒体文件路径是否正确（如果启用媒体上传）")


if __name__ == "__main__":
    main()
