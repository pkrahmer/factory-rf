"""The texts the shipped agent bodies carry after their two sentences."""

import re

import pytest

from factory.domain.sections import section_text
from shipped_agents import (
    SHIPPED_AGENTS,
    SHIPPED_NAMES,
    ShippedAgent,
    agent_body,
    template_definition,
)

_WITHOUT_ROLE = {"intake", "smoke-tester"}

_FIRST_LESSON = (
    "- Run `make check` and every other make target in the foreground and read its output. "
    "Never start one in the background, and never wait for a process with `pgrep -f`: it "
    "matches its own command line, so the wait never ends."
)

_SECOND_LESSON = (
    "- Give a project command that can take minutes, such as `make check`, the shell tool's "
    "largest timeout (600000 ms), so that the tool does not move it to the background."
)

_TEMPORARY_DIRECTORY_LESSON = (
    "- Make every file you need outside the repository in a temporary directory that removes "
    "itself: `tempfile.TemporaryDirectory()` in Python, or `d=$(mktemp -d)` followed by "
    "`trap 'rm -rf \"$d\"' EXIT` in the shell. Leave nothing behind in `/tmp` when you end."
)

_TIME_LIMIT_LESSON = (
    "- A test that waits for a time limit gives the process it starts room to start: the tests "
    "may run on every core at once, so a child can need more than a second before it does "
    "anything. Give it a limit of a few seconds and an upper bound on the elapsed time with "
    "room above it; never check that a one-second limit is met to the tenth."
)

LESSONS = {
    "intake": [
        _FIRST_LESSON,
        _SECOND_LESSON,
        "- Every clause of an Interface rule has its own criterion, on both sides: an ordering, "
        'the second branch of an "or", a "when longer than", the value for every kind an enum '
        "names, an exact value beyond its first part. A clause without one is a question.",
        "- Every behaviour that the Description, the Interface or a decision of the feature "
        "states has its own criterion; one without is a question.",
        "- A story that changes a test another story wrote names that test and has the human's "
        "word; one that does not is a question.",
    ],
    "tester": [
        _FIRST_LESSON,
        _SECOND_LESSON,
        "- Every stated limit is tested on both sides, also when no criterion spells out the "
        "refused side. The sides of one rule are rows of one parametrized test, not separate "
        "test functions, and setup that several tests share is a fixture.",
        "- The test data you build (a work item text, a state, a pipeline definition, a push) is "
        "valid under the readers and validators already built, unless the test is about that "
        "rule.",
        "- You change a test another story wrote only when the story names that test and the "
        "human has given their word, or to move a shared test helper under a standing leave "
        "that `CLAUDE.md` gives; you make that change, the coder never does, and your entry "
        "names each earlier test file you changed and the leave for it.",
        "- When the prompt says `Mode: a test change the human approved` and the coder's entry "
        "names a move of a shared test helper under that standing leave instead of an answer of "
        "the human's, make exactly that move, as step 0 of the stage says for an approved change.",
        _TIME_LIMIT_LESSON,
    ],
    "coder": [
        _FIRST_LESSON,
        _SECOND_LESSON,
        "- Before you write a helper, search the code for one that does the same, and reuse or "
        "extend it; the reviewer counts a second copy of an existing helper as a finding.",
        "- You never change a test, not even one the story names as changed with the human's "
        "word: the tester makes that change.",
        "- A reviewer's finding of a copied test helper is a change to tests: when `CLAUDE.md` "
        "gives a standing leave to move a shared test helper, end with `tests` and an entry "
        "naming the move (the helper, the shared place, the earlier test files), and the tester "
        "makes it; without that leave, it is a question.",
    ],
    "reviewer": [
        _FIRST_LESSON,
        _SECOND_LESSON,
        "- Count a second copy of an existing helper as a finding, and name the helper it copies.",
        "- Count as a finding a stated limit tested on one side only, and the sides of one rule "
        "written as separate test functions instead of rows of one parametrized test.",
    ],
    "documenter": [
        _FIRST_LESSON,
        _SECOND_LESSON,
        "- The project guide is an index plus one file for each domain, each well under the "
        "2,000 lines the file tool reads by default; split a file before it grows past that.",
        _TEMPORARY_DIRECTORY_LESSON,
        "- When every file you changed is a document (`README.md` or a file under `docs/`), end "
        "without running `make check`, in place of step 3 of the stage: the factory runs the "
        "stage's checks right after you, and that run decides. When you changed any other file, "
        "run it as step 3 says.",
    ],
    "smoke-tester": [_FIRST_LESSON, _SECOND_LESSON, _TEMPORARY_DIRECTORY_LESSON],
    "acceptance-reviewer": [
        _FIRST_LESSON,
        _SECOND_LESSON,
        _TEMPORARY_DIRECTORY_LESSON,
        "- When `make test` writes a JUnit report (the `--junit-xml` file its `Makefile` names), "
        "read the time of each test from it, and name the slowest tests in the slow checks and "
        "in the cost.",
    ],
}

ROLE_AND_STAGE_ANCHORS = {
    "intake": ["Check that the story is buildable before anyone spends tokens on it."],
    "tester": ["You write tests, not code.", "Run `make test 2>&1 | tail -5` once"],
    "coder": ["You make the failing tests pass without changing them", "Refactor, once."],
    "reviewer": [
        "You review a diff against a work item.",
        "You do not edit code, and you do not write any",
        "Item 6 is part of every review, whichever group failed.",
        "6. **Earlier tests**: every test file that `main` already holds",
    ],
    "documenter": [
        "You write for the reader who was not there",
        "Run every example you wrote or changed.",
    ],
    "smoke-tester": [
        "You run the smoke test, record what happened and judge it against the work item. "
        "You do not fix anything."
    ],
    "acceptance-reviewer": [
        "You judge and you propose; you build nothing.",
        "Do the eight checks",
        "Add the earlier tests the reviewers' entries name as changed",
    ],
}

_BANNED_WORDS = re.compile(
    r"\b(ticket|lane|gate|demo|acceptor|verdict|outcomes?|drafts|ongoing|promote|max_rounds"
    r"|stages\.yml)\b",
    re.IGNORECASE,
)


def _headings(body: str) -> list[str]:
    return re.findall(r"^## .*$", body, re.MULTILINE)


def _decisions(role: str) -> list[str]:
    definition = template_definition()
    stages = [stage for stage in definition.stages.values() if stage.role == role]
    assert len(stages) == 1
    return [*stages[0].next, "question"]


@pytest.mark.parametrize("agent", SHIPPED_AGENTS, ids=SHIPPED_NAMES)
def test_body_still_opens_with_the_boundary_and_the_entry_sentence(agent: ShippedAgent) -> None:
    body = agent_body(agent.name)

    assert body.startswith(f"{agent.boundary}\n\n{agent.entry}\n")


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_body_has_rules_role_stage_and_lessons_sections_in_order(name: str) -> None:
    expected = ["## Rules", "## Stage", "## Lessons"]
    if name not in _WITHOUT_ROLE:
        expected.insert(1, "## Role")

    assert _headings(agent_body(name)) == expected


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_body_never_says_stuck(name: str) -> None:
    assert re.findall(r"\bstuck\b", agent_body(name), re.IGNORECASE) == []


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_body_uses_no_word_the_rename_table_replaces(name: str) -> None:
    body = agent_body(name)

    assert _BANNED_WORDS.findall(body) == []
    assert "Assignment" not in body
    assert "(append only)" not in body


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_body_names_every_decision_of_its_stage_in_inline_code(name: str) -> None:
    body = agent_body(name)

    missing = [decision for decision in _decisions(name) if f"`{decision}`" not in body]

    assert missing == []


@pytest.mark.parametrize(
    "anchor",
    [
        "Git is the only truth.",
        "To ask the human, end with `question`",
        "one of the `Allowed decisions` your prompt lists",
    ],
)
@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_rules_section_carries_the_pipeline_rules_with_the_decision_contract(
    name: str, anchor: str
) -> None:
    assert anchor in (section_text(agent_body(name), "Rules") or "")


@pytest.mark.parametrize(
    "anchor",
    [
        "The factory commits, pushes and moves the work item.",
        "You never push, check out, switch, merge, pull or call `gh`.",
    ],
)
@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_rules_section_leaves_commit_push_and_move_to_the_factory(name: str, anchor: str) -> None:
    assert anchor in (section_text(agent_body(name), "Rules") or "")


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_role_and_stage_sections_carry_the_texts_of_the_role(name: str) -> None:
    body = agent_body(name)
    text = (section_text(body, "Role") or "") + (section_text(body, "Stage") or "")

    missing = [anchor for anchor in ROLE_AND_STAGE_ANCHORS[name] if anchor not in text]

    assert missing == []


@pytest.mark.parametrize(
    "phrase",
    [
        "## Recommendation",
        "## Proposed stories",
        "accepted",
        "accepted with stories",
        "not accepted",
    ],
)
def test_acceptance_reviewer_names_the_report_sections_and_recommendations(phrase: str) -> None:
    assert phrase in agent_body("acceptance-reviewer")


def test_acceptance_reviewer_writes_proposed_stories_into_the_backlog() -> None:
    assert "Write the proposed stories into the feature's `backlog/`." in agent_body(
        "acceptance-reviewer"
    )


@pytest.mark.parametrize(
    "phrase",
    ["compare the output with its `Expect:` line", "its trimmed output in a fenced block"],
)
def test_smoke_tester_compares_with_expect_and_records_trimmed_output(phrase: str) -> None:
    assert phrase in agent_body("smoke-tester")


@pytest.mark.parametrize(
    "phrase",
    [
        "A test that cannot pass against the work item",
        "end with `tests` and an entry naming the test and the change",
    ],
)
def test_coder_sends_a_wrong_test_back_to_the_tester(phrase: str) -> None:
    assert phrase in agent_body("coder")


def test_the_reviewer_no_longer_stops_before_the_earlier_tests() -> None:
    assert "Stop at the first failing group and report it" not in agent_body("reviewer")


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_lessons_section_is_last_and_holds_exactly_the_role_bullets(name: str) -> None:
    body = agent_body(name)
    lines = [line for line in (section_text(body, "Lessons") or "").splitlines() if line.strip()]

    assert _headings(body)[-1:] == ["## Lessons"]
    assert lines == LESSONS[name]
