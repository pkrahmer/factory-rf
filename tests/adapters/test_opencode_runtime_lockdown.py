"""With a provider file opencode allows only its provider and gets the lockdown switches."""

import json
from pathlib import Path

import pytest

from adapters.claude_stand_in import StandInCall, read_calls, without_locale
from adapters.container_runtime_support import container_environment, container_request
from adapters.opencode_stand_in import (
    REPLY,
    REQUEST_ENVIRONMENT,
    RESUME_REPLY,
    configuration_text,
    opencode_request,
    over_budget,
    request_configuration,
    stand_in_runtime,
)
from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.opencode_runtime import CONFIG_VARIABLE, LOCKDOWN_SWITCHES
from factory.domain.errors import AgentRuntimeError
from opencode_provider_support import PROVIDER, write_provider

SWITCH_VALUES = {
    "OPENCODE_DISABLE_MODELS_FETCH": "1",
    "OPENCODE_DISABLE_AUTOUPDATE": "1",
    "OPENCODE_DISABLE_DEFAULT_PLUGINS": "1",
}


def _provider(tmp_path: Path, provider_id: str = "corp") -> Path:
    provider = {**PROVIDER, "id": provider_id, "small_model": f"{provider_id}/m"}
    return write_provider(tmp_path / "provider", json.dumps(provider))


def _call_environment(
    tmp_path: Path, fake: FakeContainerRuns, provider_file: Path | None, *, in_container: bool
) -> tuple[dict[str, str], dict[str, str], StandInCall]:
    """Run once; the environment the call got, the one it was expected to get without switches."""
    if in_container:
        runtime = stand_in_runtime(tmp_path, [REPLY], provider_file=provider_file, containers=fake)
        runtime.run(container_request(tmp_path))
        [launch] = fake.calls
        [call] = read_calls(tmp_path / "bin")
        expected = {
            **container_environment(tmp_path / "bin"),
            CONFIG_VARIABLE: call.environment[CONFIG_VARIABLE],
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        return dict(launch.environment), expected, call
    runtime = stand_in_runtime(tmp_path, [REPLY], provider_file=provider_file)
    runtime.run(opencode_request(tmp_path / "work", environment=REQUEST_ENVIRONMENT))
    [call] = read_calls(tmp_path / "bin")
    expected = {
        **REQUEST_ENVIRONMENT,
        CONFIG_VARIABLE: call.environment[CONFIG_VARIABLE],
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return without_locale(call.environment), expected, call


PLACES = [pytest.param(False, id="host"), pytest.param(True, id="container")]


@pytest.mark.parametrize("in_container", PLACES)
def test_without_a_provider_file_the_configuration_and_environment_are_as_before(
    tmp_path: Path, fake: FakeContainerRuns, *, in_container: bool
) -> None:
    environment, expected, call = _call_environment(tmp_path, fake, None, in_container=in_container)

    assert environment == expected
    assert configuration_text(call) == json.dumps(request_configuration())


@pytest.mark.parametrize("provider_id", [pytest.param("corp"), pytest.param("corp-1")])
def test_a_provider_file_enables_only_its_own_provider(tmp_path: Path, provider_id: str) -> None:
    runtime = stand_in_runtime(tmp_path, [REPLY], provider_file=_provider(tmp_path, provider_id))

    runtime.run(opencode_request(tmp_path / "work"))

    [call] = read_calls(tmp_path / "bin")
    configuration = json.loads(configuration_text(call))
    assert configuration["enabled_providers"] == [provider_id]
    assert set(configuration) == {
        "enabled_providers",
        "provider",
        "small_model",
        "autoupdate",
        "share",
        "snapshot",
        "agent",
    }
    assert "disabled_providers" not in configuration


@pytest.mark.parametrize("in_container", PLACES)
def test_a_provider_file_adds_the_lockdown_switches_to_the_call_s_environment(
    tmp_path: Path, fake: FakeContainerRuns, *, in_container: bool
) -> None:
    environment, expected, _ = _call_environment(
        tmp_path, fake, _provider(tmp_path), in_container=in_container
    )

    assert LOCKDOWN_SWITCHES == SWITCH_VALUES
    assert environment == {**expected, **SWITCH_VALUES}


@pytest.mark.parametrize("switch", list(SWITCH_VALUES))
@pytest.mark.parametrize(
    ("with_provider", "value"),
    [pytest.param(True, "1", id="provider-file"), pytest.param(False, "0", id="no-provider-file")],
)
def test_a_request_s_lockdown_switch_is_overridden_only_with_a_provider_file(
    tmp_path: Path, switch: str, *, with_provider: bool, value: str
) -> None:
    provider_file = _provider(tmp_path) if with_provider else None
    runtime = stand_in_runtime(tmp_path, [REPLY], provider_file=provider_file)

    runtime.run(
        opencode_request(tmp_path / "work", environment={**REQUEST_ENVIRONMENT, switch: "0"})
    )

    [call] = read_calls(tmp_path / "bin")
    assert call.environment[switch] == value


def test_a_budget_resume_carries_the_first_call_s_switches_and_configuration(
    tmp_path: Path,
) -> None:
    runtime = stand_in_runtime(
        tmp_path, [over_budget(), RESUME_REPLY], provider_file=_provider(tmp_path)
    )

    runtime.run(opencode_request(tmp_path / "work"))

    first, resume = read_calls(tmp_path / "bin")
    assert {name: first.environment.get(name) for name in SWITCH_VALUES} == SWITCH_VALUES
    assert resume.environment == first.environment
    assert configuration_text(resume) == configuration_text(first)
    assert json.loads(configuration_text(first))["enabled_providers"] == ["corp"]


def test_a_refused_provider_file_fails_before_any_file_is_written(tmp_path: Path) -> None:
    path = write_provider(tmp_path / "provider", json.dumps({**PROVIDER, "unknown": 1}))
    runtime = stand_in_runtime(tmp_path, [REPLY], provider_file=path)

    with pytest.raises(AgentRuntimeError):
        runtime.run(opencode_request(tmp_path / "work"))

    assert read_calls(tmp_path / "bin") == []
    assert list((tmp_path / "state").glob("opencode-*.json")) == []
