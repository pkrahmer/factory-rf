"""The instance writes an empty health status at its start when the state directory has none."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.errors import SettingsInvalid
from factory.domain.settings import InstanceSettings
from factory.domain.stops import HealthStatus, RepositoryStop
from factory.entry.run import run_instance
from factory.entry.wiring import health_file, health_store
from wiring_support import with_dataset

FETCH_FAILED = RepositoryStop(
    scope="repository",
    reason="fetch_failed",
    detail="remote unreachable",
    at=datetime(2026, 10, 17, 8, 0, tzinfo=UTC),
)


@pytest.fixture
def settings(tmp_path: Path, remote: Path, agent_home: Path) -> InstanceSettings:
    """Return settings on `remote` whose token, checkout, state and agent home lie in `tmp_path`."""
    token_file = tmp_path / "hosting-token"
    token_file.write_text("example-value\n", encoding="utf-8")
    state = tmp_path / "instance-state"
    state.mkdir()
    return with_dataset(
        InstanceSettings(
            repository_url=str(remote),
            instance="factory-1",
            checkout=tmp_path / "instance-checkout",
            state_directory=state,
            agent_home=agent_home,
            claude_executable=str(tmp_path / "no-claude"),
            token_file=token_file,
        ),
        tmp_path,
    )


@pytest.mark.parametrize(
    "before",
    [
        pytest.param(None, id="missing"),
        pytest.param(HealthStatus(stops=[FETCH_FAILED]), id="stop-in-force"),
    ],
)
def test_run_instance_writes_an_empty_health_status_only_when_there_is_none(
    settings: InstanceSettings, hosting: FakeHostingService, before: HealthStatus | None
) -> None:
    if before is not None:
        health_store(settings.state_directory).write(before)

    run_instance(settings, sleep=lambda _seconds: None, should_stop=lambda: True, hosting=hosting)

    assert health_file(settings.state_directory).exists()
    expected = HealthStatus() if before is None else before
    assert health_store(settings.state_directory).read() == expected


def test_run_instance_writes_the_health_file_before_it_reads_the_token_file(
    settings: InstanceSettings, hosting: FakeHostingService, tmp_path: Path
) -> None:
    missing = settings.model_copy(update={"token_file": tmp_path / "no-token"})

    with pytest.raises(SettingsInvalid):
        run_instance(
            missing, sleep=lambda _seconds: None, should_stop=lambda: True, hosting=hosting
        )

    assert health_file(settings.state_directory).exists()


def test_run_instance_on_a_state_directory_that_is_a_file_raises_and_clones_nothing(
    settings: InstanceSettings, hosting: FakeHostingService, tmp_path: Path
) -> None:
    state = tmp_path / "state-file"
    state.write_text("", encoding="utf-8")
    unwritable = settings.model_copy(update={"state_directory": state})

    with pytest.raises(OSError):
        run_instance(
            unwritable, sleep=lambda _seconds: None, should_stop=lambda: False, hosting=hosting
        )

    assert not settings.checkout.exists()
