"""The git values: the time limit, the commit identity and the wrapper's options."""

from datetime import timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from factory.domain.git import GIT_TIME_LIMIT, GitIdentity, GitOptions


def test_git_time_limit_is_five_minutes() -> None:
    assert timedelta(minutes=5) == GIT_TIME_LIMIT


def test_identity_needs_a_name_and_an_email_and_is_frozen() -> None:
    identity = GitIdentity(name="factory", email="factory@noreply.invalid")
    unknown: dict[str, Any] = {"name": "factory", "email": "factory@noreply.invalid", "x": 1}
    field = "name"

    assert identity.name == "factory"
    assert identity.email == "factory@noreply.invalid"
    with pytest.raises(ValidationError):
        GitIdentity(name="", email="factory@noreply.invalid")
    with pytest.raises(ValidationError):
        GitIdentity(name="factory", email="")
    with pytest.raises(ValidationError):
        GitIdentity(**unknown)
    with pytest.raises(ValidationError):
        setattr(identity, field, "other")


def test_options_default_to_the_factory_identity_and_plain_git() -> None:
    options = GitOptions()
    other = GitOptions()
    unknown: dict[str, Any] = {"x": 1}
    field = "executable"

    options.environment["EXTRA"] = "1"

    assert options.identity == GitIdentity(name="factory", email="factory@noreply.invalid")
    assert other.environment == {}
    assert other.kill_points is None
    assert other.executable == "git"
    assert other.time_limit == GIT_TIME_LIMIT
    with pytest.raises(ValidationError):
        GitOptions(**unknown)
    with pytest.raises(ValidationError):
        setattr(other, field, "other")
