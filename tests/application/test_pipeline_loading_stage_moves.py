"""A stage that cannot move is a reported stop when the pipeline loads."""

from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.pipeline_loading import PipelineLoader
from factory.domain.errors import PipelineDefinitionInvalid
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone

PIPELINE_FILE = "factory/pipeline.yml"
ROLES = [
    "intake",
    "tester",
    "coder",
    "reviewer",
    "documenter",
    "smoke-tester",
    "acceptance-reviewer",
]
DONE_STAGE = "  done: {}"


def test_a_stage_without_role_or_approval_is_one_reported_stop(
    boundaries: Boundaries, *, agent_home: Path, human: HumanClone, checkout: GitCli
) -> None:
    install_agents(agent_home, ROLES)
    assert PIPELINE_YAML.count(DONE_STAGE) == 1
    text = PIPELINE_YAML.replace(DONE_STAGE, "  limbo: {next: [done]}\n" + DONE_STAGE)
    human.push_file("main", PIPELINE_FILE, text)
    checkout.fetch()

    with pytest.raises(PipelineDefinitionInvalid) as caught:
        PipelineLoader(boundaries).load()

    fault = "stage limbo: has neither a role nor approval"
    assert caught.value.fault == fault
    stops = boundaries.health.read().stops
    assert [(stop.reason, stop.detail) for stop in stops] == [
        ("pipeline_definition_invalid", fault)
    ]
