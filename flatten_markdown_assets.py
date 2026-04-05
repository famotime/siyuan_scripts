"""
压平指定目录下的 Markdown 与 assets 目录结构。

示例：
    python flatten_markdown_assets.py "G:\\Download\\Edge\\_OpenClaw.md\\"
"""

import argparse
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional


MARKDOWN_SUFFIXES = {".md", ".markdown"}
MARKDOWN_LINK_PATTERN = re.compile(
    r"(?P<prefix>!?\[[^\]]*\]\()(?P<target><[^>\n]+>|[^)\n]+)(?P<suffix>\))"
)


def parse_args():
    parser = argparse.ArgumentParser(description="压平目录中的 Markdown 和 assets 结构")
    parser.add_argument("target_dir", help="要处理的根目录，例如 G:\\Download\\Edge\\_OpenClaw.md\\")
    return parser.parse_args()


def build_unique_path(target_dir: Path, original_name: str) -> Path:
    candidate = target_dir / original_name
    if not candidate.exists():
        return candidate

    stem = Path(original_name).stem
    suffix = Path(original_name).suffix
    counter = 1
    while True:
        candidate = target_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def parse_markdown_target(raw_target: str) -> Dict[str, str]:
    target = raw_target.strip()
    wrapped = target.startswith("<") and target.endswith(">")
    if wrapped:
        return {
            "path": target[1:-1].strip(),
            "suffix": "",
            "wrapped": "1",
        }

    match = re.match(
        r"(?P<path>.+?)(?P<extra>\s+(?:\"[^\"]*\"|'[^']*'|\([^)]+\)))?\s*$",
        target,
    )
    if not match:
        return {
            "path": target,
            "suffix": "",
            "wrapped": "",
        }

    return {
        "path": match.group("path").strip(),
        "suffix": match.group("extra") or "",
        "wrapped": "",
    }


def is_local_resource_link(link_path: str) -> bool:
    normalized = link_path.strip().replace("\\", "/")
    if not normalized:
        return False
    if normalized.startswith("#") or normalized.startswith("//"):
        return False
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", normalized):
        return False
    return True


def resolve_local_resource_path(markdown_file: Path, link_path: str, root_dir: Path) -> Optional[Path]:
    if not is_local_resource_link(link_path):
        return None

    resolved_path = (markdown_file.parent / link_path).resolve(strict=False)
    try:
        resolved_path.relative_to(root_dir)
    except ValueError:
        return None

    if resolved_path.suffix.lower() in MARKDOWN_SUFFIXES:
        return None

    if not resolved_path.exists() or not resolved_path.is_file():
        return None

    return resolved_path


def move_resource_to_root_assets(root_dir: Path, resource_path: Path) -> str:
    target_assets_dir = root_dir / "assets"
    target_assets_dir.mkdir(parents=True, exist_ok=True)
    unique_target = build_unique_path(target_assets_dir, resource_path.name)
    shutil.move(str(resource_path), str(unique_target))
    return (Path("assets") / unique_target.name).as_posix()


def collect_and_move_linked_resources(
    root_dir: Path,
    markdown_file: Path,
    content: str,
    moved_resource_map: Dict[Path, str],
) -> int:
    moved_count = 0

    for match in MARKDOWN_LINK_PATTERN.finditer(content):
        parsed_target = parse_markdown_target(match.group("target"))
        resource_path = resolve_local_resource_path(markdown_file, parsed_target["path"], root_dir)
        if resource_path is None:
            continue

        if resource_path not in moved_resource_map:
            moved_resource_map[resource_path] = move_resource_to_root_assets(root_dir, resource_path)
            moved_count += 1

    return moved_count


def replace_resource_links(
    content: str,
    markdown_file: Path,
    root_dir: Path,
    moved_resource_map: Dict[Path, str],
) -> str:
    if not moved_resource_map:
        return content

    def repl(match):
        parsed_target = parse_markdown_target(match.group("target"))
        resource_path = (markdown_file.parent / parsed_target["path"]).resolve(strict=False)
        replacement = moved_resource_map.get(resource_path)
        if not replacement:
            return match.group(0)

        replacement_target = replacement
        if parsed_target["wrapped"]:
            replacement_target = f"<{replacement_target}>"
        replacement_target = f"{replacement_target}{parsed_target['suffix']}"
        return f"{match.group('prefix')}{replacement_target}{match.group('suffix')}"

    return MARKDOWN_LINK_PATTERN.sub(repl, content)


def remove_empty_dirs(root_dir: Path) -> int:
    removed = 0
    for directory in sorted(
        [path for path in root_dir.rglob("*") if path.is_dir()],
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        if directory == root_dir:
            continue
        try:
            next(directory.iterdir())
        except StopIteration:
            directory.rmdir()
            removed += 1
    return removed


def flatten_markdown_assets(root_dir: Path) -> Dict[str, int]:
    root_dir = Path(root_dir).resolve()
    if not root_dir.exists() or not root_dir.is_dir():
        raise ValueError(f"目录不存在或不是文件夹: {root_dir}")

    markdown_files: List[Path] = sorted(
        [
            path for path in root_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in MARKDOWN_SUFFIXES and path.parent != root_dir
        ]
    )

    result = {
        "markdown_moved": 0,
        "asset_files_moved": 0,
        "directories_removed": 0,
    }

    moved_resource_map: Dict[Path, str] = {}

    for markdown_file in markdown_files:
        original_content = markdown_file.read_text(encoding="utf-8")
        result["asset_files_moved"] += collect_and_move_linked_resources(
            root_dir=root_dir,
            markdown_file=markdown_file,
            content=original_content,
            moved_resource_map=moved_resource_map,
        )
        updated_content = replace_resource_links(
            content=original_content,
            markdown_file=markdown_file,
            root_dir=root_dir,
            moved_resource_map=moved_resource_map,
        )
        target_markdown_path = build_unique_path(root_dir, markdown_file.name)
        target_markdown_path.write_text(updated_content, encoding="utf-8")
        markdown_file.unlink()
        result["markdown_moved"] += 1

    result["directories_removed"] = remove_empty_dirs(root_dir)
    return result


def main():
    args = parse_args()
    result = flatten_markdown_assets(Path(args.target_dir))
    print(f"已移动 Markdown: {result['markdown_moved']}")
    print(f"已移动 assets 文件: {result['asset_files_moved']}")
    print(f"已删除空目录: {result['directories_removed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
