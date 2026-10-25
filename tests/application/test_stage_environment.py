"""The inline environment: nothing prepared, the agent run in the checkout, the undo as take."""

import re
import stat
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from container_support import container_dataset, container_environment, inline_boundaries
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.stage_environment import (
    InlineEnvironment,
    StageEnvironment,
    stage_environment_of,
)
from factory.application.take import TakeReport
from factory.domain.agent_runs import AgentRunResult
from factory.domain.errors import WorkItemFormatError
from git_support import write_files
from human_clone import HumanClone
from sealed_run_support import COMPLETED, RecordingRun, run_request
from stage_run_support import INSIDE
from take_support import AGENT_TEXT
from undo_support import (
    GUIDE,
    GUIDE_TEXT,
    KEPT,
    PATH,
    start_stage,
    with_broken_work_item,
    without_work_item,
)
from work_item_support import checkout_text

NEW_DOC = "docs/new.md"
OTHER_RESULT = AgentRunResult(
    end_reason="completed", decision="doing", entry="queued", duration=timedelta(seconds=7)
)


def test_prepare_does_nothing_and_reads_nothing(
    boundaries: Boundaries, agent_runtime: FakeAgentRuntime
) -> None:
    boundaries = inline_boundaries(boundaries)
    status = boundaries.git.status()
    tree = boundaries.git.work_tree_id()

    InlineEnvironment(boundaries).prepare(
        "a" * 40, "work-item/F0001-S0001", sync_time_limit=timedelta(minutes=5)
    )

    assert boundaries.git.status() == status
    assert boundaries.git.work_tree_id() == tree
    assert agent_runtime.requests() == []


@pytest.mark.parametrize("given", [False, True], ids=["runtime", "given-run"])
def test_run_agent_is_the_sealed_run_through_the_runtime_or_the_given_run(
    boundaries: Boundaries, agent_runtime: FakeAgentRuntime, *, given: bool
) -> None:
    boundaries = inline_boundaries(boundaries)
    request = run_request(boundaries.checkout)
    if given:
        recorder = RecordingRun()
        result = InlineEnvironment(boundaries).run_agent(request, run=recorder.run)
        assert recorder.requests == [request]
        assert agent_runtime.requests() == []
    else:
        agent_runtime.queue(ScriptedRun(writes={INSIDE: AGENT_TEXT}, result=COMPLETED))
        result = InlineEnvironment(boundaries).run_agent(request)
        assert agent_runtime.requests() == [request]
        assert checkout_text(boundaries, INSIDE) == AGENT_TEXT

    assert result == COMPLETED


def _inline(boundaries: Boundaries, _tmp_path: Path) -> tuple[StageEnvironment, Path]:
    return InlineEnvironment(boundaries), boundaries.checkout


def _container(boundaries: Boundaries, tmp_path: Path) -> tuple[StageEnvironment, Path]:
    dataset = container_dataset(boundaries, tmp_path)
    return container_environment(dataset), dataset.boundaries.checkout


Environment = Callable[[Boundaries, Path], tuple[StageEnvironment, Path]]


def _queued_result(
    environment: StageEnvironment, checkout: Path, runtime: FakeAgentRuntime
) -> None:
    runtime.queue(ScriptedRun(result=OTHER_RESULT))

    assert environment.run_agent(run_request(checkout)) == OTHER_RESULT


def _given_run(environment: StageEnvironment, checkout: Path, runtime: FakeAgentRuntime) -> None:
    recorder = RecordingRun()
    request = run_request(checkout)

    assert environment.run_agent(request, run=recorder.run) == COMPLETED
    assert recorder.requests == [request]
    assert runtime.requests() == []


@pytest.mark.parametrize(
    "environment_of",
    [pytest.param(_inline, id="inline"), pytest.param(_container, id="container")],
)
@pytest.mark.parametrize(
    "case",
    [pytest.param(_queued_result, id="queued"), pytest.param(_given_run, id="given-run")],
)
def test_run_agent_returns_the_runs_result(
    boundaries: Boundaries,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    *,
    environment_of: Environment,
    case: Callable[[StageEnvironment, Path, FakeAgentRuntime], None],
) -> None:
    environment, checkout = environment_of(boundaries, tmp_path)

    case(environment, checkout, agent_runtime)


def test_the_inline_run_leaves_a_nested_repository_ignored_files_and_the_git_folders_mode(
    boundaries: Boundaries, agent_runtime: FakeAgentRuntime
) -> None:
    boundaries = inline_boundaries(boundaries)
    checkout = boundaries.checkout
    write_files(checkout, {".gitignore": ".venv/\n"})
    folder = checkout / ".git"
    folder.chmod(0o2775)
    agent_runtime.queue(
        ScriptedRun(
            writes={"sub/.git/HEAD": "ref: refs/heads/main\n", ".venv/x": "kept\n"},
            result=COMPLETED,
        )
    )

    result = InlineEnvironment(boundaries).run_agent(run_request(checkout))

    assert result == COMPLETED
    assert (checkout / "sub" / ".git" / "HEAD").read_text(encoding="utf-8") == (
        "ref: refs/heads/main\n"
    )
    assert (checkout / ".venv" / "x").read_text(encoding="utf-8") == "kept\n"
    assert stat.S_IMODE(folder.stat().st_mode) == 0o2775


def _as_started(boundaries: Boundaries, start: StageStart) -> StageStart:
    del boundaries
    return start


def _with_raised_attempts(boundaries: Boundaries, start: StageStart) -> StageStart:
    target = boundaries.checkout / PATH
    current = boundaries.work_item_reader.read(target)
    assert current.state is not None
    raised = current.model_copy(update={"state": current.state.model_copy(update={"attempts": 3})})
    boundaries.work_item_writer.write(target, raised)
    return start


@pytest.mark.parametrize(
    ("change", "restored"),
    [
        pytest.param(_as_started, False, id="work-item-untouched"),
        pytest.param(_with_raised_attempts, True, id="work-item-state-changed"),
        pytest.param(without_work_item, None, id="work-item-absent"),
        pytest.param(with_broken_work_item, None, id="work-item-unreadable"),
    ],
)
def test_take_is_the_undo_turned_into_a_take_report(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    change: Callable[[Boundaries, StageStart], StageStart],
    restored: bool | None,
) -> None:
    boundaries = inline_boundaries(boundaries)
    start = start_stage(boundaries, human, write_paths=["src/*", "{work_item}"])
    used = change(boundaries, start)
    write_files(boundaries.checkout, {NEW_DOC: AGENT_TEXT, GUIDE: AGENT_TEXT, KEPT: AGENT_TEXT})

    if restored is None:
        with pytest.raises(WorkItemFormatError, match=re.escape(PATH)):
            InlineEnvironment(boundaries).take(used, PATH)
        assert checkout_text(boundaries, GUIDE) == AGENT_TEXT
        assert checkout_text(boundaries, NEW_DOC) == AGENT_TEXT
        return
    report = InlineEnvironment(boundaries).take(used, PATH)

    assert report == TakeReport(left=[GUIDE, NEW_DOC], restored_work_item=restored)
    assert checkout_text(boundaries, GUIDE) == GUIDE_TEXT
    assert checkout_text(boundaries, NEW_DOC) is None
    assert checkout_text(boundaries, KEPT) == AGENT_TEXT


def test_the_environment_of_the_boundaries_is_the_inline_one(boundaries: Boundaries) -> None:
    boundaries = inline_boundaries(boundaries)
    assert isinstance(stage_environment_of(boundaries), InlineEnvironment)
