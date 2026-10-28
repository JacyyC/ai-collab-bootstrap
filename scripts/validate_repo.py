#!/usr/bin/env python3
"""Validate the Skill repository without creating a project workspace."""
from __future__ import annotations
import argparse
import ast
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "template-source"
SKILL = ROOT / "skills/ai-collab-bootstrap"
sys.path.insert(0, str(SOURCE / "workspace/scripts"))
from maintain import CheckResult, git_diff_check, run_checks
from markdown_checks import check_links, markdown_files
from workspace_views import frontmatter


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    errors: list[str] = []
    results: list[CheckResult] = []
    required = ["README.md", "AGENTS.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md",
                "scripts/install_skill.py", "scripts/sync_templates.py", "docs/VALIDATION.md",
                "skills/ai-collab-bootstrap/SKILL.md", "skills/ai-collab-bootstrap/LICENSE",
                "skills/ai-collab-bootstrap/classification-rules.md", "skills/ai-collab-bootstrap/consistency-check.md",
                "skills/ai-collab-bootstrap/references/agent-setup.md", "skills/ai-collab-bootstrap/scripts/bootstrap.py",
                "skills/ai-collab-bootstrap/agents/openai.yaml", "skills/ai-collab-bootstrap/templates/.template-manifest.json"]
    structure = [f"缺少发行入口：{name}" for name in required if not (ROOT / name).is_file()]
    if (ROOT / ".trae").exists():
        structure.append("旧编辑器包装 .trae 仍存在")
    if (ROOT / "workspace").exists():
        structure.append("仓库根目录不应包含项目 workspace；工作区仅存在于模板中")
    if (ROOT / "LICENSE").is_file() and (SKILL / "LICENSE").is_file() and (ROOT / "LICENSE").read_bytes() != (SKILL / "LICENSE").read_bytes():
        structure.append("Skill 许可证与仓库许可证不一致")
    for path in ROOT.rglob("*.py"):
        if {".git", "__pycache__", "archive"}.intersection(path.relative_to(ROOT).parts):
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path.relative_to(ROOT)), feature_version=(3, 10))
        except SyntaxError as exc:
            structure.append(f"Python 3.10语法错误：{path.relative_to(ROOT)}:{exc.lineno}")
    if (SKILL / "SKILL.md").is_file():
        metadata = frontmatter(SKILL / "SKILL.md")
        if metadata.get("name") != "ai-collab-bootstrap" or not metadata.get("description"):
            structure.append("Skill name/description 不完整")
    results.append(CheckResult("发行结构与Python语法", "failed" if structure else "passed", f"{len(structure)} 个错误"))
    errors.extend(structure)
    sync = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/sync_templates.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
    results.append(CheckResult("模板单向同步", "passed" if sync.returncode == 0 else "failed", sync.stdout.strip() or "发行核对失败"))
    if sync.returncode:
        errors.append(sync.stderr.strip() or sync.stdout.strip())
    for name, directory in (("模板源", SOURCE), ("独立发行模板", SKILL / "templates")):
        checks, failures = run_checks(directory)
        results.append(CheckResult(name, "failed" if failures else "passed", "；".join(result.summary for result in checks)))
        errors.extend(f"{name}：{failure}" for failure in failures)
    docs = [path for path in markdown_files(ROOT)
            if not path.is_relative_to(SOURCE) and not path.is_relative_to(SKILL / "templates")]
    link_errors: list[str] = []
    _, count = check_links(docs, link_errors, ROOT)
    results.append(CheckResult("仓库与Skill本地链接", "failed" if link_errors else "passed", f"{count} 个链接/锚点，{len(link_errors)} 个错误"))
    errors.extend(link_errors)
    git_result, git_errors = git_diff_check(ROOT)
    results.append(git_result)
    errors.extend(git_errors)
    for result in results:
        print(f"{result.status}: {result.name}；{result.summary}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
