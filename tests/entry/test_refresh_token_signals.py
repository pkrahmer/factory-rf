"""Tests of the refresher's signal handlers and of the exceptions it lets pass."""

import signal
from pathlib import Path
from types import FrameType

import pytest

from factory.application.tokens import TokenSource
from factory.domain.tokens import Token
from factory.entry.refresh_token import main
from token_support import ISSUED, scripted

pytestmark = pytest.mark.usefixtures("restored_signals")


def own_handler(number: int, frame: FrameType | None) -> None:
    """A handler of the test's own, which `main` must put back."""
    del number, frame


class WatchingSource(TokenSource):
    """Answers with a token and records the `SIGTERM` handler it finds while it fetches."""

    def __init__(self) -> None:
        """Start with no handler seen."""
        self.seen: list[object] = []

    def fetch(self) -> Token:
        """Record the handler and answer."""
        self.seen.append(signal.getsignal(signal.SIGTERM))
        return Token(value=ISSUED, expires_in=3599)


class RaisingSource(TokenSource):
    """Raises the given exception on every fetch."""

    def __init__(self, error: BaseException) -> None:
        """Keep the exception to raise."""
        self.error = error

    def fetch(self) -> Token:
        """Raise the exception."""
        raise self.error


def terminate(seconds: float) -> None:
    """A wait that ends the loop by raising `SIGTERM`."""
    del seconds
    signal.raise_signal(signal.SIGTERM)


def never_sleep(seconds: float) -> None:
    """A wait the run must not reach."""
    raise AssertionError(f"waited {seconds} s")


@pytest.mark.parametrize(
    ("argv", "unset", "status", "watched"),
    [
        pytest.param(["--once"], None, 0, False, id="once"),
        pytest.param([], None, 0, True, id="loop-ended-by-sigterm"),
        pytest.param(["--once"], "FACTORY_TOKEN_URL", 2, False, id="url-unset"),
    ],
)
def test_main_puts_back_the_signal_handlers_it_found(
    environ: dict[str, str], argv: list[str], unset: str | None, status: int, watched: bool
) -> None:
    if unset is not None:
        del environ[unset]
    signal.signal(signal.SIGTERM, own_handler)
    signal.signal(signal.SIGINT, own_handler)
    source = WatchingSource()

    result = main(argv, environ, source=scripted(source), sleep=terminate)

    assert result == status
    assert signal.getsignal(signal.SIGTERM) is own_handler
    assert signal.getsignal(signal.SIGINT) is own_handler
    if watched:
        assert source.seen
        assert all(handler is not own_handler for handler in source.seen)


@pytest.mark.parametrize("argv", [pytest.param(["--once"], id="once"), pytest.param([], id="loop")])
@pytest.mark.parametrize(
    "error",
    [
        pytest.param(KeyboardInterrupt(), id="keyboard-interrupt"),
        pytest.param(SystemExit(3), id="system-exit"),
    ],
)
def test_an_interrupt_or_exit_of_a_refresh_leaves_main_as_raised(
    environ: dict[str, str],
    login_file: Path,
    argv: list[str],
    error: BaseException,
    capsys: pytest.CaptureFixture[str],
) -> None:
    login_file.parent.mkdir()
    login_file.write_text("old-token", encoding="utf-8")

    with pytest.raises(type(error)) as raised:
        main(argv, environ, source=scripted(RaisingSource(error)), sleep=never_sleep)

    assert raised.value is error
    if isinstance(error, SystemExit):
        assert raised.value.code == 3
    assert login_file.read_text(encoding="utf-8") == "old-token"
    assert "refresh_token:" not in capsys.readouterr().err
