"""
HTML to Markdown converter utility.

Reads an HTML file and writes a Markdown file using markdownify.

Usage:
  python utilities/html_to_md.py --input <input.html> --output <output.md> [--title <title>]
"""

import argparse
import pathlib
import sys
from typing import Optional

try:
    from markdownify import markdownify as md
except Exception as e:
    print("markdownify is required. Please pip install markdownify", file=sys.stderr)
    raise


def html_to_md(html: str, title: Optional[str] = None) -> str:
    body = md(html, heading_style="ATX", strip="\n\u200b\uFEFF")
    if title:
        # Ensure title is first-level heading
        heading = f"# {title.strip()}\n\n"
        if body.lstrip().startswith("# "):
            return body
        return heading + body
    return body


def main():
    parser = argparse.ArgumentParser(description="Convert HTML file to Markdown")
    parser.add_argument("--input", required=True, help="Path to input .html file")
    parser.add_argument("--output", required=True, help="Path to output .md file")
    parser.add_argument("--title", help="Optional document title to prepend as H1")
    args = parser.parse_args()

    in_path = pathlib.Path(args.input)
    out_path = pathlib.Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    html = in_path.read_text(encoding="utf-8", errors="ignore")
    md_text = html_to_md(html, title=args.title)
    out_path.write_text(md_text, encoding="utf-8")


if __name__ == "__main__":
    main()

