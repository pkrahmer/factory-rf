"""The preflight's report on the machine, the machine stop it becomes, and the stamp it leaves."""

from collections.abc import Sequence

from pydantic import AwareDatetime, BaseModel, ConfigDict

from factory.domain.git import ChangedPath, CommitId
from factory.domain.paths import STOP_RECORDS_FILE
from factory.domain.stops import RepositoryStop


class PreflightItem(BaseModel):
    """One check of the machine: its name, whether it passed and, if not, what to fix."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    passed: bool
    detail: str = ""


class PreflightReport(BaseModel):
    """Every item the preflight ran, in the order it ran them."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    items: list[PreflightItem]

    @property
    def passed(self) -> bool:
        """Whether every item passed; an empty report passes."""
        return all(item.passed for item in self.items)

    def failed(self) -> list[PreflightItem]:
        """The failed items, in order."""
        return [item for item in self.items if not item.passed]


class PreflightStamp(BaseModel):
    """What the last preflight passed on: the image build, and the commit of main it probed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    image: str | None
    main_probed: CommitId | None = None
    main_failed: CommitId | None = None


def version_matches(reported: str, pinned: str) -> bool:
    """Whether the first word of the `reported` version is the non-blank `pinned` version."""
    words = reported.split()
    return bool(pinned.strip()) and bool(words) and words[0] == pinned


def machine_stop(report: PreflightReport, *, at: AwareDatetime) -> RepositoryStop | None:
    """The machine stop naming every failed item of `report`, or `None` when it passed."""
    failed = report.failed()
    if not failed:
        return None
    detail = "; ".join(f"{item.name}: {item.detail}" for item in failed)
    return RepositoryStop(scope="machine", reason="preflight_failed", detail=detail, at=at)


def changes_only_stop_records(paths: Sequence[ChangedPath]) -> bool:
    """Whether `paths` is not empty and every one of them is the stop records file."""
    return bool(paths) and all(changed.path == STOP_RECORDS_FILE for changed in paths)
