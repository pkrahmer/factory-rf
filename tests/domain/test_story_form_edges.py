"""The story form check at a section's edge: items right under a heading or right above one."""

import pytest

from domain.test_story_form import FORM, SMOKE, _state
from factory.domain.paths import LifecycleFolder
from factory.domain.story_form import FormFinding, check_story_form
from factory.domain.work_item import WorkItemDocument, WorkItemState

START = "# A story\n\n## Description\n\nText.\n\n## Interface\n\n"
CRITERIA = "1. It works.\n2. make check stays green.\n3. docs: none."
STARTED = _state(1, "done")
ENTRY_UNDER_HEADING = (
    "None.\n\n## Acceptance criteria\n\n"
    + CRITERIA
    + "\n\n## Smoke test\n\n"
    + SMOKE
    + "\n\n## Journal\n1. human: created.\n"
)


@pytest.mark.parametrize(
    ("rest", "folder", "state", "expected"),
    [
        pytest.param(
            "None.\n\n## Acceptance criteria\n"
            + CRITERIA
            + "\n\n## Smoke test\n\n"
            + SMOKE
            + "\n\n## Journal\n",
            "backlog",
            None,
            [],
            id="criterion-right-under-its-heading",
        ),
        pytest.param(
            "1. a numbered line\n## Acceptance criteria\n\n"
            + CRITERIA
            + "\n\n## Smoke test\n\n"
            + SMOKE
            + "\n\n## Journal\n",
            "backlog",
            None,
            [],
            id="numbered-line-right-above-the-criteria",
        ),
        pytest.param(
            "None.\n\n## Acceptance criteria\n\n"
            + CRITERIA
            + "\n\n## Smoke test\n\n"
            + SMOKE
            + "\n1. a numbered line\n## Journal\n\n1. human: created.\n",
            "done",
            STARTED,
            [],
            id="numbered-line-right-above-the-journal",
        ),
        pytest.param(
            ENTRY_UNDER_HEADING, "done", STARTED, [], id="entry-right-under-its-heading-started"
        ),
        pytest.param(
            ENTRY_UNDER_HEADING,
            "backlog",
            None,
            [FormFinding(line=25, message="a backlog story carries no journal entries")],
            id="entry-right-under-its-heading-backlog",
        ),
    ],
)
def test_items_count_from_the_line_right_after_their_heading_and_not_above_it(
    rest: str,
    folder: LifecycleFolder,
    state: WorkItemState | None,
    expected: list[FormFinding],
) -> None:
    document = WorkItemDocument(state=state, body=START + rest)

    assert check_story_form(document, FORM, folder=folder) == expected
