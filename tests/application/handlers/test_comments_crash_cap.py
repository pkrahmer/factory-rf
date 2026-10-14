"""The human's answer to the crash-cap question ends the wait and resets the crash counter."""

from crash_support import (
    BRANCH,
    STORY_TITLE,
    WORK_ITEM,
    Rerun,
    claim,
    crash_event,
    handler,
    remote_state,
    snapshot,
)
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.handlers.comments import CommentHandler
from factory.domain.events import Event
from human_clone import HumanClone


def test_an_answer_to_the_crash_cap_question_unblocks_and_resets_the_crashes(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService
) -> None:
    number = hosting.create_pull_request(
        BRANCH, f"{WORK_ITEM}: {STORY_TITLE}", "body", draft=True
    ).number
    claimed = claim(boundaries, human, attempts=1, pull_request=number)
    handler(boundaries, claimed.definition, Rerun()).handle(crash_event(snapshot(boundaries)))
    assert remote_state(boundaries).blocked == "crash_cap"
    hosting.add_human_comment(number, "Rerun it.")
    work_item = snapshot(boundaries)
    assert work_item.branch_commit is not None

    CommentHandler(boundaries).handle(
        Event(kind="comment", work_item=work_item, remote_state=work_item.branch_commit)
    )

    after = remote_state(boundaries)
    assert after.blocked is None
    assert after.crashes == 0
    assert after.attempts == 1
