# 思源笔记高级SQL查询使用指南

## 概述

本指南介绍了一套完整的思源笔记数据查询和统计场景，包含25个精心设计的SQL查询，涵盖基础统计、内容分析、时间维度分析和高级查询等多个方面。

## 查询分类

### 1. 基础统计查询 (4个)

| 查询名称 | 功能描述 | 应用场景 |
|---------|---------|---------|
| 文档总体统计 | 统计文档总数、平均字数、笔记本数量等 | 了解笔记库整体规模 |
| 块类型分布统计 | 统计各种块类型的数量和占比 | 了解笔记结构特点 |
| 笔记本统计排行 | 各笔记本的文档数量、字数统计 | 识别最活跃的笔记本 |
| 标题层级分布 | 统计各级标题的使用情况 | 优化文档组织方式 |

### 2. 内容分析查询 (4个)

| 查询名称 | 功能描述 | 应用场景 |
|---------|---------|---------|
| 字数统计排行 | 按字数排序文档，找出最长/最短文档 | 识别重要文档和待完善内容 |
| 标签使用统计 | 统计标签使用频率和覆盖率 | 优化标签管理体系 |
| 引用关系分析 | 分析文档间引用关系，找出核心文档 | 识别知识网络关键节点 |
| 代码块统计分析 | 统计代码块和编程语言分布 | 了解技术栈使用情况 |

### 3. 时间维度查询 (4个)

| 查询名称 | 功能描述 | 应用场景 |
|---------|---------|---------|
| 创建时间分布 | 按月份统计文档创建情况 | 分析写作习惯和活跃度 |
| 最近活跃文档 | 查找最近更新的文档 | 快速继续编辑工作 |
| 长期未更新文档 | 查找长时间未更新的文档 | 识别需要维护的内容 |
| 每日写作统计 | 按日期统计创建和更新情况 | 制定写作计划 |

### 4. 高级查询 (5个)

| 查询名称 | 功能描述 | 应用场景 |
|---------|---------|---------|
| 孤立文档检测 | 查找没有引用关系的文档 | 改善知识网络连接 |
| 高价值文档识别 | 综合多指标识别重要文档 | 优先维护核心内容 |
| 标签共现分析 | 分析经常一起出现的标签 | 优化标签体系设计 |
| 引用网络深度分析 | 分析文档引用深度和广度 | 了解知识网络复杂度 |
| 内容相似度分析 | 基于标签找出相似文档 | 发现重复内容便于整合 |

### 5. 特殊用途查询 (5个)

| 查询名称 | 功能描述 | 应用场景 |
|---------|---------|---------|
| 图片资源统计 | 统计文档中图片使用情况 | 管理媒体文件资源 |
| 数学公式使用统计 | 统计数学公式块和行内公式 | 学术和技术文档管理 |
| 任务列表统计 | 统计任务列表完成情况 | 跟踪待办事项进度 |
| 表格使用统计 | 统计文档中表格使用情况 | 结构化数据管理 |
| 自定义属性分布 | 统计自定义属性使用情况 | 优化属性管理体系 |

## 使用方法

### 1. 基本使用

```python
from utilities.advanced_sql_queries import (
    get_query_sql, 
    get_all_query_names,
    format_query_info
)

# 获取所有查询名称
query_names = get_all_query_names()
print(f"共有 {len(query_names)} 个查询")

# 获取特定查询的SQL语句
sql = get_query_sql("文档总体统计")
print(sql)

# 获取查询的详细信息
info = format_query_info("高价值文档识别")
print(info)
```

### 2. 分类浏览

```python
from utilities.advanced_sql_queries import get_all_query_categories

categories = get_all_query_categories()
for category, queries in categories.items():
    print(f"{category}: {len(queries)}个查询")
    for name in queries.keys():
        print(f"  - {name}")
```

### 3. 关键词搜索

```python
from utilities.advanced_sql_queries import search_queries_by_keyword

# 搜索包含"标签"的查询
tag_queries = search_queries_by_keyword("标签")
print(f"找到 {len(tag_queries)} 个相关查询: {tag_queries}")
```

### 4. 参数化查询

```python
from utilities.advanced_sql_queries import (
    get_documents_by_tag,
    get_documents_by_custom_attribute,
    get_documents_by_date_range
)

# 查询包含特定标签的文档
sql = get_documents_by_tag("Python", limit=50)

# 查询特定自定义属性的文档
sql = get_documents_by_custom_attribute("classify", "技术", limit=100)

# 查询日期范围内的文档
sql = get_documents_by_date_range("2024-01-01", "2024-12-31", "updated", 200)
```

### 5. 在思源笔记中执行

```python
from utilities.api_client import SiyuanAPI
from utilities.advanced_sql_queries import get_query_sql

# 连接思源笔记API
api = SiyuanAPI()

# 执行查询
sql = get_query_sql("文档总体统计")
result = api.call_api('/api/query/sql', {'stmt': sql})

# 处理结果
if result:
    for row in result:
        print(row)
```

## 查询特点

### 1. 时间格式化
所有时间字段都使用标准格式：
```sql
datetime(时间戳/1000, 'unixepoch', 'localtime')
```

### 2. 中文字段别名
查询结果使用中文字段名，便于理解：
```sql
SELECT 
    content as 文档标题,
    hpath as 文档路径,
    datetime(created/1000, 'unixepoch', 'localtime') as 创建时间
```

### 3. 文档链接生成
自动生成思源笔记内部链接：
```sql
'[' || content || '](siyuan://blocks/' || id || ')' as 文档链接
```

### 4. 合理的限制
添加适当的LIMIT限制，避免查询结果过大：
```sql
ORDER BY updated DESC
LIMIT 50
```

## 演示脚本

运行演示脚本查看所有功能：

```bash
python examples/advanced_query_demo.py
```

演示脚本包含：
- 查询分类浏览
- 关键词搜索演示
- 查询详情展示
- 参数化查询示例
- 实际执行示例（需要连接思源笔记）
- 交互式查询浏览器

## 导出功能

可以将所有查询导出为JSON格式：

```python
from utilities.advanced_sql_queries import export_all_queries_to_dict
import json

data = export_all_queries_to_dict()
with open('queries.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

## 扩展建议

### 1. 添加新查询
在对应的查询字典中添加新的查询定义：

```python
NEW_QUERY = {
    "查询名称": {
        "description": "查询描述",
        "application": "应用场景", 
        "sql": "SQL语句",
        "expected_result": "预期结果说明"
    }
}
```

### 2. 自定义参数化查询
创建新的参数化查询函数：

```python
def get_custom_query(param1: str, param2: int) -> str:
    return f"""
        SELECT ...
        WHERE condition = '{param1}'
        LIMIT {param2}
    """
```

### 3. 结果后处理
对查询结果进行进一步处理和分析：

```python
def analyze_query_result(result: list) -> dict:
    # 对查询结果进行统计分析
    return analysis_data
```

## 注意事项

1. **数据库连接**: 确保思源笔记正在运行且API服务已启用
2. **查询性能**: 大型数据库可能需要调整LIMIT值
3. **字段兼容性**: 不同版本的思源笔记可能有字段差异
4. **自定义属性**: 自定义属性名称需要加上`custom-`前缀
5. **时间格式**: 时间戳需要除以1000转换为秒

## 技术支持

如有问题或建议，请参考：
- 思源笔记官方文档
- 数据库表结构文档
- API接口文档

---

*本查询系统基于思源笔记数据库结构设计，适用于数据分析、内容管理和知识挖掘等场景。*
