"""The git history values: changed paths, commits and the status of the work tree."""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from factory.domain.git import ChangedPath, ChangeKind, CommitInfo

COMMIT = "a" * 40
PARENT = "b" * 40
COMMITTED_AT = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


def _commit_fields(**changes: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "commit": COMMIT,
        "parents": [PARENT],
        "subject": "subject",
        "author": "Test Author",
        "committed_at": COMMITTED_AT,
    }
    return {**fields, **changes}


def test_change_kind_has_no_rename() -> None:
    kinds: TypeAdapter[ChangeKind] = TypeAdapter(ChangeKind)
    model: type[BaseModel] = ChangedPath

    assert [kinds.validate_python(kind) for kind in ("added", "modified", "deleted")] == [
        "added",
        "modified",
        "deleted",
    ]
    with pytest.raises(ValidationError):
        kinds.validate_python("renamed")
    with pytest.raises(ValidationError):
        model(path="a.txt", change="renamed")


def test_committed_at_must_be_aware_and_is_converted_to_utc() -> None:
    model: type[BaseModel] = CommitInfo
    plus_two = datetime(2026, 1, 2, 14, 0, tzinfo=timezone(timedelta(hours=2)))

    info = CommitInfo(**_commit_fields(committed_at=plus_two))

    assert info.committed_at.utcoffset() == timedelta(0)
    assert info.committed_at == COMMITTED_AT
    with pytest.raises(ValidationError):
        model(**_commit_fields(committed_at=datetime.fromisoformat("2026-01-02T12:00:00")))


@pytest.mark.parametrize(
    "fields",
    [
        _commit_fields(commit=COMMIT[:39]),
        _commit_fields(parents=[PARENT.upper()]),
    ],
    ids=["commit-of-39-characters", "uppercase-parent"],
)
def test_commit_ids_are_forty_lowercase_hexadecimal_characters(fields: dict[str, Any]) -> None:
    model: type[BaseModel] = CommitInfo

    with pytest.raises(ValidationError):
        model(**fields)
