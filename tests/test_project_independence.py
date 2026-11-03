"""Observe native layouts, state projections and independent local operation."""
from __future__ import annotations
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "template-source/workspace/scripts"))
from tests.helpers import Fixture


class ProjectIndependenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture()
        self.addCleanup(self.fixture.close)
        self.fixture.refresh()

    def test_native_layout_and_plain_readme_remain_usable(self):
        shutil.rmtree(self.fixture.root / "project")
        self.fixture.write("README.md", "# Native project\n\n[使用](docs/use.md)\n")
        self.fixture.write("docs/use.md", "# 使用\n\n已有格式无需治理 YAML。\n\n# 其他入口\n")
        self.fixture.run("git", "add", "-A")
        self.fixture.script("maintain.py", "--check")
        self.assertFalse((self.fixture.root / "workspace/docs/framework").exists())

    def test_optional_legacy_management_page_preserves_human_regions(self):
        legacy = self.fixture.root / "workspace/docs/work-items/README.md"
        legacy.write_text("人类前言\n" + legacy.read_text() + "\n人类尾注\n")
        self.fixture.item("NEXT-01", status="planned")
        self.fixture.refresh()
        self.assertTrue(legacy.read_text().startswith("人类前言\n"))
        self.assertTrue(legacy.read_text().endswith("\n人类尾注\n"))
        legacy.unlink()
        self.fixture.run("git", "add", "-A")
        self.fixture.script("maintain.py", "--new", "NEXT-02", "--title", "无需第三管理页")
        self.fixture.script("maintain.py", "--check")

    def test_work_discovers_planned_title_and_blocker_without_history_growth(self):
        self.fixture.item("PLAN-01", status="planned")
        active = self.fixture.item("LIVE-01")
        active.write_text(active.read_text().replace("next_action:", "blocked_by: ['G-CONTRACT']\nnext_action:"))
        self.fixture.refresh()
        work = self.fixture.root / "workspace/docs/WORK.md"
        before = work.read_text()
        self.assertIn("PLAN-01", before)
        self.assertIn("维护入口链接", before)
        self.assertIn("G-CONTRACT", before)
        self.fixture.item("DONE-01", status="completed")
        self.fixture.refresh()
        self.assertEqual(before, work.read_text())
        self.assertIn("DONE-01", (self.fixture.root / "workspace/docs/HISTORY.md").read_text())

    def test_staged_whitespace_is_detected_and_index_preserved(self):
        self.fixture.write("staged.txt", "bad trailing space  \n")
        self.fixture.run("git", "add", "staged.txt")
        index = self.fixture.run("git", "diff", "--cached").stdout
        result = self.fixture.script("maintain.py", "--check", expected=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("暂存区", result.stdout)
        self.assertEqual(index, self.fixture.run("git", "diff", "--cached").stdout)

    def test_active_without_acceptance_is_rejected_without_inventing_it(self):
        path = self.fixture.item("EMPTY-01")
        header = path.read_text().split("---", 2)[1]
        path.write_text("---" + header + "---\n\n# 未具备实施合同\n")
        original = path.read_bytes()
        result = self.fixture.script("maintain.py", "--check", expected=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("声明至少一项 AC", result.stderr)
        self.assertEqual(original, path.read_bytes())

    def test_private_personal_and_external_symlink_markdown_are_not_read(self):
        # Invalid UTF-8 makes accidental reads observable without using secrets.
        for relative in (".local/private.md", "开发日志.md"):
            path = self.fixture.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\xff[bad](missing.md)")
        target = self.fixture.root.parent / (self.fixture.root.name + "-external.md")
        target.write_bytes(b"\xff")
        self.addCleanup(target.unlink)
        (self.fixture.root / "external.md").symlink_to(target)
        self.fixture.script("maintain.py", "--check")

    def test_declared_architecture_roles_use_actual_paths(self):
        self.fixture.write("docs/current.md", "---\nframework_role: current\ntarget: goal.md\n---\n\n# 事实\n")
        self.fixture.write("docs/goal.md", "---\nframework_role: target\nbased_on: current.md\n---\n\n# 目标\n")
        self.fixture.script("maintain.py", "--check")
        (self.fixture.root / "docs/goal.md").unlink()
        result = self.fixture.script("maintain.py", "--check", expected=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("架构引用目标不存在", result.stderr)


if __name__ == "__main__":
    unittest.main()
