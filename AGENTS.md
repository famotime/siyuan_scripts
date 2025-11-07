# Repository Guidelines

## Project Structure & Module Organization
- `utilities/`: core clients and helpers (API wrappers, downloaders, converters). Put shared logic here.
- `examples/`: runnable demos; update when behavior or flags change.
- `export_wiznotes/` and top-level `*.py`: entry points for bulk imports/exports/cleanups.
- `docs/`: Chinese guides. Mirror new capabilities with a brief how‑to.
- `test/`: pytest suites. Write artifacts to `output/` or `test_output/` (git‑ignored).

## Build, Test, and Development Commands
- Create venv (Windows): `python -m venv .venv` then `.venv\\Scripts\\activate`
- Install deps: `pip install -r requirements.txt` (includes optional scraping extras)
- Run tests: `pytest` or focus: `pytest test/test_toutiao_fix.py -k case`
- CLI help: `python urls_to_siyuan.py --help` (similar for other scripts)
- Tip (Windows console): run `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` once per session.

## Coding Style & Naming Conventions
- Python 3.7+, 4‑space indentation. Modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Prefer descriptive docstrings for public functions.
- Follow existing `argparse` patterns; add clear `--flags` and INFO‑level logs.

## Testing Guidelines
- Framework: pytest. Name files `test_<feature>.py`.
- Use fixtures; mock external HTTP/SiYuan APIs for determinism.
- For file‑producing scripts, assert on metadata (paths, counts, titles) rather than full content.
- Cover edge encodings and sources (Feishu, Toutiao, Qiniu).

## Commit & Pull Request Guidelines
- Commits: short, imperative (CN/EN both fine).
- PRs: describe intent, include test evidence (`pytest` output or manual run), mention config/README/docs updates, and link sample outputs (e.g., `output/...`).
- Request review before non‑trivial data migrations.

## Security & Configuration Tips
- Never commit `.env` or tokens. Document required variables in `README.md` and provide safe defaults.
- Add guard prompts for destructive scripts (e.g., `delete_qiniu_files.py`) and document backup steps in `docs/`.

## File Encoding
- Use UTF‑8 (no BOM) for all code and docs. Convert non‑UTF‑8 files before submitting.
- On Windows terminals, set UTF‑8 output as shown above to avoid mojibake.

