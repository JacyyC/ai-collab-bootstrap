#!/usr/bin/env python3
"""Check documentation structure without treating it as product verification."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True

from markdown_checks import ABSOLUTE_LOCAL_PATH_RE, SKIP_PARTS, check_links, markdown_files, without_fences
from workspace_views import frontmatter, update_views


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_NAMES = (
    "README.md", "AGENTS.md", "project/README.md", "project/docs/index.md",
    "workspace/README.md", "workspace/docs/README.md",
    "workspace/docs/DOCUMENTATION_POLICY.md", "workspace/docs/DOCUMENT_LIFECYCLE.md",
    "workspace/docs/WORK.md", "workspace/docs/HISTORY.md", "workspace/docs/work-items/README.md",
    "workspace/docs/framework/README.md", "workspace/docs/framework/current/v1.md",
    "workspace/templates/work-item/README.md",
    "workspace/scripts/workspace_views.py", "workspace/scripts/check_markdown_links.py",
    "workspace/scripts/document_health_check.py", "workspace/scripts/markdown_checks.py",
    "workspace/scripts/maintain.py",
)
REQUIRED = [ROOT / name for name in REQUIRED_NAMES]
H1_RE = re.compile(r"^#\s+(.+?)\s*#*\s*$", re.MULTILINE)
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
    missing = [path for path in tracked if not path.is_file()]
    return [path for path in tracked if path.is_file()], missing


def is_dynamic(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return relative.as_posix().startswith("workspace/docs/work-items/records/") or relative.name == "开发日志.md"


def stable_markdown(root: Path) -> list[Path]:
    paths: set[Path] = {root / "README.md", root / "AGENTS.md", root / "workspace/README.md", root / "project/README.md"}
    for base in (root / "workspace/docs", root / "project/docs"):
        if base.is_dir():
            paths.update(path for path in base.rglob("*.md") if path.is_file())
    return sorted(path for path in paths if path.is_file() and not is_dynamic(path, root) and not {".trae", "archive"}.intersection(path.relative_to(root).parts))


def registry_entries(text: str, errors: list[str]) -> list[str]:
    match = REGISTRY_SECTION_RE.search(text)
    if not match:
        errors.append("Workspace README 缺少稳定文件登记表")
        return []
    return REGISTRY_ROW_RE.findall(match.group(1))


def check_registry(paths: list[Path], errors: list[str], root: Path) -> None:
    workspace_readme = root / "workspace/docs/README.md"
    if not workspace_readme.is_file():
        return
    if parse_front_matter(workspace_readme).get("governance_schema") not in {"3", "4"}:
        errors.append("workspace/docs/README.md governance_schema 必须为 3 或 4")
    entries = registry_entries(workspace_readme.read_text(encoding="utf-8"), errors)
    for entry, count in sorted(Counter(entries).items()):
        if any(marker in entry for marker in ("<", ">", "{", "}")):
            continue
        entry_path = root / entry.rstrip("/")
        if count > 1:
            errors.append(f"稳定文件登记重复 ({count} 次): {entry}")
        if not entry_path.exists():
            errors.append(f"稳定文件登记目标不存在: {entry}")
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if not any(relative == entry.rstrip("/") or relative.startswith(entry.rstrip("/") + "/") for entry in entries):
            errors.append(f"稳定文件未登记: {relative}")


def check_orphans(paths: list[Path], graph: dict[Path, set[Path]], errors: list[str], root: Path) -> None:
    roots = [root / name for name in ("README.md", "AGENTS.md", "project/docs/index.md", "workspace/README.md", "workspace/docs/README.md", "workspace/docs/framework/README.md")]
    reachable = {path.resolve() for path in roots if path.is_file()}
    pending = list(reachable)
    while pending:
        for target in graph.get(pending.pop(), set()):
            if target not in reachable:
                reachable.add(target)
                pending.append(target)
    for path in paths:
        if path.resolve() not in reachable:
            errors.append(f"孤立稳定文档: {path.relative_to(root)}")


def check_headings(paths: list[Path], errors: list[str], root: Path) -> None:
    for path in paths:
        h1 = H1_RE.findall(without_fences(path.read_text(encoding="utf-8")))
        if len(h1) != 1:
            errors.append(f"稳定文档必须恰好有一个 H1: {path.relative_to(root)}")


def check_status_headers(paths: list[Path], errors: list[str], root: Path) -> None:
    allowed = {"draft", "active", "deprecated", "superseded", "archived"}
    for path in paths:
        values = parse_front_matter(path)
        if not values:
            errors.append(f"稳定文档缺少有效 YAML 头: {path.relative_to(root)}")
            continue
        if values.get("document_status") not in allowed:
            errors.append(f"非法 document_status: {path.relative_to(root)}")
        if not values.get("last_updated"):
            errors.append(f"稳定文档缺少 last_updated: {path.relative_to(root)}")


def check_framework_roles(errors: list[str], root: Path) -> None:
    current = root / "workspace/docs/framework/current/v1.md"
    target = root / "workspace/docs/framework/target/v1.md"
    current_values = parse_front_matter(current) if current.is_file() else {}
    target_values = parse_front_matter(target) if target.is_file() else {}
    if current.is_file() and current_values.get("framework_role") != "current":
        errors.append("Current Framework 缺少 framework_role: current")
    if target.is_file() and target_values.get("framework_role") != "target":
        errors.append("Target Framework 缺少 framework_role: target")
    if current_values.get("target") and (current.parent / current_values["target"]).resolve() != target.resolve():
        errors.append("Current Framework 的 target 链接不指向 target/v1.md")
    if target_values.get("based_on") and (target.parent / target_values["based_on"]).resolve() != current.resolve():
        errors.append("Target Framework 的 based_on 链接不指向 current/v1.md")
    if current_values.get("target") and not target.is_file():
        errors.append("Current Framework 的 target 目标不存在")
    if target_values.get("based_on") and not current.is_file():
        errors.append("Target Framework 的 based_on 目标不存在")
    if current.is_file() and "## 当前限制" not in current.read_text(encoding="utf-8"):
        errors.append("Current Framework 必须有可见的当前限制章节")
    if target.is_file() and "## 剩余差异与门槛" not in target.read_text(encoding="utf-8"):
        errors.append("Target Framework 必须有剩余差异与门槛章节")


def collect_errors(root: Path, full: bool = False, include_derived: bool = True) -> tuple[list[str], dict[str, int]]:
    """Run each structural check once, shared by the CLI and maintenance entry."""
    root = root.resolve()
    errors: list[str] = []
    for name in REQUIRED_NAMES:
        if not (root / name).is_file():
            errors.append(f"缺少必需治理入口: {name}")
    tracked, missing = tracked_markdown(root)
    for path in missing:
        relative = path.relative_to(root).as_posix()
        if SKIP_PARTS.intersection(path.relative_to(root).parts):
            continue
        stable_location = relative.startswith(("workspace/docs/", "project/docs/")) or relative in {"workspace/README.md", "project/README.md"}
        # An optional stable page may be deliberately retired before commit.
        # Required paths, registry entries and live links still catch incomplete
        # removals; historical work-item records must never silently disappear.
        if relative in REQUIRED_NAMES or is_dynamic(path, root) or not stable_location or "archive" in path.relative_to(root).parts:
            errors.append(f"Git 已跟踪 Markdown 但工作树缺失: {relative}")
    stable = stable_markdown(root)
    check_status_headers(stable, errors, root)
    graph, links = check_links(markdown_files(root), errors, root)
    check_registry(stable, errors, root)
    check_orphans(stable, graph, errors, root)
    check_headings(stable, errors, root)
    check_framework_roles(errors, root)
    if full:
        for path in stable:
            if ABSOLUTE_LOCAL_PATH_RE.search(path.read_text(encoding="utf-8")):
                errors.append(f"稳定文档含本机绝对路径: {path.relative_to(root)}")
        if include_derived:
            _, derived_errors = update_views(root)
            errors.extend(derived_errors)
    return errors, {"tracked": len(tracked), "stable": len(stable), "links": links}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="运行标准结构检查")
    parser.add_argument("--full", action="store_true", help="同时检查绝对路径和派生视图")
    parser.add_argument("--root", type=Path, default=ROOT, help="指定仓库根目录")
    args = parser.parse_args()
    errors, counts = collect_errors(args.root, args.full)
    if errors:
        print(f"文档健康检查失败 ({'full' if args.full else 'standard'})")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"文档健康检查通过 ({'full' if args.full else 'standard'}): {counts['tracked']} 个跟踪 Markdown，{counts['stable']} 个稳定文档，{counts['links']} 个本地链接和锚点")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
