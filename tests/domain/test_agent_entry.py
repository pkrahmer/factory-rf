"""The agent's journal entry: speaker and kind decided by code, its text cleaned and completed."""

import pytest

from factory.domain.agent_runs import QUESTION
from factory.domain.decisions import agent_entry
from factory.domain.journal import NewEntry

ROLE = "tester"
STAGE = "tests"
LEFT_OUT_PARAGRAPH = "The factory left out changes outside the write paths: "


def test_a_result_entry_is_spoken_by_the_role_with_the_agents_text() -> None:
    entry = agent_entry(role=ROLE, stage=STAGE, decision="doing", text="wrote tests", left_out=[])

    assert entry == NewEntry(speaker=ROLE, kind="result", text="wrote tests", on=None)


def test_a_question_entry_has_kind_question_and_the_role_as_speaker() -> None:
    entry = agent_entry(role=ROLE, stage=STAGE, decision=QUESTION, text="Which one?", left_out=[])

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
    entry = agent_entry(role=ROLE, stage=STAGE, decision="doing", text=text, left_out=[])

    assert entry is not None
    assert entry.text == expected


def test_undone_paths_end_the_text_with_a_paragraph_sorted_and_joined() -> None:
    entry = agent_entry(
        role=ROLE,
        stage=STAGE,
        decision="doing",
        text="tester: wrote the tests",
        left_out=["src/b.py", "README.md"],
    )

    assert entry is not None
    assert entry.text == f"wrote the tests\n\n{LEFT_OUT_PARAGRAPH}README.md, src/b.py."


def test_nothing_undone_adds_no_paragraph() -> None:
    entry = agent_entry(
        role=ROLE, stage=STAGE, decision="doing", text="wrote the tests", left_out=[]
    )

    assert entry is not None
    assert entry.text == "wrote the tests"
    assert LEFT_OUT_PARAGRAPH not in entry.text


@pytest.mark.parametrize("text", ["", "   ", "tester: ", "tester:   ", "tests:", "\n tests: \n"])
@pytest.mark.parametrize("left_out", [[], ["src/b.py"]], ids=["nothing-left-out", "left-out"])
def test_a_blank_text_after_the_prefix_gives_no_entry(text: str, left_out: list[str]) -> None:
    assert (
        agent_entry(role=ROLE, stage=STAGE, decision="doing", text=text, left_out=left_out) is None
    )


@pytest.mark.parametrize(
    ("text", "left_out", "expected"),
    [
        pytest.param(
            "tester: done",
            ["b.py", "a.py"],
            "done\n\nThe factory left out changes outside the write paths: a.py, b.py.",
            id="two-paths-sorted",
        ),
        pytest.param("tester: done", [], "done", id="nothing-left-out"),
        pytest.param("tester:   ", ["b.py", "a.py"], None, id="blank-text"),
    ],
)
def test_the_left_out_paths_close_the_entry_in_a_paragraph_of_their_own(
    text: str, left_out: list[str], expected: str | None
) -> None:
    entry = agent_entry(role=ROLE, stage=STAGE, decision="doing", text=text, left_out=left_out)

    assert (None if entry is None else entry.text) == expected
