"""
结合 urls_to_markdown.py 和 create_notes_from_md.py：
1. 将剪贴板中的URL转换为markdown文件；
2. 将MD目录下markdown文件导入到思源笔记；
3. 将MD目录下的md文件移动到"已转思源"目录

支持多种HTML转Markdown转换方式：
- markdownify: 使用markdownify库转换
- html2text: 使用html2text库转换
- builtin: 使用内置转换器
- all: 使用所有三种方式各生成一份，文件名添加后缀区分
"""

import os
import sys
from pathlib import Path
import shutil
import asyncio

# 导入相关脚本的main函数
import urls_to_markdown
import create_notes_from_md

# 导入日志模块和转换器
from utilities import setup_logging, URLToMarkdownConverter

# markdown文件导出目录
DEFAULT_MD_FOLDER = "H:/为知笔记导出MD备份/urls_to_markdown"
# 默认转换方式, 可选: markdownify, html2text, builtin, all; all 表示使用所有三种方式各生成一份，文件名添加后缀区分
DEFAULT_CONVERTER_LIB = "markdownify"

# 支持的转换方式
SUPPORTED_CONVERTERS = ["markdownify", "html2text", "builtin", "all"]


def get_converter_config():
    """从环境变量或配置获取转换器设置"""
    converter_lib = os.getenv("CONVERTER_LIB", DEFAULT_CONVERTER_LIB)

    # 验证转换器选项
    if converter_lib not in SUPPORTED_CONVERTERS:
        logger.warning(f"不支持的转换器: {converter_lib}，使用默认: {DEFAULT_CONVERTER_LIB}")
        converter_lib = DEFAULT_CONVERTER_LIB

    return converter_lib


async def convert_urls_with_multiple_converters(output_dir, download_media=True):
    """使用多种转换器转换URL"""
    converters_to_use = ["markdownify", "html2text", "builtin"]
    converter_suffixes = {
        "markdownify": "_markdownify",
        "html2text": "_html2text",
        "builtin": "_builtin"
    }

    all_successful_files = []

    for converter_lib in converters_to_use:
        logger.info(f"\n--- 使用 {converter_lib} 转换器 ---")

        # 创建转换器
        converter = URLToMarkdownConverter(
            output_dir=output_dir,
            converter_lib=converter_lib
        )

        # 检查剪贴板
        if not converter.is_clipboard_available():
            logger.error("❌ 错误: pyperclip库未安装，请运行: pip install pyperclip")
            continue

        try:
            # 从剪贴板转换URL
            successful_files = await converter.convert_urls_from_clipboard(download_media=download_media)

            # 为文件添加转换器后缀
            if successful_files:
                suffix = converter_suffixes[converter_lib]
                renamed_files = []

                for file_path in successful_files:
                    # 生成新文件名（添加转换器后缀）
                    new_name = file_path.stem + suffix + file_path.suffix
                    new_path = file_path.parent / new_name

                    # 重命名文件
                    if new_path.exists():
                        new_path.unlink()  # 删除已存在的文件
                    file_path.rename(new_path)
                    renamed_files.append(new_path)

                    logger.info(f"  ✓ 生成文件: {new_path.name}")

                all_successful_files.extend(renamed_files)
                logger.info(f"✅ {converter_lib} 转换完成，生成 {len(renamed_files)} 个文件")
            else:
                logger.warning(f"⚠️ {converter_lib} 转换器没有生成任何文件")

        except Exception as e:
            logger.error(f"❌ {converter_lib} 转换器执行失败: {e}")

    return all_successful_files


def step1_urls_to_markdown():
    """步骤1：调用urls_to_markdown转换功能，支持多种转换方式"""
    logger.info("=== 步骤1：URL转换为Markdown文件 ===")

    # 获取转换器配置
    converter_lib = get_converter_config()
    logger.info(f"使用转换器: {converter_lib}")

    try:
        if converter_lib == "all":
            # 使用所有三种转换器
            logger.info("使用所有转换器各生成一份文件...")
            output_dir = DEFAULT_MD_FOLDER
            successful_files = asyncio.run(convert_urls_with_multiple_converters(output_dir))

            if successful_files:
                logger.info(f"✅ 总共生成 {len(successful_files)} 个文件")
                return True
            else:
                logger.error("❌ 没有成功生成任何文件")
                return False
        else:
            # 使用指定的单一转换器
            # 创建自定义转换器实例
            converter = URLToMarkdownConverter(
                output_dir=DEFAULT_MD_FOLDER,
                converter_lib=converter_lib
            )

            if not converter.is_clipboard_available():
                logger.error("❌ 错误: pyperclip库未安装，请运行: pip install pyperclip")
                return False

            # 异步转换
            async def convert():
                return await converter.convert_urls_from_clipboard(download_media=True)

            successful_files = asyncio.run(convert())

            if successful_files:
                logger.info(f"✅ 使用 {converter_lib} 转换完成，生成 {len(successful_files)} 个文件")
                return True
            else:
                logger.error("❌ 没有成功转换任何文件")
                return False

    except SystemExit as e:
        # 处理sys.exit()调用
        if e.code == 0:
            return True
        else:
            logger.error(f"❌ URL转换执行失败，退出码: {e.code}")
            return False

    except Exception as e:
        logger.error(f"调用URL转换时发生异常: {e}")
        return False


def step2_import_to_siyuan(md_folder=DEFAULT_MD_FOLDER):
    """步骤2：调用create_notes_from_md.py的main函数将md文件导入到思源笔记"""
    logger.info("\n=== 步骤2：导入Markdown文件到思源笔记 ===")

    try:
        # 直接调用create_notes_from_md的main函数
        create_notes_from_md.main(md_folder)
        return True

    except SystemExit as e:
        # 处理sys.exit()调用
        if e.code == 0:
            return True
        else:
            logger.error(f"❌ create_notes_from_md.py 执行失败，退出码: {e.code}")
            return False

    except Exception as e:
        logger.error(f"调用create_notes_from_md.py时发生异常: {e}")
        return False


def step3_move_files():
    """步骤3：将MD目录下的所有文件和目录移动到"已转思源"目录"""
    logger.info("\n=== 步骤3：移动已导入笔记到\"已转思源\"目录 ===")

    # 获取MD文件夹路径
    md_folder = os.getenv("MD_FOLDER", DEFAULT_MD_FOLDER)
    md_path = Path(md_folder)

    if not md_path.exists():
        logger.warning(f"MD文件夹不存在: {md_folder}")
        return True  # 不算失败，可能没有文件需要移动

    try:
        # 确保目标目录存在
        target_dir = md_path.parent / "已转思源"
        target_dir.mkdir(parents=True, exist_ok=True)

        # 获取所有文件和目录
        items = list(md_path.iterdir())
        moved_count = 0

        # 逐个移动文件和目录
        for item in items:
            target_item = target_dir / item.name

            # 如果目标已存在，先删除
            if target_item.exists():
                if target_item.is_dir():
                    shutil.rmtree(target_item)
                else:
                    target_item.unlink()

            # 移动文件或目录
            item.rename(target_item)
            moved_count += 1

        if moved_count > 0:
            logger.info(f"✅ 已将 {moved_count} 个文件移动到: {target_dir}")
        else:
            logger.info("📁 没有文件需要移动")

        return True

    except Exception as move_error:
        logger.error(f"移动MD文件失败: {move_error}")
        return False

def main():
    """主函数：执行完整的转换流程"""
    global logger

    # 设置日志
    logger = setup_logging()

    # 显示当前配置
    converter_lib = get_converter_config()
    print(f"\n🔧 当前转换器设置: {converter_lib}")
    print(f"📁 输出目录: {DEFAULT_MD_FOLDER}")

    try:
        # 步骤1：URL转换为Markdown
        if not step1_urls_to_markdown():
            logger.error("❌ 步骤1失败，终止流程")
            return

        # 步骤2：导入到思源笔记
        if not step2_import_to_siyuan():
            logger.error("❌ 步骤2失败，终止流程")
            return

        # 步骤3：移动文件到已转思源目录
        if not step3_move_files():
            logger.error("❌ 步骤3失败，但前面步骤已完成")
            return

        logger.info("🎉 完整转换流程执行成功！")

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序执行失败: {e}")


if __name__ == "__main__":
    main()