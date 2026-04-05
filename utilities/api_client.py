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

        self.headers = {"Content-Type": "application/json"}
        self._auth_mode = "token" if self.api_token else "none"
        if self._auth_mode == "token":
            self.headers["Authorization"] = f"Token {self.api_token}"

    def _build_headers(self, include_auth: bool) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if include_auth and self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"
        return headers

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

            include_auth = self._auth_mode == "token"
            response = requests.post(
                f"{self.api_url}{api_path}",
                headers=self._build_headers(include_auth),
                json=payload,
                timeout=30
            )
            if response.status_code == 401 and include_auth:
                logger.warning("接口 %s 拒绝 Authorization 头，回退为无认证模式重试", api_path)
                response = requests.post(
                    f"{self.api_url}{api_path}",
                    headers=self._build_headers(False),
                    json=payload,
                    timeout=30
                )
                if response.status_code < 400:
                    self._auth_mode = "none"
                    self.headers = self._build_headers(False)

            response.raise_for_status()
            json_response = response.json()

            if json_response.get("code") != 0:
                logger.error(f"调用API {api_path} 出错: {json_response.get('msg')}")
                return None

            return json_response.get("data")

        except requests.exceptions.RequestException as e:
            logger.error(f"请求API {api_path} 失败: {e}")
            return None

