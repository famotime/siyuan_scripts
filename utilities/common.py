"""
公共配置和工具函数
"""
import logging
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 默认配置
DEFAULT_API_URL = os.getenv("SIYUAN_API_URL", "http://127.0.0.1:6806")
DEFAULT_API_TOKEN = os.getenv("SIYUAN_API_TOKEN")

def setup_logging(level=logging.INFO):
    """配置日志系统"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

# 创建默认日志记录器
logger = setup_logging()