"""The disk space interface is an abstract base class with its two operations."""

from abc import ABC

from factory.adapters.disk_space import ShutilDiskSpace
from factory.application.machine import DiskSpace


def test_disk_space_is_an_abstract_base_class_with_two_operations_and_one_implementation() -> None:
    assert issubclass(DiskSpace, ABC)
    assert DiskSpace.__abstractmethods__ == frozenset({"free_bytes", "used_bytes"})
    assert issubclass(ShutilDiskSpace, DiskSpace)
