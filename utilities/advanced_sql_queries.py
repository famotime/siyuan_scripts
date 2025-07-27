"""
思源笔记高级SQL查询场景集合
包含20-30个实用的笔记数据查询和统计场景

本模块提供以下查询分类：
1. 基础统计 - 文档数量、块类型分布、笔记本统计等
2. 内容分析 - 字数统计、标签使用情况、引用关系等
3. 时间维度 - 创建/更新时间分析、活跃度统计等
4. 高级查询 - 复杂关联查询、数据挖掘类查询等

使用说明：
- 所有时间字段使用 datetime(时间戳/1000, 'unixepoch', 'localtime') 格式化
- 查询结果包含中文字段别名，便于理解
- 添加适当的 LIMIT 限制，避免查询结果过大
- 特殊查询提供参数化版本，便于程序调用
"""

# ==================== 基础统计查询 ====================

BASIC_STATS_QUERIES = {
    "文档总体统计": {
        "description": "统计所有文档的基本信息，包括数量、平均字数等",
        "application": "了解笔记库的整体规模和内容分布",
        "sql": """
            SELECT
                COUNT(*) as 文档总数,
                AVG(length) as 平均字数,
                MAX(length) as 最长文档字数,
                MIN(length) as 最短文档字数,
                COUNT(DISTINCT box) as 笔记本数量,
                datetime(MIN(created)/1000, 'unixepoch', 'localtime') as 最早创建时间,
                datetime(MAX(updated)/1000, 'unixepoch', 'localtime') as 最近更新时间
            FROM blocks
            WHERE type = 'd'
        """,
        "expected_result": "返回文档总数、平均字数、笔记本数量等基础统计信息"
    },

    "块类型分布统计": {
        "description": "统计各种块类型的数量分布",
        "application": "了解笔记内容的结构特点，如标题、段落、列表等的使用情况",
        "sql": """
            SELECT
                type as 块类型,
                CASE
                    WHEN type = 'd' THEN '文档块'
                    WHEN type = 'h' THEN '标题块'
                    WHEN type = 'p' THEN '段落块'
                    WHEN type = 'l' THEN '列表块'
                    WHEN type = 'i' THEN '列表项块'
                    WHEN type = 'c' THEN '代码块'
                    WHEN type = 't' THEN '表格块'
                    WHEN type = 'b' THEN '引述块'
                    WHEN type = 's' THEN '超级块'
                    WHEN type = 'm' THEN '数学公式块'
                    ELSE '其他'
                END as 块类型说明,
                COUNT(*) as 数量,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM blocks), 2) as 占比百分比
            FROM blocks
            GROUP BY type
            ORDER BY 数量 DESC
        """,
        "expected_result": "返回各种块类型的数量和占比，帮助了解笔记结构特点"
    },

    "笔记本统计排行": {
        "description": "统计各笔记本的文档数量、总字数等信息",
        "application": "了解各笔记本的使用情况，识别最活跃的笔记本",
        "sql": """
            SELECT
                box as 笔记本ID,
                COUNT(*) as 文档数量,
                SUM(length) as 总字数,
                AVG(length) as 平均字数,
                datetime(MIN(created)/1000, 'unixepoch', 'localtime') as 最早文档创建时间,
                datetime(MAX(updated)/1000, 'unixepoch', 'localtime') as 最近更新时间
            FROM blocks
            WHERE type = 'd'
            GROUP BY box
            ORDER BY 文档数量 DESC
            LIMIT 20
        """,
        "expected_result": "返回各笔记本的文档统计信息，按文档数量排序"
    },

    "标题层级分布": {
        "description": "统计各级标题的使用情况",
        "application": "了解文档结构的层次性，优化文档组织方式",
        "sql": """
            SELECT
                subtype as 标题级别,
                CASE
                    WHEN subtype = 'h1' THEN '一级标题'
                    WHEN subtype = 'h2' THEN '二级标题'
                    WHEN subtype = 'h3' THEN '三级标题'
                    WHEN subtype = 'h4' THEN '四级标题'
                    WHEN subtype = 'h5' THEN '五级标题'
                    WHEN subtype = 'h6' THEN '六级标题'
                    ELSE '其他'
                END as 标题类型,
                COUNT(*) as 使用次数,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM blocks WHERE type = 'h'), 2) as 占比百分比
            FROM blocks
            WHERE type = 'h'
            GROUP BY subtype
            ORDER BY 使用次数 DESC
        """,
        "expected_result": "返回各级标题的使用统计，了解文档结构层次"
    }
}

# ==================== 内容分析查询 ====================

CONTENT_ANALYSIS_QUERIES = {
    "字数统计排行": {
        "description": "按字数统计文档，找出最长和最短的文档",
        "application": "识别内容丰富的重要文档和需要完善的简短文档",
        "sql": """
            SELECT
                content as 文档标题,
                hpath as 文档路径,
                length as 字数,
                '[' || content || '](siyuan://blocks/' || id || ')' as 文档链接,
                datetime(created/1000, 'unixepoch', 'localtime') as 创建时间,
                datetime(updated/1000, 'unixepoch', 'localtime') as 更新时间
            FROM blocks
            WHERE type = 'd' AND length > 0
            ORDER BY length DESC
            LIMIT 50
        """,
        "expected_result": "返回按字数排序的文档列表，包含文档链接便于快速访问"
    },

    "标签使用统计": {
        "description": "统计所有标签的使用频率",
        "application": "了解标签体系的使用情况，优化标签管理",
        "sql": """
            SELECT
                content as 标签名称,
                COUNT(*) as 使用次数,
                COUNT(DISTINCT root_id) as 涉及文档数,
                ROUND(COUNT(DISTINCT root_id) * 100.0 / (SELECT COUNT(DISTINCT root_id) FROM blocks WHERE type = 'd'), 2) as 文档覆盖率百分比
            FROM spans
            WHERE type = 'tag' OR type = 'textmark tag'
            GROUP BY content
            ORDER BY 使用次数 DESC
            LIMIT 100
        """,
        "expected_result": "返回标签使用统计，包括使用次数和文档覆盖率"
    },

    "引用关系分析": {
        "description": "分析文档间的引用关系，找出核心文档",
        "application": "识别知识网络中的关键节点，了解文档重要性",
        "sql": """
            SELECT
                b.content as 被引用文档,
                b.hpath as 文档路径,
                COUNT(r.id) as 被引用次数,
                COUNT(DISTINCT r.root_id) as 引用来源文档数,
                '[' || b.content || '](siyuan://blocks/' || b.id || ')' as 文档链接,
                datetime(b.updated/1000, 'unixepoch', 'localtime') as 最近更新时间
            FROM blocks b
            JOIN refs r ON b.id = r.def_block_id
            WHERE b.type = 'd'
            GROUP BY b.id
            ORDER BY 被引用次数 DESC
            LIMIT 50
        """,
        "expected_result": "返回被引用最多的文档，体现文档在知识网络中的重要性"
    },

    "代码块统计分析": {
        "description": "统计代码块的使用情况和编程语言分布",
        "application": "了解技术文档的编程语言偏好和代码使用情况",
        "sql": """
            SELECT
                CASE
                    WHEN ial LIKE '%data-subtype="python"%' THEN 'Python'
                    WHEN ial LIKE '%data-subtype="javascript"%' THEN 'JavaScript'
                    WHEN ial LIKE '%data-subtype="sql"%' THEN 'SQL'
                    WHEN ial LIKE '%data-subtype="java"%' THEN 'Java'
                    WHEN ial LIKE '%data-subtype="cpp"%' THEN 'C++'
                    WHEN ial LIKE '%data-subtype="go"%' THEN 'Go'
                    WHEN ial LIKE '%data-subtype="rust"%' THEN 'Rust'
                    ELSE '其他/未指定'
                END as 编程语言,
                COUNT(*) as 代码块数量,
                COUNT(DISTINCT root_id) as 涉及文档数,
                AVG(length) as 平均代码长度
            FROM blocks
            WHERE type = 'c'
            GROUP BY 编程语言
            ORDER BY 代码块数量 DESC
        """,
        "expected_result": "返回各编程语言的代码块统计，了解技术栈使用情况"
    }
}

# ==================== 时间维度查询 ====================

TIME_ANALYSIS_QUERIES = {
    "创建时间分布": {
        "description": "按月份统计文档创建情况",
        "application": "了解笔记创建的时间规律，分析写作习惯",
        "sql": """
            SELECT
                strftime('%Y-%m', datetime(created/1000, 'unixepoch', 'localtime')) as 创建月份,
                COUNT(*) as 文档数量,
                SUM(length) as 总字数,
                AVG(length) as 平均字数
            FROM blocks
            WHERE type = 'd'
            GROUP BY 创建月份
            ORDER BY 创建月份 DESC
            LIMIT 24
        """,
        "expected_result": "返回按月份的文档创建统计，了解写作活跃度变化"
    },

    "最近活跃文档": {
        "description": "查找最近更新的活跃文档",
        "application": "快速找到正在编辑的文档，继续工作",
        "sql": """
            SELECT
                content as 文档标题,
                hpath as 文档路径,
                '[' || content || '](siyuan://blocks/' || id || ')' as 文档链接,
                datetime(created/1000, 'unixepoch', 'localtime') as 创建时间,
                datetime(updated/1000, 'unixepoch', 'localtime') as 更新时间,
                ROUND((julianday('now') - julianday(datetime(updated/1000, 'unixepoch', 'localtime'))), 1) as 距今天数
            FROM blocks
            WHERE type = 'd'
            ORDER BY updated DESC
            LIMIT 30
        """,
        "expected_result": "返回最近更新的文档列表，便于继续编辑工作"
    },

    "长期未更新文档": {
        "description": "查找长时间未更新的文档",
        "application": "识别可能需要更新或归档的旧文档",
        "sql": """
            SELECT
                content as 文档标题,
                hpath as 文档路径,
                '[' || content || '](siyuan://blocks/' || id || ')' as 文档链接,
                datetime(created/1000, 'unixepoch', 'localtime') as 创建时间,
                datetime(updated/1000, 'unixepoch', 'localtime') as 最后更新时间,
                ROUND((julianday('now') - julianday(datetime(updated/1000, 'unixepoch', 'localtime'))), 0) as 未更新天数
            FROM blocks
            WHERE type = 'd'
            AND datetime(updated/1000, 'unixepoch', 'localtime') < datetime('now', '-90 days')
            ORDER BY updated ASC
            LIMIT 50
        """,
        "expected_result": "返回长期未更新的文档，帮助识别需要维护的内容"
    },

    "每日写作统计": {
        "description": "按日期统计文档创建和更新情况",
        "application": "分析每日写作习惯，制定写作计划",
        "sql": """
            SELECT
                date(datetime(created/1000, 'unixepoch', 'localtime')) as 日期,
                COUNT(*) as 创建文档数,
                SUM(length) as 创建总字数,
                COUNT(CASE WHEN date(datetime(created/1000, 'unixepoch', 'localtime')) =
                           date(datetime(updated/1000, 'unixepoch', 'localtime')) THEN 1 END) as 当日完成文档数
            FROM blocks
            WHERE type = 'd'
            AND datetime(created/1000, 'unixepoch', 'localtime') >= datetime('now', '-30 days')
            GROUP BY 日期
            ORDER BY 日期 DESC
        """,
        "expected_result": "返回最近30天的每日写作统计，了解写作规律"
    }
}

# ==================== 高级查询 ====================

ADVANCED_QUERIES = {
    "孤立文档检测": {
        "description": "查找没有任何引用关系的孤立文档",
        "application": "识别缺乏关联的文档，改善知识网络连接",
        "sql": """
            SELECT
                b.content as 文档标题,
                b.hpath as 文档路径,
                '[' || b.content || '](siyuan://blocks/' || b.id || ')' as 文档链接,
                b.length as 字数,
                datetime(b.created/1000, 'unixepoch', 'localtime') as 创建时间,
                datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
            FROM blocks b
            WHERE b.type = 'd'
            AND b.id NOT IN (SELECT DISTINCT def_block_root_id FROM refs WHERE def_block_root_id IS NOT NULL)
            AND b.id NOT IN (SELECT DISTINCT root_id FROM refs WHERE root_id IS NOT NULL)
            ORDER BY b.updated DESC
            LIMIT 100
        """,
        "expected_result": "返回没有引用关系的孤立文档，便于建立知识连接"
    },

    "高价值文档识别": {
        "description": "综合字数、引用数、标签数等指标识别高价值文档",
        "application": "快速定位重要的核心文档，优先维护和完善",
        "sql": """
            SELECT
                b.content as 文档标题,
                b.hpath as 文档路径,
                '[' || b.content || '](siyuan://blocks/' || b.id || ')' as 文档链接,
                b.length as 字数,
                COALESCE(ref_count.引用次数, 0) as 被引用次数,
                COALESCE(tag_count.标签数量, 0) as 标签数量,
                COALESCE(attr_count.属性数量, 0) as 自定义属性数量,
                (b.length * 0.3 + COALESCE(ref_count.引用次数, 0) * 10 + COALESCE(tag_count.标签数量, 0) * 5) as 综合评分,
                datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
            FROM blocks b
            LEFT JOIN (
                SELECT def_block_root_id, COUNT(*) as 引用次数
                FROM refs
                GROUP BY def_block_root_id
            ) ref_count ON b.id = ref_count.def_block_root_id
            LEFT JOIN (
                SELECT root_id, COUNT(*) as 标签数量
                FROM spans
                WHERE type = 'tag' OR type = 'textmark tag'
                GROUP BY root_id
            ) tag_count ON b.id = tag_count.root_id
            LEFT JOIN (
                SELECT root_id, COUNT(*) as 属性数量
                FROM attributes
                WHERE name LIKE 'custom-%'
                GROUP BY root_id
            ) attr_count ON b.id = attr_count.root_id
            WHERE b.type = 'd'
            ORDER BY 综合评分 DESC
            LIMIT 50
        """,
        "expected_result": "返回按综合评分排序的高价值文档列表"
    },

    "标签共现分析": {
        "description": "分析经常一起出现的标签组合",
        "application": "了解标签使用模式，优化标签体系设计",
        "sql": """
            SELECT
                s1.content as 标签1,
                s2.content as 标签2,
                COUNT(*) as 共现次数,
                COUNT(DISTINCT s1.root_id) as 涉及文档数
            FROM spans s1
            JOIN spans s2 ON s1.root_id = s2.root_id AND s1.id < s2.id
            WHERE (s1.type = 'tag' OR s1.type = 'textmark tag')
            AND (s2.type = 'tag' OR s2.type = 'textmark tag')
            AND s1.content != s2.content
            GROUP BY s1.content, s2.content
            HAVING 共现次数 >= 3
            ORDER BY 共现次数 DESC
            LIMIT 50
        """,
        "expected_result": "返回经常一起出现的标签组合，了解标签关联模式"
    },

    "引用网络深度分析": {
        "description": "分析文档的引用深度和广度",
        "application": "了解知识网络的复杂度和文档间的关联强度",
        "sql": """
            SELECT
                b.content as 文档标题,
                b.hpath as 文档路径,
                '[' || b.content || '](siyuan://blocks/' || b.id || ')' as 文档链接,
                COALESCE(outgoing.出链数量, 0) as 引用其他文档数,
                COALESCE(incoming.入链数量, 0) as 被其他文档引用数,
                COALESCE(outgoing.出链数量, 0) + COALESCE(incoming.入链数量, 0) as 总引用关系数,
                CASE
                    WHEN COALESCE(outgoing.出链数量, 0) > 10 AND COALESCE(incoming.入链数量, 0) > 5 THEN '核心枢纽'
                    WHEN COALESCE(incoming.入链数量, 0) > 10 THEN '权威文档'
                    WHEN COALESCE(outgoing.出链数量, 0) > 10 THEN '索引文档'
                    ELSE '普通文档'
                END as 文档类型,
                datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
            FROM blocks b
            LEFT JOIN (
                SELECT root_id, COUNT(DISTINCT def_block_root_id) as 出链数量
                FROM refs
                GROUP BY root_id
            ) outgoing ON b.id = outgoing.root_id
            LEFT JOIN (
                SELECT def_block_root_id, COUNT(DISTINCT root_id) as 入链数量
                FROM refs
                GROUP BY def_block_root_id
            ) incoming ON b.id = incoming.def_block_root_id
            WHERE b.type = 'd'
            AND (COALESCE(outgoing.出链数量, 0) > 0 OR COALESCE(incoming.入链数量, 0) > 0)
            ORDER BY 总引用关系数 DESC
            LIMIT 100
        """,
        "expected_result": "返回文档的引用网络分析，识别不同类型的文档角色"
    },

    "内容相似度分析": {
        "description": "基于标签和引用找出内容相似的文档",
        "application": "发现重复或相关内容，便于整合和去重",
        "sql": """
            SELECT
                b1.content as 文档1,
                b2.content as 文档2,
                b1.hpath as 文档1路径,
                b2.hpath as 文档2路径,
                '[' || b1.content || '](siyuan://blocks/' || b1.id || ')' as 文档1链接,
                '[' || b2.content || '](siyuan://blocks/' || b2.id || ')' as 文档2链接,
                COUNT(*) as 共同标签数,
                datetime(b1.updated/1000, 'unixepoch', 'localtime') as 文档1更新时间,
                datetime(b2.updated/1000, 'unixepoch', 'localtime') as 文档2更新时间
            FROM blocks b1
            JOIN spans s1 ON b1.id = s1.root_id
            JOIN spans s2 ON s1.content = s2.content
            JOIN blocks b2 ON s2.root_id = b2.id
            WHERE b1.type = 'd' AND b2.type = 'd'
            AND b1.id < b2.id
            AND (s1.type = 'tag' OR s1.type = 'textmark tag')
            AND (s2.type = 'tag' OR s2.type = 'textmark tag')
            GROUP BY b1.id, b2.id
            HAVING 共同标签数 >= 3
            ORDER BY 共同标签数 DESC
            LIMIT 50
        """,
        "expected_result": "返回具有相似标签的文档对，便于发现相关内容"
    }
}

# ==================== 特殊用途查询 ====================

SPECIAL_PURPOSE_QUERIES = {
    "图片资源统计": {
        "description": "统计文档中的图片使用情况",
        "application": "了解图片资源分布，管理媒体文件",
        "sql": """
            SELECT
                b.content as 文档标题,
                b.hpath as 文档路径,
                COUNT(s.id) as 图片数量,
                GROUP_CONCAT(SUBSTR(s.markdown, 1, 50), '; ') as 图片列表预览,
                '[' || b.content || '](siyuan://blocks/' || b.id || ')' as 文档链接,
                datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
            FROM blocks b
            JOIN spans s ON b.id = s.root_id
            WHERE s.type = 'img' AND b.type = 'd'
            GROUP BY b.id
            ORDER BY 图片数量 DESC
            LIMIT 50
        """,
        "expected_result": "返回包含图片最多的文档列表，便于媒体资源管理"
    },

    "数学公式使用统计": {
        "description": "统计数学公式块和行内公式的使用情况",
        "application": "了解数学内容的分布，适用于学术和技术文档",
        "sql": """
            SELECT
                b.content as 文档标题,
                b.hpath as 文档路径,
                COUNT(CASE WHEN blocks.type = 'm' THEN 1 END) as 数学公式块数量,
                COUNT(CASE WHEN s.type = 'textmark inline-math' THEN 1 END) as 行内公式数量,
                COUNT(CASE WHEN blocks.type = 'm' THEN 1 END) +
                COUNT(CASE WHEN s.type = 'textmark inline-math' THEN 1 END) as 总公式数量,
                '[' || b.content || '](siyuan://blocks/' || b.id || ')' as 文档链接,
                datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
            FROM blocks b
            LEFT JOIN blocks ON b.id = blocks.root_id AND blocks.type = 'm'
            LEFT JOIN spans s ON b.id = s.root_id AND s.type = 'textmark inline-math'
            WHERE b.type = 'd'
            GROUP BY b.id
            HAVING 总公式数量 > 0
            ORDER BY 总公式数量 DESC
            LIMIT 50
        """,
        "expected_result": "返回包含数学公式的文档统计，便于学术内容管理"
    },

    "任务列表统计": {
        "description": "统计任务列表的完成情况",
        "application": "跟踪待办事项和任务完成进度",
        "sql": """
            SELECT
                b.content as 文档标题,
                b.hpath as 文档路径,
                COUNT(CASE WHEN blocks.subtype = 't' AND blocks.ial LIKE '%data-task="true"%' THEN 1 END) as 总任务数,
                COUNT(CASE WHEN blocks.subtype = 't' AND blocks.ial LIKE '%data-task="true"%'
                           AND blocks.ial NOT LIKE '%data-task="false"%' THEN 1 END) as 已完成任务数,
                ROUND(
                    COUNT(CASE WHEN blocks.subtype = 't' AND blocks.ial LIKE '%data-task="true"%'
                               AND blocks.ial NOT LIKE '%data-task="false"%' THEN 1 END) * 100.0 /
                    NULLIF(COUNT(CASE WHEN blocks.subtype = 't' AND blocks.ial LIKE '%data-task="true"%' THEN 1 END), 0),
                    2
                ) as 完成率百分比,
                '[' || b.content || '](siyuan://blocks/' || b.id || ')' as 文档链接,
                datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
            FROM blocks b
            LEFT JOIN blocks ON b.id = blocks.root_id AND blocks.type = 'i' AND blocks.subtype = 't'
            WHERE b.type = 'd'
            GROUP BY b.id
            HAVING 总任务数 > 0
            ORDER BY 总任务数 DESC
            LIMIT 50
        """,
        "expected_result": "返回包含任务列表的文档及其完成情况统计"
    },

    "表格使用统计": {
        "description": "统计文档中表格的使用情况",
        "application": "了解结构化数据的使用情况，便于数据管理",
        "sql": """
            SELECT
                b.content as 文档标题,
                b.hpath as 文档路径,
                COUNT(blocks.id) as 表格数量,
                AVG(blocks.length) as 平均表格大小,
                '[' || b.content || '](siyuan://blocks/' || b.id || ')' as 文档链接,
                datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
            FROM blocks b
            JOIN blocks ON b.id = blocks.root_id AND blocks.type = 't'
            WHERE b.type = 'd'
            GROUP BY b.id
            ORDER BY 表格数量 DESC
            LIMIT 50
        """,
        "expected_result": "返回包含表格最多的文档列表，便于结构化数据管理"
    },

    "自定义属性分布": {
        "description": "统计各种自定义属性的使用情况",
        "application": "了解自定义属性体系的使用分布，优化属性管理",
        "sql": """
            SELECT
                REPLACE(a.name, 'custom-', '') as 自定义属性名,
                COUNT(*) as 使用次数,
                COUNT(DISTINCT a.root_id) as 涉及文档数,
                COUNT(DISTINCT a.value) as 不同值数量,
                GROUP_CONCAT(DISTINCT a.value LIMIT 10) as 值示例
            FROM attributes a
            WHERE a.name LIKE 'custom-%'
            GROUP BY a.name
            ORDER BY 使用次数 DESC
        """,
        "expected_result": "返回自定义属性的使用统计，了解属性体系分布"
    }
}

# ==================== 参数化查询模板 ====================

def get_documents_by_tag(tag_name: str, limit: int = 50) -> str:
    """
    生成查询特定标签文档的SQL语句

    :param tag_name: 标签名称
    :param limit: 结果数量限制
    :return: SQL查询语句
    """
    return f"""
        SELECT DISTINCT
            b.content as 文档标题,
            b.hpath as 文档路径,
            '[' || b.content || '](siyuan://blocks/' || b.id || ')' as 文档链接,
            s.content as 标签内容,
            s.markdown as 标签markdown格式,
            datetime(b.created/1000, 'unixepoch', 'localtime') as 创建时间,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        JOIN spans s ON b.id = s.root_id
        WHERE (s.type = 'tag' OR s.type = 'textmark tag')
        AND s.content LIKE '%{tag_name}%'
        AND b.type = 'd'
        ORDER BY b.updated DESC
        LIMIT {limit}
    """

def get_documents_by_custom_attribute(attribute_name: str, attribute_value: str = None, limit: int = 100) -> str:
    """
    生成查询特定自定义属性文档的SQL语句

    :param attribute_name: 自定义属性名称（不需要custom-前缀）
    :param attribute_value: 属性值（可选，为None时查询所有值）
    :param limit: 结果数量限制
    :return: SQL查询语句
    """
    value_condition = f"AND a.value = '{attribute_value}'" if attribute_value else ""

    return f"""
        SELECT
            b.content as 文档标题,
            b.hpath as 文档路径,
            '[' || b.content || '](siyuan://blocks/' || b.id || ')' as 文档链接,
            a.value as 属性值,
            datetime(b.created/1000, 'unixepoch', 'localtime') as 创建时间,
            datetime(b.updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks b
        JOIN attributes a ON b.id = a.block_id
        WHERE a.name = 'custom-{attribute_name}'
        {value_condition}
        AND b.type = 'd'
        ORDER BY a.value, b.updated DESC
        LIMIT {limit}
    """

def get_documents_by_date_range(start_date: str, end_date: str, date_type: str = 'updated', limit: int = 100) -> str:
    """
    生成查询指定日期范围内文档的SQL语句

    :param start_date: 开始日期 (YYYY-MM-DD格式)
    :param end_date: 结束日期 (YYYY-MM-DD格式)
    :param date_type: 日期类型 ('created' 或 'updated')
    :param limit: 结果数量限制
    :return: SQL查询语句
    """
    return f"""
        SELECT
            content as 文档标题,
            hpath as 文档路径,
            '[' || content || '](siyuan://blocks/' || id || ')' as 文档链接,
            length as 字数,
            datetime(created/1000, 'unixepoch', 'localtime') as 创建时间,
            datetime(updated/1000, 'unixepoch', 'localtime') as 更新时间
        FROM blocks
        WHERE type = 'd'
        AND date(datetime({date_type}/1000, 'unixepoch', 'localtime')) BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY {date_type} DESC
        LIMIT {limit}
    """

# ==================== 查询管理和工具函数 ====================

# 合并所有查询字典
ALL_QUERIES = {
    **BASIC_STATS_QUERIES,
    **CONTENT_ANALYSIS_QUERIES,
    **TIME_ANALYSIS_QUERIES,
    **ADVANCED_QUERIES,
    **SPECIAL_PURPOSE_QUERIES
}

def get_all_query_categories() -> dict:
    """
    获取所有查询分类

    :return: 查询分类字典
    """
    return {
        "基础统计": BASIC_STATS_QUERIES,
        "内容分析": CONTENT_ANALYSIS_QUERIES,
        "时间维度": TIME_ANALYSIS_QUERIES,
        "高级查询": ADVANCED_QUERIES,
        "特殊用途": SPECIAL_PURPOSE_QUERIES
    }

def get_query_by_name(query_name: str) -> dict:
    """
    根据查询名称获取查询信息

    :param query_name: 查询名称
    :return: 查询信息字典，包含description、application、sql、expected_result
    """
    return ALL_QUERIES.get(query_name, {})

def get_query_sql(query_name: str) -> str:
    """
    根据查询名称获取SQL语句

    :param query_name: 查询名称
    :return: SQL语句，如果不存在则返回空字符串
    """
    query_info = get_query_by_name(query_name)
    return query_info.get('sql', '').strip()

def get_all_query_names() -> list:
    """
    获取所有可用的查询名称

    :return: 查询名称列表
    """
    return list(ALL_QUERIES.keys())

def search_queries_by_keyword(keyword: str) -> list:
    """
    根据关键词搜索相关查询

    :param keyword: 搜索关键词
    :return: 匹配的查询名称列表
    """
    matching_queries = []
    keyword_lower = keyword.lower()

    for name, info in ALL_QUERIES.items():
        if (keyword_lower in name.lower() or
            keyword_lower in info.get('description', '').lower() or
            keyword_lower in info.get('application', '').lower()):
            matching_queries.append(name)

    return matching_queries

def get_queries_by_category(category: str) -> dict:
    """
    根据分类获取查询

    :param category: 查询分类名称
    :return: 该分类下的所有查询
    """
    categories = get_all_query_categories()
    return categories.get(category, {})

def format_query_info(query_name: str) -> str:
    """
    格式化查询信息为可读文本

    :param query_name: 查询名称
    :return: 格式化的查询信息
    """
    query_info = get_query_by_name(query_name)
    if not query_info:
        return f"查询 '{query_name}' 不存在"

    return f"""
查询名称: {query_name}
描述: {query_info.get('description', '无描述')}
应用场景: {query_info.get('application', '无应用场景说明')}
预期结果: {query_info.get('expected_result', '无结果说明')}

SQL语句:
{query_info.get('sql', '无SQL语句').strip()}
    """.strip()

def export_all_queries_to_dict() -> dict:
    """
    导出所有查询为字典格式，便于程序调用

    :return: 包含所有查询的字典
    """
    return {
        "metadata": {
            "total_queries": len(ALL_QUERIES),
            "categories": list(get_all_query_categories().keys()),
            "description": "思源笔记高级SQL查询场景集合"
        },
        "categories": get_all_query_categories(),
        "all_queries": ALL_QUERIES,
        "parameterized_functions": {
            "get_documents_by_tag": "根据标签查询文档",
            "get_documents_by_custom_attribute": "根据自定义属性查询文档",
            "get_documents_by_date_range": "根据日期范围查询文档"
        }
    }

# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例：获取所有查询名称
    print("所有可用查询:")
    for i, name in enumerate(get_all_query_names(), 1):
        print(f"{i}. {name}")

    print("\n" + "="*50)

    # 示例：搜索包含"标签"的查询
    tag_queries = search_queries_by_keyword("标签")
    print(f"包含'标签'的查询: {tag_queries}")

    print("\n" + "="*50)

    # 示例：获取特定查询的详细信息
    if tag_queries:
        query_name = tag_queries[0]
        print(format_query_info(query_name))

    print("\n" + "="*50)

    # 示例：参数化查询
    print("参数化查询示例:")
    print("查询包含'Python'标签的文档:")
    print(get_documents_by_tag("Python", 20))

    print("\n查询自定义分类属性为'技术'的文档:")
    print(get_documents_by_custom_attribute("classify", "技术", 30))
