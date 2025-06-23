"""
结合 export_wiznotes_to_md.py 和 create_notes_from_md.py：
1. 转换为知笔记指定目录下笔记为markdown文件；
2. 将MD目录下markdown文件导入到思源笔记；
3. 将MD目录下的md文件移动到"已转思源"目录
"""

import os
import sys
from pathlib import Path
import shutil

# 导入相关脚本的main函数
import export_wiznotes_to_md
import create_notes_from_md

# 导入日志模块
from utilities import setup_logging

# 配置参数
DEFAULT_MD_FOLDER = "H:/为知笔记导出MD备份/My Emails"

def step1_export_wiz_notes():
    """步骤1：调用export_wiznotes_to_md.py的main函数导出为知笔记"""
    logger.info("=== 步骤1：调用export_wiznotes_to_md.py导出为知笔记 ===")

    try:
        # 直接调用get_wiz_notes的main函数
        export_wiznotes_to_md.main()
        return True

    except SystemExit as e:
        # 处理sys.exit()调用
        if e.code == 0:
            return True
        else:
            logger.error(f"❌ export_wiznotes_to_md.py 执行失败，退出码: {e.code}")
            return False

    except Exception as e:
        logger.error(f"调用export_wiznotes_to_md.py时发生异常: {e}")
        return False

def step2_import_to_siyuan():
    """步骤2：调用create_notes_from_md.py的main函数导入到思源笔记"""
    logger.info("\n=== 步骤2：调用create_notes_from_md.py导入到思源笔记 ===")

    try:
        # 直接调用create_notes_from_md的main函数
        create_notes_from_md.main()
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

    try:
        # 步骤1：调用export_wiznotes_to_md.py的main函数
        if not step1_export_wiz_notes():
            logger.error("❌ 步骤1失败，终止流程")
            return

        # 步骤2：调用create_notes_from_md.py的main函数
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