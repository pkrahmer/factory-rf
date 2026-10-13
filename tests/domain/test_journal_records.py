"""The journal's records in the front matter: speaker and kind kept as data."""

from typing import get_args

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.journal import FACTORY, HUMAN, JournalKind, JournalRecord

KINDS = [
    "created",
    "started",
    "result",
    "question",
    "comment",
    "close",
    "stall",
    "crash",
    "expiry",
    "move_back",
    "send_back",
    "done",
]


def test_the_journal_has_twelve_kinds() -> None:
    assert sorted(get_args(JournalKind)) == sorted(KINDS)


@pytest.mark.parametrize("kind", KINDS)
def test_a_record_accepts_each_kind(kind: str) -> None:
    model: type[BaseModel] = JournalRecord

    assert model(number=1, speaker="factory", kind=kind).model_dump()["kind"] == kind


@pytest.mark.parametrize("kind", ["comment_copied", ""])
def test_a_record_refuses_an_unknown_kind(kind: str) -> None:
    model: type[BaseModel] = JournalRecord

    with pytest.raises(ValidationError):
        model(number=1, speaker="factory", kind=kind)


def test_a_record_needs_a_positive_number_and_a_named_speaker() -> None:
    with pytest.raises(ValidationError):
        JournalRecord(number=0, speaker="factory", kind="result")
    with pytest.raises(ValidationError):
        JournalRecord(number=1, speaker="Human", kind="result")


def test_the_two_fixed_speakers() -> None:
    assert HUMAN == "human"
    assert FACTORY == "factory"
