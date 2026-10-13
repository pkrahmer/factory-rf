"""The identifiers of the factory's work items, their file names, order and branch names."""

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# Defined here rather than beside the other names in paths, which builds on this module.
BRANCH_PREFIX = "work-item/"
FEATURE_ID = r"F\d{4}"
STORY_ID = r"F\d{4}-S\d{4}"
ACCEPTANCE_ID = r"F\d{4}-A\d{4}"
_SLUG = r"[a-z0-9]+(-[a-z0-9]+)*"
_WORK_ITEM_ID = r"F\d{4}-[SA]\d{4}"

WorkItemId = Annotated[str, StringConstraints(pattern=r"^F\d{4}-[SA]\d{4}$")]
FeatureId = Annotated[str, StringConstraints(pattern=r"^F\d{4}$")]
Name = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$")]
Slug = Annotated[str, StringConstraints(pattern=rf"^{_SLUG}$")]

_WORK_ITEM_FILE_NAME = re.compile(rf"(?P<id>{_WORK_ITEM_ID})(-(?P<slug>{_SLUG}))?\.md")
_FEATURE_DIRECTORY_NAME = re.compile(rf"(?P<id>{FEATURE_ID})(-(?P<slug>{_SLUG}))?")
_WORK_ITEM_BRANCH = re.compile(rf"{re.escape(BRANCH_PREFIX)}(?P<id>{_WORK_ITEM_ID})")


class WorkItemFileName(BaseModel):
    """The parts of a work item's file name: its id and an optional slug."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: WorkItemId
    slug: Slug | None


class FeatureDirectoryName(BaseModel):
    """The parts of a feature directory's name: its id and an optional slug."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: FeatureId
    slug: Slug | None


def parse_work_item_file_name(name: str) -> WorkItemFileName | None:
    """Split a work item file name into id and slug, or return None if it is none."""
    match = _WORK_ITEM_FILE_NAME.fullmatch(name)
    if match is None:
        return None
    return WorkItemFileName(id=match["id"], slug=match["slug"])


def parse_feature_directory_name(name: str) -> FeatureDirectoryName | None:
    """Split a feature directory name into id and slug, or return None if it is none."""
    match = _FEATURE_DIRECTORY_NAME.fullmatch(name)
    if match is None:
        return None
    return FeatureDirectoryName(id=match["id"], slug=match["slug"])


def is_acceptance(work_item: WorkItemId) -> bool:
    """Tell whether the work item is a feature's acceptance rather than a story."""
    return re.fullmatch(ACCEPTANCE_ID, _checked(work_item)) is not None


def feature_of(work_item: WorkItemId) -> FeatureId:
    """Return the id of the feature the work item belongs to."""
    return _checked(work_item).split("-")[0]


def work_item_order(work_item: WorkItemId) -> tuple[str, int, str]:
    """Return the sort key that keeps string order but puts acceptances after their stories."""
    kind_rank = 1 if is_acceptance(work_item) else 0
    return (feature_of(work_item), kind_rank, work_item)


def branch_name(work_item: WorkItemId) -> str:
    """Return the name of the branch the work item is worked on."""
    return BRANCH_PREFIX + _checked(work_item)


def work_item_of_branch(branch: str) -> WorkItemId | None:
    """Return the id of the work item a branch belongs to, or None for any other branch."""
    match = _WORK_ITEM_BRANCH.fullmatch(branch)
    if match is None:
        return None
    return match["id"]


def _checked(work_item: str) -> str:
    # Callers outside Pydantic pass plain strings; a malformed id must fail loudly here.
    if re.fullmatch(_WORK_ITEM_ID, work_item) is None:
        raise ValueError(f"not a work item id: {work_item!r}")
    return work_item
