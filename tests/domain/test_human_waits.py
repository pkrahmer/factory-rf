"""The human's waits: one per blocking question, until the human's next record, and their line."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.human_waits import HumanWait, human_line, human_waits
from factory.domain.journal import HUMAN, JournalRecord
from factory.domain.post_texts import cost_table_post

REVIEWER = "reviewer"


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, 18, hour, minute, tzinfo=UTC)


CREATED = JournalRecord(number=1, speaker=HUMAN, kind="created")


@pytest.mark.parametrize(
    ("journal", "expected"),
    [
        pytest.param(
            [
                CREATED,
                JournalRecord(
                    number=2, speaker=REVIEWER, kind="question", at=_at(10), blocked="crash_cap"
                ),
                JournalRecord(number=3, speaker=HUMAN, kind="comment", at=_at(11, 30)),
            ],
            [HumanWait(question=2, blocked="crash_cap", asked_at=_at(10), answered_at=_at(11, 30))],
            id="answered-by-a-comment",
        ),
        pytest.param(
            [
                CREATED,
                JournalRecord(
                    number=2, speaker=REVIEWER, kind="question", at=_at(10), blocked="crash_cap"
                ),
                JournalRecord(number=3, speaker=REVIEWER, kind="result", at=_at(10, 30)),
                JournalRecord(number=4, speaker=HUMAN, kind="comment", at=_at(11, 30)),
            ],
            [HumanWait(question=2, blocked="crash_cap", asked_at=_at(10), answered_at=_at(11, 30))],
            id="a-result-between-ends-nothing",
        ),
        pytest.param(
            [
                CREATED,
                JournalRecord(
                    number=2, speaker=REVIEWER, kind="question", at=_at(10), blocked="send_back"
                ),
                JournalRecord(number=3, speaker=HUMAN, kind="close", at=_at(10, 45)),
            ],
            [HumanWait(question=2, blocked="send_back", asked_at=_at(10), answered_at=_at(10, 45))],
            id="answered-by-a-close",
        ),
        pytest.param(
            [
                CREATED,
                JournalRecord(
                    number=2, speaker=REVIEWER, kind="question", at=_at(10), blocked="question"
                ),
            ],
            [HumanWait(question=2, blocked="question", asked_at=_at(10))],
            id="unanswered",
        ),
        pytest.param(
            [
                CREATED,
                JournalRecord(number=2, speaker=REVIEWER, kind="question", at=_at(10)),
                JournalRecord(number=3, speaker=HUMAN, kind="comment", at=_at(11)),
            ],
            [],
            id="question-without-blocked",
        ),
        pytest.param(
            [
                CREATED,
                JournalRecord(number=2, speaker=REVIEWER, kind="question", blocked="question"),
                JournalRecord(number=3, speaker=HUMAN, kind="comment", at=_at(11)),
            ],
            [],
            id="question-without-at",
        ),
        pytest.param(
            [
                CREATED,
                JournalRecord(
                    number=2, speaker=REVIEWER, kind="question", at=_at(10), blocked="question"
                ),
                JournalRecord(number=3, speaker=HUMAN, kind="comment"),
                JournalRecord(number=4, speaker=HUMAN, kind="comment", at=_at(12)),
            ],
            [HumanWait(question=2, blocked="question", asked_at=_at(10), answered_at=_at(12))],
            id="a-human-record-without-at-ends-nothing",
        ),
        pytest.param(
            [
                CREATED,
                JournalRecord(
                    number=2, speaker=REVIEWER, kind="question", at=_at(10), blocked="question"
                ),
                JournalRecord(number=3, speaker=HUMAN, kind="comment", at=_at(11)),
                JournalRecord(
                    number=4, speaker="coder", kind="question", at=_at(12), blocked="round_cap"
                ),
                JournalRecord(number=5, speaker=HUMAN, kind="comment", at=_at(13)),
            ],
            [
                HumanWait(question=2, blocked="question", asked_at=_at(10), answered_at=_at(11)),
                HumanWait(question=4, blocked="round_cap", asked_at=_at(12), answered_at=_at(13)),
            ],
            id="two-waits-in-journal-order",
        ),
        pytest.param(
            [
                CREATED,
                JournalRecord(number=2, speaker=HUMAN, kind="comment", at=_at(9)),
                JournalRecord(
                    number=3, speaker=REVIEWER, kind="question", at=_at(10), blocked="question"
                ),
            ],
            [HumanWait(question=3, blocked="question", asked_at=_at(10))],
            id="a-human-record-before-the-question-ends-nothing",
        ),
    ],
)
def test_each_blocking_question_waits_until_the_next_human_record_with_a_time(
    journal: list[JournalRecord], expected: list[HumanWait]
) -> None:
    assert human_waits(journal) == expected


@pytest.mark.parametrize(("question", "accepted"), [(0, False), (1, True)], ids=["zero", "one"])
def test_a_wait_names_a_question_numbered_from_one(question: int, accepted: bool) -> None:
    model: type[BaseModel] = HumanWait

    if not accepted:
        with pytest.raises(ValidationError):
            model(question=question, blocked="question", asked_at=_at(10))
        return
    wait = model(question=question, blocked="question", asked_at=_at(10))
    assert isinstance(wait, HumanWait)
    assert wait.question == question


def _answered(blocked: str, duration: timedelta) -> HumanWait:
    return HumanWait.model_validate(
        {"question": 2, "blocked": blocked, "asked_at": _at(10), "answered_at": _at(10) + duration}
    )


def _unanswered(blocked: str) -> HumanWait:
    return HumanWait.model_validate({"question": 3, "blocked": blocked, "asked_at": _at(10)})


@pytest.mark.parametrize(
    ("waits", "expected"),
    [
        pytest.param([], "0 questions answered, 0.0 h waited", id="no-waits"),
        pytest.param(
            [_answered("crash_cap", timedelta(hours=1, minutes=30))],
            "1 questions answered (crash_cap 1), 1.5 h waited",
            id="one-answered",
        ),
        pytest.param(
            [
                _answered("round_cap", timedelta(minutes=15)),
                _answered("question", timedelta(hours=1, minutes=30)),
                _unanswered("send_back"),
            ],
            "2 questions answered (question 1, round_cap 1), 1.8 h waited",
            id="causes-in-blocked-order-half-up-unanswered-left-out",
        ),
        pytest.param(
            [_answered("question", timedelta(minutes=2, seconds=24))],
            "1 questions answered (question 1), 0.0 h waited",
            id="0.04-h-rounds-down",
        ),
        pytest.param(
            [_answered("question", timedelta(minutes=3))],
            "1 questions answered (question 1), 0.1 h waited",
            id="0.05-h-rounds-up",
        ),
        pytest.param(
            [_unanswered("question"), _unanswered("crash_cap")],
            "0 questions answered, 0.0 h waited",
            id="only-unanswered",
        ),
    ],
)
def test_the_human_line_counts_the_answered_waits_by_cause_and_their_hours(
    waits: list[HumanWait], expected: str
) -> None:
    assert human_line(waits) == expected


@pytest.mark.parametrize(
    ("human", "expected"),
    [
        pytest.param(None, "Cost of this work item so far\n\nT", id="without-human"),
        pytest.param(
            "0 questions answered, 0.0 h waited",
            "Cost of this work item so far\n\nT\n\nHuman: 0 questions answered, 0.0 h waited",
            id="with-human",
        ),
    ],
)
def test_the_cost_table_post_ends_with_the_human_line_when_given(
    human: str | None, expected: str
) -> None:
    if human is None:
        assert cost_table_post("T") == expected
    else:
        assert cost_table_post("T", human=human) == expected
