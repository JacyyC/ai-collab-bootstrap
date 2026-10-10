"""Portable release behavior: ownership, drift detection and safe regeneration."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.helpers import Fixture


class TemplateReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()
        self.addCleanup(self.fixture.close)
        (self.fixture.records / ".gitkeep").write_text("", encoding="utf-8")
        self.fixture.refresh()
        self.destination = self.fixture.root / "skills/ai-collab-bootstrap/templates"

    def release(self, mode: str, expected: int | None = 0):
        return self.fixture.script("sync_skill_templates.py", mode, expected=expected)

    def test_release_excludes_real_work_user_documents_and_private_data(self) -> None:
        self.fixture.item("PACK-01")
        self.fixture.refresh()
        self.fixture.write(".trae/documents/user-draft.md", "仅属用户的草稿，不进入发行。\n")
        self.fixture.write(".env", "fixture-only-private-data\n")
        self.fixture.write("workspace/private-runtime.json", "{}\n")
        protected = self.fixture.snapshot()
        self.release("--write")
        self.release("--check")
        manifest = json.loads((self.destination / ".template-manifest.json").read_text())
        self.assertNotIn("开发日志.md", manifest["files"])
        self.assertNotIn(".env", manifest["files"])
        self.assertNotIn("workspace/private-runtime.json", manifest["files"])
        self.assertFalse(any("records/pack-01" in name or "user-draft" in name for name in manifest["files"]))
        for name in ("WORK.md", "HISTORY.md", "work-items/README.md"):
            self.assertNotIn("PACK-01", (self.destination / "workspace/docs" / name).read_text())
        for relative, original in protected.items():
            self.assertEqual((self.fixture.root / relative).read_bytes(), original)

    def test_generation_is_idempotent_and_check_detects_drift_without_writes(self) -> None:
        self.release("--write")
        first = self.fixture.snapshot()
        self.release("--write")
        self.assertEqual(first, self.fixture.snapshot())
        target = self.destination / "AGENTS.md"
        target.write_text(target.read_text() + "\n副本被意外修改。\n", encoding="utf-8")
        altered = self.fixture.snapshot()
        result = self.release("--check", expected=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(altered, self.fixture.snapshot())
        self.release("--write")
        self.assertEqual(first, self.fixture.snapshot())

    def test_generated_bundle_checks_and_creates_a_single_page_without_git(self) -> None:
        self.release("--write")
        command = [sys.executable, str(self.destination / "workspace/scripts/maintain.py")]
        result = subprocess.run(command + ["--check"], cwd=self.destination, text=True,
                                capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("not_run", result.stdout)
        self.assertIn("N/A", result.stdout)
        result = subprocess.run(command + ["--new", "PORTABLE-01", "--title", "独立发行件验证"],
                                cwd=self.destination, text=True, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        files = list((self.destination / "workspace/docs/work-items/records/portable-01").iterdir())
        self.assertEqual([path.name for path in files], ["README.md"])
        self.assertIn("head: none", files[0].read_text())

    def test_user_owned_extra_file_survives_and_instance_cannot_publish(self) -> None:
        self.release("--write")
        extra = self.destination / "user-owned.txt"
        extra.write_text("应保留的额外文件\n", encoding="utf-8")
        self.release("--write")
        self.assertEqual(extra.read_text(), "应保留的额外文件\n")
        root_readme = self.fixture.root / "README.md"
        root_readme.write_text(root_readme.read_text().replace("<PROJECT-NAME>", "已实例化项目"))
        before = self.fixture.snapshot()
        result = self.release("--write", expected=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.fixture.snapshot())


if __name__ == "__main__":
    unittest.main()
