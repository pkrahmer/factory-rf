"""Tests of the token source behind an OAuth2 client-credentials grant."""

import http.client
import urllib.error
from urllib.parse import parse_qs

import pytest

from factory.adapters.oauth_token import ClientCredentialsTokenSource
from factory.domain.errors import TokenError
from factory.domain.tokens import Token
from token_support import (
    ENDPOINT,
    HIDDEN,
    ISSUED,
    RecordingOpener,
    answer,
    http_error,
    unreadable_http_error,
)


def source_of(opener: RecordingOpener, secret: str = HIDDEN) -> ClientCredentialsTokenSource:
    """A source for client `client-1` and scope `api://x/.default` that opens through `opener`."""
    return ClientCredentialsTokenSource(
        ENDPOINT, "client-1", secret, "api://x/.default", open_url=opener
    )


@pytest.mark.parametrize(
    "expires_in", [pytest.param(3599, id="integer"), pytest.param("3599", id="string")]
)
def test_a_fetch_posts_the_four_fields_form_encoded_and_returns_the_token(
    expires_in: int | str,
) -> None:
    awkward = "a&b=c+d e"
    opener = RecordingOpener(answer({"access_token": "t", "expires_in": expires_in}))

    token = source_of(opener, awkward).fetch()

    [request] = opener.requests
    assert token == Token(value="t", expires_in=3599)
    assert request.get_method() == "POST"
    assert request.full_url == ENDPOINT
    assert request.get_header("Content-type") == "application/x-www-form-urlencoded"
    assert isinstance(request.data, bytes)
    assert parse_qs(request.data.decode()) == {
        "client_id": ["client-1"],
        "scope": ["api://x/.default"],
        "client_secret": [awkward],
        "grant_type": ["client_credentials"],
    }


@pytest.mark.parametrize(
    ("timeout", "expected"),
    [pytest.param(None, 30.0, id="default"), pytest.param(5.0, 5.0, id="given")],
)
def test_open_url_receives_the_timeout(timeout: float | None, expected: float) -> None:
    opener = RecordingOpener(answer({"access_token": "t", "expires_in": 3599}))
    if timeout is None:
        source = source_of(opener)
    else:
        source = ClientCredentialsTokenSource(
            ENDPOINT, "client-1", HIDDEN, "api://x/.default", open_url=opener, timeout=timeout
        )

    source.fetch()

    assert opener.timeouts == [expected]


LONG_DESCRIPTION = "d" * 300
CUT_SHORT = http.client.IncompleteRead(b"")


@pytest.mark.parametrize(
    ("fault", "detail"),
    [
        pytest.param(
            http_error(
                400,
                answer(
                    {
                        "error": "invalid_client",
                        "error_description": "AADSTS7000215: bad secret\r\nTrace ID: x",
                    }
                ),
            ),
            "HTTP 400: invalid_client: AADSTS7000215: bad secret",
            id="http-error-first-line",
        ),
        pytest.param(
            http_error(
                400, answer({"error": "invalid_client", "error_description": LONG_DESCRIPTION})
            ),
            f"HTTP 400: invalid_client: {LONG_DESCRIPTION[:200]}",
            id="http-error-description-cut-at-200",
        ),
        pytest.param(http_error(500, b"<html>down</html>"), "HTTP 500", id="http-error-not-json"),
        pytest.param(
            http_error(400, answer({"other": "x"})), "HTTP 400", id="http-error-without-error"
        ),
        pytest.param(urllib.error.URLError("no route"), "no route", id="url-error"),
        pytest.param(OSError("boom"), "boom", id="os-error"),
        pytest.param(TimeoutError("timed out"), "timed out", id="timeout"),
        pytest.param(CUT_SHORT, str(CUT_SHORT) or type(CUT_SHORT).__name__, id="incomplete-read"),
        pytest.param(unreadable_http_error(400), "HTTP 400", id="http-error-body-unreadable"),
        pytest.param(answer([]), "the answer holds no access_token", id="body-not-an-object"),
        pytest.param(
            answer({"expires_in": 3599}), "the answer holds no access_token", id="no-access-token"
        ),
        pytest.param(
            answer({"access_token": "t", "expires_in": 0}),
            "the answer holds no expires_in",
            id="expires-in-0",
        ),
        pytest.param(
            http_error(
                400,
                answer({"error": "invalid_client", "error_description": f"bad secret {HIDDEN}"}),
            ),
            "HTTP 400: invalid_client: bad secret ***",
            id="echoed-secret",
        ),
        pytest.param(
            http_error(
                400,
                answer(
                    {
                        "access_token": ISSUED,
                        "error": "invalid_request",
                        "error_description": f"already issued {ISSUED}",
                    }
                ),
            ),
            "HTTP 400: invalid_request: already issued ***",
            id="echoed-token",
        ),
    ],
)
def test_a_failed_fetch_is_a_token_error_without_the_secret_or_the_token(
    fault: bytes | BaseException, detail: str
) -> None:
    # A first fetch hands out the token, so a later echo of it is one the source has seen.
    source = source_of(RecordingOpener(answer({"access_token": ISSUED, "expires_in": 3599}), fault))
    source.fetch()

    with pytest.raises(TokenError) as raised:
        source.fetch()

    assert raised.value.detail == detail
    assert HIDDEN not in str(raised.value)
    assert ISSUED not in str(raised.value)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        pytest.param(b"<html>", "the answer holds no access_token", id="not-json"),
        pytest.param(
            answer({"access_token": "", "expires_in": 3599}),
            "the answer holds no access_token",
            id="access-token-blank",
        ),
        pytest.param(
            answer({"access_token": "t u", "expires_in": 3599}),
            "the answer holds no access_token",
            id="access-token-with-a-space",
        ),
        pytest.param(
            answer({"access_token": 5, "expires_in": 3599}),
            "the answer holds no access_token",
            id="access-token-not-a-string",
        ),
        pytest.param(
            answer({"access_token": "t"}), "the answer holds no expires_in", id="no-expires-in"
        ),
        pytest.param(
            answer({"access_token": "t", "expires_in": "soon"}),
            "the answer holds no expires_in",
            id="expires-in-not-numeric",
        ),
        pytest.param(
            answer({"access_token": "t", "expires_in": True}),
            "the answer holds no expires_in",
            id="expires-in-true",
        ),
        pytest.param(
            answer({"access_token": "t", "expires_in": "0"}),
            "the answer holds no expires_in",
            id="expires-in-string-0",
        ),
        pytest.param(
            answer({"access_token": "t", "expires_in": "\u00b2"}),
            "the answer holds no expires_in",
            id="expires-in-superscript",
        ),
        pytest.param(
            answer({"access_token": "t", "expires_in": 1}),
            Token(value="t", expires_in=1),
            id="expires-in-1",
        ),
        pytest.param(
            answer({"access_token": "t", "expires_in": "1"}),
            Token(value="t", expires_in=1),
            id="expires-in-string-1",
        ),
    ],
)
def test_a_200_answer_needs_a_token_string_and_a_positive_life(
    body: bytes, expected: Token | str
) -> None:
    source = source_of(RecordingOpener(body))

    if isinstance(expected, Token):
        assert source.fetch() == expected
    else:
        with pytest.raises(TokenError) as raised:
            source.fetch()
        assert raised.value.detail == expected
