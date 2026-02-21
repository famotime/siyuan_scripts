"""
从飞书文档页面提取 markdown 内容块并保存
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("错误: 未安装 playwright，请运行: pip install playwright && python -m playwright install chromium")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    # 移除换行符、制表符等控制字符
    filename = re.sub(r'[\n\r\t]', ' ', filename)
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    # 移除零宽字符
    filename = re.sub(r'[\u200b-\u200f\ufeff]', '', filename)
    # 合并多个连续的下划线或空格
    filename = re.sub(r'[_\s]+', '_', filename)
    # 移除前后空格、点和下划线
    filename = filename.strip('. _')
    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]
    return filename or 'untitled'


def extract_markdown_blocks(page) -> List[Dict[str, str]]:
    """
    从飞书文档页面提取 markdown 内容块
    通过点击复制按钮来获取每个块的 markdown 内容
    
    返回: List[Dict] 每个字典包含 'title', 'content', 'level' 等信息
    """
    markdown_blocks = []
    
    try:
        # 等待页面加载完成
        page.wait_for_load_state('networkidle', timeout=30000)
    except Exception as e:
        logger.warning(f"等待 networkidle 超时: {e}，继续处理")
    
    # 首先尝试通过点击左侧导航栏章节，然后点击右侧复制按钮来提取内容
    logger.info("尝试通过左侧导航栏章节提取 markdown 内容...")
    try:
        # 1. 查找左侧导航栏的章节按钮/链接
        # 使用更精确的选择器来查找左侧导航栏
        nav_selectors = [
            'aside a',  # 侧边栏链接（最可能）
            'nav a',  # 导航链接
            '[class*="sidebar"] a',  # 侧边栏类
            '[class*="nav"] a',  # 导航类
            '[class*="menu"] a',  # 菜单类
            '[class*="toc"] a',  # 目录类
            '[class*="outline"] a',  # 大纲类
            '[class*="tree"] a',  # 树形结构
            '[class*="catalog"] a',  # 目录
            '[role="navigation"] a',  # 导航角色
            '[data-testid*="nav"] a',  # 导航测试ID
            '[data-testid*="sidebar"] a',  # 侧边栏测试ID
        ]
        
        # 也尝试查找按钮元素（有些导航可能是按钮）
        nav_button_selectors = [
            'aside button',
            'nav button',
            '[class*="sidebar"] button',
            '[class*="nav"] button',
        ]
        
        nav_links = []
        for selector in nav_selectors:
            try:
                links = page.query_selector_all(selector)
                if links:
                    logger.info(f"找到 {len(links)} 个可能的导航链接 (选择器: {selector})")
                    # 过滤出有文本内容的链接（可能是章节）
                    for link in links:
                        try:
                            text = link.inner_text().strip()
                            href = link.get_attribute('href') or ''
                            # 只保留有文本内容且可能是章节的链接
                            # 排除一些明显不是章节的链接（如"登录"、"帮助"等）
                            exclude_keywords = ['登录', '注册', '帮助', '设置', '退出', '返回', '首页']
                            if text and len(text) > 0 and len(text) < 200:
                                if not any(keyword in text for keyword in exclude_keywords):
                                    nav_links.append({
                                        'element': link,
                                        'text': text,
                                        'href': href,
                                        'type': 'link'
                                    })
                        except:
                            pass
            except Exception as e:
                logger.debug(f"选择器 {selector} 查询失败: {e}")
        
        # 也查找按钮类型的导航
        for selector in nav_button_selectors:
            try:
                buttons = page.query_selector_all(selector)
                if buttons:
                    logger.info(f"找到 {len(buttons)} 个可能的导航按钮 (选择器: {selector})")
                    for button in buttons:
                        try:
                            text = button.inner_text().strip()
                            if text and len(text) > 0 and len(text) < 200:
                                exclude_keywords = ['登录', '注册', '帮助', '设置', '退出', '返回', '首页']
                                if not any(keyword in text for keyword in exclude_keywords):
                                    nav_links.append({
                                        'element': button,
                                        'text': text,
                                        'href': '',
                                        'type': 'button'
                                    })
                        except:
                            pass
            except Exception as e:
                logger.debug(f"按钮选择器 {selector} 查询失败: {e}")
        
        # 去重导航链接
        seen_nav_texts = set()
        unique_nav_links = []
        for nav_item in nav_links:
            if nav_item['text'] not in seen_nav_texts:
                seen_nav_texts.add(nav_item['text'])
                unique_nav_links.append(nav_item)
        
        logger.info(f"找到 {len(unique_nav_links)} 个唯一的导航章节")
        
        if unique_nav_links:
            # 滚动到顶部
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)
            
            # 依次点击每个导航章节，然后提取对应的内容
            for idx, nav_item in enumerate(unique_nav_links):
                try:
                    nav_text = nav_item['text']
                    nav_element = nav_item['element']
                    
                    logger.info(f"处理章节 {idx + 1}/{len(unique_nav_links)}: {nav_text[:50]}")
                    
                    # 点击导航链接
                    try:
                        # 检查元素是否还在DOM中
                        try:
                            is_attached = nav_element.evaluate("el => el.isConnected")
                            if not is_attached:
                                logger.debug(f"导航章节 '{nav_text}' 已不在DOM中，跳过")
                                continue
                        except:
                            pass
                        
                        nav_element.scroll_into_view_if_needed()
                        page.wait_for_timeout(200)
                        nav_element.click(timeout=3000)
                        page.wait_for_timeout(1500)  # 等待右侧内容加载
                    except Exception as click_error:
                        logger.warning(f"点击导航章节 '{nav_text}' 失败: {click_error}")
                        continue
                    
                    # 等待内容加载完成（增加等待时间）
                    page.wait_for_timeout(1500)
                    
                    # 尝试等待内容区域更新
                    try:
                        # 等待页面稳定
                        page.wait_for_load_state('networkidle', timeout=5000)
                    except:
                        pass
                    
                    # 查找右侧对应的复制按钮（重新查找，因为内容可能已更新）
                    # 使用更广泛的选择器
                    copy_button_selectors = [
                        'button[title*="复制"]',
                        'button[aria-label*="复制"]',
                        'button[title*="Copy"]',
                        'button[aria-label*="Copy"]',
                        '[class*="copy"]',
                        '[class*="Copy"]',
                        '[class*="COPY"]',
                        'button:has-text("复制")',
                        '[data-testid*="copy"]',
                        '[data-testid*="Copy"]',
                        'svg[class*="copy"]',
                        'button svg[class*="copy"]',
                        '[role="button"][class*="copy"]',
                        'div[class*="copy"][role="button"]',
                    ]
                    
                    copy_button = None
                    max_retries = 5  # 增加重试次数
                    for retry in range(max_retries):
                        for selector in copy_button_selectors:
                            try:
                                buttons = page.query_selector_all(selector)
                                if buttons:
                                    # 选择第一个可见的复制按钮
                                    for btn in buttons:
                                        try:
                                            # 检查按钮是否可见且可点击
                                            is_visible = btn.is_visible()
                                            if is_visible:
                                                # 检查按钮是否在主要内容区域（排除导航栏中的）
                                                bounding_box = btn.bounding_box()
                                                if bounding_box:
                                                    # 按钮应该在页面右侧（x坐标大于页面宽度的20%）
                                                    page_width = page.evaluate("window.innerWidth")
                                                    if bounding_box['x'] > page_width * 0.2:
                                                        copy_button = btn
                                                        break
                                        except:
                                            pass
                                    if copy_button:
                                        break
                            except:
                                pass
                        
                        if copy_button:
                            break
                        
                        # 如果没找到，等待一下再重试
                        if retry < max_retries - 1:
                            page.wait_for_timeout(800)
                            # 尝试滚动一下页面，可能内容需要滚动才能显示
                            try:
                                page.evaluate("window.scrollBy(0, 200)")
                                page.wait_for_timeout(300)
                            except:
                                pass
                    
                    if not copy_button:
                        logger.warning(f"⚠️ 未找到章节 '{nav_text}' 的复制按钮（已重试 {max_retries} 次）")
                        # 尝试使用 JavaScript 直接查找复制按钮
                        try:
                            copy_button_info = page.evaluate("""
                                () => {
                                    // 查找所有可能的复制按钮
                                    const selectors = [
                                        'button[title*="复制"]',
                                        'button[aria-label*="复制"]',
                                        '[class*="copy"]',
                                        '[class*="Copy"]',
                                        'button:has(svg[class*="copy"])',
                                        '[data-testid*="copy"]',
                                    ];
                                    
                                    for (const selector of selectors) {
                                        const elements = document.querySelectorAll(selector);
                                        for (const el of elements) {
                                            // 检查是否可见且在主要内容区域
                                            const rect = el.getBoundingClientRect();
                                            const pageWidth = window.innerWidth;
                                            if (rect.width > 0 && rect.height > 0 && 
                                                rect.x > pageWidth * 0.2 && 
                                                window.getComputedStyle(el).display !== 'none') {
                                                return {
                                                    found: true,
                                                    selector: selector,
                                                    x: rect.x,
                                                    y: rect.y
                                                };
                                            }
                                        }
                                    }
                                    return { found: false };
                                }
                            """)
                            
                            if copy_button_info and copy_button_info.get('found'):
                                logger.info(f"通过 JavaScript 找到复制按钮，位置: ({copy_button_info.get('x')}, {copy_button_info.get('y')})")
                                # 尝试使用坐标点击
                                try:
                                    page.mouse.click(copy_button_info['x'] + 10, copy_button_info['y'] + 10)
                                    page.wait_for_timeout(800)
                                    copy_button = True  # 标记为已点击
                                except:
                                    pass
                        except Exception as js_error:
                            logger.debug(f"JavaScript 查找复制按钮失败: {js_error}")
                        
                        # 如果还是没找到，尝试查找所有复制按钮
                        if not copy_button:
                            try:
                                all_copy_buttons = page.query_selector_all('[class*="copy"], button[title*="复制"], button[aria-label*="复制"]')
                                logger.info(f"页面上共有 {len(all_copy_buttons)} 个复制相关元素")
                                # 如果找到了按钮，尝试使用第一个
                                if len(all_copy_buttons) > 0:
                                    logger.info(f"尝试使用第一个复制按钮...")
                                    for btn in all_copy_buttons:
                                        try:
                                            box = btn.bounding_box()
                                            if box and box['x'] > page.evaluate("window.innerWidth") * 0.2:
                                                copy_button = btn
                                                break
                                        except:
                                            pass
                            except:
                                pass
                        
                        if not copy_button:
                            logger.warning(f"跳过章节 '{nav_text}'，无法找到复制按钮")
                            continue
                    
                    # 如果 copy_button 是 True（表示已通过坐标点击），跳过滚动和点击步骤
                    if copy_button is True:
                        # 已经通过坐标点击了，直接读取剪贴板
                        pass
                    else:
                        # 滚动到复制按钮位置
                        try:
                            copy_button.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                        except:
                            pass
                        
                        # 点击复制按钮
                        try:
                            # 尝试多种点击方式
                            try:
                                copy_button.click(timeout=2000)
                            except:
                                # 如果普通点击失败，尝试使用 JavaScript 点击
                                try:
                                    copy_button.evaluate("el => el.click()")
                                except:
                                    # 如果还是失败，尝试使用坐标点击
                                    try:
                                        box = copy_button.bounding_box()
                                        if box:
                                            page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                    except:
                                        logger.warning(f"所有点击方式都失败 (章节: {nav_text})")
                                        continue
                            
                            page.wait_for_timeout(800)  # 等待复制操作完成
                        except Exception as click_error:
                            logger.warning(f"点击复制按钮失败 (章节: {nav_text}): {click_error}")
                            continue
                    
                    # 使用导航文本作为标题
                    title = nav_text
                    
                    # 从剪贴板读取内容
                    try:
                        # 首先尝试使用 pyperclip（更可靠）
                        clipboard_content = None
                        try:
                            import pyperclip
                            clipboard_content = pyperclip.paste()
                            logger.debug(f"使用 pyperclip 读取剪贴板成功")
                        except Exception as pyperclip_error:
                            logger.debug(f"pyperclip 读取失败: {pyperclip_error}，尝试浏览器 API")
                            # 使用 Playwright 的剪贴板 API 作为备用
                            try:
                                clipboard_content = page.evaluate("""
                                    async () => {
                                        try {
                                            const text = await navigator.clipboard.readText();
                                            return text;
                                        } catch (e) {
                                            console.error('Clipboard read error:', e);
                                            return '';
                                        }
                                    }
                                """)
                            except Exception as browser_clipboard_error:
                                logger.debug(f"浏览器剪贴板 API 也失败: {browser_clipboard_error}")
                                clipboard_content = None
                        
                        if clipboard_content and clipboard_content.strip():
                            # 处理 HTML 内容，提取纯文本
                            content = clipboard_content.strip()
                            
                            # 如果内容包含 HTML，尝试提取文本
                            if '<' in content and '>' in content:
                                try:
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(content, 'html.parser')
                                    # 提取所有文本
                                    content = soup.get_text(separator='\n', strip=True)
                                except:
                                    # 如果 BeautifulSoup 不可用，使用简单的正则表达式
                                    import re
                                    # 移除 HTML 标签
                                    content = re.sub(r'<[^>]+>', '', content)
                                    # 清理多余的空白
                                    content = re.sub(r'\n\s*\n', '\n\n', content)
                            
                            # 尝试从内容中提取标题
                            lines = [l.strip() for l in content.split('\n') if l.strip()]
                            
                            # 查找标题（markdown 标题、编号标题、或第一行）
                            extracted_title = None
                            for i, line in enumerate(lines[:10]):  # 只检查前10行
                                # 检查是否是 markdown 标题
                                if line.startswith('#'):
                                    extracted_title = line.lstrip('#').strip()
                                    content = '\n'.join(lines[i+1:]).strip()
                                    break
                                # 检查是否是编号标题（如 "3.1.1 论文大师"）
                                import re
                                if re.match(r'^\s*\d+(\.\d+)+\s+\S+', line):
                                    extracted_title = line.strip()
                                    content = '\n'.join(lines[i+1:]).strip()
                                    break
                                # 检查是否是注释格式的标题（如 "// Author：云舒" 后面的标题）
                                if line.startswith('//') and 'Author' in line:
                                    # 继续查找下一行的标题
                                    if i + 1 < len(lines):
                                        next_line = lines[i + 1]
                                        if next_line.startswith('#'):
                                            extracted_title = next_line.lstrip('#').strip()
                                            content = '\n'.join(lines[i+2:]).strip()
                                            break
                            
                            # 如果没有找到标题，使用第一行（如果较短）
                            if not extracted_title and lines:
                                first_line = lines[0]
                                if len(first_line) < 100 and not first_line.startswith('//'):
                                    extracted_title = first_line
                                    content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else content
                            
                            # 更新标题
                            if extracted_title:
                                title = extracted_title
                            
                            # 检查内容是否与已有内容重复（使用更严格的去重）
                            content_preview = content[:1000] if len(content) > 1000 else content  # 使用前1000字符
                            content_hash = hash(content_preview)
                            is_duplicate = False
                            for existing_block in markdown_blocks:
                                existing_content = existing_block['content'] if existing_block['content'] else ''
                                existing_preview = existing_content[:1000] if len(existing_content) > 1000 else existing_content
                                existing_hash = hash(existing_preview)
                                # 如果hash相同，或者内容相似度很高（前200字符相同）
                                if content_hash == existing_hash or \
                                   (content_preview[:200] == existing_preview[:200] and len(content_preview) > 100):
                                    is_duplicate = True
                                    logger.info(f"⏭️ 章节 '{nav_text}' 的内容与已有内容重复，跳过")
                                    break
                            
                            if not is_duplicate:
                                markdown_blocks.append({
                                    'title': title,
                                    'content': content,
                                    'level': title.count('.') + 1 if '.' in title else 1,
                                    'index': len(markdown_blocks)
                                })
                                logger.info(f"✅ 成功提取章节 {idx + 1}/{len(unique_nav_links)}: {title[:50]} (内容长度: {len(content)})")
                            else:
                                logger.info(f"⏭️ 跳过重复章节: {title[:50]}")
                        else:
                            logger.warning(f"⚠️ 章节 '{nav_text}' 的复制内容为空")
                    except Exception as e:
                        logger.warning(f"读取剪贴板内容失败 (章节: {nav_text}): {e}")
                
                except Exception as e:
                    logger.warning(f"处理章节 '{nav_text}' 时出错: {e}")
                    continue
            
            if markdown_blocks:
                logger.info(f"通过复制按钮成功提取到 {len(markdown_blocks)} 个内容块")
                return markdown_blocks
        
    except Exception as e:
        logger.warning(f"通过复制按钮提取内容时出错: {e}，将使用备用方法")
    
    # 如果复制按钮方法失败，使用原来的方法
    logger.info("使用备用方法提取内容...")
    
    # 滚动页面以加载所有内容
    logger.info("开始滚动页面以加载所有内容...")
    try:
        # 尝试点击所有可展开的元素（如折叠的内容、链接等）
        logger.info("尝试展开所有可展开的内容...")
        try:
            # 查找并点击所有可能的展开按钮/链接
            expand_selectors = [
                'a[href*="#"]',  # 锚点链接
                '[class*="expand"]',  # 展开按钮
                '[class*="toggle"]',  # 切换按钮
                '[class*="collapse"]',  # 折叠按钮
                'button[aria-expanded="false"]',  # 未展开的按钮
            ]
            
            for selector in expand_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for elem in elements[:20]:  # 限制数量避免过多点击
                        try:
                            elem.click(timeout=1000)
                            page.wait_for_timeout(300)  # 等待内容加载
                        except:
                            pass
                except:
                    pass
        except Exception as e:
            logger.debug(f"展开内容时出错: {e}")
        
        # 获取页面高度
        page_height = page.evaluate("document.body.scrollHeight")
        viewport_height = page.evaluate("window.innerHeight")
        
        # 逐步滚动到底部
        scroll_step = viewport_height * 0.8
        current_position = 0
        max_scrolls = 50  # 防止无限滚动
        scroll_count = 0
        
        while current_position < page_height and scroll_count < max_scrolls:
            page.evaluate(f"window.scrollTo(0, {current_position})")
            page.wait_for_timeout(500)  # 等待内容加载
            
            # 更新页面高度（可能因为动态加载而增加）
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height > page_height:
                page_height = new_height
            
            current_position += scroll_step
            scroll_count += 1
        
        # 滚动回顶部
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
        
        logger.info(f"页面滚动完成，总高度: {page_height}px")
    except Exception as e:
        logger.warning(f"滚动页面时出错: {e}，继续处理")
    
    # 额外等待，确保动态内容加载
    page.wait_for_timeout(2000)
    
    try:
        # 使用 JavaScript 提取飞书文档的结构化内容
        # 飞书文档通常使用特定的数据结构
        page_content = page.evaluate("""
        () => {
            const blocks = [];
            const seenTexts = new Set();
            
            // 辅助函数：检查文本是否有意义
            function isMeaningfulText(text) {
                if (!text || text.trim().length < 1) return false;
                // 允许单个 emoji 或符号，但需要配合其他内容
                const textOnly = text.replace(/[\\s\\u200b-\\u200f\\ufeff\\u2028\\u2029]/g, '');
                // 如果只有 emoji 或符号，允许但标记为需要配合内容
                if (textOnly.length < 2) {
                    // 检查是否包含中文字符或英文单词
                    const hasChinese = /[\\u4e00-\\u9fa5]/.test(text);
                    const hasEnglish = /[a-zA-Z]{2,}/.test(text);
                    return hasChinese || hasEnglish;
                }
                return true;
            }
            
            // 辅助函数：清理文本
            function cleanText(text) {
                if (!text) return '';
                return text.replace(/[\\u200b-\\u200f\\ufeff]/g, '').trim();
            }
            
            // 尝试多种方式查找内容
            // 1. 查找所有 data-block-id 元素（飞书文档块）
            const blockElements = document.querySelectorAll('[data-block-id]');
            
            if (blockElements.length > 0) {
                blockElements.forEach((block, idx) => {
                    try {
                        const text = block.innerText || block.textContent || '';
                        const trimmedText = cleanText(text);
                        
                        // 放宽过滤条件：只要不是完全空白就处理
                        if (!trimmedText || trimmedText.length < 1) return;
                        
                        // 去重：使用更长的文本片段来避免误判
                        const textKey = trimmedText.substring(0, 100);
                        if (seenTexts.has(textKey)) return;
                        seenTexts.add(textKey);
                        
                        // 尝试识别标题
                        const heading = block.querySelector('h1, h2, h3, h4, h5, h6, [class*="heading"], [class*="title"]');
                        let title = '';
                        let content = trimmedText;
                        let level = 1;
                        
                        if (heading) {
                            title = cleanText(heading.innerText || heading.textContent || '');
                            const tagName = heading.tagName.toLowerCase();
                            if (tagName.startsWith('h')) {
                                level = parseInt(tagName[1]) || 1;
                            }
                            // 从内容中移除标题
                            content = cleanText(trimmedText.replace(title, ''));
                        } else {
                            // 如果没有标题，尝试识别第一行是否为标题
                            const lines = trimmedText.split('\\n').filter(l => l.trim());
                            if (lines.length > 1) {
                                // 如果第一行较短，可能是标题
                                const firstLine = cleanText(lines[0]);
                                if (firstLine.length < 50 && firstLine.length > 0) {
                                    title = firstLine;
                                    content = cleanText(lines.slice(1).join('\\n'));
                                } else {
                                    // 第一行太长，整个作为内容
                                    title = firstLine.substring(0, 50);
                                    content = cleanText(lines.join('\\n'));
                                }
                            } else if (lines.length === 1) {
                                const singleLine = cleanText(lines[0]);
                                // 如果只有一行且较短，作为标题
                                if (singleLine.length < 100) {
                                    title = singleLine;
                                    content = '';
                                } else {
                                    title = singleLine.substring(0, 50);
                                    content = singleLine;
                                }
                            }
                            
                            if (!title) {
                                title = `内容块_${idx + 1}`;
                            }
                        }
                        
                        // 识别标题模式：包含编号的内容（如 "3.1.1 论文大师"）
                        const numberPattern = /^\\d+(\\.\\d+)*\\s+/;
                        const hasNumberPrefix = numberPattern.test(trimmedText);
                        
                        // 如果包含编号，尝试提取标题
                        if (hasNumberPrefix && !title) {
                            const lines = trimmedText.split('\\n').filter(l => l.trim());
                            if (lines.length > 0) {
                                const firstLine = cleanText(lines[0]);
                                // 如果第一行包含编号且较短，作为标题
                                if (numberPattern.test(firstLine) && firstLine.length < 150) {
                                    title = firstLine;
                                    content = cleanText(lines.slice(1).join('\\n'));
                                }
                            }
                        }
                        
                        // 保存所有有内容的块（放宽条件）
                        if (trimmedText.length > 0) {
                            // 如果标题只是 emoji/符号但内容有意义，将内容的一部分作为标题
                            if (!title || title.length < 3) {
                                const contentLines = content.split('\\n').filter(l => l.trim());
                                if (contentLines.length > 0) {
                                    const firstLine = cleanText(contentLines[0]);
                                    // 如果第一行看起来像标题（包含编号或较短）
                                    if ((numberPattern.test(firstLine) || firstLine.length < 80) && firstLine.length > 2) {
                                        title = firstLine;
                                        content = cleanText(contentLines.slice(1).join('\\n'));
                                    } else if (!title) {
                                        title = firstLine.substring(0, 50);
                                    }
                                }
                            }
                            
                            // 确保有标题
                            if (!title || title.length < 1) {
                                title = `内容块_${idx + 1}`;
                            }
                            
                            blocks.push({
                                title: cleanText(title) || `内容块_${idx + 1}`,
                                content: cleanText(content) || trimmedText,
                                level: level,
                                index: idx
                            });
                        }
                    } catch (e) {
                        console.error('处理块时出错:', e);
                    }
                });
            }
            
            // 2. 如果没找到块，尝试按标题分割
            if (blocks.length === 0) {
                const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                if (headings.length > 0) {
                    headings.forEach((heading, idx) => {
                        const title = cleanText(heading.innerText || heading.textContent || '');
                        if (!isMeaningfulText(title)) return;
                        
                        const tagName = heading.tagName.toLowerCase();
                        const level = parseInt(tagName[1]) || 1;
                        
                        // 获取标题后的内容（直到下一个同级或更高级标题）
                        let content = '';
                        let nextNode = heading.nextElementSibling;
                        while (nextNode) {
                            const nextTag = nextNode.tagName.toLowerCase();
                            if (nextTag.startsWith('h')) {
                                const nextLevel = parseInt(nextTag[1]) || 1;
                                if (nextLevel <= level) {
                                    break;
                                }
                            }
                            const nodeText = cleanText(nextNode.innerText || nextNode.textContent || '');
                            if (isMeaningfulText(nodeText)) {
                                content += nodeText + '\\n\\n';
                            }
                            nextNode = nextNode.nextElementSibling;
                        }
                        
                        content = cleanText(content);
                        if (title && (content.length > 5 || title.length > 5)) {
                            blocks.push({
                                title: title,
                                content: content,
                                level: level,
                                index: idx
                            });
                        }
                    });
                }
            }
            
            // 3. 如果前面没有找到足够的内容，尝试从整个文档中提取
            // 获取所有文本内容，按编号模式分割
            if (blocks.length < 5) {
                const bodyText = document.body.innerText || document.body.textContent || '';
                const lines = bodyText.split('\\n').filter(l => l.trim());
                
                // 编号模式：如 "3.1.1 论文大师"
                const numberPattern = /^\\s*\\d+(\\.\\d+)+\\s+[^\\s]+/;
                let currentBlock = null;
                
                lines.forEach((line, lineIdx) => {
                    const trimmedLine = cleanText(line);
                    if (!trimmedLine) return;
                    
                    // 检查是否是编号标题
                    if (numberPattern.test(trimmedLine)) {
                        // 保存前一个块
                        if (currentBlock && currentBlock.content.trim().length > 0) {
                            const blockKey = currentBlock.title.substring(0, 100);
                            if (!seenTexts.has(blockKey)) {
                                seenTexts.add(blockKey);
                                blocks.push(currentBlock);
                            }
                        }
                        
                        // 开始新块
                        const level = (trimmedLine.match(/\\./g) || []).length + 1;
                        currentBlock = {
                            title: trimmedLine,
                            content: '',
                            level: level,
                            index: blocks.length
                        };
                    } else if (currentBlock) {
                        // 添加到当前块
                        currentBlock.content += trimmedLine + '\\n';
                    }
                });
                
                // 保存最后一个块
                if (currentBlock && currentBlock.content.trim().length > 0) {
                    const blockKey = currentBlock.title.substring(0, 100);
                    if (!seenTexts.has(blockKey)) {
                        seenTexts.add(blockKey);
                        blocks.push(currentBlock);
                    }
                }
            }
            
            return blocks;
        }
        """)
        
        # 无论 JavaScript 提取结果如何，都尝试使用备用方法获取完整文本
        logger.info("尝试使用备用方法获取完整页面文本...")
        page_text = page.inner_text('body')
        
        # 保存完整页面文本用于调试
        try:
            debug_dir = Path('./download/feishu_doc')
            debug_path = debug_dir / '_full_page_text.txt'
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            debug_path.write_text(page_text, encoding='utf-8')
            logger.info(f"已保存完整页面文本到: {debug_path}")
        except Exception as e:
            logger.debug(f"保存调试文本失败: {e}")
        
        if page_text.strip():
            # 检查是否包含编号模式的内容
            import re
            number_pattern = re.compile(r'^\s*\d+(\.\d+)+\s+\S+', re.MULTILINE)
            has_numbered_content = number_pattern.search(page_text)
            
            if has_numbered_content:
                logger.info("在页面文本中发现编号模式，使用备用方法提取...")
                # 使用备用方法提取
                markdown_blocks = []
            elif page_content and len(page_content) > 0:
                logger.info(f"使用 JavaScript 提取结果: {len(page_content)} 个内容块")
                markdown_blocks = page_content
            else:
                logger.info("使用备用方法提取...")
                markdown_blocks = []
        else:
            if page_content and len(page_content) > 0:
                logger.info(f"通过 JavaScript 提取到 {len(page_content)} 个内容块")
                markdown_blocks = page_content
            else:
                markdown_blocks = []
        
        # 如果 markdown_blocks 为空，使用备用方法
        if not markdown_blocks:
            # 备用方法：直接获取页面文本并按结构分割
            if page_text and page_text.strip():
                # 按空行和可能的标题模式分割
                lines = [l.strip() for l in page_text.split('\n') if l.strip()]
                current_block = {'title': '', 'content': [], 'level': 1, 'index': 0}
                
                # 编号模式：如 "3.1.1 论文大师"
                import re
                number_pattern = re.compile(r'^\s*\d+(\.\d+)+\s+\S+')
                
                for line in lines:
                    # 检查是否是编号标题
                    if number_pattern.match(line):
                        # 保存前一个块
                        if current_block['title'] or current_block['content']:
                            markdown_blocks.append({
                                'title': current_block['title'] or f"内容块_{len(markdown_blocks) + 1}",
                                'content': '\n'.join(current_block['content']).strip(),
                                'level': current_block['level'],
                                'index': len(markdown_blocks)
                            })
                        # 开始新块
                        level = line.count('.') + 1
                        current_block = {'title': line, 'content': [], 'level': level, 'index': len(markdown_blocks)}
                    # 检查是否是其他类型的标题
                    elif len(line) < 100 and (line.startswith('#') or 
                                  any(keyword in line for keyword in ['、', '。', '：', ':', '.', '第', '一', '二', '三'])):
                        if current_block['content']:
                            # 保存当前块
                            if current_block['title'] or current_block['content']:
                                markdown_blocks.append({
                                    'title': current_block['title'] or f"内容块_{len(markdown_blocks) + 1}",
                                    'content': '\n'.join(current_block['content']).strip(),
                                    'level': current_block['level'],
                                    'index': len(markdown_blocks)
                                })
                            # 开始新块
                            current_block = {'title': line, 'content': [], 'level': 1, 'index': len(markdown_blocks)}
                        else:
                            current_block['title'] = line
                    else:
                        current_block['content'].append(line)
                
                # 保存最后一个块
                if current_block['title'] or current_block['content']:
                    markdown_blocks.append({
                        'title': current_block['title'] or f"内容块_{len(markdown_blocks) + 1}",
                        'content': '\n'.join(current_block['content']).strip(),
                        'level': current_block['level'],
                        'index': len(markdown_blocks)
                    })
    
    except Exception as e:
        logger.error(f"提取内容时出错: {e}", exc_info=True)
    
    # 去重和清理
    seen_titles = set()
    seen_content_hashes = set()
    unique_blocks = []
    for block in markdown_blocks:
        title = block.get('title', '').strip()
        content = block.get('content', '').strip()
        
        # 跳过完全空的内容
        if not content and not title:
            continue
        
        # 如果只有标题没有内容，且标题很短，跳过
        if not content and len(title) < 3:
            continue
        
        # 使用内容hash去重（更准确）
        content_hash = hash(content[:1000])  # 使用前1000字符的hash
        
        if content_hash in seen_content_hashes:
            logger.debug(f"跳过重复内容块: {title[:50]}")
            continue
        
        seen_content_hashes.add(content_hash)
        if title:
            seen_titles.add(title)
        
        unique_blocks.append(block)
    
    # 按索引排序
    unique_blocks.sort(key=lambda x: x.get('index', 0))
    
    logger.info(f"最终提取到 {len(unique_blocks)} 个唯一内容块")
    return unique_blocks


def save_markdown_blocks(blocks: List[Dict[str, str]], output_dir: Path, base_name: str = 'feishu_doc'):
    """保存 markdown 块到文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not blocks:
        logger.warning("没有找到任何内容块")
        return
    
    logger.info(f"找到 {len(blocks)} 个内容块，开始保存...")
    
    saved_files = []
    for block in blocks:
        title = block['title']
        content = block['content']
        index = block.get('index', 0)
        level = block.get('level', 1)
        
        # 生成文件名
        safe_title = sanitize_filename(title)
        filename = f"{index + 1:02d}_{safe_title}.md"
        file_path = output_dir / filename
        
        # 构建 markdown 内容
        markdown_content = f"# {title}\n\n{content}\n"
        
        # 保存文件
        try:
            file_path.write_text(markdown_content, encoding='utf-8')
            logger.info(f"已保存: {file_path.name}")
            saved_files.append(file_path)
        except Exception as e:
            logger.error(f"保存文件 {filename} 失败: {e}")
    
    # 创建一个索引文件
    index_path = output_dir / 'README.md'
    index_content = f"# {base_name}\n\n"
    index_content += f"本文档包含 {len(blocks)} 个内容块：\n\n"
    
    for block in blocks:
        title = block['title']
        index = block.get('index', 0)
        safe_title = sanitize_filename(title)
        filename = f"{index + 1:02d}_{safe_title}.md"
        index_content += f"{index + 1}. [{title}]({filename})\n"
    
    try:
        index_path.write_text(index_content, encoding='utf-8')
        logger.info(f"已创建索引文件: {index_path.name}")
    except Exception as e:
        logger.error(f"创建索引文件失败: {e}")
    
    return saved_files


def extract_feishu_markdown(url: str, output_dir: Optional[Path] = None):
    """
    从飞书文档 URL 提取 markdown 内容并保存
    
    Args:
        url: 飞书文档 URL
        output_dir: 输出目录，默认为 ./download/feishu_doc
    """
    if not HAS_PLAYWRIGHT:
        logger.error("Playwright 未安装，无法执行")
        return
    
    if output_dir is None:
        output_dir = Path('./download/feishu_doc')
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"开始访问飞书文档: {url}")
    logger.info(f"输出目录: {output_dir}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            
            # 创建浏览器上下文，模拟真实浏览器
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            
            page = context.new_page()
            
            try:
                logger.info("正在加载页面...")
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # 等待页面内容加载
                logger.info("等待页面内容加载...")
                try:
                    page.wait_for_load_state('networkidle', timeout=30000)
                except Exception:
                    logger.warning("networkidle 等待超时，继续处理")
                
                # 额外等待，确保动态内容加载
                page.wait_for_timeout(3000)
                
                # 提取 markdown 块
                logger.info("开始提取内容...")
                blocks = extract_markdown_blocks(page)
                
                if not blocks:
                    logger.warning("未找到任何内容块，尝试保存页面 HTML 以供调试")
                    html_content = page.content()
                    debug_path = output_dir / '_debug_page.html'
                    debug_path.write_text(html_content, encoding='utf-8')
                    logger.info(f"已保存调试 HTML: {debug_path}")
                    
                    # 也保存页面文本
                    page_text = page.inner_text('body')
                    text_path = output_dir / '_debug_page_text.txt'
                    text_path.write_text(page_text, encoding='utf-8')
                    logger.info(f"已保存页面文本: {text_path}")
                
                # 保存 markdown 块
                base_name = 'feishu_doc'
                saved_files = save_markdown_blocks(blocks, output_dir, base_name)
                
                logger.info(f"✅ 完成！共保存 {len(saved_files)} 个文件到 {output_dir}")
                
            except PlaywrightTimeoutError as e:
                logger.error(f"页面加载超时: {e}")
            except Exception as e:
                logger.error(f"处理页面时出错: {e}", exc_info=True)
            finally:
                browser.close()
    
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)


if __name__ == '__main__':
    url = 'https://t16jzwqrzjx.feishu.cn/wiki/NABlwmL9si2vhWkqtgJcbTxknbe'
    extract_feishu_markdown(url)

