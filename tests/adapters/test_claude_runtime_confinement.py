"""The `claude -p` runtime starts every call through `factory-confine` with the run's rules."""

import json
import tempfile
import time
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from adapters.test_claude_runtime_login import BUDGET_STOP
from adapters.test_claude_runtime_os_user import REPLY, _without_locale
from confine_support import (
    CONFINE,
    LIMIT,
    LINE,
    STAND_IN_TOOL_PATH,
    ConfineCall,
    Layout,
    Played,
    confined_runtime,
    read_records,
    run_request,
    write_confine,
    write_script,
)
from factory.adapters import claude_runtime
from factory.adapters.claude_runtime import (
    CLEANUP_SCRIPT,
    CONFIG_VARIABLE,
    SWITCHES,
    ClaudeCodeRuntime,
)
from factory.domain.confinement import DEVICE_FILES, DEVICE_FOLDERS, Confinement
from factory.domain.errors import AgentRuntimeError
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

SUDO_LINE = "sudo: a password is required"
# Short: the hanging shell it limits need not start to be killed.
SHORT_LIMIT = timedelta(seconds=3)
# The stand-ins wait far longer than any limit here.
WAIT_SECONDS = 30
ELAPSED_BOUND = 20

# An agent that records what it sees of its temporary folder and of the run's rules files,
# then leaves things in that folder, waits and prints as its plan says.
PROBE_SCRIPT = r"""
import json
import os
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parent
plan = json.loads((here / "plan.json").read_text(encoding="utf-8"))
calls = here / "probe-calls.jsonl"
index = len(calls.read_text(encoding="utf-8").splitlines()) if calls.exists() else 0
temporary = os.environ.get("TMPDIR", "")
is_folder = bool(temporary) and Path(temporary).is_dir()
rules = sorted(Path(plan["state"]).glob("confine-*.json"))
record = {
    "arguments": sys.argv[1:],
    "environment": dict(os.environ),
    "temporary_is_folder": is_folder,
    "temporary_listing": sorted(os.listdir(temporary)) if is_folder else [],
    "rules": [path.read_text(encoding="utf-8") for path in rules],
}
with calls.open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
step = plan["steps"][index]
if step["leave_locked_folder"]:
    locked = Path(temporary) / "locked"
    locked.mkdir()
    (locked / "inside.txt").write_text("x", encoding="utf-8")
    locked.chmod(0)
if step["leave_file"]:
    (Path(temporary) / "left.txt").write_text("x", encoding="utf-8")
sys.stdout.flush()
time.sleep(step["wait_seconds"])
sys.stdout.write(step["stdout"])
sys.stdout.flush()
"""

# A `sudo` that records each call, refuses the removal or plays a refusal when told, and
# otherwise runs what follows `--`.
SUDO_SCRIPT = r"""
import json
import os
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
arguments = sys.argv[1:]
record = {
    "arguments": arguments,
    "environment": dict(os.environ),
    "working_directory": os.getcwd(),
}
with (here / "calls.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
plan = json.loads((here / "plan.json").read_text(encoding="utf-8"))
rest = arguments[arguments.index("--") + 1 :]
if plan["refuse_removal"] and rest[0] == "/bin/sh":
    sys.exit(1)
if plan["stderr"]:
    sys.stderr.write(plan["stderr"])
    sys.exit(1)
os.execvp(rest[0], rest)
"""

# A shell that records each call, then lets `/bin/sh` run it.
SHELL_SCRIPT = r"""
import json
import os
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
record = {
    "arguments": sys.argv[1:],
    "environment": dict(os.environ),
    "working_directory": os.getcwd(),
}
with (here / "calls.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
os.execv("/bin/sh", ["/bin/sh", *sys.argv[1:]])
"""

# A shell that waits far longer than the removal's time limit when it is started for the
# removal, and otherwise lets `/bin/sh` run the call.
HANGING_SHELL_SCRIPT = f"""
import os
import sys
import time

if sys.argv[1:4] == ["-c", {CLEANUP_SCRIPT!r}, "factory-cleanup"]:
    time.sleep({WAIT_SECONDS})
os.execv("/bin/sh", ["/bin/sh", *sys.argv[1:]])
"""


class ProbeStep(BaseModel):
    """What the probe agent does on one call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    leave_locked_folder: bool = False
    leave_file: bool = False
    wait_seconds: float = 0
    stdout: str = ""


class ProbeCall(BaseModel):
    """What the probe agent saw on one call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    environment: dict[str, str]
    temporary_is_folder: bool
    temporary_listing: list[str]
    rules: list[str]


class Recorded(BaseModel):
    """One call a recording `sudo` or shell saw: arguments, environment, directory."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    environment: dict[str, str]
    working_directory: Path


def _write_probe(layout: Layout, steps: list[ProbeStep]) -> Path:
    plan = {"state": str(layout.state), "steps": [step.model_dump() for step in steps]}
    layout.stand_in.mkdir(parents=True, exist_ok=True)
    (layout.stand_in / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return write_script(layout.stand_in / "agent", PROBE_SCRIPT)


def _write_sudo(layout: Layout, *, refuse_removal: bool = False, stderr: str = "") -> Path:
    path = write_script(layout.sudo_bin / "sudo", SUDO_SCRIPT)
    plan = {"refuse_removal": refuse_removal, "stderr": stderr}
    (layout.sudo_bin / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return path


def _session(arguments: list[str]) -> str:
    return arguments[arguments.index("--session-id") + 1]


def _session_of_rules(rules_file: str) -> str:
    return Path(rules_file).name.removeprefix("confine-").removesuffix(".json")


def _device_folders() -> list[Path]:
    return [Path(folder) for folder in DEVICE_FOLDERS if Path(folder).exists()]


def _device_files() -> list[Path]:
    return [Path(file) for file in DEVICE_FILES if Path(file).exists()]


def test_without_a_confine_executable_a_call_starts_as_before_and_writes_no_rules(
    layout: Layout,
) -> None:
    agent = _write_probe(layout, [ProbeStep(stdout=REPLY)])
    sudo = _write_sudo(layout)
    runtime = ClaudeCodeRuntime(str(agent), layout.state, sudo_executable=str(sudo))
    request = run_request(layout, os_user="agent")

    runtime.run(request)

    [sudo_call] = read_records(layout.sudo_bin / "calls.jsonl", Recorded)
    [call] = read_records(layout.stand_in / "probe-calls.jsonl", ProbeCall)
    expected = {**request.environment, **SWITCHES}
    count = len(expected)
    head = ["-n", "-u", "agent", "--", "timeout", "--signal=KILL", "30s", "env", "-i"]
    assert runtime.confine_executable is None
    assert sudo_call.arguments[:9] == head
    assert sorted(sudo_call.arguments[9 : 9 + count]) == sorted(
        f"{name}={value}" for name, value in expected.items()
    )
    assert sudo_call.arguments[9 + count :] == [str(agent), *call.arguments]
    assert _without_locale(call.environment) == expected
    assert call.rules == []
    assert list(layout.state.glob("confine-*.json")) == []


def test_a_call_starts_through_the_confine_executable_with_its_rules_file(
    layout: Layout,
) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout)

    result = confined_runtime(layout, claude, str(confine)).run(run_request(layout))

    [call] = read_calls(layout.stand_in)
    [confined] = read_records(layout.confine_bin / "confine-calls.jsonl", ConfineCall)
    rules = layout.state / f"confine-{_session(call.arguments)}.json"
    assert confined.arguments == ["--rules", str(rules), "--", str(claude), *call.arguments]
    assert (result.end_reason, result.decision, result.entry) == ("completed", "doing", "Done.")


def test_with_a_user_sudo_starts_the_confine_executable_after_env_i_with_the_config_folder(
    layout: Layout,
) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout)
    sudo = _write_sudo(layout)

    confined_runtime(layout, claude, str(confine), sudo).run(run_request(layout, os_user="agent"))

    [call] = read_calls(layout.stand_in)
    sudo_call = read_records(layout.sudo_bin / "calls.jsonl", Recorded)[0]
    arguments = sudo_call.arguments
    head = ["-n", "-u", "agent", "--", "timeout", "--signal=KILL", "30s", "env", "-i"]
    start = arguments.index(str(confine))
    rules = layout.state / f"confine-{_session(call.arguments)}.json"
    assert arguments[:9] == head
    assert f"{CONFIG_VARIABLE}={layout.home / '.claude'}" in arguments[9:start]
    assert arguments[start + 1 :] == ["--rules", str(rules), "--", str(claude), *call.arguments]


@pytest.mark.parametrize(
    "refused", [pytest.param(False, id="completed"), pytest.param(True, id="refused")]
)
def test_the_rules_file_holds_the_confinement_while_the_call_runs_and_is_gone_after(
    layout: Layout, *, refused: bool
) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout, Played() if refused else None)
    runtime = confined_runtime(layout, claude, str(confine))

    if refused:
        with pytest.raises(AgentRuntimeError):
            runtime.run(run_request(layout))
    else:
        runtime.run(run_request(layout))

    [confined] = read_records(layout.confine_bin / "confine-calls.jsonl", ConfineCall)
    session = _session_of_rules(confined.arguments[1])
    expected = Confinement(
        folders=[
            layout.checkout / "src",
            layout.stand_in,
            layout.home / ".claude",
            *_device_folders(),
        ],
        files=_device_files(),
        temporary_directory=layout.temporary_root / f"factory-run-{session}",
    )
    assert Confinement.model_validate_json(confined.rules_text) == expected
    assert confined.rules_mode == 0o640
    assert list(layout.state.glob("confine-*.json")) == []


def test_the_rules_hold_the_targets_of_write_and_tool_paths_the_home_s_runtime_folder_and_devices(
    layout: Layout,
) -> None:
    (layout.checkout / "README.md").write_text("# Project\n", encoding="utf-8")
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout)
    request = run_request(
        layout,
        write_paths=("src/*", "README.md", "docs/openapi.json"),
        tool_paths=(".venv/*", "~/.cache/*"),
    )

    confined_runtime(layout, claude, str(confine)).run(request)

    [call] = read_calls(layout.stand_in)
    [confined] = read_records(layout.confine_bin / "confine-calls.jsonl", ConfineCall)
    checkout = layout.checkout
    assert Confinement.model_validate_json(confined.rules_text) == Confinement(
        folders=[
            checkout / "src",
            checkout / "docs",
            checkout / ".venv",
            layout.home / ".cache",
            layout.home / ".claude",
            *_device_folders(),
        ],
        files=[checkout / "README.md", *_device_files()],
        temporary_directory=layout.temporary_root / f"factory-run-{_session(call.arguments)}",
    )


@pytest.mark.parametrize(
    ("target", "end_reason", "written"),
    [
        pytest.param("src/a.txt", "completed", True, id="write-path"),
        pytest.param("other/b.txt", "died", False, id="elsewhere"),
    ],
)
def test_through_the_wrapper_only_a_write_the_rules_allow_is_made(
    layout: Layout, *, target: str, end_reason: str, written: bool
) -> None:
    path = layout.checkout / target
    claude = write_stand_in(layout.stand_in, [Step(writes={str(path): "x\n"}, stdout=REPLY)])

    result = confined_runtime(layout, claude).run(run_request(layout))

    assert result.end_reason == end_reason
    assert path.exists() == written


@pytest.mark.parametrize(
    "with_home", [pytest.param(True, id="home"), pytest.param(False, id="no-home")]
)
def test_the_agent_sees_its_temporary_folder_the_config_folder_and_the_switches(
    layout: Layout, *, with_home: bool
) -> None:
    agent = _write_probe(layout, [ProbeStep(stdout=REPLY)])
    request = run_request(
        layout, tool_paths=(STAND_IN_TOOL_PATH, "~/.cache/*"), with_home=with_home
    )

    confined_runtime(layout, agent).run(request)

    [call] = read_records(layout.stand_in / "probe-calls.jsonl", ProbeCall)
    folder = layout.temporary_root / f"factory-run-{_session(call.arguments)}"
    [rules] = call.rules
    names = {folder.name for folder in Confinement.model_validate_json(rules).folders}
    assert call.environment["TMPDIR"] == str(folder)
    assert call.temporary_is_folder
    expected_config = str(layout.home / ".claude") if with_home else None
    assert call.environment.get(CONFIG_VARIABLE) == expected_config
    assert {name: call.environment.get(name) for name in SWITCHES} == SWITCHES
    assert names & {".claude", ".cache"} == ({".claude", ".cache"} if with_home else set())


def test_a_request_without_guard_settings_is_confined_with_no_path_of_the_checkout(
    layout: Layout,
) -> None:
    claude = write_stand_in(
        layout.home / ".claude" / "stand-in",
        [Step(writes={str(layout.checkout / "c.txt"): "x\n"}, stdout=REPLY)],
    )
    request = run_request(layout).model_copy(update={"guard": None})

    result = confined_runtime(layout, claude).run(request)

    assert result.end_reason == "died"
    assert not (layout.checkout / "c.txt").exists()


@pytest.mark.parametrize(
    ("steps", "time_limit", "end_reason"),
    [
        pytest.param(
            [ProbeStep(leave_locked_folder=True, stdout=REPLY)],
            LIMIT,
            "completed",
            id="locked-subfolder",
        ),
        pytest.param(
            [ProbeStep(leave_file=True, wait_seconds=WAIT_SECONDS)],
            ROOMY_LIMIT,
            "time_limit",
            id="time-limit",
        ),
        pytest.param(
            [ProbeStep(leave_file=True, stdout=BUDGET_STOP), ProbeStep(stdout=REPLY)],
            LIMIT,
            "completed",
            id="budget-and-resume",
        ),
    ],
)
def test_the_temporary_folder_is_empty_at_each_call_and_gone_after_the_run(
    layout: Layout, *, steps: list[ProbeStep], time_limit: timedelta, end_reason: str
) -> None:
    agent = _write_probe(layout, steps)
    started = time.monotonic()

    result = confined_runtime(layout, agent).run(run_request(layout, time_limit=time_limit))

    elapsed = time.monotonic() - started
    calls = read_records(layout.stand_in / "probe-calls.jsonl", ProbeCall)
    assert result.end_reason == end_reason
    assert elapsed < ROOMY_BOUND_SECONDS
    assert len(calls) == len(steps)
    assert len({call.environment["TMPDIR"] for call in calls}) == 1
    assert all(call.temporary_is_folder and call.temporary_listing == [] for call in calls)
    assert list(layout.temporary_root.iterdir()) == []


@pytest.mark.parametrize(
    "removal_fails", [pytest.param(False, id="removed"), pytest.param(True, id="removal-fails")]
)
def test_with_a_user_the_removal_runs_through_sudo_and_its_failure_changes_no_result(
    layout: Layout, *, removal_fails: bool
) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout)
    sudo = _write_sudo(layout, refuse_removal=removal_fails)

    result = confined_runtime(layout, claude, str(confine), sudo).run(
        run_request(layout, os_user="agent")
    )

    [call] = read_calls(layout.stand_in)
    folder = layout.temporary_root / f"factory-run-{_session(call.arguments)}"
    sudo_calls = read_records(layout.sudo_bin / "calls.jsonl", Recorded)
    assert len(sudo_calls) == 2
    assert sudo_calls[-1].arguments == [
        "-n",
        "-u",
        "agent",
        "--",
        "/bin/sh",
        "-c",
        CLEANUP_SCRIPT,
        "factory-cleanup",
        str(folder),
    ]
    assert (result.end_reason, result.decision, result.entry) == ("completed", "doing", "Done.")


@pytest.mark.parametrize(
    "reply", [pytest.param("", id="no-reply"), pytest.param(REPLY, id="reply-after-the-line")]
)
def test_a_wrapper_line_without_a_reply_is_a_runtime_error_and_before_a_reply_is_ignored(
    layout: Layout, *, reply: str
) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout, Played(stdout=reply, exit_status=0 if reply else 1))
    runtime = confined_runtime(layout, claude, str(confine))

    if not reply:
        with pytest.raises(AgentRuntimeError) as raised:
            runtime.run(run_request(layout))
        assert raised.value.detail == f"{confine} refused the agent run: {LINE}"
        return
    result = runtime.run(run_request(layout))

    assert (result.end_reason, result.decision, result.entry) == ("completed", "doing", "Done.")


def test_without_a_temporary_root_the_run_s_folder_lies_in_the_system_temporary_folder(
    layout: Layout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "system-tmp"
    root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(root))
    agent = _write_probe(layout, [ProbeStep(stdout=REPLY)])
    runtime = ClaudeCodeRuntime(str(agent), layout.state, confine_executable=CONFINE)

    runtime.run(run_request(layout))

    [call] = read_records(layout.stand_in / "probe-calls.jsonl", ProbeCall)
    assert call.environment["TMPDIR"] == str(root / f"factory-run-{_session(call.arguments)}")


def test_a_sudo_refusal_is_reported_before_a_wrapper_line(layout: Layout) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout)
    sudo = _write_sudo(layout, stderr=f"{SUDO_LINE}\n{LINE}\n")
    runtime = confined_runtime(layout, claude, str(confine), sudo)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(run_request(layout, os_user="agent"))

    assert raised.value.detail == f"{sudo} refused the agent run: {SUDO_LINE}"


def test_a_wrapper_line_of_a_call_killed_at_its_time_limit_is_a_runtime_error(
    layout: Layout,
) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout, Played(wait_seconds=WAIT_SECONDS, exit_status=0))
    runtime = confined_runtime(layout, claude, str(confine))
    started = time.monotonic()

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(run_request(layout, time_limit=ROOMY_LIMIT))

    assert time.monotonic() - started < ROOMY_BOUND_SECONDS
    assert raised.value.detail == f"{confine} refused the agent run: {LINE}"


@pytest.mark.parametrize(
    "os_user", [pytest.param("agent", id="sudo"), pytest.param(None, id="shell")]
)
def test_the_removal_runs_in_the_working_directory_with_an_empty_environment(
    layout: Layout, monkeypatch: pytest.MonkeyPatch, *, os_user: str | None
) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout)
    sudo = _write_sudo(layout)
    if os_user is None:
        shell = write_script(layout.shell_bin / "sh", SHELL_SCRIPT)
        monkeypatch.setattr(claude_runtime, "SHELL_EXECUTABLE", str(shell))
    request = run_request(layout, os_user=os_user)

    confined_runtime(layout, claude, str(confine), sudo).run(request)

    recorder = layout.sudo_bin if os_user is not None else layout.shell_bin
    removal = read_records(recorder / "calls.jsonl", Recorded)[-1]
    assert CLEANUP_SCRIPT in removal.arguments
    assert removal.working_directory == request.working_directory
    assert _without_locale(removal.environment) == {}


@pytest.mark.parametrize(
    "constant",
    [pytest.param("DEVICE_FOLDERS", id="folders"), pytest.param("DEVICE_FILES", id="files")],
)
def test_the_rules_hold_only_the_device_targets_that_exist(
    layout: Layout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, constant: str
) -> None:
    existing = tmp_path / "device"
    if constant == "DEVICE_FOLDERS":
        existing.mkdir()
    else:
        existing.write_text("", encoding="utf-8")
    monkeypatch.setattr(claude_runtime, constant, (str(existing), str(tmp_path / "missing")))
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout)

    confined_runtime(layout, claude, str(confine)).run(run_request(layout))

    [call] = read_calls(layout.stand_in)
    [confined] = read_records(layout.confine_bin / "confine-calls.jsonl", ConfineCall)
    expected_folders = [existing] if constant == "DEVICE_FOLDERS" else _device_folders()
    expected_files = [existing] if constant == "DEVICE_FILES" else _device_files()
    assert Confinement.model_validate_json(confined.rules_text) == Confinement(
        folders=[
            layout.checkout / "src",
            layout.stand_in,
            layout.home / ".claude",
            *expected_folders,
        ],
        files=expected_files,
        temporary_directory=layout.temporary_root / f"factory-run-{_session(call.arguments)}",
    )


def test_a_removal_that_outlasts_its_time_limit_is_ended_and_changes_no_result(
    layout: Layout, monkeypatch: pytest.MonkeyPatch
) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    confine = write_confine(layout)
    shell = write_script(layout.shell_bin / "sh", HANGING_SHELL_SCRIPT)
    monkeypatch.setattr(claude_runtime, "SHELL_EXECUTABLE", str(shell))
    monkeypatch.setattr(claude_runtime, "CLEANUP_TIME_LIMIT", SHORT_LIMIT)
    started = time.monotonic()

    result = confined_runtime(layout, claude, str(confine)).run(run_request(layout))

    assert time.monotonic() - started < ELAPSED_BOUND
    assert (result.end_reason, result.decision, result.entry) == ("completed", "doing", "Done.")
