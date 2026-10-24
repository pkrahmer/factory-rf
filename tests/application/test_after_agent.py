"""After the agent: the branch tested, unkept results stalled, undone, the entry, the form."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from definition_support import pipeline_definition
from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.opening import WorkItemOpening
from factory.application.stage import AfterAgent, AgentAftermath, LaunchedStage, StageLauncher
from factory.application.stalls import StallResult
from factory.application.task import StoryFormChecker
from factory.domain.agent_runs import (
    QUESTION,
    AgentRunRequest,
    AgentRunResult,
    EndReason,
    PermissionDenial,
)
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord, entry_text
from factory.domain.paths import cost_records_path
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState
from git_support import install_agents
from human_clone import HumanClone
from observing_runtime import ObservingRuntime
from stage_run_support import ENVIRONMENT, INSTANCE, pushed, pushed_state
from take_support import AGENT_TEXT

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
ELSEWHERE = "elsewhere"
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
ROLES = ["tester", "reviewer"]
OUTSIDE = "src/b.py"
ENTRY = "tests written."
UNDONE_PARAGRAPH = "The factory undid changes outside the write paths: "
CRITERIA_SECTION = """\
## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

"""
SMOKE_TEST_SECTION = """\
## Smoke test

```bash
true
```
Expect: nothing.

"""
STORY = f"""\
# First story

## Description

Text.

## Interface

None.

{CRITERIA_SECTION}{SMOKE_TEST_SECTION}## Journal
"""
WITHOUT_SMOKE_TEST = STORY.replace(SMOKE_TEST_SECTION, "")
WITHOUT_INTERFACE = STORY.replace("## Interface\n\nNone.\n\n", "")
WITHOUT_EXPECT = STORY.replace("```\nExpect: nothing.\n", "```\n")
CREATED = JournalRecord(number=1, speaker="human", kind="created")
CREATED_LINE = "\n1. 2026-10-12 human: created.\n"


class SwitchingRuntime(ObservingRuntime):
    """Leaves the checkout on another branch, then lets the delegate play the scripted run."""

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Switch to `ELSEWHERE`, then play."""
        self._checkout.checkout(ELSEWHERE, start_point="HEAD")
        return super().run(request)


def _completed(decision: str = "doing", entry: str = ENTRY) -> AgentRunResult:
    return AgentRunResult(
        end_reason="completed", decision=decision, entry=entry, duration=timedelta(minutes=1)
    )


def _rendered(boundaries: Boundaries, body: str, stage: str) -> str:
    """The work item file as the agent writes it: `body` under a state the agent chose."""
    document = WorkItemDocument(
        state=WorkItemState(stage=stage, journal=[CREATED]), body=body + CREATED_LINE
    )
    return boundaries.work_item_writer.render(document)


def _launch(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    run: ScriptedRun,
    stage: str = "tests",
    body: str = STORY,
    switching: tuple[Path, FakeHostingService] | None = None,
) -> LaunchedStage:
    """Open the work item at `stage` with `body` and launch the stage with `run` queued."""
    install_agents(agent_home, ROLES)
    human.push_file("main", BACKLOG_PATH, body)
    human.start(BACKLOG_PATH)
    document = WorkItemDocument(
        state=WorkItemState(stage=stage, journal=[CREATED]), body=body + CREATED_LINE
    )
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    boundaries.git.fetch()
    definition = pipeline_definition(boundaries)
    prepared = WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)
    agent_runtime.queue(run)
    used = boundaries
    if switching is not None:
        remote, hosting = switching
        runtime = SwitchingRuntime(
            agent_runtime, remote=remote, branch=BRANCH, hosting=hosting, checkout=boundaries.git
        )
        used = replace(boundaries, agent_runtime=runtime)
    return StageLauncher(used, INSTANCE, definition, ENVIRONMENT).launch(prepared)


def _process(boundaries: Boundaries, launched: LaunchedStage) -> AgentAftermath | StallResult:
    return AfterAgent(boundaries, INSTANCE, pipeline_definition(boundaries)).process(launched)


def _aftermath(boundaries: Boundaries, launched: LaunchedStage) -> AgentAftermath:
    processed = _process(boundaries, launched)
    assert isinstance(processed, AgentAftermath)
    return processed


def _stalled(boundaries: Boundaries, launched: LaunchedStage) -> StallResult:
    processed = _process(boundaries, launched)
    assert isinstance(processed, StallResult)
    return processed


def _note(hosting: FakeHostingService, stalled: StallResult) -> str:
    [post] = hosting.factory_posts(stalled.pull_request)
    return post.body


def _started_attempts(launched: LaunchedStage) -> int:
    state = launched.started.document.state
    assert state is not None
    return state.attempts


def test_a_completed_run_with_an_allowed_decision_gives_its_aftermath(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed("doing")),
    )

    aftermath = _aftermath(boundaries, launched)

    assert aftermath.decision == "doing"
    assert aftermath.result == launched.result
    assert aftermath.started == launched.started
    assert aftermath.request == launched.request


def test_a_checkout_left_on_another_branch_stalls_as_left_branch(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed("doing")),
        switching=(remote, hosting),
    )

    stalled = _stalled(boundaries, launched)

    assert stalled.reason == "left_branch"


@pytest.mark.parametrize("end_reason", ["died", "time_limit", "budget", "no_result"])
def test_a_run_that_did_not_complete_stalls_with_its_reason_and_one_attempt_more(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    end_reason: EndReason,
) -> None:
    result = AgentRunResult(end_reason=end_reason, duration=timedelta(minutes=3))
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=result),
    )

    stalled = _stalled(boundaries, launched)

    assert stalled.reason == end_reason
    assert stalled.attempts == _started_attempts(launched) + 1
    assert pushed_state(boundaries, remote).attempts == _started_attempts(launched) + 1


@pytest.mark.parametrize(
    "denials",
    [
        [PermissionDenial(tool="Bash", detail="git push origin main")],
        [
            PermissionDenial(tool="Bash", detail="git push origin main"),
            PermissionDenial(tool="Edit", detail="src/a.py"),
        ],
    ],
    ids=["one", "two"],
)
def test_the_stall_note_names_the_first_permission_denial(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    denials: list[PermissionDenial],
) -> None:
    result = AgentRunResult(
        end_reason="died", duration=timedelta(minutes=3), permission_denials=denials
    )
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=result),
    )

    stalled = _stalled(boundaries, launched)

    note = _note(hosting, stalled)
    assert stalled.reason == "died"
    assert "denied: Bash: git push origin main" in note
    assert "Edit" not in note
    assert "src/a.py" not in note


def test_a_decision_that_is_not_allowed_stalls_naming_it_and_the_allowed_ones(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed("review")),
    )

    stalled = _stalled(boundaries, launched)

    assert stalled.reason == "decision_not_allowed"
    document = pushed(boundaries, remote)
    state = document.state
    assert state is not None
    assert (state.journal[-1].speaker, state.journal[-1].kind) == ("factory", "stall")
    allowed = ", ".join(launched.request.allowed_decisions)
    assert "doing" in launched.request.allowed_decisions
    text = entry_text(document, state.journal[-1].number)
    assert f"decision 'review' is not one of {allowed}" in text


def test_a_file_written_outside_the_write_paths_is_undone_and_reported(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(writes={OUTSIDE: AGENT_TEXT}, result=_completed()),
    )

    aftermath = _aftermath(boundaries, launched)

    assert not (boundaries.checkout / OUTSIDE).exists()
    assert OUTSIDE in aftermath.take.left


def test_the_agents_state_and_journal_edits_give_way_to_the_stage_start(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    claim = Claim(
        instance="factory-2",
        stage="doing",
        started_at=datetime(2026, 10, 1, tzinfo=UTC),
        lease_duration=5,
    )
    rewritten = WorkItemDocument(
        state=WorkItemState(
            stage="doing",
            attempts=1,
            claim=claim,
            journal=[CREATED, JournalRecord(number=2, speaker="reviewer", kind="result")],
        ),
        body=STORY + CREATED_LINE + "2. reviewer: rewrote the journal.\n",
    )
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(
            writes={PATH: boundaries.work_item_writer.render(rewritten)}, result=_completed()
        ),
        stage="review",
    )

    aftermath = _aftermath(boundaries, launched)

    started_state = launched.started.document.state
    assert started_state is not None
    assert started_state.claim is not None
    assert aftermath.document.state == started_state
    assert "rewrote the journal" not in aftermath.document.body


@pytest.mark.parametrize(("stage", "kept"), [("review", True), ("tests", False)])
def test_a_body_edit_is_kept_only_where_the_role_may_write_the_work_item(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    stage: str,
    kept: bool,
) -> None:
    paragraph = "A paragraph the agent added."
    edited = STORY.replace("Text.\n", f"Text.\n\n{paragraph}\n")
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(writes={PATH: _rendered(boundaries, edited, stage)}, result=_completed()),
        stage=stage,
    )

    aftermath = _aftermath(boundaries, launched)

    on_disk = (boundaries.checkout / PATH).read_text(encoding="utf-8")
    assert (paragraph in aftermath.document.body) is kept
    assert (paragraph in on_disk) is kept
    assert (PATH in aftermath.take.left) is not kept


def test_the_entry_is_the_roles_result_with_the_agents_text(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed("doing")),
    )

    aftermath = _aftermath(boundaries, launched)

    assert aftermath.entry.speaker == "tester"
    assert aftermath.entry.kind == "result"
    assert aftermath.entry.text == ENTRY
    assert aftermath.entry.on is None


def test_a_question_gives_a_question_entry_spoken_by_the_role(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed(QUESTION, "Which one, a or b?")),
    )

    aftermath = _aftermath(boundaries, launched)

    assert aftermath.decision == QUESTION
    assert aftermath.entry.speaker == "tester"
    assert aftermath.entry.kind == "question"
    assert aftermath.entry.text == "Which one, a or b?"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("tester: wrote tests", "wrote tests"),
        ("tests:   wrote tests", "wrote tests"),
        ("wrote tests for tester: all", "wrote tests for tester: all"),
        ("tester wrote tests", "tester wrote tests"),
    ],
    ids=["role", "stage", "in-the-middle", "without-colon"],
)
def test_the_entry_loses_a_leading_role_or_stage_name(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    text: str,
    expected: str,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed("doing", text)),
    )

    aftermath = _aftermath(boundaries, launched)

    assert aftermath.entry.text == expected


@pytest.mark.parametrize(
    ("writes", "paragraph"),
    [
        ({}, None),
        ({OUTSIDE: AGENT_TEXT, "README.md": AGENT_TEXT}, "README.md, src/b.py"),
    ],
    ids=["nothing-undone", "two-undone"],
)
def test_undone_paths_are_named_in_a_last_paragraph_of_the_entry(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    writes: dict[str, str],
    paragraph: str | None,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(writes=writes, result=_completed()),
    )

    aftermath = _aftermath(boundaries, launched)

    if paragraph is None:
        assert aftermath.entry.text == ENTRY
    else:
        assert aftermath.entry.text == f"{ENTRY}\n\n{UNDONE_PARAGRAPH}{paragraph}."


def test_an_entry_blank_after_the_prefix_stalls_as_no_result(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed("doing", "tester: ")),
    )

    stalled = _stalled(boundaries, launched)

    assert stalled.reason == "no_result"
    assert "the entry is empty" in _note(hosting, stalled)


def test_a_broken_form_stalls_with_the_agents_entry_right_above_the_stall(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    broken = STORY.replace(CRITERIA_SECTION, "")
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(
            writes={PATH: _rendered(boundaries, broken, "review")}, result=_completed()
        ),
        stage="review",
    )

    stalled = _stalled(boundaries, launched)

    assert stalled.reason == "form_invalid"
    state = pushed_state(boundaries, remote)
    records = [(record.speaker, record.kind) for record in state.journal[-2:]]
    assert records == [("reviewer", "result"), ("factory", "stall")]
    assert state.attempts == _started_attempts(launched) + 1


def test_a_finding_present_before_and_after_the_run_does_not_stall(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed()),
        body=WITHOUT_SMOKE_TEST,
    )

    aftermath = _aftermath(boundaries, launched)

    assert launched.started.findings != []
    assert aftermath.form_findings == launched.started.findings


def test_a_finding_the_agent_fixed_does_not_stall(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    fixed = WITHOUT_SMOKE_TEST.replace("## Journal\n", SMOKE_TEST_SECTION + "## Journal\n")
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(writes={PATH: _rendered(boundaries, fixed, "review")}, result=_completed()),
        stage="review",
        body=WITHOUT_SMOKE_TEST,
    )

    aftermath = _aftermath(boundaries, launched)

    assert launched.started.findings != []
    assert aftermath.form_findings == []


def test_a_finding_whose_line_number_moved_does_not_stall(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    moved = WITHOUT_EXPECT.replace("Text.\n", "Text.\n\nA paragraph the agent added.\n")
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(writes={PATH: _rendered(boundaries, moved, "review")}, result=_completed()),
        stage="review",
        body=WITHOUT_EXPECT,
    )

    aftermath = _aftermath(boundaries, launched)

    [before] = launched.started.findings
    [after] = aftermath.form_findings
    assert before.message != after.message


def test_a_second_finding_of_the_same_kind_stalls(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
) -> None:
    block = "```bash\ntrue\n```\n"
    doubled = WITHOUT_EXPECT.replace(block, f"{block}\n```bash\nfalse\n```\n")
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(
            writes={PATH: _rendered(boundaries, doubled, "review")}, result=_completed()
        ),
        stage="review",
        body=WITHOUT_EXPECT,
    )

    stalled = _stalled(boundaries, launched)

    note = _note(hosting, stalled)
    [original] = launched.started.findings
    assert original.line is not None
    # The added block opens four lines below the original one.
    added = original.message.replace(f"line {original.line}", f"line {original.line + 4}")
    assert stalled.reason == "form_invalid"
    assert added in note
    assert original.message not in note


def test_the_form_stall_note_joins_only_the_new_findings(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
) -> None:
    broken = WITHOUT_INTERFACE.replace(CRITERIA_SECTION, "").replace(SMOKE_TEST_SECTION, "")
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(
            writes={PATH: _rendered(boundaries, broken, "review")}, result=_completed()
        ),
        stage="review",
        body=WITHOUT_INTERFACE,
    )

    stalled = _stalled(boundaries, launched)

    note = _note(hosting, stalled)
    [old] = launched.started.findings
    assert stalled.reason == "form_invalid"
    assert "missing section: ## Acceptance criteria; missing section: ## Smoke test" in note
    assert old.message not in note


@pytest.mark.parametrize(
    ("body", "clean"),
    [(STORY, True), (WITHOUT_INTERFACE, False)],
    ids=["clean", "with-a-finding"],
)
def test_the_aftermath_lists_every_finding_after_the_run(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    body: str,
    clean: bool,
) -> None:
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(result=_completed()),
        body=body,
    )

    aftermath = _aftermath(boundaries, launched)

    assert aftermath.form_findings == StoryFormChecker(boundaries).findings(aftermath.document)
    assert (aftermath.form_findings == []) is clean


@pytest.mark.parametrize(
    ("outside", "paragraph"),
    [(True, f"{UNDONE_PARAGRAPH}{OUTSIDE}."), (False, None)],
    ids=["with-an-outside-file", "only-the-sidecar"],
)
def test_the_own_cost_record_file_is_not_named_as_undone(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    outside: bool,
    paragraph: str | None,
) -> None:
    sidecar = cost_records_path(PATH)
    writes = {sidecar: "overwritten by the agent\n"}
    if outside:
        writes[OUTSIDE] = AGENT_TEXT
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(writes=writes, result=_completed()),
    )

    aftermath = _aftermath(boundaries, launched)

    assert sidecar not in aftermath.entry.text
    if paragraph is None:
        assert aftermath.entry.text == ENTRY
    else:
        assert aftermath.entry.text == f"{ENTRY}\n\n{paragraph}"


def test_a_new_form_finding_stamps_the_entry_and_the_stall_with_the_launched_run(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    clock: ManualClock,
) -> None:
    broken = STORY.replace(CRITERIA_SECTION, "")
    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(
            writes={PATH: _rendered(boundaries, broken, "review")}, result=_completed()
        ),
        stage="review",
    )

    stalled = _stalled(boundaries, launched)

    assert stalled.reason == "form_invalid"
    state = pushed_state(boundaries, remote)
    stamps = [(record.kind, record.at, record.stage, record.run) for record in state.journal]
    assert stamps[-2:] == [
        ("result", clock.now(), "review", launched.cost.run),
        ("stall", clock.now(), "review", launched.cost.run),
    ]
