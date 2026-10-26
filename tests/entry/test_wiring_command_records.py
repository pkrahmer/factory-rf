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
from podman_support import PodmanPlan
from wiring_support import CREDENTIAL, dataset_podman


@pytest.mark.usefixtures("sudo_stand_in")
def test_the_built_project_commands_record_a_run_in_the_state_directory(
    tmp_path: Path, remote: Path, local_settings: InstanceSettings
) -> None:
    checkout = clone(remote, local_settings.checkout)
    (checkout / "Makefile").write_text("lint:\n\t@true\n", encoding="utf-8")
    assert local_settings.workspace is not None
    # The dataset's base holds the checkout the stand-in `zfs` cannot roll back to.
    (local_settings.workspace / "checkout").mkdir()
    dataset_podman(tmp_path.resolve(), PodmanPlan(stdout="lint: green (0 s)\n"))
    boundaries = build_boundaries(local_settings, CREDENTIAL, hosting=FakeHostingService())

    boundaries.project_commands.run("lint", time_limit=timedelta(seconds=30))

    assert isinstance(boundaries.project_commands, RecordingProjectCommands)
    path = local_settings.state_directory / "records" / "project-commands.jsonl"
    records = JsonLinesRecordLog(path, CommandRecord).read()
    assert [(record.command, record.commit, record.status) for record in records] == [
        ("lint", boundaries.git.resolve("HEAD"), "passed")
    ]
