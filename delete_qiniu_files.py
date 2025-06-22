"""
基于API批量删除七牛云上的文件
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 检查是否安装了七牛云SDK
try:
    from qiniu import Auth, BucketManager, build_batch_delete
except ImportError:
    logger.error("请先安装七牛云SDK: pip install qiniu")
    exit(1)


class QiniuFileDeleter:
    """七牛云文件批量删除工具"""

    def __init__(self, access_key: str = None, secret_key: str = None):
        """
        初始化七牛云删除工具

        :param access_key: 七牛云Access Key
        :param secret_key: 七牛云Secret Key
        """
        self.access_key = access_key or os.getenv("QINIU_ACCESS_KEY")
        self.secret_key = secret_key or os.getenv("QINIU_SECRET_KEY")

        if not self.access_key or not self.secret_key:
            raise ValueError("请设置七牛云Access Key和Secret Key")

        # 初始化认证对象
        self.auth = Auth(self.access_key, self.secret_key)

        # 初始化存储空间管理对象
        self.bucket_manager = BucketManager(self.auth)

        logger.info("七牛云删除工具初始化成功")

    def get_file_list(self, bucket_name: str, prefix: str = None,
                      limit: int = 1000, marker: str = None, max_files: int = None) -> List[str]:
        """
        获取存储空间中的文件列表

        :param bucket_name: 存储空间名称
        :param prefix: 文件前缀过滤
        :param limit: 每次API调用获取的文件数量限制
        :param marker: 分页标记
        :param max_files: 总共获取的文件数量上限，None表示获取所有文件
        :return: 文件名列表
        """
        logger.info(f"正在获取存储空间 '{bucket_name}' 中的文件列表...")
        if max_files:
            logger.info(f"最多获取 {max_files} 个文件")

        all_files = []

        while True:
            try:
                # 如果设置了max_files，调整当前批次的limit
                current_limit = limit
                if max_files and len(all_files) + limit > max_files:
                    current_limit = max_files - len(all_files)
                    if current_limit <= 0:
                        break

                # 获取文件列表
                ret, eof, info = self.bucket_manager.list(
                    bucket_name,
                    prefix=prefix,
                    marker=marker,
                    limit=current_limit,
                    delimiter=None
                )

                if info.status_code != 200:
                    logger.error(f"获取文件列表失败: {info}")
                    break

                # 提取文件名
                if ret and 'items' in ret:
                    files = [item['key'] for item in ret['items']]
                    all_files.extend(files)
                    logger.info(f"获取到 {len(files)} 个文件")

                    # 如果设置了max_files且已达到上限，停止获取
                    if max_files and len(all_files) >= max_files:
                        logger.info(f"已达到文件数量上限 {max_files}，停止获取")
                        break

                # 检查是否还有更多文件
                if eof:
                    break

                # 更新分页标记
                marker = ret.get('marker')

            except Exception as e:
                logger.error(f"获取文件列表时发生错误: {e}")
                break

        logger.info(f"总共获取到 {len(all_files)} 个文件")
        return all_files

    def delete_files_batch(self, bucket_name: str, file_keys: List[str],
                          batch_size: int = 1000) -> Dict[str, Any]:
        """
        批量删除文件

        :param bucket_name: 存储空间名称
        :param file_keys: 要删除的文件名列表
        :param batch_size: 每批删除的文件数量
        :return: 删除结果统计
        """
        if not file_keys:
            logger.warning("没有要删除的文件")
            return {"total": 0, "success": 0, "failed": 0, "errors": []}

        logger.info(f"开始批量删除 {len(file_keys)} 个文件...")

        total_files = len(file_keys)
        success_count = 0
        failed_count = 0
        errors = []

        # 分批删除
        for i in range(0, total_files, batch_size):
            batch_files = file_keys[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_files + batch_size - 1) // batch_size

            logger.info(f"正在处理第 {batch_num}/{total_batches} 批，包含 {len(batch_files)} 个文件")

            try:
                # 构建批量删除操作
                ops = build_batch_delete(bucket_name, batch_files)

                # 执行批量删除
                ret, info = self.bucket_manager.batch(ops)

                if info.status_code == 200:
                    # 统计成功和失败的文件
                    if ret:
                        for i, result in enumerate(ret):
                            if result.get('code') == 200:
                                success_count += 1
                            else:
                                failed_count += 1
                                error_msg = f"文件 {batch_files[i]} 删除失败: {result}"
                                errors.append(error_msg)
                                logger.warning(error_msg)
                    else:
                        # 如果没有返回详细结果，认为全部成功
                        success_count += len(batch_files)

                    logger.info(f"第 {batch_num} 批处理完成")
                else:
                    failed_count += len(batch_files)
                    error_msg = f"第 {batch_num} 批删除失败: {info}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            except Exception as e:
                failed_count += len(batch_files)
                error_msg = f"第 {batch_num} 批删除时发生异常: {e}"
                errors.append(error_msg)
                logger.error(error_msg)

        result = {
            "total": total_files,
            "success": success_count,
            "failed": failed_count,
            "errors": errors
        }

        logger.info(f"批量删除完成 - 总计: {total_files}, 成功: {success_count}, 失败: {failed_count}")
        return result

    def delete_files_by_prefix(self, bucket_name: str, prefix: str = None,
                              confirm: bool = False) -> Dict[str, Any]:
        """
        根据前缀删除文件

        :param bucket_name: 存储空间名称
        :param prefix: 文件前缀
        :param confirm: 是否确认删除
        :return: 删除结果
        """
        if not confirm:
            logger.warning("请设置 confirm=True 来确认删除操作")
            return {"error": "需要确认删除操作"}

        logger.info(f"开始删除存储空间 '{bucket_name}' 中前缀为 '{prefix}' 的文件...")

        # 获取文件列表
        file_list = self.get_file_list(bucket_name, prefix=prefix)

        if not file_list:
            logger.info("没有找到匹配的文件")
            return {"total": 0, "success": 0, "failed": 0, "errors": []}

        # 批量删除
        return self.delete_files_batch(bucket_name, file_list)

    def delete_all_files(self, bucket_name: str, confirm: bool = False) -> Dict[str, Any]:
        """
        删除存储空间中的所有文件

        :param bucket_name: 存储空间名称
        :param confirm: 是否确认删除
        :return: 删除结果
        """
        if not confirm:
            logger.warning("请设置 confirm=True 来确认删除操作")
            return {"error": "需要确认删除操作"}

        logger.warning(f"即将删除存储空间 '{bucket_name}' 中的所有文件！")
        return self.delete_files_by_prefix(bucket_name, prefix=None, confirm=True)

    def save_file_list(self, bucket_name: str, output_file: str = None,
                      prefix: str = None) -> str:
        """
        保存文件列表到文件

        :param bucket_name: 存储空间名称
        :param output_file: 输出文件路径
        :param prefix: 文件前缀过滤
        :return: 输出文件路径
        """
        if not output_file:
            output_file = f"{bucket_name}_files.txt"

        file_list = self.get_file_list(bucket_name, prefix=prefix)

        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            for file_key in file_list:
                f.write(f"{file_key}\n")

        logger.info(f"文件列表已保存到: {output_path}")
        return str(output_path)

    def get_limited_file_list(self, bucket_name: str, max_files: int = 100,
                             prefix: str = None) -> List[str]:
        """
        获取有限数量的文件列表（便捷方法）

        :param bucket_name: 存储空间名称
        :param max_files: 最多获取的文件数量
        :param prefix: 文件前缀过滤
        :return: 文件名列表
        """
        return self.get_file_list(bucket_name, prefix=prefix, max_files=max_files)


def main():
    """
    主函数 - 演示如何使用
    """
    # 从环境变量获取配置
    access_key = os.getenv("QINIU_ACCESS_KEY")
    secret_key = os.getenv("QINIU_SECRET_KEY")
    bucket_name = os.getenv("QINIU_BUCKET_NAME")

    if not all([access_key, secret_key, bucket_name]):
        logger.error("请设置环境变量: QINIU_ACCESS_KEY, QINIU_SECRET_KEY, QINIU_BUCKET_NAME")
        return

    try:
        # 创建删除工具实例
        deleter = QiniuFileDeleter(access_key, secret_key)

        # 示例1: 获取并保存文件列表
        # logger.info("=== 获取文件列表 ===")
        # file_list = deleter.get_file_list(bucket_name, max_files=10)  # 最多获取10个文件用于演示
        # if file_list:
        #     logger.info(f"找到文件: {file_list[:5]}...")  # 只显示前5个

        # 示例2: 保存文件列表到文件
        # logger.info("=== 保存文件列表 ===")
        # list_file = deleter.save_file_list(bucket_name, "file_list.txt")

        # 示例3: 删除指定前缀的文件（需要手动确认）
        # logger.info("=== 删除指定前缀文件 ===")
        # result = deleter.delete_files_by_prefix(bucket_name, prefix="test/", confirm=True)
        # logger.info(f"删除结果: {result}")

        # 示例4: 删除指定文件列表
        # logger.info("=== 删除指定文件 ===")
        # files_to_delete = ["file1.jpg", "file2.png"]  # 替换为实际要删除的文件
        # result = deleter.delete_files_batch(bucket_name, files_to_delete)
        # logger.info(f"删除结果: {result}")

        # 示例5: 删除存储空间中的所有文件
        logger.info("=== 删除所有文件 ===")
        result = deleter.delete_all_files(
            bucket_name,
            confirm=True  # 必须设置为True才会执行删除
        )
        logger.info(f"删除结果: {result}")

        logger.info("操作完成")

    except Exception as e:
        logger.error(f"程序执行失败: {e}")


if __name__ == "__main__":
    main()