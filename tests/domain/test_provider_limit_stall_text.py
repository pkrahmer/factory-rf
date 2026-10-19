"""The stall of a run ended by a provider's spend limit: its sentence and its journal record."""

from factory.domain import decisions, journal
from factory.domain.journal import FACTORY, JournalRecord
from factory.domain.post_texts import stall_cause, stall_note
from factory.domain.work_item import WorkItemState, initial_state

SENTENCE = "the provider's spend limit lasted past the waiting ceiling"


def test_the_provider_limit_stall_has_its_sentence_and_note() -> None:
    assert stall_cause("provider_limit") == SENTENCE
    assert stall_note("provider_limit", 1, 2) == (
        f"Stalled (attempt 1 of 2): {SENTENCE}. Retrying on the next tick."
    )


def test_a_provider_limit_stall_record_round_trips_through_the_work_item_state() -> None:
    record = JournalRecord(number=2, speaker=FACTORY, kind="stall", reason="provider_limit")
    created = JournalRecord(number=1, speaker="human", kind="created")
    state = initial_state("doing").model_copy(update={"journal": [created, record]})

    read = WorkItemState.model_validate_json(state.model_dump_json())

    assert read == state
    assert read.journal[-1].reason == "provider_limit"


def test_the_decisions_stall_reason_is_the_journals_type() -> None:
    assert decisions.StallReason is journal.StallReason
