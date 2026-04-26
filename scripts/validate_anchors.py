"""Validate WHY graph anchors for implemented module states.

Policy: ANCHOR elements inside MODULE_* nodes with STATE="PLANNED" are skipped.
The WHY graph can plan more modules than the code implements at any moment; STATE
is the watershed. Anchors are enforced only for MODULE_* nodes whose STATE is
STARTED or DONE.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from lxml import etree


ENFORCED_STATES = frozenset({"STARTED", "DONE"})
SKIPPED_STATES = frozenset({"PLANNED"})


@dataclass(frozen=True, slots=True)
class AnchorCheck:
    module_id: str
    state: str
    path: Path
    marker: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _is_module_node(element: etree._Element) -> bool:
    return str(element.tag).startswith("MODULE_")


def _parse_coord(coord: str) -> tuple[Path, str]:
    raw_path, separator, raw_marker = coord.partition("#")
    if not separator or not raw_path or not raw_marker:
        raise ValueError(f"invalid COORD {coord!r}; expected repo/path.py#START_MARKER")
    return Path(raw_path), raw_marker


def collect_enforced_anchors(graph_path: Path) -> tuple[list[AnchorCheck], list[str], int]:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.parse(str(graph_path), parser).getroot()
    checks: list[AnchorCheck] = []
    errors: list[str] = []
    skipped = 0

    for module in root.iter():
        if not _is_module_node(module):
            continue

        state = module.get("STATE", "")
        module_id = module.get("ID", "<missing module id>")
        anchors = module.findall("ANCHOR")

        if state in SKIPPED_STATES:
            skipped += len(anchors)
            continue
        if state not in ENFORCED_STATES:
            errors.append(f"{module_id}: unsupported STATE={state!r}")
            continue

        for anchor in anchors:
            name = anchor.get("NAME")
            coord = anchor.get("COORD")
            if not name or not coord:
                errors.append(f"{module_id}: ANCHOR missing NAME or COORD")
                continue
            try:
                path, marker = _parse_coord(coord)
            except ValueError as exc:
                errors.append(f"{module_id}: {exc}")
                continue
            if marker != name:
                errors.append(f"{module_id}: NAME={name!r} does not match COORD marker {marker!r}")
                continue
            checks.append(AnchorCheck(module_id=module_id, state=state, path=path, marker=marker))

    return checks, errors, skipped


def validate_anchors(graph_path: Path, repo_root: Path) -> tuple[list[str], int, int]:
    checks, errors, skipped = collect_enforced_anchors(graph_path)
    validated = 0

    for check in checks:
        target = repo_root / check.path
        if not target.exists():
            errors.append(f"{check.module_id}: missing file {check.path.as_posix()}")
            continue
        if not target.is_file():
            errors.append(f"{check.module_id}: target is not a file {check.path.as_posix()}")
            continue

        text = target.read_text(encoding="utf-8")
        if check.marker not in text:
            errors.append(
                f"{check.module_id}: missing marker {check.marker} in {check.path.as_posix()}"
            )
            continue
        validated += 1

    return errors, validated, skipped


def run(
    graph_path: Path | None = None,
    repo_root: Path | None = None,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    root = repo_root or _repo_root()
    graph = graph_path or root / "docs" / "why-graph.xml"
    errors, validated, skipped = validate_anchors(graph, root)

    print(f"Anchor validator: checked {validated} anchor(s), skipped {skipped} planned anchor(s).", file=stdout)
    if not errors:
        print("Anchor validator: OK", file=stdout)
        return 0

    print("Anchor validator: FAILED", file=stderr)
    for error in errors:
        print(f"- {error}", file=stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate WHY graph anchors against source files.")
    parser.add_argument("--graph", type=Path, default=None, help="Path to docs/why-graph.xml")
    parser.add_argument("--repo-root", type=Path, default=None, help="Repository root path")
    args = parser.parse_args(argv)
    return run(graph_path=args.graph, repo_root=args.repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
