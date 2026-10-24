"""The snapshots interface: a subclass must implement every operation."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.application.snapshots import Snapshots
from factory.domain.git import ChangedPath


class _Incomplete(Snapshots):
    @property
    def mount_point(self) -> Path:
        return Path("/srv/dataset")

    def reset(self) -> None:
        raise AssertionError

    def advance(self) -> None:
        raise AssertionError


class _Complete(_Incomplete):
    def changed_paths(self) -> list[ChangedPath]:
        return []


def test_a_snapshots_subclass_must_implement_every_operation_to_be_constructed() -> None:
    incomplete: Callable[[], object] = _Incomplete
    with pytest.raises(TypeError):
        incomplete()
    assert isinstance(_Complete(), Snapshots)
