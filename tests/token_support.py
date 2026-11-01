"""A token source that answers from a script, and an `open_url` that records its requests."""

import io
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from email.message import Message

from factory.application.tokens import TokenSource
from factory.domain.tokens import Token

ENDPOINT = "https://login.example.invalid/token"
HIDDEN = "s3cret-value"
ISSUED = "tok-abc"


def scripted(source: TokenSource) -> Callable[[str, str, str, str], TokenSource]:
    """A source factory that hands out `source` whatever it is given."""
    return lambda _url, _client_id, _secret, _scope: source


class ScriptedTokenSource(TokenSource):
    """Answers each fetch with the next token of its script, or raises the next error."""

    def __init__(self, *outcomes: Token | Exception) -> None:
        """Keep the answers in the order the fetches receive them."""
        self.outcomes = list(outcomes)
        self.fetches = 0

    def fetch(self) -> Token:
        """Return or raise the next scripted outcome."""
        outcome = self.outcomes[self.fetches]
        self.fetches += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def answer(body: object) -> bytes:
    """The JSON text of a token endpoint's answer."""
    return json.dumps(body).encode()


def http_error(code: int, body: bytes) -> urllib.error.HTTPError:
    """An HTTP error of `code` whose body is `body`."""
    return urllib.error.HTTPError(ENDPOINT, code, "error", Message(), io.BytesIO(body))


class UnreadableBody(io.BytesIO):
    """A response body that fails when it is read."""

    def read(self, size: int | None = -1) -> bytes:
        """Fail as a broken connection does."""
        del size
        raise OSError("connection reset")


def unreadable_http_error(code: int) -> urllib.error.HTTPError:
    """An HTTP error of `code` whose body cannot be read."""
    return urllib.error.HTTPError(ENDPOINT, code, "error", Message(), UnreadableBody())


class RecordingOpener:
    """An `open_url` that records each request and its timeout and answers from a script."""

    def __init__(self, *outcomes: bytes | BaseException) -> None:
        """Keep the bodies to answer with, or the errors to raise, in order."""
        self.outcomes = list(outcomes)
        self.requests: list[urllib.request.Request] = []
        self.timeouts: list[float] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> io.BytesIO:
        """Record the call and answer with the next body, or raise the next error."""
        self.requests.append(request)
        self.timeouts.append(timeout)
        outcome = self.outcomes[len(self.requests) - 1]
        if isinstance(outcome, BaseException):
            raise outcome
        return io.BytesIO(outcome)
