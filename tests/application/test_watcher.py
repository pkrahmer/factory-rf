"""The watcher reads the remote, looks up at most one pull request and judges claims."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from branch_reading import push_state
from definition_support import pipeline_definition
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.watcher import Watcher
from factory.domain.errors import GitError
from factory.domain.events import Event
from factory.domain.git import GitOptions
from factory.domain.hosting import PullRequestComment, PullRequestView
from factory.domain.identifiers import branch_name
from factory.domain.work_item import Claim, WorkItemState, initial_state
from git_support import TEST_IDENTITY, remote_commit, run_git
from human_clone import HumanClone

INSTANCE = "factory-1"
OTHER_INSTANCE = "factory-2"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"


class _CountingHosting(FakeHostingService):
    """The fake hosting service, recording every operation the watcher could call."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def create_pull_request(
        self, branch: str, title: str, body: str, *, draft: bool
    ) -> PullRequestView:
        self.calls.append("create_pull_request")
        return super().create_pull_request(branch, title, body, draft=draft)

    def find_open_pull_request(self, branch: str) -> PullRequestView | None:
        self.calls.append("find_open_pull_request")
        return super().find_open_pull_request(branch)

    def get_pull_request(self, number: int) -> PullRequestView:
        self.calls.append("get_pull_request")
        return super().get_pull_request(number)

    def list_comments(self, number: int) -> list[PullRequestComment]:
        self.calls.append("list_comments")
        return super().list_comments(number)

    def close(self, number: int) -> None:
        self.calls.append("close")
        super().close(number)

    def reopen(self, number: int) -> None:
        self.calls.append("reopen")
        super().reopen(number)

    def set_draft(self, number: int, draft: bool) -> None:
        self.calls.append("set_draft")
        super().set_draft(number, draft)

    def set_description(self, number: int, body: str) -> None:
        self.calls.append("set_description")
        super().set_description(number, body)

    def set_labels(self, number: int, labels: Sequence[str]) -> None:
        self.calls.append("set_labels")
        super().set_labels(number, labels)


def _with_hosting(boundaries: Boundaries, hosting: FakeHostingService) -> Boundaries:
    return replace(boundaries, hosting=hosting)


def _evaluate(boundaries: Boundaries) -> Event:
    boundaries.git.fetch()
    return Watcher(boundaries, INSTANCE).evaluate(pipeline_definition(boundaries))


def test_a_started_story_without_a_branch_runs_at_the_first_stage(
    boundaries: Boundaries, human: HumanClone, remote: Path
) -> None:
    human.start(BACKLOG_PATH)
    definition = pipeline_definition(boundaries)
    boundaries.git.fetch()

    event = Watcher(boundaries, INSTANCE).evaluate(definition)

    assert event.kind == "run"
    assert event.work_item is not None
    assert event.work_item.id == WORK_ITEM
    assert event.work_item.document.state == initial_state(definition.first_stage())
    assert event.remote_state == remote_commit(remote, "main")


def test_no_waiting_work_item_makes_no_hosting_call(
    boundaries: Boundaries, human: HumanClone
) -> None:
    hosting = _CountingHosting()
    human.start(BACKLOG_PATH)

    event = _evaluate(_with_hosting(boundaries, hosting))

    assert event.kind == "run"
    assert hosting.calls == []


@pytest.mark.parametrize(
    ("merged", "calls"),
    [(False, ["get_pull_request", "list_comments"]), (True, ["get_pull_request"])],
    ids=["open", "merged"],
)
def test_a_waiting_work_item_is_looked_up_once_and_its_comments_only_when_open(
    boundaries: Boundaries, human: HumanClone, merged: bool, calls: list[str]
) -> None:
    hosting = _CountingHosting()
    number = hosting.create_pull_request(BRANCH, "First story", "", draft=False).number
    hosting.add_human_comment(number, "A remark.")
    if merged:
        hosting.merge_by_human(number, "c" * 40)
    human.start(BACKLOG_PATH)
    push_state(human, WorkItemState(stage="approval", pull_request=number, handed_over="approval"))
    hosting.calls.clear()

    event = _evaluate(_with_hosting(boundaries, hosting))

    assert event.kind == ("merged" if merged else "comment")
    assert hosting.calls == calls
    assert hosting.factory_posts(number) == []


@pytest.mark.parametrize(
    ("instance", "age", "kind"),
    [
        (INSTANCE, 120, "crash"),
        (OTHER_INSTANCE, 60, "expired"),
        (OTHER_INSTANCE, 61, "expired"),
        (OTHER_INSTANCE, 59, "idle"),
    ],
    ids=["own", "other-at-lease", "other-past-lease", "other-within-lease"],
)
def test_the_claim_tier_is_decided_by_the_claim_service(
    boundaries: Boundaries,
    human: HumanClone,
    clock: ManualClock,
    *,
    instance: str,
    age: int,
    kind: str,
) -> None:
    claim = Claim(
        instance=instance,
        stage="intake",
        started_at=clock.now() - timedelta(minutes=age),
        lease_duration=60,
    )
    human.start(BACKLOG_PATH)
    push_state(human, initial_state("intake").model_copy(update={"claim": claim}))

    event = _evaluate(boundaries)

    assert event.kind == kind


def test_a_remote_without_main_is_a_git_error(boundaries: Boundaries, tmp_path: Path) -> None:
    run_git(tmp_path, "init", "-q", "--bare", "--initial-branch=main", "empty.git")
    git = GitCli(tmp_path / "empty-clone", GitOptions(identity=TEST_IDENTITY))
    git.clone(str(tmp_path / "empty.git"))
    empty = replace(boundaries, git=git)

    with pytest.raises(GitError, match="origin/main"):
        Watcher(empty, INSTANCE).evaluate(pipeline_definition(boundaries))
