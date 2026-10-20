"""The board counts a feature's story in progress beside its backlog and done stories."""

from factory.application.board import BoardReader
from factory.application.boundaries import Boundaries
from factory.domain.board import FeatureRow
from git_support import PIPELINE_YAML
from human_clone import HumanClone

FEATURE = "factory/features/F0001-example"


def test_a_feature_row_counts_one_story_in_each_folder(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.push_file("main", f"{FEATURE}/backlog/F0001-S0002-second.md", "# Second story\n")
    human.push_file("main", f"{FEATURE}/done/F0001-S0003-third.md", "# Third story\n")
    human.start(f"{FEATURE}/backlog/F0001-S0001-first.md")
    boundaries.git.fetch()
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)

    view = BoardReader(boundaries).read(definition)

    assert view.features == [
        FeatureRow(
            feature="F0001",
            title="Example feature",
            backlog=1,
            in_progress=1,
            done=1,
            acceptance="incomplete",
        )
    ]
