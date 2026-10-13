"""The names of the factory's tree, the paths of work items and their sidecars."""

import pytest

from factory.domain.paths import (
    BRANCH_PREFIX,
    COST_RECORDS_SUFFIX,
    FACTORY_DIRECTORY,
    FEATURE_FILE_NAME,
    FEATURE_FORM_FILE,
    FEATURES_DIRECTORY,
    LABEL_PREFIX,
    LIFECYCLE_FOLDERS,
    MAIN_BRANCH,
    PIPELINE_DEFINITION_FILE,
    REMOTE,
    STORY_FORM_FILE,
    LifecycleFolder,
    cost_records_path,
    folder_of,
    work_item_path,
)
from source_search import imported_modules, modules


def test_path_constants_have_their_stated_values() -> None:
    assert FACTORY_DIRECTORY == "factory"
    assert PIPELINE_DEFINITION_FILE == "factory/pipeline.yml"
    assert STORY_FORM_FILE == "factory/story-form.md"
    assert FEATURE_FORM_FILE == "factory/feature-form.md"
    assert FEATURES_DIRECTORY == "factory/features"
    assert FEATURE_FILE_NAME == "feature.md"
    assert LIFECYCLE_FOLDERS == ("backlog", "in-progress", "done")
    assert COST_RECORDS_SUFFIX == ".costs.jsonl"
    assert BRANCH_PREFIX == "work-item/"
    assert REMOTE == "origin"
    assert MAIN_BRANCH == "main"
    assert LABEL_PREFIX == "stage:"


def test_work_item_path_lies_in_the_folder_of_its_feature_directory() -> None:
    path = work_item_path("F0002-work-item-data", "in-progress", "F0002-S0001-x.md")

    assert path == "factory/features/F0002-work-item-data/in-progress/F0002-S0001-x.md"


def test_cost_records_path_sits_beside_the_work_item() -> None:
    path = cost_records_path("factory/features/F0002-a/done/F0002-S0001-x.md")

    assert path == "factory/features/F0002-a/done/F0002-S0001-x.costs.jsonl"


def test_cost_records_path_refuses_a_path_that_is_not_markdown() -> None:
    with pytest.raises(ValueError, match=r"."):
        cost_records_path("factory/features/F0002-a/done/F0002-S0001-x.txt")


@pytest.mark.parametrize("folder", ["backlog", "in-progress", "done"])
@pytest.mark.parametrize("file_name", ["F0002-S0001-x.md", "F0002-A0001.md"])
def test_folder_of_a_work_item_path_is_its_lifecycle_folder(
    folder: LifecycleFolder, file_name: str
) -> None:
    assert folder_of(f"factory/features/F0002-x/{folder}/{file_name}") == folder


@pytest.mark.parametrize(
    "path",
    [
        "factory/features/F0002-x/drafts/F0002-S0001.md",
        "factory/features/F0002-x/ongoing/F0002-S0001.md",
        "factory/features/F0002-x/backlog/extra/F0002-S0001.md",
        "factory/features/F0002-x/F0002-S0001.md",
        "factory/features/F0002-x/archive/F0002-S0001.md",
        "docs/features/F0002-x/backlog/F0002-S0001.md",
        "factory/features/f0002-x/backlog/F0002-S0001.md",
        "factory/features/F0002-x/backlog/F0002-S0001.costs.jsonl",
        "factory/features/F0002-x/backlog/.gitkeep",
        "factory/features/F0002-x/backlog/README.md",
    ],
)
def test_folder_of_a_path_that_is_no_work_item_is_none(path: str) -> None:
    assert folder_of(path) is None


@pytest.mark.parametrize("module", ["factory.domain.identifiers", "factory.domain.paths"])
def test_identity_modules_import_no_io_or_clock(module: str) -> None:
    forbidden = {"os", "pathlib", "subprocess", "socket", "datetime", "time"}
    imported = imported_modules(modules()[module])

    assert {name for name in imported if name.split(".")[0] in forbidden} == set()
