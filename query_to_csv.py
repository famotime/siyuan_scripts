"""
读取.db数据库文件，使用sql查询数据，并保存查询结果为csv文件

使用示例：
1. 直接运行脚本: python query_to_csv.py
2. 作为模块导入:
   from query_to_csv import SQLiteQueryToCSV

   # 创建查询工具
   query_tool = SQLiteQueryToCSV("path/to/siyuan.db")

   # 执行查询并保存CSV
   query_tool.query_to_csv("SELECT * FROM blocks LIMIT 10", "output.csv")

   # 导出整张表
   query_tool.export_table_to_csv("blocks", "blocks_export.csv", limit=1000)
"""

import sqlite3
import csv
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# 导入通用函数库
from utilities import setup_logging, FileManager, COMMON_QUERIES

# 配置日志
logger = setup_logging()


def quick_export_example():
    """
    快速导出示例 - 演示基本用法
    """
    print("快速导出示例")
    print("=" * 20)

    # 获取数据库路径
    db_path = input("请输入思源笔记数据库路径: ").strip().strip('"')

    if not db_path:
        print("未输入数据库路径，退出示例")
        return

    try:
        # 创建查询工具
        query_tool = SQLiteQueryToCSV(db_path)

        # 创建输出目录
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # 快速导出最新的100篇文档
        print("正在导出最新的100篇文档...")
        simple_query = """
        SELECT
            content as 文档标题,
            hpath as 文档路径,
            datetime(created/1000, 'unixepoch', 'localtime') as 创建时间,
            datetime(updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks
        WHERE type = 'd'
        ORDER BY updated DESC
        LIMIT 100
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"latest_documents_{timestamp}.csv"

        success = query_tool.query_to_csv(simple_query, str(output_file))

        if success:
            print(f"✓ 导出完成: {output_file}")
            print("你可以用Excel或其他工具打开这个CSV文件查看结果")
        else:
            print("✗ 导出失败")

    except Exception as e:
        print(f"错误: {e}")


class SQLiteQueryToCSV:
    """SQLite数据库查询并导出CSV的工具类"""

    def __init__(self, db_path: str):
        """
        初始化查询工具

        :param db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"数据库文件不存在: {db_path}")

        logger.info(f"初始化SQLite查询工具，数据库: {self.db_path}")

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        执行SQL查询

        :param sql: SQL查询语句
        :return: 查询结果列表
        """
        try:
            logger.info(f"执行SQL查询: {sql}")

            with sqlite3.connect(self.db_path) as conn:
                # 设置行工厂，使返回结果为字典格式
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 执行查询
                cursor.execute(sql)

                # 获取结果
                rows = cursor.fetchall()

                # 转换为字典列表
                result = [dict(row) for row in rows]

                logger.info(f"查询成功，返回 {len(result)} 条记录")
                return result

        except sqlite3.Error as e:
            logger.error(f"SQL查询执行失败: {e}")
            raise
        except Exception as e:
            logger.error(f"查询过程中发生错误: {e}")
            raise

    def query_to_csv(self, sql: str, output_file: str, encoding: str = 'utf-8') -> bool:
        """
        执行SQL查询并将结果保存为CSV文件

        :param sql: SQL查询语句
        :param output_file: 输出CSV文件路径
        :param encoding: 文件编码，默认utf-8
        :return: 是否成功
        """
        try:
            # 执行查询
            results = self.execute_query(sql)

            if not results:
                logger.warning("查询结果为空，将创建空的CSV文件")
                # 创建空文件
                Path(output_file).touch()
                return True

            # 确保输出目录存在
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入CSV文件
            with open(output_path, 'w', newline='', encoding=encoding) as csvfile:
                # 获取字段名
                fieldnames = list(results[0].keys())

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # 写入表头
                writer.writeheader()

                # 写入数据行
                writer.writerows(results)

            logger.info(f"CSV文件已保存到: {output_path}")
            logger.info(f"共写入 {len(results)} 条记录，{len(fieldnames)} 个字段")

            return True

        except Exception as e:
            logger.error(f"保存CSV文件失败: {e}")
            return False

    def get_table_list(self) -> List[str]:
        """
        获取数据库中所有表的列表

        :return: 表名列表
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        try:
            results = self.execute_query(sql)
            tables = [row['name'] for row in results]
            logger.info(f"数据库中共有 {len(tables)} 张表: {tables}")
            return tables
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            return []

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表的结构信息

        :param table_name: 表名
        :return: 表结构信息
        """
        sql = f"PRAGMA table_info({table_name})"
        try:
            results = self.execute_query(sql)
            logger.info(f"表 {table_name} 的结构信息: {len(results)} 个字段")
            return results
        except Exception as e:
            logger.error(f"获取表 {table_name} 信息失败: {e}")
            return []

    def export_table_to_csv(self, table_name: str, output_file: str,
                           limit: Optional[int] = None, encoding: str = 'utf-8') -> bool:
        """
        导出整张表到CSV文件

        :param table_name: 表名
        :param output_file: 输出文件路径
        :param limit: 限制导出记录数，None表示全部导出
        :param encoding: 文件编码
        :return: 是否成功
        """
        sql = f"SELECT * FROM {table_name}"
        if limit:
            sql += f" LIMIT {limit}"

        return self.query_to_csv(sql, output_file, encoding)

def run_preset_query(query_tool: SQLiteQueryToCSV, query_name: str, output_dir: Path) -> bool:
    """
    运行预设查询

    :param query_tool: 查询工具实例
    :param query_name: 查询名称
    :param output_dir: 输出目录
    :return: 是否成功
    """
    if query_name not in COMMON_QUERIES:
        print(f"未找到预设查询: {query_name}")
        return False

    sql = COMMON_QUERIES[query_name]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = query_name.replace(" ", "_").replace(":", "").replace("/", "_")
    output_file = output_dir / f"{safe_name}_{timestamp}.csv"

    print(f"执行预设查询: {query_name}")
    return query_tool.query_to_csv(sql, str(output_file))


def interactive_mode(query_tool: SQLiteQueryToCSV, output_dir: Path):
    """
    交互式查询模式

    :param query_tool: 查询工具实例
    :param output_dir: 输出目录
    """
    print("\n=== 交互式查询模式 ===")
    print("可用命令:")
    print("  - 输入SQL查询语句直接执行")
    print("  - 'presets' 显示预设查询列表")
    print("  - 'preset <编号>' 执行预设查询")
    print("  - 'tables' 显示所有表")
    print("  - 'info <表名>' 显示表结构")
    print("  - 'export <表名>' 导出整张表")
    print("  - 'quit' 退出")

    while True:
        try:
            command = input("\n请输入命令或SQL语句: ").strip()

            if command.lower() in ['quit', 'exit', 'q']:
                break

            if not command:
                continue

            # 处理特殊命令
            if command.lower() == 'presets':
                print("\n预设查询列表:")
                for i, name in enumerate(COMMON_QUERIES.keys(), 1):
                    print(f"  {i}. {name}")
                continue

            if command.lower().startswith('preset '):
                try:
                    preset_num = int(command.split()[1])
                    preset_names = list(COMMON_QUERIES.keys())
                    if 1 <= preset_num <= len(preset_names):
                        query_name = preset_names[preset_num - 1]
                        success = run_preset_query(query_tool, query_name, output_dir)
                        if success:
                            print(f"预设查询 '{query_name}' 执行完成")
                    else:
                        print(f"无效的预设查询编号: {preset_num}")
                except (IndexError, ValueError):
                    print("使用方法: preset <编号>")
                continue

            if command.lower() == 'tables':
                tables = query_tool.get_table_list()
                print(f"\n数据库表列表: {', '.join(tables)}")
                continue

            if command.lower().startswith('info '):
                try:
                    table_name = command.split()[1]
                    info = query_tool.get_table_info(table_name)
                    if info:
                        print(f"\n表 {table_name} 的结构:")
                        for field in info:
                            print(f"  {field['name']} ({field['type']})")
                    else:
                        print(f"表 {table_name} 不存在或获取信息失败")
                except IndexError:
                    print("使用方法: info <表名>")
                continue

            if command.lower().startswith('export '):
                try:
                    table_name = command.split()[1]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = output_dir / f"table_{table_name}_{timestamp}.csv"
                    success = query_tool.export_table_to_csv(table_name, str(output_file), limit=10000)
                    if success:
                        print(f"表 {table_name} 导出完成")
                except IndexError:
                    print("使用方法: export <表名>")
                continue

            # 执行SQL查询
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"query_result_{timestamp}.csv"

            success = query_tool.query_to_csv(command, str(output_file))

            if success:
                print(f"查询完成，结果已保存到: {output_file}")

        except KeyboardInterrupt:
            print("\n操作被用户中断")
            break
        except Exception as e:
            print(f"执行失败: {e}")


def main():
    """
    主函数 - 示例使用
    """
    # 获取数据库路径
    db_path = r"D:\SiYuan_data\temp\siyuan.db"

    try:
        # 创建查询工具
        query_tool = SQLiteQueryToCSV(db_path)

        # 获取并显示所有表
        tables = query_tool.get_table_list()
        if not tables:
            print("数据库中没有找到表")
            return

        print(f"\n数据库中的表: {', '.join(tables)}")

        # 创建输出目录
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # 选择操作模式
        print("\n操作模式:")
        print("1. 执行预设查询")
        print("2. 交互式查询")
        print("3. 运行所有预设查询")

        choice = input("请选择操作模式 (1-3): ").strip()

        if choice == "1":
            print("\n预设查询列表:")
            preset_names = list(COMMON_QUERIES.keys())
            for i, name in enumerate(preset_names, 1):
                print(f"  {i}. {name}")

            try:
                preset_num = int(input("请选择预设查询编号: ").strip())
                if 1 <= preset_num <= len(preset_names):
                    query_name = preset_names[preset_num - 1]
                    success = run_preset_query(query_tool, query_name, output_dir)
                    if success:
                        print(f"预设查询 '{query_name}' 执行完成")
                else:
                    print(f"无效的预设查询编号: {preset_num}")
            except ValueError:
                print("请输入有效的数字")

        elif choice == "2":
            interactive_mode(query_tool, output_dir)

        elif choice == "3":
            print("\n执行所有预设查询...")
            for query_name in COMMON_QUERIES.keys():
                success = run_preset_query(query_tool, query_name, output_dir)
                if success:
                    print(f"✓ {query_name}")
                else:
                    print(f"✗ {query_name}")
            print("所有预设查询执行完成")

        else:
            print("无效的选择")

        print("\n程序结束")

    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        print(f"错误：{e}")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"错误：{e}")


if __name__ == "__main__":
    main()

