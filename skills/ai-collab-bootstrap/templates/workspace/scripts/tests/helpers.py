"""Disposable repositories and realistic work records used by tool regressions."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
DATE = "2026-10-10"
UPDATED = f"{DATE}T12:00+08:00"
NEXT_ACTION = "运行维护验证并记录结果"
IMPACT_IDS = (
    "DOC-ROOT", "DOC-HUMAN", "DOC-CURRENT", "DOC-TARGET", "DOC-GOVERNANCE",
    "DOC-TOOLS", "DOC-WORK-ITEM", "DOC-VIEWS", "DOC-HISTORY", "DOC-CROSS-REPO",
)


def document(title: str, body: str, **metadata: str) -> str:
    fields = {"document_status": "active", "last_updated": DATE, **metadata}
    return "---\n" + "".join(f"{key}: {value}\n" for key, value in fields.items()) + f"---\n\n# {title}\n\n{body.rstrip()}\n"


def verification(status: str = "passed") -> str:
    return (
        "## 验证\n\n"
        "| 验收 | 状态 | 方法或命令 | 结果或证据 | 限制 |\n"
        "|---|---|---|---|---|\n"
        f"| AC-01 | {status} | python3 -V | 退出码 0；隔离环境实际运行 Python 版本查询 | 未覆盖生产环境 |\n"
    )


def single_record(item_id: str, *, status: str = "active", stage: str | None = None,
                  spec: str | None = None, evidence: str = "passed", head: str | None = None,
                  depends_on: tuple[str, ...] = (), body_extra: str = "") -> str:
    fields = {
        "schema_version": "4", "document_status": "active", "last_updated": DATE,
        "id": item_id, "title": "维护入口链接", "status": status,
        "updated_at": UPDATED, "next_action": NEXT_ACTION,
    }
    if stage is not None:
        fields["stage"] = stage
    if spec is not None:
        fields["spec"] = spec
    if head is not None:
        fields["head"] = head
    if depends_on:
        fields["depends_on"] = repr(list(depends_on))
    if status in {"completed", "cancelled"}:
        fields["closed_at"] = DATE
    header = "---\n" + "".join(f"{key}: {value}\n" for key, value in fields.items()) + "---\n"
    return header + (
        f"\n# {item_id} 维护入口链接\n\n"
        "## 目标与范围\n\n修复文档入口，保留用户文件，不改业务范围。\n\n"
        "## 验收\n\n- AC-01：入口可访问，用户文件内容保持原样。\n\n"
        "## 计划\n\n读取链接目标、修复入口并验证；文档影响：仅本工作项。\n\n"
        + verification(evidence) + "\n" + body_extra
    )


class Fixture:
    """Clone only template-owned files into an independent temporary Git root."""

    def __init__(self, source: Path = REPOSITORY):
        self.temporary = tempfile.TemporaryDirectory(prefix="maintenance-regression-")
        self.root = Path(self.temporary.name)
        for name in ("README.md", "AGENTS.md", ".gitignore", "project", "workspace"):
            origin = source / name
            if origin.is_dir():
                shutil.copytree(origin, self.root / name,
                                ignore=shutil.ignore_patterns("records", "__pycache__", ".DS_Store"))
            elif origin.is_file():
                shutil.copy2(origin, self.root / name)
        self.records.mkdir(parents=True, exist_ok=True)
        self.write("开发日志.md", "# 人工日志\n\n只供测试使用，工具不得改写。\n")
        self.write("protected-user.txt", "用户原有内容\n")
        self.run("git", "init", "-q")
        self.run("git", "add", ".")
        self.run("git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-qm", "fixture baseline")
        self.head = self.run("git", "rev-parse", "HEAD").stdout.strip()
        self.run(sys.executable, "-V")

    @property
    def records(self) -> Path:
        return self.root / "workspace/docs/work-items/records"

    def close(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str | Path, content: str) -> Path:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def item(self, item_id: str, **kwargs: object) -> Path:
        relative = Path("workspace/docs/work-items/records") / item_id.lower() / "README.md"
        return self.write(relative, single_record(item_id, **kwargs))

    def legacy(self, item_id: str, schema: int, *, status: str = "completed") -> Path:
        directory = self.records / item_id.lower()
        directory.mkdir(parents=True, exist_ok=True)
        fields = {
            "schema_version": str(schema), "document_status": "active", "last_updated": DATE,
            "id": item_id, "title": "维护入口链接", "status": status,
            "stage": item_id + "A", "priority": "P2", "branch": "main",
            ("base_head" if schema == 2 else "head"): self.head,
            "created_at": DATE, "updated_at": UPDATED, "updated_by": "维护者",
            "depends_on": "[]", "blocked_by": "[]", "next_action": NEXT_ACTION,
            "labels": "[]", "spec": "./spec.md", "plan": "./plan.md", "framework_scope": "[]",
        }
        if status in {"completed", "cancelled"}:
            fields["closed_at"] = DATE
        header = "---\n" + "".join(f"{key}: {value}\n" for key, value in fields.items()) + "---\n"
        readme = directory / "README.md"
        readme.write_text(header + f"\n# {item_id} 工作台\n\n## 用户成果与工作目标\n\n修复维护入口。\n\n"
                          f"## 当前快照\n\n- 下一步：{NEXT_ACTION}。\n\n"
                          f"## 交接\n\n| 字段 | 值 |\n|---|---|\n| 第一个下一动作 | {NEXT_ACTION} |\n\n"
                          "## 文档与证据导航\n\n[Spec](spec.md) · [Plan](plan.md) · [Log](log.md) · [Evidence](evidence.md)\n",
                          encoding="utf-8")
        (directory / "spec.md").write_text(document(item_id + " Spec", "## 范围\n\n修复维护入口。\n\n## 验收\n\nAC-01：链接检查通过。", work_item=item_id), encoding="utf-8")
        impact = "\n".join(f"| {category} | 不更新 | 本项只调整入口；以 AC-01 为事实入口 |" for category in IMPACT_IDS)
        plan = f"## Stage\n\n| ID | 目标 | AC | 验证 |\n|---|---|---|---|\n| {item_id}A | 修复入口 | AC-01 | 链接检查 |\n\n## 文档影响\n\n| ID | 处置 | 原因与事实入口 |\n|---|---|---|\n{impact}\n"
        (directory / "plan.md").write_text(document(item_id + " Plan", plan, work_item=item_id, impact_schema="1"), encoding="utf-8")
        (directory / "log.md").write_text(document(item_id + " Log", "## 检查点\n\n完成入口核对，尚未覆盖生产环境。", work_item=item_id), encoding="utf-8")
        (directory / "evidence.md").write_text(document(item_id + " Evidence", verification(), work_item=item_id), encoding="utf-8")
        return readme

    def run(self, *command: str, expected: int | None = 0) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(command, cwd=self.root, env=environment, text=True,
                                capture_output=True, timeout=60)
        if expected is not None and result.returncode != expected:
            raise AssertionError(f"{command!r} returned {result.returncode}, expected {expected}\n{result.stdout}\n{result.stderr}")
        return result

    def script(self, name: str, *args: str, expected: int | None = 0,
               root_argument: bool = True) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(self.root / "workspace/scripts" / name), *args]
        if root_argument:
            command += ["--root", str(self.root)]
        return self.run(*command, expected=expected)

    def refresh(self) -> None:
        self.script("workspace_views.py", "--write")

    def snapshot(self) -> dict[str, bytes]:
        return {path.relative_to(self.root).as_posix(): path.read_bytes()
                for path in self.root.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(self.root).parts
                and "__pycache__" not in path.parts}
