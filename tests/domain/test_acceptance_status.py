"""The status of a feature's acceptance, derived from its folders and its reports."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.acceptance import (
    AcceptanceOutcome,
    AcceptanceState,
    FeatureAcceptance,
    FeatureFiles,
    ReportFacts,
    acceptance_status,
    story_file_ids,
)
from factory.domain.work_item import WorkItemState

ARCHIVED = ["F0001-S0001", "F0001-S0002"]
DONE = ["F0001-S0001-a.md", "F0001-S0002-b.md"]
COMPLETE = FeatureFiles(feature="F0001", backlog=[".gitkeep"], done=DONE)


def _recorded(
    report: str, outcome: AcceptanceOutcome = "accepted", stories: list[str] | None = None
) -> ReportFacts:
    state = AcceptanceState(
        stage="done", outcome=outcome, stories=ARCHIVED if stories is None else stories
    )
    return ReportFacts(id=report, folder="done", state=state, on_branch=False)


def _open(report: str, *, on_branch: bool) -> ReportFacts:
    state = AcceptanceState(stage="acceptance", stories=ARCHIVED)
    return ReportFacts(id=report, folder="in-progress", state=state, on_branch=on_branch)


def test_story_file_ids_ascend_without_repeats() -> None:
    names = ["F0001-S0002-b.md", "F0001-S0001-a.md", "F0001-S0002-b.md"]

    assert story_file_ids(names) == ["F0001-S0001", "F0001-S0002"]


def test_story_file_ids_ignore_names_that_are_no_story_files() -> None:
    names = [".gitkeep", "README.md", "notes.md", "F0001-A0001-acceptance.md"]

    assert story_file_ids(names) == []


def test_a_gitkeep_in_the_backlog_does_not_keep_an_archived_feature_from_being_due() -> None:
    assert acceptance_status(COMPLETE, []) == "due"


def test_a_feature_without_an_archived_story_is_incomplete() -> None:
    files = FeatureFiles(
        feature="F0001", backlog=[".gitkeep"], in_progress=[".gitkeep"], done=[".gitkeep"]
    )

    assert acceptance_status(files, []) == "incomplete"


@pytest.mark.parametrize("folder", ["backlog", "in_progress"])
def test_a_waiting_story_file_keeps_a_feature_incomplete(folder: str) -> None:
    files = COMPLETE.model_copy(update={folder: ["F0001-S0003-c.md"]})

    assert acceptance_status(files, []) == "incomplete"


@pytest.mark.parametrize("outcome", ["accepted", "refused"])
def test_a_recorded_report_covering_the_archived_stories_gives_its_outcome(
    outcome: AcceptanceOutcome,
) -> None:
    assert acceptance_status(COMPLETE, [_recorded("F0001-A0001", outcome)]) == outcome


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [("accepted", "refused", "refused"), ("refused", "accepted", "accepted")],
)
def test_the_highest_covering_report_decides(
    first: AcceptanceOutcome, second: AcceptanceOutcome, expected: str
) -> None:
    reports = [_recorded("F0001-A0002", second), _recorded("F0001-A0001", first)]

    assert acceptance_status(COMPLETE, reports) == expected


@pytest.mark.parametrize(
    "stories", [["F0001-S0001"], ["F0001-S0001", "F0001-S0002", "F0001-S0003"]]
)
def test_a_report_on_other_stories_does_not_cover_the_archived_ones(stories: list[str]) -> None:
    assert acceptance_status(COMPLETE, [_recorded("F0001-A0001", stories=stories)]) == "due"


@pytest.mark.parametrize(
    "files",
    [
        COMPLETE,
        COMPLETE.model_copy(update={"backlog": ["F0001-S0003-c.md"]}),
        FeatureFiles(feature="F0001"),
    ],
)
def test_a_report_on_its_branch_alone_is_in_flight(files: FeatureFiles) -> None:
    assert acceptance_status(files, [_open("F0001-A0001", on_branch=True)]) == "in_flight"


def test_a_branch_report_merged_to_main_is_merged_unrecorded() -> None:
    reports = [_open("F0001-A0001", on_branch=True), _open("F0001-A0001", on_branch=False)]

    assert acceptance_status(COMPLETE, reports) == "merged_unrecorded"


@pytest.mark.parametrize("backlog", [[".gitkeep"], ["F0001-S0003-c.md"]])
def test_an_unrecorded_report_on_main_is_merged_unrecorded(backlog: list[str]) -> None:
    files = COMPLETE.model_copy(update={"backlog": backlog})

    assert acceptance_status(files, [_open("F0001-A0001", on_branch=False)]) == (
        "merged_unrecorded"
    )


def test_a_recorded_acceptance_does_not_stand_while_a_story_file_waits() -> None:
    files = COMPLETE.model_copy(update={"backlog": ["F0001-S0003-c.md"]})

    assert acceptance_status(files, [_recorded("F0001-A0001")]) == "incomplete"


def _valid_arguments() -> dict[str, dict[str, object]]:
    return {
        "FeatureFiles": {"feature": "F0001"},
        "ReportFacts": {
            "id": "F0001-A0001",
            "folder": "done",
            "state": AcceptanceState(stage="done", outcome="accepted", stories=ARCHIVED),
            "on_branch": False,
        },
        "FeatureAcceptance": {
            "feature": "F0001",
            "directory": "F0001-todo",
            "status": "due",
            "archived": ["F0001-S0001"],
            "next_acceptance": "F0001-A0001",
        },
    }


MODELS: dict[str, type[BaseModel]] = {
    "FeatureFiles": FeatureFiles,
    "ReportFacts": ReportFacts,
    "FeatureAcceptance": FeatureAcceptance,
}


@pytest.mark.parametrize("name", list(MODELS))
def test_the_models_refuse_an_unknown_key(name: str) -> None:
    model = MODELS[name]

    with pytest.raises(ValidationError):
        model(**_valid_arguments()[name], unknown=1)


@pytest.mark.parametrize(
    ("name", "field"),
    [("FeatureFiles", "done"), ("ReportFacts", "on_branch"), ("FeatureAcceptance", "status")],
)
def test_the_models_refuse_an_assignment(name: str, field: str) -> None:
    instance = MODELS[name](**_valid_arguments()[name])

    with pytest.raises(ValidationError):
        setattr(instance, field, getattr(instance, field))


@pytest.mark.parametrize(
    ("name", "field", "value", "valid"),
    [
        ("FeatureFiles", "feature", "F0001", True),
        ("FeatureFiles", "feature", "F001", False),
        ("FeatureAcceptance", "feature", "F0001", True),
        ("FeatureAcceptance", "feature", "F001", False),
        ("ReportFacts", "id", "F0001-A0001", True),
        ("ReportFacts", "id", "F001-A0001", False),
        ("FeatureAcceptance", "next_acceptance", "F0001-A0001", True),
        ("FeatureAcceptance", "next_acceptance", "F001-A0001", False),
        ("FeatureAcceptance", "archived", ["F0001-S0001"], True),
        ("FeatureAcceptance", "archived", ["F001-S0001"], False),
        ("ReportFacts", "folder", "done", True),
        ("ReportFacts", "folder", "ongoing", False),
        ("ReportFacts", "state", WorkItemState(stage="done"), False),
        ("FeatureAcceptance", "status", "due", True),
        ("FeatureAcceptance", "status", "other", False),
    ],
)
def test_the_model_fields_are_typed(name: str, field: str, value: object, valid: bool) -> None:
    model = MODELS[name]
    arguments = {**_valid_arguments()[name], field: value}

    if valid:
        assert getattr(model(**arguments), field) == value
    else:
        with pytest.raises(ValidationError):
            model(**arguments)
