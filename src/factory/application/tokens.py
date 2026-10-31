"""Fetching a bearer token and keeping it in the login file."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

from factory.domain.errors import TokenError
from factory.domain.tokens import Token, refresh_wait


class TokenSource(ABC):
    """Where a bearer token comes from."""

    @abstractmethod
    def fetch(self) -> Token:
        """Request a new token; raises `TokenError`."""


class TokenRefresher:
    """Writes each token its source gives out into one login file."""

    def __init__(
        self, source: TokenSource, target: Path, write: Callable[[Path, str], None]
    ) -> None:
        """Fetch from `source` and replace `target` through `write`, which raises `OSError`."""
        self._source = source
        self._target = target
        self._write = write

    def refresh(self) -> Token:
        """Fetch a token and write it alone into the target; raises `TokenError`."""
        token = self._source.fetch()
        try:
            self._write(self._target, token.value)
        except OSError as error:
            raise TokenError(f"cannot write {self._target}: {error}") from error
        return token

    def wait_after(self, token: Token) -> timedelta:
        """The wait before the refresh that follows `token`."""
        return refresh_wait(token)
