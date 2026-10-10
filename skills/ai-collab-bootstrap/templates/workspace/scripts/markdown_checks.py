#!/usr/bin/env python3
"""Shared local Markdown checks; external repositories keep their own authority."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit


SKIP_PARTS = frozenset({".git", ".trae", ".venv", "node_modules", "dist", "build", ".idea", "__pycache__"})
LINK_RE = re.compile(r"!?\[[^\]]*\]\((<[^>\n]+>|[^)\s]+)(?:\s+[^)]*)?\)")
REFERENCE_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>\n]+>|\S+)", re.MULTILINE)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
ABSOLUTE_LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9])/(?:Users|Volumes|home)/|(?<![A-Za-z0-9])[A-Za-z]:[\\/]")


def markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if path.is_file() and not SKIP_PARTS.intersection(path.relative_to(root).parts))


def without_fences(text: str) -> str:
    lines: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            lines.append("")
        else:
            lines.append(line if fence is None else "")
    return "\n".join(lines)


def slug(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value).strip().lower()
    value = re.sub(r"[^\w\-\u0080-\uffff ]+", "", value)
    return re.sub(r"\s+", "-", value)


def anchors(text: str) -> set[str]:
    text = without_fences(text)
    result = set(re.findall(r"(?:id|name)=['\"]([^'\"]+)['\"]", text))
    counts: Counter[str] = Counter()
    for heading in HEADING_RE.findall(text):
        base = slug(heading)
        number = counts[base]
        result.add(base if not number else f"{base}-{number}")
        counts[base] += 1
    return result


def local_target(source: Path, raw: str) -> tuple[Path | None, str]:
    target = raw.strip().strip("<>")
    if "<" in target or ">" in target:
        return None, ""
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith("//"):
        return None, ""
    path_part = unquote(parsed.path)
    return (source if not path_part else (source.parent / path_part).resolve(), unquote(parsed.fragment))


def absolute_local_link(raw: str) -> bool:
    raw = raw.strip().strip("<>")
    parsed = urlsplit(raw)
    return parsed.scheme.lower() == "file" or bool(re.match(r"^[A-Za-z]:[\\/]", raw)) or (not parsed.scheme and not parsed.netloc and unquote(parsed.path).startswith("/"))


def check_links(paths: list[Path], errors: list[str], root: Path) -> tuple[dict[Path, set[Path]], int]:
    root = root.resolve()
    graph: dict[Path, set[Path]] = {path.resolve(): set() for path in paths}
    cached_anchors: dict[Path, set[str]] = {}
    checked = 0
    for source in paths:
        text = without_fences(source.read_text(encoding="utf-8"))
        targets = [match.group(1) for match in LINK_RE.finditer(text)]
        targets.extend(match.group(1) for match in REFERENCE_RE.finditer(text))
        for raw in targets:
            if absolute_local_link(raw):
                errors.append(f"本机绝对路径链接: {source.relative_to(root)}")
                continue
            target, fragment = local_target(source, raw)
            if target is None:
                continue
            try:
                target.relative_to(root)
            except ValueError:
                # A relative entry into another repository is external navigation.
                # Its availability and anchors belong to that repository.
                continue
            checked += 1
            if not target.exists():
                errors.append(f"坏 Markdown 目标: {source.relative_to(root)} -> {raw}")
                continue
            if target.is_file() and target.suffix.lower() == ".md":
                graph[source.resolve()].add(target.resolve())
                if fragment:
                    if target not in cached_anchors:
                        cached_anchors[target] = anchors(target.read_text(encoding="utf-8"))
                    if fragment not in cached_anchors[target]:
                        errors.append(f"坏 Markdown 锚点: {source.relative_to(root)} -> {raw}")
    return graph, checked
