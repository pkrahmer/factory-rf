"""Helpers for tests that put a work item on its branch and read files in the checkout."""

from factory.application.boundaries import Boundaries
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState, initial_state

CREATED = JournalRecord(number=1, speaker="human", kind="created")


def created_state(stage: str) -> WorkItemState:
    """A fresh state at `stage` whose journal holds only the human's "created" entry."""
    return initial_state(stage).model_copy(update={"journal": [CREATED]})


def put_work_item(
    boundaries: Boundaries,
    branch: str,
    path: str,
    document: WorkItemDocument,
    *,
    committed: bool = True,
) -> None:
    """Check out `branch` from `origin/main`, write the work item, and commit and push it."""
    git = boundaries.git
    git.fetch()
    git.checkout(branch, start_point="origin/main")
    target = boundaries.checkout / path
    target.parent.mkdir(parents=True, exist_ok=True)
    boundaries.work_item_writer.write(target, document)
    if committed:
        git.commit("prepare the work item")
        assert git.push(branch) == "pushed"


def checkout_text(boundaries: Boundaries, path: str) -> str | None:
    """The text of `path` in the checkout, or `None` when there is no such file."""
    target = boundaries.checkout / path
    return target.read_text(encoding="utf-8") if target.exists() else None
