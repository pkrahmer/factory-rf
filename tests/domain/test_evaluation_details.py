"""The human tier's events carry their exact details, and the agent tier follows the claim."""

import pytest

from evaluation_support import (
    _at_approval,
    _blocked,
    _claimed,
    _ClaimStatus,
    _evaluate,
    _factory_comment,
    _Lookup,
    _snapshot,
    _view,
)
from factory.domain.evaluation import question_posted
from factory.domain.hosting import PullRequestComment, PullRequestView
from factory.domain.lease import ClaimStatus
from factory.domain.work_item import WorkItemState


@pytest.mark.parametrize(
    ("state", "view", "kind", "detail"),
    [
        pytest.param(_at_approval(), _view("merged"), "merged", "", id="merged"),
        pytest.param(_at_approval(), _view("closed"), "closed", "", id="closed"),
        pytest.param(_at_approval(handed_over=None), _view(), "hand_over", "", id="hand-over"),
        pytest.param(_blocked(), _view(), "ask", "", id="ask"),
        pytest.param(
            _blocked(pull_request=None), _view(), "ask", "no pull request", id="ask-no-pull-request"
        ),
    ],
)
def test_the_human_tiers_events_carry_their_exact_detail(
    state: WorkItemState, view: PullRequestView, kind: str, detail: str
) -> None:
    event = _evaluate(_snapshot(1, state), lookup=_Lookup(view=view))

    assert event.kind == kind
    assert event.detail == detail


@pytest.mark.parametrize(
    ("state", "comments", "posted"),
    [
        pytest.param(None, [], False, id="no-state"),
        pytest.param(_blocked(), [_factory_comment(1)], True, id="blocked"),
    ],
)
def test_a_question_is_posted_only_for_a_work_item_with_a_state(
    state: WorkItemState | None, comments: list[PullRequestComment], posted: bool
) -> None:
    assert question_posted(_snapshot(1, state), comments) is posted


@pytest.mark.parametrize(
    ("status", "kind", "detail", "work_item"),
    [
        pytest.param("none", "run", "", "F0001-S0001", id="none"),
        pytest.param("own", "crash", "", "F0001-S0001", id="own"),
        pytest.param("expired", "expired", "", "F0001-S0001", id="expired"),
        pytest.param("held", "idle", "F0001-S0001 is held by factory-2", None, id="held"),
    ],
)
def test_the_agent_tier_follows_the_claim_status(
    status: ClaimStatus, kind: str, detail: str, work_item: str | None
) -> None:
    event = _evaluate(_snapshot(1, _claimed()), claim_status=_ClaimStatus(status))

    assert event.kind == kind
    assert event.detail == detail
    assert (None if event.work_item is None else event.work_item.id) == work_item
