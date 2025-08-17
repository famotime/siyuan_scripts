#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整工作流程测试
测试从URL到Markdown的完整转换过程
"""

import sys
import os
import asyncio
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utilities.url_to_markdown import URLToMarkdownConverter
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_complete_workflow():
    """测试完整的工作流程"""
    
    # 测试URL列表
    test_urls = [
        'https://www.toutiao.com/article/7537272188706112043/',  # 今日头条（JavaScript重定向）
        'https://mp.weixin.qq.com/s/example',  # 微信公众号（示例，可能无效）
        'https://www.zhihu.com/question/123456789',  # 知乎（示例）
        'https://www.baidu.com',  # 百度首页（简单测试）
    ]
    
    # 创建输出目录
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    # 创建转换器
    converter = URLToMarkdownConverter(
        output_dir=str(output_dir),
        converter_lib="markdownify"
    )
    
    print("开始测试完整工作流程...")
    print("="*80)
    
    successful_conversions = []
    failed_conversions = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n[{i}/{len(test_urls)}] 测试URL: {url}")
        print("-" * 60)
        
        try:
            # 转换URL为Markdown
            result_path = await converter.convert_url_to_markdown(
                url=url,
                download_media=False  # 为了测试速度，暂时不下载媒体
            )
            
            if result_path and result_path.exists():
                file_size = result_path.stat().st_size
                print(f"✓ 转换成功!")
                print(f"  文件路径: {result_path}")
                print(f"  文件大小: {file_size:,} 字节")
                
                # 读取并显示文件内容预览
                try:
                    content = result_path.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    print(f"  总行数: {len(lines)}")
                    
                    # 显示前几行内容
                    preview_lines = lines[:10]
                    print("  内容预览:")
                    for line in preview_lines:
                        if line.strip():
                            print(f"    {line[:100]}{'...' if len(line) > 100 else ''}")
                    
                    # 检查是否包含中文
                    chinese_chars = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
                    print(f"  中文字符数: {chinese_chars}")
                    
                    # 检查是否有乱码
                    if '�' in content:
                        print("  ⚠️ 发现乱码字符")
                    else:
                        print("  ✓ 未发现乱码")
                    
                except Exception as e:
                    print(f"  ⚠️ 读取文件内容失败: {e}")
                
                successful_conversions.append((url, result_path))
                
            else:
                print("✗ 转换失败: 未生成文件")
                failed_conversions.append((url, "未生成文件"))
                
        except Exception as e:
            print(f"✗ 转换失败: {e}")
            failed_conversions.append((url, str(e)))
    
    # 输出总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"总测试数: {len(test_urls)}")
    print(f"成功转换: {len(successful_conversions)}")
    print(f"转换失败: {len(failed_conversions)}")
    
    if successful_conversions:
        print("\n✓ 成功转换的URL:")
        for url, path in successful_conversions:
            print(f"  {url} -> {path.name}")
    
    if failed_conversions:
        print("\n✗ 转换失败的URL:")
        for url, error in failed_conversions:
            print(f"  {url}: {error}")
    
    # 特殊提示
    if any('toutiao.com' in url for url, _ in failed_conversions):
        print("\n💡 今日头条链接处理提示:")
        print("今日头条使用JavaScript重定向，需要安装selenium获取真实内容:")
        print("  pip install selenium")
        print("  下载ChromeDriver: https://chromedriver.chromium.org/")
        print("  或使用: pip install webdriver-manager")

def test_encoding_scenarios():
    """测试各种编码场景"""
    print("\n" + "="*80)
    print("编码场景测试")
    print("="*80)
    
    from utilities.web_downloader import WebDownloader
    
    downloader = WebDownloader()
    
    # 测试编码检测
    test_cases = [
        ("UTF-8", "这是一个UTF-8编码的测试文本，包含中文字符。".encode('utf-8')),
        ("GBK", "这是一个GBK编码的测试文本，包含中文字符。".encode('gbk')),
        ("GB2312", "这是一个GB2312编码的测试文本。".encode('gb2312')),
        ("混合内容", b'<html><head><meta charset="utf-8"></head><body>\xe8\xbf\x99\xe6\x98\xaf\xe4\xb8\xad\xe6\x96\x87</body></html>'),
    ]
    
    for name, content in test_cases:
        print(f"\n测试 {name}:")
        try:
            detected_encoding = downloader._detect_encoding(content)
            decoded_content = content.decode(detected_encoding)
            print(f"  检测编码: {detected_encoding}")
            print(f"  解码成功: ✓")
            print(f"  内容预览: {decoded_content[:50]}...")
        except Exception as e:
            print(f"  解码失败: ✗ ({e})")

if __name__ == "__main__":
    print("开始完整工作流程测试...")
    
    # 运行异步测试
    asyncio.run(test_complete_workflow())
    
    # 运行编码测试
    test_encoding_scenarios()
    
    print("\n🎉 所有测试完成！")
