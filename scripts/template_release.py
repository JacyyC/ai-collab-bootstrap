#!/usr/bin/env python3
"""Generate only project-owned assets, including optional reference templates."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).resolve().parents[1]
ROOT = REPOSITORY / "template-source"
STATIC = (
    ".gitignore", "AGENTS.md", "README.md", "workspace/README.md", "workspace/docs/README.md",
    "workspace/docs/DOCUMENTATION_POLICY.md", "workspace/docs/DOCUMENT_LIFECYCLE.md",
    "workspace/docs/PROJECT_LAYOUT.md", "workspace/docs/WORK.md", "workspace/docs/HISTORY.md",
    "workspace/docs/work-items/records/.gitkeep",
)
RUNTIME = ("maintain.py", "record_tools.py", "workspace_views.py", "document_health_check.py", "markdown_checks.py")
MANIFEST = ".template-manifest.json"
VIEW_RE = re.compile(r"<!-- workspace-view:start -->.*?<!-- workspace-view:end -->", re.DOTALL)


def release_files(root: Path) -> dict[str, bytes]:
    if "<PROJECT-NAME>" not in (root / "README.md").read_text(encoding="utf-8"):
        raise ValueError("只允许从未实例化的模板源发布")
    paths = set(STATIC)
    paths.update("workspace/scripts/" + name for name in RUNTIME)
    paths.update("workspace/templates/work-item/" + name + ".md" for name in ("README", "spec", "plan", "log", "evidence"))
    paths.update(path.relative_to(root).as_posix() for path in (root / "optional").glob("*.md"))
    sys.path.insert(0, str(root / "workspace/scripts"))
    spec = importlib.util.spec_from_file_location("release_workspace_views", root / "workspace/scripts/workspace_views.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    empty = {"workspace/docs/WORK.md": module.work_block([]), "workspace/docs/HISTORY.md": module.history_block([])}
    result = {}
    for relative in sorted(paths):
        source = root / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"模板白名单文件缺失或为符号链接：{relative}")
        content = source.read_bytes()
        if relative in empty:
            text = content.decode("utf-8")
            if len(VIEW_RE.findall(text)) != 1:
                raise ValueError(f"派生区块必须恰好一个：{relative}")
            content = VIEW_RE.sub(lambda _: "<!-- workspace-view:start -->\n" + empty[relative] + "\n<!-- workspace-view:end -->", text).encode("utf-8")
        result[relative] = content
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--destination", type=Path, default=REPOSITORY / "skills/ai-collab-bootstrap/templates")
    args = parser.parse_args()
    root = args.root.resolve()
    raw_destination = args.destination.absolute()
    if raw_destination.is_symlink() or any(path.is_symlink() for path in raw_destination.parents):
        parser.error("发行路径不能经过符号链接")
    destination = raw_destination.resolve()
    if destination == root or root.is_relative_to(destination):
        parser.error("发行目录不能覆盖模板源或其父目录")
    try:
        files = release_files(root)
        manifest = {"version": 1, "files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
        previous = {}
        manifest_path = destination / MANIFEST
        if manifest_path.is_symlink():
            raise ValueError("发行清单不能是符号链接")
        if manifest_path.is_file():
            previous = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", {})
        obsolete = sorted(set(previous) - set(files))
        # The old manifest proves ownership. Retire only byte-identical old
        # assets, never unknown/customized content or an instantiated project.
        for name in obsolete:
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("旧发行清单含越界路径")
            target = destination / relative
            if target.is_symlink() or any(parent.is_symlink() for parent in target.parents):
                raise ValueError(f"退役路径经符号链接：{name}")
            if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() != previous[name]:
                raise ValueError(f"退役发行文件已有定制，保留并请维护者处理：{name}")
        changed = []
        for name, content in files.items():
            target = destination / name
            if target.is_symlink() or any(parent.is_symlink() for parent in target.parents):
                raise ValueError(f"发行路径经符号链接：{name}")
            if not target.is_file() or target.read_bytes() != content:
                changed.append(name)
        encoded = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        drift = not manifest_path.is_file() or manifest_path.read_bytes() != encoded
        if args.check:
            if changed or obsolete or drift:
                print("发行副本漂移：" + ", ".join(changed + obsolete + ([MANIFEST] if drift else [])))
                return 1
            print(f"发行副本检查通过：{len(files)} 个项目模板资产（optional/ 不默认安装）")
            return 0
        for name in changed:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(files[name])
        for name in obsolete:
            target = destination / name
            if target.is_file():
                target.unlink()
        if drift:
            destination.mkdir(parents=True, exist_ok=True)
            manifest_path.write_bytes(encoded)
        print(f"发行副本已生成：{len(files)} 个资产，更新 {len(changed)}，退役 {len(obsolete)} 个未定制旧资产")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
