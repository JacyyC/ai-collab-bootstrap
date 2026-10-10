#!/usr/bin/env python3
"""Preview or install the complete skill into an explicit directory; never overwrite."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parents[1] / "skills/ai-collab-bootstrap"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path, help="客户端实际使用的 skills 父目录")
    parser.add_argument("--write", action="store_true", help="明确复制；默认仅预览")
    args = parser.parse_args()
    target = args.destination.expanduser().absolute() / SOURCE.name
    try:
        if target.exists() or target.is_symlink():
            raise ValueError("目标已有同名目录或链接，拒绝覆盖")
        if any(parent.is_symlink() for parent in target.parents):
            raise ValueError("目标父路径含符号链接，请使用实际路径")
        resolved = target.resolve()
        if resolved.is_relative_to(SOURCE) or SOURCE.is_relative_to(resolved):
            raise ValueError("目标与发行源不能相互包含")
        if not (SOURCE / "SKILL.md").is_file():
            raise ValueError("发行源缺少 SKILL.md")
        if any(path.is_symlink() for path in SOURCE.rglob("*")):
            raise ValueError("发行源包含符号链接，拒绝越界复制")
        files = sum(path.is_file() for path in SOURCE.rglob("*"))
        if not args.write:
            print(f"预览：将复制 {files} 个文件到 {target}；未写入。加 --write 执行。")
            return 0
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SOURCE, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        print(f"已安装到 {target}；未修改客户端配置。")
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
