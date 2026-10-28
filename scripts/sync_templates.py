#!/usr/bin/env python3
"""Sync the single canonical template into the installable Skill."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    command = [sys.executable, "-B", str(ROOT / "template-source/workspace/scripts/sync_skill_templates.py"),
               "--root", str(ROOT / "template-source"),
               "--destination", str(ROOT / "skills/ai-collab-bootstrap/templates"), *sys.argv[1:]]
    raise SystemExit(subprocess.run(command, cwd=ROOT).returncode)
