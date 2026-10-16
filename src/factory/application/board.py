"""Reading the board from the remote-tracking refs: the features' counts and the work items."""

from pydantic import BaseModel, ConfigDict

from factory.application.acceptance_reading import AcceptanceReader, running_work_items
from factory.application.boundaries import Boundaries
from factory.application.work_items import RemoteWorkItems, read_feature_file
from factory.domain.board import BoardRow, FeatureRow, feature_rows, work_item_row
from factory.domain.identifiers import FeatureId, parse_feature_directory_name
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.sections import title
from factory.domain.work_item import StoryFile


class BoardView(BaseModel):
    """The board's content: its feature rows and its work item rows."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    features: list[FeatureRow]
    rows: list[BoardRow]


class BoardReader:
    """Reads the board from the last fetch; it fetches nothing and writes nothing."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Read through the git and the work item reader of `boundaries`."""
        self._boundaries = boundaries
        self._git = boundaries.git
        self._work_items = RemoteWorkItems(boundaries.git, boundaries.work_item_reader)

    def read(self, definition: PipelineDefinition) -> BoardView:
        """The board under `definition`: the acceptance column filled, a row per running acceptance.

        Raises `GitError` and `WorkItemFormatError`.
        """
        stories = [
            *self._work_items.list_stories("backlog"),
            *self._work_items.list_stories("in-progress"),
            *self._work_items.list_stories("done"),
        ]
        acceptances = AcceptanceReader(self._boundaries, definition)
        snapshots = running_work_items(self._work_items, acceptances, definition)
        return BoardView(
            features=acceptances.fill_board(feature_rows(stories, self._titles(stories))),
            rows=[work_item_row(snapshot) for snapshot in snapshots],
        )

    def _titles(self, stories: list[StoryFile]) -> dict[FeatureId, str]:
        titles: dict[FeatureId, str] = {}
        for directory in sorted({story.feature_directory for story in stories}):
            name = parse_feature_directory_name(directory)
            feature_title = self._feature_title(directory)
            if name is not None and feature_title is not None:
                titles.setdefault(name.id, feature_title)
        return titles

    def _feature_title(self, directory: str) -> str | None:
        text = read_feature_file(self._git, directory)
        return None if text is None else title(text)
