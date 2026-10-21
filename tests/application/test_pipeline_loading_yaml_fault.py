"""A pipeline definition that is not valid YAML is one stop and one log line."""

from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.pipeline_loading import PIPELINE_REF, PipelineLoader
from factory.domain.errors import PipelineDefinitionInvalid
from factory.domain.stops import RepositoryStop
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from log_support import log_lines

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
REPEATED_KEY_FAULT = (
    'not valid YAML: found duplicate key "done" with value "{}" (original value: "{}")'
    " (line 27, column 3)"
)


def test_a_repeated_key_on_main_is_one_stop_and_one_log_line(
    boundaries: Boundaries,
    *,
    agent_home: Path,
    human: HumanClone,
    checkout: GitCli,
    clock: ManualClock,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, ROLES)
    human.push_file("main", PIPELINE_FILE, PIPELINE_YAML + "  done: {}\n")
    checkout.fetch()
    before = log_lines(tmp_path)

    with pytest.raises(PipelineDefinitionInvalid) as caught:
        PipelineLoader(boundaries).load(PIPELINE_REF)

    assert caught.value.fault == REPEATED_KEY_FAULT
    assert boundaries.health.read().stops == [
        RepositoryStop(
            scope="repository",
            reason="pipeline_definition_invalid",
            detail=REPEATED_KEY_FAULT,
            at=clock.now(),
        )
    ]
    added = log_lines(tmp_path)[len(before) :]
    assert len(added) == 1
    assert added[0].endswith(f"stop repository pipeline_definition_invalid: {REPEATED_KEY_FAULT}")
