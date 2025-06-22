"""
文件管理器
"""
import json
from pathlib import Path
from typing import Dict, Any
from .common import logger


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