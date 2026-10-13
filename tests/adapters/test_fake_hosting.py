"""The hosting-service fake: pull requests, comments and posts in memory."""

from datetime import UTC, date, timedelta

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.application.hosting import HostingService
from factory.domain.errors import HostingServiceError
from factory.domain.hosting import PostKey, PullRequestView, render_post
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints

BRANCH = "work-item/F0001-S0001"
COMMIT = "a" * 40
KEY = PostKey(work_item="F0001-S0001", kind="question", n="2")


def _open(hosting: FakeHostingService, branch: str = BRANCH) -> PullRequestView:
    return hosting.create_pull_request(branch, "title", "body", draft=True)


def test_created_pull_requests_are_open_numbered_and_carry_url_description_and_no_labels(
    hosting: FakeHostingService,
) -> None:
    first = hosting.create_pull_request(BRANCH, "title", "body", draft=True)
    second = hosting.create_pull_request("work-item/F0001-S0002", "other", "text", draft=False)

    assert first.number == 1
    assert first.state == "open"
    assert first.branch == BRANCH
    assert first.title == "title"
    assert first.draft is True
    assert first.merge_commit is None
    assert first.url == "https://fake.invalid/pull/1"
    assert second.number == 2
    assert second.draft is False
    assert hosting.description(1) == "body"
    assert hosting.labels(1) == []


def test_pull_requests_lists_every_state_ordered_by_number(hosting: FakeHostingService) -> None:
    _open(hosting, "work-item/F0001-S0001")
    _open(hosting, "work-item/F0001-S0002")
    _open(hosting, "work-item/F0001-S0003")
    hosting.close_by_human(1)
    hosting.merge_by_human(2, COMMIT)

    pulls = hosting.pull_requests()

    assert [pull.number for pull in pulls] == [1, 2, 3]
    assert [pull.state for pull in pulls] == ["closed", "merged", "open"]


def test_find_open_pull_request_returns_only_an_open_one(hosting: FakeHostingService) -> None:
    _open(hosting, "work-item/F0001-S0001")
    closed = _open(hosting, "work-item/F0001-S0002")
    merged = _open(hosting, "work-item/F0001-S0003")
    hosting.close_by_human(closed.number)
    hosting.merge_by_human(merged.number, COMMIT)

    found = hosting.find_open_pull_request("work-item/F0001-S0001")

    assert found is not None
    assert found.number == 1
    assert found.state == "open"
    assert hosting.find_open_pull_request("work-item/F0001-S0009") is None
    assert hosting.find_open_pull_request("work-item/F0001-S0002") is None
    assert hosting.find_open_pull_request("work-item/F0001-S0003") is None


def test_human_close_and_merge_set_state_and_merge_commit(hosting: FakeHostingService) -> None:
    closed = _open(hosting, "work-item/F0001-S0001")
    merged = _open(hosting, "work-item/F0001-S0002")
    hosting.close_by_human(closed.number)
    hosting.merge_by_human(merged.number, COMMIT)

    after_close = hosting.get_pull_request(closed.number)
    after_merge = hosting.get_pull_request(merged.number)

    assert after_close.state == "closed"
    assert after_close.merge_commit is None
    assert after_merge.state == "merged"
    assert after_merge.merge_commit == COMMIT
    assert after_merge.draft is True


def test_close_and_reopen_toggle_the_state(hosting: FakeHostingService) -> None:
    pull = _open(hosting)

    hosting.close(pull.number)
    assert hosting.get_pull_request(pull.number).state == "closed"
    hosting.reopen(pull.number)
    assert hosting.get_pull_request(pull.number).state == "open"


def test_set_draft_and_set_description_change_the_pull_request(
    hosting: FakeHostingService,
) -> None:
    pull = _open(hosting)

    hosting.set_draft(pull.number, False)
    assert hosting.get_pull_request(pull.number).draft is False
    hosting.set_draft(pull.number, True)
    assert hosting.get_pull_request(pull.number).draft is True
    hosting.set_description(pull.number, "new")
    assert hosting.description(pull.number) == "new"


def test_set_labels_replaces_only_stage_labels(hosting: FakeHostingService) -> None:
    pull = _open(hosting)

    hosting.set_labels(pull.number, ["bug"])
    hosting.set_labels(pull.number, ["stage:doing"])
    assert hosting.labels(pull.number) == ["bug", "stage:doing"]
    hosting.set_labels(pull.number, ["stage:review"])
    assert hosting.labels(pull.number) == ["bug", "stage:review"]


def test_comment_ids_rise_across_pull_requests_with_a_second_apart(
    hosting: FakeHostingService,
) -> None:
    one = _open(hosting, "work-item/F0001-S0001")
    two = _open(hosting, "work-item/F0001-S0002")

    ids = [
        hosting.add_human_comment(one.number, "first"),
        hosting.add_human_comment(two.number, "second"),
        hosting.add_human_comment(one.number, "third"),
    ]
    comments_one = hosting.list_comments(one.number)
    comments_two = hosting.list_comments(two.number)

    assert ids == [1, 2, 3]
    assert [comment.id for comment in comments_one] == [1, 3]
    assert [comment.body for comment in comments_one] == ["first", "third"]
    assert [comment.id for comment in comments_two] == [2]
    first, third = comments_one
    second = comments_two[0]
    assert first.created_at.utcoffset() == timedelta(0)
    assert first.created_at.tzinfo == UTC
    assert first.created_at.date() == date(2026, 10, 12)
    assert second.created_at - first.created_at == timedelta(seconds=1)
    assert third.created_at - second.created_at == timedelta(seconds=1)


def test_human_comments_are_not_factory_posts(hosting: FakeHostingService) -> None:
    pull = _open(hosting)
    quoted = f"I saw this:\n> {KEY.comment()}\n{KEY.comment()}"

    hosting.add_human_comment(pull.number, "(a)")
    hosting.add_human_comment(pull.number, "(b)", author="someone")
    hosting.add_human_comment(pull.number, quoted)
    plain, other, quoting = hosting.list_comments(pull.number)

    assert plain.author == "human"
    assert plain.body == "(a)"
    assert plain.by_factory is False
    assert plain.key is None
    assert other.author == "someone"
    assert quoting.body == quoted
    assert quoting.by_factory is False
    assert quoting.key is None


def test_post_comment_adds_a_factory_post_with_marker_and_key(
    hosting: FakeHostingService,
) -> None:
    pull = _open(hosting)
    hosting.add_human_comment(pull.number, "(a)")

    outcome = hosting.post_comment(pull.number, "Which option?", KEY)
    posts = hosting.factory_posts(pull.number)

    assert outcome == "posted"
    assert len(posts) == 1
    post = posts[0]
    assert post.author == "factory"
    assert post.body == render_post("Which option?", KEY)
    assert post.by_factory is True
    assert post.key == KEY
    assert post in hosting.list_comments(pull.number)


def test_a_repeated_key_is_not_posted_again(hosting: FakeHostingService) -> None:
    pull = _open(hosting)
    other_n = PostKey(work_item="F0001-S0001", kind="question", n="3")
    other_kind = PostKey(work_item="F0001-S0001", kind="stall", n="2")

    hosting.post_comment(pull.number, "Which option?", KEY)
    repeated = hosting.post_comment(pull.number, "Which option?", KEY)
    count = len(hosting.list_comments(pull.number))

    assert repeated == "already_posted"
    assert count == 1
    assert hosting.post_comment(pull.number, "Which option?", other_n) == "posted"
    assert hosting.post_comment(pull.number, "Which option?", other_kind) == "posted"


def test_after_post_kill_point_fires_after_the_post_and_not_for_a_repeat(
    hosting: FakeHostingService, kill_points: KillPoints
) -> None:
    pull = _open(hosting)
    kill_points.arm(KillPoint.AFTER_POST)

    with pytest.raises(InjectedKill):
        hosting.post_comment(pull.number, "Stalled.", KEY)
    assert [comment.key for comment in hosting.list_comments(pull.number)] == [KEY]
    assert hosting.post_comment(pull.number, "Stalled.", KEY) == "already_posted"
    assert kill_points.reached(KillPoint.AFTER_POST) == 1
    other = PostKey(work_item="F0001-S0001", kind="question", n="3")
    assert hosting.post_comment(pull.number, "Again?", other) == "posted"
    assert kill_points.reached(KillPoint.AFTER_POST) == 2

    plain = FakeHostingService()
    plain_pull = _open(plain)
    assert plain.post_comment(plain_pull.number, "Stalled.", KEY) == "posted"


def test_delete_comment_removes_it_and_refuses_an_unknown_id(
    hosting: FakeHostingService,
) -> None:
    pull = _open(hosting)
    kept = hosting.add_human_comment(pull.number, "keep")
    gone = hosting.add_human_comment(pull.number, "gone")

    hosting.delete_comment(pull.number, gone)

    assert [comment.id for comment in hosting.list_comments(pull.number)] == [kept]
    with pytest.raises(HostingServiceError):
        hosting.delete_comment(pull.number, 99)


@pytest.mark.parametrize(
    ("operation", "arguments"),
    [
        ("get_pull_request", ()),
        ("list_comments", ()),
        ("post_comment", ("text", KEY)),
        ("close", ()),
        ("reopen", ()),
        ("set_draft", (False,)),
        ("set_description", ("new",)),
        ("set_labels", (["stage:doing"],)),
        ("add_human_comment", ("(a)",)),
        ("delete_comment", (1,)),
        ("close_by_human", ()),
        ("merge_by_human", (COMMIT,)),
        ("factory_posts", ()),
        ("labels", ()),
        ("description", ()),
    ],
)
def test_an_unknown_pull_request_number_is_refused(
    hosting: FakeHostingService, operation: str, arguments: tuple[object, ...]
) -> None:
    pull = _open(hosting)
    hosting.add_human_comment(pull.number, "(a)")

    with pytest.raises(HostingServiceError):
        getattr(hosting, operation)(pull.number + 1, *arguments)


def test_fail_next_fails_that_many_calls_of_that_operation(hosting: FakeHostingService) -> None:
    pull = _open(hosting)
    hosting.fail_next("post_comment", times=2)

    for _ in range(2):
        with pytest.raises(HostingServiceError) as failure:
            hosting.post_comment(pull.number, "Which option?", KEY)
        assert failure.value.operation == "post_comment"
        assert failure.value.detail == "injected failure"
        assert hosting.list_comments(pull.number) == []

    assert hosting.post_comment(pull.number, "Which option?", KEY) == "posted"
    assert len(hosting.factory_posts(pull.number)) == 1


@pytest.mark.parametrize(
    ("operation", "times"),
    [("nope", 1), ("post_comment", 0)],
)
def test_fail_next_refuses_an_unknown_operation_or_times_below_one(
    hosting: FakeHostingService, operation: str, times: int
) -> None:
    with pytest.raises(ValueError, match=r"."):
        hosting.fail_next(operation, times=times)


def test_fail_next_accepts_one_time(hosting: FakeHostingService) -> None:
    hosting.fail_next("post_comment", times=1)


def test_the_fake_inherits_the_hosting_service_interface(hosting: FakeHostingService) -> None:
    assert issubclass(FakeHostingService, HostingService)
    assert isinstance(hosting, HostingService)
