#!/usr/bin/env python3
"""One explicit entry for read-only checks, checkpoints and minimal work items."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True

from document_health_check import collect_errors
from workspace_views import CHECK_END, CHECK_START, frontmatter, load_items, update_views


ROOT = Path(__file__).resolve().parents[2]
ITEM_ID_RE = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+")


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    summary: str


def git_context(root: Path) -> tuple[str, str] | None:
    """Inspect a repository; do not initialize Git or alter its index."""
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, text=True, capture_output=True)
        if result.returncode or Path(result.stdout.strip()).resolve() != root:
            return None
        head = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=root, text=True, capture_output=True)
        branch = subprocess.run(["git", "symbolic-ref", "--short", "-q", "HEAD"], cwd=root, text=True, capture_output=True)
        return (head.stdout.strip() if not head.returncode else "none", branch.stdout.strip() if not branch.returncode else "none")
    except OSError:
        return None


def git_diff_check(root: Path) -> tuple[CheckResult, list[str]]:
    if git_context(root) is None:
        return CheckResult("git diff --check", "not_run", "N/A：根目录没有 Git 仓库，未验证差异空白"), []
    try:
        result = subprocess.run(["git", "diff", "--check"], cwd=root, text=True, capture_output=True)
    except OSError:
        return CheckResult("git diff --check", "failed", "无法执行 Git"), ["无法执行 git diff --check"]
    if result.returncode:
        # Raw output may contain private file content or local paths. Record only
        # the observed exit code; the user can inspect Git locally for details.
        summary = f"退出码 {result.returncode}；存在差异空白错误"
        return CheckResult("git diff --check", "failed", summary), [summary]
    return CheckResult("git diff --check", "passed", "退出码 0"), []


def run_checks(root: Path, write_views: bool = False) -> tuple[list[CheckResult], list[str]]:
    items, view_errors = update_views(root, write_views)
    results = [CheckResult("工作项与派生视图", "failed" if view_errors else "passed", f"{len(view_errors)} 个错误" if view_errors else f"{len(items)} 个工作项，3 个派生视图")]
    doc_errors, counts = collect_errors(root, full=True, include_derived=False)
    results.append(CheckResult("文档结构与全部本地链接", "failed" if doc_errors else "passed", f"{len(doc_errors)} 个错误" if doc_errors else f"{counts['stable']} 个稳定文档，{counts['links']} 个链接和锚点"))
    git_result, git_errors = git_diff_check(root)
    results.append(git_result)
    return results, view_errors + doc_errors + git_errors


def result_block(results: list[CheckResult]) -> str:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    rows = [CHECK_START, "## 工具检查", "", f"检查时间：{timestamp}", "", "仅记录本次工具执行的结构、链接与 Git 检查；不代表业务 AC 通过。", "", "| 检查 | 状态 | 本次结果 |", "|---|---|---|"]
    rows.extend(f"| {result.name} | {result.status} | {result.summary} |" for result in results)
    rows.extend(["", CHECK_END])
    return "\n".join(rows)


def write_result_block(path: Path, results: list[CheckResult]) -> None:
    original = path.read_text(encoding="utf-8")
    block = result_block(results)
    if CHECK_START in original or CHECK_END in original:
        if original.count(CHECK_START) != 1 or original.count(CHECK_END) != 1 or original.index(CHECK_START) > original.index(CHECK_END):
            raise ValueError("工具检查受控区块标记必须恰好各一个且顺序正确")
        before, remainder = original.split(CHECK_START, 1)
        _, after = remainder.split(CHECK_END, 1)
        updated = before + block + after
    else:
        updated = original + ("" if original.endswith("\n\n") else "\n" if original.endswith("\n") else "\n\n") + block + "\n"
    path.write_text(updated, encoding="utf-8")


def find_item(root: Path, item_id: str) -> Path:
    if not ITEM_ID_RE.fullmatch(item_id):
        raise ValueError("工作项 ID 必须使用大写字母、数字和连字符")
    records = root / "workspace/docs/work-items/records"
    if records.is_dir():
        for path in sorted(records.glob("*/README.md")):
            try:
                if frontmatter(path).get("id", "").strip("'\"") == item_id:
                    return path
            except ValueError:
                continue
    raise ValueError(f"未找到工作项 {item_id}")


def new_item(root: Path, item_id: str, title: str) -> tuple[Path, list[str]]:
    if not ITEM_ID_RE.fullmatch(item_id):
        raise ValueError("工作项 ID 必须使用大写字母、数字和连字符")
    if not title.strip() or "\n" in title or "\r" in title:
        raise ValueError("标题必须是非空单行文字")
    records = root / "workspace/docs/work-items/records"
    directory = records / item_id.lower()
    if directory.exists():
        raise ValueError(f"工作项目录已存在: {item_id.lower()}")
    items, errors = load_items(root)
    if errors:
        raise ValueError("现有工作项校验失败，先修正现有元数据")
    if any(item.value("id") == item_id for item in items):
        raise ValueError(f"工作项 ID 已登记: {item_id}")
    for relative in ("workspace/docs/WORK.md", "workspace/docs/HISTORY.md", "workspace/docs/work-items/README.md"):
        if not (root / relative).is_file():
            raise ValueError("缺少派生视图入口，先初始化 Workspace")
    now = datetime.now().astimezone()
    timestamp = now.isoformat(timespec="minutes")
    context = git_context(root)
    head, branch = context if context is not None else ("none", "none")
    content = "\n".join([
        "---", "schema_version: 4", "document_status: active", f"last_updated: {now.date().isoformat()}",
        f"id: {item_id}", f"title: {json.dumps(title.strip(), ensure_ascii=False)}", "status: planned",
        f"updated_at: {timestamp}", "next_action: 填写范围、AC 与实施步骤", f"branch: {json.dumps(branch)}", f"head: {head}", "---",
        "", f"# {item_id} {title.strip()}", "", "## 目标与范围", "", "待填写：用户成果、接受范围与不处理的内容。",
        "", "## 验收条件", "", "| AC | 验收条件 |", "|---|---|", "| AC-01 | 待填写 |",
        "", "## 计划", "", "待填写：具体步骤与验证方法；只有需要分阶段时才填写 stage。",
        "", "## 交接", "", "当前无执行记录；基线在创建时采集，检查点不会覆盖它。",
        "", "## 验证", "", "| 验收 | 状态 | 方法或命令 | 结果或证据 | 限制 |", "|---|---|---|---|---|",
        "| AC-01 | pending | 未运行 | 未验证 | 范围和验收条件待填写 |", "",
    ])
    template = root / "workspace/templates/work-item/README.md"
    if template.is_file() and frontmatter(template).get("schema_version", "").strip("'\"") == "4":
        template_text = template.read_text(encoding="utf-8")
        body = template_text.split("---", 2)[2].replace("<WORK-ID>", item_id).replace("<TITLE>", title.strip())
        next_action = frontmatter(template).get("next_action", "明确目标与验收条件")
        header = "\n".join([
            "---", "schema_version: 4", "document_status: active", f"last_updated: {now.date().isoformat()}",
            f"id: {item_id}", f"title: {json.dumps(title.strip(), ensure_ascii=False)}", "status: planned",
            f"updated_at: {timestamp}", f"next_action: {next_action}", f"branch: {json.dumps(branch)}", f"head: {head}", "---",
        ])
        content = header + body
    directory.mkdir()
    path = directory / "README.md"
    path.write_text(content, encoding="utf-8")
    _, view_errors = update_views(root, write=True)
    return path, view_errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="只读检查（默认）")
    mode.add_argument("--checkpoint", metavar="ID", help="刷新视图、检查并记录此项工具结果")
    mode.add_argument("--new", metavar="ID", help="创建只有 README 的 Schema 4 工作项")
    parser.add_argument("--title", help="新工作项标题，仅与 --new 使用")
    parser.add_argument("--root", type=Path, default=ROOT, help="指定仓库根目录")
    args = parser.parse_args()
    if args.new and not args.title:
        parser.error("--new 必须同时提供 --title")
    if args.title and not args.new:
        parser.error("--title 只能与 --new 使用")
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("指定的根目录不存在")
    try:
        if args.new:
            path, errors = new_item(root, args.new, args.title)
            print(f"已创建: {path.relative_to(root)}（Schema 4，planned；范围与 AC 待填写）")
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1 if errors else 0
        item_path = find_item(root, args.checkpoint) if args.checkpoint else None
        # Refuse malformed blocks before any checkpoint mutation.
        if item_path is not None:
            text = item_path.read_text(encoding="utf-8")
            if (CHECK_START in text or CHECK_END in text) and (text.count(CHECK_START) != 1 or text.count(CHECK_END) != 1 or text.index(CHECK_START) > text.index(CHECK_END)):
                raise ValueError("工具检查受控区块标记必须恰好各一个且顺序正确")
        results, errors = run_checks(root, write_views=item_path is not None)
        frozen = item_path is not None and frontmatter(item_path).get("status", "").strip("'\"") in {"completed", "cancelled"}
        if item_path is not None and not frozen:
            write_result_block(item_path, results)
        for result in results:
            print(f"{result.status}: {result.name}；{result.summary}")
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if frozen:
            print("终态工作项保持冻结；本次工具检查结果仅输出，派生视图已核对。")
        elif item_path is not None:
            print(f"已记录工具检查: {item_path.relative_to(root)}；业务状态与基线保持原值。")
        return 1 if errors else 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
