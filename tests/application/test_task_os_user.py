"""The composed request names the operating-system user of the instance's settings."""

import dataclasses
from pathlib import Path

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.application.boundaries import Boundaries
from factory.application.task import TaskComposer, TaskContext
from factory.domain.agent_runs import AgentDefinition, GuardSettings
from factory.domain.journal import JournalRecord
from factory.domain.settings import InstanceSettings
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import CHECKOUT, PIPELINE_YAML

ENVIRONMENT = {"PATH": "/opt/guard", "HOME": "/home/agent"}


def _context(tmp_path: Path) -> TaskContext:
    state = WorkItemState(
        stage="doing", journal=[JournalRecord(number=1, speaker="human", kind="created")]
    )
    return TaskContext(
        work_item="F0001-S0002",
        path="factory/features/F0001-example/in-progress/F0001-S0002-second.md",
        stage="doing",
        document=WorkItemDocument(state=state, body="# Second story\n"),
        branch="work-item/F0001-S0002",
        pull_request=7,
        findings=[],
        guard=GuardSettings(
            root=tmp_path / CHECKOUT, write_paths=["src/*"], protected_paths=["factory/*"]
        ),
    )


def _agent() -> AgentDefinition:
    return AgentDefinition(
        name="coder", model="sonnet", tools=["Read"], budget_usd=1, instructions="Do the work."
    )


@pytest.mark.parametrize(
    ("agent_user", "expected"),
    [("agent", "agent"), (None, None)],
    ids=["agent-user", "no-agent-user"],
)
def test_the_request_runs_as_the_settings_agent_user_with_the_given_environment(
    boundaries: Boundaries, tmp_path: Path, *, agent_user: str | None, expected: str | None
) -> None:
    settings = InstanceSettings(
        repository_url="/srv/project.git", instance="factory-1", agent_user=agent_user
    )
    composer = TaskComposer(
        dataclasses.replace(boundaries, settings=settings),
        RuamelPipelineDefinitionReader().parse(PIPELINE_YAML),
        ENVIRONMENT,
    )

    request = composer.compose(_context(tmp_path), _agent())

    assert request.os_user == expected
    assert request.environment == ENVIRONMENT
