"""The fixed names of the factory's branches, labels and tree, and the paths of work items."""

from typing import Literal

from factory.domain import identifiers
from factory.domain.identifiers import parse_feature_directory_name, parse_work_item_file_name

REMOTE = "origin"
MAIN_BRANCH = "main"
FACTORY_DIRECTORY = "factory"
PIPELINE_DEFINITION_FILE = "factory/pipeline.yml"
STORY_FORM_FILE = "factory/story-form.md"
FEATURE_FORM_FILE = "factory/feature-form.md"
FEATURES_DIRECTORY = "factory/features"
FEATURE_FILE_NAME = "feature.md"
LifecycleFolder = Literal["backlog", "in-progress", "done"]
LIFECYCLE_FOLDERS: tuple[LifecycleFolder, ...] = ("backlog", "in-progress", "done")
COST_RECORDS_SUFFIX = ".costs.jsonl"
BRANCH_PREFIX = identifiers.BRANCH_PREFIX
LABEL_PREFIX = "stage:"

_WORK_ITEM_SUFFIX = ".md"


def work_item_path(feature_directory: str, folder: LifecycleFolder, file_name: str) -> str:
    """Return the repository path of a work item file in a feature's lifecycle folder."""
    return f"{FEATURES_DIRECTORY}/{feature_directory}/{folder}/{file_name}"


def cost_records_path(work_item_path: str) -> str:
    """Return the path of the cost-record sidecar that sits beside a work item file."""
    if not work_item_path.endswith(_WORK_ITEM_SUFFIX):
        raise ValueError(f"not a work item path: {work_item_path!r}")
    return work_item_path.removesuffix(_WORK_ITEM_SUFFIX) + COST_RECORDS_SUFFIX


def folder_of(path: str) -> LifecycleFolder | None:
    """Return the lifecycle folder of a work item path, or None for any other path."""
    prefix = FEATURES_DIRECTORY + "/"
    if not path.startswith(prefix):
        return None
    parts = path.removeprefix(prefix).split("/")
    if len(parts) != 3:
        return None
    feature_directory, folder, file_name = parts
    if parse_feature_directory_name(feature_directory) is None:
        return None
    if parse_work_item_file_name(file_name) is None:
        return None
    for lifecycle_folder in LIFECYCLE_FOLDERS:
        if folder == lifecycle_folder:
            return lifecycle_folder
    return None
