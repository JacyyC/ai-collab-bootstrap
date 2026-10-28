#!/usr/bin/env python3
"""Validate work-item metadata and derive deterministic management views."""

from __future__ import annotations

import argparse
import ast
import re
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

sys.dont_write_bytecode = True

from markdown_checks import without_fences


WORKSPACE = Path(__file__).resolve().parents[1]
DOCS = WORKSPACE / "docs"
RECORDS = DOCS / "work-items" / "records"
START = "<!-- workspace-view:start -->"
END = "<!-- workspace-view:end -->"
SCHEMA_VERSIONS = {"2", "3", "4"}
IMPACT_SCHEMA_VERSION = "1"
IMPACT_IDS = {
    "DOC-ROOT",
    "DOC-HUMAN",
    "DOC-CURRENT",
    "DOC-TARGET",
    "DOC-GOVERNANCE",
    "DOC-TOOLS",
    "DOC-WORK-ITEM",
    "DOC-VIEWS",
    "DOC-HISTORY",
    "DOC-CROSS-REPO",
}
IMPACT_ROW_RE = re.compile(r"^\|\s*(DOC-[A-Z0-9-]+)\s*\|", re.MULTILINE)
STATUSES = {"planned", "ready", "active", "blocked", "paused", "completed", "cancelled"}
ACTIVE = {"ready", "active", "blocked", "paused"}
TERMINAL = {"completed", "cancelled"}
REQUIRED = {
    "schema_version",
    "document_status",
    "last_updated",
    "id",
    "title",
    "status",
    "stage",
    "priority",
    "branch",
    "created_at",
    "updated_at",
    "updated_by",
    "depends_on",
    "blocked_by",
    "next_action",
    "labels",
    "spec",
    "plan",
    "framework_scope",
}
REQUIRED_SCHEMA4 = {"schema_version", "document_status", "last_updated", "id", "title", "status", "updated_at", "next_action"}
CHECK_START = "<!-- maintenance-check:start -->"
CHECK_END = "<!-- maintenance-check:end -->"
LEGACY_DIRECTORY_IDS = {
    "audit-fix_v1": "AUDIT-FIX-01",
    "legacy-development-log": "LEGACY-LOG-01",
    "backend-debug-audit": "BACKEND-AUDIT",
}


@dataclass(frozen=True)
class Item:
    directory: str
    values: dict[str, str]

    def value(self, key: str) -> str:
        default = "P2" if key == "priority" and self.values.get("schema_version", "").strip("'\"") == "4" else ""
        value = self.values.get(key, default).strip().strip("'\"")
        return default if value in {"null", "~"} else value

    def baseline(self) -> str:
        return self.value("head") or self.value("base_head")

    def values_list(self, key: str) -> list[str]:
        raw = self.values.get(key, "").strip()
        if not raw or raw in {"[]", "null", "~"}:
            return []
        try:
            parsed = ast.literal_eval(raw)
        except (SyntaxError, ValueError) as exc:
            raise ValueError(f"{key} 必须是内联列表") from exc
        if not isinstance(parsed, (list, tuple)):
            raise ValueError(f"{key} 必须是内联列表")
        return [str(value).strip().strip("'\"") for value in parsed if str(value).strip()]


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("缺少起始 YAML 分隔符")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("缺少结束 YAML 分隔符") from exc
    result: dict[str, str] = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$", line)
        if not match:
            raise ValueError(f"第 {number} 行不是支持的扁平 YAML 字段")
        key = match.group(1)
        if key in result:
            raise ValueError(f"第 {number} 行重复字段 {key}")
        result[key] = (match.group(2) or "").strip()
    return result


def validate_schema3_plan(path: Path) -> None:
    values = frontmatter(path)
    if values.get("impact_schema", "").strip("'\"") != IMPACT_SCHEMA_VERSION:
        raise ValueError(f"plan impact_schema 必须为 {IMPACT_SCHEMA_VERSION}")
    ids = IMPACT_ROW_RE.findall(path.read_text(encoding="utf-8"))
    counts = Counter(ids)
    missing = sorted(IMPACT_IDS - set(ids))
    duplicates = sorted(item for item, count in counts.items() if count > 1)
    unexpected = sorted(set(ids) - IMPACT_IDS)
    problems = []
    if missing:
        problems.append(f"缺少文档影响类别 {', '.join(missing)}")
    if duplicates:
        problems.append(f"文档影响类别重复 {', '.join(duplicates)}")
    if unexpected:
        problems.append(f"不支持的文档影响类别 {', '.join(unexpected)}")
    if problems:
        raise ValueError("；".join(problems))


def validate_link_field(path: Path, field: str, value: str, schema: str = "3", records: Path = RECORDS) -> None:
    if not value or value in {"null", "~"}:
        return
    expected = f"./{field}.md"
    target = (path.parent / value).resolve()
    if field == "spec":
        try:
            relative = target.relative_to(records.resolve())
        except ValueError as exc:
            raise ValueError("共享 spec 必须位于同一 records 中的工作项 spec.md") from exc
        if len(relative.parts) != 2 or relative.name != "spec.md" or not target.is_file():
            raise ValueError("共享 spec 必须指向工作项的 spec.md")
        registration = target.parent / "README.md"
        if not registration.is_file():
            raise ValueError("共享 spec 的工作项必须已登记 README.md")
        registered_id = frontmatter(registration).get("id", "").strip("'\"")
        if registered_id != LEGACY_DIRECTORY_IDS.get(target.parent.name, target.parent.name.upper()):
            raise ValueError("共享 spec 的工作项登记 ID 与目录不符")
        return
    if value != expected or not target.is_file() or path.parent.resolve() not in target.parents:
        raise ValueError(f"{field} 必须是工作项目录内的 {expected} 或 null")


def section(text: str, titles: tuple[str, ...]) -> str:
    """Read named README sections without consuming subsequent peer sections."""
    parts: list[str] = []
    matches = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*#*\s*$", text, re.MULTILINE))
    for index, match in enumerate(matches):
        if match.group(2).strip() not in titles:
            continue
        end = len(text)
        for following in matches[index + 1:]:
            if len(following.group(1)) <= len(match.group(1)):
                end = following.start()
                break
        parts.append(text[match.end():end])
    return "\n".join(parts)


def without_tool_results(text: str) -> str:
    return re.sub(re.escape(CHECK_START) + r".*?" + re.escape(CHECK_END), "", text, flags=re.DOTALL)


def stage_is_defined(text: str, stage: str) -> bool:
    token = r"`?" + re.escape(stage) + r"`?"
    for line in without_fences(text).splitlines():
        if re.match(r"^\|\s*" + token + r"\s*\|", line):
            return True
        if re.match(r"^\s*(?:[-*+] |\d+[.)] )" + token + r"(?:\s*[:：—-]\s*|\s+)(?=\S)", line):
            return True
        if re.match(r"^#{1,6}\s+(?:Stage\s+)?" + token + r"(?:$|\s+|\s*[:：—])", line):
            return True
    return False


def validate_schema4(path: Path, item: Item) -> None:
    for key in REQUIRED_SCHEMA4:
        if not item.value(key):
            raise ValueError(f"Schema 4 字段 {key} 不能为空")
    if item.value("document_status") not in {"draft", "active", "deprecated", "superseded", "archived"}:
        raise ValueError("非法 document_status")
    try:
        date.fromisoformat(item.value("last_updated"))
        datetime.fromisoformat(item.value("updated_at"))
    except ValueError as exc:
        raise ValueError("Schema 4 日期必须使用实际 ISO 日期或时间") from exc
    original = path.read_text(encoding="utf-8")
    if (CHECK_START in original or CHECK_END in original) and (original.count(CHECK_START) != 1 or original.count(CHECK_END) != 1 or original.index(CHECK_START) > original.index(CHECK_END)):
        raise ValueError("工具检查受控区块标记必须恰好各一个且顺序正确")
    text = without_tool_results(original)
    prose = re.sub(r"`[^`\n]*`", "", without_fences(text))
    if item.value("status") != "planned" and re.search(r"<(?:[A-Z][A-Z0-9_-]*|[\u3400-\u9fff][^>\n]*)>|^\s*待(?:填写|补充)[：:]", prose, re.MULTILINE):
        raise ValueError("实际工作项仍有未填写占位符；planned 草稿可保留，执行前须填写范围与验收")
    stage = item.value("stage")
    if stage:
        plan = path.parent / "plan.md"
        plan_text = plan.read_text(encoding="utf-8") if plan.is_file() else ""
        inline_plan = section(text, ("计划", "实施计划"))
        if not (stage_is_defined(plan_text, stage) or stage_is_defined(inline_plan, stage)):
            raise ValueError(f"Stage {stage} 未出现在 Plan 或 README 计划中")
    plan = path.parent / "plan.md"
    if plan.is_file():
        plan_values = frontmatter(plan) if plan.read_text(encoding="utf-8").startswith("---") else {}
        if plan_values.get("impact_schema", "").strip("'\"") not in {"", "2"}:
            raise ValueError("Schema 4 Plan 如声明 impact_schema，必须为 2")
    if item.value("status") not in TERMINAL:
        return
    try:
        date.fromisoformat(item.value("closed_at"))
    except ValueError as exc:
        raise ValueError("Schema 4 closed_at 必须使用实际 ISO 日期") from exc
    evidence = path.parent / "evidence.md"
    verification = section(text, ("验证", "验证记录", "验收与验证"))
    if evidence.is_file():
        verification += "\n" + evidence.read_text(encoding="utf-8")
    verification = without_tool_results(verification)
    records: list[tuple[str, str, bool]] = []
    for line in verification.splitlines():
        ac = re.search(r"\bAC-\d+\b", line)
        if not ac:
            continue
        status = re.search(r"\b(passed|failed|not_run|pending)\b", line)
        if not status:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        status_index = next((index for index, cell in enumerate(cells) if re.fullmatch(r"`?(passed|failed|not_run|pending)`?", cell)), -1)
        # A table row has a method, result/evidence and limitation after status.
        # This establishes a traceable record, not the truth of its prose.
        substantive = status_index >= 0 and len(cells) >= status_index + 4 and all(
            cell and cell not in {"-", "待填写", "待补充", "TBD"} and not re.search(r"<[^>]+>", cell)
            for cell in cells[status_index + 1:status_index + 4]
        )
        if status.group(1) == "passed" and status_index >= 0 and any(cell in {"未运行", "未验证", "pending", "not_run"} for cell in cells[status_index + 1:status_index + 3]):
            substantive = False
        records.append((ac.group(0), status.group(1), substantive))
    if not records or not any(substantive for _, _, substantive in records):
        raise ValueError("Schema 4 终态必须有 AC 对应的验证记录（状态、方法、结果或证据、限制）")
    if item.value("status") == "completed":
        latest = {ac: (status, substantive) for ac, status, substantive in records}
        if any(status != "passed" or not substantive for status, substantive in latest.values()):
            raise ValueError("completed 每项 AC 的最后一条验收记录必须 passed，且有方法、结果和限制")
        spec_value = item.value("spec")
        spec = (path.parent / spec_value).resolve() if spec_value else path.parent / "spec.md"
        declared_text = spec.read_text(encoding="utf-8") if spec.is_file() else section(text, ("验收", "验收条件", "范围与验收", "目标与范围及验收"))
        declared = set(re.findall(r"\bAC-\d+\b", without_fences(declared_text)))
        passed = {ac for ac, (status, substantive) in latest.items() if status == "passed" and substantive}
        if not declared or declared - passed:
            raise ValueError("completed 必须逐项覆盖 Spec 或 README 已声明的 AC")


def load_items(root: Path | None = None) -> tuple[list[Item], list[str]]:
    items: list[Item] = []
    errors: list[str] = []
    seen: set[str] = set()
    records = (root / "workspace/docs/work-items/records") if root is not None else RECORDS
    if not records.is_dir():
        return [], ["缺少工作项目录: workspace/docs/work-items/records"]
    for directory in sorted(path for path in records.iterdir() if path.is_dir()):
        path = directory / "README.md"
        label = f"workspace/docs/work-items/records/{directory.name}/README.md"
        if not path.is_file():
            errors.append(f"{label}: 缺少 README.md")
            continue
        try:
            values = frontmatter(path)
            schema = values.get("schema_version", "").strip("'\"")
            missing = sorted((REQUIRED_SCHEMA4 if schema == "4" else REQUIRED) - values.keys())
            if missing:
                raise ValueError(f"缺少字段 {', '.join(missing)}")
            item = Item(directory.name, values)
            schema = item.value("schema_version")
            if schema not in SCHEMA_VERSIONS:
                raise ValueError(f"schema_version 必须为 2、3 或 4，当前为 {schema!r}")
            item_id = item.value("id")
            if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+", item_id):
                raise ValueError(f"id 格式无效: {item_id!r}")
            expected_id = LEGACY_DIRECTORY_IDS.get(directory.name, directory.name.upper())
            if item_id != expected_id:
                raise ValueError(f"目录 {directory.name!r} 必须包含 id {expected_id!r}")
            if schema == "4" and directory.name != item_id.lower():
                raise ValueError("Schema 4 工作项目录必须是 ID 对应的小写字母、数字和连字符")
            if item_id in seen:
                raise ValueError(f"工作项 ID {item_id} 重复")
            seen.add(item_id)
            if item.value("status") not in STATUSES:
                raise ValueError(f"非法 status {item.value('status')!r}")
            if not re.fullmatch(r"P[0-3]", item.value("priority")):
                raise ValueError("priority 必须使用 P0-P3")
            if not re.match(r"^\d{4}-\d{2}-\d{2}(?:T|$)", item.value("updated_at")):
                raise ValueError("updated_at 必须以 YYYY-MM-DD 开头")
            if schema == "3":
                if not item.baseline():
                    raise ValueError("Schema 3 必须有非空 head")
                if not item.value("next_action"):
                    raise ValueError("Schema 3 必须有非空 next_action")
                if item.value("plan") != "./plan.md":
                    raise ValueError("Schema 3 工作项必须有 ./plan.md")
                plan_path = directory / "plan.md"
                if not plan_path.is_file():
                    raise ValueError("Schema 3 工作项缺少 plan.md")
                validate_schema3_plan(plan_path)
            elif schema == "2" and not item.baseline():
                raise ValueError("Schema 2 必须包含 head 或 legacy base_head")
            for field in ("depends_on", "blocked_by", "labels", "framework_scope"):
                item.values_list(field)
            for field in ("spec", "plan"):
                validate_link_field(path, field, item.value(field), schema, records)
            closed_at = item.value("closed_at")
            terminal = item.value("status") in TERMINAL
            if terminal and not closed_at:
                raise ValueError("终态工作项必须包含 closed_at")
            if not terminal and closed_at:
                raise ValueError("非终态工作项不能包含 closed_at")
            if closed_at and not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:\.\.\d{2})?", closed_at):
                raise ValueError("closed_at 必须使用 YYYY-MM-DD 或历史日期范围")
            has_evidence = (directory / "evidence.md").is_file()
            has_legacy_source = item.value("document_status") == "archived" and (directory / "source.md.txt").is_file()
            if terminal and schema != "4" and not (has_evidence or has_legacy_source):
                raise ValueError("终态工作项必须包含 evidence.md，或显式归档 source.md.txt")
            if schema == "4":
                validate_schema4(path, item)
            items.append(item)
        except (OSError, ValueError) as exc:
            errors.append(f"{label}: {exc}")
    known = {item.value("id") for item in items}
    for item in items:
        for dependency in item.values_list("depends_on"):
            if dependency not in known:
                errors.append(f"{item.value('id')}: depends_on 引用了不存在的工作项 {dependency}")
        for blocker in item.values_list("blocked_by"):
            if blocker not in known and not re.fullmatch(r"G-[A-Z0-9-]+", blocker):
                errors.append(f"{item.value('id')}: blocked_by 引用了不存在的工作项或 G-* 门禁 {blocker}")
    dependencies = {item.value("id"): item.values_list("depends_on") for item in items}
    visited: set[str] = set()
    visiting: list[str] = []

    def visit(item_id: str) -> None:
        if item_id in visiting:
            errors.append("工作项依赖循环: " + " -> ".join(visiting[visiting.index(item_id):] + [item_id]))
            return
        if item_id in visited:
            return
        visiting.append(item_id)
        for dependency in dependencies.get(item_id, []):
            if dependency in dependencies:
                visit(dependency)
        visiting.pop()
        visited.add(item_id)

    for item_id in dependencies:
        visit(item_id)
    return items, errors


def escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ") or "-"


def link(item: Item, base: str) -> str:
    return f"[{escape(item.value('id'))}]({base}/{item.directory}/README.md)"


def sort_key(item: Item) -> tuple[int, str]:
    return int(item.value("priority")[1:]), item.value("id")


def work_block(items: list[Item]) -> str:
    active = sorted((item for item in items if item.value("status") in ACTIVE), key=sort_key)
    lines = ["| 优先级 | ID | 状态 | Stage | 依赖 | 下一动作 | 入口 |", "|---|---|---|---|---|---|---|"]
    for item in active:
        deps = ", ".join(item.values_list("depends_on")) or "-"
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} |".format(
                escape(item.value("priority")), escape(item.value("id")), escape(item.value("status")),
                escape(item.value("stage")), escape(deps), escape(item.value("next_action")),
                link(item, "work-items/records"),
            )
        )
    if not active:
        lines.extend(["", "当前没有 `ready`、`active`、`blocked` 或 `paused` 工作项。"])
    return "\n".join(lines)


def history_block(items: list[Item]) -> str:
    terminal = sorted((item for item in items if item.value("status") in TERMINAL), key=lambda item: (item.value("closed_at"), item.value("id")), reverse=True)
    lines = ["| 终态日期 | ID | 结果 | 标签 | 入口 |", "|---|---|---|---|---|"]
    for item in terminal:
        labels = ", ".join(item.values_list("labels")) or "-"
        lines.append(f"| {escape(item.value('closed_at'))} | {escape(item.value('id'))} | {escape(item.value('status'))} | {escape(labels)} | {link(item, 'work-items/records')} |")
    if not terminal:
        lines.extend(["", "当前没有终态工作项。"])
    return "\n".join(lines)


def management_block(items: list[Item]) -> str:
    planned = sorted((item for item in items if item.value("status") == "planned"), key=sort_key)
    active = sorted((item for item in items if item.value("status") in ACTIVE), key=sort_key)
    terminal = sorted((item for item in items if item.value("status") in TERMINAL), key=lambda item: (item.value("closed_at"), item.value("id")), reverse=True)
    lines = ["## 规划项", "", "| 优先级 | ID | 下一动作 | 入口 |", "|---|---|---|---|"]
    for item in planned:
        lines.append(f"| {escape(item.value('priority'))} | {escape(item.value('id'))} | {escape(item.value('next_action'))} | {link(item, 'records')} |")
    if not planned:
        lines.extend(["", "当前没有规划工作项。"])
    lines.extend(["", "## 活动项", "", "| 优先级 | ID | 状态 | Stage | 下一动作 | 入口 |", "|---|---|---|---|---|---|"])
    for item in active:
        lines.append(f"| {escape(item.value('priority'))} | {escape(item.value('id'))} | {escape(item.value('status'))} | {escape(item.value('stage'))} | {escape(item.value('next_action'))} | {link(item, 'records')} |")
    if not active:
        lines.extend(["", "当前没有活动工作项。"])
    lines.extend(["", "## 历史项", "", "| 终态日期 | ID | 结果 | 入口 |", "|---|---|---|---|"])
    for item in terminal:
        lines.append(f"| {escape(item.value('closed_at'))} | {escape(item.value('id'))} | {escape(item.value('status'))} | {link(item, 'records')} |")
    if not terminal:
        lines.extend(["", "当前没有终态工作项。"])
    return "\n".join(lines)


def replace_block(path: Path, generated: str, write: bool) -> bool:
    original = path.read_text(encoding="utf-8")
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError(f"{path}: 必须且只能包含一个受控区块")
    before, remainder = original.split(START, 1)
    _, after = remainder.split(END, 1)
    expected = f"{before}{START}\n{generated}\n{END}{after}"
    if expected == original:
        return True
    if write:
        path.write_text(expected, encoding="utf-8")
        return True
    return False


def update_views(root: Path, write: bool = False) -> tuple[list[Item], list[str]]:
    """Validate once and check or refresh the three deterministic view blocks."""
    items, errors = load_items(root)
    if errors:
        return items, errors
    docs = root / "workspace/docs"
    targets = {
        docs / "WORK.md": work_block(items),
        docs / "HISTORY.md": history_block(items),
        docs / "work-items/README.md": management_block(items),
    }
    for path, generated in targets.items():
        label = path.relative_to(root)
        try:
            if not replace_block(path, generated, write):
                errors.append(f"派生视图过期: {label}")
        except (OSError, ValueError) as exc:
            detail = "必须且只能包含一个有序受控区块" if isinstance(exc, ValueError) else "文件缺失或不可读"
            errors.append(f"{label}: {detail}")
    return items, errors


def self_test() -> int:
    sample = Item("v1-01", {"id": "V1-01", "status": "active", "stage": "V1-01A", "priority": "P1", "depends_on": "[]", "next_action": "运行验证", "labels": "['core']", "updated_at": "2026-01-02T03:04+08:00"})
    assert "V1-01A" in work_block([sample])
    assert "当前没有终态工作项" in history_block([sample])
    assert "records/v1-01/README.md" in management_block([sample])
    completed = Item("v1-02", {"id": "V1-02", "status": "completed", "stage": "V1-02A", "priority": "P1", "depends_on": "[]", "next_action": "无", "labels": "['core']", "updated_at": "2026-02-03T04:05+08:00", "closed_at": "2026-01-31"})
    assert "2026-01-31" in history_block([completed])
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "view.md"
        path.write_text(f"人工前言\n{START}\n旧内容\n{END}\n人工尾注\n", encoding="utf-8")
        assert replace_block(path, "新内容", True)
        assert path.read_text(encoding="utf-8") == f"人工前言\n{START}\n新内容\n{END}\n人工尾注\n"
    print("自检通过: 状态渲染和人工区保留。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="更新三个派生视图的受控区块")
    mode.add_argument("--check", action="store_true", help="检查 YAML 和派生视图是否一致")
    mode.add_argument("--self-test", action="store_true", help="运行确定性渲染和人工区保留测试")
    parser.add_argument("--root", type=Path, default=None, help="隔离测试时指定包含 workspace/ 的仓库根目录")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    root = args.root.resolve() if args.root is not None else WORKSPACE.parent
    items, errors = update_views(root, args.write)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    action = "已生成" if args.write else "检查通过"
    print(f"{action}: {len(items)} 个工作项，3 个派生视图。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
