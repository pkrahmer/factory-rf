"""The acceptance reviewer's facts sum the human's waits of the archived stories on main."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from factory.application.acceptance import AcceptanceService
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import AcceptanceState
from factory.domain.journal import HUMAN, Blocked, JournalKind, JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML
from human_clone import HumanClone

FEATURE = "F0002"
TODO = "factory/features/F0002-todo"
ASKED = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)
BODY = "# A story\n\n## Journal\n\n1. 2026-10-18 human: created.\n"


def _journal(blocked: Blocked, waited: timedelta, answer: JournalKind) -> list[JournalRecord]:
    return [
        JournalRecord(number=1, speaker=HUMAN, kind="created"),
        JournalRecord(number=2, speaker="reviewer", kind="question", at=ASKED, blocked=blocked),
        JournalRecord(number=3, speaker=HUMAN, kind=answer, at=ASKED + waited),
    ]


def _text(boundaries: Boundaries, state: WorkItemState) -> str:
    return boundaries.work_item_writer.render(WorkItemDocument(state=state, body=BODY))


def _story(boundaries: Boundaries, blocked: Blocked, waited: timedelta) -> str:
    state = WorkItemState(stage="done", journal=_journal(blocked, waited, "comment"))
    return _text(boundaries, state)


def _no_extra(boundaries: Boundaries) -> dict[str, str]:
    del boundaries
    return {}


def _backlog_story(boundaries: Boundaries) -> dict[str, str]:
    text = _story(boundaries, "send_back", timedelta(hours=3))
    return {f"{TODO}/backlog/F0002-S0003-c.md": text}


def _without_front_matter(boundaries: Boundaries) -> dict[str, str]:
    del boundaries
    return {f"{TODO}/done/F0002-S0003-c.md": "# C\n"}


def _invalid_front_matter(boundaries: Boundaries) -> dict[str, str]:
    del boundaries
    return {f"{TODO}/done/F0002-S0003-c.md": "---\nstage: done\nunknown: 1\n---\n# C\n"}


@pytest.mark.parametrize(
    "extra",
    [_no_extra, _backlog_story, _without_front_matter, _invalid_front_matter],
    ids=["counted-stories", "backlog-story", "no-front-matter", "invalid-front-matter"],
)
def test_the_facts_carry_the_waits_of_the_archived_stories_only(
    boundaries: Boundaries, human: HumanClone, extra: Callable[[Boundaries], dict[str, str]]
) -> None:
    report = AcceptanceState(
        stage="done",
        stories=["F0002-S0001", "F0002-S0002"],
        outcome="accepted",
        journal=_journal("round_cap", timedelta(hours=2), "comment"),
    )
    files = {
        f"{TODO}/feature.md": "# Todo service\n",
        f"{TODO}/done/F0002-S0001-a.md": _story(boundaries, "question", timedelta(hours=1)),
        f"{TODO}/done/F0002-S0002-b.md": _text(
            boundaries,
            WorkItemState(
                stage="done", journal=_journal("crash_cap", timedelta(minutes=30), "close")
            ),
        ),
        f"{TODO}/done/F0002-A0001-acceptance.md": _text(boundaries, report),
        **extra(boundaries),
    }
    for path, text in files.items():
        human.push_file("main", path, text)
    boundaries.git.fetch()
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)

    facts = AcceptanceService(boundaries, definition).facts(FEATURE)

    assert facts.human_line == "2 questions answered (question 1, crash_cap 1), 1.5 h waited"
