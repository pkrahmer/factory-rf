"""The leftovers program: its arguments, its refusals, its rounds and its faults."""

import io
import os
import pwd
import signal
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, run_process
from factory.domain.leftovers import Identity
from factory.domain.sessions import ProcessEntry
from factory.entry.leftovers import main

AGENT = Identity(uid=1001, user="agent", pid=11)
USAGE_LINE = "factory-leftovers: usage: python -m factory.entry.leftovers --user <name>\n"


def _entry(pid: int, uid: int = 1001, *, ended: bool = False) -> ProcessEntry:
    return ProcessEntry(pid=pid, session=pid, ended=ended, uid=uid)


@dataclass
class Recorder:
    """The injected calls of `main`, each recording how it was called."""

    identity_value: Identity = AGENT
    tables: list[list[ProcessEntry]] = field(default_factory=list)
    kill_error: OSError | None = None
    processes_error: Exception | None = None
    identities: int = 0
    kills: list[int] = field(default_factory=list)
    listings: int = 0
    pauses: list[float] = field(default_factory=list)
    stderr: io.StringIO = field(default_factory=io.StringIO)

    def identity(self) -> Identity:
        self.identities += 1
        return self.identity_value

    def kill(self, signal_number: int) -> None:
        self.kills.append(signal_number)
        if self.kill_error is not None:
            raise self.kill_error

    def processes(self) -> list[ProcessEntry]:
        self.listings += 1
        if self.processes_error is not None:
            raise self.processes_error
        return self.tables.pop(0) if self.tables else []

    def sleep(self, seconds: float) -> None:
        self.pauses.append(seconds)

    def run(self, argv: list[str]) -> int:
        return main(
            argv,
            stderr=self.stderr,
            identity=self.identity,
            kill=self.kill,
            processes=self.processes,
            sleep=self.sleep,
        )


@pytest.mark.parametrize(
    "argv",
    [
        pytest.param([], id="none"),
        pytest.param(["--user"], id="no-name"),
        pytest.param(["--user", ""], id="empty-name"),
        pytest.param(["--name", "agent"], id="other-option"),
        pytest.param(["--user", "agent", "extra"], id="extra"),
        pytest.param(["agent"], id="name-only"),
    ],
)
def test_wrong_arguments_print_the_usage(argv: list[str]) -> None:
    recorder = Recorder()

    status = recorder.run(argv)

    assert status == 1
    assert recorder.stderr.getvalue() == USAGE_LINE
    assert recorder.identities == 0
    assert recorder.kills == []


def test_the_user_s_name_starts_the_rounds() -> None:
    recorder = Recorder()

    status = recorder.run(["--user", "agent"])

    assert status == 0
    assert recorder.stderr.getvalue() == ""
    assert recorder.kills == [signal.SIGKILL]


@pytest.mark.parametrize(
    ("identity", "user", "expected"),
    [
        pytest.param(
            Identity(uid=0, user="root", pid=11),
            "root",
            "factory-leftovers: refuses to run as root\n",
            id="root",
        ),
        pytest.param(
            AGENT, "factory", "factory-leftovers: runs as agent, not factory\n", id="other"
        ),
    ],
)
def test_refusals_come_before_the_first_signal(
    identity: Identity, user: str, expected: str
) -> None:
    recorder = Recorder(identity_value=identity)

    status = recorder.run(["--user", user])

    assert status == 1
    assert recorder.stderr.getvalue() == expected
    assert recorder.kills == []
    assert recorder.listings == 0
    assert recorder.pauses == []


@pytest.mark.parametrize(
    ("tables", "status", "kills", "pauses", "written"),
    [
        pytest.param([[]], 0, 1, 0, "", id="none-after-round-1"),
        pytest.param([[_entry(7)], []], 0, 2, 1, "", id="none-after-round-2"),
        pytest.param([[_entry(7)]] * 49 + [[]], 0, 50, 49, "", id="none-after-round-50"),
        pytest.param(
            [[_entry(7), _entry(10)]] * 50,
            1,
            50,
            49,
            "factory-leftovers: 2 processes left after 50 rounds: 7, 10\n",
            id="left-after-round-50",
        ),
        pytest.param(
            [[_entry(11), _entry(8, ended=True), _entry(9, uid=1000)]],
            0,
            1,
            0,
            "",
            id="only-own-zombie-and-other-user",
        ),
    ],
)
def test_rounds_signal_until_none_is_left(
    tables: list[list[ProcessEntry]], status: int, kills: int, pauses: int, written: str
) -> None:
    recorder = Recorder(tables=list(tables))

    result = recorder.run(["--user", "agent"])

    assert result == status
    assert recorder.kills == [signal.SIGKILL] * kills
    assert recorder.pauses == [0.1] * pauses
    assert recorder.stderr.getvalue() == written


@pytest.mark.parametrize(
    ("make", "written", "kills", "listings"),
    [
        pytest.param(
            lambda: Recorder(kill_error=PermissionError(1, "Operation not permitted")),
            "factory-leftovers: cannot signal the processes: [Errno 1] Operation not permitted\n",
            1,
            0,
            id="kill",
        ),
        pytest.param(
            lambda: Recorder(processes_error=OSError("no table")),
            "factory-leftovers: cannot list the processes: no table\n",
            1,
            1,
            id="list-os-error",
        ),
        pytest.param(
            lambda: Recorder(processes_error=ValueError("too few fields in the status line of 5")),
            "factory-leftovers: cannot list the processes:"
            " too few fields in the status line of 5\n",
            1,
            1,
            id="list-value-error",
        ),
    ],
)
def test_faults_of_signal_and_listing_end_the_program(
    make: Callable[[], Recorder], written: str, kills: int, listings: int
) -> None:
    recorder = make()

    status = recorder.run(["--user", "agent"])

    assert status == 1
    assert recorder.stderr.getvalue() == written
    assert len(recorder.kills) == kills
    assert recorder.listings == listings


def _refusal_line() -> str:
    if os.getuid() == 0:
        return "factory-leftovers: refuses to run as root\n"
    user = pwd.getpwuid(os.getuid()).pw_name
    return f"factory-leftovers: runs as {user}, not factory-test-nobody\n"


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        pytest.param(["--user", "factory-test-nobody"], _refusal_line, id="another-user"),
        pytest.param([], lambda: USAGE_LINE, id="no-arguments"),
    ],
)
def test_the_real_module_refuses_in_a_child_process(
    tmp_path: Path, arguments: list[str], expected: Callable[[], str]
) -> None:
    argv = [sys.executable, "-I", "-B", "-m", "factory.entry.leftovers", *arguments]

    result = run_process(ProcessRequest(argv=argv, cwd=tmp_path))

    assert result.exit_status == 1
    assert result.stdout == ""
    assert result.stderr == expected()
