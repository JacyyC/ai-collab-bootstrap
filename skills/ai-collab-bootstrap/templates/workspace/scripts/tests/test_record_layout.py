"""Record-file organization through the real maintenance entry point."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.helpers import Fixture, document


class RecordLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()
        self.addCleanup(self.fixture.close)
        self.readme = self.fixture.item("TEST-01")
        self.fixture.refresh()

    def write(self, name: str, content: str = "# 独立专题\n\n保存需要独立阅读的依据。\n") -> Path:
        return self.fixture.write(self.readme.parent.relative_to(self.fixture.root) / name, content)

    def assert_layout_error(self, expected: str) -> None:
        before = self.fixture.snapshot()
        result = self.fixture.script("maintain.py", "--check", expected=None)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(expected, result.stderr)
        self.assertEqual(before, self.fixture.snapshot())

    def test_untracked_summary_is_rejected_and_retained_at_checkpoint(self) -> None:
        extra = self.write("stage-01-summary.md")
        original = extra.read_bytes()
        self.assert_layout_error("非约定记录路径: stage-01-summary.md")
        result = self.fixture.script("maintain.py", "--checkpoint", "TEST-01", expected=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(extra.read_bytes(), original)
        self.assertIn("status: active", self.readme.read_text())
        self.assertIn("failed", self.readme.read_text())
        self.assertFalse((self.readme.parent / "topics").exists())

    def test_canonical_files_require_readme_navigation(self) -> None:
        for name in ("spec.md", "plan.md", "log.md", "evidence.md"):
            with self.subTest(name=name):
                extra = self.write(name)
                self.assert_layout_error(f"缺少 README 入口: {name}")
                extra.unlink()

    def test_structured_record_with_topics_and_raw_artifacts_passes(self) -> None:
        self.readme = self.fixture.item("TEST-01", spec="./spec.md", body_extra=(
            "## 正文入口\n\n"
            "[计划](plan.md)：实施步骤。\n\n[决定](log.md)：重要过程。\n\n"
            "[证据](evidence.md)：验收依据。\n\n"
            "[迁移专题](topics/data-migration.md)：独立迁移边界。\n\n"
            "[协议专题](topics/api-v2/contract.md#范围)：协议细节。\n\n"
            "[原始产物](artifacts/)：实际工具输出。\n"
        ))
        for name in ("spec.md", "plan.md", "log.md", "evidence.md"):
            self.write(name)
        self.write("topics/data-migration.md")
        self.write("topics/api-v2/contract.md", "# 协议\n\n## 范围\n\n迁移协议的独立说明。\n")
        self.write("artifacts/Test Report.MD", "# 工具输出\n\n机器报告保留原名称。\n")
        self.write("artifacts/raw-output.log", "exit=0\n")
        self.fixture.refresh()
        before = self.fixture.snapshot()
        self.fixture.script("maintain.py", "--check")
        self.assertEqual(before, self.fixture.snapshot())

    def test_topics_require_valid_names_even_when_linked(self) -> None:
        for name in ("topics/Review.md", "topics/test_result.md", "topics/测试.md",
                     "topics/review--final.md", "topics/BadDir/report.md", "topics/report.MD"):
            with self.subTest(name=name):
                extra = self.write(name)
                original = self.readme.read_text()
                self.readme.write_text(original + f"\n[专题]({name})：独立用途。\n", encoding="utf-8")
                self.assert_layout_error("专题命名须用小写英文、数字和连字符")
                self.readme.write_text(original, encoding="utf-8")
                extra.unlink()

    def test_nested_markdown_outside_topics_is_rejected(self) -> None:
        self.write("notes/review.md")
        self.assert_layout_error("非约定记录路径: notes/review.md")

    def test_topic_must_have_a_real_direct_readme_entry(self) -> None:
        self.write("topics/data-migration.md")
        self.write("spec.md", "# 范围\n\n[迁移专题](topics/data-migration.md)\n")
        self.readme = self.fixture.item("TEST-01", spec="./spec.md")
        original = self.readme.read_text()
        fake_entries = (
            "",  # An indirect link from spec is insufficient.
            "\n```markdown\n[专题](topics/data-migration.md)\n```\n",
            "\n`[专题](topics/data-migration.md)`\n",
            "\n<!-- [专题](topics/data-migration.md) -->\n",
            "\n[unused]: topics/data-migration.md\n",
            "\n[专题](https://example.invalid/topics/data-migration.md)\n",
            "\n<!-- maintenance-check:start -->\n[专题](topics/data-migration.md)\n<!-- maintenance-check:end -->\n",
        )
        for entry in fake_entries:
            with self.subTest(entry=entry):
                self.readme.write_text(original + entry, encoding="utf-8")
                self.assert_layout_error("缺少 README 入口: topics/data-migration.md")

    def test_reference_links_are_valid_readme_entries(self) -> None:
        self.write("topics/data-migration.md")
        original = self.readme.read_text()
        for entry in (
            "[迁移说明][scope]\n\n[scope]: topics/data-migration.md\n",
            "[Scope][]\n\n[scope]: <topics/data-migration.md>\n",
            "[scope]\n\n[SCOPE]: topics/data-migration.md\n",
        ):
            with self.subTest(entry=entry):
                self.readme.write_text(original + "\n" + entry, encoding="utf-8")
                self.fixture.refresh()
                self.fixture.script("maintain.py", "--check")

    def test_artifacts_need_a_directory_or_key_file_entry(self) -> None:
        self.write("artifacts/Test Run.log", "actual raw output\n")
        self.assert_layout_error("缺少 README 入口: artifacts/")
        original = self.readme.read_text()
        for entry in (
            "[原始日志](artifacts/)：工具输出。",
            "[关键日志](artifacts/Test%20Run.log)：本次执行结果。",
        ):
            with self.subTest(entry=entry):
                self.readme.write_text(original + "\n" + entry + "\n", encoding="utf-8")
                self.fixture.refresh()
                self.fixture.script("maintain.py", "--check")

    def test_archived_subtree_does_not_need_migration(self) -> None:
        self.write("archive/Old Summary.MD")
        self.write("archive/notes/阶段总结.md")
        before = self.fixture.snapshot()
        self.fixture.script("maintain.py", "--check")
        self.assertEqual(before, self.fixture.snapshot())

    def test_old_schemas_and_frozen_records_keep_existing_files(self) -> None:
        old2 = self.fixture.legacy("OLD-02", 2, status="active")
        old3 = self.fixture.legacy("OLD-03", 3, status="planned")
        completed = self.fixture.item("DONE-01", status="completed")
        cancelled = self.fixture.item("STOP-01", status="cancelled")
        archived = self.fixture.item("ARCHIVE-01")
        archived.write_text(archived.read_text().replace("document_status: active", "document_status: archived"), encoding="utf-8")
        for readme in (old2, old3, completed, cancelled, archived):
            (readme.parent / "Old Summary.md").write_text(document("旧记录", "保留原始记录，不为新规则改名。"), encoding="utf-8")
        self.fixture.refresh()
        before = {path: path.read_bytes() for readme in (old2, old3, completed, cancelled, archived)
                  for path in readme.parent.iterdir() if path.is_file()}
        self.fixture.script("maintain.py", "--check")
        self.fixture.script("maintain.py", "--checkpoint", "DONE-01")
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
