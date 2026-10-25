"""What every agent runtime shares: its calls' words, refusals and login, and a run's end."""

import time
from collections.abc import Mapping, Sequence
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, JsonValue

from factory.application.containers import ContainerRuns
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult, Login
from factory.domain.containers import WORK_CHECKOUT, Mount
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import KillPoint, KillPoints

ENTRY_DESCRIPTION = (
    "your journal entry, without its number or your name: "
    "everything your instructions say the entry contains"
)
FINISH_MESSAGE = "Finish now: give your decision (question if the work is not done) and your entry."
MINIMUM_RESUME_BUDGET = Decimal("0.50")
CENT = Decimal("0.01")
VERSION_TIME_LIMIT = timedelta(seconds=30)
# A kill inside a container exits 128 + 9; `subprocess` reports a death by SIGKILL as -9.
KILL_STATUSES = frozenset({137, -9})
# podman's `--timeout` ends the container with 255, not 137 (podman 4.9.3, measured 2026-10-24).
PODMAN_TIMEOUT_STATUS = 255
CONTAINER_KILL_STATUSES = KILL_STATUSES | {PODMAN_TIMEOUT_STATUS}

SHELL_EXECUTABLE = "/bin/sh"
# Claude Code's name for a token made by `claude setup-token`.
LOGIN_VARIABLE = "CLAUDE_CODE_OAUTH_TOKEN"
# The name an Anthropic API key goes by for every runtime that calls the API.
API_LOGIN_VARIABLE = "ANTHROPIC_API_KEY"
LOGIN_PREFIX = "factory-login:"
API_LOGIN_PREFIX = "factory-api-login:"
LOGIN_USED_PREFIX = "factory-login-used:"
API_LOGIN_OPTION = "--api-login"
_SCRIPT_NAME = "factory-login"
# Run by the call's own shell, so the factory never holds the
# key or the token and neither stands in any process's arguments. A key in the API file wins,
# and the token file is not read then. A shell variable cannot hold a zero byte, so the ASCII
# check counts the bytes left once the allowed ones are deleted.
LOGIN_SCRIPT = f"""\
check_text() {{
    if [ ! -f "$2" ] || ! cat -- "$2" >/dev/null 2>&1; then
        printf '%s\\n' "$1 cannot be read" >&2
        exit 1
    fi
    other_bytes=$(LC_ALL=C tr -d '!-~ \\t\\r\\n' <"$2" 2>/dev/null | wc -c)
    if [ $other_bytes -ne 0 ]; then
        printf '%s\\n' "$1 not ASCII text" >&2
        exit 1
    fi
}}
stripped() {{
    LC_ALL=C tr -d ' \\t\\r\\n' <"$1" 2>/dev/null
}}
if [ "$1" = '{API_LOGIN_OPTION}' ]; then
    api_login_file=$2
    shift 2
    if [ -e "$api_login_file" ]; then
        check_text '{API_LOGIN_PREFIX}' "$api_login_file"
        api_login=$(stripped "$api_login_file")
        if [ -n "$api_login" ]; then
            unset {LOGIN_VARIABLE}
            export {API_LOGIN_VARIABLE}="$api_login"
            printf '%s\\n' '{LOGIN_USED_PREFIX} api_key' >&2
            shift
            exec "$@"
        fi
    fi
fi
unset {API_LOGIN_VARIABLE}
login_file=$1
shift
if [ -z "$login_file" ] || [ ! -e "$login_file" ]; then
    unset {LOGIN_VARIABLE}
    printf '%s\\n' '{LOGIN_USED_PREFIX} none' >&2
    exec "$@"
fi
check_text '{LOGIN_PREFIX}' "$login_file"
login=$(stripped "$login_file")
if [ -z "$login" ]; then
    unset {LOGIN_VARIABLE}
    printf '%s\\n' '{LOGIN_USED_PREFIX} none' >&2
    exec "$@"
fi
export {LOGIN_VARIABLE}="$login"
printf '%s\\n' '{LOGIN_USED_PREFIX} subscription' >&2
exec "$@"
"""


class LoginFiles(BaseModel):
    """The files an agent run's shell reads its login from; either may be unset."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subscription: Path | None = None
    api: Path | None = None


def login_argv(files: LoginFiles) -> list[str]:
    """The words that start a call through the login shell; the runtime's command follows them.

    No words when neither file is set.
    """
    if files.subscription is None and files.api is None:
        return []
    subscription = "" if files.subscription is None else str(files.subscription)
    shell = [SHELL_EXECUTABLE, "-c", LOGIN_SCRIPT, _SCRIPT_NAME]
    if files.api is None:
        return [*shell, subscription]
    return [*shell, API_LOGIN_OPTION, str(files.api), subscription]


def login_paths(files: LoginFiles) -> list[Path]:
    """The login files that are set, the subscription file first."""
    return [path for path in (files.subscription, files.api) if path is not None]


def line_starting(stderr: str, prefix: str) -> str | None:
    """The first line of `stderr` that starts with `prefix`, or `None`."""
    for line in stderr.splitlines():
        if line.startswith(prefix):
            return line
    return None


def _rest(line: str, prefix: str) -> str:
    return line.removeprefix(prefix).strip()


def login_used(stderr: str) -> Login | None:
    """The login the shell reported it handed over, or `None` when it reported none it knows."""
    line = line_starting(stderr, LOGIN_USED_PREFIX)
    if line is None:
        return None
    word = _rest(line, LOGIN_USED_PREFIX)
    if word == "api_key":
        return "api_key"
    if word == "subscription":
        return "subscription"
    if word == "none":
        return "none"
    return None


def login_refusal(stderr: str, files: LoginFiles) -> str | None:
    """Why the shell refused a login file, naming the file, or `None` when it refused none."""
    api_line = line_starting(stderr, API_LOGIN_PREFIX)
    if api_line is not None:
        reason = _rest(api_line, API_LOGIN_PREFIX)
        return f"cannot read the agent's API login file {files.api}: {reason}"
    line = line_starting(stderr, LOGIN_PREFIX)
    if line is not None:
        reason = _rest(line, LOGIN_PREFIX)
        return f"cannot read the agent's login file {files.subscription}: {reason}"
    return None


def without_login(environment: Mapping[str, str]) -> dict[str, str]:
    """A copy of `environment` without either login: a run's login comes from its files alone."""
    return {
        name: value
        for name, value in environment.items()
        if name not in (LOGIN_VARIABLE, API_LOGIN_VARIABLE)
    }


class Launch(BaseModel):
    """The words, environment and time limit of one call, before the process module starts it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    argv: list[str]
    # `None`: the process's own environment.
    env: dict[str, str] | None
    time_limit: timedelta


def resume_budget(budget: Decimal) -> Decimal:
    """The budget of a call that resumes a session its budget stopped: a quarter, at least 0.50."""
    quarter = (budget / 4).quantize(CENT, rounding=ROUND_HALF_UP)
    return max(quarter, MINIMUM_RESUME_BUDGET)


def launch(argv: Sequence[str], environment: Mapping[str, str], *, time_limit: timedelta) -> Launch:
    """The call of `argv` with `environment` alone, ended by the factory's own kill at the limit."""
    return Launch(argv=list(argv), env=dict(environment), time_limit=time_limit)


def container_launch(
    containers: ContainerRuns,
    argv: Sequence[str],
    environment: Mapping[str, str],
    *,
    files: Sequence[Path],
    time_limit: timedelta,
) -> Launch:
    """`argv` with `environment` in a container; `files` mounted read-only at their own paths."""
    mounts = [Mount(source=file, target=str(file), read_only=True) for file in dict.fromkeys(files)]
    started = containers.launch(
        argv,
        mounts=mounts,
        environment=environment,
        time_limit=time_limit,
        working_directory=WORK_CHECKOUT,
    )
    return Launch(argv=started.argv, env=started.env, time_limit=started.time_limit)


def version_launch(
    executable: str, *, containers: ContainerRuns | None, time_limit: timedelta
) -> Launch:
    """The call of `<executable> --version`, on the host or in a container."""
    argv = [executable, "--version"]
    if containers is None:
        return Launch(argv=argv, env=None, time_limit=time_limit)
    return container_launch(containers, argv, {}, files=[], time_limit=time_limit)


def killed_at_limit(
    *,
    exit_status: int | None,
    duration: timedelta,
    time_limit: timedelta,
    in_container: bool = False,
) -> bool:
    """Whether a call `in_container` was ended by the container's own kill at the limit.

    A call on the host is ended by the factory's own kill, which the process module reports.
    """
    if not in_container or exit_status not in CONTAINER_KILL_STATUSES:
        return False
    return duration >= time_limit


def first_word(output: str) -> str | None:
    """The first word of the first non-blank line of `output`, or `None`."""
    for line in output.splitlines():
        if line.strip():
            return line.split()[0]
    return None


class Starters(BaseModel):
    """What a runtime starts its calls through: the login files."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    login_files: LoginFiles


def run_environment(
    request: AgentRunRequest, runtime_environment: Mapping[str, str]
) -> dict[str, str]:
    """The environment of a call for `request`: the request's without logins, with the runtime's."""
    # The login comes from the files or not at all, never from the request.
    return {**without_login(request.environment), **runtime_environment}


def run_launch(
    request: AgentRunRequest,
    argv: Sequence[str],
    runtime_environment: Mapping[str, str],
    *,
    time_limit: timedelta,
) -> Launch:
    """The call of a runtime's `argv` for `request`, its environment with `runtime_environment`."""
    return launch(argv, run_environment(request, runtime_environment), time_limit=time_limit)


def call_refusal(stderr: str, *, printed: bool, starters: Starters) -> str | None:
    """Why the login shell refused a call, or `None`.

    `printed` says the call printed a reply the runtime reads; such a call was not refused.
    """
    if printed:
        return None
    return login_refusal(stderr, starters.login_files)


class CallEnd(BaseModel):
    """How a runtime's call ended, as the reading of its end needs it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stderr: str
    printed: bool
    exit_status: int | None
    duration: timedelta
    timed_out: bool


def read_call_end(
    end: CallEnd,
    *,
    time_limit: timedelta,
    starters: Starters,
    in_container: bool = False,
) -> bool:
    """Whether a call ended at its time limit; a call that was refused is `AgentRuntimeError`."""
    # The container's kill ends the call as the factory's own would: read as its time limit.
    timed_out = end.timed_out or killed_at_limit(
        exit_status=end.exit_status,
        duration=end.duration,
        time_limit=time_limit,
        in_container=in_container,
    )
    refusal = call_refusal(end.stderr, printed=end.printed, starters=starters)
    if refusal is not None:
        raise AgentRuntimeError(refusal)
    return timed_out


def state_directory_error(state_directory: Path, error: OSError) -> AgentRuntimeError:
    """The error of a run whose files cannot be written to `state_directory`."""
    return AgentRuntimeError(f"cannot write the state directory {state_directory}: {error}")


def version_printed(executable: str, *, failed: bool, stdout: str, stderr: str) -> str:
    """The version `<executable> --version` printed: the first word of `stdout`.

    A call that `failed` or printed nothing is `AgentRuntimeError`.
    """
    if failed:
        raise AgentRuntimeError(f"{executable} --version failed: {stderr}")
    version = first_word(stdout)
    if version is None:
        raise AgentRuntimeError(f"{executable} --version printed nothing")
    return version


def since(started: float) -> timedelta:
    """The time gone since `started`, a reading of `time.monotonic()`."""
    return timedelta(seconds=time.monotonic() - started)


def finished_run(
    result: AgentRunResult, started: float, kill_points: KillPoints | None
) -> AgentRunResult:
    """`result` with the whole run's duration since `started`, its kill point reached."""
    result = result.model_copy(update={"duration": since(started)})
    if kill_points is not None:
        kill_points.reach(KillPoint.AGENT_RUN)
    return result


def denied_path(tool_input: JsonValue, keys: Sequence[str]) -> str | None:
    """The file a refused call named: the first string at one of `keys` of its `tool_input`."""
    if not isinstance(tool_input, dict):
        return None
    for key in keys:
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return None
