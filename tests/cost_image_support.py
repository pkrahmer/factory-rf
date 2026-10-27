"""The launch and settings of the cost tests on the stage image."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.opening import WorkItemOpening
from factory.application.stage import LaunchedStage, StageLauncher
from factory.domain.agent_runs import AgentRunResult
from factory.domain.settings import InstanceSettings
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from settings_support import AGENT_HOME
from stage_run_support import (
    BACKLOG_PATH,
    BRANCH,
    CREATED,
    CREATED_LINE,
    ENVIRONMENT,
    INSTANCE,
    PATH,
    STORY,
    WORK_ITEM,
)

MAKEFILE = (
    ".PHONY: lint check test\n\n"
    "lint:\n\t@echo 'lint done'\n\t@exit 0\n"
    "check:\n\t@echo 'check done'\n\t@exit 0\n"
    "test:\n\t@echo 'test done'\n\t@exit 0\n"
    "sync:\n\t@:\n"
)


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
