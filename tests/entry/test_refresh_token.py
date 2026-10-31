"""Tests of the command that keeps a bearer token in the login file."""

import os
import signal
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.oauth_token import ClientCredentialsTokenSource
from factory.application.tokens import TokenSource
from factory.domain.errors import TokenError
from factory.domain.tokens import Token
from factory.entry.refresh_token import main
from token_support import (
    ENDPOINT,
    HIDDEN,
    ISSUED,
    RecordingOpener,
    ScriptedTokenSource,
    answer,
    http_error,
)

VARIABLES = [
    "FACTORY_TOKEN_URL",
    "FACTORY_TOKEN_SCOPE",
    "FACTORY_TOKEN_CLIENT_ID",
    "FACTORY_TOKEN_CLIENT_SECRET_FILE",
    "FACTORY_API_LOGIN_FILE",
]


@pytest.fixture
def secret_file(tmp_path: Path) -> Path:
    """The mounted client secret."""
    path = tmp_path / "secret" / "client-secret"
    path.parent.mkdir()
    path.write_text(HIDDEN, encoding="utf-8")
    return path


@pytest.fixture
def login_file(tmp_path: Path) -> Path:
    """The login file the command keeps fresh."""
    return tmp_path / "login" / "api-login"


@pytest.fixture
def environ(secret_file: Path, login_file: Path) -> dict[str, str]:
    """A complete environment of the command."""
    return {
        "FACTORY_TOKEN_URL": ENDPOINT,
        "FACTORY_TOKEN_SCOPE": "api://x/.default",
        "FACTORY_TOKEN_CLIENT_ID": "client-1",
        "FACTORY_TOKEN_CLIENT_SECRET_FILE": str(secret_file),
        "FACTORY_API_LOGIN_FILE": str(login_file),
    }


def scripted(source: TokenSource) -> Callable[[str, str, str, str], TokenSource]:
    """A source factory that hands out `source` whatever it is given."""
    return lambda _url, _client_id, _secret, _scope: source


class SignallingSleep:
    """A wait that records its seconds and the login file, and raises `number` on wait `last`."""

    def __init__(self, login_file: Path, number: signal.Signals, last: int) -> None:
        """Remember the file to read and when to signal."""
        self.login_file = login_file
        self.number = number
        self.last = last
        self.waits: list[tuple[str, float]] = []

    def __call__(self, seconds: float) -> None:
        """Record the wait; on the last one, raise the signal."""
        self.waits.append((self.login_file.read_text(encoding="utf-8"), seconds))
        if len(self.waits) == self.last:
            signal.raise_signal(self.number)


def never_sleep(seconds: float) -> None:
    """A wait the `--once` runs must not reach."""
    raise AssertionError(f"waited {seconds} s")


@pytest.mark.parametrize("value", [pytest.param(None, id="unset"), pytest.param("  ", id="blank")])
@pytest.mark.parametrize("variable", VARIABLES)
def test_a_missing_or_blank_variable_exits_2_naming_it(
    environ: dict[str, str], variable: str, value: str | None, capsys: pytest.CaptureFixture[str]
) -> None:
    if value is None:
        del environ[variable]
    else:
        environ[variable] = value

    status = main(["--once"], environ, source=scripted(ScriptedTokenSource()), sleep=never_sleep)

    assert status == 2
    assert f"refresh_token: {variable} is not set" in capsys.readouterr().err


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(None, id="missing"),
        pytest.param(b"", id="blank"),
        pytest.param(b"\xff\xfe", id="not-utf-8"),
    ],
)
def test_an_unreadable_or_blank_secret_file_exits_2(
    environ: dict[str, str],
    secret_file: Path,
    content: bytes | None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if content is None:
        secret_file.unlink()
    else:
        secret_file.write_bytes(content)

    status = main(["--once"], environ, source=scripted(ScriptedTokenSource()), sleep=never_sleep)

    assert status == 2
    assert f"refresh_token: cannot read {secret_file}" in capsys.readouterr().err


@pytest.mark.usefixtures("restored_signals")
def test_once_writes_the_token_and_names_its_life_and_the_wait(
    environ: dict[str, str], login_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = ScriptedTokenSource(Token(value=ISSUED, expires_in=3599))

    status = main(["--once"], environ, source=scripted(source), sleep=never_sleep)

    assert status == 0
    assert login_file.read_text(encoding="utf-8") == ISSUED
    assert "token refreshed: valid 3599 s, next in 600 s" in capsys.readouterr().out


@pytest.mark.usefixtures("restored_signals")
def test_once_with_a_failing_source_keeps_the_file_and_exits_1(
    environ: dict[str, str], login_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    login_file.parent.mkdir()
    login_file.write_text("old-token", encoding="utf-8")
    source = ScriptedTokenSource(TokenError("HTTP 400: invalid_client"))

    status = main(["--once"], environ, source=scripted(source), sleep=never_sleep)

    assert status == 1
    assert login_file.read_text(encoding="utf-8") == "old-token"
    assert (
        "refresh_token: token request failed: HTTP 400: invalid_client" in capsys.readouterr().err
    )


@pytest.mark.usefixtures("restored_signals")
@pytest.mark.parametrize("number", [signal.SIGTERM, signal.SIGINT])
def test_the_loop_refreshes_after_each_wait_until_a_signal(
    environ: dict[str, str], login_file: Path, number: signal.Signals
) -> None:
    source = ScriptedTokenSource(
        Token(value="tok-1", expires_in=3599), Token(value="tok-2", expires_in=3599)
    )
    sleep = SignallingSleep(login_file, number, last=2)

    status = main([], environ, source=scripted(source), sleep=sleep)

    assert status == 0
    assert source.fetches == 2
    assert sleep.waits == [("tok-1", 600.0), ("tok-2", 600.0)]


@pytest.mark.usefixtures("restored_signals")
@pytest.mark.parametrize("number", [signal.SIGTERM, signal.SIGINT])
def test_the_loop_keeps_the_file_after_a_failure_and_retries_after_a_minute(
    environ: dict[str, str],
    login_file: Path,
    number: signal.Signals,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = ScriptedTokenSource(
        Token(value="tok-1", expires_in=3599),
        TokenError("no route"),
        Token(value="tok-2", expires_in=3599),
    )
    sleep = SignallingSleep(login_file, number, last=3)

    status = main([], environ, source=scripted(source), sleep=sleep)

    assert status == 0
    assert sleep.waits == [("tok-1", 600.0), ("tok-1", 60.0), ("tok-2", 600.0)]
    assert "token request failed: no route" in capsys.readouterr().err


@pytest.mark.usefixtures("restored_signals")
def test_the_secret_and_the_token_appear_in_no_output_error_or_environment(
    environ: dict[str, str], login_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    echo = answer({"error": "invalid_client", "error_description": f"{HIDDEN} {ISSUED}"})
    opener = RecordingOpener(
        answer({"access_token": ISSUED, "expires_in": 3599}), http_error(400, echo)
    )

    def real_source(url: str, client_id: str, secret: str, scope: str) -> TokenSource:
        return ClientCredentialsTokenSource(url, client_id, secret, scope, open_url=opener)

    status = main(
        [], environ, source=real_source, sleep=SignallingSleep(login_file, signal.SIGTERM, last=2)
    )
    direct = ClientCredentialsTokenSource(
        ENDPOINT,
        "client-1",
        HIDDEN,
        "api://x/.default",
        open_url=RecordingOpener(
            answer({"access_token": ISSUED, "expires_in": 3599}), http_error(400, echo)
        ),
    )
    direct.fetch()
    with pytest.raises(TokenError) as raised:
        direct.fetch()

    captured = capsys.readouterr()
    assert status == 0
    assert len(opener.requests) == 2
    assert login_file.read_text(encoding="utf-8") == ISSUED
    for text in [
        captured.out,
        captured.err,
        str(raised.value),
        raised.value.detail,
        *os.environ.values(),
    ]:
        assert HIDDEN not in text
        assert ISSUED not in text
