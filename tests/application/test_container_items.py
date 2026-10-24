"""The preflight items of a container instance: the tools' versions, the dataset, the image."""

from collections.abc import Callable

import pytest

from factory.application.preflight import dataset_item, stage_image_item, tool_version_item
from factory.domain.errors import ContainerError, SnapshotError
from factory.domain.preflight import PreflightItem

DATASET = "tank/factory/vm"
IMAGE = "factory-stage:1"


def _returning[T](value: T) -> Callable[[], T]:
    return lambda: value


def _raising[T](error: Exception, _kind: type[T]) -> Callable[[], T]:
    def answer() -> T:
        raise error

    return answer


@pytest.mark.parametrize(
    ("name", "version", "passed", "detail"),
    [
        pytest.param(
            "podman",
            _returning("podman version 4.9.3"),
            True,
            "podman version 4.9.3",
            id="podman-answers",
        ),
        pytest.param(
            "podman",
            _raising(ContainerError("podman --version", "exit status 127"), str),
            False,
            "podman does not answer --version: "
            "container command podman --version failed: exit status 127",
            id="podman-fails",
        ),
        pytest.param("zfs", _returning("zfs-2.2.2"), True, "zfs-2.2.2", id="zfs-answers"),
        pytest.param(
            "zfs",
            _raising(SnapshotError("zfs --version", "exit status 127"), str),
            False,
            "zfs does not answer --version: snapshot command zfs --version failed: exit status 127",
            id="zfs-fails",
        ),
    ],
)
def test_a_tool_passes_with_its_version_line_or_fails_naming_the_error(
    name: str, version: Callable[[], str], *, passed: bool, detail: str
) -> None:
    item = tool_version_item(name, version)

    assert item == PreflightItem(name=name, passed=passed, detail=detail)


@pytest.mark.parametrize(
    ("exists", "passed", "detail"),
    [
        pytest.param(_returning(True), True, "", id="exists"),
        pytest.param(
            _returning(False),
            False,
            f"the dataset {DATASET} does not exist; make it with zfs create, "
            f"and its base with zfs snapshot {DATASET}@base",
            id="missing",
        ),
        pytest.param(
            _raising(SnapshotError(f"zfs list -H -o name {DATASET}", "permission denied"), bool),
            False,
            f"cannot list the dataset {DATASET}: "
            f"snapshot command zfs list -H -o name {DATASET} failed: permission denied",
            id="cannot-list",
        ),
    ],
)
def test_the_dataset_item_passes_when_the_dataset_exists_and_says_how_to_make_it(
    exists: Callable[[], bool], *, passed: bool, detail: str
) -> None:
    item = dataset_item(DATASET, exists)

    assert item.name == "dataset"
    assert item.passed == passed
    if not passed:
        assert item.detail == detail


@pytest.mark.parametrize(
    ("exists", "passed", "detail"),
    [
        pytest.param(_returning(True), True, "", id="built"),
        pytest.param(
            _returning(False),
            False,
            f"the stage image {IMAGE} is not built; build it with podman build",
            id="not-built",
        ),
        pytest.param(
            _raising(ContainerError(f"podman image exists {IMAGE}", "cannot connect"), bool),
            False,
            f"cannot look for the stage image {IMAGE}: "
            f"container command podman image exists {IMAGE} failed: cannot connect",
            id="cannot-look",
        ),
    ],
)
def test_the_stage_image_item_passes_when_the_image_is_built_and_says_how_to_build_it(
    exists: Callable[[], bool], *, passed: bool, detail: str
) -> None:
    item = stage_image_item(IMAGE, exists)

    assert item.name == "stage-image"
    assert item.passed == passed
    if not passed:
        assert item.detail == detail
