"""The pull request DTOs, the factory's marker and the post key."""

import re
from datetime import UTC, datetime
from typing import Annotated, Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    PositiveInt,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)

from factory.domain.git import CommitId
from factory.domain.identifiers import WorkItemId

FACTORY_MARKER = "<!-- factory -->"
PullRequestState = Literal["open", "closed", "merged"]
PostKind = Literal[
    "question",
    "attempts_cap",
    "round_cap",
    "crash_cap",
    "send_back",
    "stall",
    "expiry",
    "correction",
    "error",
    "cost_table",
]
PostOutcome = Literal["posted", "already_posted"]

_KEY_LINE = re.compile(r"^<!-- factory key=(?P<work_item>[^:]*):(?P<kind>[^:]*):(?P<n>[^:]*) -->$")


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class PullRequestView(_Frozen):
    """What the factory reads of one pull request."""

    number: PositiveInt
    branch: str
    title: str
    state: PullRequestState
    draft: bool
    merge_commit: CommitId | None = None
    url: str

    @model_validator(mode="after")
    def _merge_commit_exactly_when_merged(self) -> Self:
        if (self.state == "merged") != (self.merge_commit is not None):
            raise ValueError("merge_commit is set exactly when the state is merged")
        return self


class PostKey(_Frozen):
    """The key that makes a repeated post of the factory recognisable."""

    work_item: WorkItemId
    kind: PostKind
    n: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]+$")]

    def comment(self) -> str:
        """The key as the HTML comment that ends a post."""
        return f"<!-- factory key={self.work_item}:{self.kind}:{self.n} -->"


class PullRequestComment(_Frozen):
    """One comment on a pull request, told apart by the marker, not the author."""

    id: PositiveInt
    author: str
    body: str
    created_at: AwareDatetime
    by_factory: bool
    key: PostKey | None

    @field_validator("created_at")
    @classmethod
    def _to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @classmethod
    def from_body(
        cls, *, id: int, author: str, body: str, created_at: datetime
    ) -> "PullRequestComment":
        """Build a comment, deriving `by_factory` and `key` from the body alone."""
        by_factory = FACTORY_MARKER in body
        return cls(
            id=id,
            author=author,
            body=body,
            created_at=created_at,
            by_factory=by_factory,
            key=parse_post_key(body) if by_factory else None,
        )


def render_post(text: str, key: PostKey) -> str:
    """The body of a factory post: the text, the marker and the key last."""
    return f"{text.rstrip()}\n\n{FACTORY_MARKER}\n{key.comment()}"


def parse_post_key(body: str) -> PostKey | None:
    """The key on the last non-blank line of `body`, or `None` if there is none."""
    lines = [line.rstrip() for line in body.splitlines() if line.strip()]
    if not lines:
        return None
    match = _KEY_LINE.match(lines[-1])
    if match is None:
        return None
    try:
        return PostKey.model_validate(match.groupdict())
    except ValidationError:
        return None
