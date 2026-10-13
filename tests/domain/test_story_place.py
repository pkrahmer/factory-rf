"""The place of a story file: its location, its names and the feature file beside it."""

import pytest

from factory.domain.story_form import FormFinding, check_story_place

NOT_A_LOCATION = (
    "not a work item location: "
    "expected factory/features/<feature>/<backlog|in-progress|done>/<file>.md"
)
MISSING_FEATURE_FILE = (
    "the feature file feature.md is missing in factory/features/F0002-work-item-data"
)


def _messages(path: str, *, feature_file_exists: bool = True) -> list[str]:
    findings = check_story_place(path, feature_file_exists=feature_file_exists)
    assert all(finding.line is None for finding in findings)
    return [finding.message for finding in findings]


@pytest.mark.parametrize(
    "path",
    [
        "factory/features/F0002-work-item-data/backlog/F0002-S0001-x.md",
        "factory/features/F0002-work-item-data/in-progress/F0002-S0001-x.md",
        "factory/features/F0002-work-item-data/done/F0002-S0001-x.md",
        "factory/features/F0002-work-item-data/backlog/F0002-S0001.md",
    ],
    ids=["backlog", "in-progress", "done", "without-slug"],
)
def test_a_story_in_its_place_has_no_finding(path: str) -> None:
    assert check_story_place(path, feature_file_exists=True) == []


@pytest.mark.parametrize(
    ("path", "feature_file_exists"),
    [
        ("factory/features/F0002-work-item-data/ongoing/F0002-S0001-x.md", True),
        ("factory/features/F0002-work-item-data/backlog/extra/F0002-S0001-x.md", True),
        ("factory/features/F0002-work-item-data/F0002-S0001-x.md", True),
        ("docs/features/F0002-work-item-data/backlog/F0002-S0001-x.md", True),
        ("factory/stories/F0002-work-item-data/backlog/F0002-S0001-x.md", True),
        ("factory/features/F0002-work-item-data/drafts/F0002-S0001-x.md", True),
        ("factory/features/work-item-data/ongoing/.gitkeep", False),
    ],
    ids=[
        "ongoing",
        "one-part-too-deep",
        "one-part-too-short",
        "outside-factory",
        "outside-features",
        "not-a-lifecycle-folder",
        "everything-else-wrong-too",
    ],
)
def test_a_path_outside_the_work_item_locations_gives_only_that_finding(
    path: str, feature_file_exists: bool
) -> None:
    assert check_story_place(path, feature_file_exists=feature_file_exists) == [
        FormFinding(line=None, message=NOT_A_LOCATION)
    ]


@pytest.mark.parametrize("name", ["F0002-S0001-x.txt", ".gitkeep", "F0002-A0001-x.md", "s0001.md"])
def test_a_file_name_that_is_not_a_story_name_is_a_finding(name: str) -> None:
    path = f"factory/features/F0002-work-item-data/backlog/{name}"

    assert _messages(path) == [f'the file name "{name}" is not F0000-S0000[-slug].md']


@pytest.mark.parametrize("directory", ["work-item-data", "f0002-x"])
def test_a_feature_directory_that_does_not_parse_is_a_finding(directory: str) -> None:
    path = f"factory/features/{directory}/backlog/F0002-S0001-x.md"

    assert _messages(path) == [f'the feature directory "{directory}" is not F0000[-slug]']


def test_a_story_in_the_directory_of_another_feature_is_a_finding() -> None:
    path = "factory/features/F0002-work-item-data/backlog/F0003-S0001-x.md"

    assert _messages(path) == ["the story F0003-S0001 is in the directory of feature F0002"]


def test_a_story_in_the_directory_of_its_own_feature_is_no_finding() -> None:
    path = "factory/features/F0003-other/backlog/F0003-S0001-x.md"

    assert _messages(path) == []


@pytest.mark.parametrize(
    ("feature_file_exists", "messages"),
    [(False, [MISSING_FEATURE_FILE]), (True, [])],
    ids=["missing", "present"],
)
def test_a_missing_feature_file_is_a_finding(
    feature_file_exists: bool, messages: list[str]
) -> None:
    path = "factory/features/F0002-work-item-data/backlog/F0002-S0001-x.md"

    assert _messages(path, feature_file_exists=feature_file_exists) == messages


def test_a_bad_name_in_a_bad_directory_without_feature_file_gives_three_findings_in_order() -> None:
    path = "factory/features/work-item-data/backlog/s0001.md"

    assert _messages(path, feature_file_exists=False) == [
        'the file name "s0001.md" is not F0000-S0000[-slug].md',
        'the feature directory "work-item-data" is not F0000[-slug]',
        "the feature file feature.md is missing in factory/features/work-item-data",
    ]
