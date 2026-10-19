"""Each refusal of the claim service names its cause in the text of its `ValueError`."""

from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.domain.git import WorkTreeStatus
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument
from git_support import remote_commit
from work_item_support import checkout_text, created_state, put_work_item

BRANCH = "work-item/F0001-S0001"
OTHER_BRANCH = "work-item/F0001-S0002"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
NOTES = "factory/features/F0001-example/in-progress/notes.md"
BODY = (
    "# First story\n\n## Description\n\nOriginal.\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
)


def _document(stage: str) -> WorkItemDocument:
    return WorkItemDocument(state=created_state(stage), body=BODY)


def _snapshot(
    boundaries: Boundaries, remote: Path
) -> tuple[WorkTreeStatus, str | None, str | None, str | None]:
    return (
        boundaries.git.status(),
        checkout_text(boundaries, PATH),
        checkout_text(boundaries, NOTES),
        remote_commit(remote, BRANCH),
    )


@pytest.fixture
def prepared(boundaries: Boundaries) -> None:
    """Put the work item, at `doing`, on its own pushed branch, which stays checked out."""
    put_work_item(boundaries, BRANCH, PATH, _document("doing"))


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("Factory-1", "not an instance name: 'Factory-1'"),
        ("", "not an instance name: ''"),
        ("factory-1", None),
    ],
    ids=["upper", "empty", "accepted"],
)
def test_service_refusal_of_an_instance_name_quotes_the_name(
    boundaries: Boundaries, definition: PipelineDefinition, name: str, message: str | None
) -> None:
    if message is None:
        ClaimService(boundaries, name, definition)
        return
    with pytest.raises(ValueError) as caught:
        ClaimService(boundaries, name, definition)
    assert str(caught.value) == message


@pytest.mark.parametrize(
    ("branch", "path", "document_stage", "stage", "on_main", "message"),
    [
        (
            BRANCH,
            PATH,
            "doing",
            "review",
            False,
            "the work item is in stage doing, not review",
        ),
        (
            BRANCH,
            PATH,
            "nosuch",
            "nosuch",
            False,
            "nosuch is not a stage of the pipeline definition",
        ),
        (
            BRANCH,
            PATH,
            "approval",
            "approval",
            False,
            "stage approval has no role to claim it for",
        ),
        (
            OTHER_BRANCH,
            PATH,
            "doing",
            "doing",
            False,
            f"{OTHER_BRANCH} is not the work item's branch {BRANCH}",
        ),
        (
            BRANCH,
            NOTES,
            "doing",
            "doing",
            False,
            f"{NOTES} is not a work item's file",
        ),
        (
            BRANCH,
            PATH,
            "doing",
            "doing",
            True,
            f"the checkout is on main, not on {BRANCH}",
        ),
    ],
    ids=[
        "other-stage",
        "unknown-stage",
        "stage-without-role",
        "other-branch",
        "no-work-item-file",
        "checkout-on-main",
    ],
)
@pytest.mark.usefixtures("prepared")
def test_claim_refusal_names_its_cause_and_writes_nothing(
    boundaries: Boundaries,
    remote: Path,
    definition: PipelineDefinition,
    *,
    branch: str,
    path: str,
    document_stage: str,
    stage: str,
    on_main: bool,
    message: str,
) -> None:
    if on_main:
        boundaries.git.checkout("main", start_point="origin/main")
    before = _snapshot(boundaries, remote)
    service = ClaimService(boundaries, "factory-1", definition)

    with pytest.raises(ValueError) as caught:
        service.claim(branch, path, _document(document_stage), stage)

    assert str(caught.value) == message
    assert _snapshot(boundaries, remote) == before
