"""The board's rows: the features' counts, the work items in progress and their text."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.board import BoardRow, FeatureRow, feature_rows, render_board, work_item_row
from factory.domain.identifiers import branch_name
from factory.domain.paths import LifecycleFolder, work_item_path
from factory.domain.work_item import (
    Claim,
    StoryFile,
    WorkItemDocument,
    WorkItemSnapshot,
    WorkItemState,
)

WORK_ITEM = "F0001-S0001"
DIRECTORY = "F0001-demo"
STARTED_AT = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
CLAIM = Claim(instance="factory-1", stage="tests", started_at=STARTED_AT, lease_duration=30)


def _story(work_item: str, folder: LifecycleFolder, directory: str = DIRECTORY) -> StoryFile:
    file_name = f"{work_item}-story.md"
    return StoryFile(
        id=work_item,
        path=work_item_path(directory, folder, file_name),
        feature_directory=directory,
        file_name=file_name,
        folder=folder,
    )


def _snapshot(state: WorkItemState, body: str) -> WorkItemSnapshot:
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=work_item_path(DIRECTORY, "in-progress", f"{WORK_ITEM}-story.md"),
        folder="in-progress",
        branch=branch_name(WORK_ITEM),
        branch_commit="a" * 40,
        document=WorkItemDocument(state=state, body=body),
    )


def _board_row(**changes: object) -> dict[str, object]:
    return {
        "work_item": WORK_ITEM,
        "title": "Domain model",
        "folder": "in-progress",
        "stage": "tests",
        "blocked": None,
        "claim": None,
        "running_since": None,
        "pull_request": 7,
        **changes,
    }


def _feature_row(**changes: object) -> dict[str, object]:
    return {
        "feature": "F0001",
        "title": "Todo service",
        "backlog": 1,
        "in_progress": 2,
        "done": 3,
        **changes,
    }


def test_feature_rows_count_the_story_files_of_each_folder() -> None:
    stories = [
        _story("F0001-S0001", "backlog"),
        _story("F0001-S0002", "in-progress"),
        _story("F0001-S0003", "in-progress"),
        _story("F0001-S0004", "done"),
        _story("F0001-S0005", "done"),
        _story("F0001-S0006", "done"),
    ]

    rows = feature_rows(stories, {})

    assert len(rows) == 1
    assert rows[0].feature == "F0001"
    assert (rows[0].backlog, rows[0].in_progress, rows[0].done) == (1, 2, 3)
    assert rows[0].acceptance is None


def test_feature_rows_are_one_per_feature_in_plain_id_order() -> None:
    stories = [
        _story("F0003-S0001", "done", "F0003-third"),
        _story("F0001-S0002", "backlog"),
        _story("F0002-S0001", "in-progress", "F0002-second"),
        _story("F0001-S0001", "in-progress"),
        _story("F0003-S0002", "backlog", "F0003-third"),
    ]

    rows = feature_rows(stories, {})

    assert [row.feature for row in rows] == ["F0001", "F0002", "F0003"]


@pytest.mark.parametrize(
    ("titles", "expected"),
    [
        ({"F0001": "Todo service"}, "Todo service"),
        ({"F0002": "Another feature"}, DIRECTORY),
        ({}, DIRECTORY),
    ],
    ids=["from-the-mapping", "other-feature-only", "empty-mapping"],
)
def test_a_feature_title_comes_from_the_mapping_else_the_directory_name(
    titles: dict[str, str], expected: str
) -> None:
    rows = feature_rows([_story(WORK_ITEM, "backlog")], titles)

    assert [row.title for row in rows] == [expected]


@pytest.mark.parametrize(
    ("body", "title"),
    [
        ("Some text\n# Domain model\n\n# Later title\n", "Domain model"),
        ("No title here\n\n## Interface\n", WORK_ITEM),
    ],
    ids=["first-title", "no-title"],
)
def test_a_work_item_row_is_filled_from_the_snapshot(body: str, title: str) -> None:
    state = WorkItemState(stage="tests", blocked="question", pull_request=7, claim=CLAIM)

    row = work_item_row(_snapshot(state, body))

    assert row.work_item == WORK_ITEM
    assert row.title == title
    assert row.folder == "in-progress"
    assert row.stage == "tests"
    assert row.blocked == "question"
    assert row.claim == CLAIM
    assert row.pull_request == 7


@pytest.mark.parametrize(
    ("claim", "running_since"),
    [(CLAIM, STARTED_AT), (None, None)],
    ids=["claimed", "unclaimed"],
)
def test_running_since_is_the_claims_start(
    claim: Claim | None, running_since: datetime | None
) -> None:
    state = WorkItemState(stage="tests", claim=claim)

    row = work_item_row(_snapshot(state, "# Domain model\n"))

    assert row.running_since == running_since


def test_render_board_writes_the_features_and_the_work_items() -> None:
    features = [FeatureRow(feature="F0001", title="Todo service", backlog=1, in_progress=2, done=3)]
    rows = [
        BoardRow(
            work_item=WORK_ITEM,
            title="Domain model",
            folder="in-progress",
            stage="tests",
            blocked=None,
            claim=CLAIM,
            running_since=None,
            pull_request=7,
        )
    ]

    text = render_board(features, rows)

    assert text == (
        "features\n"
        "F0001  Todo service  backlog=1  in-progress=2  done=3  acceptance=-\n"
        "work items\n"
        "F0001-S0001  Domain model  in-progress  stage=tests  blocked=-  claim=factory-1"
        "  running_since=-  pull_request=7\n"
    )


def test_an_empty_board_has_only_its_two_headings() -> None:
    assert render_board([], []) == "features\nwork items\n"


def test_render_board_writes_running_since_in_utc_with_a_z() -> None:
    since = datetime(2026, 10, 12, 14, 0, 30, tzinfo=timezone(timedelta(hours=2)))
    row = BoardRow.model_validate(_board_row(claim=CLAIM, running_since=since))

    lines = render_board([], [row]).splitlines()

    assert "  running_since=2026-10-12T12:00:30Z  " in lines[-1]


@pytest.mark.parametrize(
    ("model", "fields"),
    [(BoardRow, _board_row()), (FeatureRow, _feature_row())],
    ids=["board-row", "feature-row"],
)
def test_a_row_refuses_an_unknown_key(model: type[BaseModel], fields: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        model(**fields, unknown=1)


@pytest.mark.parametrize(
    ("model", "fields", "field"),
    [(BoardRow, _board_row(), "title"), (FeatureRow, _feature_row(), "backlog")],
    ids=["board-row", "feature-row"],
)
def test_a_row_refuses_an_assignment(
    model: type[BaseModel], fields: dict[str, object], field: str
) -> None:
    row = model(**fields)

    with pytest.raises(ValidationError):
        setattr(row, field, row.model_dump()[field])


@pytest.mark.parametrize("field", ["backlog", "in_progress", "done"])
@pytest.mark.parametrize(("count", "accepted"), [(0, True), (-1, False)])
def test_a_feature_count_is_not_negative(field: str, count: int, accepted: bool) -> None:
    model: type[BaseModel] = FeatureRow
    if accepted:
        assert getattr(model(**_feature_row(**{field: count})), field) == count
    else:
        with pytest.raises(ValidationError):
            model(**_feature_row(**{field: count}))


@pytest.mark.parametrize(
    ("field", "value", "accepted"),
    [
        ("pull_request", 1, True),
        ("pull_request", None, True),
        ("pull_request", 0, False),
        ("folder", "in-progress", True),
        ("folder", "ongoing", False),
        ("running_since", STARTED_AT, True),
        ("running_since", datetime(2026, 10, 12, 12, 0), False),  # noqa: DTZ001
    ],
)
def test_a_board_row_accepts_only_its_values(field: str, value: object, accepted: bool) -> None:
    model: type[BaseModel] = BoardRow
    if accepted:
        assert getattr(model(**_board_row(**{field: value})), field) == value
    else:
        with pytest.raises(ValidationError):
            model(**_board_row(**{field: value}))


@pytest.mark.parametrize(("value", "accepted"), [("due", True), ("other", False)])
def test_a_feature_row_accepts_only_an_acceptance_status(value: str, accepted: bool) -> None:
    model: type[BaseModel] = FeatureRow
    if accepted:
        assert model(**_feature_row(acceptance=value)).model_dump()["acceptance"] == value
    else:
        with pytest.raises(ValidationError):
            model(**_feature_row(acceptance=value))
