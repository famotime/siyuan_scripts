"""
从为知笔记读取信息，导出单篇或批量导出markdown笔记
"""

import sys
import logging
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# 导入各个模块
from export_wiznotes.wiz_client import WizNoteClient
from export_wiznotes.note_exporter import NoteExporter
from export_wiznotes.utils import setup_logging, list_folders_and_notes


def read_folders_from_log(log_file):
    """从日志文件中读取文件夹列表"""
    folders = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            folder = line.strip()
            if folder and not folder.startswith('#'):
                folders.append(folder)
    return folders


def export_folder(args):
    """导出单个文件夹的笔记"""
    folder, client, export_dir, max_notes = args
    try:
        exporter = NoteExporter(client)
        logging.info(f"开始导出文件夹: {folder}")
        exporter.export_notes(
            folder=folder,
            export_dir=export_dir,
            max_notes=max_notes,
            resume=True
        )
        logging.info(f"文件夹 {folder} 导出完成")
        return True
    except Exception as e:
        logging.error(f"导出文件夹 {folder} 时出错: {e}")
        return False


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    # ========== 配置参数 ==========
    # 基础配置
    export_dir = Path("H:/为知笔记导出MD备份")
    max_notes = None  # 不限制笔记数量，自动处理超过1000条笔记的情况（通过双向查询和去重）

    # 默认导出"My Emails"文件夹
    default_folders = ["/My Emails/"]

    # 性能配置
    max_workers = 3  # 配置并行下载的线程数

    try:
        # 设置日志
        setup_logging(export_dir)

        # 检查环境变量
        wiz_username = os.getenv('WIZ_USERNAME')
        wiz_password = os.getenv('WIZ_PASSWORD')

        if not wiz_username or not wiz_password:
            logging.error("请在.env文件中设置WIZ_USERNAME和WIZ_PASSWORD")
            print("请在项目根目录创建.env文件，并添加以下配置：")
            print("WIZ_USERNAME=your_username@example.com")
            print("WIZ_PASSWORD=your_password")
            return

        # 创建临时配置
        temp_config = {
            'wiz': {
                'username': wiz_username,
                'password': wiz_password
            }
        }

        # 创建客户端并登录
        client = WizNoteClient()
        client.config = temp_config
        client.login()

        # 使用默认文件夹列表
        folders = default_folders
        logging.info(f"将导出以下文件夹: {folders}")

        # 准备导出参数
        export_args = [(folder, client, export_dir, max_notes) for folder in folders]

        # 使用线程池并行导出
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_folder = {
                executor.submit(export_folder, export_arg): export_arg[0]
                for export_arg in export_args
            }

            # 处理完成的任务
            success_count = 0
            for future in as_completed(future_to_folder):
                folder = future_to_folder[future]
                try:
                    if future.result():
                        success_count += 1
                except Exception as e:
                    logging.error(f"处理文件夹 {folder} 时发生异常: {e}")

        logging.info(f"导出完成，成功导出 {success_count}/{len(folders)} 个文件夹")

    except KeyboardInterrupt:
        logging.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logging.error(f"程序执行失败: {e}")


if __name__ == '__main__':
    main()