"""The path of a work item file moved to another lifecycle folder of its feature."""

import pytest

from factory.domain.archive import destination_path
from factory.domain.paths import LifecycleFolder

IN_PROGRESS = "factory/features/F0001-todo/in-progress/F0001-S0001-x.md"


@pytest.mark.parametrize(
    ("folder", "expected"),
    [
        ("done", "factory/features/F0001-todo/done/F0001-S0001-x.md"),
        ("backlog", "factory/features/F0001-todo/backlog/F0001-S0001-x.md"),
    ],
)
def test_the_destination_is_the_same_file_in_the_folder_of_the_same_feature(
    folder: LifecycleFolder, expected: str
) -> None:
    assert destination_path(IN_PROGRESS, folder) == expected


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "factory/features/F0001-todo/feature.md",
        "factory/features/F0001-todo/drafts/F0001-S0001-x.md",
    ],
)
def test_a_path_in_no_lifecycle_folder_has_no_destination(path: str) -> None:
    with pytest.raises(ValueError, match=r".+"):
        destination_path(path, "done")
