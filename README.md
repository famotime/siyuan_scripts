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

### 🏷️ 元数据管理
- **元数据添加**: `add_meta_data.py` - 为思源笔记文档添加元数据信息。
- **配置读取**: `read_siyuan_config.py` - 读取思源笔记配置，导出快捷键设置为Markdown表格。

### ☁️ 云存储管理
- **七牛云批量删除**: `delete_qiniu_files.py` - 七牛云同步文件批量删除工具，解决官网批量删除操作缓慢问题。详见 `七牛云文件批量删除使用说明.md`。

### 🛠️ 核心工具库
- **utilities模块**：提供统一的API客户端和管理器，包括：
  - 思源笔记API操作（SiyuanAPI、NotebookManager、DocumentManager、BlockManager）
  - Markdown导入器（MarkdownImporter）
  - 媒体文件管理（MediaManager、MediaDownloader）
  - 网页内容处理（WebDownloader、HTMLConverter）

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
- `requests`
- `python-dotenv`
- `beautifulsoup4`
- `lxml`
- `html5lib`
- `markdownify`
- `html2text`
- `Pillow`
- `urllib3`
- `aiohttp`
- `aiofiles`
- `qiniu`
- `pyperclip`
- `yagmail`

## 快速开始

### 1. 基础配置
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

### 2. 获取思源API Token
1. 打开思源笔记客户端。
2. 进入 `设置` -> `关于`。
3. 在 `API Token` 处找到你的Token。
4. 复制并粘贴到 `.env` 文件中。

### 3. 运行脚本
根据你的需求执行相应的脚本。例如，要将剪贴板中的URL一键存入思源：
```bash
python urls_to_siyuan.py
```

## 项目结构

```
siyuan_scripts/
├── .git/
├── .gitignore
├── docs/                        # 项目文档
│   ├── 思源笔记API.md
│   └── 思源笔记数据库表与字段.md
├── export_wiznotes/             # 为知笔记导出模块
├── output/                      # 脚本输出目录
├── test/                        # 测试代码
├── utilities/                   # 核心功能工具库
├── __pycache__/
├── add_meta_data.py             # 添加元数据
├── api_test.ipynb               # API测试Jupyter Notebook
├── clipboard_notes_mailto_wiznotes.py # 剪贴板内容发送至为知
├── create_notes_from_md.py      # 从MD文件创建笔记
├── delete_qiniu_files.py        # 删除七牛云文件
├── export_wiznotes_to_md.py     # 导出为知笔记为MD
├── instuctions.md               # 其他说明文档
├── query_to_csv.py              # 查询并导出为CSV
├── read_siyuan_config.py        # 读取思源配置
├── README.md                    # 本文档
├── requirements.txt             # Python依赖
├── urls_to_markdown.py          # 网址转Markdown
├── urls_to_siyuan.py            # 网址转思源笔记
├── wiznotes_to_siyuan.py        # 为知笔记迁移到思源
└── 七牛云文件批量删除使用说明.md
```

## 安全提醒
- **数据备份**: 在执行任何可能修改数据的脚本前，请务必备份你的思源笔记数据。
- **凭证安全**: 妥善保管你的 `.env` 文件，不要将包含敏感信息（如API Token、密码）的文件提交到公共代码库。
- **删除操作**: `delete_qiniu_files.py` 会永久删除云端文件，请在确认无误后再执行。

---

**注意**：此工具集主要用于个人笔记管理和数据迁移，请遵守相关服务的使用条款。