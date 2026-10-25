"""The instance's run waits for its repository through the repository waiter."""

from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.settings import InstanceSettings
from factory.entry.run import run_instance
from factory.entry.wiring import health_store
from git_support import run_git
from wiring_support import with_dataset


def test_run_instance_over_a_remote_without_commits_stops_and_pauses_thirty_seconds(
    tmp_path: Path, agent_home: Path, hosting: FakeHostingService
) -> None:
    run_git(tmp_path, "init", "-q", "--bare", "--initial-branch=main", "empty.git")
    token_file = tmp_path / "hosting-token"
    token_file.write_text("example-value\n", encoding="utf-8")
    state = tmp_path / "instance-state"
    state.mkdir()
    settings = with_dataset(
        InstanceSettings(
            repository_url=str(tmp_path / "empty.git"),
            instance="factory-1",
            checkout=tmp_path / "instance-checkout",
            state_directory=state,
            agent_home=agent_home,
            claude_executable=str(tmp_path / "no-claude"),
            token_file=token_file,
        ),
        tmp_path,
    )
    sleeps: list[float] = []

    run_instance(settings, sleep=sleeps.append, should_stop=lambda: bool(sleeps), hosting=hosting)

    stops = health_store(state).read().stops
    assert [(stop.reason, stop.detail) for stop in stops] == [
        ("repository_unavailable", "the repository has no main branch yet")
    ]
    assert sleeps == [30.0]
