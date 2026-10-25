"""`main` writes the stop of invalid settings into the directory `FACTORY_STATE` names."""

import re
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.domain.errors import SettingsInvalid
from factory.domain.settings import InstanceSettings
from factory.entry.run import main
from factory.entry.wiring import health_store

STAMP = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ "
TWO_REPOSITORIES = "https://example.invalid/a.git,https://example.invalid/b.git"
REPOSITORY_FAULT = "FACTORY_REPOSITORY_URL: names more than one repository"


class Runner:
    """Records the settings it is called with, and raises the error it is given."""

    def __init__(self, error: SettingsInvalid | None = None) -> None:
        self.calls: list[InstanceSettings] = []
        self._error = error

    def __call__(self, settings: InstanceSettings) -> None:
        self.calls.append(settings)
        if self._error is not None:
            raise self._error


def _token_fault(tmp_path: Path) -> SettingsInvalid:
    return SettingsInvalid("FACTORY_TOKEN_FILE", f"cannot read {tmp_path / 'token'}")


def _assert_stop(state_directory: Path, detail: str) -> None:
    [line] = (state_directory / "factory.log").read_text(encoding="utf-8").splitlines()
    assert re.fullmatch(STAMP + re.escape(f"settings invalid: {detail}"), line)
    [stop] = health_store(state_directory).read().stops
    assert (stop.scope, stop.reason) == ("machine", "preflight_failed")
    assert detail in stop.detail


def test_the_stop_of_invalid_settings_goes_to_the_directory_the_environment_names(
    environment: dict[str, str], tmp_path: Path, clock: ManualClock
) -> None:
    environ = {
        **environment,
        "FACTORY_REPOSITORY_URL": TWO_REPOSITORIES,
        "FACTORY_STATE": str(tmp_path / "state"),
    }

    status = main(environ, runner=Runner(), state_directory=tmp_path / "fallback", clock=clock)

    assert status == 2
    _assert_stop(tmp_path / "state", REPOSITORY_FAULT)
    assert not (tmp_path / "fallback").exists()


@pytest.mark.parametrize(
    ("extra", "detail"),
    [
        pytest.param(
            {"FACTORY_REPOSITORY_URL": TWO_REPOSITORIES}, REPOSITORY_FAULT, id="state-unset"
        ),
        pytest.param(
            {"FACTORY_REPOSITORY_URL": TWO_REPOSITORIES, "FACTORY_STATE": ""},
            REPOSITORY_FAULT,
            id="state-blank",
        ),
        pytest.param(
            {"FACTORY_STATE": "state"},
            "FACTORY_STATE: is not an absolute path",
            id="state-relative",
        ),
    ],
)
def test_the_stop_of_invalid_settings_falls_back_to_the_given_directory(
    *,
    environment: dict[str, str],
    tmp_path: Path,
    clock: ManualClock,
    monkeypatch: pytest.MonkeyPatch,
    extra: dict[str, str],
    detail: str,
) -> None:
    monkeypatch.chdir(tmp_path)

    status = main(
        {**environment, **extra},
        runner=Runner(),
        state_directory=tmp_path / "fallback",
        clock=clock,
    )

    assert status == 2
    _assert_stop(tmp_path / "fallback", detail)
    assert not (tmp_path / "state").exists()


@pytest.mark.parametrize(
    ("invalid", "state", "raises", "status", "written"),
    [
        pytest.param(False, "{tmp}/state", False, 0, None, id="recorded"),
        pytest.param(False, "{tmp}/state", True, 2, "state", id="runner-fault"),
        pytest.param(False, None, True, 2, "fallback", id="runner-fault-without-state"),
        pytest.param(True, "  {tmp}/state  ", False, 2, "state", id="state-padded"),
    ],
)
def test_the_runner_gets_the_paths_and_its_settings_fault_follows_the_state_variable(
    *,
    environment: dict[str, str],
    tmp_path: Path,
    clock: ManualClock,
    invalid: bool,
    state: str | None,
    raises: bool,
    status: int,
    written: str | None,
) -> None:
    environ = {**environment, "FACTORY_CHECKOUT": str(tmp_path / "repo")}
    if state is not None:
        environ["FACTORY_STATE"] = state.format(tmp=tmp_path)
    if invalid:
        environ["FACTORY_REPOSITORY_URL"] = TWO_REPOSITORIES
    fault = _token_fault(tmp_path)
    runner = Runner(fault if raises else None)

    result = main(environ, runner=runner, state_directory=tmp_path / "fallback", clock=clock)

    assert result == status
    if written is None:
        [settings] = runner.calls
        assert (settings.checkout, settings.state_directory) == (
            tmp_path / "repo",
            tmp_path / "state",
        )
    else:
        detail = REPOSITORY_FAULT if invalid else f"{fault.variable}: {fault.fault}"
        _assert_stop(tmp_path / written, detail)
    if written != "fallback":
        assert not (tmp_path / "fallback").exists()
