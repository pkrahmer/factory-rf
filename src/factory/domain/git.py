"""The git values the factory reasons about."""

from datetime import UTC, datetime, timedelta
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, field_validator

from factory.domain.kill_points import KillPoints

CommitId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]

PushOutcome = Literal["pushed", "rejected", "unreachable"]

MergeOutcome = Literal["merged", "fast_forwarded", "up_to_date", "conflict", "not_fast_forward"]

# A rename is a deletion plus an addition, so that no tool's rename detection shapes the answer.
ChangeKind = Literal["added", "modified", "deleted"]

GIT_TIME_LIMIT = timedelta(minutes=5)


class RemoteBranch(BaseModel):
    """A branch as the remote holds it: its name without the remote's prefix, and its commit."""

    name: str
    commit: CommitId


class GitIdentity(BaseModel):
    """The author and committer of the factory's commits."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: Annotated[str, Field(min_length=1)]
    email: Annotated[str, Field(min_length=1)]


class GitOptions(BaseModel):
    """The settings of a git wrapper: identity, environment, kill points, executable, limit."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    identity: GitIdentity = GitIdentity(name="factory", email="factory@noreply.invalid")
    environment: dict[str, str] = {}
    kill_points: KillPoints | None = None
    executable: str = "git"
    time_limit: timedelta = GIT_TIME_LIMIT


class ChangedPath(BaseModel):
    """A path that differs from the state it is compared with, and how."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    change: ChangeKind


class CommitInfo(BaseModel):
    """One commit of a log: its id, parents, subject, author and committer date in UTC."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    commit: CommitId
    parents: list[CommitId]
    subject: str
    author: str
    committed_at: AwareDatetime

    @field_validator("committed_at")
    @classmethod
    def _in_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


class WorkTreeStatus(BaseModel):
    """The checked-out branch, the commit HEAD points to and what differs from it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    branch: str | None
    head: CommitId | None
    changes: list[ChangedPath]


def check_repository_path(path: str) -> None:
    """Raise `ValueError` unless `path` is relative to the repository and stays inside it."""
    pure = PurePosixPath(path)
    if not path or pure.is_absolute():
        raise ValueError(f"not a repository-relative path: {path!r}")
    if ".." in pure.parts:
        raise ValueError(f"path leaves the repository: {path!r}")


def check_git_argument(value: str) -> None:
    """Raise `ValueError` for a ref, branch, commit or url that git could read as an option."""
    # No ref, branch name or remote url starts with a dash, so refusing one loses nothing.
    if not value or value.startswith("-"):
        raise ValueError(f"not a git ref, branch or url: {value!r}")


def check_branch_name(value: str) -> None:
    """Raise ValueError for a value that `git push` could read as anything but a branch name."""
    check_git_argument(value)
    # A leading `+` forces, a `:` names another ref or deletes one, a `*` is a pattern.
    if value.startswith("+") or ":" in value or "*" in value:
        raise ValueError(f"not a branch name git push takes literally: {value!r}")
    # `HEAD` and `@` name the checked-out branch, not a branch of that name.
    if value in BRANCH_ALIASES or not _is_valid_ref_name(value):
        raise ValueError(f"not a branch name git takes: {value!r}")


# The rules of `git check-ref-format --branch`, so that no other kind of ref passes as a branch.
BRANCH_ALIASES = frozenset({"HEAD", "@"})
FORBIDDEN_REF_CHARACTERS = frozenset("^~?[\\ ")
FORBIDDEN_REF_SEQUENCES = ("..", "@{", "//")


def _is_valid_ref_name(value: str) -> bool:
    if any(_is_forbidden_character(character) for character in value):
        return False
    if any(sequence in value for sequence in FORBIDDEN_REF_SEQUENCES):
        return False
    if value.startswith("/") or value.endswith("/") or value.endswith("."):
        return False
    return all(_is_valid_component(component) for component in value.split("/"))


def _is_forbidden_character(character: str) -> bool:
    return character in FORBIDDEN_REF_CHARACTERS or ord(character) < 0x20 or ord(character) == 0x7F


def _is_valid_component(component: str) -> bool:
    return not component.startswith(".") and not component.endswith(".lock")
