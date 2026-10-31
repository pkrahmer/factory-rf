"""The command that keeps a bearer token for the model API in the login file."""

import argparse
import os
import signal
import sys
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path

from factory.application.tokens import TokenRefresher, TokenSource
from factory.domain.errors import TokenError
from factory.domain.tokens import RETRY_INTERVAL, masked
from factory.entry.inputs import UnreadableInput, read_input
from factory.entry.run import install_stop_handlers
from factory.entry.wiring import build_token_refresher, client_credentials_source

_PROGRAM = "refresh_token"
_OK = 0
_FAILED = 1
_SETTINGS_INVALID = 2

_URL = "FACTORY_TOKEN_URL"
_SCOPE = "FACTORY_TOKEN_SCOPE"
_CLIENT_ID = "FACTORY_TOKEN_CLIENT_ID"
_CLIENT_CREDENTIAL_FILE = "FACTORY_TOKEN_CLIENT_SECRET_FILE"
_LOGIN_FILE = "FACTORY_API_LOGIN_FILE"

SourceFactory = Callable[[str, str, str, str], TokenSource]


class _Invalid(Exception):
    pass


def main(
    argv: Sequence[str] | None = None,
    environ: Mapping[str, str] = os.environ,
    *,
    source: SourceFactory | None = None,
    sleep: Callable[[float], None] | None = None,
) -> int:
    """Refresh the token once with `--once`, else until `SIGTERM` or `SIGINT`; 2 when invalid.

    `source` builds the token source from the URL, client id, client secret and scope, and
    `sleep` waits the given seconds; both default to the real ones.
    """
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.add_argument("--once", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        refreshes = _refreshes(environ, client_credentials_source if source is None else source)
    except _Invalid as invalid:
        print(f"{_PROGRAM}: {invalid}", file=sys.stderr)
        return _SETTINGS_INVALID
    if arguments.once:
        return _OK if refreshes.run() is not None else _FAILED
    with _stop_on_signal() as stop:
        wait = stop.wait if sleep is None else sleep
        while not stop.is_set():
            seconds = refreshes.run()
            wait(RETRY_INTERVAL.total_seconds() if seconds is None else seconds)
    return _OK


class _Refreshes:
    """Refreshes one at a time and prints each outcome, the secret and the last token masked."""

    def __init__(self, refresher: TokenRefresher, secret: str) -> None:
        self._refresher = refresher
        self._secret = secret
        self._issued = ""

    def run(self) -> float | None:
        """Refresh once; the seconds to wait after a success, `None` after a failure."""
        try:
            token = self._refresher.refresh()
        except TokenError as error:
            self._report(str(error))
            return None
        except Exception as error:
            # A fault nobody listed must not end the loop: the next run would find no token.
            self._report(f"{type(error).__name__}: {error}")
            return None
        self._issued = token.value
        seconds = self._refresher.wait_after(token).total_seconds()
        print(f"token refreshed: valid {token.expires_in} s, next in {int(seconds)} s", flush=True)
        return seconds

    def _report(self, message: str) -> None:
        print(f"{_PROGRAM}: {masked(message, [self._secret, self._issued])}", file=sys.stderr)


def _refreshes(environ: Mapping[str, str], source: SourceFactory) -> _Refreshes:
    url, scope, client_id, secret_file, login_file = (
        _variable(environ, name)
        for name in (_URL, _SCOPE, _CLIENT_ID, _CLIENT_CREDENTIAL_FILE, _LOGIN_FILE)
    )
    secret = _secret(Path(secret_file))
    refresher = build_token_refresher(source(url, client_id, secret, scope), Path(login_file))
    return _Refreshes(refresher, secret)


def _variable(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name, "").strip()
    if not value:
        raise _Invalid(f"{name} is not set")
    return value


def _secret(path: Path) -> str:
    try:
        secret = read_input(path).strip()
    except UnreadableInput as error:
        raise _Invalid(f"cannot read {path}") from error
    if not secret:
        raise _Invalid(f"cannot read {path}")
    return secret


@contextmanager
def _stop_on_signal() -> Iterator[threading.Event]:
    signals = (signal.SIGTERM, signal.SIGINT)
    previous = {number: signal.getsignal(number) for number in signals}
    stop = threading.Event()
    install_stop_handlers(stop)
    try:
        yield stop
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


if __name__ == "__main__":
    raise SystemExit(main())
