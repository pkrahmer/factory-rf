"""A stop of one work item is posted once on its pull request, opened first when needed."""

import dataclasses
from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.domain.errors import GitError, HostingServiceError
from factory.domain.git import GitOptions
from factory.domain.hosting import PostKey
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.post_texts import opened_for_stop_description
from factory.domain.stops import StopPosted, WorkItemStop
from git_support import TEST_IDENTITY, run_git
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = "work-item/F0001-S0001"
KEY = PostKey(work_item=WORK_ITEM, kind="stall", n="3")
TEXT = "Stage tests stalled twice. Comment anything to retry; close the pull request to stop."


def _stop(pull_request: int | None = None, *, key: PostKey = KEY, text: str = TEXT) -> WorkItemStop:
    return WorkItemStop(
        key=key,
        branch=BRANCH,
        title=f"{WORK_ITEM}: stage tests stalled",
        pull_request=pull_request,
        text=text,
    )


def _push_branch(human: HumanClone, checkout: GitCli) -> None:
    human.push_file(BRANCH, "note.txt", "x")
    checkout.fetch()


def _without_git(boundaries: Boundaries, tmp_path: Path) -> Boundaries:
    """Boundaries whose git fails on every call: a directory that does not exist."""
    missing = GitCli(tmp_path / "missing", GitOptions(identity=TEST_IDENTITY))
    return dataclasses.replace(boundaries, git=missing)


def _open_pull_request(hosting: FakeHostingService) -> int:
    return hosting.create_pull_request(BRANCH, "opened by the factory", "", draft=True).number


def test_a_stop_with_a_pull_request_is_posted_there_without_opening_one_or_calling_git(
    boundaries: Boundaries, hosting: FakeHostingService, tmp_path: Path
) -> None:
    number = _open_pull_request(hosting)
    before = hosting.pull_requests()

    posted = StopService(_without_git(boundaries, tmp_path)).post(_stop(number))

    assert posted == StopPosted(pull_request=number, opened=False, outcome="posted")
    assert hosting.pull_requests() == before
    assert [comment.key for comment in hosting.factory_posts(number)] == [KEY]


def test_a_stop_is_posted_on_its_pull_request_after_the_human_closed_it(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    number = _open_pull_request(hosting)
    hosting.close_by_human(number)

    posted = StopService(boundaries).post(_stop(number))

    assert posted.outcome == "posted"
    assert posted.pull_request == number
    assert len(hosting.factory_posts(number)) == 1


def test_a_stop_without_a_pull_request_opens_a_draft_on_its_branch(
    boundaries: Boundaries, hosting: FakeHostingService, human: HumanClone, checkout: GitCli
) -> None:
    _push_branch(human, checkout)
    stop = _stop()

    StopService(boundaries).post(stop)

    pull_requests = hosting.pull_requests()
    assert len(pull_requests) == 1
    opened = pull_requests[0]
    assert opened.draft
    assert opened.branch == stop.branch
    assert opened.title == stop.title
    assert hosting.description(opened.number) == opened_for_stop_description(WORK_ITEM)


def test_a_stop_without_a_pull_request_is_posted_on_the_draft_it_opened(
    boundaries: Boundaries, hosting: FakeHostingService, human: HumanClone, checkout: GitCli
) -> None:
    _push_branch(human, checkout)

    posted = StopService(boundaries).post(_stop())

    number = hosting.pull_requests()[0].number
    assert posted == StopPosted(pull_request=number, opened=True, outcome="posted")
    assert [comment.key for comment in hosting.factory_posts(number)] == [KEY]


def test_a_stop_without_a_pull_request_reuses_the_open_one_of_its_branch(
    boundaries: Boundaries, hosting: FakeHostingService, human: HumanClone, checkout: GitCli
) -> None:
    _push_branch(human, checkout)
    number = _open_pull_request(hosting)

    posted = StopService(boundaries).post(_stop())

    assert posted == StopPosted(pull_request=number, opened=True, outcome="posted")
    assert [pull.number for pull in hosting.pull_requests()] == [number]
    assert len(hosting.factory_posts(number)) == 1


def test_a_stop_without_a_pull_request_does_not_reuse_one_the_human_closed(
    boundaries: Boundaries, hosting: FakeHostingService, human: HumanClone, checkout: GitCli
) -> None:
    _push_branch(human, checkout)
    closed = _open_pull_request(hosting)
    hosting.close_by_human(closed)

    posted = StopService(boundaries).post(_stop())

    assert posted.pull_request != closed
    assert posted.outcome == "posted"
    pull_requests = {pull.number: pull for pull in hosting.pull_requests()}
    assert len(pull_requests) == 2
    assert pull_requests[posted.pull_request].draft
    assert pull_requests[posted.pull_request].state == "open"
    assert len(hosting.factory_posts(posted.pull_request)) == 1
    assert hosting.factory_posts(closed) == []


@pytest.mark.usefixtures("human")
@pytest.mark.parametrize("remote_branch", ["missing", "at-main"])
def test_no_pull_request_is_opened_for_a_branch_without_a_commit_beyond_main(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    checkout: GitCli,
    tmp_path: Path,
    remote_branch: str,
) -> None:
    if remote_branch == "at-main":
        run_git(tmp_path / "human", "push", "-q", "origin", f"origin/main:refs/heads/{BRANCH}")
        checkout.fetch()

    with pytest.raises(HostingServiceError) as raised:
        StopService(boundaries).post(_stop())

    assert raised.value.operation == "create_pull_request"
    assert hosting.pull_requests() == []


def test_the_posted_comment_is_the_factorys_with_the_stops_key(
    boundaries: Boundaries, hosting: FakeHostingService, human: HumanClone, checkout: GitCli
) -> None:
    _push_branch(human, checkout)

    posted = StopService(boundaries).post(_stop())

    posts = hosting.factory_posts(posted.pull_request)
    assert len(posts) == 1
    assert posts[0].by_factory
    assert posts[0].key == KEY


def test_posting_the_same_stop_again_posts_nothing(
    boundaries: Boundaries, hosting: FakeHostingService, human: HumanClone, checkout: GitCli
) -> None:
    _push_branch(human, checkout)
    service = StopService(boundaries)
    first = service.post(_stop())

    again = service.post(_stop(first.pull_request))

    assert again.outcome == "already_posted"
    assert again.pull_request == first.pull_request
    assert len(hosting.factory_posts(first.pull_request)) == 1


def test_a_stop_with_the_same_key_and_another_text_posts_nothing(
    boundaries: Boundaries, hosting: FakeHostingService, human: HumanClone, checkout: GitCli
) -> None:
    _push_branch(human, checkout)
    service = StopService(boundaries)
    first = service.post(_stop())
    body = hosting.factory_posts(first.pull_request)[0].body

    again = service.post(_stop(first.pull_request, text="Another text for the same stop."))

    assert again.outcome == "already_posted"
    posts = hosting.factory_posts(first.pull_request)
    assert len(posts) == 1
    assert posts[0].body == body


@pytest.mark.parametrize(
    "other",
    [
        PostKey(work_item=WORK_ITEM, kind="stall", n="4"),
        PostKey(work_item=WORK_ITEM, kind="question", n="3"),
    ],
    ids=["another-n", "another-kind"],
)
def test_a_stop_with_another_key_posts_again(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    human: HumanClone,
    checkout: GitCli,
    other: PostKey,
) -> None:
    _push_branch(human, checkout)
    service = StopService(boundaries)
    first = service.post(_stop())

    second = service.post(_stop(first.pull_request, key=other))

    assert second.outcome == "posted"
    assert second.pull_request == first.pull_request
    assert [post.key for post in hosting.factory_posts(first.pull_request)] == [KEY, other]


def test_a_stop_killed_after_its_post_is_not_posted_again_after_the_restart(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    human: HumanClone,
    checkout: GitCli,
    kill_points: KillPoints,
) -> None:
    _push_branch(human, checkout)
    service = StopService(boundaries)
    kill_points.arm(KillPoint.AFTER_POST)
    with pytest.raises(InjectedKill):
        service.post(_stop())

    restarted = service.post(_stop())

    assert restarted.outcome == "already_posted"
    assert len(hosting.factory_posts(restarted.pull_request)) == 1


def test_a_stop_killed_after_its_post_opens_no_second_pull_request_after_the_restart(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    human: HumanClone,
    checkout: GitCli,
    kill_points: KillPoints,
) -> None:
    _push_branch(human, checkout)
    service = StopService(boundaries)
    kill_points.arm(KillPoint.AFTER_POST)
    with pytest.raises(InjectedKill):
        service.post(_stop())

    restarted = service.post(_stop())

    pull_requests = hosting.pull_requests()
    assert len(pull_requests) == 1
    assert restarted.pull_request == pull_requests[0].number


def test_a_failed_post_keeps_the_opened_pull_request_and_the_retry_posts_once(
    boundaries: Boundaries, hosting: FakeHostingService, human: HumanClone, checkout: GitCli
) -> None:
    _push_branch(human, checkout)
    service = StopService(boundaries)
    hosting.fail_next("post_comment")
    with pytest.raises(HostingServiceError):
        service.post(_stop())

    assert len(hosting.pull_requests()) == 1

    retried = service.post(_stop())

    pull_requests = hosting.pull_requests()
    assert len(pull_requests) == 1
    assert retried.pull_request == pull_requests[0].number
    assert len(hosting.factory_posts(retried.pull_request)) == 1


def test_a_failed_pull_request_creation_posts_nothing(
    boundaries: Boundaries, hosting: FakeHostingService, human: HumanClone, checkout: GitCli
) -> None:
    _push_branch(human, checkout)
    hosting.fail_next("create_pull_request")

    with pytest.raises(HostingServiceError):
        StopService(boundaries).post(_stop())

    assert hosting.pull_requests() == []


def test_posting_a_stop_leaves_the_checkout_as_it_was(
    boundaries: Boundaries, human: HumanClone, checkout: GitCli
) -> None:
    _push_branch(human, checkout)
    head = checkout.resolve("HEAD")

    StopService(boundaries).post(_stop())

    assert checkout.status().changes == []
    assert checkout.resolve("HEAD") == head


def test_a_git_error_reading_the_remote_branch_is_raised_and_opens_nothing(
    boundaries: Boundaries, hosting: FakeHostingService, tmp_path: Path
) -> None:
    with pytest.raises(GitError):
        StopService(_without_git(boundaries, tmp_path)).post(_stop())

    assert hosting.pull_requests() == []
