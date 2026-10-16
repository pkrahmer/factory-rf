"""The texts the shipped agent bodies carry after their two sentences."""

import re

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.sections import section_text
from shipped_agents import ROOT, SHIPPED_AGENTS, SHIPPED_NAMES, ShippedAgent, front_matter_and_body

_WITHOUT_ROLE = {"intake", "smoke-tester"}

_FIRST_LESSON = (
    "- Run `make check` and every other make target in the foreground and read its output. "
    "Never start one in the background, and never wait for a process with `pgrep -f`: it "
    "matches its own command line, so the wait never ends."
)

LESSONS = {
    "intake": [
        _FIRST_LESSON,
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
        "- Every stated limit is tested on both sides, also when no criterion spells out the "
        "refused side. The sides of one rule are rows of one parametrized test, not separate "
        "test functions, and setup that several tests share is a fixture.",
        "- The test data you build (a work item text, a state, a pipeline definition, a push) is "
        "valid under the readers and validators already built, unless the test is about that "
        "rule.",
        "- You change a test another story wrote only when the story names that test and the "
        "human has given their word; you make that change, the coder never does.",
    ],
    "coder": [
        _FIRST_LESSON,
        "- Before you write a helper, search the code for one that does the same, and reuse or "
        "extend it; the reviewer counts a second copy of an existing helper as a finding.",
        "- You never change a test, not even one the story names as changed with the human's "
        "word: the tester makes that change.",
    ],
    "reviewer": [
        _FIRST_LESSON,
        "- Count a second copy of an existing helper as a finding, and name the helper it copies.",
        "- Count as a finding a stated limit tested on one side only, and the sides of one rule "
        "written as separate test functions instead of rows of one parametrized test.",
    ],
    "documenter": [
        _FIRST_LESSON,
        "- The project guide is an index plus one file for each domain, each well under the "
        "2,000 lines the file tool reads by default; split a file before it grows past that.",
    ],
    "smoke-tester": [_FIRST_LESSON],
    "acceptance-reviewer": [_FIRST_LESSON],
}

ROLE_AND_STAGE_ANCHORS = {
    "intake": ["Check that the story is buildable before anyone spends tokens on it."],
    "tester": ["You write tests, not code.", "Run `make test 2>&1 | tail -5` once"],
    "coder": ["You make the failing tests pass without changing them", "Refactor, once."],
    "reviewer": [
        "You review a diff against a work item.",
        "You do not edit code, and you do not write any",
    ],
    "documenter": [
        "You write for the reader who was not there",
        "Run every example you wrote or changed.",
    ],
    "smoke-tester": [
        "You run the smoke test, record what happened and judge it against the work item. "
        "You do not fix anything."
    ],
    "acceptance-reviewer": ["You judge and you propose; you build nothing.", "Do the eight checks"],
}

_BANNED_WORDS = re.compile(
    r"\b(ticket|lane|gate|demo|acceptor|verdict|outcomes?|drafts|ongoing|promote|max_rounds"
    r"|stages\.yml)\b",
    re.IGNORECASE,
)


def _body(name: str) -> str:
    _, body = front_matter_and_body(name)
    return body


def _headings(body: str) -> list[str]:
    return re.findall(r"^## .*$", body, re.MULTILINE)


def _decisions(role: str) -> list[str]:
    text = (ROOT / "template" / "factory" / "pipeline.yml").read_text(encoding="utf-8")
    definition = RuamelPipelineDefinitionReader().parse(text)
    stages = [stage for stage in definition.stages.values() if stage.role == role]
    assert len(stages) == 1
    return [*stages[0].next, "question"]


@pytest.mark.parametrize("agent", SHIPPED_AGENTS, ids=SHIPPED_NAMES)
def test_body_still_opens_with_the_boundary_and_the_entry_sentence(agent: ShippedAgent) -> None:
    body = _body(agent.name)

    assert body.startswith(f"{agent.boundary}\n\n{agent.entry}\n")


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_body_has_rules_role_stage_and_lessons_sections_in_order(name: str) -> None:
    expected = ["## Rules", "## Stage", "## Lessons"]
    if name not in _WITHOUT_ROLE:
        expected.insert(1, "## Role")

    assert _headings(_body(name)) == expected


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_body_never_says_stuck(name: str) -> None:
    assert re.findall(r"\bstuck\b", _body(name), re.IGNORECASE) == []


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_body_uses_no_word_the_rename_table_replaces(name: str) -> None:
    body = _body(name)

    assert _BANNED_WORDS.findall(body) == []
    assert "Assignment" not in body
    assert "(append only)" not in body


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_body_names_every_decision_of_its_stage_in_inline_code(name: str) -> None:
    body = _body(name)

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
    assert anchor in (section_text(_body(name), "Rules") or "")


@pytest.mark.parametrize(
    "anchor",
    [
        "The factory commits, pushes and moves the work item.",
        "You never push, check out, switch, merge, pull or call `gh`.",
    ],
)
@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_rules_section_leaves_commit_push_and_move_to_the_factory(name: str, anchor: str) -> None:
    assert anchor in (section_text(_body(name), "Rules") or "")


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_role_and_stage_sections_carry_the_texts_of_the_role(name: str) -> None:
    body = _body(name)
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
    assert phrase in _body("acceptance-reviewer")


def test_acceptance_reviewer_writes_proposed_stories_into_the_backlog() -> None:
    assert "Write the proposed stories into the feature's `backlog/`." in _body(
        "acceptance-reviewer"
    )


@pytest.mark.parametrize(
    "phrase",
    ["compare the output with its `Expect:` line", "its trimmed output in a fenced block"],
)
def test_smoke_tester_compares_with_expect_and_records_trimmed_output(phrase: str) -> None:
    assert phrase in _body("smoke-tester")


@pytest.mark.parametrize(
    "phrase",
    [
        "A test that cannot pass against the work item",
        "end with `tests` and an entry naming the test and the change",
    ],
)
def test_coder_sends_a_wrong_test_back_to_the_tester(phrase: str) -> None:
    assert phrase in _body("coder")


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_lessons_section_is_last_and_holds_exactly_the_role_bullets(name: str) -> None:
    body = _body(name)
    lines = [line for line in (section_text(body, "Lessons") or "").splitlines() if line.strip()]

    assert _headings(body)[-1:] == ["## Lessons"]
    assert lines == LESSONS[name]
