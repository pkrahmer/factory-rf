"""The loop of one factory instance, its pauses, and the preparation of its checkout."""

from collections.abc import Callable
from datetime import timedelta

from factory.application.git import Git
from factory.application.machine import FactoryLog
from factory.domain.settings import InstanceSettings

FIRST_PAUSE = timedelta(seconds=15)
MAX_PAUSE = timedelta(seconds=120)


def pause_after(idle_ticks: int) -> timedelta:
    """The pause after an iteration that left `idle_ticks` idle ticks since the last activity."""
    if idle_ticks < 0:
        raise ValueError(f"idle_ticks must not be negative, got {idle_ticks}")
    # Doubling step by step stops at the cap; `FIRST_PAUSE * 2**idle_ticks` overflows
    # timedelta after a long idle stretch.
    pause = FIRST_PAUSE
    for _ in range(idle_ticks):
        if pause >= MAX_PAUSE:
            break
        pause *= 2
    return min(pause, MAX_PAUSE)


class Scheduler:
    """Runs one instance's iterations, prepare then tick, with a pause that follows activity."""

    def __init__(
        self,
        prepare: Callable[[], bool],
        tick: Callable[[], bool],
        sleep: Callable[[float], None],
        should_stop: Callable[[], bool],
        log: FactoryLog,
    ) -> None:
        """Keep the callables of one loop and the log that takes a failed iteration."""
        self._prepare = prepare
        self._tick = tick
        self._sleep = sleep
        self._should_stop = should_stop
        self._log = log

    def run(self) -> None:
        """Repeat iterations until `should_stop` is true; the first runs at once."""
        idle_ticks = 0
        while not self._should_stop():
            if self._iterate():
                idle_ticks = 0
            else:
                idle_ticks += 1
            if self._should_stop():
                return
            self._sleep(pause_after(idle_ticks).total_seconds())

    def _iterate(self) -> bool:
        try:
            return self._prepare() and self._tick()
        except Exception as error:
            self._log.line(f"iteration failed: {type(error).__name__}: {error}")
            return False


class CheckoutPreparer:
    """Clones the instance's checkout when it is missing and leaves an existing one alone."""

    def __init__(self, git: Git, settings: InstanceSettings) -> None:
        """Bind the working copy of the checkout and the settings that name its repository."""
        self._git = git
        self._settings = settings

    def prepare(self) -> bool:
        """Clone the repository unless the checkout already holds a clone; always `True`."""
        if not (self._settings.checkout / ".git").exists():
            self._git.clone(self._settings.repository_url)
        return True
