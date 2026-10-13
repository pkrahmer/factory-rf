"""A definition the rules refuse is a reported stop when the pipeline loads."""

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


@pytest.mark.parametrize(
    ("old", "new", "fault"),
    [
        (
            "next: [review, tests]",
            "next: [review, ship]",
            "stage doing: next names unknown stage ship",
        ),
        (
            '["README.md", "docs/*"]',
            "[]",
            "role documenter: write_paths is empty",
        ),
        (
            'contract: "1.0"',
            'contract: "2.0"',
            "contract major 2 is not supported (this factory reads major 1)",
        ),
        (
            '  coder: {write_paths: ["src/*"]}',
            '  coder: {time_limit: 51, write_paths: ["src/*"]}',
            "role coder at stage doing: 61 min exceed lease_duration 60 min",
        ),
    ],
)
def test_a_definition_the_rules_refuse_is_one_reported_stop(
    boundaries: Boundaries,
    *,
    agent_home: Path,
    human: HumanClone,
    checkout: GitCli,
    old: str,
    new: str,
    fault: str,
) -> None:
    install_agents(agent_home, ROLES)
    assert PIPELINE_YAML.count(old) == 1
    human.push_file("main", PIPELINE_FILE, PIPELINE_YAML.replace(old, new))
    checkout.fetch()

    with pytest.raises(PipelineDefinitionInvalid) as caught:
        PipelineLoader(boundaries).load()

    assert caught.value.fault == fault
    stops = boundaries.health.read().stops
    assert [(stop.reason, stop.detail) for stop in stops] == [
        ("pipeline_definition_invalid", fault)
    ]
