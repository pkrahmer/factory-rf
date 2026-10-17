"""The proof's helpers: the rerun's time, a branch's state, and one copy of each helper."""

import ast
from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from factory.domain.identifiers import branch_name
from factory.domain.work_item import WorkItemState
from proof_support import (
    FEATURE,
    CaseResult,
    World,
    branch_state,
    case_by_id,
    completed,
    rerun_seconds,
    run_case,
    run_ticks,
    start_story,
    state_at,
    violations,
    work_item_file,
)

TESTS = Path(__file__).parent
HELPER_MODULES = ("proof_support.py", "test_kill_points.py", "test_fault_paths_7_to_13.py")
COPIES = {"_rerun_seconds", "_branch_state", "_state_at", "_opening_text"}
ONE_SECOND = timedelta(seconds=1)


@pytest.fixture(scope="module")
def commit_push(tmp_path_factory: pytest.TempPathFactory) -> CaseResult:
    return run_case(case_by_id("commit-push"), tmp_path_factory.mktemp("commit-push"))


@pytest.fixture(scope="module")
def post_record(tmp_path_factory: pytest.TempPathFactory) -> CaseResult:
    return run_case(case_by_id("post-record"), tmp_path_factory.mktemp("post-record"))


def _as_recorded(result: CaseResult) -> CaseResult:
    return result


def _killed_earlier(result: CaseResult) -> CaseResult:
    assert result.killed_at is not None
    return replace(result, killed_at=result.killed_at - ONE_SECOND)


def _never_killed(result: CaseResult) -> CaseResult:
    return replace(result, killed_at=None)


@pytest.mark.parametrize(
    ("case_id", "change", "expected"),
    [
        ("commit-push", _as_recorded, []),
        ("commit-push", _killed_earlier, ["kill-to-rerun-recorded"]),
        ("commit-push", _never_killed, ["kill-to-rerun-recorded"]),
        ("post-record", _killed_earlier, []),
    ],
    ids=["recorded", "killed-earlier", "no-kill-time", "no-crash-charged"],
)
def test_the_kill_to_rerun_check_holds_only_for_the_recorded_five_seconds(
    request: pytest.FixtureRequest,
    case_id: str,
    change: Callable[[CaseResult], CaseResult],
    expected: list[str],
) -> None:
    result: CaseResult = request.getfixturevalue(case_id.replace("-", "_"))

    found = violations(change(result), case_by_id(case_id), ("kill-to-rerun-recorded",))

    assert found == expected


def test_the_rerun_seconds_of_a_result_without_a_kill_time_raise(commit_push: CaseResult) -> None:
    with pytest.raises(AssertionError):
        rerun_seconds(replace(commit_push, killed_at=None))


def _summary(state: WorkItemState | None) -> tuple[str, int, str | None] | None:
    if state is None:
        return None
    return (state.stage, state.round, state.blocked)


def _ticked_story(world: World) -> tuple[WorkItemState | None, WorkItemState | None]:
    work_item = start_story(world)
    world.agent_runtime.queue(completed("question", "Which format does the title take?"))
    run_ticks(world)
    world.boundaries.git.fetch()
    path = work_item_file(world, work_item)
    held = state_at(world, f"origin/{branch_name(work_item)}", path)
    assert held is not None
    return branch_state(world, work_item), held


def _story_without_branch(world: World) -> tuple[WorkItemState | None, WorkItemState | None]:
    return branch_state(world, start_story(world)), None


def _path_off_main(world: World) -> tuple[WorkItemState | None, WorkItemState | None]:
    world.boundaries.git.fetch()
    return state_at(world, "origin/main", f"{FEATURE}/in-progress/none.md"), None


@pytest.mark.parametrize(
    "read",
    [_ticked_story, _story_without_branch, _path_off_main],
    ids=["ticked-story", "no-branch", "no-file"],
)
def test_the_state_helpers_read_the_branch_or_return_none(
    world: World, read: Callable[[World], tuple[WorkItemState | None, WorkItemState | None]]
) -> None:
    found, expected = read(world)

    assert _summary(found) == _summary(expected)


def _functions(name: str) -> dict[str, ast.FunctionDef]:
    tree = ast.parse((TESTS / name).read_text(encoding="utf-8"))
    return {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def _called(function: ast.FunctionDef) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    return names


def test_each_proof_helper_has_one_copy() -> None:
    defined = {name: set(_functions(name)) & COPIES for name in HELPER_MODULES}
    called = _called(_functions("proof_support.py")["_rerun"])

    assert defined == {name: set() for name in HELPER_MODULES}
    assert "rerun" in called
    assert called & {"restart", "advance"} == set()
    assert not (TESTS / "test_fault_path_names.py").exists()
