"""The acceptance handlers refuse a report without a state before they push or post anything."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from acceptance_walk import FIRST, FIRST_RECORDS, AcceptanceWalk, report_of
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.application.acceptance import (
    AcceptanceClosed,
    AcceptanceHandOver,
    AcceptanceMerged,
)
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.files import WorkItemReader
from factory.domain.errors import CannotHandle
from factory.domain.events import Event
from factory.domain.identifiers import branch_name
from factory.domain.paths import MAIN_BRANCH
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument
from git_support import remote_commit

HandlerFactory = Callable[[Boundaries, PipelineDefinition], Handler]


class StatelessReportReader(WorkItemReader):
    """Reads the report at one path as a document without a state; delegates everything else."""

    def __init__(self, report: Path) -> None:
        """Give `report` without a state; read every other file with the real reader."""
        self._report = report
        self._reader = FrontmatterWorkItemReader()

    def parse(self, text: str) -> WorkItemDocument:
        """Parse with the real reader."""
        return self._reader.parse(text)

    def parse_specification(self, text: str) -> WorkItemDocument:
        """Parse with the real reader."""
        return self._reader.parse_specification(text)

    def read(self, path: Path) -> WorkItemDocument:
        """The report's text without a state, any other file through the real reader."""
        if path == self._report:
            return WorkItemDocument(state=None, body=path.read_text(encoding="utf-8"))
        return self._reader.read(path)


def _hand_over(walk: AcceptanceWalk, number: int) -> None:
    walk.record(FIRST, number, FIRST_RECORDS, stage="approval")


def _merged(walk: AcceptanceWalk, number: int) -> None:
    walk.record(FIRST, number, FIRST_RECORDS, stage="approval", handed_over="approval")
    walk.merge(FIRST, number)


def _closed(walk: AcceptanceWalk, number: int) -> None:
    walk.record(FIRST, number, FIRST_RECORDS, stage="approval", handed_over="approval")
    walk.close(number)


@pytest.mark.parametrize(
    ("bring", "handler", "kind", "reason", "branch"),
    [
        pytest.param(
            _hand_over,
            AcceptanceHandOver,
            "hand_over",
            "the work item on its branch has no state",
            branch_name(FIRST),
            id="hand_over",
        ),
        pytest.param(
            _merged,
            AcceptanceMerged,
            "merged",
            "the report on the main branch has no state",
            MAIN_BRANCH,
            id="merged",
        ),
        pytest.param(
            _closed,
            AcceptanceClosed,
            "closed",
            "the report on its branch has no state",
            branch_name(FIRST),
            id="closed",
        ),
    ],
)
def test_a_stateless_report_is_refused_before_anything_is_pushed_or_posted(
    bring: Callable[[AcceptanceWalk, int], None],
    handler: HandlerFactory,
    kind: str,
    reason: str,
    branch: str,
    *,
    walk: AcceptanceWalk,
    boundaries: Boundaries,
    hosting: FakeHostingService,
    remote: Path,
) -> None:
    number = walk.open(FIRST)
    bring(walk, number)
    event: Event = walk.evaluate()
    assert event.kind == kind
    reader = StatelessReportReader(boundaries.checkout / report_of(FIRST))
    stand_in = replace(boundaries, work_item_reader=reader)
    pushed = remote_commit(remote, branch)
    comments = hosting.list_comments(number)

    with pytest.raises(CannotHandle) as raised:
        handler(stand_in, walk.definition).handle(event)

    assert (raised.value.kind, raised.value.reason) == (kind, reason)
    assert remote_commit(remote, branch) == pushed
    assert hosting.list_comments(number) == comments
