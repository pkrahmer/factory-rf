"""The fake snapshots the tests use: a folder whose base is a copy of it beside it."""

from factory.adapters.copy_snapshots import CopySnapshots


class FakeSnapshots(CopySnapshots):
    """Snapshots on a folder: the base is a copy of it beside it."""
