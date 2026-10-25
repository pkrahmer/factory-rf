"""The stage protocol calls its environment: prepare after the claim, the run, the take after."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.opening import WorkItemOpening
from factory.application.stage import AfterAgent, AgentAftermath, LaunchedStage, StageLauncher
from factory.application.stage_environment import StageEnvironment
from factory.application.take import TakeReport
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.errors import SnapshotError
from factory.domain.git import CommitId
from factory.domain.journal import entry_text
from factory.domain.paths import cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from git_support import PIPELINE_YAML, remote_commit
from human_clone import HumanClone
from stage_run_support import (
    BRANCH,
    ENVIRONMENT,
    INSTANCE,
    PATH,
    WORK_ITEM,
    completed,
    open_story,
    pushed,
    pushed_state,
    run_stage,
)
from take_support import AGENT_TEXT
from work_item_support import checkout_text

OUTSIDE = "src/b.py"
UNDONE_PARAGRAPH = "The factory undid changes outside the write paths: "
TEST_COMMAND = "  test: {time_limit: 10}\n"
WITH_SYNC = PIPELINE_YAML.replace(TEST_COMMAND, TEST_COMMAND + "  sync: {time_limit: 5}\n")
NOTHING_LEFT = TakeReport(left=[], restored_work_item=False)


class RecordingEnvironment(StageEnvironment):
    """Records each call with its arguments and the remote's branch head at `prepare`."""

    def __init__(
        self,
        remote: Path,
        *,
        taken: TakeReport = NOTHING_LEFT,
        refusal: SnapshotError | None = None,
    ) -> None:
        self._remote = remote
        self._taken = taken
        self._refusal = refusal
        self.calls: list[str] = []
        self.prepared: list[tuple[CommitId, str, timedelta]] = []
        self.remote_heads: list[str | None] = []
        self.requests: list[AgentRunRequest] = []
        self.takes: list[tuple[StageStart, str]] = []

    def prepare(self, commit: CommitId, branch: str, *, sync_time_limit: timedelta) -> None:
        self.calls.append("prepare")
        self.prepared.append((commit, branch, sync_time_limit))
        self.remote_heads.append(remote_commit(self._remote, branch))
        if self._refusal is not None:
            raise self._refusal

    def run_agent(
        self,
        request: AgentRunRequest,
        *,
        run: Callable[[AgentRunRequest], AgentRunResult] | None = None,
    ) -> AgentRunResult:
        self.calls.append("run_agent")
        self.requests.append(request)
        assert run is not None
        return run(request)

    def take(self, stage_start: StageStart, work_item_path: str) -> TakeReport:
        self.calls.append("take")
        self.takes.append((stage_start, work_item_path))
        return self._taken


def _launch(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    environment: RecordingEnvironment,
    definition: PipelineDefinition | None = None,
) -> LaunchedStage:
    open_story(boundaries, human, agent_home)
    used = definition or boundaries.pipeline_reader.parse(PIPELINE_YAML)
    prepared = WorkItemOpening(boundaries, used).prepare(WORK_ITEM, PATH)
    launcher = StageLauncher(boundaries, INSTANCE, used, ENVIRONMENT, stage_environment=environment)
    return launcher.launch(prepared)


@pytest.mark.parametrize(
    ("text", "limit"),
    [
        pytest.param(WITH_SYNC, timedelta(minutes=5), id="sync-command"),
        pytest.param(PIPELINE_YAML, timedelta(minutes=10), id="no-sync-command"),
    ],
)
def test_the_launch_prepares_after_the_claim_then_runs_the_agent_through_the_environment(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    text: str,
    limit: timedelta,
) -> None:
    environment = RecordingEnvironment(remote)
    agent_runtime.queue(ScriptedRun(result=completed()))

    launched = _launch(
        boundaries,
        human=human,
        agent_home=agent_home,
        environment=environment,
        definition=boundaries.pipeline_reader.parse(text),
    )

    commit = launched.started.stage_start.commit
    assert environment.calls == ["prepare", "run_agent"]
    assert environment.prepared == [(commit, BRANCH, limit)]
    assert environment.remote_heads == [commit]
    assert environment.requests == [launched.request]
    assert agent_runtime.requests() == [launched.request]
    assert launched.result == completed()


def test_a_refused_prepare_ends_the_launch_after_the_claim_and_before_the_run(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    refusal = SnapshotError("reset", "no base")
    environment = RecordingEnvironment(remote, refusal=refusal)
    agent_runtime.queue(ScriptedRun(result=completed()))

    with pytest.raises(SnapshotError) as raised:
        _launch(boundaries, human=human, agent_home=agent_home, environment=environment)

    assert raised.value is refusal
    state = pushed_state(boundaries, remote)
    assert state.claim is not None
    assert environment.remote_heads == [remote_commit(remote, BRANCH)]
    assert environment.calls == ["prepare"]
    assert agent_runtime.requests() == []
    assert not (boundaries.checkout / cost_records_path(PATH)).exists()


@pytest.mark.parametrize(
    ("left", "paragraph"),
    [
        pytest.param([OUTSIDE], f"\n\n{UNDONE_PARAGRAPH}{OUTSIDE}.", id="one-path"),
        pytest.param(
            [cost_records_path(PATH), OUTSIDE],
            f"\n\n{UNDONE_PARAGRAPH}{OUTSIDE}.",
            id="own-cost-records-left-out",
        ),
        pytest.param([], None, id="nothing-left"),
    ],
)
def test_after_the_agent_the_environment_takes_and_its_report_closes_the_entry(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    left: list[str],
    paragraph: str | None,
) -> None:
    taken = TakeReport(left=left, restored_work_item=False)
    environment = RecordingEnvironment(remote, taken=taken)
    agent_runtime.queue(ScriptedRun(writes={OUTSIDE: AGENT_TEXT}, result=completed()))
    launched = _launch(boundaries, human=human, agent_home=agent_home, environment=environment)
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    after = AfterAgent(boundaries, INSTANCE, definition, stage_environment=environment)

    processed = after.process(launched)

    assert isinstance(processed, AgentAftermath)
    assert environment.takes == [(launched.started.stage_start, PATH)]
    assert environment.calls == ["prepare", "run_agent", "take"]
    assert processed.take == taken
    # Nothing but the stand-in's take ran: the inline undo would have reverted the file.
    assert checkout_text(boundaries, OUTSIDE) == AGENT_TEXT
    if paragraph is None:
        assert UNDONE_PARAGRAPH not in processed.entry.text
    else:
        assert processed.entry.text.endswith(paragraph)


def test_a_stage_built_without_an_environment_runs_the_inline_one(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    open_story(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(writes={OUTSIDE: AGENT_TEXT}, result=completed()))

    run_stage(boundaries)

    assert checkout_text(boundaries, OUTSIDE) is None
    document = pushed(boundaries, remote)
    state = document.state
    assert state is not None
    [record] = [record for record in state.journal if record.speaker == "tester"]
    assert f"{UNDONE_PARAGRAPH}{OUTSIDE}." in entry_text(document, record.number)
