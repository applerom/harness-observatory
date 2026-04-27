from observatory.importers.markdown_table import parse_pipe_tables, split_pipe_row


def test_split_pipe_row_preserves_code_span_pipes() -> None:
    row = r"| Harness | Evidence | Note |"
    assert split_pipe_row(row) == ["Harness", "Evidence", "Note"]

    row_with_code = r"| OpenCode | `a | b` and `x\|y` | кириллица ✅ |"
    assert split_pipe_row(row_with_code) == ["OpenCode", "`a | b` and `x\\|y`", "кириллица ✅"]


def test_parse_pipe_tables_returns_headers_rows_and_start_line() -> None:
    markdown = """
Intro

| Harness | Primary evidence |
|---|---|
| OpenCode | `src/session.ts:12` |
| Codex CLI | `codex-rs/core.rs` |
"""
    tables = parse_pipe_tables(markdown)

    assert len(tables) == 1
    assert tables[0].headers == ["Harness", "Primary evidence"]
    assert tables[0].start_line == 4
    assert tables[0].rows[0]["Harness"] == "OpenCode"
    assert tables[0].rows[1]["Primary evidence"] == "`codex-rs/core.rs`"

