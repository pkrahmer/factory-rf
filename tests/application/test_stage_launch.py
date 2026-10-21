"""The start of a stage: the claim pushed first, then the pull request, the guard and the run."""

import shutil
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.opening import PreparedWorkItem, WorkItemOpening
from factory.application.stage import LaunchedStage, StageLauncher
from factory.application.task import StoryFormChecker
from factory.application.write_paths import WritePathService
from factory.domain.agent_runs import AgentRunResult, EndReason
from factory.domain.errors import AgentDefinitionMissing, AgentRuntimeError, PushFailed
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState, initial_state
from git_support import PIPELINE_YAML, install_agents, remote_commit
from human_clone import HumanClone
from observing_runtime import ObservingRuntime
from stage_run_support import INSTANCE

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
ROLES = ["intake", "tester", "coder"]
ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}
STORY = """\
# First story

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.

## Journal
"""
WITHOUT_SMOKE_TEST = STORY.replace("## Smoke test\n\n```bash\ntrue\n```\nExpect: nothing.\n\n", "")
BRANCH_BODY = STORY + "\n1. 2026-10-12 human: created.\n"
CREATED = JournalRecord(number=1, speaker="human", kind="created")
STARTED = JournalRecord(number=2, speaker="factory", kind="started")
COMPLETED = AgentRunResult(
    end_reason="completed", decision="doing", entry="tests written.", duration=timedelta(minutes=1)
)


def _start(human: HumanClone, checkout: GitCli, text: str = STORY) -> None:
    """Write the backlog story on `main`, start it and fetch."""
    human.push_file("main", BACKLOG_PATH, text)
    human.start(BACKLOG_PATH)
    checkout.fetch()


def _push_branch(
    boundaries: Boundaries, human: HumanClone, checkout: GitCli, state: WorkItemState
) -> None:
    """Open the work item's branch on the remote with a document in `state`, then fetch."""
    document = WorkItemDocument(state=state, body=BRANCH_BODY)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    checkout.fetch()


def _prepare(boundaries: Boundaries) -> PreparedWorkItem:
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    return WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)


def _observing(
    boundaries: Boundaries,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> ObservingRuntime:
    return ObservingRuntime(
        agent_runtime, remote=remote, branch=BRANCH, hosting=hosting, checkout=boundaries.git
    )


def _launcher(boundaries: Boundaries, runtime: ObservingRuntime | None = None) -> StageLauncher:
    used = boundaries if runtime is None else replace(boundaries, agent_runtime=runtime)
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    return StageLauncher(used, INSTANCE, definition, ENVIRONMENT)


def _document_at(boundaries: Boundaries, commit: str | None) -> WorkItemDocument:
    assert commit is not None
    text = boundaries.git.show_file(commit, PATH)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def _state_at(boundaries: Boundaries, commit: str | None) -> WorkItemState:
    state = _document_at(boundaries, commit).state
    assert state is not None
    return state


def _later_state(stage: str, pull_request: int | None = None) -> WorkItemState:
    return WorkItemState(stage=stage, pull_request=pull_request, journal=[CREATED])


def _launch_new(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> tuple[LaunchedStage, ObservingRuntime]:
    """Start a new work item and launch its first stage with one completed run queued."""
    install_agents(agent_home, ROLES)
    _start(human, checkout)
    prepared = _prepare(boundaries)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    runtime = _observing(boundaries, agent_runtime, remote, hosting)
    return _launcher(boundaries, runtime).launch(prepared), runtime


def test_the_stage_start_commit_is_on_the_remote_when_the_run_starts(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    clock: ManualClock,
) -> None:
    launched, runtime = _launch_new(
        boundaries,
        human=human,
        checkout=checkout,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        remote=remote,
        hosting=hosting,
    )

    [observed] = runtime.observations()
    assert observed.remote_head == launched.started.stage_start.commit
    document = _document_at(boundaries, observed.remote_head)
    state = document.state
    assert state is not None
    assert state.claim is not None
    assert state.claim.instance == INSTANCE
    assert state.claim.stage == "intake"
    assert state.claim.started_at == clock.now()
    assert (state.journal[-1].speaker, state.journal[-1].kind) == ("factory", "started")
    assert launched.started.document == document


def test_the_stage_start_commit_is_one_commit_above_the_existing_branch(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    install_agents(agent_home, ROLES)
    _start(human, checkout)
    _push_branch(boundaries, human, checkout, _later_state("tests"))
    previous = remote_commit(remote, BRANCH)
    assert previous is not None
    prepared = _prepare(boundaries)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    runtime = _observing(boundaries, agent_runtime, remote, hosting)

    launched = _launcher(boundaries, runtime).launch(prepared)

    [observed] = runtime.observations()
    assert observed.remote_head is not None
    commits = checkout.log(observed.remote_head, since=previous)
    assert len(commits) == 1
    assert commits[0].parents == [previous]
    assert launched.started.stage_start.commit == observed.remote_head
    assert launched.started.stage_start.commit == observed.checkout_head


def test_the_stage_start_commit_of_a_new_work_item_is_its_opening_commit(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    clock: ManualClock,
) -> None:
    launched, _ = _launch_new(
        boundaries,
        human=human,
        checkout=checkout,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        remote=remote,
        hosting=hosting,
    )

    commits = checkout.log(f"origin/{BRANCH}", since="origin/main")
    assert len(commits) == 1
    state = _state_at(boundaries, commits[0].commit)
    assert state.claim == launched.started.stage_start.claim
    assert state.model_copy(update={"claim": None, "journal": []}) == initial_state("intake")
    stamp = {"at": clock.now(), "stage": "intake"}
    assert state.journal == [CREATED.model_copy(update=stamp), STARTED.model_copy(update=stamp)]


def test_a_push_by_another_clone_rejects_the_claim_and_no_run_starts(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    install_agents(agent_home, ROLES)
    _start(human, checkout)
    _push_branch(boundaries, human, checkout, _later_state("tests"))
    prepared = _prepare(boundaries)
    human.push_file(BRANCH, "elsewhere.md", "pushed by another clone\n")
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    with pytest.raises(PushFailed) as caught:
        _launcher(boundaries).launch(prepared)

    assert caught.value.outcome == "rejected"
    assert agent_runtime.requests() == []


def test_an_unreachable_remote_fails_the_claim_and_no_run_starts(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    install_agents(agent_home, ROLES)
    _start(human, checkout)
    prepared = _prepare(boundaries)
    shutil.rmtree(remote)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    with pytest.raises(PushFailed) as caught:
        _launcher(boundaries).launch(prepared)

    assert caught.value.outcome == "unreachable"
    assert agent_runtime.requests() == []


@pytest.mark.parametrize("branch_existed", [False, True], ids=["new", "existing"])
def test_a_missing_agent_file_is_raised_before_anything_is_pushed(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    branch_existed: bool,
) -> None:
    install_agents(agent_home, ["coder"])
    _start(human, checkout)
    if branch_existed:
        _push_branch(boundaries, human, checkout, _later_state("tests"))
    previous = remote_commit(remote, BRANCH)
    prepared = _prepare(boundaries)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    with pytest.raises(AgentDefinitionMissing):
        _launcher(boundaries).launch(prepared)

    assert remote_commit(remote, BRANCH) == previous
    assert (previous is None) is not branch_existed
    assert agent_runtime.requests() == []


def test_a_conflicted_work_item_is_refused_before_anything_is_read_or_pushed(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    # No agent is installed: reading the agent definition first would raise another error.
    _start(human, checkout)
    prepared = _prepare(boundaries).model_copy(update={"merge_conflict": True})
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    with pytest.raises(ValueError):
        _launcher(boundaries).launch(prepared)

    assert remote_commit(remote, BRANCH) is None
    assert agent_runtime.requests() == []


def test_a_stage_without_a_role_is_refused_naming_the_stage(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    # No agent is installed: reading the agent definition first would raise another error.
    _start(human, checkout)
    _push_branch(boundaries, human, checkout, _later_state("approval"))
    previous = remote_commit(remote, BRANCH)
    prepared = _prepare(boundaries)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    with pytest.raises(ValueError, match="approval"):
        _launcher(boundaries).launch(prepared)

    assert remote_commit(remote, BRANCH) == previous
    assert agent_runtime.requests() == []


def test_a_new_work_item_has_one_open_draft_when_the_run_starts(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    launched, runtime = _launch_new(
        boundaries,
        human=human,
        checkout=checkout,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        remote=remote,
        hosting=hosting,
    )

    [observed] = runtime.observations()
    drafts = [
        pull
        for pull in observed.pull_requests
        if pull.branch == BRANCH and pull.state == "open" and pull.draft
    ]
    assert len(drafts) == 1
    assert launched.started.pull_request == drafts[0]
    assert _state_at(boundaries, launched.started.stage_start.commit).pull_request is None


def test_a_recorded_open_pull_request_is_kept_and_reused(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
) -> None:
    for number in range(1, 7):
        hosting.create_pull_request(branch_name(f"F0001-S{number + 1:04d}"), "t", "b", draft=True)
    recorded = hosting.create_pull_request(BRANCH, "recorded", "body", draft=False)
    assert recorded.number == 7
    install_agents(agent_home, ROLES)
    _start(human, checkout)
    _push_branch(boundaries, human, checkout, _later_state("tests", pull_request=7))
    prepared = _prepare(boundaries)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    launched = _launcher(boundaries).launch(prepared)

    assert _state_at(boundaries, launched.started.stage_start.commit).pull_request == 7
    assert len(hosting.pull_requests()) == 7
    assert launched.started.pull_request.number == 7


def test_the_runtime_receives_the_request_with_the_guard_and_the_draft_number(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    launched, _ = _launch_new(
        boundaries,
        human=human,
        checkout=checkout,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        remote=remote,
        hosting=hosting,
    )

    [request] = agent_runtime.requests()
    [draft] = hosting.pull_requests()
    assert request == launched.request
    assert request.guard == WritePathService(boundaries).at(launched.started.stage_start, PATH)
    assert f"Pull request: {draft.number}" in request.prompt.split("\n")


def test_the_request_carries_exactly_the_given_environment(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    _launch_new(
        boundaries,
        human=human,
        checkout=checkout,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        remote=remote,
        hosting=hosting,
    )

    [request] = agent_runtime.requests()
    assert request.environment == ENVIRONMENT


@pytest.mark.parametrize(
    ("body", "complete"),
    [(STORY, True), (WITHOUT_SMOKE_TEST, False)],
    ids=["complete", "without-smoke-test"],
)
def test_the_first_stage_prompt_carries_the_form_findings(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    body: str,
    complete: bool,
) -> None:
    install_agents(agent_home, ROLES)
    _start(human, checkout, body)
    prepared = _prepare(boundaries)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    launched = _launcher(boundaries).launch(prepared)

    findings = launched.started.findings
    lines = launched.request.prompt.split("\n")
    if complete:
        assert findings == []
        assert "Format check: passed" in lines
    else:
        assert findings != []
        assert findings == StoryFormChecker(boundaries).findings(prepared.document)
        items = " ".join(f"{n}. {finding.message}" for n, finding in enumerate(findings, start=1))
        assert f"Format check found: {items}" in lines


@pytest.mark.parametrize("end_reason", ["died", "time_limit", "budget"])
def test_a_run_that_did_not_complete_is_returned_as_its_result(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    end_reason: EndReason,
) -> None:
    install_agents(agent_home, ROLES)
    _start(human, checkout)
    prepared = _prepare(boundaries)
    result = AgentRunResult(end_reason=end_reason, duration=timedelta(minutes=3))
    agent_runtime.queue(ScriptedRun(result=result))

    launched = _launcher(boundaries).launch(prepared)

    assert launched.result == result


def test_a_runtime_error_propagates_and_leaves_the_claim_pushed(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    install_agents(agent_home, ROLES)
    _start(human, checkout)
    prepared = _prepare(boundaries)
    runtime = _observing(boundaries, agent_runtime, remote, hosting)

    # Nothing is queued, so the fake runtime raises when it is asked to run.
    with pytest.raises(AgentRuntimeError) as caught:
        _launcher(boundaries, runtime).launch(prepared)

    assert caught.value.detail == "no scripted run is queued"
    [observed] = runtime.observations()
    assert observed.remote_head is not None
    assert remote_commit(remote, BRANCH) == observed.remote_head
    claim = _state_at(boundaries, observed.remote_head).claim
    assert claim is not None
    assert claim.instance == INSTANCE
