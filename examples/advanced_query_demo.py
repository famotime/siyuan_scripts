#!/usr/bin/env python3
"""
思源笔记高级SQL查询演示脚本

本脚本演示如何使用 advanced_sql_queries 模块中的各种查询场景。
包含以下功能：
1. 查询分类浏览
2. 关键词搜索查询
3. 执行特定查询
4. 参数化查询示例
5. 查询结果导出

使用方法：
python examples/advanced_query_demo.py
"""

import sys
import os
import json
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.advanced_sql_queries import (
    get_all_query_categories,
    get_all_query_names,
    get_query_by_name,
    get_query_sql,
    search_queries_by_keyword,
    get_queries_by_category,
    format_query_info,
    export_all_queries_to_dict,
    get_documents_by_tag,
    get_documents_by_custom_attribute,
    get_documents_by_date_range
)

from utilities.api_client import SiyuanAPI
from utilities.common import setup_logging

def print_separator(title="", char="=", width=60):
    """打印分隔线"""
    if title:
        print(f"\n{char * 5} {title} {char * (width - len(title) - 7)}")
    else:
        print(char * width)

def display_query_categories():
    """显示所有查询分类"""
    print_separator("查询分类概览")
    categories = get_all_query_categories()
    
    for category, queries in categories.items():
        print(f"\n📁 {category} ({len(queries)}个查询)")
        for i, (name, info) in enumerate(queries.items(), 1):
            print(f"   {i}. {name}")
            print(f"      💡 {info.get('description', '无描述')}")

def search_and_display_queries():
    """搜索并显示查询"""
    print_separator("查询搜索")
    
    # 演示几个搜索示例
    search_terms = ["标签", "时间", "引用", "统计"]
    
    for term in search_terms:
        results = search_queries_by_keyword(term)
        print(f"\n🔍 搜索关键词 '{term}' 的结果:")
        if results:
            for i, query_name in enumerate(results, 1):
                print(f"   {i}. {query_name}")
        else:
            print("   未找到相关查询")

def display_query_details():
    """显示查询详细信息"""
    print_separator("查询详细信息示例")
    
    # 选择几个有代表性的查询进行展示
    sample_queries = [
        "文档总体统计",
        "高价值文档识别", 
        "标签使用统计",
        "孤立文档检测"
    ]
    
    for query_name in sample_queries:
        print(f"\n📋 {query_name}")
        print("-" * 40)
        query_info = get_query_by_name(query_name)
        if query_info:
            print(f"描述: {query_info.get('description')}")
            print(f"应用: {query_info.get('application')}")
            print(f"预期结果: {query_info.get('expected_result')}")
            print(f"\nSQL语句:")
            print(query_info.get('sql', '').strip())
        else:
            print("查询不存在")

def demonstrate_parameterized_queries():
    """演示参数化查询"""
    print_separator("参数化查询示例")
    
    print("\n1. 根据标签查询文档")
    print("   函数: get_documents_by_tag(tag_name, limit)")
    print("   示例: 查询包含'Python'标签的文档")
    sql = get_documents_by_tag("Python", 20)
    print(f"   生成的SQL:\n{sql}")
    
    print("\n2. 根据自定义属性查询文档")
    print("   函数: get_documents_by_custom_attribute(attribute_name, attribute_value, limit)")
    print("   示例: 查询分类为'技术'的文档")
    sql = get_documents_by_custom_attribute("classify", "技术", 30)
    print(f"   生成的SQL:\n{sql}")
    
    print("\n3. 根据日期范围查询文档")
    print("   函数: get_documents_by_date_range(start_date, end_date, date_type, limit)")
    print("   示例: 查询最近7天更新的文档")
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    sql = get_documents_by_date_range(start_date, end_date, 'updated', 50)
    print(f"   生成的SQL:\n{sql}")

def execute_sample_queries():
    """执行示例查询（需要连接到思源笔记）"""
    print_separator("执行示例查询")
    
    try:
        # 尝试连接思源笔记API
        api = SiyuanAPI()
        
        # 执行一个简单的统计查询
        print("\n📊 执行文档总体统计查询...")
        sql = get_query_sql("文档总体统计")
        if sql:
            result = api.call_api('/api/query/sql', {'stmt': sql})
            if result:
                print("查询结果:")
                for row in result:
                    for key, value in row.items():
                        print(f"   {key}: {value}")
            else:
                print("查询无结果")
        
        # 执行块类型分布统计
        print("\n📊 执行块类型分布统计查询...")
        sql = get_query_sql("块类型分布统计")
        if sql:
            result = api.call_api('/api/query/sql', {'stmt': sql})
            if result:
                print("查询结果:")
                for row in result[:5]:  # 只显示前5行
                    print(f"   {row.get('块类型说明', '')}: {row.get('数量', 0)}个 ({row.get('占比百分比', 0)}%)")
                if len(result) > 5:
                    print(f"   ... 还有{len(result) - 5}行结果")
            else:
                print("查询无结果")
                
    except Exception as e:
        print(f"⚠️  无法连接到思源笔记API: {e}")
        print("请确保思源笔记正在运行，并且API服务已启用")
        print("您仍然可以查看SQL语句，手动在思源笔记中执行")

def export_queries_to_file():
    """导出查询到文件"""
    print_separator("导出查询信息")
    
    # 导出为JSON格式
    output_file = "siyuan_advanced_queries.json"
    queries_data = export_all_queries_to_dict()
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(queries_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 查询信息已导出到: {output_file}")
        print(f"   总计 {queries_data['metadata']['total_queries']} 个查询")
        print(f"   分为 {len(queries_data['metadata']['categories'])} 个分类")
    except Exception as e:
        print(f"❌ 导出失败: {e}")

def interactive_query_browser():
    """交互式查询浏览器"""
    print_separator("交互式查询浏览器")
    print("输入查询名称的部分关键词来搜索，输入 'quit' 退出")
    
    while True:
        try:
            keyword = input("\n🔍 请输入搜索关键词: ").strip()
            if keyword.lower() in ['quit', 'exit', 'q']:
                break
            
            if not keyword:
                continue
                
            results = search_queries_by_keyword(keyword)
            if results:
                print(f"\n找到 {len(results)} 个相关查询:")
                for i, query_name in enumerate(results, 1):
                    print(f"{i}. {query_name}")
                
                try:
                    choice = input("\n请输入序号查看详情 (回车跳过): ").strip()
                    if choice and choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(results):
                            print(format_query_info(results[idx]))
                except (ValueError, IndexError):
                    print("无效的选择")
            else:
                print("未找到相关查询")
                
        except KeyboardInterrupt:
            break
    
    print("\n👋 感谢使用查询浏览器！")

def main():
    """主函数"""
    print("🚀 思源笔记高级SQL查询演示")
    print("=" * 60)
    
    # 设置日志
    setup_logging()
    
    # 1. 显示查询分类
    display_query_categories()
    
    # 2. 搜索演示
    search_and_display_queries()
    
    # 3. 查询详情演示
    display_query_details()
    
    # 4. 参数化查询演示
    demonstrate_parameterized_queries()
    
    # 5. 执行示例查询
    execute_sample_queries()
    
    # 6. 导出查询信息
    export_queries_to_file()
    
    # 7. 交互式浏览器
    print("\n" + "=" * 60)
    choice = input("是否启动交互式查询浏览器？(y/N): ").strip().lower()
    if choice in ['y', 'yes']:
        interactive_query_browser()
    
    print("\n✨ 演示完成！")
    print("您可以在 utilities/advanced_sql_queries.py 中查看所有查询定义")

if __name__ == "__main__":
    main()
