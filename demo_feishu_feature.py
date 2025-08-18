#!/usr/bin/env python3
"""
飞书链接微信原文提取功能演示脚本
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utilities.web_downloader import WebDownloader

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def demo_link_extraction():
    """演示链接提取功能"""
    
    print("🎯 飞书链接微信原文提取功能演示")
    print("=" * 50)
    
    # 模拟飞书页面内容
    demo_contents = [
        {
            "name": "标准格式",
            "content": """<!DOCTYPE html>
<html><head><title>AI技术分享</title></head>
<body>
<h1>AI技术深度解析</h1>
<p>原文链接：https://mp.weixin.qq.com/s/AbCdEf123456</p>
<div>这里是文章内容...</div>
</body></html>"""
        },
        {
            "name": "带参数的链接",
            "content": """<!DOCTYPE html>
<html><head><title>技术文章</title></head>
<body>
<h1>深度学习最新进展</h1>
<p>原文链接：https://mp.weixin.qq.com/s?__biz=MzI1234567890&mid=2247484123&idx=1&sn=abcdef123456</p>
<div>文章正文内容...</div>
</body></html>"""
        },
        {
            "name": "无原文链接",
            "content": """<!DOCTYPE html>
<html><head><title>飞书原创文章</title></head>
<body>
<h1>这是飞书原创内容</h1>
<p>这篇文章没有微信公众号原文链接</p>
<div>直接在飞书上创建的内容...</div>
</body></html>"""
        }
    ]
    
    downloader = WebDownloader()
    
    for i, demo in enumerate(demo_contents, 1):
        print(f"\n📄 演示 {i}: {demo['name']}")
        print("-" * 30)
        
        # 提取原文链接
        original_url = downloader._extract_wechat_original_link(demo['content'])
        
        if original_url:
            print(f"✅ 找到原文链接: {original_url}")
            print(f"🔄 系统将使用原文链接获取内容")
        else:
            print(f"ℹ️  未找到微信原文链接")
            print(f"📝 系统将使用飞书页面内容")

def demo_url_detection():
    """演示URL检测功能"""
    
    print("\n🔍 URL检测功能演示")
    print("=" * 50)
    
    test_urls = [
        "https://waytoagi.feishu.cn/wiki/example123",
        "https://waytoagi.feishu.cn/docs/example456", 
        "https://mp.weixin.qq.com/s/abc123",
        "https://example.com/article",
    ]
    
    for url in test_urls:
        is_feishu = url.startswith("https://waytoagi.feishu.cn/")
        
        if is_feishu:
            print(f"🎯 飞书链接: {url}")
            print(f"   → 将检查是否包含微信原文链接")
        else:
            print(f"🌐 普通链接: {url}")
            print(f"   → 直接获取内容")

def show_usage_guide():
    """显示使用指南"""
    
    print("\n📖 使用指南")
    print("=" * 50)
    
    print("""
🚀 如何使用这个功能：

1️⃣ 复制飞书链接到剪贴板
   例如：https://waytoagi.feishu.cn/wiki/example

2️⃣ 运行转换脚本
   python urls_to_siyuan.py

3️⃣ 系统自动处理
   ✓ 检测飞书链接
   ✓ 获取页面内容
   ✓ 查找前10行中的"原文链接："
   ✓ 如果找到微信链接，使用原文内容
   ✓ 如果没找到，使用飞书内容
   ✓ 转换为Markdown
   ✓ 导入思源笔记

📋 支持的原文链接格式：
   • 原文链接：https://mp.weixin.qq.com/s/abc123
   • 原文链接:https://mp.weixin.qq.com/s/def456
   • 原文链接： https://mp.weixin.qq.com/s/ghi789
   • 原文链接 : https://mp.weixin.qq.com/s/jkl012

⚠️ 注意事项：
   • 原文链接必须在页面前10行中
   • 必须是完整的微信公众号链接
   • 支持带参数的微信链接
""")

def main():
    """主演示函数"""
    
    print("🎉 欢迎使用飞书链接微信原文提取功能！")
    print()
    
    try:
        # 演示链接提取
        demo_link_extraction()
        
        # 演示URL检测
        demo_url_detection()
        
        # 显示使用指南
        show_usage_guide()
        
        print("\n✨ 演示完成！功能已集成到主脚本中，可以直接使用。")
        print("🔧 如需测试，请运行：python test_feishu_wechat_extraction.py")
        
    except Exception as e:
        print(f"❌ 演示过程出错: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
