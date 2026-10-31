"""The token source behind an OAuth2 client-credentials grant, over the standard library."""

import json
import urllib.error
import urllib.parse
import urllib.request
from contextlib import AbstractContextManager
from typing import Protocol

from factory.application.tokens import TokenSource
from factory.domain.errors import TokenError
from factory.domain.tokens import Token

_MASK = "***"
_DESCRIPTION_LIMIT = 200
_NO_ACCESS = "the answer holds no access_token"
_NO_EXPIRY = "the answer holds no expires_in"


class _Body(Protocol):
    def read(self) -> bytes: ...


class OpenUrl(Protocol):
    """The shape of `urllib.request.urlopen` the source calls."""

    def __call__(
        self, request: urllib.request.Request, /, *, timeout: float
    ) -> AbstractContextManager[_Body]:
        """Send `request` and return its answer."""
        ...


class ClientCredentialsTokenSource(TokenSource):
    """Requests a token with a client id and a client secret from the grant's endpoint."""

    def __init__(
        self,
        url: str,
        client_id: str,
        client_secret: str,
        scope: str,
        *,
        open_url: OpenUrl = urllib.request.urlopen,
        timeout: float = 30.0,
    ) -> None:
        """Post to `url` through `open_url`, which waits at most `timeout` seconds."""
        self._url = url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._open_url = open_url
        self._timeout = timeout
        self._issued = ""

    def fetch(self) -> Token:
        """Request a token; raises `TokenError` without the secret or a token in its detail."""
        try:
            with self._open_url(self._request(), timeout=self._timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            raise self._error(_http_detail(error)) from None
        except urllib.error.URLError as error:
            raise self._error(str(error.reason)) from None
        except OSError as error:
            raise self._error(str(error)) from None
        token = self._token_of(body)
        self._issued = token.value
        return token

    def _request(self) -> urllib.request.Request:
        fields = {
            "client_id": self._client_id,
            "scope": self._scope,
            "client_secret": self._client_secret,
            "grant_type": "client_credentials",
        }
        return urllib.request.Request(
            self._url,
            data=urllib.parse.urlencode(fields).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

    def _token_of(self, body: bytes) -> Token:
        answer = _json_object(body)
        value = answer.get("access_token")
        if not isinstance(value, str) or not value or any(c.isspace() for c in value):
            raise self._error(_NO_ACCESS)
        expires_in = _positive_seconds(answer.get("expires_in"))
        if expires_in is None:
            raise self._error(_NO_EXPIRY)
        return Token(value=value, expires_in=expires_in)

    def _error(self, detail: str) -> TokenError:
        # A server may echo what it was sent or gave out; neither may reach a log line.
        # Only the last token is kept, so a long-running refresher holds no growing list.
        return TokenError(_masked(detail, [self._client_secret, self._issued]))


def _masked(detail: str, hidden: list[str]) -> str:
    for value in hidden:
        if value:
            detail = detail.replace(value, _MASK)
    return detail


def _json_object(body: bytes) -> dict[str, object]:
    try:
        answer: object = json.loads(body)
    except ValueError:
        return {}
    if not isinstance(answer, dict):
        return {}
    return {str(key): value for key, value in answer.items()}


def _positive_seconds(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value)
    if isinstance(value, int) and value > 0:
        return value
    return None


def _http_detail(error: urllib.error.HTTPError) -> str:
    answer = _json_object(error.read())
    parts = [f"HTTP {error.code}"]
    kind = answer.get("error")
    if isinstance(kind, str) and kind:
        parts.append(kind)
    description = answer.get("error_description")
    if isinstance(description, str) and description.strip():
        parts.append(description.splitlines()[0][:_DESCRIPTION_LIMIT])
    echoed = answer.get("access_token")
    return _masked(": ".join(parts), [echoed] if isinstance(echoed, str) else [])
