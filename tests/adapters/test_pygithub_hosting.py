"""The PyGithub hosting client, against stand-ins of PyGithub's objects."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from typing import cast

import pytest
from github import GithubException
from github.Repository import Repository

from adapters.pygithub_stand_ins import (
    Call,
    StandInComment,
    StandInPullRequest,
    StandInRepository,
    StandInUser,
    Untouchable,
)
from factory.adapters.pygithub_hosting import PyGithubHostingService
from factory.application.hosting import HostingService
from factory.domain.errors import HostingServiceError
from factory.domain.hosting import FACTORY_MARKER, PostKey, render_post
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints

COMMIT = "a" * 40
BRANCH = "work-item/F0001-S0001"
CREATED = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)


def _service(
    repository: StandInRepository, kill_points: KillPoints | None = None
) -> PyGithubHostingService:
    return PyGithubHostingService(cast(Repository, repository), kill_points)


def _repository_with(pull: StandInPullRequest) -> StandInRepository:
    return StandInRepository(pulls=[pull])


def _key(n: str = "7") -> PostKey:
    return PostKey.model_validate({"work_item": "F0001-S0001", "kind": "question", "n": n})


def _comment(id: int, body: str, created_at: datetime = CREATED) -> StandInComment:
    return StandInComment(id=id, user=StandInUser("someone"), body=body, created_at=created_at)


STRUCTURAL_FIT: HostingService = _service(StandInRepository())


@pytest.mark.parametrize("draft", [True, False])
def test_create_pull_request_opens_against_main_and_returns_the_view(draft: bool) -> None:
    repository = StandInRepository()

    view = _service(repository).create_pull_request(BRANCH, "title", "body", draft=draft)

    assert repository.calls_to("create_pull") == [
        Call(
            "create_pull",
            kwargs={
                "base": "main",
                "head": BRANCH,
                "title": "title",
                "body": "body",
                "draft": draft,
            },
        )
    ]
    created = repository.pulls[view.number]
    assert view.branch == BRANCH
    assert view.title == "title"
    assert view.draft is draft
    assert view.state == "open"
    assert view.url == created.html_url


def test_find_open_pull_request_filters_by_owner_and_branch() -> None:
    first = StandInPullRequest(4, BRANCH, html_url="https://example.invalid/pull/4")
    second = StandInPullRequest(9, BRANCH)
    repository = StandInRepository(owner_login="octo", open_pulls=[first, second])

    view = _service(repository).find_open_pull_request(BRANCH)

    assert repository.calls_to("get_pulls") == [
        Call("get_pulls", kwargs={"state": "open", "head": f"octo:{BRANCH}"})
    ]
    assert view is not None
    assert view.number == 4
    assert view.url == "https://example.invalid/pull/4"


def test_find_open_pull_request_is_none_without_a_result() -> None:
    assert _service(StandInRepository()).find_open_pull_request(BRANCH) is None


def test_get_pull_request_maps_the_pull_request_to_a_view() -> None:
    pull = StandInPullRequest(
        5, BRANCH, title="A title", draft=True, html_url="https://example.invalid/pull/5"
    )
    repository = _repository_with(pull)

    view = _service(repository).get_pull_request(5)

    assert repository.calls_to("get_pull") == [Call("get_pull", (5,))]
    assert view.number == 5
    assert view.branch == BRANCH
    assert view.title == "A title"
    assert view.draft is True
    assert view.url == "https://example.invalid/pull/5"


@pytest.mark.parametrize(
    ("state", "merged", "sha", "expected_state", "expected_commit"),
    [
        ("closed", True, COMMIT, "merged", COMMIT),
        ("closed", False, None, "closed", None),
        ("open", False, None, "open", None),
    ],
)
def test_view_state_follows_merged_then_state(
    state: str, merged: bool, sha: str | None, expected_state: str, expected_commit: str | None
) -> None:
    pull = StandInPullRequest(5, BRANCH, state=state, merged=merged, merge_commit_sha=sha)

    view = _service(_repository_with(pull)).get_pull_request(5)

    assert view.state == expected_state
    assert view.merge_commit == expected_commit


@pytest.mark.parametrize("state", ["open", "closed"])
def test_unmerged_pull_request_has_no_merge_commit_even_with_a_sha(state: str) -> None:
    pull = StandInPullRequest(5, BRANCH, state=state, merged=False, merge_commit_sha=COMMIT)

    view = _service(_repository_with(pull)).get_pull_request(5)

    assert view.merge_commit is None


def test_list_comments_sorts_by_id_and_reads_naive_times_as_utc() -> None:
    naive = datetime(2026, 10, 12, 8, 0)
    aware = datetime(2026, 10, 12, 11, 0, tzinfo=timezone(timedelta(hours=2)))
    pull = StandInPullRequest(
        5,
        BRANCH,
        comments=[
            StandInComment(id=30, user=StandInUser("carol"), body="third", created_at=CREATED),
            StandInComment(id=10, user=StandInUser("alice"), body="first", created_at=naive),
            StandInComment(id=20, user=StandInUser("bob"), body="second", created_at=aware),
        ],
    )

    comments = _service(_repository_with(pull)).list_comments(5)

    assert [(c.id, c.author, c.body) for c in comments] == [
        (10, "alice", "first"),
        (20, "bob", "second"),
        (30, "carol", "third"),
    ]
    assert comments[0].created_at == datetime(2026, 10, 12, 8, 0, tzinfo=UTC)
    assert comments[1].created_at == datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
    assert comments[2].created_at == CREATED


def test_list_comments_tells_factory_posts_by_marker_and_key() -> None:
    key = _key()
    pull = StandInPullRequest(
        5,
        BRANCH,
        comments=[
            _comment(1, render_post("a question", key)),
            _comment(2, f"marked\n\n{FACTORY_MARKER}"),
            _comment(3, f"quoted\n\n{key.comment()}"),
        ],
    )

    first, second, third = _service(_repository_with(pull)).list_comments(5)

    assert (first.by_factory, first.key) == (True, key)
    assert (second.by_factory, second.key) == (True, None)
    assert (third.by_factory, third.key) == (False, None)


def test_post_comment_posts_the_rendered_body_once() -> None:
    pull = StandInPullRequest(5, BRANCH, comments=[_comment(1, "hello")])
    key = _key()

    outcome = _service(_repository_with(pull)).post_comment(5, "a question", key)

    assert outcome == "posted"
    assert pull.calls_to("create_issue_comment") == [
        Call("create_issue_comment", (render_post("a question", key),))
    ]


def test_post_comment_skips_an_existing_key_but_not_a_quoted_one() -> None:
    key = _key()
    posted = StandInPullRequest(5, BRANCH, comments=[_comment(1, render_post("earlier", key))])
    quoted = StandInPullRequest(5, BRANCH, comments=[_comment(1, f"see\n\n{key.comment()}")])

    assert _service(_repository_with(posted)).post_comment(5, "again", key) == "already_posted"
    assert posted.calls_to("create_issue_comment") == []
    assert _service(_repository_with(quoted)).post_comment(5, "again", key) == "posted"
    assert len(quoted.calls_to("create_issue_comment")) == 1


def test_kill_after_post_leaves_the_post_recognisable(kill_points: KillPoints) -> None:
    pull = StandInPullRequest(5, BRANCH)
    repository = _repository_with(pull)
    key = _key()
    kill_points.arm(KillPoint.AFTER_POST)

    with pytest.raises(InjectedKill):
        _service(repository, kill_points).post_comment(5, "a question", key)

    assert len(pull.calls_to("create_issue_comment")) == 1
    assert _service(repository, kill_points).post_comment(5, "a question", key) == "already_posted"
    assert kill_points.reached(KillPoint.AFTER_POST) == 1
    other = _repository_with(StandInPullRequest(5, BRANCH))
    assert _service(other).post_comment(5, "a question", key) == "posted"


@pytest.mark.parametrize(
    ("operation", "expected"),
    [
        ("close", {"state": "closed"}),
        ("reopen", {"state": "open"}),
    ],
)
def test_close_and_reopen_edit_the_state(operation: str, expected: dict[str, object]) -> None:
    pull = StandInPullRequest(5, BRANCH)
    other = StandInPullRequest(6, "work-item/F0001-S0002")
    service = _service(StandInRepository(pulls=[pull, other]))

    getattr(service, operation)(5)

    assert pull.calls_to("edit") == [Call("edit", kwargs=expected)]
    assert other.calls == []


@pytest.mark.parametrize(
    ("draft", "method"), [(True, "convert_to_draft"), (False, "mark_ready_for_review")]
)
def test_set_draft_converts_or_marks_ready(draft: bool, method: str) -> None:
    pull = StandInPullRequest(5, BRANCH)

    _service(_repository_with(pull)).set_draft(5, draft)

    assert pull.calls_to(method) == [Call(method)]
    assert pull.calls_to("edit") == []


def test_set_description_edits_the_body() -> None:
    pull = StandInPullRequest(5, BRANCH)

    _service(_repository_with(pull)).set_description(5, "new text")

    assert pull.calls_to("edit") == [Call("edit", kwargs={"body": "new text"})]


@pytest.mark.parametrize(
    ("existing", "expected"),
    [
        (["bug", "stage:tests"], ("bug", "stage:doing")),
        ([], ("stage:doing",)),
    ],
)
def test_set_labels_keeps_foreign_labels_and_replaces_stage_labels(
    existing: list[str], expected: tuple[str, ...]
) -> None:
    pull = StandInPullRequest(5, BRANCH, labels=existing)

    _service(_repository_with(pull)).set_labels(5, ["stage:doing"])

    assert pull.calls_to("set_labels") == [Call("set_labels", expected)]


Operation = Callable[[PyGithubHostingService], object]

FAILING_CALLS: list[tuple[str, Operation, str, str]] = [
    (
        "create_pull_request",
        lambda s: s.create_pull_request(BRANCH, "t", "b", draft=False),
        "repository",
        "create_pull",
    ),
    (
        "find_open_pull_request",
        lambda s: s.find_open_pull_request(BRANCH),
        "repository",
        "get_pulls",
    ),
    ("get_pull_request", lambda s: s.get_pull_request(5), "repository", "get_pull"),
    ("list_comments", lambda s: s.list_comments(5), "pull", "get_issue_comments"),
    ("post_comment", lambda s: s.post_comment(5, "text", _key()), "pull", "get_issue_comments"),
    ("post_comment", lambda s: s.post_comment(5, "text", _key()), "pull", "create_issue_comment"),
    ("close", lambda s: s.close(5), "pull", "edit"),
    ("reopen", lambda s: s.reopen(5), "pull", "edit"),
    ("set_draft", lambda s: s.set_draft(5, True), "pull", "convert_to_draft"),
    ("set_draft", lambda s: s.set_draft(5, False), "pull", "mark_ready_for_review"),
    ("set_description", lambda s: s.set_description(5, "text"), "pull", "edit"),
    ("set_labels", lambda s: s.set_labels(5, ["stage:doing"]), "pull", "get_labels"),
    ("set_labels", lambda s: s.set_labels(5, ["stage:doing"]), "pull", "set_labels"),
]


def _failing(target: str, method: str, error: BaseException) -> StandInRepository:
    pull = StandInPullRequest(5, BRANCH)
    repository = _repository_with(pull)
    (repository if target == "repository" else pull).failures[method] = error
    return repository


@pytest.mark.parametrize(
    "error",
    [GithubException(500, {"message": "boom"}, None), OSError("connection refused")],
    ids=["github", "os"],
)
@pytest.mark.parametrize(
    ("operation", "call", "target", "method"),
    FAILING_CALLS,
    ids=[f"{name}-{method}" for name, _, _, method in FAILING_CALLS],
)
def test_every_failing_call_raises_hosting_service_error(
    operation: str, call: Operation, target: str, method: str, error: Exception
) -> None:
    service = _service(_failing(target, method, error))

    with pytest.raises(HostingServiceError) as raised:
        call(service)

    assert raised.value.operation == operation
    assert raised.value.detail == str(error)
    assert raised.value.__cause__ is error


def test_other_errors_and_injected_kills_pass_through(kill_points: KillPoints) -> None:
    error = ValueError("not a hosting error")
    service = _service(_failing("repository", "get_pull", error))

    with pytest.raises(ValueError) as raised:
        service.get_pull_request(5)
    assert raised.value is error

    kill_points.arm(KillPoint.AFTER_POST)
    killing = _service(_repository_with(StandInPullRequest(5, BRANCH)), kill_points)
    with pytest.raises(InjectedKill) as killed:
        killing.post_comment(5, "text", _key())
    assert killed.value.point is KillPoint.AFTER_POST


def test_constructor_touches_nothing_on_the_repository() -> None:
    PyGithubHostingService(cast(Repository, Untouchable()))


def test_client_fits_the_interface_without_inheriting_it() -> None:
    assert HostingService not in PyGithubHostingService.__mro__
    assert isinstance(STRUCTURAL_FIT, PyGithubHostingService)
