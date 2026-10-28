#!/usr/bin/env python3
"""Check repository-relative Markdown targets and heading anchors."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from markdown_checks import check_links, local_target, markdown_files, slug


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="指定仓库根目录")
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    _, checked = check_links(markdown_files(root), errors, root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"链接检查通过: {checked} 个仓库内 Markdown 链接和锚点。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
