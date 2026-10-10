#!/usr/bin/env python3
"""Check portable release structure, references, source checks and syntax offline."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/ai-collab-bootstrap"


def main() -> int:
    errors: list[str] = []
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        errors.append("SKILL.md 缺少 YAML frontmatter")
    else:
        fields = dict(re.findall(r"^([a-z-]+):\s*(.+)$", match.group(1), re.MULTILINE))
        if fields.get("name") != SKILL.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields.get("name", "")):
            errors.append("skill 名称和目录不一致或格式不合法")
        if not fields.get("description") or len(fields.get("description", "")) > 1024:
            errors.append("skill 描述缺失或过长")
    ui = (SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
    if "$ai-collab-bootstrap" not in ui:
        errors.append("UI 默认提示未引用 skill 名称")
    scripts = list(ROOT.rglob("*.py"))
    for path in scripts:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path.relative_to(ROOT)))
        except SyntaxError:
            errors.append(f"Python 语法错误：{path.relative_to(ROOT)}")
    for path in ROOT.rglob("*"):
        if path.is_symlink():
            errors.append(f"发行仓包含符号链接：{path.relative_to(ROOT)}")
        if path.is_file() and path.name in {".env", ".DS_Store"}:
            errors.append(f"发行仓包含本地文件：{path.relative_to(ROOT)}")
    commands = [
        [sys.executable, str(ROOT / "template-source/workspace/scripts/sync_skill_templates.py"), "--check", "--destination", str(SKILL / "templates")],
        [sys.executable, str(ROOT / "template-source/workspace/scripts/maintain.py"), "--check"],
        [sys.executable, str(SKILL / "templates/workspace/scripts/maintain.py"), "--check"],
        [sys.executable, str(ROOT / "template-source/workspace/scripts/check_markdown_links.py"), "--root", str(ROOT)],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        print(result.stdout, end="")
        if result.returncode:
            print(result.stderr, end="", file=sys.stderr)
            errors.append(f"校验命令失败：{Path(command[1]).name}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"仓库检查通过；{len(scripts)} 个 Python 文件语法合法；结构检查不代表模型行为验收。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
