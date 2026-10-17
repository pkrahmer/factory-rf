"""The wired project commands record every run in the state directory."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.project_commands import RecordingProjectCommands
from factory.domain.command_records import CommandRecord
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from git_support import clone

CREDENTIAL = "example-value"


@pytest.fixture
def settings(tmp_path: Path) -> InstanceSettings:
    """Settings whose checkout, state directory and agent home lie in `tmp_path`."""
    root = tmp_path.resolve()
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=root / "agents-home",
    )


def test_the_built_project_commands_record_a_run_in_the_state_directory(
    remote: Path, settings: InstanceSettings
) -> None:
    checkout = clone(remote, settings.checkout)
    (checkout / "Makefile").write_text("lint:\n\t@true\n", encoding="utf-8")
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    boundaries.project_commands.run("lint", time_limit=timedelta(seconds=30))

    assert isinstance(boundaries.project_commands, RecordingProjectCommands)
    path = settings.state_directory / "records" / "project-commands.jsonl"
    records = JsonLinesRecordLog(path, CommandRecord).read()
    assert [(record.command, record.commit, record.status) for record in records] == [
        ("lint", boundaries.git.resolve("HEAD"), "passed")
    ]
