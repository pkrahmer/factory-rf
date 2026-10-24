"""The errors of the snapshot and container tools."""

import pytest

from factory.domain.errors import BoundaryError, ContainerError, FactoryError, SnapshotError


@pytest.mark.parametrize(
    ("error_class", "command", "detail", "message"),
    [
        pytest.param(
            SnapshotError,
            "zfs rollback -r tank/f@base",
            "dataset is busy",
            "snapshot command zfs rollback -r tank/f@base failed: dataset is busy",
            id="snapshot",
        ),
        pytest.param(
            ContainerError,
            "podman",
            "[Errno 2] No such file or directory",
            "container command podman failed: [Errno 2] No such file or directory",
            id="container",
        ),
    ],
)
def test_an_environment_error_names_its_command_and_detail(
    error_class: type[SnapshotError] | type[ContainerError],
    command: str,
    detail: str,
    message: str,
) -> None:
    error = error_class(command, detail)

    assert error.command == command
    assert error.detail == detail
    assert str(error) == message
    assert isinstance(error, BoundaryError)
    assert isinstance(error, FactoryError)
