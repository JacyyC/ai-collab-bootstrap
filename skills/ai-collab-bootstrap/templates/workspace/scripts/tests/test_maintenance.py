"""Behavioral maintenance-tool regressions, all run in disposable repositories."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.helpers import DATE, NEXT_ACTION, Fixture, document, verification


START = "<!-- maintenance-check:start -->"
END = "<!-- maintenance-check:end -->"


def without_machine_result(text: str) -> str:
    # Checkpoint timestamps may change mechanically; compare the human body.
    if text.startswith("---\n"):
        text = text.split("---", 2)[2]
    before, marker, after = text.partition(START)
    if not marker:
        return text.strip()
    _, _, tail = after.partition(END)
    return (before + tail).strip()


def field(text: str, name: str) -> str | None:
    header = text.split("---", 2)[1]
    for line in header.splitlines():
        if line.startswith(name + ":"):
            return line.partition(":")[2].strip()
    return None


class MaintenanceBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()
        self.addCleanup(self.fixture.close)
        self.fixture.refresh()

    def check(self, expected: int | None = 0):
        return self.fixture.script("maintain.py", "--check", expected=expected)

    def rejected(self, text: str, item_id: str = "TEST-01") -> None:
        self.fixture.write(f"workspace/docs/work-items/records/{item_id.lower()}/README.md", text)
        # If the bad record is mistakenly accepted, make its views current so a
        # drift error cannot make the negative test pass accidentally.
        self.fixture.script("workspace_views.py", "--write", expected=None)
        result = self.check(expected=None)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_small_task_new_fill_verify_and_complete(self) -> None:
        protected = {name: self.fixture.snapshot()[name] for name in ("开发日志.md", "protected-user.txt")}
        self.fixture.script("maintain.py", "--new", "TEST-01", "--title", "维护入口链接")
        directory = self.fixture.records / "test-01"
        self.assertEqual([path.name for path in directory.iterdir()], ["README.md"])
        self.assertEqual(field((directory / "README.md").read_text(), "status"), "planned")
        self.check()
        self.fixture.run(sys.executable, "-V")
        self.fixture.item("TEST-01", status="active")
        self.fixture.script("maintain.py", "--checkpoint", "TEST-01")
        self.fixture.item("TEST-01", status="completed")
        self.fixture.script("maintain.py", "--checkpoint", "TEST-01")
        self.check()
        history = (self.fixture.root / "workspace/docs/HISTORY.md").read_text()
        self.assertIn("TEST-01", history)
        self.assertIn("completed", history)
        self.assertEqual(len(list(directory.iterdir())), 1)
        for name, content in protected.items():
            self.assertEqual(self.fixture.snapshot()[name], content)

    def test_long_task_stage_and_shared_spec(self) -> None:
        first = self.fixture.item("LONG-01", status="planned")
        (first.parent / "spec.md").write_text(document("共享范围", "## 范围\n\n两个维护入口共同使用相同验收边界。\n\nAC-01：入口可访问。", work_item="LONG-01"), encoding="utf-8")
        self.fixture.item("LONG-02", stage="LONG-02A", spec="../long-01/spec.md")
        self.fixture.write("workspace/docs/work-items/records/long-02/plan.md", document("分阶段实施", "## Stage\n\n| ID | 目标 |\n|---|---|\n| LONG-02A | 更新入口并验证 |", work_item="LONG-02"))
        self.fixture.refresh()
        self.check()
        self.assertEqual(len(list(self.fixture.records.rglob("spec.md"))), 1)
        self.assertIn("LONG-02A", (self.fixture.root / "workspace/docs/WORK.md").read_text())

    def test_new_does_not_overwrite_existing_work_record(self) -> None:
        self.fixture.item("TEST-01", body_extra="用户已有的工作备注。\n")
        self.fixture.refresh()
        before = self.fixture.snapshot()
        result = self.fixture.script("maintain.py", "--new", "TEST-01", "--title", "覆盖尝试", expected=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.fixture.snapshot())

    def test_stage_can_be_inline_without_plan_file(self) -> None:
        readme = self.fixture.item("TEST-01", stage="TEST-01A")
        readme.write_text(readme.read_text().replace("读取链接目标、修复入口并验证", "- TEST-01A：读取链接目标、修复入口并验证"), encoding="utf-8")
        self.fixture.refresh()
        self.check()
        self.assertFalse((readme.parent / "plan.md").exists())

    def test_stage_can_be_inline_when_an_optional_plan_defines_other_stages(self) -> None:
        readme = self.fixture.item("TEST-01", stage="TEST-01B")
        readme.write_text(readme.read_text().replace("读取链接目标、修复入口并验证", "- TEST-01B：核对第二阶段成果"), encoding="utf-8")
        (readme.parent / "plan.md").write_text(document("第一阶段计划", "## Stage\n\n| ID | 目标 |\n|---|---|\n| TEST-01A | 核对第一阶段成果 |", work_item="TEST-01"), encoding="utf-8")
        self.fixture.refresh()
        self.check()

    def test_schema2_and_schema3_history_remain_readable_and_frozen(self) -> None:
        first = self.fixture.legacy("OLD-02", 2)
        second = self.fixture.legacy("OLD-03", 3)
        self.fixture.refresh()
        old_content = {path.relative_to(self.fixture.root).as_posix(): path.read_bytes()
                       for directory in (first.parent, second.parent) for path in directory.iterdir()}
        self.check()
        self.fixture.item("TEST-01")
        self.fixture.script("maintain.py", "--checkpoint", "TEST-01")
        for relative, content in old_content.items():
            self.assertEqual((self.fixture.root / relative).read_bytes(), content)
        history = (self.fixture.root / "workspace/docs/HISTORY.md").read_text()
        self.assertIn("OLD-02", history)
        self.assertIn("OLD-03", history)

    def test_schema2_and_schema3_can_share_registered_spec_without_migration(self) -> None:
        for schema in (2, 3):
            with self.subTest(schema=schema):
                owner = self.fixture.legacy(f"OWNER-0{schema}", schema, status="planned")
                readme = self.fixture.legacy(f"OLD-0{schema}", schema)
                shared = f"../owner-0{schema}/spec.md"
                text = readme.read_text().replace("spec: ./spec.md", f"spec: {shared}")
                text = text.replace("[Spec](spec.md)", f"[Spec]({shared})")
                readme.write_text(text, encoding="utf-8")
                (readme.parent / "spec.md").unlink()
                self.fixture.refresh()
                self.check()
                self.assertTrue((owner.parent / "spec.md").exists())
                self.assertEqual(field(readme.read_text(), "schema_version"), str(schema))

    def test_single_page_pause_resume_preserves_work_baseline(self) -> None:
        self.fixture.item("TEST-01", status="paused", head=self.fixture.head)
        self.fixture.script("maintain.py", "--checkpoint", "TEST-01")
        readme = self.fixture.item("TEST-01", status="active", head=self.fixture.head)
        self.fixture.script("maintain.py", "--checkpoint", "TEST-01")
        text = readme.read_text()
        self.assertEqual(field(text, "status"), "active")
        self.assertEqual(field(text, "head"), self.fixture.head)
        self.assertEqual(field(text, "next_action"), NEXT_ACTION)
        self.assertEqual(self.fixture.run("git", "rev-parse", "HEAD").stdout.strip(), self.fixture.head)

    def test_check_is_read_only_and_default_mode_is_check(self) -> None:
        self.fixture.item("TEST-01")
        self.fixture.refresh()
        before = self.fixture.snapshot()
        self.check()
        self.fixture.script("maintain.py")
        self.assertEqual(before, self.fixture.snapshot())

    def test_check_reports_view_drift_without_repairing_it(self) -> None:
        self.fixture.item("TEST-01")
        before = self.fixture.snapshot()
        result = self.check(expected=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.fixture.snapshot())

    def test_checkpoint_preserves_human_content_and_does_not_accumulate_blocks(self) -> None:
        readme = self.fixture.item("TEST-01", head=self.fixture.head, body_extra="## 接手说明\n\n保留现有备注，不改业务范围。\n")
        original = readme.read_text()
        protected = {name: self.fixture.snapshot()[name] for name in ("开发日志.md", "protected-user.txt")}
        self.fixture.script("maintain.py", "--checkpoint", "TEST-01")
        first = readme.read_text()
        self.fixture.script("maintain.py", "--checkpoint", "TEST-01")
        second = readme.read_text()
        self.assertEqual(without_machine_result(original), without_machine_result(second))
        self.assertEqual(second.count(START), 1)
        self.assertEqual(second.count(END), 1)
        self.assertEqual(len(first), len(second))
        for name in ("status", "head", "next_action"):
            self.assertEqual(field(original, name), field(second, name))
        for name, content in protected.items():
            self.assertEqual(self.fixture.snapshot()[name], content)

    def test_failed_checkpoint_records_failure_without_rewriting_business_evidence(self) -> None:
        readme = self.fixture.item("TEST-01", head=self.fixture.head,
                                  body_extra="## 附加入口\n\n[失效入口](missing-target.md)\n")
        original = readme.read_text()
        result = self.fixture.script("maintain.py", "--checkpoint", "TEST-01", expected=None)
        self.assertNotEqual(result.returncode, 0)
        updated = readme.read_text()
        self.assertEqual(without_machine_result(original), without_machine_result(updated))
        block = updated.partition(START)[2].partition(END)[0]
        self.assertIn("failed", block)
        self.assertEqual(field(updated, "status"), "active")
        self.assertEqual(field(updated, "head"), self.fixture.head)

    def test_bad_target_and_bad_anchor_are_rejected(self) -> None:
        readme = self.fixture.item("TEST-01")
        self.fixture.refresh()
        good = readme.read_text()
        for link in ("[缺失](absent.md)", "[坏锚点](README.md#absent-anchor)"):
            with self.subTest(link=link):
                self.rejected(good + "\n" + link + "\n")

    def test_circular_dependencies_are_rejected(self) -> None:
        self.fixture.item("TEST-01", depends_on=("TEST-02",))
        self.fixture.item("TEST-02", depends_on=("TEST-01",))
        self.fixture.script("workspace_views.py", "--write", expected=None)
        result = self.check(expected=None)
        self.assertNotEqual(result.returncode, 0)

    def test_missing_exact_stage_is_rejected(self) -> None:
        readme = self.fixture.item("TEST-01", stage="TEST-01A")
        readme.write_text(readme.read_text().replace("读取链接目标、修复入口并验证", "- TEST-01AA：另一个阶段，不能冒充 A 阶段"), encoding="utf-8")
        self.rejected(readme.read_text())

    def test_stage_reference_in_prose_is_not_a_stage_definition(self) -> None:
        readme = self.fixture.item("TEST-01", stage="TEST-01A")
        text = readme.read_text().replace("读取链接目标、修复入口并验证", "参考记录中提到 TEST-01A；此处尚未定义实施阶段")
        self.rejected(text)

    def test_completed_cannot_have_empty_or_all_pending_evidence(self) -> None:
        readme = self.fixture.item("TEST-01", status="completed", evidence="pending")
        pending = readme.read_text()
        self.rejected(pending)
        self.rejected(pending.replace(verification("pending"), "## 验证\n\n尚无实际验证。\n"))

    def test_completed_needs_actual_method_and_result_for_passed_row(self) -> None:
        readme = self.fixture.item("TEST-01", status="completed")
        text = readme.read_text()
        for invalid in (
            text.replace("python3 -V", ""),
            text.replace("退出码 0；隔离环境实际运行 Python 版本查询", ""),
            text.replace("| AC-01 | passed |", "| AC-01 | failed |"),
        ):
            with self.subTest(evidence=invalid):
                self.rejected(invalid)

    def test_completed_requires_all_acceptance_conditions_to_pass(self) -> None:
        readme = self.fixture.item("TEST-01", status="completed")
        text = readme.read_text().replace("- AC-01：入口可访问，用户文件内容保持原样。", "- AC-01：入口可访问，用户文件内容保持原样。\n- AC-02：另一入口也必须通过核对。")
        for status in ("pending", "failed", "not_run"):
            with self.subTest(status=status):
                self.rejected(text + f"| AC-02 | {status} | 检查另一入口 | 尚未获得通过结果 | 该入口未通过验收 |\n")

    def test_failed_acceptance_can_be_retried_without_erasing_history(self) -> None:
        self.fixture.run(sys.executable, "-c", "raise SystemExit(1)", expected=1)
        readme = self.fixture.item("TEST-01", status="completed")
        failed = "| AC-01 | failed | python3 -c 'raise SystemExit(1)' | 退出码 1；第一次检查失败 | 后续需要重试 |"
        text = readme.read_text().replace("| AC-01 | passed |", failed + "\n| AC-01 | passed |")
        readme.write_text(text, encoding="utf-8")
        self.fixture.refresh()
        self.check()
        self.assertIn(failed, readme.read_text())
        # A subsequent failing result must supersede the earlier success too.
        self.rejected(text.rstrip() + "\n" + failed + "\n")

    def test_completed_cannot_omit_declared_readme_or_shared_spec_acceptance(self) -> None:
        readme = self.fixture.item("TEST-01", status="completed")
        text = readme.read_text().replace("- AC-01：入口可访问，用户文件内容保持原样。", "- AC-01：入口可访问，用户文件内容保持原样。\n- AC-02：另一入口也必须通过核对。")
        self.rejected(text)
        owner = self.fixture.item("SCOPE-01", status="planned")
        (owner.parent / "spec.md").write_text(document("共享合同", "## 验收\n\n- AC-01：入口存在。\n- AC-02：用户内容未改变。", work_item="SCOPE-01"), encoding="utf-8")
        readme = self.fixture.item("TEST-01", status="completed", spec="../scope-01/spec.md")
        self.rejected(readme.read_text())

    def test_checkpoint_on_completed_item_does_not_modify_frozen_record(self) -> None:
        readme = self.fixture.item("TEST-01", status="completed", head=self.fixture.head,
                                  body_extra="## 结束说明\n\n已有验收事实应保持冻结。\n")
        original = readme.read_bytes()
        self.fixture.script("maintain.py", "--checkpoint", "TEST-01")
        self.assertEqual(readme.read_bytes(), original)
        self.assertEqual(self.fixture.run("git", "rev-parse", "HEAD").stdout.strip(), self.fixture.head)

    def test_machine_passed_result_is_not_business_acceptance(self) -> None:
        readme = self.fixture.item("TEST-01", status="completed", evidence="pending")
        text = readme.read_text() + f"\n{START}\n| AC-01 | passed | python3 -V | 退出码 0 | 无 |\n{END}\n"
        self.rejected(text)

    def test_spec_cannot_escape_work_records(self) -> None:
        self.fixture.write("project/docs/spec.md", document("项目正文", "AC-01：业务说明，不能冒充工作范围合同。"))
        readme = self.fixture.item("TEST-01", spec="../../../../../project/docs/spec.md")
        result = self.fixture.script("workspace_views.py", "--write", expected=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(field(readme.read_text(), "spec"), "../../../../../project/docs/spec.md")

    def test_real_record_placeholders_rejected_template_placeholders_allowed(self) -> None:
        self.check()  # The unchanged, not-yet-instantiated template is legitimate.
        readme = self.fixture.item("TEST-01")
        self.fixture.refresh()
        self.rejected(readme.read_text().replace("修复文档入口，保留用户文件，不改业务范围。", "<待填写范围>"))

    def test_cancelled_task_keeps_reason_and_unverified_scope(self) -> None:
        readme = self.fixture.item("TEST-01", status="cancelled", evidence="not_run",
                                  body_extra="## 取消说明\n\n取消原因：用户撤回入口调整；未执行链接变更，未验证生产环境。\n")
        text = readme.read_text().replace("退出码 0；隔离环境实际运行 Python 版本查询", "未执行：用户撤回本次变更")
        readme.write_text(text, encoding="utf-8")
        self.fixture.refresh()
        self.check()
        self.assertIn("cancelled", (self.fixture.root / "workspace/docs/HISTORY.md").read_text())


    def test_client_protocol_entry_is_allowed_and_its_links_are_still_checked(self) -> None:
        self.fixture.write("CLAUDE.md", "# Project instructions\n\n@AGENTS.md\n\n[协议](AGENTS.md)\n")
        self.fixture.write("GEMINI.md", "# Project instructions\n\nRead AGENTS.md before changing this project.\n")
        self.check()
        self.fixture.write("CLAUDE.md", "# Project instructions\n\n[协议](missing-agents.md)\n")
        result = self.fixture.script("maintain.py", "--check", expected=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CLAUDE.md", result.stdout + result.stderr)
        self.assertIn("missing-agents.md", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
