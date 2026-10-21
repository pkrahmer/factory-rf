"""Cost records name the instance that ran the agent run, taken from the instance's settings."""

from dataclasses import replace
from pathlib import Path

import pytest

from application.test_cost_image import _launch, _settings
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.costs import CostRecorder
from factory.domain.settings import InstanceSettings
from human_clone import HumanClone


@pytest.mark.parametrize(
    ("settings", "expected"),
    [(_settings("build-7"), "factory-1")],
    ids=["settings"],
)
def test_a_cost_record_names_the_instance_of_the_settings_and_keeps_it_when_completed(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    settings: InstanceSettings,
    expected: str,
) -> None:
    used = replace(boundaries, settings=settings)
    launched = _launch(used, human, agent_home, agent_runtime)
    recorder = CostRecorder(used)

    begun = recorder.begin(launched.started, "tester")
    completed = recorder.complete(begun, launched.result)

    assert begun.records[-1].status == "started"
    assert begun.records[-1].instance == expected
    assert completed.records[-1].status == "completed"
    assert completed.records[-1].instance == expected
    assert launched.cost.records[-1].instance == expected
