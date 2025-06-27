"""
思源笔记SQL查询模板
包含常用的SQL查询语句，用于数据分析和导出

本模块整合了以下查询：
1. 基础文档查询 - 文档统计、创建时间等
2. 标签相关查询 - 包含标签的文档、标签统计、特定标签查询
3. 引用关系查询 - 反向链接、引用统计
4. 内容分析查询 - 字数统计、代码块、图片等
5. 自定义属性查询 - 自定义分类和属性
6. 数据库结构查询 - 表信息、记录统计

注意：
- 时间字段会自动转换为本地时间格式
- 部分查询包含LIMIT限制，可根据需要调整
- 特定标签查询中的标签名称需要手动修改
"""

# 常用查询模板
COMMON_QUERIES = {
    "包含标签的文档": """
        SELECT DISTINCT
            b.root_id,
            b.content as 文档标题,
            b.hpath as 文档路径,
            b.box as 笔记本ID,
            datetime(b.created/1000, 'unixepoch', 'localtime') as 创建时间,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        WHERE b.root_id IN (
            SELECT DISTINCT s.root_id
            FROM spans s
            WHERE s.type = 'tag' OR s.type = 'textmark tag'
        )
        AND b.type = 'd'
        ORDER BY b.updated DESC
        LIMIT 1000
    """,

    "所有文档统计": """
        SELECT
            b.content as 文档标题,
            b.hpath as 文档路径,
            datetime(b.created/1000, 'unixepoch', 'localtime') as 创建时间,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间,
            LENGTH(b.content) as 标题长度
        FROM blocks b
        WHERE b.type = 'd'
        ORDER BY b.updated DESC
        LIMIT 1000
    """,

    "最常用的标签": """
        SELECT
            s.content as 标签名称,
            COUNT(*) as 使用次数,
            COUNT(DISTINCT s.root_id) as 出现在文档数
        FROM spans s
        WHERE s.type = 'tag' OR s.type = 'textmark tag'
        GROUP BY s.content
        ORDER BY 使用次数 DESC
        LIMIT 100
    """,

    "文档字数统计": """
        SELECT
            b.content as 文档标题,
            b.hpath as 文档路径,
            SUM(LENGTH(b2.content)) as 总字数,
            COUNT(b2.id) as 块数量,
            datetime(b.created/1000, 'unixepoch', 'localtime') as 创建时间,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        LEFT JOIN blocks b2 ON b.root_id = b2.root_id
        WHERE b.type = 'd'
        GROUP BY b.root_id
        ORDER BY 总字数 DESC
        LIMIT 500
    """,

    "引用关系": """
        SELECT
            b1.content as 引用文档,
            b2.content as 被引用文档,
            r.def_block_id as 被引用块ID,
            datetime(r.created/1000, 'unixepoch', 'localtime') as 引用创建时间
        FROM refs r
        JOIN blocks b1 ON r.root_id = b1.root_id AND b1.type = 'd'
        JOIN blocks b2 ON r.def_block_root_id = b2.root_id AND b2.type = 'd'
        ORDER BY r.created DESC
        LIMIT 1000
    """,

    "自定义属性": """
        SELECT
            b.content as 文档标题,
            a.name as 属性名,
            a.value as 属性值,
            b.hpath as 文档路径
        FROM blocks b
        JOIN attributes a ON b.id = a.block_id
        WHERE b.type = 'd' AND a.name LIKE 'custom-%'
        ORDER BY a.name, b.updated DESC
        LIMIT 1000
    """,

    "块类型统计": """
        SELECT
            type as 块类型,
            COUNT(*) as 数量,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM blocks), 2) as 百分比
        FROM blocks
        GROUP BY type
        ORDER BY 数量 DESC
    """,

    "笔记本统计": """
        SELECT
            box as 笔记本ID,
            COUNT(*) as 文档数量,
            datetime(MIN(created)/1000, 'unixepoch', 'localtime') as 最早创建时间,
            datetime(MAX(updated)/1000, 'unixepoch', 'localtime') as 最后更新时间
        FROM blocks
        WHERE type = 'd'
        GROUP BY box
        ORDER BY 文档数量 DESC
    """,

    "每日创建文档统计": """
        SELECT
            DATE(created/1000, 'unixepoch', 'localtime') as 日期,
            COUNT(*) as 创建文档数
        FROM blocks
        WHERE type = 'd'
        AND created > (strftime('%s', 'now', '-30 days') * 1000)
        GROUP BY DATE(created/1000, 'unixepoch', 'localtime')
        ORDER BY 日期 DESC
    """,

    "包含图片的文档": """
        SELECT DISTINCT
            b.content as 文档标题,
            b.hpath as 文档路径,
            COUNT(b2.id) as 图片块数量,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        JOIN blocks b2 ON b.root_id = b2.root_id
        WHERE b.type = 'd'
        AND b2.type = 'img'
        GROUP BY b.root_id
        ORDER BY 图片块数量 DESC, b.updated DESC
        LIMIT 500
    """,

    "代码块统计": """
        SELECT DISTINCT
            b.content as 文档标题,
            b.hpath as 文档路径,
            COUNT(b2.id) as 代码块数量,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        JOIN blocks b2 ON b.root_id = b2.root_id
        WHERE b.type = 'd'
        AND b2.type = 'c'
        GROUP BY b.root_id
        ORDER BY 代码块数量 DESC, b.updated DESC
        LIMIT 500
    """,

    "反向链接最多的文档": """
        SELECT
            b.content as 被引用文档,
            b.hpath as 文档路径,
            COUNT(r.id) as 被引用次数,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        JOIN refs r ON b.root_id = r.def_block_root_id
        WHERE b.type = 'd'
        GROUP BY b.root_id
        ORDER BY 被引用次数 DESC
        LIMIT 100
    """,

    "特定标签的文档": """
        SELECT DISTINCT
            b.root_id,
            b.content as 文档标题,
            s.content as 标签内容,
            s.markdown as 标签markdown格式,
            b.hpath as 文档路径,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        JOIN spans s ON b.root_id = s.root_id
        WHERE s.type = 'tag' OR s.type = 'textmark tag'
        AND s.content LIKE '%思源笔记%'
        AND b.type = 'd'
        ORDER BY b.updated DESC
        LIMIT 500
    """,

    "标签详细信息": """
        SELECT
            s.content as 标签名称,
            s.markdown as 标签markdown,
            b.content as 文档标题,
            b.hpath as 文档路径,
            s.block_id as 标签所在块ID,
            b2.content as 标签所在块内容,
            b2.type as 标签所在块类型,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 文档更新时间
        FROM spans s
        JOIN blocks b ON s.root_id = b.root_id AND b.type = 'd'
        JOIN blocks b2 ON s.block_id = b2.id
        WHERE s.type = 'tag' OR s.type = 'textmark tag'
        ORDER BY s.content, b.updated DESC
        LIMIT 1000
    """,

    "文档标签统计": """
        SELECT
            b.content as 文档标题,
            b.hpath as 文档路径,
            '[' || b.content || '](siyuan://blocks/' || b.root_id || ')' as 文档链接,
            COUNT(s.id) as 标签数量,
            GROUP_CONCAT(s.content, ', ') as 所有标签,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        JOIN spans s ON b.root_id = s.root_id
        WHERE b.type = 'd' AND (s.type = 'tag' OR s.type = 'textmark tag')
        GROUP BY b.root_id
        ORDER BY 标签数量 DESC
        LIMIT 200
    """,

    "自定义分类属性": """
        SELECT
            b.content as 文档标题,
            a.value as 分类标签,
            b.hpath as 文档路径,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        JOIN attributes a ON b.id = a.block_id
        WHERE a.name = 'custom-classify'
        AND b.type = 'd'
        ORDER BY a.value, b.updated DESC
        LIMIT 1000
    """
}


# 数据库表结构查询
TABLE_QUERIES = {
    "所有表列表": "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",

    "blocks表结构": "PRAGMA table_info(blocks)",
    "spans表结构": "PRAGMA table_info(spans)",
    "refs表结构": "PRAGMA table_info(refs)",
    "attributes表结构": "PRAGMA table_info(attributes)",

    "blocks表记录数": "SELECT COUNT(*) as 记录数 FROM blocks",
    "文档数量": "SELECT COUNT(*) as 文档数量 FROM blocks WHERE type = 'd'",
    "标签数量": "SELECT COUNT(*) as 标签数量 FROM spans WHERE type = 'tag' OR type = 'textmark tag'"
}


def get_query_by_name(query_name: str) -> str:
    """
    根据查询名称获取SQL语句

    :param query_name: 查询名称
    :return: SQL语句，如果不存在则返回空字符串
    """
    return COMMON_QUERIES.get(query_name, "")


def get_all_query_names() -> list:
    """
    获取所有可用的查询名称

    :return: 查询名称列表
    """
    return list(COMMON_QUERIES.keys())


def get_table_query_by_name(query_name: str) -> str:
    """
    根据查询名称获取表结构相关的SQL语句

    :param query_name: 查询名称
    :return: SQL语句，如果不存在则返回空字符串
    """
    return TABLE_QUERIES.get(query_name, "")


def get_all_table_query_names() -> list:
    """
    获取所有可用的表查询名称

    :return: 表查询名称列表
    """
    return list(TABLE_QUERIES.keys())


def get_specific_tag_query(tag_name: str) -> str:
    """
    生成查询特定标签文档的SQL语句

    :param tag_name: 标签名称
    :return: SQL查询语句
    """
    return f"""
        SELECT DISTINCT
            b.root_id,
            b.content as 文档标题,
            s.content as 标签内容,
            s.markdown as 标签markdown格式,
            b.hpath as 文档路径,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        JOIN spans s ON b.root_id = s.root_id
        WHERE s.type = 'tag' OR s.type = 'textmark tag'
        AND s.content LIKE '%{tag_name}%'
        AND b.type = 'd'
        ORDER BY b.updated DESC
        LIMIT 500
    """


def get_custom_attribute_query(attribute_name: str) -> str:
    """
    生成查询特定自定义属性的SQL语句

    :param attribute_name: 自定义属性名称（不需要custom-前缀）
    :return: SQL查询语句
    """
    return f"""
        SELECT
            b.content as 文档标题,
            a.value as 属性值,
            b.hpath as 文档路径,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        JOIN attributes a ON b.id = a.block_id
        WHERE a.name = 'custom-{attribute_name}'
        AND b.type = 'd'
        ORDER BY a.value, b.updated DESC
        LIMIT 1000
    """