# 思源笔记脚本工具集

这是一个用于操作思源笔记（SiYuan）的脚本工具集，主要用于批量处理笔记数据、元数据管理、内容导入导出等。

## 主要功能

### 📝 笔记导入与管理
- **Markdown文件导入**: `create_notes_from_md.py` - 将文件夹下的Markdown文件批量导入到思源笔记。
- **为知笔记导出**: `export_wiznotes_to_md.py` - 从为知笔记导出单篇或批量导出Markdown笔记。
- **为知笔记转思源**: `wiznotes_to_siyuan.py` - 完整流程：导出为知笔记 -> 导入思源笔记 -> 整理文件。
- **数据库查询导出**: `query_to_csv.py` - 执行SQL查询并将结果导出为CSV文件。

### 🌐 网页内容处理
- **URL转Markdown**: `urls_to_markdown.py` - 将网页内容批量转换为Markdown文件，支持媒体下载。
- **URL转思源**: `urls_to_siyuan.py` - 完整流程：剪贴板URL -> Markdown -> 思源笔记。
- **剪贴板笔记处理**: `clipboard_notes_mailto_wiznotes.py` - 从剪贴板提取文章链接，批量发送到为知笔记。
- **剪贴板HTML转换**: `clipboard_html_to_markdown.py` - 将剪贴板中的HTML内容直接转换为Markdown文件。
- **飞书链接智能处理**: 自动检测飞书链接并提取微信公众号原文链接，优先使用原文内容。
- **特殊网站处理**: 支持今日头条等网站的乱码修复，智能编码检测和压缩内容处理（gzip、deflate、brotli）。
- **JavaScript重定向支持**: 可选集成 Playwright 处理需要浏览器渲染的动态网站。

### 🏷️ 元数据管理
- **元数据添加**: `add_meta_data.py` - 为思源笔记文档添加元数据信息。
- **配置读取**: `read_siyuan_config.py` - 读取思源笔记配置，导出快捷键设置为Markdown表格。

### 📊 高级数据查询
- **SQL查询系统**: `utilities/advanced_sql_queries.py` - 提供22个实用的思源笔记数据库查询场景，包括：
  - 基础统计查询（文档总体统计、块类型分布、笔记本排行、标题层级分布）
  - 内容分析查询（字数统计、标签使用、引用关系、代码块分析）
  - 时间维度查询（创建时间分布、活跃文档、长期未更新、每日写作统计）
  - 高级查询（孤立文档检测、高价值文档识别、标签共现、引用网络）
  - 特殊用途查询（图片资源、数学公式、任务列表、表格使用、自定义属性）
- **查询演示**: `examples/advanced_query_demo.py` - 交互式查询演示脚本，支持分类浏览和关键词搜索。

### ⚙️ 配置管理系统
- **统一配置**: `config.py` - 统一的配置管理类，支持导出目录、思源笔记、为知笔记等各项配置。
- **配置管理工具**: `config_manager.py` - 命令行和交互式配置管理工具，支持配置的查看、修改、保存和加载。
- **配置文件**: `project_config.json` - JSON格式的配置文件，便于版本控制和分享。

### ☁️ 云存储管理
- **七牛云批量删除**: `delete_qiniu_files.py` - 七牛云同步文件批量删除工具，解决官网批量删除操作缓慢问题。详见 `七牛云文件批量删除使用说明.md`。

### 🛠️ 核心工具库
- **utilities模块**：提供统一的API客户端和管理器，包括：
  - 思源笔记API操作（SiyuanAPI、NotebookManager、DocumentManager、BlockManager）
  - Markdown导入器（MarkdownImporter）
  - 媒体文件管理（MediaManager、MediaDownloader）
  - 网页内容处理（WebDownloader、HTMLConverter）
  - 剪贴板管理（ClipboardManager）
  - 高级SQL查询（AdvancedSQLQueries）

## 安装要求

### 系统要求
- Python 3.7+
- 思源笔记客户端运行中（用于需要与思源交互的功能）

### 依赖包
首先，请通过以下命令安装所有必需的库：
```bash
pip install -r requirements.txt
```

主要依赖包括：
- `requests` - HTTP请求库
- `python-dotenv` - 环境变量管理
- `beautifulsoup4` - HTML解析
- `lxml` - XML/HTML解析器
- `html5lib` - HTML5解析器
- `markdownify` - HTML转Markdown
- `html2text` - HTML转文本
- `Pillow` - 图像处理
- `urllib3` - HTTP客户端
- `aiohttp` - 异步HTTP客户端
- `aiofiles` - 异步文件操作
- `qiniu` - 七牛云SDK
- `pyperclip` - 剪贴板操作
- `yagmail` - 邮件发送
- `brotli` - Brotli压缩支持
- `chardet` - 智能编码检测

**可选依赖**（用于处理JavaScript重定向网站）：
- `playwright` - 现代浏览器自动化与渲染（需安装浏览器内核）

## 快速开始

### 1. 基础配置

#### 环境变量配置
在项目根目录创建 `.env` 文件，并根据需要配置以下变量：

```env
# 思源笔记API配置
SIYUAN_API_URL=http://127.0.0.1:6806
SIYUAN_API_TOKEN=your_api_token_here

# 为知笔记配置（可选）
WIZ_USERNAME=your_username@example.com
WIZ_PASSWORD=your_password

# 七牛云配置（可选）
QINIU_ACCESS_KEY=your_access_key_here
QINIU_SECRET_KEY=your_secret_key_here
QINIU_BUCKET_NAME=your_bucket_name_here

# 邮件配置（可选）
MAIL_189_HOST=smtp.189.cn
MAIL_189_USER=your_email@189.cn
MAIL_189_PASSWORD=your_password
MAIL_RECEIVER=your_wiznote_email@mywiz.cn
```

#### 项目配置管理
本项目提供了统一的配置管理系统，支持通过配置文件管理导出目录、思源笔记设置等：

```bash
# 查看当前配置
python config_manager.py --show

# 交互式配置编辑
python config_manager.py --interactive

# 设置基础导出目录
python config_manager.py --base "D:/笔记备份"

# 保存配置到文件
python config_manager.py --save my_config.json

# 从文件加载配置
python config_manager.py --load my_config.json
```

详细配置说明请参考：`配置系统使用说明.md`

### 2. 获取思源API Token
1. 打开思源笔记客户端。
2. 进入 `设置` -> `关于`。
3. 在 `API Token` 处找到你的Token。
4. 复制并粘贴到 `.env` 文件中。

### 3. 运行脚本
根据你的需求执行相应的脚本。例如：

```bash
# 将剪贴板中的URL一键存入思源（支持飞书链接智能处理）
python urls_to_siyuan.py

# 将剪贴板中的HTML转换为Markdown
python clipboard_html_to_markdown.py

# 运行SQL查询演示
python examples/advanced_query_demo.py

# 演示飞书链接处理功能
python demo_feishu_feature.py

# 测试特殊网站处理功能
python test/test_toutiao_fix.py
```

## 新功能使用指南

### 🔍 高级SQL查询系统

本项目提供了22个实用的思源笔记数据库查询场景，帮助您深入分析笔记数据：

#### 基本使用
```python
from utilities.advanced_sql_queries import get_query_sql, get_all_query_names
from utilities.api_client import SiyuanAPI

# 获取所有查询名称
queries = get_all_query_names()
print(f"可用查询: {len(queries)}个")

# 获取特定查询的SQL
sql = get_query_sql("高价值文档识别")

# 执行查询
api = SiyuanAPI()
result = api.call_api('/api/query/sql', {'stmt': sql})
```

#### 参数化查询
```python
from utilities.advanced_sql_queries import (
    get_documents_by_tag,
    get_documents_by_custom_attribute,
    get_documents_by_date_range
)

# 查询包含"Python"标签的文档
sql = get_documents_by_tag("Python", 50)

# 查询分类为"技术"的文档
sql = get_documents_by_custom_attribute("classify", "技术", 100)

# 查询最近7天更新的文档
sql = get_documents_by_date_range("2024-07-20", "2024-07-27", "updated", 50)
```

#### 交互式查询演示
```bash
python examples/advanced_query_demo.py
```

详细使用指南请参考：`docs/思源笔记高级SQL查询使用指南.md`

### 🔗 飞书链接智能处理

本项目支持飞书链接的智能处理，自动提取微信公众号原文链接：

#### 功能特性
- **自动检测**：识别以 `https://waytoagi.feishu.cn/` 开头的飞书链接
- **智能提取**：在页面前10行中搜索微信公众号原文链接
- **优先原文**：找到原文链接时优先使用原文内容
- **回退机制**：未找到原文链接时使用飞书页面内容
- **格式兼容**：支持多种原文链接格式

#### 支持的原文链接格式
```
原文链接：https://mp.weixin.qq.com/s/abc123
原文链接:https://mp.weixin.qq.com/s/def456
原文链接： https://mp.weixin.qq.com/s/ghi789
原文链接 : https://mp.weixin.qq.com/s/jkl012
```

#### 使用方法
```bash
# 复制飞书链接到剪贴板，然后运行：
python urls_to_siyuan.py

# 或者只转换为Markdown：
python urls_to_markdown.py
```

详细说明请参考：`docs/飞书链接微信原文提取功能说明.md`

### 🛠️ 特殊网站处理

项目包含针对特殊网站的处理优化：

#### 编码和压缩处理
- **智能编码检测**：使用chardet自动检测字符编码
- **压缩内容支持**：自动处理gzip、deflate、brotli压缩格式
- **多编码尝试**：按优先级尝试UTF-8、GBK、GB2312等编码
- **HTML meta解析**：从页面meta标签提取编码信息

#### JavaScript重定向支持
对于需要浏览器渲染的网站（如今日头条），安装 Playwright：
```bash
pip install playwright
python -m playwright install chromium
```

#### 使用示例
```bash
# 处理今日头条等特殊网站（已自动优化）
python urls_to_siyuan.py

# 查看处理日志了解编码检测过程
```

详细说明请参考：`docs/今日头条乱码修复说明.md` 和 `docs/修复总结和使用指南.md`

### ⚙️ 配置管理系统

#### 命令行配置管理
```bash
# 查看当前配置
python config_manager.py --show

# 设置基础导出目录
python config_manager.py --base "D:/我的笔记备份"

# 设置子目录
python config_manager.py --subdir urls "网页收集"

# 保存配置
python config_manager.py --save my_config.json

# 测试路径配置
python config_manager.py --test
```

#### 程序中使用配置
```python
from config import get_config, get_wiznotes_path, get_urls_path

# 获取配置实例
config = get_config()

# 获取特定路径
wiznotes_path = get_wiznotes_path()
urls_path = get_urls_path()

# 使用配置值
notebook_name = config.siyuan["default_notebook"]
max_workers = config.wiznotes["max_workers"]
```

### 📋 剪贴板处理功能

#### HTML转Markdown
```bash
# 复制HTML内容到剪贴板，然后运行：
python clipboard_html_to_markdown.py
```

#### URL批量处理
```bash
# 复制多个URL到剪贴板（每行一个），然后运行：
python urls_to_markdown.py
python urls_to_siyuan.py
```

## 项目结构

```
siyuan_scripts/
├── docs/                        # 项目文档
│   ├── 思源笔记API.md
│   ├── 思源笔记数据库表与字段.md
│   ├── 思源笔记高级SQL查询使用指南.md
│   ├── 思源笔记SQL查询系统总结.md
│   ├── 配置系统使用说明.md
│   ├── 飞书链接微信原文提取功能说明.md
│   ├── 功能实现总结.md
│   ├── 今日头条乱码修复说明.md
│   ├── 修复总结和使用指南.md
│   └── 七牛云文件批量删除使用说明.md
├── examples/                    # 示例代码
│   ├── advanced_query_demo.py   # SQL查询演示脚本
│   └── siyuan_advanced_queries.json # 导出的查询数据
├── export_wiznotes/             # 为知笔记导出模块
│   ├── wiz_client.py           # 为知笔记客户端
│   ├── note_exporter.py        # 笔记导出器
│   ├── collaboration_parser.py # 协作笔记解析器
│   └── utils.py                # 工具函数
├── output/                      # 脚本输出目录
├── test/                        # 测试代码
│   ├── test_feishu_integration.py # 飞书功能集成测试
│   ├── test_feishu_wechat_extraction.py # 飞书微信链接提取测试
│   ├── test_toutiao_fix.py     # 今日头条修复测试
│   └── ... (其他测试文件)
├── utilities/                   # 核心功能工具库
│   ├── api_client.py           # 思源API客户端
│   ├── advanced_sql_queries.py # 高级SQL查询模块
│   ├── url_to_markdown.py      # URL转Markdown转换器
│   ├── web_downloader.py       # 网页下载器
│   ├── html_converter.py       # HTML转换器
│   ├── media_downloader.py     # 媒体下载器
│   ├── clipboard_manager.py    # 剪贴板管理
│   ├── special_site_handler.py # 特殊网站处理器
│   ├── markdown_importer.py    # Markdown导入器
│   ├── media_manager.py        # 媒体管理器
│   └── ... (其他工具模块)
├── add_meta_data.py             # 添加元数据
├── api_test.ipynb               # API测试Jupyter Notebook
├── clipboard_html_to_markdown.py # 剪贴板HTML转Markdown
├── clipboard_notes_mailto_wiznotes.py # 剪贴板内容发送至为知
├── config.py                    # 配置管理类
├── config_manager.py            # 配置管理工具
├── create_notes_from_md.py      # 从MD文件创建笔记
├── delete_qiniu_files.py        # 删除七牛云文件
├── demo_feishu_feature.py       # 飞书功能演示脚本
├── export_wiznotes_to_md.py     # 导出为知笔记为MD
├── project_config.json          # 项目配置文件
├── query_to_csv.py              # 查询并导出为CSV
├── read_siyuan_config.py        # 读取思源配置
├── README.md                    # 本文档
├── requirements.txt             # Python依赖
├── siyuan_advanced_queries.json # SQL查询数据导出
├── urls_to_markdown.py          # 网址转Markdown
├── urls_to_siyuan.py            # 网址转思源笔记
└── wiznotes_to_siyuan.py        # 为知笔记迁移到思源
```

## 📚 相关文档

项目包含详细的使用文档和说明：

### 核心功能文档
- **`docs/思源笔记高级SQL查询使用指南.md`** - SQL查询系统完整使用指南，包含所有22个查询场景的详细说明
- **`docs/思源笔记SQL查询系统总结.md`** - SQL查询系统的项目总结和核心特性介绍
- **`docs/配置系统使用说明.md`** - 配置管理系统的详细使用说明，包含命令行和程序接口
- **`docs/思源笔记API.md`** - 思源笔记API接口文档
- **`docs/思源笔记数据库表与字段.md`** - 思源笔记数据库结构说明

### 新功能文档
- **`docs/飞书链接微信原文提取功能说明.md`** - 飞书链接智能处理功能的详细使用指南
- **`docs/功能实现总结.md`** - 飞书链接功能的实现总结和技术细节
- **`docs/今日头条乱码修复说明.md`** - 今日头条等网站乱码问题的修复说明
- **`docs/修复总结和使用指南.md`** - 编码检测和压缩处理功能的综合使用指南

### 工具使用文档
- **`docs/七牛云文件批量删除使用说明.md`** - 七牛云文件批量删除工具的使用说明

## 安全提醒
- **数据备份**: 在执行任何可能修改数据的脚本前，请务必备份你的思源笔记数据。
- **凭证安全**: 妥善保管你的 `.env` 文件，不要将包含敏感信息（如API Token、密码）的文件提交到公共代码库。
- **删除操作**: `delete_qiniu_files.py` 会永久删除云端文件，请在确认无误后再执行。

---

**注意**：此工具集主要用于个人笔记管理和数据迁移，请遵守相关服务的使用条款。
