"""A stage whose report reaches its time limit: the entry's line for it says it was stopped."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import override

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.project_commands import ProjectCommands
from factory.domain.checks import CheckResult
from factory.domain.journal import entry_text
from human_clone import HumanClone
from stage_run_support import PATH, branch_head, completed, open_story, run_stage, stage_makefile

STOPPED_TEST = CheckResult(
    command="test",
    status="time_limit",
    exit_status=None,
    duration=timedelta(seconds=600.7),
    last_line="1718/1858 mutants",
    output_tail="1718/1858 mutants",
)


class StoppedTestCommands(ProjectCommands):
    """Project commands whose `test` reaches its time limit; every other runs on the delegate."""

    def __init__(self, delegate: ProjectCommands) -> None:
        self._delegate = delegate

    @override
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        if command == "test":
            return STOPPED_TEST
        return self._delegate.run(command, time_limit=time_limit)


def test_a_report_stopped_at_its_time_limit_says_so_in_the_entry(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    stopped = replace(boundaries, project_commands=StoppedTestCommands(boundaries.project_commands))
    open_story(stopped, human, agent_home, makefile=stage_makefile())
    agent_runtime.queue(ScriptedRun(result=completed("doing")))

    report = run_stage(stopped)

    assert report.rule == 6
    assert report.next_stage == "doing"
    text = boundaries.git.show_file(branch_head(remote), PATH)
    assert text is not None
    document = boundaries.work_item_reader.parse(text)
    assert document.state is not None
    [record] = [record for record in document.state.journal if record.speaker == "tester"]
    assert entry_text(document, record.number).endswith(
        "`lint`: lint done\n`test`: 1718/1858 mutants (stopped at its time limit after 600 s)"
    )
