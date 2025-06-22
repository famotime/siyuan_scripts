"""
媒体文件管理器
"""
import requests
from pathlib import Path
from typing import Optional
from .common import logger


class MediaManager:
    """媒体文件管理类"""

    def __init__(self, api_client):
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
                # logger.info(f"成功上传文件: {file_path.name} -> {uploaded_path}")
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