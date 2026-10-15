"""The evaluation ranks a due feature's acceptance among the runnable work items of tier 4."""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.evaluation import EvaluationInput, PullRequestObservation, evaluate
from factory.domain.events import Event
from factory.domain.hosting import PullRequestView
from factory.domain.lease import ClaimStatus
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.domain.work_item import (
    Claim,
    WorkItemDocument,
    WorkItemSnapshot,
    WorkItemState,
    initial_state,
)

MAIN = "a" * 40
BRANCH_COMMIT = "b" * 40
PULL_REQUEST = 7
AT = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)

DEFINITION = PipelineDefinition(
    contract="1.0",
    stages={
        "intake": StageDefinition(role="intake", next=["approval"]),
        "approval": StageDefinition(approval=True, next=["done", "intake"]),
        "done": StageDefinition(),
    },
    roles={"intake": RoleDefinition(write_paths=["{work_item}"])},
    attempts_cap=2,
)


def _snapshot(work_item: str, state: WorkItemState) -> WorkItemSnapshot:
    directory = f"{work_item.split('-', maxsplit=1)[0]}-demo"
    return WorkItemSnapshot(
        id=work_item,
        path=f"factory/features/{directory}/in-progress/{work_item}-x.md",
        folder="in-progress",
        branch=f"work-item/{work_item}",
        branch_commit=BRANCH_COMMIT,
        document=WorkItemDocument(state=state, body="# T\n"),
    )


def _runnable(work_item: str) -> WorkItemSnapshot:
    return _snapshot(work_item, initial_state("intake"))


def _no_lookup(number: int) -> PullRequestObservation:
    raise AssertionError(f"pull request {number} must not be looked up")


def _open_lookup(number: int) -> PullRequestObservation:
    view = PullRequestView(
        number=number,
        branch="work-item/F0003-S0001",
        title="t",
        state="open",
        draft=False,
        merge_commit=None,
        url=f"https://example.test/{number}",
    )
    return PullRequestObservation(view=view, comments=[])


def _status(status: ClaimStatus) -> Callable[[WorkItemState], ClaimStatus]:
    return lambda _state: status


def _due(*snapshots: WorkItemSnapshot) -> EvaluationInput:
    return EvaluationInput(
        definition=DEFINITION, snapshots=list(snapshots), main_commit=MAIN, due=["F0002"]
    )


def test_due_is_empty_by_default_and_holds_feature_ids() -> None:
    plain = EvaluationInput(definition=DEFINITION, snapshots=[], main_commit=MAIN)

    assert plain.due == []
    assert _due().due == ["F0002"]


@pytest.mark.parametrize(
    "extra",
    [{"due": ["F002"]}, {"unknown": 1}],
    ids=["malformed-feature-id", "unknown-key"],
)
def test_evaluation_input_refuses_a_malformed_due_and_an_unknown_key(
    extra: dict[str, object],
) -> None:
    model: type[BaseModel] = EvaluationInput

    with pytest.raises(ValidationError):
        model(definition=DEFINITION, snapshots=[], main_commit=MAIN, **extra)


@pytest.mark.parametrize(
    ("work_item", "kind", "feature"),
    [("F0003-S0001", "acceptance_due", "F0002"), ("F0001-S0001", "run", None)],
    ids=["later-feature-story", "earlier-feature-story"],
)
def test_a_due_feature_ranks_after_earlier_and_before_later_features_stories(
    work_item: str, kind: str, feature: str | None
) -> None:
    snapshot = _runnable(work_item)

    event = evaluate(_due(snapshot), _no_lookup, _status("none"))

    assert (event.kind, event.feature) == (kind, feature)
    if kind == "acceptance_due":
        assert event.work_item is None
        assert event.remote_state == MAIN
    else:
        assert event.work_item == snapshot


def test_a_features_own_story_runs_before_its_due_acceptance() -> None:
    snapshot = _runnable("F0002-S0003")

    event = evaluate(_due(snapshot), _no_lookup, _status("none"))

    assert event == Event(kind="run", work_item=snapshot, remote_state=BRANCH_COMMIT)


def _waiting() -> WorkItemSnapshot:
    state = WorkItemState(stage="approval", pull_request=PULL_REQUEST, handed_over="approval")
    return _snapshot("F0003-S0001", state)


def _held() -> WorkItemSnapshot:
    claim = Claim(instance="factory-2", stage="intake", started_at=AT, lease_duration=60)
    return _snapshot("F0003-S0001", initial_state("intake").model_copy(update={"claim": claim}))


@pytest.mark.parametrize(
    ("snapshot", "lookup", "status"),
    [(_waiting(), _open_lookup, "none"), (_held(), _no_lookup, "held")],
    ids=["waiting-for-the-human", "claim-held"],
)
def test_a_waiting_work_item_and_a_held_claim_win_over_a_due_feature(
    snapshot: WorkItemSnapshot,
    lookup: Callable[[int], PullRequestObservation],
    status: ClaimStatus,
) -> None:
    event = evaluate(_due(snapshot), lookup, _status(status))

    assert (event.kind, event.work_item, event.feature) == ("idle", None, None)
