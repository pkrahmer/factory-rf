"""The agent's journal entry: speaker and kind decided by code, its text cleaned and completed."""

import pytest

from factory.domain.agent_runs import QUESTION
from factory.domain.decisions import agent_entry
from factory.domain.journal import NewEntry

ROLE = "tester"
STAGE = "tests"
UNDONE_PARAGRAPH = "The factory undid changes outside the write paths: "


def test_a_result_entry_is_spoken_by_the_role_with_the_agents_text() -> None:
    entry = agent_entry(role=ROLE, stage=STAGE, decision="doing", text="wrote tests", undone=[])

    assert entry == NewEntry(speaker=ROLE, kind="result", text="wrote tests", on=None)


def test_a_question_entry_has_kind_question_and_the_role_as_speaker() -> None:
    entry = agent_entry(role=ROLE, stage=STAGE, decision=QUESTION, text="Which one?", undone=[])

    assert entry == NewEntry(speaker=ROLE, kind="question", text="Which one?", on=None)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("tester: wrote tests", "wrote tests"),
        ("tests: wrote tests", "wrote tests"),
        ("tester:    wrote tests", "wrote tests"),
        ("  tester: wrote tests  ", "wrote tests"),
        ("tester: tester: wrote tests", "tester: wrote tests"),
        ("tester: tests: wrote tests", "tests: wrote tests"),
        ("wrote tests for tester: and tests: alike", "wrote tests for tester: and tests: alike"),
        ("tester wrote tests", "tester wrote tests"),
        ("tests wrote themselves", "tests wrote themselves"),
        ("tester : wrote tests", "tester : wrote tests"),
    ],
    ids=[
        "role",
        "stage",
        "whitespace-after-colon",
        "surrounding-whitespace",
        "role-removed-once",
        "role-before-stage-removed-once",
        "in-the-middle",
        "role-without-colon",
        "stage-without-colon",
        "space-before-colon",
    ],
)
def test_a_leading_role_or_stage_name_is_removed_once(text: str, expected: str) -> None:
    entry = agent_entry(role=ROLE, stage=STAGE, decision="doing", text=text, undone=[])

    assert entry is not None
    assert entry.text == expected


def test_undone_paths_end_the_text_with_a_paragraph_sorted_and_joined() -> None:
    entry = agent_entry(
        role=ROLE,
        stage=STAGE,
        decision="doing",
        text="tester: wrote the tests",
        undone=["src/b.py", "README.md"],
    )

    assert entry is not None
    assert entry.text == f"wrote the tests\n\n{UNDONE_PARAGRAPH}README.md, src/b.py."


def test_nothing_undone_adds_no_paragraph() -> None:
    entry = agent_entry(role=ROLE, stage=STAGE, decision="doing", text="wrote the tests", undone=[])

    assert entry is not None
    assert entry.text == "wrote the tests"
    assert UNDONE_PARAGRAPH not in entry.text


@pytest.mark.parametrize("text", ["", "   ", "tester: ", "tester:   ", "tests:", "\n tests: \n"])
@pytest.mark.parametrize("undone", [[], ["src/b.py"]], ids=["nothing-undone", "undone"])
def test_a_blank_text_after_the_prefix_gives_no_entry(text: str, undone: list[str]) -> None:
    assert agent_entry(role=ROLE, stage=STAGE, decision="doing", text=text, undone=undone) is None
