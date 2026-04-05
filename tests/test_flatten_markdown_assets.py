import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from flatten_markdown_assets import flatten_markdown_assets


def test_flatten_markdown_and_assets_to_root(tmp_path):
    nested_dir = tmp_path / "level1" / "level2"
    nested_dir.mkdir(parents=True)
    assets_dir = nested_dir / "assets"
    assets_dir.mkdir()

    md_path = nested_dir / "article.md"
    md_path.write_text("# Title\n\n![img](assets/image.png)\n", encoding="utf-8")
    (assets_dir / "image.png").write_bytes(b"image-bytes")
    (nested_dir / "note.txt").write_text("keep me", encoding="utf-8")

    result = flatten_markdown_assets(tmp_path)

    moved_md = tmp_path / "article.md"
    merged_assets = tmp_path / "assets" / "image.png"

    assert result["markdown_moved"] == 1
    assert result["asset_files_moved"] == 1
    assert result["directories_removed"] >= 1
    assert moved_md.exists()
    assert merged_assets.exists()
    assert moved_md.read_text(encoding="utf-8") == "# Title\n\n![img](assets/image.png)\n"
    assert not md_path.exists()
    assert not assets_dir.exists()
    assert (nested_dir / "note.txt").exists()


def test_flatten_renames_duplicate_markdown_and_asset_files(tmp_path):
    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"
    left_assets = left_dir / "assets"
    right_assets = right_dir / "assets"
    left_assets.mkdir(parents=True)
    right_assets.mkdir(parents=True)

    (left_dir / "same.md").write_text("![a](assets/image.png)\n", encoding="utf-8")
    (right_dir / "same.md").write_text("![b](assets/image.png)\n", encoding="utf-8")
    (left_assets / "image.png").write_bytes(b"left")
    (right_assets / "image.png").write_bytes(b"right")

    result = flatten_markdown_assets(tmp_path)

    assert result["markdown_moved"] == 2
    assert result["asset_files_moved"] == 2
    assert (tmp_path / "same.md").exists()
    assert (tmp_path / "same_1.md").exists()
    assert (tmp_path / "assets" / "image.png").read_bytes() == b"left"
    assert (tmp_path / "assets" / "image_1.png").read_bytes() == b"right"
    assert (tmp_path / "same.md").read_text(encoding="utf-8") == "![a](assets/image.png)\n"
    assert (tmp_path / "same_1.md").read_text(encoding="utf-8") == "![b](assets/image_1.png)\n"


def test_flatten_moves_referenced_local_resources_not_just_assets_dir(tmp_path):
    nested_dir = tmp_path / "articles" / "2026"
    media_dir = nested_dir / "media"
    media_dir.mkdir(parents=True)

    md_path = nested_dir / "story.md"
    md_path.write_text(
        "# Story\n\n![img](media/cover.png)\n[附件](media/file.pdf)\n",
        encoding="utf-8",
    )
    (media_dir / "cover.png").write_bytes(b"cover")
    (media_dir / "file.pdf").write_bytes(b"pdf")

    result = flatten_markdown_assets(tmp_path)

    assert result["markdown_moved"] == 1
    assert result["asset_files_moved"] == 2
    assert (tmp_path / "story.md").read_text(encoding="utf-8") == (
        "# Story\n\n![img](assets/cover.png)\n[附件](assets/file.pdf)\n"
    )
    assert (tmp_path / "assets" / "cover.png").read_bytes() == b"cover"
    assert (tmp_path / "assets" / "file.pdf").read_bytes() == b"pdf"


def test_flatten_rewrites_parent_relative_resource_paths(tmp_path):
    chapter_dir = tmp_path / "book" / "chapter1"
    shared_dir = tmp_path / "book" / "shared"
    chapter_dir.mkdir(parents=True)
    shared_dir.mkdir(parents=True)

    md_path = chapter_dir / "intro.md"
    md_path.write_text(
        "# Intro\n\n![logo](../shared/logo.png)\n",
        encoding="utf-8",
    )
    (shared_dir / "logo.png").write_bytes(b"logo")

    result = flatten_markdown_assets(tmp_path)

    assert result["markdown_moved"] == 1
    assert result["asset_files_moved"] == 1
    assert (tmp_path / "intro.md").read_text(encoding="utf-8") == (
        "# Intro\n\n![logo](assets/logo.png)\n"
    )
    assert (tmp_path / "assets" / "logo.png").read_bytes() == b"logo"
