"""Both runtimes start their calls directly, without the write guard's wrapper or its files."""

import inspect
import json
import re
from collections.abc import Callable
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from adapters.container_runtime_support import run_folders
from adapters.opencode_stand_in import MODELS, REPLY_EVENTS, write_opencode
from adapters.test_claude_runtime_os_user import REPLY, _sudo_calls, _write_sudo
from confine_support import Layout, run_request, write_script
from factory.adapters import agent_launch, claude_runtime, opencode_runtime
from factory.adapters.agent_launch import LOGIN_PREFIX, LoginFiles, Starters, call_refusal
from factory.adapters.claude_runtime import SWITCHES, ClaudeCodeRuntime
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.application import preflight
from factory.domain.errors import AgentRuntimeError
from factory.entry.wiring import build_boundaries

CONFINE_LINE = "factory-confine: the kernel offers Landlock ABI 2"
SUDO_LINE = "sudo: a password is required"
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SEEN = "seen.json"
RECORDING = """\
import json, os, sys
from pathlib import Path

here = Path(__file__).resolve().parent
state = Path({state!r})
seen = {{"environment": dict(os.environ), "state": sorted(p.name for p in state.iterdir())}}
(here / {seen!r}).write_text(json.dumps(seen), encoding="utf-8")
sys.stdout.write({reply!r})
"""


@pytest.mark.parametrize(
    ("module", "name"),
    [
        *(
            pytest.param(agent_launch, name, id=f"agent-launch-{name}")
            for name in (
                "TEMPORARY_PREFIX",
                "CLEANUP_SCRIPT",
                "CLEANUP_TIME_LIMIT",
                "CONFINE_PREFIX",
                "confined_argv",
                "cleanup_argv",
                "temporary_folder",
                "existing_devices",
                "request_home",
                "run_confinement",
                "device_confinement",
                "cleanup_launch",
            )
        ),
        pytest.param(preflight, "confinement_item", id="preflight-confinement-item"),
        pytest.param(opencode_runtime, "RUNTIME_FOLDERS", id="opencode-runtime-folders"),
        pytest.param(claude_runtime, "CONFIG_VARIABLE", id="claude-config-variable"),
        pytest.param(claude_runtime, "RUNTIME_FOLDER", id="claude-runtime-folder"),
    ],
)
def test_the_wrapper_s_names_are_gone(module: object, name: str) -> None:
    assert not hasattr(module, name)


def test_the_starters_are_sudo_the_login_files_and_the_leftovers_program() -> None:
    assert list(Starters.model_fields) == ["sudo_executable", "login_files", "leftovers"]


@pytest.mark.parametrize(
    ("callable_", "parameter"),
    [
        pytest.param(ClaudeCodeRuntime.__init__, "confine_executable", id="claude-confine"),
        pytest.param(ClaudeCodeRuntime.__init__, "temporary_root", id="claude-temporary-root"),
        pytest.param(OpencodeRuntime.__init__, "confine_executable", id="opencode-confine"),
        pytest.param(OpencodeRuntime.__init__, "temporary_root", id="opencode-temporary-root"),
        pytest.param(OpencodeRuntime.__init__, "runtime_folders", id="opencode-runtime-folders"),
        pytest.param(build_boundaries, "confine_executable", id="wiring-confine"),
    ],
)
def test_no_constructor_takes_the_wrapper_or_its_folders(
    callable_: Callable[..., object], parameter: str
) -> None:
    assert parameter not in inspect.signature(callable_).parameters
    assert not hasattr(ClaudeCodeRuntime, "confine_executable")


def _login_file(layout: Layout) -> Path:
    path = layout.checkout.parent / "claude-login"
    path.write_text("stand-in-login\n", encoding="utf-8")
    path.chmod(0o600)
    return path


def _recording(folder: Path, state: Path, reply: str) -> Path:
    script = RECORDING.format(state=str(state), seen=SEEN, reply=reply)
    return write_script(folder / "agent", script)


def _seen(folder: Path) -> dict[str, object]:
    seen: dict[str, object] = json.loads((folder / SEEN).read_text(encoding="utf-8"))
    return seen


@pytest.mark.parametrize("with_login", [True, False], ids=["login-file", "no-login-file"])
def test_a_claude_call_as_a_user_starts_the_login_words_then_the_call_after_env_i(
    layout: Layout, *, with_login: bool
) -> None:
    executable = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    sudo = _write_sudo(layout.sudo_bin)
    login = _login_file(layout) if with_login else None
    runtime = ClaudeCodeRuntime(
        str(executable), layout.state, sudo_executable=str(sudo), login_file=login
    )

    runtime.run(run_request(layout, os_user="agent"))

    [call] = _sudo_calls(layout.sudo_bin)
    words = call.arguments
    start = words.index("-i") + 1
    while ASSIGNMENT.match(words[start]):
        start += 1
    login_words = agent_launch.login_argv(LoginFiles(subscription=login)) if login else []
    [claude_call] = read_calls(layout.stand_in)
    assert words[start:] == [*login_words, str(executable), *claude_call.arguments]
    assert "--rules" not in words
    assert not any(word.endswith("factory-confine") for word in words)


@pytest.mark.parametrize(
    ("runtime_of", "pattern"),
    [
        pytest.param(
            lambda path, layout: ClaudeCodeRuntime(
                str(_recording(path, layout.state, REPLY)), layout.state
            ),
            "instructions-*.md",
            id="claude",
        ),
        pytest.param(
            lambda path, layout: OpencodeRuntime(
                str(_recording(path, layout.state, REPLY_EVENTS)), layout.state, models=MODELS
            ),
            "opencode-*.json",
            id="opencode",
        ),
    ],
)
def test_a_call_without_a_user_has_no_rules_file_and_makes_no_run_folder(
    layout: Layout,
    runtime_of: Callable[[Path, Layout], ClaudeCodeRuntime | OpencodeRuntime],
    pattern: str,
) -> None:
    layout.state.mkdir(parents=True, exist_ok=True)
    folder = layout.checkout.parent / "recording-bin"
    runtime = runtime_of(folder, layout)
    before = run_folders()

    runtime.run(run_request(layout))

    seen = _seen(folder)
    state = seen["state"]
    assert isinstance(state, list)
    assert len([name for name in state if Path(name).match(pattern)]) == 1
    assert not [name for name in state if Path(name).match("confine-*.json")]
    environment = seen["environment"]
    assert isinstance(environment, dict)
    assert "CLAUDE_CONFIG_DIR" not in environment
    if isinstance(runtime, ClaudeCodeRuntime):
        assert SWITCHES.items() <= environment.items()
    assert run_folders() <= before


def _claude_end(layout: Layout, stderr: str) -> tuple[str | None, str | None]:
    executable = write_stand_in(layout.stand_in, [Step(stderr=stderr, exit_status=1)])
    try:
        result = ClaudeCodeRuntime(str(executable), layout.state).run(run_request(layout))
    except AgentRuntimeError as error:
        return error.detail, None
    return None, result.end_reason


def _opencode_end(layout: Layout, stderr: str) -> tuple[str | None, str | None]:
    layout.state.mkdir(parents=True, exist_ok=True)
    executable = write_opencode(layout.stand_in, [Step(stderr=stderr, exit_status=1)])
    runtime = OpencodeRuntime(str(executable), layout.state, models=MODELS)
    try:
        result = runtime.run(run_request(layout))
    except AgentRuntimeError as error:
        return error.detail, None
    return None, result.end_reason


def _sudo_refused(layout: Layout) -> tuple[str | None, str | None]:
    executable = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    sudo = _write_sudo(layout.sudo_bin, (f"{SUDO_LINE}\n", 1))
    runtime = ClaudeCodeRuntime(str(executable), layout.state, sudo_executable=str(sudo))
    try:
        result = runtime.run(run_request(layout, os_user="agent"))
    except AgentRuntimeError as error:
        return error.detail, None
    return None, result.end_reason


def _login_refused(_: Layout) -> tuple[str | None, str | None]:
    starters = Starters(
        sudo_executable="/usr/bin/sudo",
        login_files=LoginFiles(subscription=Path("/home/agent/.claude-token")),
    )
    refusal = call_refusal(
        f"{LOGIN_PREFIX} cannot be read\n",
        printed=False,
        timed_out=False,
        os_user=None,
        starters=starters,
    )
    return refusal, None


@pytest.mark.parametrize(
    ("end_of", "refusal_words", "end_reason"),
    [
        pytest.param(
            lambda layout: _claude_end(layout, f"{CONFINE_LINE}\n"),
            None,
            "died",
            id="claude-wrapper-line",
        ),
        pytest.param(
            lambda layout: _opencode_end(layout, f"{CONFINE_LINE}\n"),
            None,
            "died",
            id="opencode-wrapper-line",
        ),
        pytest.param(
            lambda _: (
                call_refusal(
                    f"{CONFINE_LINE}\n",
                    printed=False,
                    timed_out=False,
                    os_user="agent",
                    starters=Starters(sudo_executable="/usr/bin/sudo", login_files=LoginFiles()),
                ),
                None,
            ),
            None,
            None,
            id="call-refusal-wrapper-line",
        ),
        pytest.param(
            _sudo_refused,
            lambda layout: [f"{layout.sudo_bin / 'sudo'} refused the agent run: {SUDO_LINE}"],
            None,
            id="sudo-refused",
        ),
        pytest.param(
            _login_refused,
            lambda _: ["/home/agent/.claude-token"],
            None,
            id="login-file-refused",
        ),
        pytest.param(
            lambda layout: _claude_end(layout, f"{SUDO_LINE}\n"),
            None,
            "died",
            id="sudo-line-without-a-user",
        ),
    ],
)
def test_only_sudo_and_the_login_shell_refuse_a_call(
    layout: Layout,
    end_of: Callable[[Layout], tuple[str | None, str | None]],
    refusal_words: Callable[[Layout], list[str]] | None,
    end_reason: str | None,
) -> None:
    refusal, ended = end_of(layout)

    if refusal_words is None:
        assert refusal is None
    else:
        assert refusal is not None
        assert all(word in refusal for word in refusal_words(layout))
    assert ended == end_reason
