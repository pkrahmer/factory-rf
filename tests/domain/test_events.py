"""An event names what the watcher saw: its kind, its work item or feature, the remote state."""

from typing import get_args

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.events import Event, EventKind
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, initial_state

WORK_ITEM = "F0001-S0001"
FEATURE = "F0001"
COMMIT = "a" * 40
ALL_KINDS: list[str] = list(get_args(EventKind))
WITHOUT_WORK_ITEM = ["idle", "acceptance_due"]
WITH_WORK_ITEM = [kind for kind in ALL_KINDS if kind not in WITHOUT_WORK_ITEM]


def _snapshot() -> WorkItemSnapshot:
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=f"factory/features/F0001-demo/in-progress/{WORK_ITEM}-x.md",
        folder="in-progress",
        branch=f"work-item/{WORK_ITEM}",
        branch_commit=None,
        document=WorkItemDocument(state=initial_state("intake"), body="# T\n"),
    )


def _accepted(kind: str) -> Event:
    model: type[BaseModel] = Event
    work_item = None if kind in WITHOUT_WORK_ITEM else _snapshot()
    feature = FEATURE if kind == "acceptance_due" else None
    event = model(kind=kind, work_item=work_item, feature=feature, remote_state=COMMIT)
    assert isinstance(event, Event)
    return event


def test_the_kinds_are_the_thirteen_named() -> None:
    assert sorted(ALL_KINDS) == sorted(
        [
            "run",
            "comment",
            "ask",
            "merged",
            "closed",
            "reject",
            "hand_over",
            "crash",
            "expired",
            "duplicate",
            "pull_request_lookup",
            "acceptance_due",
            "idle",
        ]
    )
    assert len(WITH_WORK_ITEM) == 11


@pytest.mark.parametrize(
    ("kind", "key"),
    [("run", "run:F0001-S0001"), ("acceptance_due", "acceptance_due:F0001"), ("idle", "idle:-")],
    ids=["work-item", "feature", "neither"],
)
def test_key_names_the_kind_and_the_work_item_or_feature(kind: str, key: str) -> None:
    assert _accepted(kind).key == key


@pytest.mark.parametrize("kind", WITHOUT_WORK_ITEM)
def test_idle_and_acceptance_due_refuse_a_work_item(kind: str) -> None:
    model: type[BaseModel] = Event
    feature = FEATURE if kind == "acceptance_due" else None

    with pytest.raises(ValidationError):
        model(kind=kind, work_item=_snapshot(), feature=feature, remote_state=COMMIT)


@pytest.mark.parametrize("kind", WITH_WORK_ITEM)
def test_every_other_kind_refuses_a_missing_work_item(kind: str) -> None:
    model: type[BaseModel] = Event

    with pytest.raises(ValidationError):
        model(kind=kind, work_item=None, remote_state=COMMIT)


@pytest.mark.parametrize("kind", [kind for kind in ALL_KINDS if kind != "acceptance_due"])
def test_a_feature_is_refused_for_every_kind_but_acceptance_due(kind: str) -> None:
    model: type[BaseModel] = Event
    work_item = None if kind in WITHOUT_WORK_ITEM else _snapshot()

    with pytest.raises(ValidationError):
        model(kind=kind, work_item=work_item, feature=FEATURE, remote_state=COMMIT)


def test_acceptance_due_refuses_a_missing_feature() -> None:
    model: type[BaseModel] = Event

    with pytest.raises(ValidationError):
        model(kind="acceptance_due", work_item=None, remote_state=COMMIT)


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_every_accepted_pairing_builds(kind: str) -> None:
    event = _accepted(kind)

    assert event.kind == kind
    assert event.pull_request is None
    assert event.detail == ""


@pytest.mark.parametrize(("kind", "accepted"), [("idle", True), ("other", False)])
def test_event_accepts_only_a_known_kind(kind: str, accepted: bool) -> None:
    model: type[BaseModel] = Event

    if accepted:
        assert isinstance(model(kind=kind, work_item=None, remote_state=COMMIT), Event)
    else:
        with pytest.raises(ValidationError):
            model(kind=kind, work_item=None, remote_state=COMMIT)


@pytest.mark.parametrize(
    ("remote_state", "accepted"),
    [("a" * 40, True), ("a" * 39, False), ("A" + "a" * 39, False)],
    ids=["40-lower-hex", "39-characters", "upper-case"],
)
def test_event_accepts_only_a_full_lower_case_commit_id(remote_state: str, accepted: bool) -> None:
    model: type[BaseModel] = Event

    if accepted:
        event = model(kind="idle", work_item=None, remote_state=remote_state)
        assert isinstance(event, Event)
        assert event.remote_state == remote_state
    else:
        with pytest.raises(ValidationError):
            model(kind="idle", work_item=None, remote_state=remote_state)
