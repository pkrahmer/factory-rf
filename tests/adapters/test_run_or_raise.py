"""The run-or-raise helper: one request, one result, and the wrapper's own fault on a failure."""

import ast
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.printed_output import no_end_detail
from factory.adapters.process import run_or_raise
from source_search import SRC

_LIMIT = timedelta(seconds=10)
_DEFAULT = "default"


def _fault(detail: str) -> Exception:
    return RuntimeError(detail)


def _shell(script: str) -> Callable[[Path], list[str]]:
    return lambda _tmp_path: ["sh", "-c", script]


def _missing_program(tmp_path: Path) -> list[str]:
    return [str(tmp_path / "no-such-program")]


@dataclass(frozen=True)
class _Row:
    argv: Callable[[Path], list[str]]
    accepted: tuple[int, ...] | None | str = _DEFAULT
    time_limit: timedelta = _LIMIT
    exit_status: int | None = None
    stdout: str | None = None
    fault_text: str | None = None
    start_failure: bool = False


@pytest.mark.parametrize(
    "row",
    [
        pytest.param(_Row(_shell("echo ok"), exit_status=0, stdout="ok\n"), id="success"),
        pytest.param(_Row(_shell("echo boom; exit 3"), fault_text="boom"), id="refused-status"),
        pytest.param(
            _Row(_shell("echo boom >&2; exit 3"), fault_text="boom"), id="refused-status-stderr"
        ),
        pytest.param(
            _Row(_shell("echo boom; exit 3"), accepted=(0, 3), exit_status=3), id="accepted-status"
        ),
        pytest.param(
            _Row(_shell("echo boom; exit 3"), accepted=None, exit_status=3), id="every-status"
        ),
        pytest.param(_Row(_shell("exit 1"), fault_text="exit status 1"), id="nothing-printed"),
        pytest.param(_Row(_missing_program, start_failure=True), id="cannot-start"),
        pytest.param(
            _Row(
                _shell("sleep 30"),
                time_limit=timedelta(seconds=1),
                fault_text=no_end_detail(timedelta(seconds=1)),
            ),
            id="time-limit",
        ),
    ],
)
def test_run_or_raise_returns_the_result_or_raises_the_wrappers_fault(
    row: _Row, tmp_path: Path
) -> None:
    def call() -> tuple[int | None, str]:
        argv = row.argv(tmp_path)
        if isinstance(row.accepted, str):
            result = run_or_raise(argv, time_limit=row.time_limit, fault=_fault)
        else:
            result = run_or_raise(
                argv, time_limit=row.time_limit, fault=_fault, accepted=row.accepted
            )
        return result.exit_status, result.stdout

    if row.fault_text is None and not row.start_failure:
        exit_status, stdout = call()
        assert exit_status == row.exit_status
        if row.stdout is not None:
            assert stdout == row.stdout
        return

    with pytest.raises(RuntimeError) as raised:
        call()

    if row.start_failure:
        assert isinstance(raised.value.__cause__, OSError)
        assert str(raised.value) == str(raised.value.__cause__)
    else:
        assert str(raised.value) == row.fault_text


@pytest.mark.parametrize("given", [pytest.param(False, id="root"), pytest.param(True, id="given")])
def test_run_or_raise_runs_in_root_unless_given_a_directory(given: bool, tmp_path: Path) -> None:
    if given:
        result = run_or_raise(["pwd"], time_limit=_LIMIT, fault=_fault, cwd=tmp_path)
        expected = str(tmp_path)
    else:
        result = run_or_raise(["pwd"], time_limit=_LIMIT, fault=_fault)
        expected = "/"

    assert result.stdout.strip() == expected


def _assigned_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _request_builders(node: ast.AST, function: str | None = None) -> list[str | None]:
    """The innermost function around each `ProcessRequest(...)` call under `node`."""
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        function = node.name
    found: list[str | None] = []
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "ProcessRequest"
    ):
        found.append(function)
    for child in ast.iter_child_nodes(node):
        found.extend(_request_builders(child, function))
    return found


@pytest.mark.parametrize(
    ("module", "builders"),
    [
        pytest.param("zfs_snapshots", [], id="zfs_snapshots"),
        pytest.param("power_off", [], id="power_off"),
        pytest.param("podman_runs", ["run"], id="podman_runs"),
    ],
)
def test_the_wrappers_hold_no_copy_of_the_run_or_raise_block(
    module: str, builders: list[str | None]
) -> None:
    path = SRC / "adapters" / f"{module}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    assert "_ROOT" not in _assigned_names(tree)
    assert _request_builders(tree) == builders
