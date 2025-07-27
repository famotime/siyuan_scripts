"""将剪贴板中的html转换为markdown文件"""

import sys
from datetime import datetime
from pathlib import Path
from utilities import ClipboardManager, HTMLConverter
from utilities.common import logger


def main():
    # 1. 读取剪贴板内容
    clipboard = ClipboardManager()
    if not clipboard.is_available():
        logger.error("剪贴板不可用，请确保已安装 pyperclip 库。")
        sys.exit(1)

    try:
        import pyperclip
        html_content = pyperclip.paste()

        # 调试信息
        logger.info(f"剪贴板内容长度: {len(html_content) if html_content else 0}")
        if html_content:
            logger.info(f"剪贴板内容前100字符: {html_content[:100]}")

    except Exception as e:
        logger.error(f"读取剪贴板失败: {e}")
        sys.exit(1)

    if not html_content or len(html_content.strip()) == 0:
        logger.error("剪贴板内容为空！")
        sys.exit(1)

    # 2. 转换为 Markdown
    converter = HTMLConverter()
    markdown = converter.convert_html_to_markdown(html_content)

    # 3. 自动命名并保存
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"clipboard_{now_str}.md"
    output_file.write_text(markdown, encoding="utf-8")

    logger.info(f"已保存为: {output_file}")
    print(f"已保存为: {output_file}")

if __name__ == "__main__":
    main()
