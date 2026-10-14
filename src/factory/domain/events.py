"""The event: what the watcher saw on the remote, as one kind with its work item or feature."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from factory.domain.git import CommitId
from factory.domain.hosting import PullRequestView
from factory.domain.identifiers import FeatureId
from factory.domain.work_item import WorkItemSnapshot

EventKind = Literal[
    "run",
    "comment",
    "ask",
    "merged",
    "closed",
    "reject",
    "hand_over",
    "crash",
    "expired",
    "duplicate",
    "pull_request_lookup",
    "acceptance_due",
    "idle",
]

_WITHOUT_WORK_ITEM: frozenset[EventKind] = frozenset({"idle", "acceptance_due"})
_NO_SUBJECT = "-"


class Event(BaseModel):
    """One event of one evaluation; `detail` is for display and never read back."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: EventKind
    work_item: WorkItemSnapshot | None
    pull_request: PullRequestView | None = None
    feature: FeatureId | None = None
    remote_state: CommitId
    detail: str = ""

    @model_validator(mode="after")
    def _subject_fits_the_kind(self) -> Self:
        needs_work_item = self.kind not in _WITHOUT_WORK_ITEM
        if needs_work_item != (self.work_item is not None):
            requirement = "needs" if needs_work_item else "takes no"
            raise ValueError(f"an event of kind {self.kind} {requirement} work item")
        needs_feature = self.kind == "acceptance_due"
        if needs_feature != (self.feature is not None):
            requirement = "needs" if needs_feature else "takes no"
            raise ValueError(f"an event of kind {self.kind} {requirement} feature")
        return self

    @property
    def key(self) -> str:
        """The kind and the work item's id, else the feature's id, else a dash."""
        if self.work_item is not None:
            return f"{self.kind}:{self.work_item.id}"
        if self.feature is not None:
            return f"{self.kind}:{self.feature}"
        return f"{self.kind}:{_NO_SUBJECT}"
