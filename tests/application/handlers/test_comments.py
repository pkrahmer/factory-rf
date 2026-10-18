"""The human's comments on the pull request, copied into the journal by comment id."""

from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.handlers.comments import CommentCopier, CopyResult
from factory.domain.hosting import FACTORY_MARKER, PostKey, PullRequestComment
from factory.domain.journal import FACTORY, HUMAN, JournalRecord, NewEntry, append_entry, entry_text
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import remote_commit

StateWith = Callable[[int | None], WorkItemState]
SnapshotOf = Callable[[WorkItemState | None], WorkItemSnapshot]
CREATED = JournalRecord(number=1, speaker=HUMAN, kind="created")


def _comment(id: int, body: str, created_at: datetime | None = None) -> PullRequestComment:
    return PullRequestComment.from_body(
        id=id,
        author="human",
        body=body,
        created_at=created_at or datetime(2026, 10, 12, 9, 0, tzinfo=UTC),
    )


def _document(snapshot_of: SnapshotOf, state: WorkItemState) -> WorkItemDocument:
    return snapshot_of(state).document


def _remote_document(
    boundaries: Boundaries, checkout: GitCli, work_item: WorkItemSnapshot
) -> WorkItemDocument:
    checkout.fetch()
    text = checkout.show_file(f"origin/{work_item.branch}", work_item.path)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def _state_of(document: WorkItemDocument) -> WorkItemState:
    assert document.state is not None
    return document.state


def _comment_records(document: WorkItemDocument) -> int:
    return sum(1 for record in _state_of(document).journal if record.kind == "comment")


def test_unread_leaves_out_every_comment_with_the_marker_whatever_its_author(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    pull_request: int,
    state_with: StateWith,
) -> None:
    hosting.add_human_comment(pull_request, f"marked by the human\n\n{FACTORY_MARKER}")
    hosting.post_comment(
        pull_request, "a question", PostKey(work_item="F0001-S0001", kind="question", n="1")
    )
    unmarked = hosting.add_human_comment(pull_request, "an answer")

    unread = CommentCopier(boundaries).unread(state_with(pull_request), pull_request)

    assert [comment.id for comment in unread] == [unmarked]


def test_unread_returns_unmarked_comments_of_any_author_and_any_prefix(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    pull_request: int,
    state_with: StateWith,
) -> None:
    other = hosting.add_human_comment(pull_request, "from another login", author="someone-else")
    prefixed = hosting.add_human_comment(pull_request, "factory: still the human")

    unread = CommentCopier(boundaries).unread(state_with(pull_request), pull_request)

    assert [comment.id for comment in unread] == [other, prefixed]


def test_unread_leaves_out_the_comments_read_and_keeps_the_listed_order(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    pull_request: int,
    state_with: StateWith,
) -> None:
    first = hosting.add_human_comment(pull_request, "first")
    second = hosting.add_human_comment(pull_request, "second")
    third = hosting.add_human_comment(pull_request, "third")
    state = state_with(pull_request).model_copy(update={"comments_read": [first]})

    unread = CommentCopier(boundaries).unread(state, pull_request)

    assert [comment.id for comment in unread] == [second, third]


def test_append_adds_one_dated_human_comment_entry_per_comment_in_order(
    boundaries: Boundaries, *, snapshot_of: SnapshotOf, state_with: StateWith, clock: ManualClock
) -> None:
    document = _document(snapshot_of, state_with(1))
    late_in_berlin = datetime(2026, 10, 13, 1, 30, tzinfo=timezone(timedelta(hours=2)))
    comments = [_comment(4, "a\r\nb\r\n", late_in_berlin), _comment(2, "  single line  \n")]

    appended = CommentCopier(boundaries).append(document, comments)

    stamp = {"at": clock.now(), "stage": _state_of(document).stage}
    assert _state_of(appended).journal == [
        CREATED,
        JournalRecord(number=2, speaker=HUMAN, kind="comment", **stamp),
        JournalRecord(number=3, speaker=HUMAN, kind="comment", **stamp),
    ]
    assert entry_text(appended, 2) == "a\nb"
    assert entry_text(appended, 3) == "single line"
    assert "\r" not in appended.body
    assert "2. 2026-10-12 human: a\n" in appended.body
    assert "3. 2026-10-12 human: single line" in appended.body


def test_append_marks_a_blank_comment_read_without_an_entry(
    boundaries: Boundaries, *, snapshot_of: SnapshotOf, state_with: StateWith
) -> None:
    document = _document(snapshot_of, state_with(1))

    appended = CommentCopier(boundaries).append(document, [_comment(3, ""), _comment(5, " \n\t ")])

    assert _state_of(appended).comments_read == [3, 5]
    assert _state_of(appended).journal == [CREATED]
    assert appended.body == document.body


def test_append_keeps_comments_read_sorted_without_repeats(
    boundaries: Boundaries, *, snapshot_of: SnapshotOf, state_with: StateWith
) -> None:
    state = state_with(1).model_copy(update={"comments_read": [3, 7]})
    document = _document(snapshot_of, state)
    comments = [_comment(9, "nine"), _comment(3, "three"), _comment(5, "five")]

    appended = CommentCopier(boundaries).append(document, comments)

    assert _state_of(appended).comments_read == [3, 5, 7, 9]


def test_copy_records_and_pushes_the_comments_before_anything_else(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    remote: Path,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    first = hosting.add_human_comment(pull_request, "first")
    second = hosting.add_human_comment(pull_request, "second")

    result = CommentCopier(boundaries).copy(work_item, pull_request)

    assert result.recorded == [first, second]
    assert result.commit == remote_commit(remote, work_item.branch)
    recorded = _remote_document(boundaries, checkout, work_item)
    assert _state_of(recorded).comments_read == [first, second]
    assert _comment_records(recorded) == 2
    assert hosting.factory_posts(pull_request) == []


def test_copy_with_nothing_unread_records_nothing(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    hosting.post_comment(
        pull_request, "a question", PostKey(work_item="F0001-S0001", kind="question", n="1")
    )

    result = CommentCopier(boundaries).copy(work_item, pull_request)

    assert result == CopyResult(recorded=[], commit=None)
    assert remote_commit(remote, work_item.branch) == work_item.branch_commit


def test_a_comment_after_a_factory_post_is_copied_by_the_next_copy(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    copier = CommentCopier(boundaries)
    first = hosting.add_human_comment(pull_request, "first")
    copier.copy(work_item, pull_request)
    hosting.post_comment(
        pull_request, "a question", PostKey(work_item="F0001-S0001", kind="question", n="1")
    )
    later = hosting.add_human_comment(pull_request, "the answer")

    result = copier.copy(work_item, pull_request)

    assert result.recorded == [later]
    recorded = _remote_document(boundaries, checkout, work_item)
    assert _state_of(recorded).comments_read == [first, later]
    assert _comment_records(recorded) == 2


def test_a_deleted_comment_neither_skips_nor_repeats_any_other(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    copier = CommentCopier(boundaries)
    ids = [hosting.add_human_comment(pull_request, text) for text in ("one", "two", "three")]
    copier.copy(work_item, pull_request)
    hosting.delete_comment(pull_request, ids[1])
    new = hosting.add_human_comment(pull_request, "four")

    result = copier.copy(work_item, pull_request)

    assert result.recorded == [new]
    recorded = _remote_document(boundaries, checkout, work_item)
    assert _state_of(recorded).comments_read == [*ids, new]
    assert _comment_records(recorded) == 4


def test_adjust_sees_the_appended_document_and_lands_in_the_same_commit(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    calls: list[tuple[WorkItemDocument, list[PullRequestComment]]] = []

    def adjust(
        document: WorkItemDocument, comments: Sequence[PullRequestComment]
    ) -> WorkItemDocument:
        calls.append((document, list(comments)))
        return append_entry(document, NewEntry(speaker=FACTORY, kind="result", text="adjusted"))

    copier = CommentCopier(boundaries)
    copier.copy(work_item, pull_request, adjust)
    assert calls == []

    answer = hosting.add_human_comment(pull_request, "an answer")
    blank = hosting.add_human_comment(pull_request, "   ")
    result = copier.copy(work_item, pull_request, adjust)

    [(document, comments)] = calls
    assert [comment.id for comment in comments] == [answer, blank]
    assert _state_of(document).comments_read == [answer, blank]
    assert [record.kind for record in _state_of(document).journal] == ["created", "comment"]
    assert result.commit is not None
    assert len(checkout.log(result.commit, since=work_item.branch_commit)) == 1
    recorded = _remote_document(boundaries, checkout, work_item)
    assert [record.kind for record in _state_of(recorded).journal] == [
        "created",
        "comment",
        "result",
    ]


def test_a_kill_before_the_push_leaves_the_remote_and_the_next_copy_records_once(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    remote: Path,
    kill_points: KillPoints,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    ids = [hosting.add_human_comment(pull_request, text) for text in ("one", "two")]
    kill_points.arm(KillPoint.BEFORE_PUSH)

    with pytest.raises(InjectedKill):
        CommentCopier(boundaries).copy(work_item, pull_request)

    assert remote_commit(remote, work_item.branch) == work_item.branch_commit
    result = CommentCopier(boundaries).copy(work_item, pull_request)
    assert result.recorded == ids
    recorded = _remote_document(boundaries, checkout, work_item)
    assert _state_of(recorded).comments_read == ids
    assert _comment_records(recorded) == 2


@pytest.mark.parametrize(
    ("commit", "accepted"),
    [("a" * 40, True), ("a" * 39, False), ("a" * 39 + "A", False)],
    ids=["forty-lowercase", "thirty-nine", "uppercase"],
)
def test_a_copy_result_commit_is_a_commit_id(commit: str, accepted: bool) -> None:
    if accepted:
        assert CopyResult(recorded=[], commit=commit).commit == commit
    else:
        with pytest.raises(ValidationError):
            CopyResult(recorded=[], commit=commit)
