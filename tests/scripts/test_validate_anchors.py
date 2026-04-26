import importlib.util
import sys
from collections.abc import Callable
from io import StringIO
from pathlib import Path
from typing import cast


def _load_validator_run() -> Callable[..., int]:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "validate_anchors.py"
    spec = importlib.util.spec_from_file_location("validate_anchors", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(Callable[..., int], module.run)


run = _load_validator_run()


def _write_graph(path: Path, module_state: str, coord: str) -> None:
    path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<Why_Graph schema="0.8" project="fixture">
  <MODULE_FIXTURE ID="MOD-FIXTURE" FILE="src/example.py" STATE="{module_state}">
    <ANCHOR NAME="START_FIXTURE" COORD="{coord}"/>
  </MODULE_FIXTURE>
</Why_Graph>
""",
        encoding="utf-8",
    )


def test_started_module_missing_anchor_fails(tmp_path: Path) -> None:
    repo_root = tmp_path
    graph_path = tmp_path / "why-graph.xml"
    source_path = tmp_path / "src" / "example.py"
    source_path.parent.mkdir()
    source_path.write_text("print('no marker here')\n", encoding="utf-8")
    _write_graph(graph_path, "STARTED", "src/example.py#START_FIXTURE")

    stdout = StringIO()
    stderr = StringIO()
    exit_code = run(graph_path=graph_path, repo_root=repo_root, stdout=stdout, stderr=stderr)

    assert exit_code == 1
    assert "checked 0 anchor(s)" in stdout.getvalue()
    assert "missing marker START_FIXTURE" in stderr.getvalue()


def test_planned_module_with_missing_file_is_skipped(tmp_path: Path) -> None:
    graph_path = tmp_path / "why-graph.xml"
    _write_graph(graph_path, "PLANNED", "src/missing.py#START_FIXTURE")

    stdout = StringIO()
    stderr = StringIO()
    exit_code = run(graph_path=graph_path, repo_root=tmp_path, stdout=stdout, stderr=stderr)

    assert exit_code == 0
    assert "checked 0 anchor(s)" in stdout.getvalue()
    assert "skipped 1 planned anchor(s)" in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_started_module_with_present_anchor_passes(tmp_path: Path) -> None:
    repo_root = tmp_path
    graph_path = tmp_path / "why-graph.xml"
    source_path = tmp_path / "src" / "example.py"
    source_path.parent.mkdir()
    source_path.write_text("# START_FIXTURE:\nprint('ok')\n", encoding="utf-8")
    _write_graph(graph_path, "DONE", "src/example.py#START_FIXTURE")

    stdout = StringIO()
    stderr = StringIO()
    exit_code = run(graph_path=graph_path, repo_root=repo_root, stdout=stdout, stderr=stderr)

    assert exit_code == 0
    assert "checked 1 anchor(s)" in stdout.getvalue()
    assert "Anchor validator: OK" in stdout.getvalue()
    assert stderr.getvalue() == ""
