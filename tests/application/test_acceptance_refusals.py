"""Opening an acceptance refuses every status but due, and story files count only directly."""

from pathlib import Path

import pytest

from acceptance_walk import FEATURE, FIRST, TODO, AcceptanceWalk, report_of
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.application.acceptance import AcceptanceService
from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import AcceptanceOutcome, AcceptanceState
from factory.domain.board import AcceptanceStatus
from factory.domain.errors import CannotHandle
from factory.domain.identifiers import branch_name
from factory.domain.paths import feature_file_path, work_item_path
from factory.domain.work_item import WorkItemDocument
from git_support import PIPELINE_YAML, remote_commit, run_git
from human_clone import HumanClone

ARCHIVED = ["F0002-S0001", "F0002-S0002"]
OUTCOMES: dict[AcceptanceStatus, AcceptanceOutcome] = {"accepted": "accepted", "refused": "refused"}
REFUSING: list[AcceptanceStatus] = ["in_flight", "merged_unrecorded", "accepted", "refused"]


@pytest.fixture
def brought(
    request: pytest.FixtureRequest, walk: AcceptanceWalk, boundaries: Boundaries, human: HumanClone
) -> AcceptanceStatus:
    """Bring `F0002-todo` into the status the test is parametrized with; return that status."""
    status: AcceptanceStatus = request.param
    if status in ("in_flight", "merged_unrecorded"):
        boundaries.git.fetch()
        AcceptanceService(boundaries, walk.definition).open(FEATURE)
    if status == "merged_unrecorded":
        human.merge(branch_name(FIRST), "merge")
    outcome = OUTCOMES.get(status)
    if outcome is not None:
        state = AcceptanceState(stage="done", outcome=outcome, stories=ARCHIVED)
        report = WorkItemDocument(state=state, body="# Acceptance\n")
        text = FrontmatterWorkItemWriter().render(report)
        human.push_file("main", report_of(FIRST, "done"), text)
    assert walk.status() == status
    return status


@pytest.mark.parametrize("brought", [*REFUSING, "due"], indirect=True)
def test_only_a_due_feature_is_opened(
    brought: AcceptanceStatus, walk: AcceptanceWalk, boundaries: Boundaries, remote: Path
) -> None:
    service = AcceptanceService(boundaries, walk.definition)

    if brought == "due":
        assert service.open(FEATURE).id == FIRST
        assert remote_commit(remote, branch_name(FIRST)) is not None
    else:
        with pytest.raises(CannotHandle) as raised:
            service.open(FEATURE)
        assert raised.value.kind == "acceptance_due"
        assert raised.value.reason == f"feature F0002 is {brought}, not due"


@pytest.mark.parametrize("brought", REFUSING, indirect=True)
def test_a_refused_opening_leaves_every_remote_branch_as_it_was(
    brought: AcceptanceStatus, walk: AcceptanceWalk, boundaries: Boundaries, remote: Path
) -> None:
    before = run_git(remote, "for-each-ref", "refs/heads")

    with pytest.raises(CannotHandle, match=f"is {brought}, not due"):
        AcceptanceService(boundaries, walk.definition).open(FEATURE)

    assert run_git(remote, "for-each-ref", "refs/heads") == before
    assert remote_commit(remote, branch_name("F0002-A0002")) is None


@pytest.mark.parametrize(
    ("paths", "status", "done"),
    [
        ([work_item_path(TODO, "done", "old/F0002-S0001-a.md")], "incomplete", []),
        (
            [
                work_item_path(TODO, "done", "F0002-S0001-a.md"),
                work_item_path(TODO, "backlog", "old/F0002-S0002-b.md"),
            ],
            "due",
            ["F0002-S0001-a.md"],
        ),
    ],
    ids=["only-below-done", "below-backlog"],
)
def test_a_story_file_counts_only_directly_in_its_folder(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    paths: list[str],
    status: AcceptanceStatus,
    done: list[str],
) -> None:
    human.push_file("main", feature_file_path(TODO), "# Todo service\n")
    for path in paths:
        human.push_file("main", path, "# Story\n")
    boundaries.git.fetch()
    reader = AcceptanceReader(boundaries, boundaries.pipeline_reader.parse(PIPELINE_YAML))

    statuses = {entry.feature: entry.status for entry in reader.read()}

    assert statuses[FEATURE] == status
    assert reader.feature_files(FEATURE).done == done
