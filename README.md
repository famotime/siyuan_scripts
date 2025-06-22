# 思源笔记脚本工具集

这是一个用于操作思源笔记（SiYuan）的Python脚本工具集，主要用于批量处理笔记数据、元数据管理、内容导入导出和媒体文件处理。

## 主要功能

### 📝 笔记导入工具
- **Markdown文件导入**：`create_notes_from_md.py` - 将文件夹下的Markdown文件批量导入到思源笔记
- **为知笔记导出**：`export_wiznotes_to_md.py` - 从为知笔记导出单篇或批量导出Markdown笔记
- **为知笔记转思源**：`wiznotes_to_siyuan.py` - 完整流程：导出为知笔记 → 导入思源笔记 → 整理文件

### 🌐 网页内容处理
- **URL转Markdown**：`urls_to_markdown.py` - 将网页内容批量转换为Markdown文件，支持媒体下载
- **URL转思源**：`urls_to_siyuan.py` - 完整流程：剪贴板URL → Markdown → 思源笔记
- **剪贴板笔记处理**：`clipboard_notes_mailto_wiznotes.py` - 从剪贴板提取文章链接，批量发送到为知笔记

### 🏷️ 元数据管理
- **元数据添加**：`add_meta_data.py` - 为思源笔记文档添加元数据信息
- **配置读取**：`read_siyuan_config.py` - 读取思源笔记配置，导出快捷键设置为Markdown表格

### ☁️ 云存储管理
- **七牛云批量删除**：`delete_qiniu_files.py` - 七牛云文件批量删除工具，支持按前缀删除和安全确认

### 🛠️ 核心工具库
- **utilities模块**：提供统一的API客户端和管理器，包括：
  - 思源笔记API操作（SiyuanAPI、NotebookManager、DocumentManager、BlockManager）
  - Markdown导入器（MarkdownImporter）
  - 媒体文件管理（MediaManager、MediaDownloader）
  - 网页内容处理（WebDownloader、HTMLConverter）

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
- `yagmail`：邮件发送

## 快速开始

### 基础配置
创建 `.env` 文件并配置以下变量：

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

### 常用功能示例

#### 1. 网页转思源笔记
```bash
# 将剪贴板中的URL转换为Markdown并导入思源笔记
python urls_to_siyuan.py
```

#### 2. Markdown文件导入
```bash
# 将指定文件夹的Markdown文件导入思源笔记
python create_notes_from_md.py
```

#### 3. 为知笔记迁移
```bash
# 完整的为知笔记迁移流程
python wiznotes_to_siyuan.py
```

#### 4. 网页内容下载
```bash
# 将网页转换为Markdown文件
python urls_to_markdown.py
```

## 项目结构

```
siyuan_scripts/
├── 🔧 核心工具库
│   └── utilities/                    # 通用工具模块
│       ├── api_client.py            # 思源API客户端
│       ├── notebook.py              # 笔记本管理
│       ├── document.py              # 文档管理
│       ├── block.py                 # 块管理
│       ├── markdown_importer.py     # Markdown导入器
│       ├── media_manager.py         # 媒体文件管理
│       ├── url_to_markdown.py       # URL转Markdown核心功能
│       └── ...
│
├── 📝 笔记导入工具
│   ├── create_notes_from_md.py      # Markdown文件导入思源
│   ├── export_wiznotes_to_md.py     # 为知笔记导出为Markdown
│   └── wiznotes_to_siyuan.py        # 为知笔记完整迁移流程
│
├── 🌐 网页处理工具
│   ├── urls_to_markdown.py          # URL转Markdown
│   ├── urls_to_siyuan.py            # URL转思源完整流程
│   └── clipboard_notes_mailto_wiznotes.py  # 剪贴板内容处理
│
├── 🏷️ 元数据工具
│   ├── add_meta_data.py             # 元数据添加
│   └── read_siyuan_config.py        # 配置读取和导出
│
├── ☁️ 云存储工具
│   ├── delete_qiniu_files.py        # 七牛云批量删除
│   └── 七牛云批量删除使用说明.md      # 详细使用说明
│
├── 📊 分析工具
│   └── api_test.ipynb               # API测试和数据分析
│
├── 📁 目录结构
│   ├── docs/                       # 文档目录
│   ├── export_wiznotes/             # 为知笔记导出模块
│   ├── output/                      # 输出文件目录
│   ├── test/                        # 测试文件
│   ├── requirements.txt             # 依赖包列表
│   └── .env                         # 环境变量配置
```

## 详细功能说明

### utilities工具库
提供了统一的API接口和管理器，简化了思源笔记的操作：

#### 核心类
- **SiyuanAPI**：思源笔记API客户端
- **NotebookManager**：笔记本管理（列表、创建、打开）
- **DocumentManager**：文档管理（查询、获取、树结构）
- **BlockManager**：块管理（属性、子块、元数据）
- **MarkdownImporter**：Markdown文件导入器
- **MediaManager**：媒体文件上传和管理

#### 网页处理类
- **URLToMarkdownConverter**：URL转Markdown转换器
- **WebDownloader**：网页内容下载器
- **HTMLConverter**：HTML到Markdown转换器
- **MediaDownloader**：媒体文件下载器

### 脚本文件说明

#### 笔记导入类
- **create_notes_from_md.py**：批量导入Markdown文件到思源笔记，支持媒体文件上传
- **export_wiznotes_to_md.py**：从为知笔记导出笔记为Markdown格式
- **wiznotes_to_siyuan.py**：一键式为知笔记迁移，包含导出、导入、文件整理

#### 网页处理类
- **urls_to_markdown.py**：高级网页到Markdown转换，支持媒体下载和元数据提取
- **urls_to_siyuan.py**：剪贴板URL一键导入思源笔记的完整流程
- **clipboard_notes_mailto_wiznotes.py**：智能识别和处理剪贴板中的文章链接

#### 元数据管理类
- **add_meta_data.py**：为思源笔记文档添加自定义属性和元数据
- **read_siyuan_config.py**：读取思源配置文件，导出快捷键设置为表格

#### 云存储工具类
- **delete_qiniu_files.py**：七牛云文件批量删除，支持前缀过滤和安全确认

## 获取API Token
1. 打开思源笔记
2. 进入 `设置` → `关于` → `API Token`
3. 复制Token到 `.env` 文件中

## 安全提醒
- **备份数据**：操作前请备份重要笔记数据
- **测试环境**：建议先在测试环境验证功能
- **权限控制**：妥善保管API Token和密码信息
- **删除确认**：删除操作不可逆，请谨慎操作

## 技术特性
- 🔄 **异步处理**：支持并发下载和处理
- 📦 **模块化设计**：utilities工具库提供统一接口
- 🛡️ **错误处理**：完善的异常处理和日志记录
- 🎯 **智能识别**：自动识别内容类型和媒体文件
- 📊 **进度追踪**：详细的操作日志和结果统计

---

**注意**：此工具集主要用于个人笔记管理和数据迁移，请遵守相关服务的使用条款。

