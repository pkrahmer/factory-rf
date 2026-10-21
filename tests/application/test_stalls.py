"""A stall: writes inside the write paths kept, the rest undone, committed, pushed, then said."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from definition_support import pipeline_definition
from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.opening import WorkItemOpening
from factory.application.stage import StageLauncher, StartedStage
from factory.application.stalls import StallContext, StallResult, StallService
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult, EndReason
from factory.domain.decisions import StallReason, stall_reason_of
from factory.domain.errors import HostingServiceError, PushFailed
from factory.domain.git import CommitId
from factory.domain.hosting import PostKey, PullRequestView
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord, NewEntry, append_entry, entry_text
from factory.domain.post_texts import stall_cause, stall_note
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import install_agents, remote_commit
from human_clone import HumanClone
from observing_runtime import ObservingRuntime

INSTANCE = "factory-1"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
ELSEWHERE = "elsewhere"
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}
STORY = "# First story\n\n## Description\n\nText.\n\n## Journal\n"
BRANCH_BODY = STORY + "\n1. 2026-10-12 human: created.\n"
CREATED = JournalRecord(number=1, speaker="human", kind="created")
INSIDE = "tests/test_a.py"
OUTSIDE = "src/b.py"
COMMITTED_ELSEWHERE = "tests/test_elsewhere.py"
AGENT_TEXT = "written by the agent\n"
WRITES = {INSIDE: AGENT_TEXT, OUTSIDE: AGENT_TEXT}
DIED = AgentRunResult(end_reason="died", duration=timedelta(minutes=3))
STALL_PREFIX = "Stage tests stalled (attempt 1 of 2): "


class SwitchingRuntime(ObservingRuntime):
    """Commits on another branch and leaves the checkout there, then lets the delegate play."""

    elsewhere_head: CommitId | None = None

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Switch to `ELSEWHERE`, commit a file there, then play the scripted run on it."""
        self._checkout.checkout(ELSEWHERE, start_point="HEAD")
        target = request.working_directory / COMMITTED_ELSEWHERE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(AGENT_TEXT, encoding="utf-8")
        self.elsewhere_head = self._checkout.commit("the agent's commit elsewhere")
        return super().run(request)


def _open(boundaries: Boundaries, human: HumanClone, state: WorkItemState) -> None:
    """Start the story on `main` and push its branch with a document in `state`, then fetch."""
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    document = WorkItemDocument(state=state, body=BRANCH_BODY)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    boundaries.git.fetch()


def _launch(
    boundaries: Boundaries,
    agent_runtime: FakeAgentRuntime,
    run: ScriptedRun,
    runtime: AgentRuntime | None = None,
) -> StartedStage:
    definition = pipeline_definition(boundaries)
    prepared = WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)
    agent_runtime.queue(run)
    used = boundaries if runtime is None else replace(boundaries, agent_runtime=runtime)
    return StageLauncher(used, INSTANCE, definition, ENVIRONMENT).launch(prepared).started


def _started(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    state: WorkItemState | None = None,
    run: ScriptedRun | None = None,
) -> StartedStage:
    """Open the work item in stage `tests` and launch it with `run`, by default a death."""
    install_agents(agent_home, ["tester"])
    _open(boundaries, human, state or WorkItemState(stage="tests", journal=[CREATED]))
    return _launch(boundaries, agent_runtime, run or ScriptedRun(writes=WRITES, result=DIED))


def _context(
    started: StartedStage,
    *,
    pull_request: PullRequestView | None = None,
    document: WorkItemDocument | None = None,
) -> StallContext:
    return StallContext(
        work_item=started.work_item,
        stage=started.stage,
        branch=started.branch,
        path=started.path,
        stage_start=started.stage_start,
        document=document,
        pull_request=pull_request,
    )


def _stall(
    boundaries: Boundaries, context: StallContext, reason: StallReason = "died", detail: str = ""
) -> StallResult:
    return StallService(boundaries, INSTANCE, pipeline_definition(boundaries)).stall(
        context, reason, detail
    )


def _head(remote: Path) -> CommitId:
    commit = remote_commit(remote, BRANCH)
    assert commit is not None
    return commit


def _pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:
    text = boundaries.git.show_file(_head(remote), PATH)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def _pushed_state(boundaries: Boundaries, remote: Path) -> WorkItemState:
    state = _pushed(boundaries, remote).state
    assert state is not None
    return state


def _start_state(boundaries: Boundaries, started: StartedStage) -> WorkItemState:
    text = boundaries.git.show_file(started.stage_start.commit, PATH)
    assert text is not None
    state = boundaries.work_item_reader.parse(text).state
    assert state is not None
    return state


@pytest.mark.parametrize("end_reason", ["died", "time_limit", "budget", "no_result"])
def test_a_stall_keeps_the_writes_inside_the_write_paths_and_drops_the_rest(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    end_reason: EndReason,
) -> None:
    result = AgentRunResult(end_reason=end_reason, duration=timedelta(minutes=3))
    started = _started(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        run=ScriptedRun(writes=WRITES, result=result),
    )
    reason = stall_reason_of(result)
    assert reason is not None

    _stall(boundaries, _context(started, pull_request=started.pull_request), reason)

    head = _head(remote)
    assert boundaries.git.show_file(head, INSIDE) == AGENT_TEXT
    assert boundaries.git.show_file(head, OUTSIDE) is None
    assert not (boundaries.checkout / OUTSIDE).exists()


def test_the_agents_rewrite_of_the_state_and_journal_is_put_back(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    clock: ManualClock,
) -> None:
    started = _started(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        state=WorkItemState(stage="tests", attempts=1, journal=[CREATED]),
    )
    target = boundaries.checkout / PATH
    current = boundaries.work_item_reader.read(target)
    assert current.state is not None
    rewritten = current.model_copy(
        update={"state": current.state.model_copy(update={"attempts": 0, "stage": "doing"})}
    )
    entry = NewEntry(speaker="tester", kind="result", text="written by the agent.")
    boundaries.work_item_writer.write(target, append_entry(rewritten, entry))

    _stall(boundaries, _context(started, pull_request=started.pull_request))

    state = _pushed_state(boundaries, remote)
    start_journal = _start_state(boundaries, started).journal
    stall = JournalRecord(
        number=len(start_journal) + 1,
        speaker="factory",
        kind="stall",
        at=clock.now(),
        stage="tests",
        reason="died",
    )
    assert state.stage == "tests"
    assert state.attempts == 2
    assert state.journal == [*start_journal, stall]


def test_each_stall_raises_the_attempts_by_one(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    assert _start_state(boundaries, started).attempts == 0

    first = _stall(boundaries, _context(started, pull_request=started.pull_request))
    first_attempts = _pushed_state(boundaries, remote).attempts
    again = _launch(boundaries, agent_runtime, ScriptedRun(result=DIED))
    second = _stall(boundaries, _context(again, pull_request=again.pull_request))

    assert (first_attempts, first.attempts) == (1, 1)
    assert (_pushed_state(boundaries, remote).attempts, second.attempts) == (2, 2)
    assert first.attempts_cap == second.attempts_cap == pipeline_definition(boundaries).attempts_cap


def test_a_stall_leaves_every_other_counter_as_the_stage_start_held_it(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    state = WorkItemState(
        stage="tests",
        round=1,
        crashes=1,
        comments_read=[3],
        handed_over="tester",
        journal=[CREATED],
    )
    started = _started(
        boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime, state=state
    )

    _stall(boundaries, _context(started, pull_request=started.pull_request))

    fields = ["stage", "blocked", "round", "crashes", "comments_read", "handed_over"]
    pushed = _pushed_state(boundaries, remote).model_dump(include=set(fields))
    assert pushed == _start_state(boundaries, started).model_dump(include=set(fields))
    assert pushed["crashes"] == 1
    assert pushed["comments_read"] == [3]
    assert pushed["handed_over"] == "tester"


def test_a_stall_releases_the_claim(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    assert _start_state(boundaries, started).claim is not None

    _stall(boundaries, _context(started, pull_request=started.pull_request))

    assert _pushed_state(boundaries, remote).claim is None


def test_the_journal_gains_one_stall_entry_of_the_factory_naming_the_cause(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    clock: ManualClock,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    before = len(_start_state(boundaries, started).journal)

    _stall(boundaries, _context(started, pull_request=started.pull_request), "died")

    document = _pushed(boundaries, remote)
    assert document.state is not None
    assert len(document.state.journal) == before + 1
    assert document.state.journal[-1] == JournalRecord(
        number=before + 1,
        speaker="factory",
        kind="stall",
        at=clock.now(),
        stage="tests",
        reason="died",
    )
    text = entry_text(document, before + 1)
    assert text.startswith(STALL_PREFIX)
    assert text.removeprefix(STALL_PREFIX).startswith(stall_cause("died"))


@pytest.mark.parametrize("source", ["context", "open", "none"])
def test_the_stall_records_the_pull_request_of_the_context_or_an_open_one_or_a_new_draft(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    source: str,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    launched_number = started.pull_request.number
    given: PullRequestView | None = None
    if source == "context":
        given = hosting.create_pull_request(BRANCH, "another", "body", draft=False)
        expected = given.number
    elif source == "open":
        expected = launched_number
    else:
        hosting.close_by_human(launched_number)
        expected = launched_number + 1

    result = _stall(boundaries, _context(started, pull_request=given))

    assert _pushed_state(boundaries, remote).pull_request == expected
    assert result.pull_request == expected
    pulls = hosting.pull_requests()
    if source == "open":
        assert len(pulls) == 1
    if source == "none":
        assert len(pulls) == 2
        assert pulls[-1].number == expected
        assert pulls[-1].branch == BRANCH
        assert pulls[-1].state == "open"
        assert pulls[-1].draft


def test_an_agent_that_committed_nothing_gets_exactly_one_stall_commit_pushed(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)

    result = _stall(boundaries, _context(started, pull_request=started.pull_request))

    assert result.commit == _head(remote)
    commits = boundaries.git.log(result.commit, since=started.stage_start.commit)
    assert len(commits) == 1
    assert commits[0].parents == [started.stage_start.commit]


def test_the_agents_own_commit_stays_below_the_one_stall_commit(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    agent_commit = boundaries.git.commit("the agent's own commit")

    result = _stall(boundaries, _context(started, pull_request=started.pull_request))

    commits = boundaries.git.log(result.commit, since=agent_commit)
    assert len(commits) == 1
    assert commits[0].parents == [agent_commit]
    assert boundaries.git.is_ancestor(agent_commit, _head(remote))
    assert boundaries.git.show_file(agent_commit, INSIDE) == AGENT_TEXT


@pytest.mark.parametrize(
    "agent_subject", [None, "the agent's own commit"], ids=["no-agent-commit", "agent-commit"]
)
def test_the_stall_commit_carries_the_work_item_prefix(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    agent_subject: str | None,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    if agent_subject is not None:
        boundaries.git.commit(agent_subject)

    result = _stall(boundaries, _context(started, pull_request=started.pull_request))

    commits = boundaries.git.log(result.commit)
    assert commits[0].subject == "work item F0001-S0001: tests stalled"
    if agent_subject is not None:
        assert commits[1].subject == agent_subject


def test_a_rejected_push_raises_and_posts_no_note(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    human.push_file(BRANCH, "elsewhere.md", "pushed by another clone\n")

    with pytest.raises(PushFailed):
        _stall(boundaries, _context(started, pull_request=started.pull_request))

    assert hosting.factory_posts(started.pull_request.number) == []


def test_the_stall_note_is_posted_once_with_the_stall_entrys_key(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    number = len(_start_state(boundaries, started).journal) + 1

    result = _stall(
        boundaries, _context(started, pull_request=started.pull_request), "check_red", "3 failed"
    )

    [post] = hosting.factory_posts(started.pull_request.number)
    assert post.key == PostKey(work_item=WORK_ITEM, kind="stall", n=str(number))
    assert stall_note("check_red", 1, 2, detail="3 failed") in post.body
    assert result.note == "posted"


def test_a_stall_before_the_stage_started_undoes_nothing_and_still_counts(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    _open(boundaries, human, WorkItemState(stage="tests", journal=[CREATED]))
    WorkItemOpening(boundaries, pipeline_definition(boundaries)).prepare(WORK_ITEM, PATH)
    context = StallContext(
        work_item=WORK_ITEM, stage="tests", branch=BRANCH, path=PATH, stage_start=None
    )

    result = _stall(boundaries, context, "merge_conflict")

    assert result.undo is None
    assert _pushed_state(boundaries, remote).attempts == 1
    assert result.commit == _head(remote)
    assert len(hosting.factory_posts(result.pull_request)) == 1
    assert result.note == "posted"


def test_an_agent_that_left_the_branch_is_brought_back_and_its_other_branch_kept(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    install_agents(agent_home, ["tester"])
    _open(boundaries, human, WorkItemState(stage="tests", journal=[CREATED]))
    runtime = SwitchingRuntime(
        agent_runtime, remote=remote, branch=BRANCH, hosting=hosting, checkout=boundaries.git
    )
    started = _launch(boundaries, agent_runtime, ScriptedRun(writes=WRITES, result=DIED), runtime)
    elsewhere_head = runtime.elsewhere_head
    assert elsewhere_head is not None
    assert boundaries.git.status().branch == ELSEWHERE

    result = _stall(boundaries, _context(started, pull_request=started.pull_request), "left_branch")

    status = boundaries.git.status()
    assert status.branch == BRANCH
    assert status.head == result.commit
    [stall_commit] = boundaries.git.log(result.commit, since=started.stage_start.commit)
    assert stall_commit.parents == [started.stage_start.commit]
    for path in (INSIDE, OUTSIDE, COMMITTED_ELSEWHERE):
        assert not (boundaries.checkout / path).exists()
        assert boundaries.git.show_file(result.commit, path) is None
    assert boundaries.git.resolve(ELSEWHERE) == elsewhere_head


def test_a_given_document_keeps_its_entries_above_the_stall_entry(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    clock: ManualClock,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    entry = NewEntry(speaker="tester", kind="result", text="the agent's entry.")
    document = append_entry(started.document, entry)
    before = len(_start_state(boundaries, started).journal)

    _stall(
        boundaries,
        _context(started, pull_request=started.pull_request, document=document),
    )

    pushed = _pushed(boundaries, remote)
    assert pushed.state is not None
    assert pushed.state.journal[-2] == JournalRecord(
        number=before + 1, speaker="tester", kind="result"
    )
    assert pushed.state.journal[-1] == JournalRecord(
        number=before + 2,
        speaker="factory",
        kind="stall",
        at=clock.now(),
        stage="tests",
        reason="died",
    )
    assert entry_text(pushed, before + 1) == "the agent's entry."


def test_a_hosting_error_while_ensuring_the_pull_request_leaves_the_remote_unchanged(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    hosting.close_by_human(started.pull_request.number)
    hosting.fail_next("create_pull_request")

    with pytest.raises(HostingServiceError):
        _stall(boundaries, _context(started))

    assert remote_commit(remote, BRANCH) == started.stage_start.commit


def test_a_hosting_error_while_posting_the_note_leaves_the_stall_commit_pushed(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    hosting.fail_next("post_comment")

    with pytest.raises(HostingServiceError):
        _stall(boundaries, _context(started, pull_request=started.pull_request))

    [stall_commit] = boundaries.git.log(_head(remote), since=started.stage_start.commit)
    assert stall_commit.parents == [started.stage_start.commit]
    assert _pushed_state(boundaries, remote).attempts == 1
    assert hosting.factory_posts(started.pull_request.number) == []


def test_a_stall_without_a_cost_stamps_its_entry_with_the_time_and_stage_and_no_run(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    clock: ManualClock,
) -> None:
    started = _started(boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime)
    context = _context(started, pull_request=started.pull_request)
    assert context.cost is None

    _stall(boundaries, context, "died")

    stall = _pushed_state(boundaries, remote).journal[-1]
    assert (stall.kind, stall.at, stall.stage, stall.run) == ("stall", clock.now(), "tests", None)


def _result(**changes: object) -> StallResult:
    values: dict[str, object] = {
        "reason": "died",
        "attempts": 1,
        "attempts_cap": 1,
        "commit": "a" * 40,
        "pull_request": 1,
        "note": "posted",
        "undo": None,
    }
    model: type[BaseModel] = StallResult
    built = model.model_validate({**values, **changes})
    assert isinstance(built, StallResult)
    return built


def test_a_stall_result_accepts_the_lowest_counts_and_a_full_commit_id() -> None:
    result = _result()

    assert (result.attempts, result.attempts_cap, result.pull_request) == (1, 1, 1)
    assert result.commit == "a" * 40


@pytest.mark.parametrize(
    ("field", "value"),
    [("attempts", 0), ("attempts_cap", 0), ("pull_request", 0), ("commit", "a" * 39)],
)
def test_a_stall_result_refuses_a_count_below_one_and_a_short_commit_id(
    field: str, value: object
) -> None:
    with pytest.raises(ValidationError):
        _result(**{field: value})
