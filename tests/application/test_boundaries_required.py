"""The boundaries need every collaborator, and the fixture's boundaries carry each feature."""

from collections.abc import Callable
from dataclasses import fields
from pathlib import Path

import pytest

from factory.adapters.clock import ManualWaiter
from factory.application.boundaries import Boundaries
from factory.application.disk_records import DiskRecorder
from factory.domain.disk import DiskRecord, DiskUse

REQUIRED = ("settings", "disk", "disk_records", "stop_records", "waiter", "result_records")


@pytest.mark.parametrize("missing", REQUIRED)
def test_boundaries_without_one_of_the_collaborators_are_refused(
    boundaries: Boundaries, missing: str
) -> None:
    given = {field.name: getattr(boundaries, field.name) for field in fields(boundaries)}
    others = {name: value for name, value in given.items() if name != missing}
    build: Callable[..., Boundaries] = Boundaries

    with pytest.raises(TypeError):
        build(**others)
    assert build(**given) == boundaries


def test_the_fixture_boundaries_carry_every_feature(boundaries: Boundaries, tmp_path: Path) -> None:
    assert boundaries.settings.instance == "factory-1"
    assert boundaries.settings.state_directory == tmp_path / "state"
    assert isinstance(boundaries.waiter, ManualWaiter)

    record = DiskRecorder(boundaries).record("start")

    assert isinstance(record, DiskRecord)
    assert record.folders == [
        DiskUse(path=str(tmp_path), free_bytes=10**12, used_bytes=1),
        DiskUse(path=str(tmp_path / "state"), free_bytes=10**12, used_bytes=1),
    ]
    assert boundaries.disk_records.read() == [record]
