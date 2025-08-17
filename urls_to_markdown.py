"""
将输入的Web页面链接转换为Markdown文档：
1. 复制URL到剪贴板，每行一个URL；
2. 网页内容保存为markdown文件，媒体文件保存到media文件夹；
"""

import asyncio
import logging
from utilities import URLToMarkdownConverter

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """
    主函数 - 从剪贴板读取URL并转换为Markdown
    """
    # 导入配置模块
    from config import get_urls_path
    
    converter = URLToMarkdownConverter(output_dir=str(get_urls_path()))

    if not converter.is_clipboard_available():
        print("❌ 错误: pyperclip库未安装")
        print("请运行: pip install pyperclip")
        return False

    print("正在从剪贴板读取URL...")

    try:
        # 从剪贴板读取并转换URL
        successful_files = await converter.convert_urls_from_clipboard(download_media=True)

        # 显示结果
        print("\n" + "=" * 50)
        if successful_files:
            print(f"✅ 转换完成! 成功转换 {len(successful_files)} 个文件")
            print(f"📁 输出目录: {converter.output_dir.absolute()}")

            print(f"\n生成的Markdown文件:")
            for file_path in successful_files:
                size = file_path.stat().st_size
                print(f"  📄 {file_path.name} ({size:,} 字节)")

            # 检查媒体文件
            media_dir = converter.output_dir / "media"
            if media_dir.exists():
                media_files = list(media_dir.glob("*"))
                if media_files:
                    print(f"\n📁 下载的媒体文件: {len(media_files)} 个")
            return True
        else:
            print("❌ 没有成功转换任何文件")
            print("请检查剪贴板中的URL格式是否正确")
            return False

    except Exception as e:
        print(f"❌ 转换过程中出现错误: {e}")
        return False


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())