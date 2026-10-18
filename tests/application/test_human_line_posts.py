"""The cost table posted at the approval ends with the human's waits of the work item's journal."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from bill_support import completed_records, sidecar_text
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.acceptance import AcceptanceHandOver, AcceptanceService
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.hand_over import HandOverHandler
from factory.domain.acceptance import AcceptanceState
from factory.domain.bills import bills_by_stage, cost_table
from factory.domain.events import Event
from factory.domain.hand_over import cost_table_key
from factory.domain.hosting import render_post
from factory.domain.identifiers import branch_name
from factory.domain.journal import FACTORY, HUMAN, JournalRecord
from factory.domain.paths import cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import cost_table_post
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import PIPELINE_YAML
from human_clone import HumanClone

APPROVAL = "approval"
TODO = "factory/features/F0002-todo"
HUMAN_LINE = "1 questions answered (question 1), 1.5 h waited"
BODY = (
    "# A work item\n\n## Description\n\nBuild it.\n\n## Journal\n\n"
    "1. factory: started.\n2. reviewer: a question.\n3. 2026-10-18 human: an answer.\n"
)
JOURNAL = [
    JournalRecord(number=1, speaker=FACTORY, kind="started"),
    JournalRecord(
        number=2,
        speaker="reviewer",
        kind="question",
        at=datetime(2026, 10, 18, 10, 0, tzinfo=UTC),
        blocked="question",
    ),
    JournalRecord(
        number=3, speaker=HUMAN, kind="comment", at=datetime(2026, 10, 18, 11, 30, tzinfo=UTC)
    ),
]


def _story_state(pull_request: int) -> WorkItemState:
    return WorkItemState(stage=APPROVAL, pull_request=pull_request, journal=JOURNAL)


def _acceptance_state(pull_request: int) -> WorkItemState:
    return AcceptanceState(
        stage=APPROVAL,
        stories=["F0002-S0001", "F0002-S0002"],
        pull_request=pull_request,
        journal=JOURNAL,
    )


def _open_nothing(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone
) -> None:
    del boundaries, definition, human


def _open_acceptance(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone
) -> None:
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")
    boundaries.git.fetch()
    AcceptanceService(boundaries, definition).open("F0002")


@dataclass(frozen=True)
class HandOverCase:
    """A work item at its approval: where it lives, how it is opened, its state, its handler."""

    work_item: str
    path: str
    open: Callable[[Boundaries, PipelineDefinition, HumanClone], None]
    state: Callable[[int], WorkItemState]
    handler: Callable[[Boundaries, PipelineDefinition], Handler]


STORY = HandOverCase(
    work_item="F0001-S0001",
    path="factory/features/F0001-example/in-progress/F0001-S0001-first.md",
    open=_open_nothing,
    state=_story_state,
    handler=HandOverHandler,
)
ACCEPTANCE = HandOverCase(
    work_item="F0002-A0001",
    path=f"{TODO}/in-progress/F0002-A0001-acceptance.md",
    open=_open_acceptance,
    state=_acceptance_state,
    handler=AcceptanceHandOver,
)


@pytest.mark.parametrize("case", [STORY, ACCEPTANCE], ids=["story", "acceptance"])
def test_the_hand_over_posts_the_cost_table_with_the_human_line_of_the_journal(
    boundaries: Boundaries, *, hosting: FakeHostingService, human: HumanClone, case: HandOverCase
) -> None:
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    case.open(boundaries, definition, human)
    branch = branch_name(case.work_item)
    number = hosting.create_pull_request(branch, case.work_item, "body", draft=True).number
    records = completed_records(case.work_item, 2)
    document = WorkItemDocument(state=case.state(number), body=BODY)
    human.push_file(branch, cost_records_path(case.path), sidecar_text(records))
    human.push_file(branch, case.path, boundaries.work_item_writer.render(document))
    boundaries.git.fetch()
    snapshot = WorkItemSnapshot(
        id=case.work_item,
        path=case.path,
        folder="in-progress",
        branch=branch,
        branch_commit=boundaries.git.resolve(f"origin/{branch}"),
        document=document,
    )

    case.handler(boundaries, definition).handle(
        Event(kind="hand_over", work_item=snapshot, remote_state="a" * 40)
    )

    [post] = hosting.factory_posts(number)
    key = cost_table_key(case.work_item, document)
    table = cost_table(bills_by_stage(records))
    assert post.key == key
    assert post.body == render_post(cost_table_post(table, human=HUMAN_LINE), key)
    assert f"Human: {HUMAN_LINE}" in post.body.splitlines()
