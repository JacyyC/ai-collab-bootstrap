"""Validate the standalone repository without mutating its authored files."""
from __future__ import annotations
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def snapshot(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


class RepositoryValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="standalone-repository-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve() / "repository"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".DS_Store"))

    def check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-B", str(self.root / "scripts/validate_repo.py")],
                              cwd=self.root, text=True, capture_output=True, timeout=60)

    def test_read_only_repository_validation_leaves_snapshot_unchanged(self) -> None:
        self.assertFalse((self.root / "workspace").exists())
        before = snapshot(self.root)
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, snapshot(self.root))
        self.assertFalse((self.root / "workspace").exists())

    def test_unexpected_root_workspace_is_reported_without_modifying_it(self) -> None:
        workspace = self.root / "workspace"
        workspace.mkdir()
        (workspace / "notes.txt").write_text("用户的内容，校验器不得删除。\n", encoding="utf-8")
        before = snapshot(self.root)
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("workspace", result.stdout + result.stderr)
        self.assertEqual(before, snapshot(self.root))

    def test_missing_portable_setup_is_rejected_without_repairing_files(self) -> None:
        (self.root / "skills/ai-collab-bootstrap/references/agent-setup.md").unlink()
        before = snapshot(self.root)
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("agent-setup.md", result.stdout + result.stderr)
        self.assertEqual(before, snapshot(self.root))


if __name__ == "__main__":
    unittest.main()
