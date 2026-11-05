"""The process of one instance: its loop over one tick until a signal stops it."""

import os
import signal
import sys
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import FrameType
from typing import TypedDict, Unpack

from factory.application.boundaries import Boundaries
from factory.application.disk_records import DiskRecorder
from factory.application.hosting import HostingService
from factory.application.idle_shutdown import IdleShutdown
from factory.application.images import Images
from factory.application.machine import Clock
from factory.application.scheduler import CheckoutPreparer, RepositoryWaiter, Scheduler
from factory.application.stops import StopService
from factory.application.tick import Tick, TickOutcome
from factory.domain.stops import HealthStatus, RepositoryStop
from factory.entry.wiring import (
    ImageSizes,
    build_boundaries,
    build_images,
    build_tick,
    chosen_image,
    health_file,
    health_store,
    idle_shutdown_of,
    machine_log,
    machine_stop_exit_of,
    read_environment_settings,
    read_hosting_token,
    stage_file_on_main,
    stage_image_report,
    system_clock,
)
from factory.shared.domain.errors import FetchFailed, MachineStopStood, SettingsInvalid
from factory.shared.domain.settings import STATE_DIRECTORY, InstanceSettings, named_state_directory

__all__ = [
    "activity",
    "activity_tick",
    "build_boundaries",
    "build_tick",
    "idle_shutdown_of",
    "install_stop_handlers",
    "main",
    "run_instance",
    "run_until_stopped",
]

_OK = 0
_MACHINE_STOP_STOOD = 1
_SETTINGS_INVALID = 2


def activity(outcome: TickOutcome) -> bool:
    """True exactly when the tick handled an event that is not `idle`."""
    # A standing stop, a capped event or an error repeats itself on every tick; counting it
    # as activity would hold the pause at its shortest while nothing changes.
    return (
        outcome.dispatch == "handled" and outcome.event is not None and outcome.event.kind != "idle"
    )


def activity_tick(
    tick: Tick, idle: IdleShutdown | None = None, *, fetched: bool = False
) -> Callable[[], bool]:
    """Return the scheduler's tick: run `tick`, the same on every call, and tell its activity.

    Each outcome goes to `idle` first when it is given. With `fetched`, the caller fetches
    before every call, and the tick does not fetch again.
    """

    def run() -> bool:
        outcome = tick.run(fetched=fetched)
        if idle is not None:
            idle.observe(outcome)
        return activity(outcome)

    return run


def _observed_iteration(
    prepare: Callable[[], bool], tick: Callable[[], bool], observe: Callable[[], None]
) -> tuple[Callable[[], bool], Callable[[], bool]]:
    # An iteration ends after its tick, or after a `prepare` that left no tick to run.

    def observed_prepare() -> bool:
        ready = prepare()
        if not ready:
            observe()
        return ready

    def observed_tick() -> bool:
        try:
            return tick()
        finally:
            observe()

    return observed_prepare, observed_tick


def install_stop_handlers(stop: threading.Event) -> None:
    """Make `SIGTERM` and `SIGINT` set `stop`."""

    def handle(_number: int, _frame: FrameType | None) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, handle)
    signal.signal(signal.SIGINT, handle)


def run_until_stopped(
    settings: InstanceSettings,
    stop: threading.Event | None = None,
    *,
    hosting: HostingService | None = None,
) -> None:
    """Run the instance of `settings` until `stop` is set, by a signal or by its owner."""
    event = threading.Event() if stop is None else stop
    install_stop_handlers(event)

    def sleep(seconds: float) -> None:
        event.wait(seconds)

    run_instance(
        settings, sleep=sleep, should_stop=event.is_set, hosting=hosting, request_stop=event.set
    )


class Replacements(TypedDict, total=False):
    """The adapters a caller of `run_instance` puts in place of the production ones."""

    hosting: HostingService | None
    images: Images | None


def run_instance(
    settings: InstanceSettings,
    *,
    sleep: Callable[[float], None],
    should_stop: Callable[[], bool],
    request_stop: Callable[[], None] | None = None,
    **replacements: Unpack[Replacements],
) -> None:
    """Run the instance of `settings` until `should_stop`; `hosting` replaces PyGithub.

    The containers run in the image the project's stage file builds through `images`, podman's
    by default, built again before the next tick when the file on `origin/main` changed; while
    that file stands as a stop, no tick runs. The idle shutdown's `exit` ends
    the loop through `request_stop`, and so does a machine stop that stands too long under that
    setting.

    Raises `SettingsInvalid` when the token file cannot be read, `OSError` when the
    health file cannot be written, and `MachineStopStood` after a machine stop ended the loop.
    """
    _write_an_empty_health_status_when_there_is_none(settings.state_directory)
    token = read_hosting_token(settings.token_file)
    boundaries = replace(
        build_boundaries(settings, token, hosting=replacements.get("hosting")),
        stop_requested=should_stop,
    )
    images = replacements.get("images")
    DiskRecorder(boundaries).record("start")
    preparer = CheckoutPreparer(boundaries.git, settings)
    waiter = RepositoryWaiter(preparer, boundaries, StopService(boundaries))
    start = _ProjectImageStart(
        _StartInputs(
            settings=settings,
            token=token,
            boundaries=boundaries,
            images=build_images(settings) if images is None else images,
            idle=idle_shutdown_of(settings, boundaries, request_stop),
        ),
        waiter,
    )
    prepare, scheduled_tick = start.prepare, start.tick
    machine_stop_exit = machine_stop_exit_of(settings, boundaries, request_stop)
    if machine_stop_exit is not None:
        prepare, scheduled_tick = _observed_iteration(
            prepare, scheduled_tick, machine_stop_exit.observe
        )
    Scheduler(
        prepare=prepare,
        tick=scheduled_tick,
        sleep=sleep,
        should_stop=should_stop,
        log=boundaries.log,
    ).run()
    if machine_stop_exit is not None and machine_stop_exit.ended:
        raise MachineStopStood


@dataclass(frozen=True, kw_only=True)
class _StartInputs:
    settings: InstanceSettings
    token: str
    boundaries: Boundaries
    images: Images
    idle: IdleShutdown | None


class _ProjectImageStart:
    """The instance's tick, in the image the stage file on `origin/main` chose.

    The stage file is compared before every tick, and a tick is built again only when it changed.
    The tick's status lives in memory and counts across ticks until then: a rebuilt tick starts
    its error counts again at zero. A tick that runs keeps its image.
    """

    def __init__(self, inputs: _StartInputs, waiter: RepositoryWaiter) -> None:
        self._inputs = inputs
        self._waiter = waiter
        # None while the stage file stands as a stop, or before the first choice.
        self._tick: Callable[[], bool] | None = None
        self._followed = False
        self._stage_file: str | None = None
        self._in_project_image = False

    def prepare(self) -> bool:
        if not self._waiter.prepare():
            return False
        if not self._follow_main():
            return False
        return self._tick is not None

    def tick(self) -> bool:
        return self._tick is not None and self._tick()

    def _follow_main(self) -> bool:
        boundaries = self._inputs.boundaries
        stops = StopService(boundaries)
        try:
            boundaries.git.fetch()
        except FetchFailed as error:
            # The same stop as the tick's fetch: the health status, not a log line, tells the
            # operator that nothing runs.
            stop = RepositoryStop(
                scope="repository",
                reason="fetch_failed",
                detail=str(error),
                at=boundaries.clock.now(),
            )
            stops.raise_stop(stop)
            return False
        stops.clear_stop("fetch_failed")
        stage_file = stage_file_on_main(boundaries.git)
        # The same file again builds nothing, and one that failed is not tried again.
        if self._followed and stage_file == self._stage_file:
            return True
        at_start = not self._followed
        self._followed = True
        self._stage_file = stage_file
        self._choose(stage_file is not None, at_start=at_start)
        return True

    def _choose(self, has_stage_file: bool, *, at_start: bool) -> None:
        inputs = self._inputs
        boundaries = inputs.boundaries
        report = stage_image_report(boundaries.git, boundaries.log, boundaries.clock)
        # Without a stage file the report only tells the base's size, which the start tells once.
        told = report if has_stage_file or at_start else None
        chosen = chosen_image(
            inputs.settings, boundaries.git, inputs.images, StopService(boundaries), report=told
        )
        if chosen is None:
            self._tick = None
            return
        if self._in_project_image and not has_stage_file:
            report.log.line(f"stage image: back to the base at {report.commit}")
        self._in_project_image = has_stage_file
        built = build_boundaries(
            chosen.settings, inputs.token, hosting=boundaries.hosting, images=inputs.images
        )
        # The tick's preflight must see the factory's own stop, or a probe it cuts off is judged.
        carried = replace(built, stop_requested=boundaries.stop_requested)
        chosen_boundaries = _sized(carried, chosen.sizes)
        # `_follow_main` fetches before every tick and raises or clears `fetch_failed` itself.
        tick = build_tick(chosen_boundaries, chosen.settings)
        self._tick = activity_tick(tick, inputs.idle, fetched=True)


def _sized(boundaries: Boundaries, sizes: ImageSizes | None) -> Boundaries:
    # Measured when the image is chosen, so that no run waits for podman to tell them.
    if sizes is None:
        return boundaries
    return replace(
        boundaries, base_image_bytes=sizes.base_bytes, project_layer_bytes=sizes.layer_bytes
    )


def _write_an_empty_health_status_when_there_is_none(state_directory: Path) -> None:
    # The health check reads a missing file as not healthy; written before anything can fail,
    # it tells a started instance from one that never ran. An existing file keeps its stops.
    if not health_file(state_directory).exists():
        health_store(state_directory).write(HealthStatus())


def main(
    environ: Mapping[str, str] | None = None,
    *,
    runner: Callable[[InstanceSettings], None] | None = None,
    state_directory: Path = STATE_DIRECTORY,
    clock: Clock | None = None,
) -> int:
    """Read the settings, `environ` or the process's, and run the instance; 2 when invalid.

    1 when a machine stop that stood too long in a job ended the instance.

    The stop of invalid settings goes to the state directory the environment names, else to
    `state_directory`.
    """
    run = run_until_stopped if runner is None else runner
    variables = os.environ if environ is None else environ
    try:
        settings = read_environment_settings(variables)
        run(settings)
    except SettingsInvalid as error:
        _report_the_invalid_settings(
            error,
            named_state_directory(variables) or state_directory,
            system_clock() if clock is None else clock,
        )
        return _SETTINGS_INVALID
    except MachineStopStood:
        # The stop's line is already the log's last: a failed execution is the job's signal.
        return _MACHINE_STOP_STOOD
    return _OK


def _report_the_invalid_settings(
    error: SettingsInvalid, state_directory: Path, clock: Clock
) -> None:
    try:
        _stop_the_machine(error, state_directory, clock)
    except OSError as fault:
        # Without a stop on disk, standard error is the operator's only trace of the cause.
        print(f"factory-run: settings invalid: {error}", file=sys.stderr)
        print(
            f"factory-run: cannot write the machine stop: {type(fault).__name__}: {fault}",
            file=sys.stderr,
        )


def _stop_the_machine(error: SettingsInvalid, state_directory: Path, clock: Clock) -> None:
    # No boundaries exist yet, so the stop is written directly; the stops in force stay.
    machine_log(state_directory, clock).line(f"settings invalid: {error}")
    stop = RepositoryStop(
        scope="machine", reason="preflight_failed", detail=str(error), at=clock.now()
    )
    health = health_store(state_directory)
    health.write(health.read().with_stop(stop))


if __name__ == "__main__":
    raise SystemExit(main())
