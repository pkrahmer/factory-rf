"""Shared helpers of the take tests: the dataset beside the host's checkout, and the take."""

from collections.abc import Sequence
from pathlib import Path

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.take import TakeReport, TakeService
from factory.domain.git import ChangedPath, ChangeKind
from git_support import write_files
from undo_support import PATH

DATASET_CHECKOUT = "checkout"
AGENT_TEXT = "written by the agent\n"


def dataset_of(boundaries: Boundaries) -> Path:
    """The dataset's mount point, a folder beside the host's checkout."""
    return boundaries.checkout.parent / "dataset"


def write_dataset(boundaries: Boundaries, files: dict[str, str]) -> None:
    """Write each file under the dataset's `checkout/`, as the agent would have."""
    write_files(dataset_of(boundaries) / DATASET_CHECKOUT, files)


def dataset_text(boundaries: Boundaries, path: str) -> str | None:
    """The text of `path` under the dataset's `checkout/`, or `None` when there is none."""
    target = dataset_of(boundaries) / DATASET_CHECKOUT / path
    return target.read_text(encoding="utf-8") if target.exists() else None


def copy_work_item_to_dataset(boundaries: Boundaries) -> str:
    """Put the host's work item into the dataset, as the stage started, and return its text."""
    text = (boundaries.checkout / PATH).read_text(encoding="utf-8")
    write_dataset(boundaries, {PATH: text})
    return text


def changed(path: str, change: ChangeKind) -> ChangedPath:
    """A changed path of the dataset's `checkout/`."""
    return ChangedPath(path=f"{DATASET_CHECKOUT}/{path}", change=change)


def take_stage(
    boundaries: Boundaries, start: StageStart, changes: Sequence[ChangedPath]
) -> TakeReport:
    """Run the take of the work item of `start_stage` from the dataset beside the checkout."""
    dataset_of(boundaries).mkdir(parents=True, exist_ok=True)
    return TakeService(boundaries, dataset_of(boundaries)).take(start, PATH, changes)
