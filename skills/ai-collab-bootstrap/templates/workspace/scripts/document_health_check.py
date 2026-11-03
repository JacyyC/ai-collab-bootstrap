#!/usr/bin/env python3
"""Validate local collaboration contracts and real links without imposing a product layout."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
from markdown_checks import SKIP_PARTS, check_links, markdown_files
from workspace_views import frontmatter, update_views

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_NAMES = (
    "README.md", "AGENTS.md",
    "workspace/docs/DOCUMENTATION_POLICY.md", "workspace/docs/DOCUMENT_LIFECYCLE.md",
    "workspace/docs/PROJECT_LAYOUT.md", "workspace/docs/WORK.md", "workspace/docs/HISTORY.md",
    "workspace/templates/work-item/README.md", "workspace/templates/work-item/spec.md",
    "workspace/templates/work-item/plan.md", "workspace/templates/work-item/log.md",
    "workspace/templates/work-item/evidence.md", "workspace/scripts/workspace_views.py",
    "workspace/scripts/document_health_check.py", "workspace/scripts/markdown_checks.py",
    "workspace/scripts/maintain.py",
)
REGISTRY_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|", re.MULTILINE)
REGISTRY_SECTION_RE = re.compile(r"^## 稳定文件登记表\s*$\n(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)


def parse_front_matter(path: Path) -> dict[str, str]:
    try:
        return {key: value.strip("'\"") for key, value in frontmatter(path).items()}
    except ValueError:
        return {}


def tracked_markdown(root: Path) -> tuple[list[Path], list[Path]]:
    try:
        git_root = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL).strip()
        if Path(git_root).resolve() != root.resolve():
            return markdown_files(root), []
        output = subprocess.check_output(["git", "-c", "core.quotePath=false", "ls-files", "--cached"], cwd=root, text=True)
        tracked = [root / line for line in output.splitlines() if line.lower().endswith(".md")]
    except (OSError, subprocess.CalledProcessError):
        return markdown_files(root), []
    return [path for path in tracked if path.is_file()], [path for path in tracked if not path.is_file()]


def is_dynamic(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return relative.as_posix().startswith("workspace/docs/work-items/records/") or relative.name == "开发日志.md"


def stable_markdown(root: Path) -> list[Path]:
    # Native docs can live anywhere. Their existing prose/YAML conventions are
    # preserved; work-item metadata has its own versioned parser.
    return [path for path in markdown_files(root) if not is_dynamic(path, root) and "archive" not in path.relative_to(root).parts]


def check_registry(errors: list[str], root: Path) -> None:
    """Validate an existing registry without requiring another file ledger."""
    navigation = root / "workspace/docs/README.md"
    if not navigation.is_file():
        return
    match = REGISTRY_SECTION_RE.search(navigation.read_text(encoding="utf-8"))
    if not match:
        return
    for entry, count in Counter(REGISTRY_ROW_RE.findall(match.group(1))).items():
        if any(marker in entry for marker in ("<", ">", "{", "}")):
            continue
        target = (root / entry.rstrip("/")).resolve()
        if not target.is_relative_to(root):
            errors.append(f"稳定文件登记路径越界: {entry}")
        elif not target.exists():
            errors.append(f"稳定文件登记目标不存在: {entry}")
        if count > 1:
            errors.append(f"稳定文件登记重复 ({count} 次): {entry}")


def check_declared_roles(paths: list[Path], errors: list[str], root: Path) -> None:
    """Check explicit architecture metadata wherever the project keeps it."""
    for path in paths:
        values = parse_front_matter(path)
        role = values.get("framework_role")
        if not role:
            continue
        label = path.relative_to(root)
        if role not in {"current", "target"}:
            errors.append(f"非法 framework_role: {label}")
            continue
        for field, expected in (("target", "target"), ("based_on", "current")):
            value = values.get(field)
            if not value or value in {"null", "~"} or any(char in value for char in "<>{}"):
                continue
            target = (path.parent / value).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                errors.append(f"架构引用目标不存在或越界: {label} {field}")
            else:
                actual = parse_front_matter(target).get("framework_role")
                if actual and actual != expected:
                    errors.append(f"架构引用角色不符: {label} {field}")


def collect_errors(root: Path, full: bool = False, include_derived: bool = True) -> tuple[list[str], dict[str, int]]:
    root = root.resolve()
    errors = [f"缺少必需治理入口: {name}" for name in REQUIRED_NAMES if not (root / name).is_file()]
    tracked, missing = tracked_markdown(root)
    for path in missing:
        relative = path.relative_to(root)
        if SKIP_PARTS.intersection(relative.parts):
            continue
        # Retiring an ordinary stable page is allowed when all live references
        # are repaired. Required contracts and frozen records cannot disappear.
        if relative.as_posix() in REQUIRED_NAMES or is_dynamic(path, root) or "archive" in relative.parts:
            errors.append(f"Git 已跟踪 Markdown 但工作树缺失: {relative}")
    paths = markdown_files(root)
    _, links = check_links(paths, errors, root)
    check_registry(errors, root)
    stable = stable_markdown(root)
    check_declared_roles(stable, errors, root)
    if full and include_derived:
        _, derived_errors = update_views(root)
        errors.extend(derived_errors)
    return errors, {"tracked": len(tracked), "stable": len(stable), "links": links}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--full", action="store_true", help="同时核对工作项及派生视图")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors, counts = collect_errors(args.root, args.full)
    if errors:
        print("文档检查失败")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"文档检查通过: {counts['tracked']} 个跟踪 Markdown，{counts['stable']} 个非工作项文档，{counts['links']} 个本地链接和锚点")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
