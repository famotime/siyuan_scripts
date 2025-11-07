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
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    
# 兼容旧字段，避免未引用变量报错
HAS_WEBDRIVER_MANAGER = False

logger = logging.getLogger(__name__)


class SpecialSiteHandler:
    """特殊网站处理器"""
    
    # 类变量：缓存ChromeDriver路径，避免每次调用都检测
    _cached_chromedriver_path = None
    _chromedriver_manager = None
    
    def __init__(self):
        """初始化处理器"""
        self.site_handlers = {
            'toutiao.com': self._handle_toutiao,
            'm.toutiao.com': self._handle_toutiao,
        }
        # Playwright 模式无需驱动管理
        
    @classmethod
    def _get_chromedriver_path(cls):
        """向后兼容占位（Playwright 不使用 ChromeDriver）。"""
        return None
    
    def can_handle(self, url: str) -> bool:
        """检查是否可以处理该URL"""
        if not HAS_PLAYWRIGHT:
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
        """
        处理今日头条链接
        
        支持两种链接格式：
        1. 标准文章链接：https://www.toutiao.com/article/xxx/
        2. 分享链接：https://www.toutiao.com/w/xxx/
        """
        if not HAS_PLAYWRIGHT:
            logger.warning("Playwright 未安装，无法处理今日头条链接")
            return None
        
        try:
            # 使用 Playwright 渲染并抓取（改进版）
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])

                # 判断是否为分享页/移动端优先页面
                is_share = '/w/' in url or 'm.toutiao.com' in url

                if is_share:
                    ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
                    context = browser.new_context(
                        user_agent=ua,
                        viewport={'width': 390, 'height': 844},
                        is_mobile=True,
                        has_touch=True,
                        extra_http_headers={'Referer': 'https://m.toutiao.com/', 'Accept-Language': 'zh-CN,zh;q=0.9'}
                    )
                else:
                    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    context = browser.new_context(
                        user_agent=ua,
                        viewport={'width': 1920, 'height': 1080},
                        extra_http_headers={'Accept-Language': 'zh-CN,zh;q=0.9'}
                    )

                page = context.new_page()
                logger.info(f"使用Playwright获取今日头条内容: {url}")
                page.goto(url, wait_until='domcontentloaded', timeout=45000)
                try:
                    page.wait_for_load_state('networkidle', timeout=45000)
                except Exception:
                    logger.warning('networkidle 等待超时，继续处理')

                # 分享页尝试跟随 canonical 或目标详情页
                if is_share:
                    try:
                        canonical = page.locator('link[rel="canonical"]').first.get_attribute('href')
                        if not canonical:
                            canonical = page.locator('meta[property="og:url"]').first.get_attribute('content')
                        if canonical and any(x in canonical for x in ['article', 'group', '/a', '/i']):
                            logger.info(f"检测到 canonical，二次跳转: {canonical}")
                            page.goto(canonical, wait_until='domcontentloaded', timeout=45000)
                            try:
                                page.wait_for_load_state('networkidle', timeout=45000)
                            except Exception:
                                pass
                    except Exception:
                        pass

                # 等待标题变更
                try:
                    for _ in range(15):
                        t = (page.title() or '').strip()
                        if t and t != '今日头条' and len(t) > 5:
                            break
                        time.sleep(1)
                except Exception:
                    logger.warning("等待标题更新超时，继续处理")

                # 扩展正文选择器
                # 今日头条分享/移动端“微头条(weitoutiao)”页面在 SSR 输出中常用 .weitoutiao / .weitoutiao-content
                # 普通文章/图文页常见 role 或 class 标记
                content_selectors = [
                    # 微头条/分享页（优先）
                    '.weitoutiao-content', '.weitoutiao', '.news_article .weitoutiao-content',
                    # 常规文章区域
                    '[role="article"]', 'article', '[role="main"]', 'main',
                    '.article-content', '.tt-article-content', '.tt-article',
                    '[class*="article"]', '[class*="content"]', '[data-article]', '[id*="article"]',
                    '.RichText', '.rich-text', '#root main'
                ]

                def extract_from_page(pg) -> Optional[tuple]:
                    # 在一组选择器中寻找 outerHTML
                    for selector in content_selectors:
                        try:
                            pg.wait_for_selector(selector, timeout=20000)
                            loc = pg.locator(selector)
                            if loc.count() > 0:
                                handle = loc.first.element_handle()
                                if handle:
                                    html = handle.evaluate('el => el.outerHTML')
                                    return (html, selector)
                        except Exception:
                            continue
                    return None

                # 先从主页面提取
                found = extract_from_page(page)
                html_content = found[0] if found else None
                matched_selector = found[1] if found else None

                # 若失败，再遍历 frames 提取
                if not html_content:
                    try:
                        for fr in page.frames:
                            if fr == page.main_frame:
                                continue
                            found = extract_from_page(fr)
                            if found:
                                html_content, matched_selector = found
                                logger.info('从子 frame 中提取到正文内容')
                                break
                    except Exception:
                        pass

                # 仍失败则回退整个页面
                # 注意：微头条(.weitoutiao-content/.weitoutiao) 本身内容较短，不强制最小长度
                prefer_small = matched_selector in {'.weitoutiao-content', '.weitoutiao', '.news_article .weitoutiao-content'}
                if not html_content or (len(html_content) < 2000 and not prefer_small):
                    html_content = page.content()
                    logger.info(f"使用整个页面内容，长度: {len(html_content)} 字符")

                # 再次检查是否仍为 JS 重定向
                if (len(html_content) < 2000 and not prefer_small) or 'var glb' in html_content[:1000]:
                    logger.warning("内容可能仍为JS重定向，延时后重取")
                    time.sleep(5)
                    try:
                        page.wait_for_load_state('networkidle', timeout=20000)
                    except Exception:
                        pass
                    html_content = page.content()

                # 标题/描述/作者/时间
                title = "未知标题"
                try:
                    raw_title = (page.title() or '').strip()
                    # 头条“微头条”页 <title> 往往包含多行与标签，优先取首行，裁剪标签和省略号
                    if raw_title:
                        # 取首行，移除末尾省略号和尾随标签段
                        first_line = raw_title.splitlines()[0].strip()
                        # 去掉常见尾部省略号
                        if first_line.endswith('...'):
                            first_line = first_line[:-3].rstrip()
                        # 去掉“ #标签”之后的部分，避免把话题串进标题
                        hash_pos = first_line.find(' #')
                        if hash_pos > 8:  # 避免误删短标题
                            first_line = first_line[:hash_pos].rstrip()
                        if first_line and first_line != '今日头条' and len(first_line) >= 5:
                            title = first_line
                            logger.info(f"从title获取标题: {title[:50]}...")

                    # 常规页面的 heading/h1 回退
                    if not title or len(title) < 8:
                        h = page.locator('[role="heading"]').first
                        if h and h.count() > 0:
                            t = (h.inner_text() or '').strip()
                            if t and len(t) > 8:
                                title = t
                    if not title or len(title) < 8:
                        h1 = page.locator('h1').first
                        if h1 and h1.count() > 0:
                            t = (h1.inner_text() or '').strip()
                            if t and len(t) > 8:
                                title = t

                    # meta og:title 兜底（Playwright 分支补齐 Selenium 的兜底逻辑）
                    if not title or len(title) < 8:
                        ogt = page.locator('meta[property="og:title"]').first
                        if ogt and ogt.count() > 0:
                            t = (ogt.get_attribute('content') or '').strip()
                            if t and len(t) > 8:
                                title = t

                    # 选择器兜底：从常见标题类名/区域提取
                    if not title or len(title) < 8:
                        title_selectors = [
                            'article h1', '.tt-article-content h1', '.article-content h1',
                            '[class*="title"]', '[class*="headline"]', '.byline-title'
                        ]
                        for sel in title_selectors:
                            loc = page.locator(sel)
                            if loc.count() > 0:
                                t = (loc.first.inner_text() or '').strip()
                                if t and len(t) > 8:
                                    title = t
                                    break

                    # 微头条页面：优先用正文首行做标题，避免把“Github仓库/标签”串进标题
                    if is_share:
                        wt = page.locator('.weitoutiao-content').first
                        if wt and wt.count() > 0:
                            t = (wt.inner_text() or '').strip()
                            if t:
                                t_first = t.splitlines()[0].strip()
                                # 如果当前标题较长或包含“Github仓库”等次要信息，则用正文首行替换
                                if (not title or len(title) > 40 or 'Github' in title or 'GitHub' in title):
                                    if len(t_first) > 60:
                                        t_first = t_first[:60].rstrip()
                                    if len(t_first) >= 6:
                                        title = t_first
                except Exception:
                    logger.warning("提取标题失败")

                description = ""
                try:
                    meta_desc = page.locator('meta[name="description"]').first
                    if meta_desc and meta_desc.count() > 0:
                        description = meta_desc.get_attribute('content') or ''
                    if not description:
                        og_desc = page.locator('meta[property="og:description"]').first
                        if og_desc and og_desc.count() > 0:
                            description = og_desc.get_attribute('content') or ''
                except Exception:
                    pass

                author = ""
                try:
                    for sel in ['.article-author', '.author-name', '[data-testid="author"]', '.byline-author', '[class*="author"]', '[class*="source"]', '.source']:
                        loc = page.locator(sel)
                        if loc.count() > 0:
                            txt = (loc.first.inner_text() or '').strip()
                            if txt:
                                author = txt
                                break
                except Exception:
                    pass

                publish_time = ""
                try:
                    for sel in ['[class*="time"]', '[class*="date"]', 'time', '.publish-time', '.article-time']:
                        loc = page.locator(sel)
                        if loc.count() > 0:
                            txt = (loc.first.inner_text() or '').strip()
                            if txt and len(txt) > 5:
                                publish_time = txt
                                break
                except Exception:
                    pass

                logger.info(f"成功提取内容 - 标题: {title[:50] if len(title) > 50 else title}")

                page.close()
                context.close()
                browser.close()

                return {
                    'html_content': html_content,
                    'title': title.strip() if title else "未知标题",
                    'description': description.strip(),
                    'author': author.strip(),
                    'publish_time': publish_time.strip()
                }

            # 结束 Playwright 快路径，下面旧的 Selenium 代码将不会被执行
            # 设置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 创建WebDriver
            # 如果安装了webdriver-manager，使用缓存的路径（只检测一次）
            driver = None
            if HAS_WEBDRIVER_MANAGER:
                try:
                    # 获取ChromeDriver路径（第一次调用时会检测，后续使用缓存）
                    driver_path = self._get_chromedriver_path()
                    if driver_path:
                        service = Service(driver_path)
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        logger.debug("使用webdriver-manager管理的ChromeDriver")
                    else:
                        # 如果获取路径失败，尝试使用系统PATH中的ChromeDriver
                        logger.warning("无法获取ChromeDriver路径，尝试使用系统PATH中的ChromeDriver")
                        driver = webdriver.Chrome(options=chrome_options)
                except Exception as e:
                    logger.warning(f"使用webdriver-manager创建WebDriver失败，尝试使用系统PATH中的ChromeDriver: {e}")
                    try:
                        driver = webdriver.Chrome(options=chrome_options)
                    except Exception as e2:
                        logger.error(f"创建WebDriver失败: {e2}")
                        return None
            else:
                # 没有webdriver-manager，直接使用系统PATH中的ChromeDriver
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e:
                    logger.error(f"创建WebDriver失败: {e}")
                    return None
            
            if driver is None:
                logger.error("无法创建WebDriver")
                return None
            
            try:
                logger.info(f"使用selenium获取今日头条内容: {url}")
                driver.get(url)
                
                # 等待页面加载 - 增加等待时间，特别是对于/w/格式的分享链接
                wait = WebDriverWait(driver, 20)
                
                # 等待页面完全加载，使用多种策略
                try:
                    # 策略1: 等待页面标题不再是"今日头条"
                    wait.until(lambda d: d.title and d.title.strip() and d.title != "今日头条" and len(d.title) > 5)
                    logger.info(f"页面标题已加载: {driver.title}")
                except:
                    logger.warning("等待页面标题超时，继续尝试其他方式")
                
                # 额外等待，确保JavaScript完全执行
                time.sleep(5)
                
                # 策略2: 尝试等待文章内容区域加载
                # 根据浏览器快照，今日头条使用 role="article" 和 role="main"
                content_selectors = [
                    '[role="article"]',  # 最准确的选择器
                    'article',  # 标准HTML5标签
                    '[role="main"]',  # 主要内容区域
                    'main',  # 标准HTML5标签
                    '.article-content',
                    '[class*="article"]',
                    '[class*="content"]',
                ]
                
                content_loaded = False
                for selector in content_selectors:
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        content_loaded = True
                        logger.info(f"检测到内容区域: {selector}")
                        break
                    except:
                        continue
                
                if not content_loaded:
                    logger.warning("未检测到明确的内容区域，继续处理")
                    time.sleep(5)  # 增加等待时间
                
                # 获取页面内容
                # 策略：优先获取main区域（包含article），确保获取完整内容
                html_content = None
                try:
                    # 方法1: 尝试获取main区域（包含article和所有相关内容）
                    main_elements = driver.find_elements(By.CSS_SELECTOR, '[role="main"], main')
                    if main_elements:
                        # 获取main区域的完整HTML，包含所有子元素
                        html_content = main_elements[0].get_attribute('outerHTML')
                        logger.info(f"成功获取main区域内容，长度: {len(html_content)} 字符")
                    else:
                        # 方法2: 如果没有main，尝试获取article区域
                        article_elements = driver.find_elements(By.CSS_SELECTOR, '[role="article"], article')
                        if article_elements:
                            # 获取article及其父容器的HTML，确保包含完整内容
                            article_elem = article_elements[0]
                            # 尝试获取包含article的父容器
                            try:
                                parent = article_elem.find_element(By.XPATH, './..')
                                html_content = parent.get_attribute('outerHTML')
                                logger.info("成功获取article父容器内容")
                            except:
                                html_content = article_elem.get_attribute('outerHTML')
                                logger.info("成功获取article区域内容")
                except Exception as e:
                    logger.warning(f"获取特定区域内容失败: {e}")
                
                # 如果获取特定区域失败或内容太少，使用整个页面
                if not html_content or len(html_content) < 2000:
                    html_content = driver.page_source
                    logger.info(f"使用整个页面内容，长度: {len(html_content)} 字符")
                
                # 检查是否获取到有效内容（不是JavaScript重定向页面）
                if len(html_content) < 2000 or 'var glb' in html_content[:1000]:
                    logger.warning("获取的内容可能仍然是JavaScript重定向页面，尝试等待更长时间并重新获取")
                    time.sleep(8)  # 增加等待时间
                    # 重新获取整个页面
                    html_content = driver.page_source
                    logger.info(f"重新获取页面内容，长度: {len(html_content)} 字符")
                    
                    # 再次尝试从main或article区域提取
                    if 'var glb' in html_content[:1000]:
                        logger.warning("仍然检测到JavaScript重定向页面，但继续处理")
                
                # 提取标题
                title = "未知标题"
                try:
                    # 方法1: 从title标签获取（最可靠）
                    title_text = driver.title
                    if title_text and title_text.strip() and title_text != "今日头条":
                        title = title_text.strip()
                        logger.info(f"从title标签获取标题: {title[:50]}...")
                    
                    # 方法2: 从role="heading"获取（根据浏览器快照）
                    if not title or title == "未知标题" or len(title) < 10:
                        try:
                            heading_elements = driver.find_elements(By.CSS_SELECTOR, '[role="heading"]')
                            for heading in heading_elements:
                                heading_text = heading.text.strip()
                                if heading_text and len(heading_text) > 10:  # 标题应该有一定长度
                                    title = heading_text
                                    logger.info(f"从heading获取标题: {title[:50]}...")
                                    break
                        except:
                            pass
                    
                    # 方法3: 从h1标签获取
                    if not title or title == "未知标题" or len(title) < 10:
                        h1_elements = driver.find_elements(By.TAG_NAME, "h1")
                        for h1 in h1_elements:
                            h1_text = h1.text.strip()
                            if h1_text and len(h1_text) > 10:
                                title = h1_text
                                logger.info(f"从h1获取标题: {title[:50]}...")
                                break
                    
                    # 方法4: 从meta标签获取
                    if not title or title == "未知标题" or len(title) < 10:
                        try:
                            og_title = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
                            if og_title:
                                og_title_content = og_title.get_attribute("content")
                                if og_title_content and og_title_content.strip() and len(og_title_content.strip()) > 10:
                                    title = og_title_content.strip()
                                    logger.info(f"从og:title获取标题: {title[:50]}...")
                        except:
                            pass
                    
                    # 方法5: 从页面中查找标题选择器
                    if not title or title == "未知标题" or len(title) < 10:
                        title_selectors = [
                            'h1[class*="article"]',
                            '.article-title',
                            '[class*="title"]',
                            '[class*="headline"]',
                        ]
                        for selector in title_selectors:
                            try:
                                title_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                for title_elem in title_elements:
                                    title_text = title_elem.text.strip()
                                    if title_text and len(title_text) > 10:
                                        title = title_text
                                        logger.info(f"从{selector}获取标题: {title[:50]}...")
                                        break
                                if title and title != "未知标题":
                                    break
                            except:
                                continue
                                
                except Exception as e:
                    logger.warning(f"提取标题失败: {e}")
                
                # 提取描述
                description = ""
                try:
                    # 方法1: meta description
                    try:
                        meta_desc = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                        if meta_desc:
                            description = meta_desc.get_attribute("content") or ""
                    except:
                        pass
                    
                    # 方法2: og:description
                    if not description:
                        try:
                            og_desc = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
                            if og_desc:
                                description = og_desc.get_attribute("content") or ""
                        except:
                            pass
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
                        '.byline-author',
                        '[class*="author"]',
                        '[class*="source"]',
                        '.source'
                    ]
                    
                    for selector in author_selectors:
                        try:
                            author_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for author_elem in author_elements:
                                author_text = author_elem.text.strip()
                                if author_text and len(author_text) > 0:
                                    author = author_text
                                    break
                            if author:
                                break
                        except:
                            continue
                except:
                    pass
                
                # 提取发布时间
                publish_time = ""
                try:
                    time_selectors = [
                        '[class*="time"]',
                        '[class*="date"]',
                        'time',
                        '.publish-time',
                        '.article-time'
                    ]
                    
                    for selector in time_selectors:
                        try:
                            time_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for time_elem in time_elements:
                                time_text = time_elem.text.strip()
                                if time_text and len(time_text) > 5:
                                    publish_time = time_text
                                    break
                            if publish_time:
                                break
                        except:
                            continue
                except:
                    pass
                
                logger.info(f"成功提取内容 - 标题: {title[:50] if len(title) > 50 else title}")
                
                return {
                    'html_content': html_content,
                    'title': title.strip() if title else "未知标题",
                    'description': description.strip(),
                    'author': author.strip(),
                    'publish_time': publish_time.strip()
                }
                
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"Playwright 处理今日头条链接失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def get_installation_guide(self) -> str:
        """获取安装指南"""
        if not HAS_PLAYWRIGHT:
            return """
要处理今日头条等需要动态渲染的网站，建议安装 Playwright：

1. 安装依赖：
   pip install playwright

2. 安装浏览器内核：
   python -m playwright install chromium

3. Windows 终端请设置 UTF-8：
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

安装完成后，程序将自动使用 Playwright 处理今日头条链接。
"""
        return "Playwright 已安装，可以处理特殊网站。"


def create_special_site_handler() -> SpecialSiteHandler:
    """创建特殊网站处理器实例"""
    return SpecialSiteHandler()
