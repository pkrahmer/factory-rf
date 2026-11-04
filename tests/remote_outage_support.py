"""A remote that a test makes unreachable and reachable again, and the stops of such an outage."""

from pathlib import Path

from factory.domain.stops import RepositoryStop


class RemoteOutage:
    """A remote that can be renamed away, out of reach of every clone, and back."""

    def __init__(self, remote: Path) -> None:
        self.remote = remote
        self.away = remote.with_name("remote-away.git")

    def go_away(self) -> None:
        """Make the remote unreachable."""
        self.remote.rename(self.away)

    def come_back(self) -> None:
        """Make the remote reachable again."""
        self.away.rename(self.remote)


def move_remote_away(remote: Path, tmp_path: Path) -> Path:
    """Rename the remote to a path under `tmp_path` that no clone knows; return that path."""
    moved = tmp_path / "moved.git"
    remote.rename(moved)
    return moved


def fetch_failed(stops: list[RepositoryStop]) -> list[RepositoryStop]:
    """The `fetch_failed` stops among `stops`."""
    return [stop for stop in stops if stop.reason == "fetch_failed"]
