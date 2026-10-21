"""A stage runs its checks and reports through the known results."""

from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.boundaries import Boundaries
from factory.application.stage import StageReport, StageRunner
from factory.domain.journal import entry_text
from factory.domain.known_results import ResultRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML
from human_clone import HumanClone
from stage_run_support import (
    CREATED,
    ENVIRONMENT,
    INSTANCE,
    PATH,
    WORK_ITEM,
    completed,
    open_story,
    pushed,
    stage_makefile,
)

ROLES = ("coder", "reviewer", "documenter")
NOT_READ_CHECK = 'check: {time_limit: 10, not_read: ["docs/*", "factory/features/*"]}'
NOT_READ_YAML = PIPELINE_YAML.replace("check: {time_limit: 10}", NOT_READ_CHECK)
REPORT_YAML = NOT_READ_YAML.replace(
    "doing: {role: coder, next: [review, tests], checks: [check]}",
    "doing: {role: coder, next: [review, tests], checks: [check], reports: [test]}",
)
CODE = {"src/a.py": "a = 1\n"}


@dataclass
class Stages:
    """The boundaries with the known results, the definition, and the log the Makefile writes."""

    boundaries: Boundaries
    records: JsonLinesRecordLog[ResultRecord]
    definition_yaml: str
    ran_log: Path

    def run(self) -> StageReport:
        """Run the work item's stage once."""
        definition = self.boundaries.pipeline_reader.parse(self.definition_yaml)
        runner = StageRunner(self.boundaries, INSTANCE, definition, ENVIRONMENT)
        return runner.run(WORK_ITEM, PATH)

    def ran(self, command: str) -> int:
        """How often the Makefile ran `command`."""
        if not self.ran_log.exists():
            return 0
        return self.ran_log.read_text(encoding="utf-8").splitlines().count(command)


def _stages(
    boundaries: Boundaries,
    human: HumanClone,
    agent_home: Path,
    tmp_path: Path,
    *,
    definition_yaml: str,
    statuses: dict[str, int] | None = None,
) -> Stages:
    ran_log = tmp_path / "ran.log"
    records = JsonLinesRecordLog(
        tmp_path / "state" / "records" / "known-results.jsonl", ResultRecord
    )
    known = replace(boundaries, result_records=records)
    makefile = stage_makefile(statuses, extra=[f"@echo $@ >> {ran_log}"])
    state = WorkItemState(stage="doing", journal=[CREATED])
    open_story(known, human, agent_home, makefile=makefile, state=state, roles=ROLES)
    return Stages(known, records, definition_yaml, ran_log)


def _entry_of(document: WorkItemDocument, speaker: str) -> str:
    state = document.state
    assert state is not None
    [record] = [record for record in state.journal if record.speaker == speaker]
    return entry_text(document, record.number)


@pytest.mark.parametrize(
    ("definition_yaml", "main_change", "check_runs"),
    [
        pytest.param(NOT_READ_YAML, False, 1, id="reused"),
        pytest.param(REPORT_YAML, False, 1, id="with-report"),
        pytest.param(PIPELINE_YAML, False, 2, id="no-not-read"),
        pytest.param(NOT_READ_YAML, True, 2, id="merged-code"),
    ],
)
def test_the_docs_stage_takes_the_coders_passed_check_on_the_same_code(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
    definition_yaml: str,
    main_change: bool,
    check_runs: int,
) -> None:
    stages = _stages(boundaries, human, agent_home, tmp_path, definition_yaml=definition_yaml)
    agent_runtime.queue(ScriptedRun(writes=CODE, result=completed("review")))
    agent_runtime.queue(ScriptedRun(result=completed("docs")))
    agent_runtime.queue(
        ScriptedRun(writes={"docs/guide.md": "guide\n"}, result=completed("smoke-test"))
    )

    stages.run()
    coder_records = stages.records.read()
    stages.run()
    if main_change:
        human.push_file("main", "src/b.py", "b = 1\n")
        stages.boundaries.git.fetch()
    stages.run()

    document = pushed(stages.boundaries, remote)
    assert stages.ran("check") == check_runs
    if definition_yaml == REPORT_YAML:
        assert [(record.key.command, record.reused) for record in coder_records] == [
            ("check", None),
            ("test", None),
        ]
        assert _entry_of(document, "coder").endswith("`check`: check done\n`test`: test done")
    documenter = _entry_of(document, "documenter")
    if check_runs == 1:
        tree = stages.records.read()[0].key.tree
        assert documenter.endswith(
            f"`check`: check done (not run again: passed on tree {tree[:12]}"
            " at 2026-10-12T12:00:00Z)"
        )
    else:
        assert documenter.endswith("`check`: check done")


def test_a_red_check_stalls_and_is_run_again_on_the_same_code(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    tmp_path: Path,
) -> None:
    stages = _stages(
        boundaries,
        human,
        agent_home,
        tmp_path,
        definition_yaml=NOT_READ_YAML,
        statuses={"check": 2},
    )
    agent_runtime.queue(ScriptedRun(writes=CODE, result=completed("review")))
    agent_runtime.queue(ScriptedRun(writes=CODE, result=completed("review")))

    report = stages.run()

    assert report.rule == 5
    assert report.stall is not None
    assert report.stall.reason == "check_red"
    [note] = hosting.factory_posts(report.pull_request)
    assert "`check`." in note.body
    assert "check done" in note.body
    assert [record.status for record in stages.records.read()] == ["failed"]

    stages.run()

    assert stages.ran("check") == 2
