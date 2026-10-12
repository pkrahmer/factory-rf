"""Named points where a test can inject a crash into the factory's wrappers."""

from enum import StrEnum


class KillPoint(StrEnum):
    """A place in a wrapper where a test may kill the factory."""

    AGENT_RUN = "agent-run"
    BEFORE_PUSH = "before-push"
    AFTER_POST = "after-post"
    AFTER_PUSH = "after-push"


class InjectedKill(BaseException):
    """The crash an armed kill point raises.

    A `BaseException`, so that no `except Exception` survives it, just as no
    handler survives a real death.
    """

    point: KillPoint

    def __init__(self, point: KillPoint) -> None:
        """Name the point that fired."""
        super().__init__(f"injected kill at {point.value}")
        self.point = point


class KillPoints:
    """The kill points of one factory: inert until a test arms one."""

    def __init__(self) -> None:
        """Start with every point inert and unreached."""
        self._reaches: dict[KillPoint, int] = dict.fromkeys(KillPoint, 0)
        self._passes_left: dict[KillPoint, int] = {}

    def arm(self, point: KillPoint, *, after: int = 0) -> None:
        """Make `point` raise on its reach after the next `after` reaches."""
        if after < 0:
            raise ValueError(f"after must not be negative, got {after}")
        self._passes_left[point] = after

    def reach(self, point: KillPoint) -> None:
        """Count a reach of `point` and raise `InjectedKill` if it fires now."""
        self._reaches[point] += 1
        if point not in self._passes_left:
            return
        if self._passes_left[point] > 0:
            self._passes_left[point] -= 1
            return
        del self._passes_left[point]
        raise InjectedKill(point)

    def reached(self, point: KillPoint) -> int:
        """How often `point` was reached, the raising reach included."""
        return self._reaches[point]
