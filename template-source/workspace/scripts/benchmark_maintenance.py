#!/usr/bin/env python3
"""Compare reproducible structural costs, without estimating model tokens or time.

Both versions use isolated repositories and the same maintenance acceptance
criteria. This is a tooling-change diagnostic, not a new per-task requirement.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from tests.helpers import NEXT_ACTION, REPOSITORY, Fixture, document


OLD_ENTRIES = ("AGENTS.md", "README.md", "workspace/docs/README.md", "workspace/docs/WORK.md")
NEW_ENTRIES = ("AGENTS.md", "README.md", "workspace/docs/WORK.md")
ACCEPTANCE = (
    "## 范围与验收\n\n核对项目文档入口并保留用户文件，不修改业务代码。\n\n"
    "| ID | 条件 |\n|---|---|\n"
    "| AC-01 | project/docs/index.md 存在且为文件 |\n"
    "| AC-02 | protected-user.txt 的内容仍为用户原有内容 |\n"
)
PLAN = (
    "## 计划\n\n| ID | 目标 | 实现 AC | 验证方法 |\n|---|---|---|---|\n"
    "| BENCH-01A | 核对项目文档入口 | AC-01 | 检查文件存在 |\n"
    "| BENCH-01B | 核对用户文件未改变 | AC-02 | 比较原始内容 |\n"
)
VERIFICATION = (
    "## 验证\n\n| 验收 | 状态 | 方法或命令 | 结果或证据 | 限制 |\n|---|---|---|---|---|\n"
    "| AC-01 | passed | Python pathlib.is_file | 临时仓库 project/docs/index.md 存在；命令退出码 0 | 不代表业务验收 |\n"
    "| AC-02 | passed | Python read_text 比较原始内容 | 用户原有内容完全一致；命令退出码 0 | 仅覆盖临时用户文件 |\n"
)


def record_cost(fixture: Fixture) -> dict[str, int]:
    files = list((fixture.records / "bench-01").glob("*.md"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in files)
    readme = (fixture.records / "bench-01/README.md").read_text(encoding="utf-8")
    occurrences = readme.count(NEXT_ACTION)
    return {
        "record_markdown_files": len(files),
        "record_unicode_characters_before_checkpoint": sum(len(path.read_text(encoding="utf-8")) for path in files),
        "readme_next_action_occurrences": occurrences,
        "readme_duplicate_next_action_copies": max(0, occurrences - 1),
        "fixed_impact_matrix_rows": len(re.findall(r"^\| DOC-[A-Z-]+ \|", text, re.MULTILINE)),
    }


def actual_acceptance(fixture: Fixture) -> None:
    code = (
        "from pathlib import Path; "
        "assert Path('project/docs/index.md').is_file(); "
        "assert Path('protected-user.txt').read_text(encoding='utf-8') == '用户原有内容\\n'; "
        "print('AC-01 passed; AC-02 passed')"
    )
    fixture.run(sys.executable, "-c", code)


def prepare_task(fixture: Fixture, *, old: bool, long: bool) -> None:
    actual_acceptance(fixture)
    if old:
        readme = fixture.legacy("BENCH-01", 3)
        (readme.parent / "spec.md").write_text(document("BENCH-01 范围", ACCEPTANCE, work_item="BENCH-01"), encoding="utf-8")
        plan = (readme.parent / "plan.md").read_text(encoding="utf-8")
        if long:
            readme.write_text(readme.read_text().replace("stage: BENCH-01A", "stage: BENCH-01B"), encoding="utf-8")
            plan = plan.replace("| BENCH-01A | 修复入口 | AC-01 | 链接检查 |", "| BENCH-01A | 核对项目文档入口 | AC-01 | 检查文件存在 |\n| BENCH-01B | 核对用户文件未改变 | AC-02 | 比较原始内容 |")
            (readme.parent / "plan.md").write_text(plan, encoding="utf-8")
        else:
            (readme.parent / "plan.md").write_text(plan.replace("| 修复入口 | AC-01 |", "| 核对入口与用户文件 | AC-01、AC-02 |"), encoding="utf-8")
        (readme.parent / "evidence.md").write_text(document("BENCH-01 Evidence", VERIFICATION, work_item="BENCH-01"), encoding="utf-8")
    else:
        readme = fixture.item("BENCH-01", status="completed", stage="BENCH-01B" if long else None,
                              spec="./spec.md" if long else None)
        original = readme.read_text(encoding="utf-8")
        header = original.split("---", 2)[:2]
        original_header = "---".join(header) + "---\n"
        body = f"\n# BENCH-01 维护入口核对\n\n"
        if long:
            body += "## 范围与计划\n\n[范围与验收](spec.md) · [分阶段计划](plan.md)\n\n"
            (readme.parent / "spec.md").write_text(document("BENCH-01 范围", ACCEPTANCE, work_item="BENCH-01"), encoding="utf-8")
            (readme.parent / "plan.md").write_text(document("BENCH-01 Plan", PLAN + "\n## 文档影响\n\n仅本工作项；没有稳定产品或架构事实变化。", work_item="BENCH-01"), encoding="utf-8")
        else:
            body += ACCEPTANCE + "\n## 计划\n\n核对两个条件，不改用户文件；文档影响：仅本工作项。\n\n"
        body += "## 关键事件\n\n实际核对入口和用户内容，未改变业务范围。\n\n" + VERIFICATION
        readme.write_text(original_header + body, encoding="utf-8")
    fixture.refresh()


def close_checks(fixture: Fixture, *, old: bool) -> list[dict[str, object]]:
    results = []
    if old:
        calls = (
            ("workspace_views.py", ("--check",), True),
            ("document_health_check.py", ("--full",), True),
            ("check_markdown_links.py", (), False),
        )
        for name, args, root_argument in calls:
            result = fixture.script(name, *args, root_argument=root_argument)
            results.append({"command": name + " " + " ".join(args), "exit_code": result.returncode,
                            "summary": (result.stdout + result.stderr).strip()})
        result = fixture.run("git", "diff", "--check")
        results.append({"command": "git diff --check", "exit_code": result.returncode,
                        "summary": (result.stdout + result.stderr).strip() or "无空白错误"})
    else:
        result = fixture.script("maintain.py", "--checkpoint", "BENCH-01")
        results.append({"command": "maintain.py --checkpoint BENCH-01", "exit_code": result.returncode,
                        "summary": (result.stdout + result.stderr).strip()})
    return results


def version_result(source: Path, *, old: bool) -> dict[str, object]:
    fixture = Fixture(source)
    try:
        fixture.refresh()
        entries = OLD_ENTRIES if old else NEW_ENTRIES
        entry_cost = {
            "pages": list(entries),
            "unicode_characters": sum(len((fixture.root / name).read_text(encoding="utf-8")) for name in entries),
            "basis": "首次接手基础入口；派生视图为空；不含所选工作项及按需深入页面",
        }
        if old:
            default_files = len(list((source / "workspace/templates/work-item").glob("*.md")))
            default_basis = "旧 README 的初始化方式：复制完整五文件工作项模板"
        else:
            fixture.script("maintain.py", "--new", "ENTRY-01", "--title", "预建结构样例")
            default_files = len(list((fixture.records / "entry-01").glob("*.md")))
            default_basis = "实际运行 --new 后预建的工作项 Markdown 数；不计可选模板库存"
    finally:
        fixture.close()
    scenarios = {}
    for long in (False, True):
        fixture = Fixture(source)
        try:
            prepare_task(fixture, old=old, long=long)
            costs = record_cost(fixture)
            checks = close_checks(fixture, old=old)
            actual_acceptance(fixture)
            costs["explicit_close_commands"] = len(checks)
            scenarios["two_stage_task" if long else "small_maintenance_task"] = {
                **costs, "actual_checks": checks,
                "business_acceptance": "AC-01、AC-02 在隔离仓库中实际运行并通过",
                "default_bundle": "旧默认五文件实例化" if old else "新单页或按需拆分实例化",
            }
        finally:
            fixture.close()
    return {
        "first_visit_entry": entry_cost,
        "default_precreated_work_item_files": default_files,
        "default_precreated_file_basis": default_basis,
        "scenarios": scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", type=Path, required=True, help="旧版本的只读归档目录")
    parser.add_argument("--root", type=Path, default=REPOSITORY, help="新版本模板根目录")
    parser.add_argument("--json", action="store_true", help="打印可保存的 JSON")
    args = parser.parse_args()
    result = {
        "measurement": "结构成本；Unicode 字符数、记录文件数和显式命令数，不是 token、运行耗时或长期效果",
        "qualification": "旧默认 bundle 为五文件，不意味着旧规范每种任务最少必须五文件；复杂度相同的场景使用同一工作项及相同 AC。",
        "old": version_result(args.baseline_root.resolve(), old=True),
        "new": version_result(args.root.resolve(), old=False),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["measurement"])
        print(result["qualification"])
        for label in ("old", "new"):
            version = result[label]
            print(f"{label}: 基础入口 {version['first_visit_entry']['unicode_characters']} 字符，默认预建 {version['default_precreated_work_item_files']} 个文件")
            for name, scenario in version["scenarios"].items():
                print(f"  {name}: {scenario['record_markdown_files']} 个记录文件，下一步重复副本 {scenario['readme_duplicate_next_action_copies']}，影响表 {scenario['fixed_impact_matrix_rows']} 行，收口 {scenario['explicit_close_commands']} 条命令；实际检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
