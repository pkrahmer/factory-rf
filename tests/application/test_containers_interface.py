"""The container-runs interface: a subclass must implement every operation."""

from collections.abc import Callable, Mapping, Sequence
from datetime import timedelta

import pytest

from factory.application.containers import ContainerRuns
from factory.domain.containers import ContainerLaunch, ContainerResult, Mount


class _Incomplete(ContainerRuns):
    def launch(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerLaunch:
        raise AssertionError((command, mounts, environment, time_limit, working_directory))


class _Complete(_Incomplete):
    def run(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerResult:
        raise AssertionError((command, mounts, environment, time_limit, working_directory))


def test_a_container_runs_subclass_must_implement_every_operation_to_be_constructed() -> None:
    incomplete: Callable[[], object] = _Incomplete
    with pytest.raises(TypeError):
        incomplete()
    assert isinstance(_Complete(), ContainerRuns)
