"""Opening a story whose backlog body has sections but no journal appends the journal."""

from factory.application.boundaries import Boundaries
from factory.application.opening import WorkItemOpening
from factory.domain.pipeline_definition import PipelineDefinition
from human_clone import HumanClone

BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"


def test_a_body_with_sections_and_no_journal_gets_the_journal_at_its_end(
    boundaries: Boundaries, human: HumanClone, definition: PipelineDefinition
) -> None:
    human.push_file("main", BACKLOG_PATH, "# First story\n\n## Description\n\nText.\n")
    human.start(BACKLOG_PATH)
    boundaries.git.fetch()

    prepared = WorkItemOpening(boundaries, definition).prepare("F0001-S0001", PATH)

    assert prepared.document.body == (
        "# First story\n\n## Description\n\nText.\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
    )
