"""Mechanical record edits and evidence imports; conclusions remain author supplied."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from markdown_checks import SKIP_PARTS, anchors, slug
from workspace_views import (
    END, START, TERMINAL, Item, artifact_entry_targets, frontmatter, history_block, load_items,
    management_block, record_entry_targets, work_block,
)


@dataclass(frozen=True)
class Edit:
    path: Path
    before: bytes | None
    after: bytes


def project_path(root: Path, path: Path) -> Path:
    """Keep writes within the project without following in-project links."""
    path = path if path.is_absolute() else root / path
    if not path.is_relative_to(root) or ".." in path.relative_to(root).parts:
        raise ValueError("目标路径必须位于项目内")
    parts = path.relative_to(root).parts
    if SKIP_PARTS.intersection(parts) or path.name == "开发日志.md":
        raise ValueError("目标属于私有、人工或缓存区域")
    if any(candidate.is_symlink() for candidate in (path, *path.parents) if candidate.is_relative_to(root)):
        raise ValueError("目标路径不能经过符号链接")
    return path


def current_item(root: Path, item_id: str) -> tuple[Path, str]:
    if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+", item_id):
        raise ValueError("工作项 ID 必须使用大写字母、数字和连字符")
    path = project_path(root, Path("workspace/docs/work-items/records") / item_id.lower() / "README.md")
    original = path.read_bytes().decode("utf-8")
    item = Item(path.parent.name, frontmatter(path, original))
    if item.value("id") != item_id or item.value("schema_version") != "4":
        raise ValueError("辅助写入仅用于 ID 相符的 Schema 4 项；旧格式保持原合同")
    if item.value("status") in TERMINAL or item.value("document_status") == "archived":
        raise ValueError("终态或归档项保持冻结；新变化使用新的工作项")
    return path, original


def rewrite_fields(text: str, changes: dict[str, str | list[str] | None]) -> str:
    # Parse before replacing: anchored keys cannot accidentally match
    # document_status when the caller changes status.
    fields = frontmatter(Path("unused"), text)
    lines = text.splitlines(keepends=True)
    end = next(index for index, line in enumerate(lines[1:], 1) if line.rstrip("\r\n") == "---")
    pending = dict(changes)
    header = [lines[0]]
    for line in lines[1:end]:
        key = line.split(":", 1)[0]
        if key not in pending:
            header.append(line)
            continue
        value = pending.pop(key)
        if value is not None:
            header.append(f"{key}: {json.dumps(value, ensure_ascii=False)}\n")
    for key, value in pending.items():
        if value is not None:
            header.append(f"{key}: {json.dumps(value, ensure_ascii=False)}\n")
    if not fields:
        raise ValueError("缺少工作项元数据")
    return "".join(header + lines[end:])


def view_edits(root: Path, items: list[Item]) -> list[Edit]:
    docs = root / "workspace/docs"
    targets = {docs / "WORK.md": work_block(items), docs / "HISTORY.md": history_block(items)}
    legacy = docs / "work-items/README.md"
    if legacy.exists():
        targets[legacy] = management_block(items)
    edits = []
    for candidate, generated in targets.items():
        path = project_path(root, candidate)
        before = path.read_bytes()
        text = before.decode("utf-8")
        if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
            raise ValueError(f"派生视图区块损坏，未写入: {path.relative_to(root)}")
        prefix, remainder = text.split(START, 1)
        _, suffix = remainder.split(END, 1)
        after = (prefix + START + "\n" + generated + "\n" + END + suffix).encode("utf-8")
        if before != after:
            edits.append(Edit(path, before, after))
    return edits


def validated_record_edits(root: Path, path: Path, original: str, updated: str) -> list[Edit]:
    items, errors = load_items(root, overrides={path: updated})
    if errors:
        raise ValueError("未写入；工作项校验失败：" + "；".join(errors))
    edits = [] if original == updated else [Edit(path, original.encode("utf-8"), updated.encode("utf-8"))]
    return edits + view_edits(root, items)


def apply_edits(edits: list[Edit]) -> None:
    """Preflight every file, roll back only bytes written by this operation."""
    for edit in edits:
        actual = edit.path.read_bytes() if edit.path.exists() else None
        if actual != edit.before:
            raise ValueError("文件已被其他操作改变，未写入；请重新读取")
    written: list[Edit] = []
    try:
        for edit in edits:
            edit.path.parent.mkdir(parents=True, exist_ok=True)
            if edit.before is None:
                with edit.path.open("xb") as stream:
                    try:
                        stream.write(edit.after)
                        stream.flush()
                    except OSError:
                        # The exclusively created file belongs to this write;
                        # remove a partial result, not an existing user file.
                        identity = os.fstat(stream.fileno())
                        stream.close()
                        actual = edit.path.stat(follow_symlinks=False)
                        if (identity.st_dev, identity.st_ino) == (actual.st_dev, actual.st_ino):
                            edit.path.unlink()
                        raise
                written.append(edit)
            else:
                if edit.path.read_bytes() != edit.before:
                    raise ValueError("写入前文件已改变，请重新读取")
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile(dir=edit.path.parent, prefix=".record-", delete=False) as stream:
                        temporary = Path(stream.name)
                        stream.write(edit.after)
                    if edit.path.read_bytes() != edit.before:
                        raise ValueError("写入前文件已改变，请重新读取")
                    os.chmod(temporary, edit.path.stat().st_mode & 0o777)
                    os.replace(temporary, edit.path)
                    written.append(edit)
                finally:
                    if temporary is not None:
                        temporary.unlink(missing_ok=True)
    except (OSError, ValueError):
        for edit in reversed(written):
            if edit.path.is_file() and edit.path.read_bytes() == edit.after:
                if edit.before is None:
                    edit.path.unlink()
                else:
                    edit.path.write_bytes(edit.before)
        raise


def update_item(root: Path, item_id: str, changes: dict[str, str | list[str] | None]) -> Path:
    path, original = current_item(root, item_id)
    if not changes:
        raise ValueError("--update 至少需要一个显式字段选项")
    allowed = {"status", "next_action", "stage", "priority", "depends_on", "blocked_by"}
    if set(changes) - allowed:
        raise ValueError("只支持状态、下一步、阶段、优先级和依赖字段")
    for value in changes.values():
        values = value if isinstance(value, list) else [value]
        if any(isinstance(entry, str) and ("\n" in entry or "\r" in entry or not entry.strip()) for entry in values):
            raise ValueError("字段须为非空单行；清空阶段或列表使用对应 clear 选项")
    now = datetime.now().astimezone()
    updates = dict(changes)
    updates.update(last_updated=now.date().isoformat(), updated_at=now.isoformat(timespec="minutes"))
    if changes.get("status") in TERMINAL:
        updates["closed_at"] = now.date().isoformat()
    updated = rewrite_fields(original, updates)
    # Terminal validation still requires declared AC and real evidence rows.
    # The caller explicitly selects status; a green structural check never does.
    apply_edits(validated_record_edits(root, path, original, updated))
    return path


def relative_link(source: Path, target: Path, label: str, fragment: str = "") -> str:
    if not label.strip() or "\n" in label or "\r" in label:
        raise ValueError("链接说明必须为非空单行")
    relative = quote(os.path.relpath(target, source.parent).replace(os.sep, "/"), safe="/-._~")
    safe_label = label.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    return f"[{safe_label}]({relative}{fragment})"


def local_link(root: Path, source: Path, target: Path, label: str, heading: str | None = None) -> str:
    source = project_path(root, source)
    target = project_path(root, target)
    if not source.is_file() or not target.exists():
        raise ValueError("链接来源文件与目标必须实际存在")
    fragment = ""
    if heading is not None:
        if not target.is_file() or target.suffix.lower() != ".md":
            raise ValueError("章节链接目标须为 Markdown 文件")
        available = anchors(target.read_text(encoding="utf-8"))
        candidate = heading if heading in available else slug(heading)
        if candidate not in available:
            raise ValueError("目标章节不存在；已有锚点：" + ", ".join(sorted(available)))
        fragment = "#" + quote(candidate, safe="-_")
    return relative_link(source, target, label, fragment)


def attach_file(root: Path, item_id: str, source: Path, category: str, label: str) -> tuple[Path, str]:
    path, original = current_item(root, item_id)
    relative = Path(category)
    if not relative.parts or relative.is_absolute() or any(name in {"..", "."} for name in relative.parts):
        raise ValueError("--category 须为项目内的类别或批次，如 checks 或 r1/c1")
    source = source.expanduser().absolute()
    if source.is_symlink():
        raise ValueError("原件不能是符号链接")
    source = source.parent.resolve() / source.name
    if not source.is_file() or SKIP_PARTS.intersection(source.parts) or source.name == "开发日志.md" or source.name.startswith(".env") or source.suffix.lower() in {".key", ".pem", ".db", ".sqlite", ".sqlite3"}:
        raise ValueError("请选择已获授权的普通报告或原件，不读取私有、凭据、数据库或人工文件")
    if source.name == "attachment-index.json":
        raise ValueError("attachment-index.json 是本工具的原件索引名；该文件应通过既有入口引用")
    directory = project_path(root, path.parent / "artifacts" / relative)
    target = project_path(root, directory / source.name)
    index = project_path(root, directory / "attachment-index.json")
    content = source.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    previous = target.read_bytes() if target.exists() else None
    if previous is not None and previous != content:
        raise ValueError("同批次已有不同内容的同名原件，未覆盖；请选择新的真实批次")
    old_index = index.read_bytes() if index.exists() else None
    manifest = json.loads(old_index) if old_index is not None else {"version": 1, "files": {}}
    if not isinstance(manifest, dict) or manifest.get("version") != 1 or not isinstance(manifest.get("files"), dict):
        raise ValueError("已有附件索引格式不受支持，未写入")
    entry = {"sha256": digest, "bytes": len(content)}
    recorded = manifest["files"].get(source.name)
    if recorded is not None and (recorded != entry or previous is None):
        raise ValueError("已有原件身份与索引不一致，未更新历史记录")
    manifest["files"][source.name] = entry
    new_index = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    # Generate a batch entrance; avoid one README link per physical output.
    link = relative_link(path, index, label)
    item = Item(path.parent.name, frontmatter(path, original))
    targets = artifact_entry_targets(path, record_entry_targets(path, original, item))
    has_entrance = any(candidate == directory or candidate.is_relative_to(directory) for candidate in targets)
    updated = original if has_entrance else original.rstrip() + "\n\n" + link + "\n"
    if updated != original:
        now = datetime.now().astimezone()
        updated = rewrite_fields(updated, {"last_updated": now.date().isoformat(), "updated_at": now.isoformat(timespec="minutes")})
    edits = validated_record_edits(root, path, original, updated)
    if previous is None:
        edits.insert(0, Edit(target, None, content))
    if old_index != new_index:
        edits.insert(1 if previous is None else 0, Edit(index, old_index, new_index))
    apply_edits(edits)
    return target, link
