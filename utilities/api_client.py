"""
思源笔记API客户端
"""
import requests
from typing import Dict, Any, Optional
from .common import DEFAULT_API_URL, DEFAULT_API_TOKEN, logger


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

