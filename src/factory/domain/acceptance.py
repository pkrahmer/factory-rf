"""The feature acceptance as data: its id, its report file name, its state and its status."""

from collections.abc import Iterable, Sequence
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from factory.domain.board import AcceptanceStatus
from factory.domain.identifiers import (
    FeatureId,
    WorkItemId,
    feature_of,
    is_acceptance,
    parse_work_item_file_name,
)
from factory.domain.paths import LifecycleFolder
from factory.domain.pipeline_definition import DONE_STAGE
from factory.domain.work_item import WorkItemState

ACCEPTANCE_SLUG = "acceptance"
AcceptanceOutcome = Literal["accepted", "refused"]

_FIRST_NUMBER = 1
_LAST_NUMBER = 9999


class AcceptanceState(WorkItemState):
    """The state of a feature acceptance: a work item's, the stories it covers and its outcome."""

    stories: list[WorkItemId] = []
    outcome: AcceptanceOutcome | None = None

    @field_validator("stories")
    @classmethod
    def _stories_only_strictly_ascending(cls, stories: list[str]) -> list[str]:
        acceptances = [story for story in stories if is_acceptance(story)]
        if acceptances:
            raise ValueError(f"stories must hold story ids only, got {acceptances}")
        if stories != sorted(set(stories)):
            raise ValueError(f"stories must ascend without repeats, got {stories}")
        return stories

    @model_validator(mode="after")
    def _outcome_exactly_when_done(self) -> Self:
        if self.stage == DONE_STAGE and self.outcome is None:
            raise ValueError(f"an acceptance at {DONE_STAGE!r} needs an outcome")
        if self.stage != DONE_STAGE and self.outcome is not None:
            raise ValueError(f"an acceptance at {self.stage!r} has no outcome yet")
        return self


def acceptance_id(feature: FeatureId, number: int) -> WorkItemId:
    """Return the id of the feature's acceptance with the given number, 1 to 9999."""
    if not _FIRST_NUMBER <= number <= _LAST_NUMBER:
        raise ValueError(
            f"an acceptance number runs from {_FIRST_NUMBER} to {_LAST_NUMBER}, got {number}"
        )
    return f"{feature}-A{number:04d}"


def _acceptance_number(work_item: WorkItemId) -> int:
    return int(work_item.split("-A")[1])


def next_acceptance_id(feature: FeatureId, existing: Iterable[WorkItemId]) -> WorkItemId:
    """Return the id after the feature's highest acceptance among `existing`; a gap stays open."""
    numbers = [
        _acceptance_number(work_item)
        for work_item in existing
        if is_acceptance(work_item) and feature_of(work_item) == feature
    ]
    return acceptance_id(feature, max(numbers, default=0) + 1)


def acceptance_file_name(work_item: WorkItemId) -> str:
    """Return the file name of the acceptance's report."""
    if not is_acceptance(work_item):
        raise ValueError(f"not an acceptance id: {work_item!r}")
    return f"{work_item}-{ACCEPTANCE_SLUG}.md"


class FeatureFiles(BaseModel):
    """The file names directly in a feature's three lifecycle folders."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    feature: FeatureId
    backlog: list[str] = []
    in_progress: list[str] = []
    done: list[str] = []


class ReportFacts(BaseModel):
    """One acceptance report as read: its id, folder, state and whether it is on its branch."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: WorkItemId
    folder: LifecycleFolder
    state: AcceptanceState
    on_branch: bool


class FeatureAcceptance(BaseModel):
    """A feature's acceptance as the remote shows it: its status and what comes next."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    feature: FeatureId
    directory: str
    status: AcceptanceStatus
    archived: list[WorkItemId]
    next_acceptance: WorkItemId


def story_file_ids(names: Iterable[str]) -> list[WorkItemId]:
    """The ids of the story files among `names`, ascending without repeats; others are ignored."""
    ids: set[WorkItemId] = set()
    for name in names:
        parsed = parse_work_item_file_name(name)
        if parsed is not None and not is_acceptance(parsed.id):
            ids.add(parsed.id)
    return sorted(ids)


def acceptance_status(files: FeatureFiles, reports: Sequence[ReportFacts]) -> AcceptanceStatus:
    """The status of the feature's acceptance from its folders and every report of it."""
    on_main = [report for report in reports if not report.on_branch]
    merged_ids = {report.id for report in on_main}
    if any(report.on_branch and report.id not in merged_ids for report in reports):
        return "in_flight"
    if any(report.state.stage != DONE_STAGE for report in on_main):
        return "merged_unrecorded"
    archived = story_file_ids(files.done)
    if not archived or story_file_ids(files.backlog) or story_file_ids(files.in_progress):
        return "incomplete"
    return _recorded_outcome(on_main, archived) or "due"


def _recorded_outcome(
    on_main: Sequence[ReportFacts], archived: list[WorkItemId]
) -> AcceptanceOutcome | None:
    covering = [
        report
        for report in on_main
        if set(report.state.stories) == set(archived) and report.state.outcome is not None
    ]
    if not covering:
        return None
    return max(covering, key=lambda report: report.id).state.outcome
