# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python 3.7+ toolkit for automating SiYuan Note operations: batch import/export, web clipping, metadata management, and database queries. Runs on Windows; most scripts read URLs from the system clipboard via `pyperclip`. Requires SiYuan desktop client running at `http://127.0.0.1:6806`.

## Development Commands

### Environment Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Optional: for JS-heavy sites (Toutiao, etc.)
pip install playwright
python -m playwright install chromium
```

### Running Scripts
Most scripts are standalone entry points:
```bash
python urls_to_siyuan.py              # clipboard URLs → markdown → SiYuan
python urls_to_markdown.py            # clipboard URLs → local markdown files
python clipboard_html_to_markdown.py  # clipboard HTML → markdown
python create_notes_from_md.py        # folder of .md files → SiYuan
python wiznotes_to_siyuan.py          # WizNote export → SiYuan pipeline
python export_wiznotes_to_md.py       # WizNote → local markdown
python config_manager.py --show       # view current config
python config_manager.py --interactive
python examples/advanced_query_demo.py
```

### Testing
```bash
pytest                                         # all tests
pytest test/test_toutiao_fix.py                # single file
pytest test/test_feishu_integration.py -k name  # single case
pytest tests/                                   # secondary test dir
```

Test directories: `test/` (primary, 14 files) and `tests/` (secondary, 2 files). Output artifacts go to `test_output/` (git-ignored).

## Architecture

### `utilities/` — Core Library

The package `__init__.py` exports all key classes and provides factory functions (`create_siyuan_client()`, `create_managers()`, `create_media_manager()`, `create_markdown_importer()`, `create_url_to_markdown_converter()`). Use these instead of instantiating classes directly.

**SiYuan API Layer:**
- `api_client.py` — `SiyuanAPI.call_api(path, payload)`. 30s timeout. Auth via `SIYUAN_API_TOKEN`. Returns `None` on failure with logged error. Has 401 fallback (strips auth header).
- `notebook.py` — `NotebookManager`: list/create/find notebooks by name
- `document.py` — `DocumentManager`: create docs with markdown, query docs via SQL
- `block.py` — `BlockManager`: get/set attributes, get child blocks, prepend metadata
- `media_manager.py` — `MediaManager`: upload assets via multipart to `/api/asset/upload`
- `markdown_importer.py` — `MarkdownImporter`: orchestrates import; `convert_soft_breaks_to_hard_breaks()` handles SiYuan rendering quirks

**Web Content Processing Pipeline (`URLToMarkdownConverter` is the orchestrator):**
1. `web_downloader.py` — fetches HTML with chardet encoding detection + gzip/deflate/brotli decompression
2. `special_site_handler.py` — Feishu (extracts WeChat original links), Toutiao (Playwright JS rendering), X/Twitter
3. `html_converter.py` — `HTMLConverter` with `CustomMarkdownConverter` (extends `markdownify`); supports markdownify, html2text, builtin modes
4. `media_downloader.py` — async downloads via aiohttp/aiofiles, configurable concurrency
5. `clipboard_manager.py` — reads `%%%`-delimited or newline-delimited URLs from clipboard

**Database Queries:**
- `sql_queries.py` — 17 predefined queries + 7 table schema queries
- `advanced_sql_queries.py` — 22 analytical queries with parameterized functions (tag, attribute, date-range)

### Top-Level Scripts

Entry points that orchestrate `utilities/` modules. Key ones not in the pipeline above:
- `add_meta_data.py` — injects WizNote custom attributes into SiYuan doc blocks
- `clipboard_notes_mailto_wiznotes.py` — extracts article links from clipboard, emails to WizNote via yagmail
- `flatten_markdown_assets.py` — flattens nested `assets/` dirs, rewrites image links
- `extract_feishu_markdown.py` — Playwright-based Feishu document content extraction
- `query_to_csv.py` — `SQLiteQueryToCSV` class for querying SiYuan's `.db` file
- `delete_qiniu_files.py` — bulk Qiniu CDN deletion (permanent, use with caution)

### `export_wiznotes/` — WizNote Export Sub-package

Separate package with own `requirements.txt`. Key components:
- `wiz_client.py` — unofficial WizNote API client
- `note_exporter.py` — multi-threaded note exporter
- `collaboration_parser.py` — collaborative note parser

### Configuration System

Two-tier approach:

1. **`.env`** — credentials and API tokens: `SIYUAN_API_URL`, `SIYUAN_API_TOKEN`, `WIZ_USERNAME`, `WIZ_PASSWORD`, `QINIU_*`, `MAIL_*`
2. **`config.py` + `project_config.json`** — paths and behavior settings. Singleton `Config` class with helpers `get_config()`, `get_urls_path()`, `get_wiznotes_path()`. Modify via `config_manager.py --interactive` or edit `project_config.json` directly.

## Important Implementation Details

**File naming:** `url_to_markdown.py:generate_filename()` replaces filesystem-forbidden chars with full-width equivalents (`/` → `／`, `:` → `：`). Empty titles fall back to domain name.

**Soft break conversion:** `MarkdownImporter.convert_soft_breaks_to_hard_breaks()` converts single `\n` to double `\n\n` for SiYuan rendering. Skips code blocks, headers, lists, blockquotes, tables, and horizontal rules.

**Media path handling:** `MarkdownImporter` tracks local → SiYuan asset path mappings and replaces paths in markdown with SiYuan asset URLs after upload.

**Encoding cascade:** WebDownloader tries UTF-8 → GBK → GB2312 → chardet-detected encoding, with HTML meta charset as hint.

## Common Pitfalls

1. **API Token**: Scripts fail silently if `SIYUAN_API_TOKEN` is not set in `.env`
2. **SiYuan must be running**: API calls require the desktop client active on localhost:6806
3. **Windows console encoding**: Run `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` in PowerShell to avoid garbled Chinese
4. **Playwright**: JS-heavy sites need both `pip install playwright` AND `python -m playwright install chromium`
5. **Hardcoded paths**: `config.py` defaults `base_export_dir` to `"H:/为知笔记导出MD备份"` — override via `config_manager.py` or `project_config.json`
6. **Dual test dirs**: Tests exist in both `test/` and `tests/` — run `pytest` from root to catch all

## Conventions

- Python 3.7+, 4-space indent, `snake_case` modules/functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- Commits: imperative mood, use `feat:`, `fix:`, `docs:`, `refactor:` prefixes (Chinese or English)
- Mock external HTTP/SiYuan API calls in tests; assert on metadata (paths, counts, titles) not full content
- API calls return `None` on failure — check return values before using results
- UTF-8 (no BOM) for all source files

## Documentation

`docs/` contains detailed Chinese guides. Key docs: `思源笔记API.md`, `思源笔记数据库表与字段.md`, `思源笔记高级SQL查询使用指南.md`, `配置系统使用说明.md`.
