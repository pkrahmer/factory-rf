"""What every agent runtime shares to start its calls: the shell that hands a call its login."""

from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from factory.domain.agent_runs import Login

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
# Run by the call's own shell, as the user the call runs as, so the factory never holds the
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
