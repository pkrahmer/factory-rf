"""The login shell hands the run the API file's key, or else the token file's token."""

import json
import os
from collections.abc import Callable
from pathlib import Path

import pytest

from agent_login_support import API_LOGIN, SUBSCRIPTION, _utf_16
from factory.adapters.agent_launch import (
    API_LOGIN_OPTION,
    API_LOGIN_VARIABLE,
    LOGIN_SCRIPT,
    LOGIN_VARIABLE,
    SHELL_EXECUTABLE,
    LoginFiles,
    login_argv,
    login_refusal,
    login_used,
)
from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.domain.agent_runs import Login
from run_layout_support import write_script

SHELL_API_LOGIN = "shell-api-login"
SHELL_SUBSCRIPTION = "shell-login"
SEEN = "seen.json"
RECORDING = f"""
import json
import os
from pathlib import Path

Path(__file__).with_name({SEEN!r}).write_text(json.dumps(dict(os.environ)), encoding="utf-8")
"""


def _missing(_path: Path) -> None:
    pass


def _folder(path: Path) -> None:
    path.mkdir()


def _text(text: str) -> Callable[[Path], None]:
    def make(path: Path) -> None:
        path.write_text(text, encoding="utf-8")

    return make


def _launch(tmp_path: Path, files: LoginFiles) -> tuple[ProcessResult, dict[str, str] | None]:
    command = write_script(tmp_path / "bin" / "command", RECORDING)
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        API_LOGIN_VARIABLE: SHELL_API_LOGIN,
        LOGIN_VARIABLE: SHELL_SUBSCRIPTION,
    }
    result = run_process(
        ProcessRequest(argv=[*login_argv(files), str(command)], cwd=tmp_path, env=environment)
    )
    seen = command.with_name(SEEN)
    if not seen.exists():
        return result, None
    loaded: dict[str, str] = json.loads(seen.read_text(encoding="utf-8"))
    return result, loaded


@pytest.mark.parametrize(
    ("make_api", "make_subscription"),
    [
        pytest.param(_text(f"{API_LOGIN}\n"), _text(f"{SUBSCRIPTION}\n"), id="line-feed"),
        pytest.param(_text(f"{API_LOGIN}\r\n"), _text(f"{SUBSCRIPTION}\n"), id="carriage-return"),
        pytest.param(_text(f"{API_LOGIN}\n"), _folder, id="token-file-a-folder"),
    ],
)
def test_an_api_file_holding_a_key_hands_over_the_key_and_no_token(
    tmp_path: Path,
    *,
    make_api: Callable[[Path], None],
    make_subscription: Callable[[Path], None],
) -> None:
    api, subscription = tmp_path / "api-login", tmp_path / "subscription"
    make_api(api)
    make_subscription(subscription)

    result, seen = _launch(tmp_path, LoginFiles(subscription=subscription, api=api))

    assert result.exit_status == 0
    assert seen is not None
    assert seen[API_LOGIN_VARIABLE] == API_LOGIN
    assert LOGIN_VARIABLE not in seen
    assert "factory-login-used: api_key" in result.stderr.splitlines()
    assert "factory-login:" not in result.stderr


@pytest.mark.parametrize(
    ("make_api", "make_subscription", "subscription_set", "expected", "line"),
    [
        pytest.param(
            _missing, _text(f"{SUBSCRIPTION}\n"), True, SUBSCRIPTION,
            "factory-login-used: subscription", id="api-missing",
        ),
        pytest.param(
            _text(""), _text(f"{SUBSCRIPTION}\n"), True, SUBSCRIPTION,
            "factory-login-used: subscription", id="api-empty",
        ),
        pytest.param(
            _text("  \n"), _text(f"{SUBSCRIPTION}\n"), True, SUBSCRIPTION,
            "factory-login-used: subscription", id="api-blank",
        ),
        pytest.param(
            _text("  \n"), _missing, True, None, "factory-login-used: none", id="no-token-either",
        ),
        pytest.param(
            _text(""), _missing, False, None, "factory-login-used: none",
            id="empty-token-file-argument",
        ),
        pytest.param(
            _missing, _folder, True, None, "factory-login: cannot be read",
            id="token-file-a-folder",
        ),
    ],
)  # fmt: skip
def test_without_a_key_the_shell_goes_on_with_the_token_file(
    tmp_path: Path,
    *,
    make_api: Callable[[Path], None],
    make_subscription: Callable[[Path], None],
    subscription_set: bool,
    expected: str | None,
    line: str,
) -> None:
    api, subscription = tmp_path / "api-login", tmp_path / "subscription"
    make_api(api)
    make_subscription(subscription)
    files = LoginFiles(subscription=subscription if subscription_set else None, api=api)

    result, seen = _launch(tmp_path, files)

    assert line in result.stderr.splitlines()
    if line.startswith("factory-login:"):
        assert result.exit_status == 1
        assert seen is None
        return
    assert result.exit_status == 0
    assert seen is not None
    assert API_LOGIN_VARIABLE not in seen
    assert seen.get(LOGIN_VARIABLE) == expected


@pytest.mark.parametrize(
    ("make_api", "line"),
    [
        pytest.param(_folder, "factory-api-login: cannot be read", id="folder"),
        pytest.param(_utf_16, "factory-api-login: not ASCII text", id="utf-16"),
    ],
)
def test_an_api_file_that_cannot_be_used_stops_the_shell(
    tmp_path: Path, *, make_api: Callable[[Path], None], line: str
) -> None:
    api, subscription = tmp_path / "api-login", tmp_path / "subscription"
    make_api(api)
    subscription.write_text(f"{SUBSCRIPTION}\n", encoding="utf-8")

    result, seen = _launch(tmp_path, LoginFiles(subscription=subscription, api=api))

    assert line in result.stderr.splitlines()
    assert result.exit_status == 1
    assert seen is None


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        pytest.param(LoginFiles(), [], id="neither"),
        pytest.param(
            LoginFiles(subscription=Path("/s")),
            [SHELL_EXECUTABLE, "-c", LOGIN_SCRIPT, "factory-login", "/s"],
            id="subscription-only",
        ),
        pytest.param(
            LoginFiles(api=Path("/a")),
            [SHELL_EXECUTABLE, "-c", LOGIN_SCRIPT, "factory-login", API_LOGIN_OPTION, "/a", ""],
            id="api-only",
        ),
        pytest.param(
            LoginFiles(subscription=Path("/s"), api=Path("/a")),
            [SHELL_EXECUTABLE, "-c", LOGIN_SCRIPT, "factory-login", API_LOGIN_OPTION, "/a", "/s"],
            id="both",
        ),
    ],
)
def test_the_login_words_name_the_files_that_are_set(
    files: LoginFiles, expected: list[str]
) -> None:
    assert login_argv(files) == expected
    assert API_LOGIN_OPTION == "--api-login"


@pytest.mark.parametrize(
    ("stderr", "expected"),
    [
        pytest.param("factory-login-used: api_key\n", "api_key", id="api-key"),
        pytest.param("factory-login-used: subscription\n", "subscription", id="subscription"),
        pytest.param("warning\nfactory-login-used: none \n", "none", id="none"),
        pytest.param(
            "factory-login-used: subscription\nfactory-login-used: api_key\n",
            "subscription",
            id="first-line",
        ),
        pytest.param("warning\n", None, id="no-line"),
        pytest.param("factory-login-used: other\n", None, id="other"),
    ],
)
def test_the_login_used_is_read_from_the_shell_s_report(
    stderr: str, expected: Login | None
) -> None:
    assert login_used(stderr) == expected


FILES = LoginFiles(subscription=Path("/home/agent/.claude-token"), api=Path("/home/agent/.api"))
API_TEXT = "cannot read the agent's API login file /home/agent/.api: not ASCII text"
SUBSCRIPTION_TEXT = "cannot read the agent's login file /home/agent/.claude-token: cannot be read"


@pytest.mark.parametrize(
    ("stderr", "expected"),
    [
        pytest.param("factory-api-login: not ASCII text\n", API_TEXT, id="api"),
        pytest.param("factory-login: cannot be read\n", SUBSCRIPTION_TEXT, id="subscription"),
        pytest.param(
            "factory-api-login: not ASCII text\nfactory-login: cannot be read\n",
            API_TEXT,
            id="api-first",
        ),
        pytest.param(
            "factory-login: cannot be read\nfactory-api-login: not ASCII text\n",
            API_TEXT,
            id="api-second",
        ),
        pytest.param("factory-login-used: none\n", None, id="report-only"),
    ],
)
def test_the_refusal_names_the_file_the_shell_could_not_use(
    stderr: str, expected: str | None
) -> None:
    assert login_refusal(stderr, FILES) == expected
