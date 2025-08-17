"""
特殊网站处理器
处理需要特殊方法获取内容的网站，如今日头条等
"""

import logging
import re
import time
from typing import Optional, Dict
from urllib.parse import urlparse

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

logger = logging.getLogger(__name__)


class SpecialSiteHandler:
    """特殊网站处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.site_handlers = {
            'toutiao.com': self._handle_toutiao,
            'm.toutiao.com': self._handle_toutiao,
        }
    
    def can_handle(self, url: str) -> bool:
        """检查是否可以处理该URL"""
        if not HAS_SELENIUM:
            return False
            
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        return any(site in domain for site in self.site_handlers.keys())
    
    def get_content(self, url: str) -> Optional[Dict[str, str]]:
        """获取特殊网站的内容"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        for site_pattern, handler in self.site_handlers.items():
            if site_pattern in domain:
                return handler(url)
        
        return None
    
    def _handle_toutiao(self, url: str) -> Optional[Dict[str, str]]:
        """处理今日头条链接"""
        if not HAS_SELENIUM:
            logger.warning("selenium未安装，无法处理今日头条链接")
            return None
        
        try:
            # 设置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 创建WebDriver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                logger.info(f"使用selenium获取今日头条内容: {url}")
                driver.get(url)
                
                # 等待页面加载
                wait = WebDriverWait(driver, 10)
                
                # 等待文章内容加载
                try:
                    # 尝试等待文章标题
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                except:
                    # 如果没有h1标签，等待一段时间让页面完全加载
                    time.sleep(3)
                
                # 获取页面内容
                html_content = driver.page_source
                
                # 提取标题
                title = "未知标题"
                try:
                    title_element = driver.find_element(By.TAG_NAME, "title")
                    if title_element:
                        title = title_element.get_attribute("textContent") or title_element.text
                    
                    # 如果title标签没有内容，尝试h1标签
                    if not title or title == "未知标题":
                        h1_elements = driver.find_elements(By.TAG_NAME, "h1")
                        if h1_elements:
                            title = h1_elements[0].text
                except Exception as e:
                    logger.warning(f"提取标题失败: {e}")
                
                # 提取描述
                description = ""
                try:
                    meta_desc = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                    if meta_desc:
                        description = meta_desc.get_attribute("content") or ""
                except:
                    pass
                
                # 提取作者
                author = ""
                try:
                    # 今日头条的作者信息可能在不同的位置
                    author_selectors = [
                        '.article-author',
                        '.author-name',
                        '[data-testid="author"]',
                        '.byline-author'
                    ]
                    
                    for selector in author_selectors:
                        try:
                            author_element = driver.find_element(By.CSS_SELECTOR, selector)
                            if author_element:
                                author = author_element.text
                                break
                        except:
                            continue
                except:
                    pass
                
                return {
                    'html_content': html_content,
                    'title': title.strip() if title else "未知标题",
                    'description': description.strip(),
                    'author': author.strip(),
                    'publish_time': ""
                }
                
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"selenium处理今日头条链接失败: {e}")
            return None
    
    def get_installation_guide(self) -> str:
        """获取安装指南"""
        if not HAS_SELENIUM:
            return """
要处理今日头条等特殊网站，需要安装selenium和Chrome浏览器：

1. 安装selenium:
   pip install selenium

2. 安装Chrome浏览器（如果尚未安装）

3. 下载ChromeDriver:
   - 访问 https://chromedriver.chromium.org/
   - 下载与您的Chrome版本匹配的ChromeDriver
   - 将ChromeDriver添加到系统PATH中

4. 或者使用webdriver-manager自动管理：
   pip install webdriver-manager
   
安装完成后，程序将自动使用selenium处理今日头条链接。
"""
        return "selenium已安装，可以处理特殊网站。"


def create_special_site_handler() -> SpecialSiteHandler:
    """创建特殊网站处理器实例"""
    return SpecialSiteHandler()
