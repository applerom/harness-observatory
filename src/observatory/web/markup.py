"""Shared inline-markup rendering helpers for web templates."""

from __future__ import annotations

import html
import re


_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_CODE_RE = re.compile(r"`([^`]+)`")
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")
_BULLET_RE = re.compile(r"^\s*-\s+(.*)$")


def render_inline_markup(value: str | None) -> str | None:
    """Render a small safe Markdown-like subset as HTML.

    The renderer escapes user input first, then supports:
    - inline bold: **bold**
    - inline code: `code`
    - headings: #, ##, ###
    - bullet lists: - item
    - plain paragraphs and line breaks
    """
    if not value:
        return None

    escaped = html.escape(value)
    escaped = _BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = _CODE_RE.sub(r"<code>\1</code>", escaped)
    return _render_blocks(escaped)


def _render_blocks(value: str) -> str:
    lines = value.splitlines()
    out: list[str] = []
    list_buffer: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            out.append(f"<p>{'<br>'.join(paragraph)}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if list_buffer:
            items = "".join(f"<li>{item}</li>" for item in list_buffer)
            out.append(f"<ul>{items}</ul>")
            list_buffer.clear()

    for line in lines:
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush_paragraph()
            flush_list()
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            out.append(f"<h{level}>{text}</h{level}>")
            continue

        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            flush_paragraph()
            list_buffer.append(bullet_match.group(1).strip())
            continue

        if line.strip() == "":
            flush_paragraph()
            flush_list()
            continue

        paragraph.append(line.strip())

    flush_paragraph()
    flush_list()

    return "".join(out) if out else f"<p>{value}</p>"
