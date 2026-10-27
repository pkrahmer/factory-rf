"""Cost records name the image the agent run ran on, taken from the instance's settings."""

from dataclasses import replace
from pathlib import Path

import pytest

from cost_image_support import (
    _launch,
    _settings,
)
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.costs import CostRecorder
from factory.domain.settings import InstanceSettings
from human_clone import HumanClone


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
