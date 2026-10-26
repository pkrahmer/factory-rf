"""`factory-run` stops at the start without the agent files' folder or the image identity file."""

from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.domain.settings import InstanceSettings
from factory.entry.run import main


class Runner:
    """Records every settings it is called with."""

    def __init__(self) -> None:
        self.calls: list[InstanceSettings] = []

    def __call__(self, settings: InstanceSettings) -> None:
        self.calls.append(settings)


@pytest.mark.parametrize(
    ("left_out", "status", "line"),
    [
        pytest.param(
            "FACTORY_CLAUDE_HOME", 2, "settings invalid: FACTORY_CLAUDE_HOME", id="agent-home"
        ),
        pytest.param(
            "FACTORY_IMAGE_ID_FILE", 2, "settings invalid: FACTORY_IMAGE_ID_FILE", id="image-file"
        ),
        pytest.param(None, 0, None, id="both"),
    ],
)
def test_a_missing_path_setting_is_the_stop_of_invalid_settings(
    environment: dict[str, str],
    tmp_path: Path,
    clock: ManualClock,
    *,
    left_out: str | None,
    status: int,
    line: str | None,
) -> None:
    environ = {name: value for name, value in environment.items() if name != left_out}
    state = tmp_path / "state"
    state.mkdir()
    runner = Runner()

    returned = main(environ, runner=runner, state_directory=state, clock=clock)

    assert returned == status
    log = state / "factory.log"
    if line is None:
        assert len(runner.calls) == 1
    else:
        assert runner.calls == []
        assert any(line in text for text in log.read_text(encoding="utf-8").splitlines())
