"""The preflight's report on the machine and the one machine stop a failed report becomes."""

from pydantic import AwareDatetime, BaseModel, ConfigDict

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
