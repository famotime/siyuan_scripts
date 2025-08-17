#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试今日头条链接修复效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utilities.web_downloader import WebDownloader
from utilities.html_converter import HTMLConverter
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_toutiao_fix():
    """测试今日头条链接修复效果"""
    
    # 测试URL
    test_urls = [
        'https://www.toutiao.com/article/7537272188706112043/',
        'https://www.baidu.com',  # 对比测试
        'https://www.zhihu.com'   # 对比测试
    ]
    
    downloader = WebDownloader()
    converter = HTMLConverter()
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"测试URL: {url}")
        print('='*60)
        
        try:
            # 获取网页内容
            html_content = downloader.fetch_webpage(url)
            
            if html_content:
                print(f"✓ 成功获取内容，长度: {len(html_content)} 字符")
                
                # 检查中文字符
                chinese_chars = sum(1 for char in html_content[:2000] if '\u4e00' <= char <= '\u9fff')
                print(f"  前2000字符中的中文字符数: {chinese_chars}")
                
                # 检查是否有乱码
                if '�' in html_content:
                    print("  ⚠️ 发现乱码字符")
                else:
                    print("  ✓ 未发现乱码字符")
                
                # 提取页面信息
                page_info = downloader.extract_page_info(html_content)
                print(f"  标题: {page_info['title'][:100]}")
                print(f"  描述: {page_info['description'][:100] if page_info['description'] else '无'}")
                
                # 显示内容预览
                preview = html_content[:500].replace('\n', ' ').replace('\r', ' ')
                print(f"  内容预览: {preview}...")
                
                # 检查是否是JavaScript重定向页面
                if downloader._is_js_redirect_page(html_content):
                    print("  ⚠️ 检测到JavaScript重定向页面")
                    print("  建议: 该网站可能需要使用selenium或其他方式获取真实内容")
                else:
                    print("  ✓ 正常的HTML页面")
                    
                    # 尝试转换为Markdown
                    try:
                        clean_html = converter.clean_html_for_conversion(html_content)
                        markdown = converter.convert_html_to_markdown(clean_html)
                        print(f"  ✓ 成功转换为Markdown，长度: {len(markdown)} 字符")
                        
                        # 显示Markdown预览
                        md_preview = markdown[:300].replace('\n', ' ')
                        print(f"  Markdown预览: {md_preview}...")
                        
                    except Exception as e:
                        print(f"  ✗ Markdown转换失败: {e}")
                
            else:
                print("✗ 获取内容失败")
                
        except Exception as e:
            print(f"✗ 测试失败: {e}")

def test_encoding_detection():
    """测试编码检测功能"""
    print(f"\n{'='*60}")
    print("测试编码检测功能")
    print('='*60)
    
    downloader = WebDownloader()
    
    # 测试不同编码的内容
    test_cases = [
        ("UTF-8中文", "这是UTF-8编码的中文内容".encode('utf-8')),
        ("GBK中文", "这是GBK编码的中文内容".encode('gbk')),
        ("GB2312中文", "这是GB2312编码的中文内容".encode('gb2312')),
    ]
    
    for name, content in test_cases:
        detected = downloader._detect_encoding(content)
        try:
            decoded = content.decode(detected)
            print(f"  {name}: 检测编码={detected}, 解码成功=✓")
            print(f"    内容: {decoded}")
        except Exception as e:
            print(f"  {name}: 检测编码={detected}, 解码失败=✗ ({e})")

if __name__ == "__main__":
    print("开始测试今日头条链接修复效果...")
    test_toutiao_fix()
    test_encoding_detection()
    print("\n测试完成！")
