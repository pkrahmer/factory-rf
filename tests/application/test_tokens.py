"""Tests of the refresher that writes a fetched token into the login file."""

from pathlib import Path

import pytest

from factory.adapters.atomic_file import replace_text
from factory.application.tokens import TokenRefresher
from factory.domain.errors import TokenError
from factory.domain.tokens import Token
from token_support import ScriptedTokenSource


@pytest.fixture
def target(tmp_path: Path) -> Path:
    """The login file, in a folder that does not exist yet."""
    return tmp_path / "logins" / "api-login"


def test_a_refresh_writes_the_token_alone_and_replaces_the_older_one(target: Path) -> None:
    source = ScriptedTokenSource(
        Token(value="tok-1", expires_in=3599), Token(value="tok-2", expires_in=3599)
    )
    refresher = TokenRefresher(source, target, replace_text)

    first = refresher.refresh()
    written_first = target.read_bytes()
    refresher.refresh()

    assert first == Token(value="tok-1", expires_in=3599)
    assert written_first == b"tok-1"
    assert target.read_bytes() == b"tok-2"


def test_a_failed_fetch_leaves_the_old_file_untouched(target: Path) -> None:
    target.parent.mkdir()
    target.write_text("old-token", encoding="utf-8")
    refresher = TokenRefresher(ScriptedTokenSource(TokenError("no route")), target, replace_text)

    with pytest.raises(TokenError) as raised:
        refresher.refresh()

    assert raised.value.detail == "no route"
    assert target.read_text(encoding="utf-8") == "old-token"


def test_a_write_that_fails_is_a_token_error_naming_the_target(target: Path) -> None:
    target.mkdir(parents=True)
    refresher = TokenRefresher(
        ScriptedTokenSource(Token(value="tok-1", expires_in=3599)), target, replace_text
    )

    with pytest.raises(TokenError) as raised:
        refresher.refresh()

    assert raised.value.detail.startswith(f"cannot write {target}: ")
    assert len(raised.value.detail) > len(f"cannot write {target}: ")
    assert str(raised.value) == f"token request failed: {raised.value.detail}"
