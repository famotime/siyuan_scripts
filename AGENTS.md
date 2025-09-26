# Repository Guidelines

This repository collects automation scripts that integrate SiYuan, WizNote, and web sources. Follow the practices below to add features without breaking existing workflows.

## Project Structure & Module Organization
- `utilities/` holds core clients and helpers (API wrappers, downloaders, converters). Keep new shared logic here.
- `examples/` packages runnable demos illustrating scripted flows; update them when behavior changes.
- `export_wiznotes/` and top-level `*.py` scripts are entry points for bulk imports, exports, and cleanups.
- `docs/` contains Chinese-language feature guides. Mirror any new capability with a short how-to here.
- `test/` stores pytest suites; generated artifacts should be written to `output/` or `test_output/` and git-ignored.

## Build, Test, and Development Commands
- `python -m venv .venv` followed by `.venv\Scripts\activate` (Windows) creates an isolated environment.
- `pip install -r requirements.txt` installs runtime and optional scraping dependencies.
- `pytest` runs all automated checks under `test/`; use `pytest test/test_toutiao_fix.py -k case` for focused runs.
- `python urls_to_siyuan.py --help` or similar scripts expose CLI options; document new flags in `docs/`.

## Coding Style & Naming Conventions
Use Python 3.7+ syntax with 4-space indentation. Modules and functions should stay in `snake_case`, classes in `PascalCase`, and constants in `UPPER_SNAKE_CASE`. Prefer descriptive docstrings for public functions. When adding CLI arguments, follow existing `argparse` patterns and emit clear INFO-level logs.
???????????????

## Testing Guidelines
Author pytest modules as `test_<feature>.py` and group scenario helpers under fixtures. Mock external HTTP calls or SiYuan APIs to keep tests deterministic. When a script produces files, assert on generated metadata rather than raw content. Aim to extend coverage for new query types, converters, and edge-case encodings (Feishu, Toutiao, Qiniu).

## Commit & Pull Request Guidelines
Commit messages are short and action-oriented (imperative verbs; Chinese or English acceptable). Pull requests should describe intent, list test evidence (`pytest` output, manual script run), mention config or README updates, and attach sample output paths when relevant. Request review before merging non-trivial data migrations.

## Security & Configuration Tips
Never commit `.env` or personal tokens. Document new required variables in `README.md` and provide safe defaults in code. Treat destructive scripts (`delete_qiniu_files.py`) with guard prompts and highlight backup steps in docs.

## File Encoding
When modifying or adding any code files, the following coding requirements must be adhered to:
- First time using shell must execute: [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
- Encoding should be unified to UTF-8 (without BOM). It is strictly prohibited to use other local encodings such as GBK/ANSI, and it is strictly prohibited to submit content containing unreadable characters. 
- When modifying or adding files, be sure to save them in UTF-8 format; if you find any files that are not in UTF-8 format before submitting, please convert them to UTF-8 before submitting.

## ??
????????????????????????????????????????????