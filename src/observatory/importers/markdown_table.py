# FILE: src/observatory/importers/markdown_table.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Small markdown pipe-table parser for the v0.1 canon importer.
# PRD_REF: docs/PRD.md §26.1
# WHY_REF: docs/why-graph.xml#MOD-IMPORTER
# SCOPE: pipe table detection; code-span-aware cell splitting; simple row normalization
# INVARIANTS:
# - Code spans may contain literal pipes and must remain in the same cell.
# - This parser is intentionally narrow; ambiguous markdown is reported by the importer.
# START_MODULE_MAP:
# - MarkdownTable: parsed table value object.
# - parse_pipe_tables: find all simple pipe tables in markdown text.
# - split_pipe_row: split one table row while respecting code spans and escaped pipes.
# :END_MODULE_MAP
# :END_MODULE_CONTRACT

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarkdownTable:
    headers: list[str]
    rows: list[dict[str, str]]
    start_line: int


def split_pipe_row(line: str) -> list[str]:
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    backtick_run = 0
    escaped = False

    for char in line.strip():
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            current.append(char)
            continue
        if char == "`":
            backtick_run += 1
            current.append(char)
            continue
        if backtick_run:
            in_code = not in_code
            backtick_run = 0
        if char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    if backtick_run:
        in_code = not in_code
    cells.append("".join(current).strip())
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def parse_pipe_tables(markdown: str) -> list[MarkdownTable]:
    lines = markdown.splitlines()
    tables: list[MarkdownTable] = []
    index = 0
    while index < len(lines) - 1:
        header = lines[index]
        separator = lines[index + 1]
        if "|" not in header or not _is_separator_row(separator):
            index += 1
            continue

        headers = split_pipe_row(header)
        separator_cells = split_pipe_row(separator)
        if len(headers) < 2 or len(separator_cells) != len(headers):
            index += 1
            continue

        rows: list[dict[str, str]] = []
        row_index = index + 2
        while row_index < len(lines) and "|" in lines[row_index].strip():
            values = split_pipe_row(lines[row_index])
            if len(values) == len(headers):
                rows.append(dict(zip(headers, values, strict=True)))
            else:
                break
            row_index += 1

        tables.append(MarkdownTable(headers=headers, rows=rows, start_line=index + 1))
        index = row_index
    return tables


def _is_separator_row(line: str) -> bool:
    cells = split_pipe_row(line)
    if len(cells) < 2:
        return False
    return all(_is_separator_cell(cell) for cell in cells)


def _is_separator_cell(cell: str) -> bool:
    stripped = cell.strip()
    if not stripped:
        return False
    stripped = stripped.strip(":")
    return bool(stripped) and set(stripped) <= {"-"}

