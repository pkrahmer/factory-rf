"""A value not written in its own YAML type is a reported stop when the pipeline loads."""

from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.pipeline_loading import PipelineLoader
from factory.domain.errors import PipelineDefinitionInvalid
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone

PIPELINE_FILE = "factory/pipeline.yml"
CODER = '  coder: {write_paths: ["src/*"]}'
ROLES = [
    "intake",
    "tester",
    "coder",
    "reviewer",
    "documenter",
    "smoke-tester",
    "acceptance-reviewer",
]


def test_a_time_limit_written_as_a_boolean_is_one_reported_stop(
    boundaries: Boundaries, *, agent_home: Path, human: HumanClone, checkout: GitCli
) -> None:
    install_agents(agent_home, ROLES)
    assert PIPELINE_YAML.count(CODER) == 1
    text = PIPELINE_YAML.replace(CODER, '  coder: {time_limit: true, write_paths: ["src/*"]}')
    human.push_file("main", PIPELINE_FILE, text)
    checkout.fetch()

    with pytest.raises(PipelineDefinitionInvalid):
        PipelineLoader(boundaries).load()

    stops = boundaries.health.read().stops
    assert [stop.reason for stop in stops] == ["pipeline_definition_invalid"]
    assert stops[0].detail.startswith("invalid roles.coder.time_limit:")
