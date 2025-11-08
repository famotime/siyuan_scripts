# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python toolkit for automating SiYuan Note operations, including note import/export, web clipping, metadata management, and database queries. The project emphasizes batch processing workflows and integrates with external services (WizNote, Qiniu Cloud).

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install Playwright for JS-heavy sites
pip install playwright
python -m playwright install chromium
```

### Running Scripts
Most scripts are standalone entry points that can be run directly:
```bash
# URL to SiYuan workflow (clipboard → markdown → SiYuan)
python urls_to_siyuan.py

# URL to markdown only
python urls_to_markdown.py

# HTML clipboard to markdown
python clipboard_html_to_markdown.py

# Import markdown files to SiYuan
python create_notes_from_md.py

# SQL query demo
python examples/advanced_query_demo.py

# Configuration management
python config_manager.py --show
python config_manager.py --interactive
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest test/test_toutiao_fix.py

# Run specific test case
pytest test/test_feishu_integration.py -k test_case_name
```

## Architecture Overview

### Core Module Structure (`utilities/`)

The `utilities/` module contains the core functionality organized into specialized components:

**SiYuan API Layer:**
- `api_client.py` - Base SiyuanAPI client with generic `/api/*` call method
- `notebook.py` - NotebookManager for notebook operations
- `document.py` - DocumentManager for document operations
- `block.py` - BlockManager for block operations
- `media_manager.py` - MediaManager for asset uploads
- `markdown_importer.py` - MarkdownImporter orchestrates the import workflow

**Web Content Processing Pipeline:**
- `url_to_markdown.py` - URLToMarkdownConverter (orchestrator)
- `web_downloader.py` - WebDownloader fetches HTML with encoding/compression handling
- `html_converter.py` - HTMLConverter (supports markdownify, html2text, builtin)
- `media_downloader.py` - MediaDownloader for async image/media downloads
- `special_site_handler.py` - SpecialSiteHandler for Feishu/Toutiao edge cases
- `clipboard_manager.py` - ClipboardManager for clipboard operations

**Database Queries:**
- `sql_queries.py` - Basic predefined SQL queries
- `advanced_sql_queries.py` - 22 advanced analytical queries with parameterization

### Configuration System

The project uses a two-tier configuration approach:

1. **Environment Variables (`.env`)**: API tokens and credentials
   - `SIYUAN_API_URL`, `SIYUAN_API_TOKEN`
   - `WIZ_USERNAME`, `WIZ_PASSWORD`
   - `QINIU_ACCESS_KEY`, `QINIU_SECRET_KEY`, `QINIU_BUCKET_NAME`

2. **Project Config (`config.py` + `project_config.json`)**: Paths and behavior
   - Managed via `Config` class singleton (`config = Config()`)
   - Access via helper functions: `get_config()`, `get_urls_path()`, `get_wiznotes_path()`
   - Modify via `config_manager.py` CLI tool

### Key Workflows

**URL → SiYuan (`urls_to_siyuan.py`):**
1. URLToMarkdownConverter reads URLs from clipboard
2. WebDownloader fetches HTML (with special handling via SpecialSiteHandler)
3. HTMLConverter converts to markdown
4. MediaDownloader downloads referenced images/media
5. MarkdownImporter uploads markdown + media to SiYuan
6. Processed files moved to "已转思源" directory

**Feishu Link Processing:**
- Auto-detects `https://waytoagi.feishu.cn/` links
- Extracts WeChat article original link from page content
- Prefers original article over Feishu page
- Supports multiple link format patterns (see `special_site_handler.py`)

**Encoding/Compression Handling:**
- WebDownloader auto-detects encoding via chardet
- Supports gzip, deflate, brotli decompression
- Fallback encoding cascade: UTF-8 → GBK → GB2312 → detected
- Parses HTML meta charset as hint

## Important Implementation Notes

### File Naming and Title Extraction
- `url_to_markdown.py:generate_filename()` sanitizes titles by replacing filesystem-forbidden characters with full-width equivalents (e.g., `/` → `／`, `:` → `：`)
- This preserves readability while ensuring cross-platform compatibility
- Empty/short titles fall back to URL domain name

### Soft Break Conversion
- `markdown_importer.py:convert_soft_breaks_to_hard_breaks()` converts single newlines to double newlines for proper rendering in SiYuan
- Skips conversion inside code blocks (triple backticks), headers, lists, blockquotes, tables, and horizontal rules

### Media Path Handling
- MarkdownImporter tracks local → SiYuan asset path mappings
- Replaces relative/local paths in markdown with SiYuan asset URLs
- Handles both local files and already-downloaded web images

### Error Handling Pattern
- API calls return `None` on failure with logged error
- Most scripts use try-except with informative error messages
- Check `api_client.py:call_api()` for standard response handling pattern

## Database Schema
SiYuan stores notes in SQLite. Key tables:
- `blocks` - All content blocks (paragraphs, headings, code, etc.)
- `attributes` - Custom attributes and metadata
- `refs` - Block references and backlinks
- `spans` - Inline elements and formatting

See `docs/思源笔记数据库表与字段.md` for full schema documentation.

## Common Pitfalls

1. **API Token**: Many scripts fail silently if `SIYUAN_API_TOKEN` is not set in `.env`
2. **SiYuan Must Be Running**: API calls require SiYuan desktop client to be active
3. **Windows Console Encoding**: Run `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` in PowerShell to avoid garbled Chinese characters
4. **Playwright Installation**: JS-heavy sites require both `pip install playwright` AND `python -m playwright install chromium`
5. **Config Paths**: `config.py` hard-codes `base_export_dir = "H:/为知笔记导出MD备份"` - modify via `config_manager.py` or edit `project_config.json`

## Testing Conventions

- Test files: `test/test_<feature>.py`
- Output artifacts go to `test_output/` (git-ignored)
- Use fixtures for common setup (SiYuan API mocks, temp directories)
- Mock external HTTP calls; test against local files when possible

## Documentation
- `docs/` contains detailed Chinese guides for all major features
- Update relevant docs when adding new capabilities
- Key docs: 思源笔记API.md, 思源笔记高级SQL查询使用指南.md, 配置系统使用说明.md

## Notes on External Integrations

**WizNote Export (`export_wiznotes/`):**
- Uses unofficial API client (`wiz_client.py`)
- Handles collaborative notes with `collaboration_parser.py`
- Multi-threaded export via `note_exporter.py`

**Qiniu Cloud (`delete_qiniu_files.py`):**
- Bulk delete tool for Qiniu CDN files
- Use with caution - deletions are permanent
- Requires `QINIU_ACCESS_KEY`, `QINIU_SECRET_KEY`, `QINIU_BUCKET_NAME` in `.env`
