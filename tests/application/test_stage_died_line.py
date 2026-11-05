"""A stage whose run died writes one line in the factory log that quotes the run's text."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.domain.agent_runs import AgentRunResult
from factory.shared.domain.paths import cost_records_path
from human_clone import HumanClone
from recording_log import RecordingLog
from stage_run_support import PATH, WORK_ITEM, branch_head, completed, open_story, run_stage

LIMIT_TEXT = "You've hit your limit · resets 12am"
DIED = AgentRunResult(end_reason="died", duration=timedelta(minutes=3), died_text=LIMIT_TEXT)


@pytest.mark.parametrize(
    ("result", "died"),
    [pytest.param(DIED, True, id="died"), pytest.param(completed(), False, id="completed")],
)
def test_a_died_run_writes_its_line_in_the_factory_log_and_no_other_run_does(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    result: AgentRunResult,
    died: bool,
) -> None:
    open_story(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=result))
    log = RecordingLog()

    run_stage(replace(boundaries, log=log))

    text = boundaries.git.show_file(branch_head(remote), cost_records_path(PATH))
    assert text is not None
    [record] = boundaries.cost_reader.parse(text)
    expected = f"run {record.run} of {WORK_ITEM} (tests) died: {LIMIT_TEXT}"
    assert [line for line in log.lines if " died: " in line] == ([expected] if died else [])
