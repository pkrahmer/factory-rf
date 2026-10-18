"""A question record names the block it opened and a stall record its reason."""

import typing
from datetime import UTC, datetime

import pytest
from pydantic import BaseModel

from factory.domain import decisions, journal, work_item
from factory.domain.journal import (
    FACTORY,
    Blocked,
    JournalRecord,
    NewEntry,
    StallReason,
    append_entry,
)
from factory.domain.work_item import WorkItemDocument, initial_state

AT = datetime(2026, 10, 18, 9, 30, tzinfo=UTC)
BODY = "# T\n\n## Journal\n\n1. 2026-10-17 human: created.\n"
RECORD: type[BaseModel] = JournalRecord


def _document() -> WorkItemDocument:
    created = JournalRecord(number=1, speaker="human", kind="created")
    state = initial_state("tests").model_copy(update={"journal": [created]})
    return WorkItemDocument(state=state, body=BODY)


@pytest.mark.parametrize(
    ("kind", "causes", "accepted"),
    [
        pytest.param("question", {"blocked": "crash_cap"}, True, id="question-blocked"),
        pytest.param("stall", {"reason": "time_limit"}, True, id="stall-reason"),
        pytest.param("question", {}, True, id="question-without"),
        pytest.param("stall", {}, True, id="stall-without"),
        pytest.param("result", {"blocked": "question"}, False, id="result-blocked"),
        pytest.param("comment", {"blocked": "question"}, False, id="comment-blocked"),
        pytest.param("stall", {"blocked": "question"}, False, id="stall-blocked"),
        pytest.param("crash", {"reason": "check_red"}, False, id="crash-reason"),
        pytest.param("expiry", {"reason": "check_red"}, False, id="expiry-reason"),
        pytest.param("question", {"reason": "check_red"}, False, id="question-reason"),
    ],
)
def test_a_cause_is_accepted_only_on_its_own_kind(
    kind: str, causes: dict[str, str], *, accepted: bool
) -> None:
    if accepted:
        record = RECORD(number=1, speaker=FACTORY, kind=kind, **causes)
        assert isinstance(record, JournalRecord)
        assert record.blocked == causes.get("blocked")
        assert record.reason == causes.get("reason")
    else:
        with pytest.raises(ValueError):
            RECORD(number=1, speaker=FACTORY, kind=kind, **causes)


@pytest.mark.parametrize(
    ("kind", "field", "value", "accepted"),
    [
        pytest.param("question", "blocked", "maybe", False, id="blocked-maybe"),
        pytest.param("stall", "reason", "slow", False, id="reason-slow"),
        *(
            pytest.param("question", "blocked", value, True, id=f"blocked-{value}")
            for value in typing.get_args(Blocked)
        ),
        *(
            pytest.param("stall", "reason", value, True, id=f"reason-{value}")
            for value in typing.get_args(StallReason)
        ),
    ],
)
def test_a_cause_outside_its_type_is_refused_and_every_value_of_it_accepted(
    kind: str, field: str, value: str, *, accepted: bool
) -> None:
    if accepted:
        record = RECORD(number=1, speaker=FACTORY, kind=kind, **{field: value})
        assert getattr(record, field) == value
    else:
        with pytest.raises(ValueError):
            RECORD(number=1, speaker=FACTORY, kind=kind, **{field: value})


def test_the_cause_types_kept_in_work_item_and_decisions_are_the_journals() -> None:
    assert typing.get_args(work_item.Blocked) == typing.get_args(journal.Blocked)
    assert typing.get_args(decisions.StallReason) == typing.get_args(journal.StallReason)


@pytest.mark.parametrize(
    ("speaker", "kind", "blocked", "reason", "at", "accepted"),
    [
        pytest.param(FACTORY, "question", "round_cap", None, AT, True, id="question-with-at"),
        pytest.param(FACTORY, "question", "round_cap", None, None, True, id="question-without-at"),
        pytest.param(FACTORY, "stall", None, "merge_conflict", AT, True, id="stall-with-at"),
        pytest.param(FACTORY, "stall", None, "merge_conflict", None, True, id="stall-without-at"),
        pytest.param("tester", "result", "question", None, AT, False, id="result-blocked"),
    ],
)
def test_append_entry_puts_a_cause_into_the_new_record_only_on_its_own_kind(
    speaker: str,
    kind: typing.Literal["question", "stall", "result"],
    blocked: Blocked | None,
    reason: StallReason | None,
    at: datetime | None,
    *,
    accepted: bool,
) -> None:
    entry = NewEntry(speaker=speaker, kind=kind, text="Why it waits.")

    if not accepted:
        with pytest.raises(ValueError):
            append_entry(_document(), entry, at=at, blocked=blocked, reason=reason)
        return
    appended = append_entry(_document(), entry, at=at, blocked=blocked, reason=reason)

    assert appended.state is not None
    record = appended.state.journal[-1]
    assert (record.kind, record.blocked, record.reason, record.at) == (kind, blocked, reason, at)
    if at is None:
        assert (record.stage, record.run) == (None, None)
    else:
        assert record.stage == "tests"
