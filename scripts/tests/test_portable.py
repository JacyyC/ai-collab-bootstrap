"""Exercise installer and scaffold behavior against disposable user projects."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALL = ROOT / "scripts/install_skill.py"
BOOTSTRAP = ROOT / "skills/ai-collab-bootstrap/scripts/bootstrap.py"


def snapshot(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file() and not path.is_symlink()}


class PortableBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="skill-portable-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.target = self.directory / "project"

    def run_script(self, script: Path, *arguments: str, expected: int = 0) -> str:
        result = subprocess.run([sys.executable, str(script), *arguments],
                                cwd=self.directory, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def test_install_preview_writes_nothing_and_existing_install_is_preserved(self) -> None:
        destination = self.directory / "skills"
        self.run_script(INSTALL, "--destination", str(destination))
        self.assertFalse(destination.exists())
        self.run_script(INSTALL, "--destination", str(destination), "--write")
        installed = destination / "ai-collab-bootstrap"
        before = snapshot(installed)
        self.run_script(INSTALL, "--destination", str(destination), "--write", expected=1)
        self.assertEqual(before, snapshot(installed))

    def test_scaffold_preview_writes_nothing(self) -> None:
        self.run_script(BOOTSTRAP, "--target", str(self.target))
        self.assertFalse(self.target.exists())

    def test_conflict_stops_before_any_write(self) -> None:
        self.target.mkdir()
        (self.target / "README.md").write_text("已有项目说明，不可覆盖\n")
        (self.target / "src").mkdir()
        (self.target / "src/main.py").write_text("print('existing code')\n")
        before = snapshot(self.target)
        self.run_script(BOOTSTRAP, "--target", str(self.target), "--write", expected=1)
        self.assertEqual(before, snapshot(self.target))
        self.assertFalse((self.target / "workspace").exists())

    def test_scaffold_preserves_existing_code(self) -> None:
        (self.target / "src").mkdir(parents=True)
        code = self.target / "src/main.py"
        code.write_text("print('existing code')\n")
        self.run_script(BOOTSTRAP, "--target", str(self.target), "--write")
        self.assertEqual(code.read_text(), "print('existing code')\n")
        self.assertTrue((self.target / "workspace/scripts/maintain.py").is_file())

    def test_template_drift_and_traversal_are_rejected_before_write(self) -> None:
        source = self.directory / "templates"
        shutil.copytree(ROOT / "skills/ai-collab-bootstrap/templates", source)
        (source / "AGENTS.md").write_text("unexpected drift\n")
        self.run_script(BOOTSTRAP, "--template-dir", str(source), "--target", str(self.target), "--write", expected=1)
        self.assertFalse(self.target.exists())
        manifest = {"version": 1, "files": {"../outside.txt": "invalid"}}
        (source / ".template-manifest.json").write_text(json.dumps(manifest))
        self.run_script(BOOTSTRAP, "--template-dir", str(source), "--target", str(self.target), "--write", expected=1)
        self.assertFalse(self.target.exists())

    def test_symlinked_target_is_rejected(self) -> None:
        actual = self.directory / "actual"
        actual.mkdir()
        self.target.symlink_to(actual, target_is_directory=True)
        self.run_script(BOOTSTRAP, "--target", str(self.target), "--write", expected=1)
        self.assertEqual(snapshot(actual), {})

    def test_installed_skill_bootstraps_checks_and_records_a_checkpoint(self) -> None:
        destination = self.directory / "skills"
        self.run_script(INSTALL, "--destination", str(destination), "--write")
        installed = destination / "ai-collab-bootstrap"
        self.run_script(installed / "scripts/bootstrap.py", "--target", str(self.target), "--write")
        maintain = self.target / "workspace/scripts/maintain.py"
        before = snapshot(self.target)
        output = self.run_script(maintain, "--root", str(self.target), "--check")
        self.assertIn("not_run", output)
        self.assertEqual(before, snapshot(self.target))
        self.run_script(maintain, "--root", str(self.target), "--new", "DEMO-01", "--title", "验证协作入口")
        record = self.target / "workspace/docs/work-items/records/demo-01/README.md"
        self.assertEqual([path.name for path in record.parent.iterdir()], ["README.md"])
        self.assertIn("head: none", record.read_text())
        self.run_script(maintain, "--root", str(self.target), "--checkpoint", "DEMO-01")
        self.assertIn("## 工具检查", record.read_text())
        self.assertIn("status: planned", record.read_text())
        self.run_script(maintain, "--root", str(self.target), "--check")


if __name__ == "__main__":
    unittest.main()
