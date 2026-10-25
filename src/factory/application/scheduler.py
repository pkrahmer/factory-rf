"""The loop of one factory instance, its pauses, and the preparation of its checkout."""

import os
from collections.abc import Callable
from datetime import timedelta

from factory.application.boundaries import Boundaries
from factory.application.git import Git
from factory.application.machine import FactoryLog
from factory.application.stops import StopService
from factory.domain.errors import GitError
from factory.domain.paths import MAIN_BRANCH, PIPELINE_DEFINITION_FILE, REMOTE
from factory.domain.settings import InstanceSettings
from factory.domain.stops import RepositoryStop, RepositoryStopReason

_UNAVAILABLE: RepositoryStopReason = "repository_unavailable"
_ORIGIN_MAIN = f"{REMOTE}/{MAIN_BRANCH}"

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
    """Clones the instance's checkout when it is missing."""

    def __init__(self, git: Git, settings: InstanceSettings, log: FactoryLog | None = None) -> None:
        """Bind the working copy, the settings that name its repository and the log, if any."""
        self._git = git
        self._settings = settings
        self._log = log

    def prepare(self) -> None:
        """Clone when the checkout holds no `.git`; keep any checkout that does."""
        if not os.path.lexists(self._settings.checkout / ".git"):
            self._git.clone(self._settings.repository_url)


class RepositoryWaiter:
    """Prepares the checkout and waits, as a stop, until `origin/main` holds the pipeline."""

    def __init__(
        self, preparer: CheckoutPreparer, boundaries: Boundaries, stops: StopService
    ) -> None:
        """Bind the preparer of the checkout, the boundaries it reads and the stop service."""
        self._preparer = preparer
        self._boundaries = boundaries
        self._stops = stops

    def prepare(self) -> bool:
        """True once the checkout's `origin/main` holds the pipeline definition.

        Otherwise the fault stands as the stop `repository_unavailable` and this is `False`.
        """
        try:
            self._preparer.prepare()
        except GitError as error:
            return self._unavailable(f"cannot prepare the checkout: {error}")
        # A ready checkout is left as it is; only one that is not ready yet fetches.
        fault = self._main_fault()
        if fault is not None:
            fault = self._fault_after_fetch()
        if fault is not None:
            return self._unavailable(fault)
        self._stops.clear_stop(_UNAVAILABLE)
        return True

    def _fault_after_fetch(self) -> str | None:
        try:
            self._boundaries.git.fetch()
        except GitError as error:
            return f"cannot fetch: {error}"
        return self._main_fault()

    def _main_fault(self) -> str | None:
        git = self._boundaries.git
        if git.resolve(_ORIGIN_MAIN) is None:
            return "the repository has no main branch yet"
        if git.show_file(_ORIGIN_MAIN, PIPELINE_DEFINITION_FILE) is None:
            return f"{_ORIGIN_MAIN} has no {PIPELINE_DEFINITION_FILE} yet"
        return None

    def _unavailable(self, detail: str) -> bool:
        standing = self._boundaries.health.read().stops
        # The same fault on every iteration is reported once, as v1 printed each reason once.
        if not any(stop.reason == _UNAVAILABLE and stop.detail == detail for stop in standing):
            stop = RepositoryStop(
                scope="repository",
                reason=_UNAVAILABLE,
                detail=detail,
                at=self._boundaries.clock.now(),
            )
            self._stops.raise_stop(stop)
        return False
