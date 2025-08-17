#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试今日头条链接的编码问题
"""

import requests
import chardet
from bs4 import BeautifulSoup
import gzip
import brotli
import io

def test_toutiao_encoding():
    """测试今日头条链接的编码问题"""
    url = 'https://www.toutiao.com/article/7537272188706112043/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        print(f"正在请求: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应编码: {response.encoding}")
        print(f"Content-Type: {response.headers.get('Content-Type', '未知')}")
        print(f"Content-Encoding: {response.headers.get('Content-Encoding', '未知')}")
        print(f"内容长度: {len(response.content)} 字节")

        # 检查是否是压缩内容
        content_encoding = response.headers.get('Content-Encoding', '').lower()
        raw_content = response.content

        if content_encoding == 'gzip':
            print("检测到gzip压缩，正在解压...")
            try:
                raw_content = gzip.decompress(response.content)
                print(f"解压后长度: {len(raw_content)} 字节")
            except Exception as e:
                print(f"gzip解压失败: {e}")
        elif content_encoding == 'br':
            print("检测到Brotli压缩，正在解压...")
            try:
                raw_content = brotli.decompress(response.content)
                print(f"解压后长度: {len(raw_content)} 字节")
            except Exception as e:
                print(f"Brotli解压失败: {e}")
        elif content_encoding == 'deflate':
            print("检测到deflate压缩，正在解压...")
            try:
                import zlib
                raw_content = zlib.decompress(response.content)
                print(f"解压后长度: {len(raw_content)} 字节")
            except Exception as e:
                print(f"deflate解压失败: {e}")

        # 使用chardet检测编码
        detected = chardet.detect(raw_content)
        print(f"chardet检测编码: {detected}")
        
        # 尝试不同编码方式
        print("\n=== 尝试不同编码 ===")
        encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']

        for encoding in encodings_to_try:
            try:
                decoded_content = raw_content.decode(encoding)
                print(f"{encoding}: 成功解码，长度 {len(decoded_content)}")

                # 检查是否包含中文
                chinese_chars = sum(1 for char in decoded_content[:1000] if '\u4e00' <= char <= '\u9fff')
                print(f"  前1000字符中的中文字符数: {chinese_chars}")

                # 提取标题
                soup = BeautifulSoup(decoded_content, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                    print(f"  标题: {title[:100]}")

                print(f"  内容预览: {decoded_content[:200]}")
                print()

            except Exception as e:
                print(f"{encoding}: 解码失败 - {e}")
        
        # 测试requests自动检测的编码
        print("=== requests自动检测编码 ===")
        print(f"response.text长度: {len(response.text)}")
        print(f"response.text预览: {response.text[:200]}")
        
        # 检查是否有乱码特征
        if '�' in response.text:
            print("⚠️ 发现乱码字符 '�'")
        
        # 尝试强制设置编码
        print("\n=== 强制设置编码测试 ===")
        for encoding in ['utf-8', 'gbk']:
            response.encoding = encoding
            print(f"强制设置为 {encoding}:")
            print(f"  文本长度: {len(response.text)}")
            print(f"  预览: {response.text[:200]}")
            if '�' in response.text:
                print(f"  ⚠️ {encoding} 编码下发现乱码")
            else:
                print(f"  ✓ {encoding} 编码正常")
            print()
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_toutiao_encoding()
