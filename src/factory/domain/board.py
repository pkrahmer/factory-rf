"""The board: one row per feature with its story counts, one per work item in progress."""

from collections.abc import Mapping, Sequence
from datetime import UTC
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, NonNegativeInt, PositiveInt

from factory.domain.identifiers import FeatureId, Name, WorkItemId, parse_feature_directory_name
from factory.domain.paths import LifecycleFolder
from factory.domain.sections import title
from factory.domain.work_item import Blocked, Claim, StoryFile, WorkItemSnapshot

AcceptanceStatus = Literal[
    "incomplete", "due", "in_flight", "merged_unrecorded", "accepted", "refused"
]

_ABSENT = "-"
_SEPARATOR = "  "
_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class BoardRow(BaseModel):
    """One work item in progress as the board shows it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_item: WorkItemId
    title: str
    folder: LifecycleFolder
    stage: Name | None
    blocked: Blocked | None
    claim: Claim | None
    running_since: AwareDatetime | None
    pull_request: PositiveInt | None


class FeatureRow(BaseModel):
    """One feature as the board shows it: its story files counted per lifecycle folder."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    feature: FeatureId
    title: str
    backlog: NonNegativeInt
    in_progress: NonNegativeInt
    done: NonNegativeInt
    acceptance: AcceptanceStatus | None = None


def work_item_row(snapshot: WorkItemSnapshot) -> BoardRow:
    """The board row of one work item, titled by its body's first `# ` title, else its id."""
    state = snapshot.document.state
    claim = None if state is None else state.claim
    return BoardRow(
        work_item=snapshot.id,
        title=title(snapshot.document.body) or snapshot.id,
        folder=snapshot.folder,
        stage=None if state is None else state.stage,
        blocked=None if state is None else state.blocked,
        claim=claim,
        running_since=None if claim is None else claim.started_at,
        pull_request=None if state is None else state.pull_request,
    )


def feature_rows(stories: Sequence[StoryFile], titles: Mapping[FeatureId, str]) -> list[FeatureRow]:
    """One row per feature of the stories, in id order, titled from `titles` or its directory."""
    by_feature: dict[FeatureId, list[StoryFile]] = {}
    for story in stories:
        directory = parse_feature_directory_name(story.feature_directory)
        if directory is not None:
            by_feature.setdefault(directory.id, []).append(story)
    return [_feature_row(feature, by_feature[feature], titles) for feature in sorted(by_feature)]


def _feature_row(
    feature: FeatureId, stories: Sequence[StoryFile], titles: Mapping[FeatureId, str]
) -> FeatureRow:
    folders = [story.folder for story in stories]
    return FeatureRow(
        feature=feature,
        title=titles.get(feature, stories[0].feature_directory),
        backlog=folders.count("backlog"),
        in_progress=folders.count("in-progress"),
        done=folders.count("done"),
    )


def render_board(features: Sequence[FeatureRow], rows: Sequence[BoardRow]) -> str:
    """The board as text: the features, then the work items, one line each."""
    lines = [
        "features",
        *(_feature_line(feature) for feature in features),
        "work items",
        *(_work_item_line(row) for row in rows),
    ]
    return "".join(f"{line}\n" for line in lines)


def _feature_line(feature: FeatureRow) -> str:
    return _SEPARATOR.join(
        [
            feature.feature,
            feature.title,
            f"backlog={feature.backlog}",
            f"in-progress={feature.in_progress}",
            f"done={feature.done}",
            f"acceptance={_or_absent(feature.acceptance)}",
        ]
    )


def _work_item_line(row: BoardRow) -> str:
    claim = None if row.claim is None else row.claim.instance
    since = None if row.running_since is None else row.running_since.astimezone(UTC)
    return _SEPARATOR.join(
        [
            row.work_item,
            row.title,
            row.folder,
            f"stage={_or_absent(row.stage)}",
            f"blocked={_or_absent(row.blocked)}",
            f"claim={_or_absent(claim)}",
            f"running_since={_ABSENT if since is None else since.strftime(_TIME_FORMAT)}",
            f"pull_request={_or_absent(row.pull_request)}",
        ]
    )


def _or_absent(value: object) -> str:
    return _ABSENT if value is None else str(value)
