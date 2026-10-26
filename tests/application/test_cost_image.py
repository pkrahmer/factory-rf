"""Cost records name the image the agent run ran on, taken from the instance's settings."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.costs import CostRecorder
from factory.application.opening import WorkItemOpening
from factory.application.stage import LaunchedStage, StageLauncher
from factory.domain.agent_runs import AgentRunResult
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord
from factory.domain.settings import InstanceSettings
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from settings_support import AGENT_HOME
from stage_run_support import ENVIRONMENT, INSTANCE

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
MAKEFILE = (
    ".PHONY: lint check test\n\n"
    "lint:\n\t@echo 'lint done'\n\t@exit 0\n"
    "check:\n\t@echo 'check done'\n\t@exit 0\n"
    "test:\n\t@echo 'test done'\n\t@exit 0\n"
    "sync:\n\t@:\n"
)
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
CREATED = JournalRecord(number=1, speaker="human", kind="created")
CREATED_LINE = "\n1. 2026-10-12 human: created.\n"


def _settings(image: str | None) -> InstanceSettings:
    return InstanceSettings(
        repository_url="https://example.invalid/project.git",
        instance=INSTANCE,
        agent_home=AGENT_HOME,
        image=image,
    )


def _launch(
    boundaries: Boundaries, human: HumanClone, agent_home: Path, agent_runtime: FakeAgentRuntime
) -> LaunchedStage:
    """Start the story in `tests` and run its stage once, on a completed agent run."""
    # The sync copies the agent home, so it is the fixture's whatever the settings name.
    settings = boundaries.settings.model_copy(update={"agent_home": agent_home})
    boundaries = replace(boundaries, settings=settings)
    install_agents(agent_home, ["tester"])
    human.push_file("main", "Makefile", MAKEFILE)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    state = WorkItemState(stage="tests", attempts=0, journal=[CREATED])
    document = WorkItemDocument(state=state, body=STORY + CREATED_LINE)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    boundaries.git.fetch()
    agent_runtime.queue(
        ScriptedRun(
            result=AgentRunResult.model_validate(
                {
                    "end_reason": "completed",
                    "decision": "doing",
                    "entry": "tests written.",
                    "duration": timedelta(minutes=1),
                }
            )
        )
    )
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    prepared = WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)
    return StageLauncher(boundaries, INSTANCE, definition, ENVIRONMENT).launch(prepared)


def test_a_cost_record_names_the_image_of_the_settings_and_keeps_it_when_completed(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    used = replace(boundaries, settings=_settings("build-7"))
    launched = _launch(used, human, agent_home, agent_runtime)
    recorder = CostRecorder(used)

    begun = recorder.begin(launched.started, "tester")
    completed = recorder.complete(begun, launched.result)

    assert begun.records[-1].status == "started"
    assert begun.records[-1].image == "build-7"
    assert completed.records[-1].status == "completed"
    assert completed.records[-1].image == "build-7"
    assert launched.cost.records[-1].image == "build-7"


@pytest.mark.parametrize("settings", [_settings(None)], ids=["settings-without-image"])
def test_a_cost_record_has_no_image_when_the_settings_name_none(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    settings: InstanceSettings,
) -> None:
    used = replace(boundaries, settings=settings)
    launched = _launch(used, human, agent_home, agent_runtime)

    begun = CostRecorder(used).begin(launched.started, "tester")

    assert begun.records[-1].image is None
    assert launched.cost.records[-1].image is None
