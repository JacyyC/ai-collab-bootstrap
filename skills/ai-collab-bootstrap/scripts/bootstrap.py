#!/usr/bin/env python3
"""Copy an uninstantiated workspace scaffold after checking all target conflicts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
DEFAULT_SOURCE = Path(__file__).resolve().parents[1] / "templates"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path, help="目标项目根；保留既有代码布局")
    parser.add_argument("--write", action="store_true", help="明确复制；默认仅预览")
    parser.add_argument("--template-dir", type=Path, help="完整且带 SHA-256 清单的模板源")
    args = parser.parse_args()
    source = args.template_dir or Path(os.environ.get("AI_COLLAB_TEMPLATE_DIR", str(DEFAULT_SOURCE)))
    source = source.expanduser().absolute()
    target = args.target.expanduser().absolute()
    try:
        if source.is_symlink() or target.is_symlink():
            raise ValueError("模板源或目标不能是符号链接")
        if any(parent.is_symlink() for parent in (*source.parents, *target.parents)):
            raise ValueError("路径含符号链接，请使用实际路径")
        source, target = source.resolve(), target.resolve()
        if source == target or target.is_relative_to(source) or source.is_relative_to(target):
            raise ValueError("目标和模板源不能相互包含")
        manifest = json.loads((source / ".template-manifest.json").read_text(encoding="utf-8"))
        if manifest.get("version") != 1 or not isinstance(manifest.get("files"), dict):
            raise ValueError("不支持的模板清单")
        prepared: dict[str, bytes] = {}
        conflicts: list[str] = []
        for name, checksum in manifest["files"].items():
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts or not relative.parts:
                raise ValueError("清单含越界路径")
            origin, destination = source / relative, target / relative
            if origin.is_symlink() or any(p.is_symlink() for p in origin.parents):
                raise ValueError(f"模板路径含符号链接：{name}")
            content = origin.read_bytes()
            if hashlib.sha256(content).hexdigest() != checksum:
                raise ValueError(f"模板完整性校验失败：{name}")
            if destination.exists() or destination.is_symlink() or any(
                p.is_symlink() or (p.exists() and not p.is_dir()) for p in destination.parents
            ):
                conflicts.append(name)
            prepared[name] = content
        if not prepared or "AGENTS.md" not in prepared or "workspace/scripts/maintain.py" not in prepared:
            raise ValueError("模板清单不完整")
        if conflicts:
            raise ValueError("存在目标冲突，未写入；用 skill 更新路径处理：" + ", ".join(conflicts))
        if not args.write:
            print(f"预览：复制 {len(prepared)} 个骨架文件到 {target}；未写入。")
            return 0
        for name, content in prepared.items():
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(content)
        print(f"已复制 {len(prepared)} 个骨架文件；尚未实例化。请填写项目定位、日期和真实事实，再运行 maintain.py --check。")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
