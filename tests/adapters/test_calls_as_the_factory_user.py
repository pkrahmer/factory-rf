"""A call without a container runs as the factory's own user: no `sudo`, no `env -i`."""

import json
import os
from collections.abc import Callable, Iterator
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, write_stand_in
from adapters.opencode_stand_in import MODELS, REPLY, REPLY_EVENTS, write_opencode
from confine_support import Layout, run_request, write_script
from factory.adapters import claude_runtime, opencode_runtime
from factory.adapters.agent_launch import (
    API_LOGIN_VARIABLE,
    LOGIN_VARIABLE,
    SHELL_EXECUTABLE,
    Launch,
    LoginFiles,
    Starters,
    call_refusal,
    killed_at_limit,
    launch,
)
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.opencode_runtime import CONFIG_VARIABLE, OpencodeRuntime
from factory.adapters.process import ProcessRequest, ProcessResult, Stream, run_streaming
from run_process_recorder import Recorder

LIMIT = timedelta(seconds=30)
STARTERS_WORDS = {"sudo", "/usr/bin/sudo", "env", "-i"}
CLAUDE_REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "total_cost_usd": 0.1,
        "duration_ms": 100,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
        "structured_output": {"decision": "doing", "entry": "Done."},
    }
)
MODES = "modes.json"
# Writes the mode of every file in the state folder that the runtime made for this call.
MODE_RECORDING = """\
import json, sys
from pathlib import Path

here = Path(__file__).resolve().parent
state = Path({state!r})
modes = {{p.name: p.stat().st_mode & 0o777 for p in state.iterdir() if p.match({pattern!r})}}
(here / {modes!r}).write_text(json.dumps(modes), encoding="utf-8")
sys.stdout.write({reply!r})
"""


def _login_file(layout: Layout) -> Path:
    path = layout.checkout.parent / "login"
    path.write_text("stand-in-login\n", encoding="utf-8")
    path.chmod(0o600)
    return path


def _claude(layout: Layout, login: Path | None) -> ClaudeCodeRuntime:
    executable = write_stand_in(layout.stand_in, [Step(stdout=CLAUDE_REPLY)])
    return ClaudeCodeRuntime(str(executable), layout.state, login_file=login)


def _opencode(layout: Layout, login: Path | None) -> OpencodeRuntime:
    executable = write_opencode(layout.stand_in, [REPLY])
    return OpencodeRuntime(str(executable), layout.state, models=MODELS, api_login_file=login)


def _recorded(monkeypatch: pytest.MonkeyPatch) -> Recorder:
    recorder = Recorder()
    monkeypatch.setattr(claude_runtime, "run_process", recorder)
    monkeypatch.setattr(opencode_runtime, "run_process", recorder)

    def streaming(request: ProcessRequest, on_line: Callable[[Stream, str], bool]) -> ProcessResult:
        recorder.requests.append(request)
        return run_streaming(request, on_line)

    monkeypatch.setattr(opencode_runtime, "run_streaming", streaming)
    return recorder


@pytest.mark.parametrize(
    ("runtime_of", "executable_name", "own_entries"),
    [
        pytest.param(_claude, "claude", claude_runtime.SWITCHES, id="claude"),
        pytest.param(_opencode, "opencode", opencode_runtime.SWITCHES, id="opencode"),
    ],
)
@pytest.mark.parametrize("with_login", [True, False], ids=["login-file", "no-login-file"])
def test_a_call_without_a_container_starts_the_runtime_itself_with_the_request_s_environment(
    layout: Layout,
    monkeypatch: pytest.MonkeyPatch,
    *,
    runtime_of: Callable[[Layout, Path | None], ClaudeCodeRuntime | OpencodeRuntime],
    executable_name: str,
    own_entries: dict[str, str],
    with_login: bool,
) -> None:
    layout.state.mkdir(parents=True, exist_ok=True)
    recorder = _recorded(monkeypatch)
    runtime = runtime_of(layout, _login_file(layout) if with_login else None)
    given = {
        "HOME": str(layout.home),
        "LANG": "C.UTF-8",
        LOGIN_VARIABLE: "t",
        API_LOGIN_VARIABLE: "k",
    }
    request = run_request(layout).model_copy(update={"environment": given})

    runtime.run(request)

    calls = [call for call in recorder.requests if "--version" not in call.argv]
    assert calls
    call = calls[0]
    if with_login:
        assert call.argv[0] == SHELL_EXECUTABLE
    else:
        assert Path(call.argv[0]).name == executable_name
    assert not STARTERS_WORDS & set(call.argv)
    assert call.env is not None
    environment = dict(call.env)
    if executable_name == "opencode":
        assert Path(environment.pop(CONFIG_VARIABLE)).parent == layout.state
    expected = {"HOME": str(layout.home), "LANG": "C.UTF-8", **own_entries}
    assert environment == expected
    assert (
        call_refusal(
            "sudo: a password is required\n",
            printed=False,
            starters=Starters(login_files=LoginFiles()),
        )
        is None
    )


def test_launch_hands_over_the_call_its_environment_and_its_limit() -> None:
    assert launch(["x"], {"A": "1"}, time_limit=LIMIT) == Launch(
        argv=["x"], env={"A": "1"}, time_limit=LIMIT
    )


@pytest.mark.parametrize(
    ("in_container", "exit_status", "duration", "killed"),
    [
        pytest.param(True, 137, LIMIT, True, id="container-137-at-limit"),
        pytest.param(True, -9, LIMIT, True, id="container-minus-9-at-limit"),
        pytest.param(True, 255, LIMIT, True, id="container-255-at-limit"),
        pytest.param(True, 255, timedelta(seconds=29.9), False, id="container-255-before-limit"),
        pytest.param(True, 1, LIMIT, False, id="container-1-at-limit"),
        pytest.param(False, 137, LIMIT, False, id="host-137-at-limit"),
    ],
)
def test_only_a_container_call_is_read_as_killed_at_its_limit(
    *, in_container: bool, exit_status: int, duration: timedelta, killed: bool
) -> None:
    assert (
        killed_at_limit(
            exit_status=exit_status,
            duration=duration,
            time_limit=LIMIT,
            in_container=in_container,
        )
        is killed
    )


@pytest.fixture
def umask_of(request: pytest.FixtureRequest) -> Iterator[int]:
    """Run the test under the umask its parameter names and restore the previous one."""
    mask: int = request.param
    previous = os.umask(mask)
    yield mask
    os.umask(previous)


def _mode_recording(folder: Path, state: Path, pattern: str, reply: str) -> Path:
    script = MODE_RECORDING.format(state=str(state), pattern=pattern, modes=MODES, reply=reply)
    return write_script(folder / "agent", script)


@pytest.mark.parametrize("umask_of", [0o077, 0o022], ids=["umask-077", "umask-022"], indirect=True)
@pytest.mark.parametrize(
    ("runtime_of", "pattern"),
    [
        pytest.param(
            lambda path, layout: ClaudeCodeRuntime(
                str(_mode_recording(path, layout.state, "instructions-*.md", CLAUDE_REPLY)),
                layout.state,
            ),
            "instructions-*.md",
            id="claude",
        ),
        pytest.param(
            lambda path, layout: OpencodeRuntime(
                str(_mode_recording(path, layout.state, "opencode-*.json", REPLY_EVENTS)),
                layout.state,
                models=MODELS,
            ),
            "opencode-*.json",
            id="opencode",
        ),
    ],
)
def test_the_run_files_keep_the_mode_the_umask_gives(
    layout: Layout,
    umask_of: int,
    runtime_of: Callable[[Path, Layout], ClaudeCodeRuntime | OpencodeRuntime],
    pattern: str,
) -> None:
    layout.state.mkdir(parents=True, exist_ok=True)
    folder = layout.checkout.parent / "recording-bin"
    runtime = runtime_of(folder, layout)

    runtime.run(run_request(layout))

    modes: dict[str, int] = json.loads((folder / MODES).read_text(encoding="utf-8"))
    assert len(modes) == 1, pattern
    assert list(modes.values()) == [0o666 & ~umask_of]
