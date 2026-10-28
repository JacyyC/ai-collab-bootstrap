#!/usr/bin/env python3
"""Generate the portable Skill templates from the canonical template repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True


ROOT = Path(__file__).resolve().parents[2]
STATIC = (
    ".gitignore", "AGENTS.md", "README.md", "project/README.md",
    "project/docs/index.md", "project/backend/.gitkeep", "project/frontend/.gitkeep",
    "workspace/README.md", "workspace/docs/README.md",
    "workspace/docs/DOCUMENTATION_POLICY.md", "workspace/docs/DOCUMENT_LIFECYCLE.md",
    "workspace/docs/WORK.md", "workspace/docs/HISTORY.md", "workspace/docs/ROADMAP.md",
    "workspace/docs/work-items/README.md", "workspace/docs/work-items/.gitkeep",
    "workspace/docs/work-items/records/.gitkeep", "workspace/docs/framework/README.md",
    "workspace/docs/framework/current/v1.md", "workspace/docs/framework/target/v1.md",
    "workspace/docs/decisions/README.md", "workspace/docs/decisions/ADR-0000-template.md",
)
VIEWS = frozenset({
    "workspace/docs/WORK.md", "workspace/docs/HISTORY.md",
    "workspace/docs/work-items/README.md",
})
RETIRED = frozenset(
    "workspace/docs/framework/current/v1/" + name + ".md"
    for name in ("technology", "components", "flows", "data-integration", "verification")
)
MANIFEST = ".template-manifest.json"
VIEW_RE = re.compile(r"<!-- workspace-view:start -->.*?<!-- workspace-view:end -->", re.DOTALL)


def release_files(root: Path) -> dict[str, bytes]:
    """Only export template-owned paths; never include project records or private files."""
    if "<PROJECT-NAME>" not in (root / "README.md").read_text(encoding="utf-8"):
        raise ValueError("只允许从未实例化的主模板发布；不能把实际项目事实覆盖到发行副本")
    paths = set(STATIC)
    paths.update(str(path.relative_to(root)) for path in (root / "workspace/templates/work-item").glob("*.md"))
    paths.update(str(path.relative_to(root)) for path in (root / "workspace/scripts").glob("*.py"))
    paths.update(str(path.relative_to(root)) for path in (root / "workspace/scripts/tests").glob("*.py"))
    sys.path.insert(0, str(root / "workspace/scripts"))
    import workspace_views

    empty = {
        "workspace/docs/WORK.md": workspace_views.work_block([]),
        "workspace/docs/HISTORY.md": workspace_views.history_block([]),
        "workspace/docs/work-items/README.md": workspace_views.management_block([]),
    }
    result: dict[str, bytes] = {}
    for relative in sorted(paths):
        source = root / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"模板白名单文件缺失或为符号链接：{relative}")
        content = source.read_bytes()
        if relative in VIEWS:
            text = content.decode("utf-8")
            if len(VIEW_RE.findall(text)) != 1:
                raise ValueError(f"派生区块必须恰好一个：{relative}")
            replacement = "<!-- workspace-view:start -->\n" + empty[relative].strip("\n") + "\n<!-- workspace-view:end -->"
            content = VIEW_RE.sub(lambda _: replacement, text).encode("utf-8")
        result[relative] = content
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="单向生成发行副本")
    mode.add_argument("--check", action="store_true", help="只读检查发行副本漂移")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--destination", type=Path, help="隔离发行测试的输出目录")
    args = parser.parse_args()
    root = args.root.resolve()
    destination = args.destination or root / "dist/ai-collab-bootstrap/templates"
    if destination.is_symlink():
        parser.error("发行根目录不能是符号链接")
    destination = destination.resolve()
    if destination == root or root.is_relative_to(destination):
        parser.error("发行目录不能覆盖主模板根或其父目录")
    try:
        files = release_files(root)
        manifest = {"version": 1, "files": {
            relative: hashlib.sha256(content).hexdigest()
            for relative, content in files.items()
        }}
        previous: dict[str, str] = {}
        manifest_path = destination / MANIFEST
        if manifest_path.is_file():
            previous = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", {})
        # Only known retired scaffold paths may be removed. Unknown files are preserved.
        retired = [path for path in sorted(RETIRED) if (destination / path).is_file()]
        obsolete = set(previous) - set(files) - RETIRED
        if obsolete:
            raise ValueError("发行清单有未声明迁移的旧文件，保留并请维护者处理：" + ", ".join(sorted(obsolete)))
        changed = []
        for relative, content in files.items():
            target = destination / relative
            if target.is_symlink() or any(parent.is_symlink() for parent in target.parents if parent != destination.parent):
                raise ValueError(f"发行路径不能经符号链接写入：{relative}")
            if not target.is_file() or target.read_bytes() != content:
                changed.append(relative)
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        manifest_changed = not manifest_path.is_file() or manifest_path.read_bytes() != manifest_bytes
        if args.check:
            if changed or retired or manifest_changed:
                print("发行副本漂移：" + ", ".join(changed + retired + ([MANIFEST] if manifest_changed else [])))
                return 1
            print(f"发行副本检查通过：{len(files)} 个白名单文件；真实工作项不进入副本")
            return 0
        for relative in changed:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(files[relative])
        for relative in retired:
            (destination / relative).unlink()
        if manifest_changed:
            destination.mkdir(parents=True, exist_ok=True)
            manifest_path.write_bytes(manifest_bytes)
        print(f"发行副本已生成：{len(files)} 个文件，更新 {len(changed)}，移除 {len(retired)} 个退役空骨架")
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
