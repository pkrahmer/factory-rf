"""At the error cap, the stop of a work item without a state opens a draft for its report."""

from pathlib import Path

from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.hosting.adapters.git_cli import GitCli
from factory.hosting.domain.hosting import PostKey
from factory.pipeline.application.boundaries import Boundaries
from factory.pipeline.application.dispatcher import Dispatcher
from factory.pipeline.application.stops import StopService
from factory.pipeline.domain.events import Event
from factory.pipeline.domain.tick_status import TickStatus
from factory.work.domain.work_item import WorkItemDocument, WorkItemSnapshot
from support.git_support import remote_commit
from support.human_clone import HumanClone
from support.tick_support import Failing

WORK_ITEM = "F0001-S0001"
BRANCH = "work-item/F0001-S0001"


def test_the_error_report_of_a_work_item_without_a_state_opens_a_draft(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    human: HumanClone,
    checkout: GitCli,
    remote: Path,
) -> None:
    human.push_file(BRANCH, "note.txt", "x")
    checkout.fetch()
    tip = remote_commit(remote, BRANCH)
    assert tip is not None
    snapshot = WorkItemSnapshot(
        id=WORK_ITEM,
        path=f"factory/features/F0001-demo/in-progress/{WORK_ITEM}-x.md",
        folder="in-progress",
        branch=BRANCH,
        branch_commit=tip,
        document=WorkItemDocument(state=None, body="# Demo story\n"),
    )
    event = Event(kind="run", work_item=snapshot, remote_state="a" * 40)
    dispatcher = Dispatcher({"run": Failing()}, TickStatus(), StopService(boundaries))

    outcomes = [dispatcher.dispatch(event) for _ in range(3)]

    assert outcomes == ["error", "error", "reported"]
    pull_requests = hosting.pull_requests()
    assert [
        (opened.number, opened.draft, opened.branch, opened.title) for opened in pull_requests
    ] == [(1, True, BRANCH, f"{WORK_ITEM}: Demo story")]
    assert [post.key for post in hosting.factory_posts(1)] == [
        PostKey(work_item=WORK_ITEM, kind="error", n="aaaaaaaaaaaa")
    ]
