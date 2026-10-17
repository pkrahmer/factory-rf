"""The closed models of a work item as the remote shows it and of a story file listed on main."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.work_item import StoryFile, WorkItemDocument, WorkItemSnapshot

PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
DOCUMENT = WorkItemDocument(state=None, body="# First story\n")


def _snapshot_fields(**changes: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "id": "F0001-S0001",
        "path": PATH,
        "folder": "in-progress",
        "branch": "work-item/F0001-S0001",
        "branch_commit": "a" * 40,
        "document": DOCUMENT,
    }
    return {**fields, **changes}


def _story_file_fields(**changes: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "id": "F0001-S0001",
        "path": PATH,
        "feature_directory": "F0001-example",
        "file_name": "F0001-S0001-first.md",
        "folder": "in-progress",
    }
    return {**fields, **changes}


def _fields_of(model: type[BaseModel], **changes: object) -> dict[str, object]:
    if model is WorkItemSnapshot:
        return _snapshot_fields(**changes)
    return _story_file_fields(**changes)


MODELS: list[type[BaseModel]] = [WorkItemSnapshot, StoryFile]


@pytest.mark.parametrize(
    ("branch_commit", "accepted"),
    [
        ("a" * 40, True),
        (None, True),
        ("a" * 39, False),
        ("A" + "a" * 39, False),
    ],
)
def test_branch_commit_is_forty_lower_case_hex_characters_or_none(
    branch_commit: str | None, *, accepted: bool
) -> None:
    model: type[BaseModel] = WorkItemSnapshot
    fields = _snapshot_fields(branch_commit=branch_commit)

    if accepted:
        assert model(**fields).model_dump()["branch_commit"] == branch_commit
    else:
        with pytest.raises(ValidationError):
            model(**fields)


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize(("folder", "accepted"), [("in-progress", True), ("ongoing", False)])
def test_folder_is_a_lifecycle_folder(
    model: type[BaseModel], folder: str, *, accepted: bool
) -> None:
    fields = _fields_of(model, folder=folder)

    if accepted:
        assert model(**fields).model_dump()["folder"] == folder
    else:
        with pytest.raises(ValidationError):
            model(**fields)


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize(("work_item", "accepted"), [("F0001-S0001", True), ("F001-S0001", False)])
def test_id_is_a_work_item_id(model: type[BaseModel], work_item: str, *, accepted: bool) -> None:
    fields = _fields_of(model, id=work_item)

    if accepted:
        assert model(**fields).model_dump()["id"] == work_item
    else:
        with pytest.raises(ValidationError):
            model(**fields)
