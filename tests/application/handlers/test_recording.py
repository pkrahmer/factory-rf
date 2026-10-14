"""The shared plumbing of the handlers: the event's target, commit subjects and the recorder."""

from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.handlers.recording import (
    Target,
    WorkItemRecorder,
    commit_subject,
    require_pull_request,
    target_of,
)
from factory.domain.errors import CannotHandle, PushFailed
from factory.domain.events import Event, EventKind
from factory.domain.journal import FACTORY, NewEntry, append_entry
from factory.domain.work_item import WorkItemSnapshot, WorkItemState
from git_support import remote_commit
from human_clone import HumanClone

SnapshotOf = Callable[[WorkItemState | None], WorkItemSnapshot]
StateWith = Callable[[int | None], WorkItemState]
EventOf = Callable[[EventKind, WorkItemSnapshot | None], Event]


def test_the_target_of_an_event_is_its_work_item_state_and_pull_request(
    snapshot_of: SnapshotOf, state_with: StateWith, event_of: EventOf
) -> None:
    snapshot = snapshot_of(state_with(5))

    target = target_of(event_of("comment", snapshot))

    assert target.snapshot == snapshot
    assert target.state == snapshot.document.state
    assert target.pull_request == 5


@pytest.mark.parametrize("kind", ["idle", "comment"])
def test_an_event_without_a_work_item_or_without_a_state_cannot_be_handled(
    snapshot_of: SnapshotOf, event_of: EventOf, kind: EventKind
) -> None:
    snapshot = None if kind == "idle" else snapshot_of(None)
    reason = (
        "the event names no work item" if snapshot is None else "work item F0001-S0001 has no state"
    )

    with pytest.raises(CannotHandle) as raised:
        target_of(event_of(kind, snapshot))

    assert raised.value.kind == kind
    assert raised.value.reason == reason


def test_a_pull_request_is_required_of_the_target(
    snapshot_of: SnapshotOf, state_with: StateWith
) -> None:
    with_pull = state_with(5)
    without_pull = state_with(None)

    assert (
        require_pull_request(
            Target(snapshot=snapshot_of(with_pull), state=with_pull, pull_request=5), "ask"
        )
        == 5
    )
    with pytest.raises(CannotHandle) as raised:
        require_pull_request(
            Target(snapshot=snapshot_of(without_pull), state=without_pull, pull_request=None),
            "ask",
        )
    assert raised.value.kind == "ask"
    assert raised.value.reason == "work item F0001-S0001 has no pull request"


def test_a_commit_subject_names_the_work_item() -> None:
    assert commit_subject("F0001-S0001", "x") == "work item F0001-S0001: x"


def test_check_out_drops_every_local_leftover_and_stands_at_the_remote_head(
    boundaries: Boundaries, *, checkout: GitCli, remote: Path, work_item: WorkItemSnapshot
) -> None:
    recorder = WorkItemRecorder(boundaries)
    recorder.check_out(work_item.branch)
    tracked = boundaries.checkout / work_item.path
    remote_text = tracked.read_text(encoding="utf-8")
    tracked.write_text(remote_text + "committed locally\n", encoding="utf-8")
    checkout.commit("never pushed")
    tracked.write_text(remote_text + "left uncommitted\n", encoding="utf-8")
    stray = boundaries.checkout / "stray.txt"
    stray.write_text("untracked\n", encoding="utf-8")

    recorder.check_out(work_item.branch)

    status = checkout.status()
    assert status.branch == work_item.branch
    assert status.head == remote_commit(remote, work_item.branch)
    assert status.changes == []
    assert tracked.read_text(encoding="utf-8") == remote_text
    assert not stray.exists()


def test_record_writes_commits_and_pushes_the_document(
    boundaries: Boundaries, *, checkout: GitCli, remote: Path, work_item: WorkItemSnapshot
) -> None:
    recorder = WorkItemRecorder(boundaries)
    recorder.check_out(work_item.branch)
    document = append_entry(
        recorder.read(work_item.path), NewEntry(speaker=FACTORY, kind="result", text="recorded")
    )

    commit = recorder.record(work_item.branch, work_item.path, document, "the subject")

    assert remote_commit(remote, work_item.branch) == commit
    [info] = checkout.log(commit, since=work_item.branch_commit)
    assert info.subject == "the subject"
    text = checkout.show_file(commit, work_item.path)
    assert text is not None
    assert boundaries.work_item_reader.parse(text) == document


@pytest.mark.parametrize("outcome", ["rejected", "unreachable"])
def test_publish_raises_push_failed_when_the_push_does_not_reach_the_remote(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    work_item: WorkItemSnapshot,
    outcome: str,
) -> None:
    recorder = WorkItemRecorder(boundaries)
    recorder.check_out(work_item.branch)
    if outcome == "rejected":
        human.push_file(work_item.branch, "human.txt", "pushed by the human\n")
    else:
        remote.rename(remote.with_name("moved.git"))
    human_head = remote_commit(remote, work_item.branch) if outcome == "rejected" else None
    document = append_entry(
        recorder.read(work_item.path), NewEntry(speaker=FACTORY, kind="result", text="recorded")
    )
    recorder.write(work_item.path, document)

    with pytest.raises(PushFailed) as raised:
        recorder.publish(work_item.branch, "the subject")

    assert raised.value.branch == work_item.branch
    assert raised.value.outcome == outcome
    if outcome == "rejected":
        assert remote_commit(remote, work_item.branch) == human_head


def test_a_target_is_frozen_and_forbids_unknown_keys(
    snapshot_of: SnapshotOf, state_with: StateWith
) -> None:
    state = state_with(5)
    snapshot = snapshot_of(state)
    target = Target(snapshot=snapshot, state=state, pull_request=5)
    model: type[BaseModel] = Target
    field = "pull_request"

    with pytest.raises(ValidationError):
        model(snapshot=snapshot, state=state, pull_request=5, extra="unknown")
    with pytest.raises(ValidationError):
        setattr(target, field, 6)
