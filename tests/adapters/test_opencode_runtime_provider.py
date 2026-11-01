"""The opencode runtime merges the provider file into the configuration of every run."""

import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls
from adapters.opencode_stand_in import (
    MODELS,
    REPLY_EVENTS,
    opencode_request,
    request_configuration,
    write_opencode,
)
from factory.adapters.opencode_runtime import CONFIG_VARIABLE, OpencodeRuntime
from factory.domain.errors import AgentRuntimeError
from opencode_provider_support import CONFIGURATION, write_provider


def _runtime(
    tmp_path: Path,
    provider_file: Path | None,
    models: Mapping[str, str] = MODELS,
    *,
    given: bool = True,
) -> OpencodeRuntime:
    """The runtime on the stand-in; without `given`, `provider_file` is left to its default."""
    executable = str(write_opencode(tmp_path / "bin", [Step(stdout=REPLY_EVENTS)]))
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    if not given:
        return OpencodeRuntime(executable, state, models=models)
    return OpencodeRuntime(executable, state, models=models, provider_file=provider_file)


def _configuration_text(tmp_path: Path) -> str:
    [call] = read_calls(tmp_path / "bin")
    return call.files[call.environment[CONFIG_VARIABLE]]


@pytest.mark.parametrize(
    "given",
    [pytest.param(False, id="default"), pytest.param(True, id="none")],
)
def test_without_a_provider_file_the_configuration_is_as_before(
    tmp_path: Path, *, given: bool
) -> None:
    runtime = _runtime(tmp_path, None, given=given)

    runtime.run(opencode_request(tmp_path / "work"))

    assert _configuration_text(tmp_path) == json.dumps(request_configuration())


def test_a_provider_file_adds_its_keys_beside_the_existing_ones(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, write_provider(tmp_path / "provider"))

    runtime.run(opencode_request(tmp_path / "work"))

    assert json.loads(_configuration_text(tmp_path)) == {
        **request_configuration(),
        **CONFIGURATION,
        "enabled_providers": ["corp"],
    }


@pytest.mark.parametrize(
    "fault",
    [
        pytest.param("missing", id="missing"),
        pytest.param("directory", id="directory"),
        pytest.param("invalid", id="invalid"),
    ],
)
def test_a_provider_file_that_cannot_be_used_fails_before_anything_starts(
    tmp_path: Path, fault: str
) -> None:
    folder = tmp_path / "provider"
    if fault == "missing":
        path = folder / "provider.json"
    elif fault == "directory":
        path = folder / "provider.json"
        path.mkdir(parents=True)
    else:
        path = write_provider(folder, "{}")
    runtime = _runtime(tmp_path, path)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(opencode_request(tmp_path / "work"))

    assert raised.value.detail.startswith(f"cannot use the opencode provider file {path}:")
    assert read_calls(tmp_path / "bin") == []
    assert list((tmp_path / "state").glob("opencode-*.json")) == []


@pytest.mark.parametrize(
    ("model", "models"),
    [
        pytest.param("corp/m", MODELS, id="provider-model"),
        pytest.param("opus", {"opus": "corp/m"}, id="alias"),
    ],
)
def test_a_model_of_the_provider_file_is_passed_as_it_is(
    tmp_path: Path, model: str, models: Mapping[str, str]
) -> None:
    runtime = _runtime(tmp_path, write_provider(tmp_path / "provider"), models)

    runtime.run(opencode_request(tmp_path / "work", model=model))

    [call] = read_calls(tmp_path / "bin")
    assert call.arguments == [
        "run",
        "--format",
        "json",
        "--auto",
        "--model",
        "corp/m",
        "--agent",
        "factory-coder",
        "Stage: doing",
    ]
