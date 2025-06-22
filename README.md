# 思源笔记脚本工具集

这是一个用于操作思源笔记（SiYuan）的Python脚本工具集，主要用于批量处理笔记数据和元数据管理。

## 新增功能 🆕

### 七牛云批量删除工具 (delete_qiniu_files.py)

新增了七牛云文件批量删除功能，支持：

- **获取文件列表**：支持按前缀过滤和分页获取
- **批量删除文件**：支持分批处理大量文件
- **按前缀删除**：删除指定前缀的所有文件
- **安全确认机制**：防止误删除操作
- **详细日志记录**：完整的操作日志和错误处理

### URL到Markdown转换器 (url2markdown.py)

新增了高级的Web页面到Markdown转换功能，支持：

- **多种转换库支持**：markdownify、html2text、内置转换器
- **媒体文件下载**：自动下载并保存图片、视频、音频文件到本地
- **智能内容提取**：自动识别页面主要内容区域
- **异步并发处理**：支持批量转换和媒体文件并发下载
- **丰富的元数据**：提取页面标题、描述、作者、发布时间等信息

## 安装要求

### 系统要求
- Python 3.7+
- 思源笔记客户端运行中（用于思源相关功能）

### 依赖包
```bash
pip install -r requirements.txt
```

主要依赖：
- `requests`：HTTP请求库
- `python-dotenv`：环境变量管理
- `beautifulsoup4`：HTML解析
- `markdownify`：HTML到Markdown转换
- `html2text`：另一个HTML到Markdown转换库
- `aiohttp`：异步HTTP客户端
- `aiofiles`：异步文件操作
- `Pillow`：图片处理（可选）
- `qiniu`：七牛云Python SDK

## 使用方法

### 七牛云批量删除工具

#### 快速开始

```bash
# 1. 安装依赖
pip install qiniu python-dotenv

# 2. 配置环境变量（创建.env文件）
QINIU_ACCESS_KEY=你的AccessKey
QINIU_SECRET_KEY=你的SecretKey
QINIU_BUCKET_NAME=你的存储空间名称

# 3. 运行测试
python test_qiniu_delete.py

# 4. 查看详细使用说明
# 请参考：七牛云批量删除使用说明.md
```

#### Python代码使用

```python
from delete_qiniu_files import QiniuFileDeleter

# 初始化删除工具
deleter = QiniuFileDeleter()

# 获取文件列表
files = deleter.get_file_list("your-bucket-name")
print(f"找到 {len(files)} 个文件")

# 删除指定前缀的文件（需要确认）
result = deleter.delete_files_by_prefix(
    "your-bucket-name",
    prefix="temp/",
    confirm=True  # 必须设置为True
)
print(f"删除结果: {result}")

# 批量删除指定文件
files_to_delete = ["file1.jpg", "file2.png"]
result = deleter.delete_files_batch("your-bucket-name", files_to_delete)
```

#### 安全提醒 ⚠️

- **删除操作不可逆**：请在操作前备份重要数据
- **需要确认参数**：删除操作必须设置 `confirm=True`
- **建议测试环境**：先在测试环境验证功能
- **查看详细文档**：[七牛云批量删除使用说明.md](七牛云批量删除使用说明.md)

### URL到Markdown转换器

#### 命令行使用

```bash
# 基本用法 - 转换网页到Markdown
python url2markdown.py https://www.python.org/

# 指定输出文件名
python url2markdown.py https://docs.python.org/3/ -o python_docs.md

# 指定输出目录
python url2markdown.py https://github.com/ -d my_output/

# 不下载媒体文件
python url2markdown.py https://example.com/ --no-media

# 指定转换库
python url2markdown.py https://example.com/ --converter markdownify
python url2markdown.py https://example.com/ --converter html2text
```

#### Python代码使用

```python
import asyncio
from url2markdown import AdvancedWebToMarkdownConverter

async def convert_webpage():
    # 创建转换器
    converter = AdvancedWebToMarkdownConverter(
        output_dir="output",
        converter_lib="auto"  # 或 "markdownify", "html2text"
    )

    # 转换单个页面
    result_path = await converter.convert_url_to_markdown(
        "https://www.python.org/",
        "python_homepage.md",
        download_media=True
    )

    if result_path:
        print(f"转换成功: {result_path}")
    else:
        print("转换失败")

# 运行转换
asyncio.run(convert_webpage())
```

#### 批量转换示例

```python
import asyncio
from url2markdown import AdvancedWebToMarkdownConverter

async def batch_convert():
    converter = AdvancedWebToMarkdownConverter(output_dir="batch_output")

    urls = [
        ("https://www.python.org/", "python_home.md"),
        ("https://docs.python.org/3/", "python_docs.md"),
        ("https://pypi.org/", "pypi.md"),
    ]

    # 并发转换多个页面
    tasks = []
    for url, filename in urls:
        task = asyncio.create_task(
            converter.convert_url_to_markdown(url, filename)
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    successful = sum(1 for result in results if result is not None)
    print(f"批量转换完成: {successful}/{len(urls)} 成功")

asyncio.run(batch_convert())
```

### 功能特点

#### 1. 智能内容提取
- 自动识别页面主要内容区域（main, article, .content等）
- 移除导航、广告、脚注等无关内容
- 保留文章结构和格式

#### 2. 媒体文件管理
- 自动下载页面中的图片、视频、音频文件
- 支持相对路径和绝对路径的媒体文件
- 生成唯一文件名避免冲突
- 验证和优化下载的图片文件

#### 3. 多种转换器支持
- **markdownify**：Python原生转换器，格式规范
- **html2text**：功能强大的转换器，支持复杂格式
- **内置转换器**：基础转换功能，无外部依赖

#### 4. 丰富的输出格式
生成的Markdown文件包含：
- 页面标题作为文档标题
- 原始链接和转换时间
- 页面描述、作者、发布时间等元数据
- 格式化的内容正文

### 运行示例程序

```bash
# 运行基础示例
python url2markdown_example.py

# 运行测试程序
python test_url2markdown_simple.py
```

## 配置说明

### 环境变量配置
创建 `.env` 文件并配置以下变量：

```env
# 思源笔记API地址（默认本地地址）
SIYUAN_API_URL=http://127.0.0.1:6806

# 思源笔记API Token（必需）
SIYUAN_API_TOKEN=your_api_token_here

# 七牛云配置（用于批量删除功能）
QINIU_ACCESS_KEY=your_access_key_here
QINIU_SECRET_KEY=your_secret_key_here
QINIU_BUCKET_NAME=your_bucket_name_here
```

### 获取API Token
1. 打开思源笔记
2. 进入 `设置` -> `关于` -> `API Token`
3. 复制Token到 `.env` 文件中

## 项目结构

```
siyuan_scripts/
├── functions.py                       # 通用函数库模块
├── add_meta_data.py                  # 元数据添加脚本
├── delete_qiniu_files.py             # 🆕 七牛云批量删除工具
├── test_qiniu_delete.py              # 🆕 七牛云删除功能测试
├── 七牛云批量删除使用说明.md            # 🆕 详细使用说明文档
├── 快速开始.md                       # 🆕 快速开始指南
├── url2markdown.py                   # URL到Markdown转换器
├── url2markdown_example.py           # 转换器使用示例
├── test_url2markdown_simple.py       # 功能测试脚本
├── api_test.ipynb                    # API测试和数据分析
├── requirements.txt                  # Python依赖包列表
├── .env                             # 环境变量配置文件（需自行创建）
├── docs/                            # 文档目录
│   ├── 思源API.md                  # 思源笔记API文档
│   ├── 思源数据库表.md              # 数据库表结构说明
│   └── 思源块类型.md                # 块类型说明
└── output/                          # 输出文件目录
    ├── media/                       # 媒体文件存储目录
    ├── get_siyuan_notes_docguids.py # 文档GUID提取脚本
    ├── compare_docguids.py          # 文档GUID比较脚本
    ├── *.json                       # 各种数据导出文件
    ├── *.md                         # 转换生成的Markdown文件
    └── *.txt                        # 文本格式输出
```

## 模块说明

### functions.py - 通用函数库
提供了以下核心类和功能：

#### SiyuanAPI 类
- `call_api()` - 通用API调用函数
- `make_api_request()` - 兼容旧版本的API请求函数

#### NotebookManager 类
- `list_notebooks()` - 获取所有笔记本列表
- `get_notebook_id_by_name()` - 根据名称获取笔记本ID
- `get_notebook_name()` - 根据ID获取笔记本名称
- `open_notebook()` - 打开指定笔记本

#### DocumentManager 类
- `get_docs_in_path()` - 获取指定路径下的文档
- `get_notebook_docs_by_sql()` - 通过SQL查询获取文档
- `get_ids_by_hpath()` - 根据路径获取文档ID
- `get_doc_tree()` - 获取文档树结构

#### BlockManager 类
- `get_block_attributes()` - 获取块属性
- `get_child_blocks()` - 获取子块
- `get_first_paragraph_id()` - 获取第一个段落块ID
- `prepend_metadata_to_block()` - 在块开头添加元数据

#### FileManager 类
- `load_json_file()` - 加载JSON文件
- `save_json_file()` - 保存JSON文件

### url2markdown.py - URL转换器 🆕

#### AdvancedWebToMarkdownConverter 类
- `convert_url_to_markdown()` - 主要转换方法
- `extract_page_info()` - 提取页面元信息
- `extract_media_urls()` - 提取媒体文件URL
- `convert_html_to_markdown()` - HTML到Markdown转换

#### MediaDownloader 类
- `download_media_batch()` - 批量下载媒体文件
- `download_media_async()` - 异步下载单个文件
- `is_supported_media_type()` - 检查媒体类型支持

### 脚本文件说明

#### add_meta_data.py
主要的元数据处理脚本，使用functions.py模块中的类：
- 连接思源笔记API
- 获取指定笔记本和路径下的所有文档
- 读取文档的自定义属性
- 将属性信息以引用块格式插入到文档开头

## 使用案例

### 1. 学术研究
```python
# 批量转换研究相关的网页文档
urls = [
    "https://arxiv.org/abs/2301.00001",
    "https://scholar.google.com/...",
    "https://www.nature.com/articles/..."
]

for url in urls:
    await converter.convert_url_to_markdown(url)
```

### 2. 技术文档收集
```python
# 收集技术文档并保存媒体文件
tech_docs = [
    ("https://docs.python.org/3/tutorial/", "python_tutorial.md"),
    ("https://docs.djangoproject.com/", "django_docs.md"),
    ("https://reactjs.org/docs/", "react_docs.md"),
]

for url, filename in tech_docs:
    await converter.convert_url_to_markdown(url, filename, download_media=True)
```

### 3. 新闻文章存档
```python
# 转换新闻文章，包含图片和视频
news_urls = [
    "https://news.ycombinator.com/item?id=...",
    "https://techcrunch.com/...",
    "https://www.wired.com/..."
]

converter = AdvancedWebToMarkdownConverter(
    output_dir="news_archive",
    converter_lib="html2text"  # 更好地处理复杂格式
)

for url in news_urls:
    await converter.convert_url_to_markdown(url, download_media=True)
```

## 故障排除

### 常见问题

#### URL转换器相关
1. **依赖库缺失**：运行 `pip install -r requirements.txt` 安装所有依赖
2. **网络连接问题**：检查网络连接和目标网站可访问性
3. **媒体文件下载失败**：某些网站可能有防盗链保护
4. **转换质量问题**：尝试不同的转换器（markdownify vs html2text）
5. **编码问题**：程序会自动检测和处理编码，但某些特殊网站可能需要手动处理

#### 思源笔记相关
1. **API Token无效**：检查Token是否正确配置
2. **连接失败**：确认思源笔记正在运行且API服务可用
3. **路径不存在**：检查笔记本名称和文档路径是否正确
4. **权限问题**：确保有足够权限修改笔记内容
5. **模块导入错误**：确保functions.py文件在正确位置

### 性能优化建议

1. **批量转换**：使用异步并发处理提高效率
2. **媒体文件管理**：根据需要选择是否下载媒体文件
3. **转换器选择**：根据内容类型选择合适的转换器
4. **输出目录管理**：定期清理不需要的文件

### 调试技巧

1. **启用详细日志**：修改日志级别为DEBUG查看详细信息
2. **测试小页面**：先用简单页面测试功能
3. **检查依赖**：运行测试脚本检查环境配置
4. **逐步调试**：分步骤测试转换、下载等功能

## 更新日志

### v2.0.0 (2024-01)
- 🆕 新增 URL到Markdown 转换功能
- 🆕 支持媒体文件自动下载
- 🆕 多种HTML转换器支持
- 🆕 异步并发处理
- 🆕 智能内容提取
- 🆕 丰富的元数据支持

### v1.0.0
- ✅ 思源笔记API操作基础功能
- ✅ 元数据添加和管理
- ✅ 文档树结构处理
- ✅ 批量操作支持

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License
