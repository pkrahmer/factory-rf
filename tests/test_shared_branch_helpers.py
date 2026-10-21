"""The work item on its branch, its posts and the disk records are read from one shared place."""

import ast
from pathlib import Path

import pytest

from branch_reading import error_posts, push_state, remote_document
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.domain.hosting import PostKey
from factory.domain.work_item import WorkItemState
from human_clone import HumanClone
from stage_run_support import BACKLOG_PATH, BRANCH, pushed_state

TESTS = Path(__file__).parent
HELPERS = {
    "pushed": ["Boundaries", "Path"],
    "pushed_state": ["Boundaries", "Path"],
    "remote_document": ["Boundaries", "GitCli"],
    "push_state": ["HumanClone", "WorkItemState"],
}
RECORD_LOGS = ("JsonLinesRecordLog[StopRecord]", "JsonLinesRecordLog[DiskRecord]")


def _annotations(function: ast.FunctionDef) -> list[str]:
    arguments = function.args.posonlyargs + function.args.args + function.args.kwonlyargs
    return [
        ast.unparse(argument.annotation) if argument.annotation else "" for argument in arguments
    ]


def _copied(function: ast.FunctionDef) -> str | None:
    name = function.name.removeprefix("_")
    if HELPERS.get(name) == _annotations(function):
        return name
    returned = ast.unparse(function.returns) if function.returns else None
    return returned if returned in RECORD_LOGS else None


def copies(source: str) -> list[str]:
    """The shared helpers and record fixtures the top-level functions of `source` copy."""
    functions = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)]
    return [copied for function in functions if (copied := _copied(function)) is not None]


@pytest.mark.parametrize(
    ("shared", "expected"),
    [
        pytest.param("pushed", ["stage_run_support.py"], id="pushed"),
        pytest.param("pushed_state", ["stage_run_support.py"], id="pushed_state"),
        pytest.param("remote_document", ["branch_reading.py"], id="remote_document"),
        pytest.param("push_state", ["branch_reading.py"], id="push_state"),
        pytest.param("JsonLinesRecordLog[StopRecord]", ["conftest.py"], id="stop-records"),
        pytest.param("JsonLinesRecordLog[DiskRecord]", ["conftest.py"], id="disk-records"),
    ],
)
def test_each_shared_helper_and_fixture_is_written_in_one_module(
    shared: str, expected: list[str]
) -> None:
    holding = sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if shared in copies(path.read_text(encoding="utf-8"))
    )

    assert holding == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "def _pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:\n    ...\n",
            ["pushed"],
            id="a-copy-of-pushed",
        ),
        pytest.param(
            "def __pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:\n    ...\n",
            [],
            id="two-leading-underscores",
        ),
        pytest.param(
            "def _pushed_state(boundaries: Boundaries, path: str) -> WorkItemState:\n    ...\n",
            [],
            id="pushed-state-of-another-path",
        ),
        pytest.param(
            "def _push_state(human: HumanClone, state: WorkItemState, *, path: str = PATH)"
            " -> None:\n    ...\n",
            [],
            id="push-state-with-a-keyword-only-path",
        ),
        pytest.param(
            "def disk_log(tmp_path: Path) -> JsonLinesRecordLog[DiskRecord]:\n    ...\n",
            ["JsonLinesRecordLog[DiskRecord]"],
            id="a-record-fixture-under-another-name",
        ),
        pytest.param(
            "class Rig:\n    def pushed(self, boundaries: Boundaries, remote: Path) -> None:\n"
            "        ...\n",
            [],
            id="a-method-named-pushed",
        ),
    ],
)
def test_the_guard_finds_a_copy_by_name_and_parameters_only(
    source: str, expected: list[str]
) -> None:
    assert copies(source) == expected


def test_the_shared_helpers_read_and_write_as_the_copies_did(
    boundaries: Boundaries,
    human: HumanClone,
    checkout: GitCli,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    state = WorkItemState(stage="doing", pull_request=1)
    human.start(BACKLOG_PATH)

    push_state(human, state)

    assert remote_document(boundaries, checkout).state == state
    assert pushed_state(boundaries, remote) == state
    number = hosting.create_pull_request(BRANCH, "First story", "", draft=True).number
    error = PostKey(work_item="F0001-S0001", kind="error", n="1")
    cost = PostKey(work_item="F0001-S0001", kind="cost_table", n="1")
    hosting.post_comment(number, "An error.", error)
    hosting.post_comment(number, "A cost table.", cost)
    [post] = error_posts(hosting, number)
    assert post.key == error
