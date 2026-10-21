"""The process of one instance: activity, the stop handlers, the run and `main`."""

import re
import signal
import tempfile
import threading
from collections.abc import Callable, Iterator, Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import factory.entry.run as run_module
from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import DispatchOutcome
from factory.application.tick import Tick, TickOutcome
from factory.domain.agent_runs import AgentRunResult
from factory.domain.disk import DiskRecord
from factory.domain.errors import SettingsInvalid
from factory.domain.events import Event, EventKind
from factory.domain.settings import InstanceSettings, read_settings
from factory.domain.stops import HealthStatus, RepositoryStop
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from factory.entry.run import (
    activity,
    activity_tick,
    install_stop_handlers,
    main,
    run_instance,
    run_until_stopped,
)
from factory.entry.wiring import handler_factory, health_store, read_environment_settings
from git_support import PIPELINE_YAML, install_agents, run_git
from human_clone import HumanClone
from stage_run_support import INSTANCE
from wiring_support import ENVIRONMENT

BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
STORY = """\
# First story

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.

## Journal
"""
STATE = "a" * 40
STAMP = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ "
HOSTED_URL = "https://github.com/example/project.git"
READ_FAULT = "cannot read /run/secrets/hosting-token"
COMPLETED = AgentRunResult(
    end_reason="completed", decision="tests", entry="checked.", duration=timedelta(minutes=1)
)


class Sleeps:
    """Records every pause the loop asks for."""

    def __init__(self) -> None:
        self.seconds: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.seconds.append(seconds)


class Runner:
    """Records the settings it is called with, and raises the error it is given."""

    def __init__(self, error: SettingsInvalid | None = None) -> None:
        self.calls: list[InstanceSettings] = []
        self._error = error

    def __call__(self, settings: InstanceSettings) -> None:
        self.calls.append(settings)
        if self._error is not None:
            raise self._error


class RecordingEvent(threading.Event):
    """An event whose `wait` records its timeout, sets the event and returns at once."""

    def __init__(self) -> None:
        super().__init__()
        self.timeouts: list[float | None] = []

    def wait(self, timeout: float | None = None) -> bool:
        self.timeouts.append(timeout)
        self.set()
        return True


@pytest.fixture
def restored_signals() -> Iterator[None]:
    """Put back the handlers of `SIGTERM` and `SIGINT` the test found."""
    previous = {number: signal.getsignal(number) for number in (signal.SIGTERM, signal.SIGINT)}
    yield
    for number, handler in previous.items():
        signal.signal(number, handler)


@pytest.fixture
def token_file(tmp_path: Path) -> Path:
    """Return a token file in `tmp_path` that holds `example-value`."""
    path = tmp_path / "hosting-token"
    path.write_text("example-value\n", encoding="utf-8")
    return path


@pytest.fixture
def settings(tmp_path: Path, remote: Path, agent_home: Path, token_file: Path) -> InstanceSettings:
    """Return settings on `remote` whose checkout, state and agent home lie in `tmp_path`."""
    state = tmp_path / "instance-state"
    state.mkdir()
    return InstanceSettings(
        repository_url=str(remote),
        instance=INSTANCE,
        checkout=tmp_path / "instance-checkout",
        state_directory=state,
        agent_home=agent_home,
        claude_executable=str(tmp_path / "no-claude"),
        token_file=token_file,
    )


@pytest.fixture
def image_file(tmp_path: Path) -> Path:
    """Return an image identity file in `tmp_path` that holds `build-7`."""
    path = tmp_path / "image-id"
    path.write_text("build-7\n", encoding="utf-8")
    return path


@pytest.fixture
def environment(image_file: Path) -> dict[str, str]:
    """Return a valid environment whose image identity file lies in `tmp_path`."""
    return {
        "FACTORY_REPOSITORY_URL": HOSTED_URL,
        "FACTORY_INSTANCE": INSTANCE,
        "FACTORY_IMAGE_ID_FILE": str(image_file),
    }


def _snapshot() -> WorkItemSnapshot:
    return WorkItemSnapshot(
        id="F0001-S0001",
        path="factory/features/F0001-example/in-progress/F0001-S0001-first.md",
        folder="in-progress",
        branch="work-item/F0001-S0001",
        branch_commit=None,
        document=WorkItemDocument(state=WorkItemState(stage="doing"), body="# First story\n"),
    )


def _event(kind: EventKind) -> Event:
    work_item = None if kind == "idle" else _snapshot()
    return Event(kind=kind, work_item=work_item, remote_state=STATE)


def _outcome(kind: EventKind | None, dispatch: DispatchOutcome | None) -> TickOutcome:
    return TickOutcome(event=None if kind is None else _event(kind), dispatch=dispatch)


def _stop_after(sleeps: Sleeps, count: int) -> Callable[[], bool]:
    return lambda: len(sleeps.seconds) >= count


def _log_lines(state_directory: Path) -> list[str]:
    return (state_directory / "factory.log").read_text(encoding="utf-8").splitlines()


def _main_without_instance(
    environment: Mapping[str, str], state_directory: Path, clock: ManualClock, runner: Runner
) -> int:
    invalid = {name: value for name, value in environment.items() if name != "FACTORY_INSTANCE"}
    return main(invalid, runner=runner, state_directory=state_directory, clock=clock)


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        pytest.param(_outcome("run", "handled"), True, id="handled-run"),
        pytest.param(_outcome("idle", "handled"), False, id="handled-idle"),
        pytest.param(TickOutcome(stopped="fetch_failed"), False, id="repository-stop"),
        pytest.param(_outcome("run", "capped"), False, id="capped"),
        pytest.param(_outcome("run", "error"), False, id="error"),
        pytest.param(_outcome("run", "reported"), False, id="reported"),
    ],
)
def test_only_a_handled_event_that_is_not_idle_counts_as_activity(
    outcome: TickOutcome, *, expected: bool
) -> None:
    assert activity(outcome) is expected


def test_the_activity_tick_keeps_one_tick_and_the_errors_of_both_calls(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    # A write outside the working directory makes each queued run raise inside the handler.
    for _ in range(2):
        agent_runtime.queue(ScriptedRun(writes={"../outside.md": "x"}, result=COMPLETED))
    tick = Tick(boundaries, INSTANCE, handler_factory(boundaries, INSTANCE, ENVIRONMENT))
    serve = activity_tick(tick)

    first = serve()
    second = serve()

    assert (first, second) == (False, False)
    # The first call's claim turns the second call's event into a crash; a fresh tick per call
    # would hold only the crash.
    assert sorted(entry.event_key for entry in tick.status.errors) == [
        "crash:F0001-S0001",
        "run:F0001-S0001",
    ]


def test_run_instance_clones_a_missing_checkout_and_pauses_thirty_seconds_after_it(
    settings: InstanceSettings, hosting: FakeHostingService
) -> None:
    sleeps = Sleeps()

    run_instance(settings, sleep=sleeps, should_stop=_stop_after(sleeps, 1), hosting=hosting)

    assert run_git(settings.checkout, "rev-parse", "--verify", "origin/main")
    assert sleeps.seconds == [30.0]


def test_run_instance_refuses_a_missing_token_file_before_it_clones(
    settings: InstanceSettings, hosting: FakeHostingService, tmp_path: Path
) -> None:
    missing = settings.model_copy(update={"token_file": tmp_path / "no-token"})
    sleeps = Sleeps()

    with pytest.raises(SettingsInvalid) as raised:
        run_instance(missing, sleep=sleeps, should_stop=_stop_after(sleeps, 1), hosting=hosting)

    assert raised.value.variable == "FACTORY_TOKEN_FILE"
    assert not settings.checkout.exists()


def test_run_instance_builds_one_tick_for_the_whole_run(
    settings: InstanceSettings, hosting: FakeHostingService, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = run_module.build_tick
    built: list[Tick] = []

    def recording(boundaries: Boundaries, given: InstanceSettings) -> Tick:
        tick = original(boundaries, given)
        built.append(tick)
        return tick

    monkeypatch.setattr(run_module, "build_tick", recording)
    sleeps = Sleeps()

    run_instance(settings, sleep=sleeps, should_stop=_stop_after(sleeps, 3), hosting=hosting)

    assert len(sleeps.seconds) == 3
    assert len(built) == 1


def test_run_instance_writes_one_start_disk_record_before_it_runs(
    settings: InstanceSettings, hosting: FakeHostingService
) -> None:
    run_instance(settings, sleep=Sleeps(), should_stop=lambda: True, hosting=hosting)

    path = settings.state_directory / "records" / "disk.jsonl"
    [record] = JsonLinesRecordLog(path, DiskRecord).read()
    assert record.occasion == "start"
    assert not settings.checkout.exists()


@pytest.mark.parametrize(
    ("read", "expected"),
    [
        pytest.param(read_environment_settings, Path(tempfile.gettempdir()), id="environment"),
        pytest.param(
            lambda environ: read_settings(environ, read_file=Path.read_text), None, id="settings"
        ),
    ],
)
def test_only_the_environment_settings_name_the_temporary_directory(
    environment: dict[str, str],
    read: Callable[[Mapping[str, str]], InstanceSettings],
    expected: Path | None,
) -> None:
    assert read(environment).temporary_directory == expected


@pytest.mark.usefixtures("restored_signals")
@pytest.mark.parametrize("number", [signal.SIGTERM, signal.SIGINT])
def test_the_stop_handlers_set_the_event_on_sigterm_and_sigint(number: signal.Signals) -> None:
    stop = threading.Event()
    install_stop_handlers(stop)

    signal.raise_signal(number)

    assert stop.is_set()


@pytest.mark.usefixtures("restored_signals")
def test_run_until_stopped_with_its_event_set_returns_and_clones_nothing(
    settings: InstanceSettings, hosting: FakeHostingService
) -> None:
    stop = threading.Event()
    stop.set()

    run_until_stopped(settings, stop, hosting=hosting)

    assert not settings.checkout.exists()


@pytest.mark.usefixtures("restored_signals")
def test_run_until_stopped_installs_its_own_handlers_and_refuses_a_missing_token_file(
    settings: InstanceSettings, tmp_path: Path
) -> None:
    missing = settings.model_copy(update={"token_file": tmp_path / "no-token"})
    before = {number: signal.getsignal(number) for number in (signal.SIGTERM, signal.SIGINT)}

    with pytest.raises(SettingsInvalid) as raised:
        run_until_stopped(missing)

    assert raised.value.variable == "FACTORY_TOKEN_FILE"
    for number, handler in before.items():
        assert signal.getsignal(number) != handler


@pytest.mark.usefixtures("restored_signals")
def test_run_until_stopped_pauses_on_its_stop_event(
    settings: InstanceSettings, hosting: FakeHostingService
) -> None:
    stop = RecordingEvent()

    run_until_stopped(settings, stop, hosting=hosting)

    assert stop.timeouts == [30.0]


def test_main_refuses_an_environment_without_an_instance_with_a_line_and_a_machine_stop(
    environment: dict[str, str], tmp_path: Path, clock: ManualClock
) -> None:
    runner = Runner()

    status = _main_without_instance(environment, tmp_path, clock, runner)

    assert status == 2
    assert runner.calls == []
    [line] = _log_lines(tmp_path)
    assert re.match(STAMP + "settings invalid: FACTORY_INSTANCE", line)
    [stop] = health_store(tmp_path).read().stops
    assert (stop.scope, stop.reason, stop.at) == ("machine", "preflight_failed", clock.now())
    assert "FACTORY_INSTANCE" in stop.detail


@pytest.mark.parametrize("content", [None, ""], ids=["missing", "empty"])
def test_main_refuses_a_missing_or_empty_image_identity_file(
    environment: dict[str, str],
    tmp_path: Path,
    clock: ManualClock,
    content: str | None,
) -> None:
    image = tmp_path / "other-image-id"
    if content is not None:
        image.write_text(content, encoding="utf-8")
    state = tmp_path / "machine"
    state.mkdir()
    runner = Runner()

    status = main(
        {**environment, "FACTORY_IMAGE_ID_FILE": str(image)},
        runner=runner,
        state_directory=state,
        clock=clock,
    )

    assert status == 2
    assert runner.calls == []
    [line] = _log_lines(state)
    assert re.match(STAMP + "settings invalid: FACTORY_IMAGE_ID_FILE", line)


def test_main_hands_the_runner_the_image_identity_of_the_file(
    environment: dict[str, str], tmp_path: Path, clock: ManualClock
) -> None:
    runner = Runner()

    main(environment, runner=runner, state_directory=tmp_path, clock=clock)

    [settings] = runner.calls
    assert settings.image == "build-7"


def test_main_keeps_the_stops_in_force_and_replaces_its_own(
    environment: dict[str, str], tmp_path: Path, clock: ManualClock
) -> None:
    older = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
    fetch = RepositoryStop(
        scope="repository", reason="fetch_failed", detail="remote unreachable", at=older
    )
    previous = RepositoryStop(
        scope="machine", reason="preflight_failed", detail="an older fault", at=older
    )
    health_store(tmp_path).write(HealthStatus(stops=[fetch, previous]))

    _main_without_instance(environment, tmp_path, clock, Runner())

    stops = health_store(tmp_path).read().stops
    assert fetch in stops
    [preflight] = [stop for stop in stops if stop.reason == "preflight_failed"]
    assert "FACTORY_INSTANCE" in preflight.detail


def test_main_without_a_mapping_reads_the_process_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FACTORY_REPOSITORY_URL", HOSTED_URL)
    monkeypatch.delenv("FACTORY_INSTANCE", raising=False)
    runner = Runner()

    status = main(runner=runner, state_directory=tmp_path)

    assert status == 2
    [line] = _log_lines(tmp_path)
    assert re.match(STAMP + r"settings invalid: FACTORY_INSTANCE: \S", line)


def test_main_runs_a_valid_environment_once_and_returns_zero(
    environment: dict[str, str], tmp_path: Path, clock: ManualClock
) -> None:
    runner = Runner()

    status = main(environment, runner=runner, state_directory=tmp_path, clock=clock)

    assert status == 0
    expected = read_settings(environment, read_file=Path.read_text).model_copy(
        update={"temporary_directory": Path(tempfile.gettempdir())}
    )
    assert runner.calls == [expected]


def test_main_turns_a_settings_fault_of_the_runner_into_a_line_and_a_machine_stop(
    environment: dict[str, str], tmp_path: Path, clock: ManualClock
) -> None:
    runner = Runner(SettingsInvalid("FACTORY_TOKEN_FILE", READ_FAULT))

    status = main(environment, runner=runner, state_directory=tmp_path, clock=clock)

    assert status == 2
    [line] = _log_lines(tmp_path)
    assert re.fullmatch(STAMP + f"settings invalid: FACTORY_TOKEN_FILE: {READ_FAULT}", line)
    [stop] = health_store(tmp_path).read().stops
    assert (stop.scope, stop.reason) == ("machine", "preflight_failed")
    assert "FACTORY_TOKEN_FILE" in stop.detail


@pytest.mark.parametrize(
    ("writable", "expected_errors"),
    [
        pytest.param(True, [], id="writable"),
        pytest.param(
            False,
            [
                re.escape("factory-run: settings invalid: FACTORY_INSTANCE: missing"),
                re.escape("factory-run: cannot write the machine stop: ")
                + r"(NotADirectoryError|FileNotFoundError): .+",
            ],
            id="unwritable",
        ),
    ],
)
def test_main_returns_two_for_invalid_settings_whether_or_not_the_stop_can_be_written(
    environment: dict[str, str],
    tmp_path: Path,
    clock: ManualClock,
    capsys: pytest.CaptureFixture[str],
    *,
    writable: bool,
    expected_errors: list[str],
) -> None:
    (tmp_path / "file").write_text("", encoding="utf-8")
    state = tmp_path / "state" if writable else tmp_path / "file" / "state"
    if writable:
        state.mkdir()
    runner = Runner()

    status = _main_without_instance(environment, state, clock, runner)

    assert status == 2
    assert runner.calls == []
    errors = capsys.readouterr().err.splitlines()
    assert len(errors) == len(expected_errors)
    for line, pattern in zip(errors, expected_errors, strict=True):
        assert re.fullmatch(pattern, line)
    if writable:
        [line] = _log_lines(state)
        assert re.match(STAMP + "settings invalid: FACTORY_INSTANCE", line)
        [stop] = health_store(state).read().stops
        assert (stop.scope, stop.reason) == ("machine", "preflight_failed")


def test_main_lets_an_os_error_of_the_runner_out(
    environment: dict[str, str], tmp_path: Path, clock: ManualClock
) -> None:
    def failing(_settings: InstanceSettings) -> None:
        raise OSError("disk gone")

    with pytest.raises(OSError, match="disk gone"):
        main(environment, runner=failing, state_directory=tmp_path, clock=clock)
