"""Processing helpers."""

from __future__ import annotations

import re
from uuid import uuid4


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def normalize_markdown(text: str) -> str:
    """Strip BOM and normalize newlines; keep code content untouched later."""
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^(`{3,}|~{3,})(\w*)\s*$")
_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.+)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*\|?\s*$")


def is_heading(line: str) -> re.Match[str] | None:
    return _HEADING_RE.match(line)


def is_fence(line: str) -> re.Match[str] | None:
    return _FENCE_RE.match(line)


def is_list_item(line: str) -> re.Match[str] | None:
    return _LIST_RE.match(line)


def is_table_separator(line: str) -> bool:
    if "|" not in line:
        return False
    return bool(_TABLE_SEP_RE.match(line))


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]
