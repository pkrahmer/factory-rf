"""The work item file of a feature acceptance: its two extra keys read and written."""

import pytest

from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.domain.acceptance import AcceptanceState
from factory.domain.errors import WorkItemFormatError
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState

PLAIN = "round: 1\nattempts: 0\n"
BODY = "# Acceptance of Todo service\n"


def _text(front_matter: str) -> str:
    return f"---\n{front_matter}---\n\n{BODY}"


def _keys(text: str) -> list[str]:
    front_matter = text.split("---\n")[1]
    return [line.split(":")[0] for line in front_matter.splitlines() if line[:1].isalpha()]


def _fault_of_parse(text: str) -> str:
    with pytest.raises(WorkItemFormatError) as caught:
        FrontmatterWorkItemReader().parse(text)
    return caught.value.fault


@pytest.mark.parametrize(
    ("front_matter", "expected"),
    [
        (
            f"stage: done\n{PLAIN}stories: [F0001-S0001, F0001-S0002]\noutcome: refused\n",
            AcceptanceState(
                stage="done", round=1, stories=["F0001-S0001", "F0001-S0002"], outcome="refused"
            ),
        ),
        (
            f"stage: acceptance\n{PLAIN}stories: [F0001-S0001]\n",
            AcceptanceState(stage="acceptance", round=1, stories=["F0001-S0001"]),
        ),
    ],
)
def test_reader_returns_an_acceptance_state_for_either_extra_key(
    front_matter: str, expected: AcceptanceState
) -> None:
    state = FrontmatterWorkItemReader().parse(_text(front_matter)).state

    assert isinstance(state, AcceptanceState)
    assert state == expected


def test_reader_returns_a_plain_state_without_the_extra_keys() -> None:
    state = FrontmatterWorkItemReader().parse(_text(f"stage: doing\n{PLAIN}")).state

    assert isinstance(state, WorkItemState)
    assert not isinstance(state, AcceptanceState)


@pytest.mark.parametrize(
    "front_matter",
    [
        f"stage: doing\n{PLAIN}verdict: fine\n",
        f"stage: acceptance\n{PLAIN}stories: [F0001-S0001]\nverdict: fine\n",
    ],
)
def test_reader_refuses_any_other_unknown_key(front_matter: str) -> None:
    assert "verdict" in _fault_of_parse(_text(front_matter))


@pytest.mark.parametrize(
    ("front_matter", "key"),
    [
        (f"stage: acceptance\n{PLAIN}stories: [F0001-S0002, F0001-S0001]\n", "stories"),
        (f"stage: done\n{PLAIN}outcome: maybe\n", "outcome"),
    ],
)
def test_reader_names_the_extra_key_of_an_invalid_value(front_matter: str, key: str) -> None:
    assert key in _fault_of_parse(_text(front_matter))


def test_writer_puts_stories_and_outcome_last() -> None:
    document = WorkItemDocument(
        state=AcceptanceState(stage="acceptance", stories=["F0001-S0001"]), body=BODY
    )

    text = FrontmatterWorkItemWriter().render(document)

    assert _keys(text) == [*WorkItemState.model_fields, "stories", "outcome"]
    assert "\noutcome: null\n" in text


def test_writer_gives_a_plain_state_neither_extra_key() -> None:
    document = WorkItemDocument(state=WorkItemState(stage="doing"), body=BODY)

    keys = _keys(FrontmatterWorkItemWriter().render(document))

    assert "stories" not in keys
    assert "outcome" not in keys


def test_acceptance_document_survives_a_round_trip() -> None:
    state = AcceptanceState(
        stage="done",
        stories=["F0001-S0001", "F0001-S0002"],
        outcome="accepted",
        journal=[
            JournalRecord(number=1, speaker="factory", kind="created"),
            JournalRecord(number=2, speaker="acceptance", kind="result"),
        ],
    )
    document = WorkItemDocument(state=state, body=BODY)

    reader, writer = FrontmatterWorkItemReader(), FrontmatterWorkItemWriter()

    assert reader.parse(writer.render(document)) == document
