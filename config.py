"""
思源笔记脚本项目配置文件
统一管理各种导出目录和路径配置
"""

from pathlib import Path
import os
from typing import Dict, Any

class Config:
    """配置管理类"""
    
    def __init__(self):
        # 基础导出目录
        self.base_export_dir = "H:/为知笔记导出MD备份"
        
        # 各种导出子目录
        self.export_subdirs = {
            "wiznotes": "My Emails",           # 为知笔记导出目录
            "urls": "urls_to_markdown",        # URL转Markdown导出目录
            "clips": "clips_to_markdown",      # 剪贴板内容转Markdown导出目录
            "processed": "已转思源",            # 已处理文件移动目录
        }
        
        # 思源笔记相关配置
        self.siyuan = {
            "default_notebook": "剪藏笔记本",
            "default_parent_folder": "/Web收集箱/urls2markdown",
        }
        
        # 为知笔记相关配置
        self.wiznotes = {
            "default_folders": ["/My Emails/"],
            "max_workers": 3,
        }
        
        # 媒体文件配置
        self.media = {
            "download_media": True,
            "media_subdir": "media",
        }
    
    @property
    def base_path(self) -> Path:
        """获取基础导出目录的Path对象"""
        return Path(self.base_export_dir)
    
    def get_export_path(self, subdir_key: str) -> Path:
        """获取指定子目录的完整路径"""
        if subdir_key not in self.export_subdirs:
            raise ValueError(f"未知的子目录键: {subdir_key}")
        
        return self.base_path / self.export_subdirs[subdir_key]
    
    def get_wiznotes_path(self) -> Path:
        """获取为知笔记导出目录路径"""
        return self.get_export_path("wiznotes")
    
    def get_urls_path(self) -> Path:
        """获取URL转Markdown导出目录路径"""
        return self.get_export_path("urls")
    
    def get_clips_path(self) -> Path:
        """获取剪贴板内容转Markdown导出目录路径"""
        return self.get_export_path("clips")
    
    def get_processed_path(self) -> Path:
        """获取已处理文件目录路径"""
        return self.get_export_path("processed")
    
    def get_media_path(self, base_subdir: str) -> Path:
        """获取指定导出目录下的媒体文件目录路径"""
        base_path = self.get_export_path(base_subdir)
        return base_path / self.media["media_subdir"]
    
    def update_base_dir(self, new_base_dir: str):
        """更新基础导出目录"""
        self.base_export_dir = new_base_dir
    
    def update_subdir(self, subdir_key: str, new_subdir: str):
        """更新指定的子目录名"""
        if subdir_key not in self.export_subdirs:
            raise ValueError(f"未知的子目录键: {subdir_key}")
        
        self.export_subdirs[subdir_key] = new_subdir
    
    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典格式"""
        return {
            "base_export_dir": self.base_export_dir,
            "export_subdirs": self.export_subdirs.copy(),
            "siyuan": self.siyuan.copy(),
            "wiznotes": self.wiznotes.copy(),
            "media": self.media.copy(),
        }
    
    def from_dict(self, config_dict: Dict[str, Any]):
        """从字典格式加载配置"""
        if "base_export_dir" in config_dict:
            self.base_export_dir = config_dict["base_export_dir"]
        
        if "export_subdirs" in config_dict:
            self.export_subdirs.update(config_dict["export_subdirs"])
        
        if "siyuan" in config_dict:
            self.siyuan.update(config_dict["siyuan"])
        
        if "wiznotes" in config_dict:
            self.wiznotes.update(config_dict["wiznotes"])
        
        if "media" in config_dict:
            self.media.update(config_dict["media"])

# 创建全局配置实例
config = Config()

# 便捷函数
def get_config() -> Config:
    """获取全局配置实例"""
    return config

def get_export_path(subdir_key: str) -> Path:
    """获取指定子目录的完整路径"""
    return config.get_export_path(subdir_key)

def get_wiznotes_path() -> Path:
    """获取为知笔记导出目录路径"""
    return config.get_wiznotes_path()

def get_urls_path() -> Path:
    """获取URL转Markdown导出目录路径"""
    return config.get_urls_path()

def get_clips_path() -> Path:
    """获取剪贴板内容转Markdown导出目录路径"""
    return config.get_clips_path()

def get_processed_path() -> Path:
    """获取已处理文件目录路径"""
    return config.get_processed_path()

def get_media_path(base_subdir: str) -> Path:
    """获取指定导出目录下的媒体文件目录路径"""
    return config.get_media_path(base_subdir)
