"""The inline environment: nothing prepared, the agent sealed in the checkout, the undo as take."""

import re
from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from application.test_nested_repositories import NestingRuntime
from application.test_sealed_runs import OPEN_FILE, OPEN_FOLDER, ModeRecordingRuntime, _leave
from application.test_sealed_runs_runner import Runner
from application.test_undo import _with_broken_work_item, _without_work_item
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.stage_environment import InlineEnvironment, stage_environment_of
from factory.application.take import TakeReport
from factory.domain.errors import WorkItemFormatError
from git_support import run_git, write_files
from human_clone import HumanClone
from sealed_run_support import COMPLETED, run_request
from undo_support import GUIDE, GUIDE_TEXT, KEPT, PATH, start_stage
from work_item_support import checkout_text

WRITTEN = "tests/test_a.py"
NEW_DOC = "docs/new.md"
AGENT_TEXT = "written by the agent\n"
SEALED_MODES = (0o2755, 0o644)


def _open_git_folder(checkout: Path) -> None:
    folder = checkout / ".git"
    folder.chmod(OPEN_FOLDER)
    (folder / "config").chmod(OPEN_FILE)


def test_prepare_does_nothing_and_reads_nothing(
    boundaries: Boundaries, agent_runtime: FakeAgentRuntime
) -> None:
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
    _open_git_folder(boundaries.checkout)
    request = run_request(boundaries.checkout)
    if given:
        runner = Runner(boundaries.checkout, _leave)
        sealed = InlineEnvironment(boundaries).run_agent(request, run=runner.run)
        assert runner.requests == [request]
        assert runner.modes == [SEALED_MODES]
        assert agent_runtime.requests() == []
    else:
        agent_runtime.queue(ScriptedRun(writes={WRITTEN: AGENT_TEXT}, result=COMPLETED))
        runtime = ModeRecordingRuntime(agent_runtime, boundaries.checkout)
        recording = replace(boundaries, agent_runtime=runtime)
        sealed = InlineEnvironment(recording).run_agent(request)
        assert runtime.modes == [SEALED_MODES]
        assert agent_runtime.requests() == [request]
        assert checkout_text(boundaries, WRITTEN) == AGENT_TEXT

    assert sealed.result == COMPLETED
    assert sealed.nested_repositories == []


def test_run_agent_removes_a_nested_repository_and_names_it(
    boundaries: Boundaries, agent_runtime: FakeAgentRuntime
) -> None:
    def nest(checkout: Path) -> None:
        notes = checkout / "notes"
        notes.mkdir()
        run_git(notes, "init", "-q")

    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    nesting = replace(
        boundaries, agent_runtime=NestingRuntime(agent_runtime, boundaries.checkout, nest)
    )

    sealed = InlineEnvironment(nesting).run_agent(run_request(boundaries.checkout))

    assert sealed.result == COMPLETED
    assert sealed.nested_repositories == ["notes/.git"]
    assert not (boundaries.checkout / "notes" / ".git").exists()


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
        pytest.param(_without_work_item, None, id="work-item-absent"),
        pytest.param(_with_broken_work_item, None, id="work-item-unreadable"),
    ],
)
def test_take_is_the_undo_turned_into_a_take_report(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    change: Callable[[Boundaries, StageStart], StageStart],
    restored: bool | None,
) -> None:
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
    assert isinstance(stage_environment_of(boundaries), InlineEnvironment)
