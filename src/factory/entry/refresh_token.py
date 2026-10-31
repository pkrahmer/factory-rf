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
from factory.domain.tokens import RETRY_INTERVAL
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
        refresher = _refresher(environ, client_credentials_source if source is None else source)
    except _Invalid as invalid:
        print(f"{_PROGRAM}: {invalid}", file=sys.stderr)
        return _SETTINGS_INVALID
    if arguments.once:
        return _OK if _refresh(refresher) is not None else _FAILED
    with _stop_on_signal() as stop:
        wait = stop.wait if sleep is None else sleep
        while not stop.is_set():
            seconds = _refresh(refresher)
            wait(RETRY_INTERVAL.total_seconds() if seconds is None else seconds)
    return _OK


def _refresher(environ: Mapping[str, str], source: SourceFactory) -> TokenRefresher:
    url, scope, client_id, secret_file, login_file = (
        _variable(environ, name)
        for name in (_URL, _SCOPE, _CLIENT_ID, _CLIENT_CREDENTIAL_FILE, _LOGIN_FILE)
    )
    secret = _secret(Path(secret_file))
    return build_token_refresher(source(url, client_id, secret, scope), Path(login_file))


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


def _refresh(refresher: TokenRefresher) -> float | None:
    try:
        token = refresher.refresh()
    except TokenError as error:
        print(f"{_PROGRAM}: {error}", file=sys.stderr)
        return None
    seconds = refresher.wait_after(token).total_seconds()
    print(f"token refreshed: valid {token.expires_in} s, next in {int(seconds)} s", flush=True)
    return seconds


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
