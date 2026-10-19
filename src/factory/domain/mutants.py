"""The report of a mutation run: mutmut's result lines read, reported and named for a rerun."""

from collections import Counter
from collections.abc import Sequence
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError

MutantStatus = Literal[
    "killed",
    "survived",
    "timeout",
    "suspicious",
    "no tests",
    "skipped",
    "segfault",
    "caught by type check",
    "check was interrupted by user",
    "not checked",
]

MutantName = Annotated[str, StringConstraints(pattern=r"^[^\s.:]+(\.[^\s.:]+)+$")]

_SEPARATOR = ": "
_REPORTED: frozenset[MutantStatus] = frozenset({"survived", "timeout", "suspicious", "segfault"})
_DONE_WITH: frozenset[MutantStatus] = frozenset({"killed", "caught by type check"})
_OTHER: frozenset[MutantStatus] = frozenset(
    {"suspicious", "skipped", "segfault", "caught by type check", "check was interrupted by user"}
)


class MutantResult(BaseModel):
    """One mutant of a mutation run, by mutmut's name for it, and how its run ended."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: MutantName
    status: MutantStatus

    @property
    def module(self) -> str:
        """The dotted module the mutant belongs to: its name without the last part."""
        return self.name.rpartition(".")[0]


class MutationReport(BaseModel):
    """What a mutation run of some modules printed for the reader, and whether it is complete."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lines: list[str]
    partial: bool


def _parse_line(line: str) -> MutantResult:
    name, separator, status = line.rpartition(_SEPARATOR)
    refusal = ValueError(f"not a result line of mutmut: {line!r}")
    if not separator:
        raise refusal
    try:
        return MutantResult.model_validate({"name": name, "status": status})
    except ValidationError as error:
        raise refusal from error


def parse_results(text: str) -> list[MutantResult]:
    """Read the lines `mutmut results --all true` prints, in their order, blank lines skipped."""
    stripped = (line.strip() for line in text.splitlines())
    return [_parse_line(line) for line in stripped if line]


def _chosen(results: Sequence[MutantResult], modules: Sequence[str]) -> list[MutantResult]:
    wanted = set(modules)
    return [result for result in results if result.module in wanted]


def _last_line(
    chosen: Sequence[MutantResult], module_count: int, *, partial: bool, stopped_after: int | None
) -> str:
    counts = Counter(result.status for result in chosen)
    other = sum(counts[status] for status in _OTHER)
    prefix = "partial, " if partial else ""
    stop = "" if stopped_after is None else f" (stopped after {stopped_after} s)"
    return (
        f"mutants: {prefix}{counts['killed']} killed, {counts['survived']} survived, "
        f"{counts['timeout']} timed out, {counts['no tests']} without tests, "
        f"{counts['not checked']} not checked, {other} other "
        f"of {len(chosen)} mutant(s) in {module_count} module(s){stop}"
    )


def mutation_report(
    results: Sequence[MutantResult], modules: Sequence[str], *, stopped_after: int | None
) -> MutationReport:
    """Report the open mutants of the modules and a last line that counts every status."""
    if stopped_after is not None and stopped_after < 1:
        raise ValueError(f"stopped_after must be at least 1, not {stopped_after}")
    chosen = _chosen(results, modules)
    reported = [
        f"{result.name}{_SEPARATOR}{result.status}"
        for result in chosen
        if result.status in _REPORTED
    ]
    partial = stopped_after is not None or any(result.status == "not checked" for result in chosen)
    last = _last_line(chosen, len(set(modules)), partial=partial, stopped_after=stopped_after)
    return MutationReport(lines=[*reported, last], partial=partial)


def rerun_names(results: Sequence[MutantResult], modules: Sequence[str]) -> list[str]:
    """Name the mutants of the modules still to run, and a pattern for a module with none."""
    chosen = _chosen(results, modules)
    names = [result.name for result in chosen if result.status not in _DONE_WITH]
    with_results = {result.module for result in chosen}
    without = [module for module in dict.fromkeys(modules) if module not in with_results]
    return [*names, *(f"{module}.*" for module in without)]
