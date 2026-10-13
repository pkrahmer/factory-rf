"""The git values: the time limit, the commit identity and the wrapper's options."""

from datetime import timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from factory.domain.git import (
    GIT_TIME_LIMIT,
    GitIdentity,
    GitOptions,
    check_branch_name,
    check_git_argument,
)


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


@pytest.mark.parametrize("value", ["", "-x", "--force"])
def test_git_argument_that_is_empty_or_starts_with_a_dash_is_refused(value: str) -> None:
    with pytest.raises(ValueError):
        check_git_argument(value)


@pytest.mark.parametrize(
    "value",
    ["main", "origin/main", "HEAD~1", "work-item/F0001-S0001", "file:///tmp/remote.git"],
)
def test_git_argument_that_is_a_ref_branch_or_url_is_accepted(value: str) -> None:
    check_git_argument(value)


@pytest.mark.parametrize(
    "value", ["", "-x", "+main", ":main", "main:other", "HEAD:refs/heads/x", "refs/heads/x*"]
)
def test_branch_name_that_git_push_reads_as_an_option_or_a_refspec_is_refused(value: str) -> None:
    with pytest.raises(ValueError):
        check_branch_name(value)


@pytest.mark.parametrize("value", ["main", "work-item/F0001-S0001", "feature/x", "a+b"])
def test_branch_name_without_refspec_syntax_is_accepted(value: str) -> None:
    check_branch_name(value)


@pytest.mark.parametrize(
    "value",
    [
        "HEAD",
        "@",
        "^main",
        "main~1",
        "ma?n",
        "ma[in",
        "ma\\in",
        "ma in",
        "a\tb",
        "a..b",
        "a@{1}",
        "/x",
        "x/",
        "a//b",
        "x.",
        "feature/.x",
        "x.lock",
        "feature/x.lock/y",
        "a\x7fb",
    ],
)
def test_branch_name_that_git_would_not_take_as_a_branch_is_refused(value: str) -> None:
    with pytest.raises(ValueError):
        check_branch_name(value)


@pytest.mark.parametrize("value", ["x*y", "", "-x", "+main", ":main", "main:other"])
def test_branch_name_with_a_star_inside_or_refspec_syntax_is_refused(value: str) -> None:
    with pytest.raises(ValueError):
        check_branch_name(value)


@pytest.mark.parametrize(
    "value",
    [
        "main",
        "work-item/F0001-S0001",
        "feature/x",
        "a+b",
        "a@b",
        "release-1.2",
        "feature/HEAD",
        "x.lock.y",
    ],
)
def test_branch_name_that_git_takes_as_a_branch_is_accepted(value: str) -> None:
    check_branch_name(value)
