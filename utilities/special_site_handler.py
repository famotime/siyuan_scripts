"""
特殊网站处理器
处理需要特殊方法获取内容的网站，如今日头条等
"""

import logging
import re
import time
from html import escape
from typing import Optional, Dict
from urllib.parse import urlparse
import requests

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
        self.last_error: Dict[str, str] = {}
        self.goto_timeout_ms = 15000
        self.networkidle_timeout_ms = 6000
        self.site_handlers = {
            'toutiao.com': self._handle_toutiao,
            'm.toutiao.com': self._handle_toutiao,
            'x.com': self._handle_x_post,
            'twitter.com': self._handle_x_post,
        }
        # Playwright 模式无需驱动管理

    def _set_last_error(self, code: str, message: str, stage: str = "") -> None:
        """记录最近一次特殊处理失败原因。"""
        self.last_error = {
            "code": code,
            "message": message,
            "stage": stage,
        }

    def _is_unavailable_content(self, text: str) -> bool:
        """判断页面是否提示文章已失效或不可访问。"""
        if not text:
            return False

        normalized = re.sub(r"\s+", "", text).lower()
        unavailable_markers = [
            "内容不存在",
            "文章不存在",
            "已失效",
            "已删除",
            "无法查看",
            "暂时无法访问",
            "404",
            "page not found",
            "content unavailable",
        ]
        return any(marker in normalized for marker in unavailable_markers)
        
    @classmethod
    def _get_chromedriver_path(cls):
        """向后兼容占位（Playwright 不使用 ChromeDriver）。"""
        return None
    
    def can_handle(self, url: str) -> bool:
        """检查是否可以处理该URL"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        if "x.com" in domain or "twitter.com" in domain:
            return True
        return HAS_PLAYWRIGHT and any(site in domain for site in self.site_handlers.keys())
    
    def get_content(self, url: str) -> Optional[Dict[str, str]]:
        """获取特殊网站的内容"""
        self.last_error = {}
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        for site_pattern, handler in self.site_handlers.items():
            if site_pattern in domain:
                return handler(url)
        
        self._set_last_error("UNSUPPORTED_SPECIAL_SITE", "未匹配到对应的特殊站点处理器", "route")
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
            self._set_last_error("PLAYWRIGHT_MISSING", "Playwright 未安装，无法处理动态页面", "init")
            return None

        browser = None
        context = None
        page = None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])

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
                page.goto(url, wait_until='domcontentloaded', timeout=self.goto_timeout_ms)
                try:
                    page.wait_for_load_state('networkidle', timeout=self.networkidle_timeout_ms)
                except PlaywrightTimeoutError:
                    logger.warning('networkidle 等待超时，继续处理')

                quick_probe = ""
                try:
                    title = page.title() or ""
                    body_text = page.locator('body').inner_text(timeout=2500) or ""
                    quick_probe = f"{title}\n{body_text[:2000]}"
                except Exception:
                    pass

                if self._is_unavailable_content(quick_probe):
                    self._set_last_error("ARTICLE_UNAVAILABLE", "页面提示内容不存在或已失效", "probe")
                    return None

                if is_share:
                    try:
                        canonical = page.locator('link[rel="canonical"]').first.get_attribute('href')
                        if not canonical:
                            canonical = page.locator('meta[property="og:url"]').first.get_attribute('content')
                        if canonical and any(x in canonical for x in ['article', 'group', '/a', '/i']):
                            logger.info(f"检测到 canonical，二次跳转: {canonical}")
                            page.goto(canonical, wait_until='domcontentloaded', timeout=10000)
                            try:
                                page.wait_for_load_state('networkidle', timeout=5000)
                            except PlaywrightTimeoutError:
                                pass
                    except Exception:
                        pass

                # 轻量等待标题更新，避免长期阻塞
                try:
                    for _ in range(5):
                        t = (page.title() or '').strip()
                        if t and t != '今日头条' and len(t) > 5:
                            break
                        time.sleep(0.4)
                except Exception:
                    logger.warning("等待标题更新超时，继续处理")

                content_selectors = [
                    '.weitoutiao-content', '.weitoutiao', '.news_article .weitoutiao-content',
                    '[role="article"]', 'article', '[role="main"]', 'main',
                    '.article-content', '.tt-article-content', '.tt-article',
                    '[class*="article"]', '[class*="content"]', '[data-article]', '[id*="article"]',
                    '.RichText', '.rich-text', '#root main'
                ]

                def extract_from_page(pg) -> Optional[tuple]:
                    for selector in content_selectors:
                        try:
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

                prefer_small = matched_selector in {'.weitoutiao-content', '.weitoutiao', '.news_article .weitoutiao-content'}
                if not html_content or (len(html_content) < 2000 and not prefer_small):
                    html_content = page.content()
                    logger.info(f"使用整个页面内容，长度: {len(html_content)} 字符")

                if (len(html_content) < 2000 and not prefer_small) or 'var glb' in html_content[:1000]:
                    logger.warning("内容可能仍为JS重定向，快速重试一次")
                    time.sleep(1)
                    try:
                        page.wait_for_load_state('networkidle', timeout=3000)
                    except PlaywrightTimeoutError:
                        pass
                    html_content = page.content()

                if self._is_unavailable_content(html_content):
                    self._set_last_error("ARTICLE_UNAVAILABLE", "页面提示内容不存在或已失效", "content")
                    return None

                if not html_content or len(html_content.strip()) < 100:
                    self._set_last_error("CONTENT_EMPTY", "页面内容过短，无法提取正文", "content")
                    return None

                title = "未知标题"
                try:
                    raw_title = (page.title() or '').strip()
                    if raw_title:
                        first_line = raw_title.splitlines()[0].strip()
                        if first_line.endswith('...'):
                            first_line = first_line[:-3].rstrip()
                        hash_pos = first_line.find(' #')
                        if hash_pos > 8:
                            first_line = first_line[:hash_pos].rstrip()
                        if first_line and first_line != '今日头条' and len(first_line) >= 5:
                            title = first_line
                            logger.info(f"从title获取标题: {title[:50]}...")

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

                    if not title or len(title) < 8:
                        ogt = page.locator('meta[property="og:title"]').first
                        if ogt and ogt.count() > 0:
                            t = (ogt.get_attribute('content') or '').strip()
                            if t and len(t) > 8:
                                title = t

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

                return {
                    'html_content': html_content,
                    'title': title.strip() if title else "未知标题",
                    'description': description.strip(),
                    'author': author.strip(),
                    'publish_time': publish_time.strip()
                }
        except PlaywrightTimeoutError as e:
            self._set_last_error("PLAYWRIGHT_TIMEOUT", f"动态渲染超时: {e}", "playwright")
            logger.error(f"Playwright 处理今日头条链接超时: {e}")
            return None
        except Exception as e:
            self._set_last_error("SPECIAL_HANDLER_ERROR", str(e), "playwright")
            logger.error(f"Playwright 处理今日头条链接失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
        finally:
            for target in (page, context, browser):
                if target:
                    try:
                        target.close()
                    except Exception:
                        pass

    def _extract_x_post_id(self, url: str) -> Optional[str]:
        """提取X/Twitter帖子ID。"""
        parsed = urlparse(url)
        path = parsed.path or ""
        match = re.search(r"/status/(\d+)", path)
        if match:
            return match.group(1)
        return None

    def _build_x_html(self, text: str, author: str, post_url: str, media_urls=None) -> str:
        """将X帖子信息组装为可转换的HTML。"""
        media_urls = media_urls or []
        escaped_text = escape(text or "").replace("\n", "<br/>")
        escaped_author = escape(author or "")
        escaped_url = escape(post_url or "")
        parts = [
            "<article class='x-post'>",
            f"<p><strong>{escaped_author}</strong></p>" if escaped_author else "",
            f"<p>{escaped_text}</p>" if escaped_text else "",
            f"<p><a href='{escaped_url}'>{escaped_url}</a></p>" if escaped_url else "",
        ]
        for media_url in media_urls:
            safe_url = escape(media_url)
            parts.append(f"<p><img src='{safe_url}' alt='media' /></p>")
        parts.append("</article>")
        return "".join(parts)

    def _build_x_html_from_blocks(self, blocks: list, author: str, post_url: str) -> str:
        """按提取到的顺序块重建X帖子HTML（文本/图片交错）。"""
        escaped_author = escape(author or "")
        escaped_url = escape(post_url or "")
        html_parts = ["<article class='x-post'>"]

        if escaped_author:
            html_parts.append(f"<p><strong>{escaped_author}</strong></p>")

        for block in blocks or []:
            block_type = block.get("type")
            if block_type == "text":
                content = (block.get("value") or "").strip()
                if content:
                    html_parts.append(f"<p>{escape(content).replace(chr(10), '<br/>')}</p>")
            elif block_type == "image":
                src = (block.get("value") or "").strip()
                if src:
                    safe_src = escape(src)
                    html_parts.append(f"<p><img src='{safe_src}' alt='media' /></p>")

        if escaped_url:
            html_parts.append(f"<p><a href='{escaped_url}'>{escaped_url}</a></p>")

        html_parts.append("</article>")
        return "".join(html_parts)

    def _clean_x_article_text(self, text: str) -> str:
        """清洗X页面article文本，尽量去掉登录提示和导航噪音。"""
        if not text:
            return ""

        noise_lines = {
            "don’t miss what’s happening",
            "don't miss what’s happening",
            "don't miss what's happening",
            "people on x are the first to know.",
            "log in",
            "sign up",
            "see new posts",
            "conversation",
            "article",
        }

        cleaned_lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            lower_line = line.lower()
            if lower_line in noise_lines:
                continue

            # 过滤纯数字互动计数行
            if re.fullmatch(r"[\d,.]+[kKmM]?", line):
                continue
            if re.fullmatch(r"[\d,.]+(?:万|亿|千)?", line):
                continue
            if line.startswith("@") and len(line) <= 40:
                continue

            cleaned_lines.append(line)

        # 截断过长内容，避免把整页评论都放进正文
        return "\n".join(cleaned_lines[:60]).strip()

    def _extract_x_media_urls_from_page(self, page) -> list:
        """从X页面提取图片/视频封面链接。"""
        media_urls = []
        seen = set()

        def add_candidate(raw_url: str):
            if not raw_url:
                return
            url = raw_url.strip()
            if not url.startswith("http"):
                return
            lower_url = url.lower()

            # 过滤头像/emoji等非正文媒体
            blocked_patterns = [
                "profile_images",
                "profile_banners",
                "emoji",
                "abs.twimg.com",
            ]
            if any(pattern in lower_url for pattern in blocked_patterns):
                return

            allowed_markers = [
                "pbs.twimg.com/media/",
                "pbs.twimg.com/ext_tw_video_thumb/",
                "video.twimg.com/ext_tw_video_thumb/",
                "twimg.com/media/",
            ]
            if not any(marker in lower_url for marker in allowed_markers):
                return

            if url not in seen:
                seen.add(url)
                media_urls.append(url)

        try:
            selectors = [
                "[data-testid='tweetPhoto'] img",
                "article img",
                "img[src*='pbs.twimg.com/media']",
                "img[src*='ext_tw_video_thumb']",
            ]
            for selector in selectors:
                loc = page.locator(selector)
                count = min(loc.count(), 12)
                for i in range(count):
                    try:
                        src = loc.nth(i).get_attribute("src")
                        add_candidate(src)
                    except Exception:
                        continue
        except Exception:
            pass

        try:
            poster_loc = page.locator("video[poster]")
            count = min(poster_loc.count(), 6)
            for i in range(count):
                try:
                    poster = poster_loc.nth(i).get_attribute("poster")
                    add_candidate(poster)
                except Exception:
                    continue
        except Exception:
            pass

        try:
            og_image = page.locator("meta[property='og:image']").first
            if og_image and og_image.count() > 0:
                add_candidate(og_image.get_attribute("content"))
        except Exception:
            pass

        return media_urls

    def _extract_x_ordered_blocks_from_article(self, page) -> list:
        """从article按DOM顺序提取正文和图片块。"""
        js = """
        () => {
          const article = document.querySelector("article");
          if (!article) return [];

          const blocks = [];
          const seen = new Set();
          const selectors = "[data-testid='tweetText'], [data-testid='tweetPhoto'] img, img[src*='pbs.twimg.com/media'], img[src*='ext_tw_video_thumb'], video[poster]";
          const nodes = article.querySelectorAll(selectors);

          const addText = (txt) => {
            if (!txt) return;
            const clean = txt.trim();
            if (!clean) return;
            const key = "t::" + clean;
            if (seen.has(key)) return;
            seen.add(key);
            blocks.push({type: "text", value: clean});
          };

          const addImage = (url) => {
            if (!url) return;
            const clean = url.trim();
            if (!clean || !clean.startsWith("http")) return;
            const key = "i::" + clean;
            if (seen.has(key)) return;
            seen.add(key);
            blocks.push({type: "image", value: clean});
          };

          for (const node of nodes) {
            if (node.matches("[data-testid='tweetText']")) {
              addText(node.innerText || "");
              continue;
            }
            if (node.tagName === "VIDEO") {
              addImage(node.getAttribute("poster") || "");
              continue;
            }
            if (node.tagName === "IMG") {
              addImage(node.getAttribute("src") || "");
              continue;
            }
          }
          return blocks;
        }
        """
        try:
            blocks = page.evaluate(js) or []
        except Exception:
            blocks = []

        filtered = []
        for block in blocks:
            block_type = block.get("type")
            value = (block.get("value") or "").strip()
            if not value:
                continue
            if block_type == "image":
                lower_value = value.lower()
                if "profile_images" in lower_value or "emoji" in lower_value or "abs.twimg.com" in lower_value:
                    continue
                if ("pbs.twimg.com/media/" not in lower_value and
                        "pbs.twimg.com/ext_tw_video_thumb/" not in lower_value and
                        "video.twimg.com/ext_tw_video_thumb/" not in lower_value):
                    continue
            filtered.append({"type": block_type, "value": value})
        return filtered

    def _fetch_x_post_by_syndication(self, post_id: str, original_url: str) -> Optional[Dict[str, str]]:
        """使用Twitter syndication接口匿名获取帖子内容。"""
        endpoint = f"https://cdn.syndication.twimg.com/tweet-result?id={post_id}&lang=zh-cn"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(endpoint, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self._set_last_error("X_SYNDICATION_FAILED", f"syndication获取失败: {e}", "x_syndication")
            return None

        text = (data.get("text") or "").strip()
        user_info = data.get("user") or {}
        author_name = (user_info.get("name") or "").strip()
        author_screen_name = (user_info.get("screen_name") or "").strip()
        author = author_name or (f"@{author_screen_name}" if author_screen_name else "")
        publish_time = (data.get("created_at") or "").strip()

        photos = data.get("photos") or []
        media_urls = []
        for photo in photos:
            media_url = photo.get("url") or photo.get("expanded_url")
            if media_url:
                media_urls.append(media_url)

        if not text:
            self._set_last_error("X_EMPTY_CONTENT", "syndication返回内容为空", "x_syndication")
            return None

        title = f"X帖子 @{author_screen_name}" if author_screen_name else "X帖子"
        html_content = self._build_x_html(text, author, original_url, media_urls)
        return {
            "html_content": html_content,
            "title": title,
            "description": text[:200],
            "author": author,
            "publish_time": publish_time,
        }

    def _fetch_x_post_by_playwright(self, url: str) -> Optional[Dict[str, str]]:
        """使用Playwright提取X帖子内容（syndication失败时兜底）。"""
        if not HAS_PLAYWRIGHT:
            self._set_last_error("PLAYWRIGHT_MISSING", "Playwright 未安装，无法执行X页面兜底提取", "x_playwright")
            return None

        browser = None
        context = None
        page = None
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 900},
                    extra_http_headers={'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'}
                )
                page = context.new_page()
                page.goto(url, wait_until='domcontentloaded', timeout=12000)
                try:
                    page.wait_for_load_state('networkidle', timeout=4000)
                except Exception:
                    pass

                title = (page.title() or "X帖子").strip()
                post_text = ""
                author = ""
                publish_time = ""
                media_urls = self._extract_x_media_urls_from_page(page)
                ordered_blocks = self._extract_x_ordered_blocks_from_article(page)
                article_outer_html = ""

                try:
                    text_loc = page.locator("[data-testid='tweetText']").first
                    if text_loc and text_loc.count() > 0:
                        post_text = (text_loc.inner_text() or "").strip()
                except Exception:
                    pass

                if not post_text:
                    try:
                        article_loc = page.locator("article").first
                        if article_loc and article_loc.count() > 0:
                            article_text = (article_loc.inner_text() or "").strip()
                            post_text = self._clean_x_article_text(article_text)
                            handle = article_loc.element_handle()
                            if handle:
                                article_outer_html = (handle.evaluate("el => el.outerHTML") or "").strip()
                    except Exception:
                        pass

                if not post_text:
                    try:
                        og_desc = page.locator("meta[property='og:description']").first
                        if og_desc and og_desc.count() > 0:
                            post_text = (og_desc.get_attribute("content") or "").strip()
                    except Exception:
                        pass

                if not post_text:
                    title_quote = re.search(r'on X:\s*"(.*?)"\s*/\s*X$', title, re.IGNORECASE)
                    if title_quote and title_quote.group(1).strip():
                        post_text = title_quote.group(1).strip()

                try:
                    author_loc = page.locator("[data-testid='User-Name']").first
                    if author_loc and author_loc.count() > 0:
                        author = (author_loc.inner_text() or "").strip().split("\n")[0]
                except Exception:
                    pass

                if not author:
                    title_author = re.match(r"^(.*?)\s+on X:", title, re.IGNORECASE)
                    if title_author and title_author.group(1).strip():
                        author = title_author.group(1).strip()

                try:
                    time_loc = page.locator("time").first
                    if time_loc and time_loc.count() > 0:
                        publish_time = (time_loc.get_attribute("datetime") or "").strip()
                except Exception:
                    pass

                if not post_text:
                    self._set_last_error("X_EMPTY_CONTENT", "X页面未提取到正文", "x_playwright")
                    if media_urls:
                        post_text = "（未提取到可用正文，已保留帖子图片内容）"
                    else:
                        return None

                if article_outer_html and len(article_outer_html) > 200:
                    # 优先使用原始article HTML，最大程度保留正文和图片原始相对位置
                    html_content = article_outer_html
                elif ordered_blocks:
                    if post_text:
                        normalized_post_text = post_text.strip()
                        has_same_text = any(
                            item.get("type") == "text" and (item.get("value") or "").strip() == normalized_post_text
                            for item in ordered_blocks
                        )
                        if not has_same_text:
                            ordered_blocks.insert(0, {"type": "text", "value": normalized_post_text})
                        else:
                            # 正文置顶，避免出现“图片先于正文”的阅读顺序
                            for idx, item in enumerate(ordered_blocks):
                                if item.get("type") == "text" and (item.get("value") or "").strip() == normalized_post_text:
                                    if idx > 0:
                                        ordered_blocks.insert(0, ordered_blocks.pop(idx))
                                    break

                    has_image_block = any(item.get("type") == "image" for item in ordered_blocks)
                    if media_urls and not has_image_block:
                        ordered_blocks.extend({"type": "image", "value": u} for u in media_urls)
                    html_content = self._build_x_html_from_blocks(ordered_blocks, author, url)
                else:
                    html_content = self._build_x_html(post_text, author, url, media_urls)
                return {
                    "html_content": html_content,
                    "title": title or "X帖子",
                    "description": post_text[:200],
                    "author": author,
                    "publish_time": publish_time,
                }
        except Exception as e:
            self._set_last_error("X_PLAYWRIGHT_FAILED", f"Playwright提取X帖子失败: {e}", "x_playwright")
            return None
        finally:
            for target in (page, context, browser):
                if target:
                    try:
                        target.close()
                    except Exception:
                        pass

    def _handle_x_post(self, url: str) -> Optional[Dict[str, str]]:
        """处理X/Twitter帖子链接。"""
        post_id = self._extract_x_post_id(url)
        if not post_id:
            self._set_last_error("X_INVALID_URL", "无法从URL中提取X帖子ID", "x_parser")
            return None

        result = self._fetch_x_post_by_syndication(post_id, url)
        if result:
            self.last_error = {}
            logger.info(f"使用syndication成功获取X帖子: {url}")
            return result

        result = self._fetch_x_post_by_playwright(url)
        if result:
            self.last_error = {}
            logger.info(f"使用Playwright兜底成功获取X帖子: {url}")
            return result

        if not self.last_error:
            self._set_last_error("X_FETCH_FAILED", "X帖子内容抓取失败", "x_handler")
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
