"""The subjects of the commits the handlers record on the work item's branch."""

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.handlers.closed import ClosedHandler
from factory.application.handlers.comments import CommentCopier
from factory.application.handlers.reject import RejectHandler
from factory.domain.events import Event
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot
from human_clone import HumanClone

BRANCH = "work-item/F0001-S0001"


def _subjects(checkout: GitCli, since: str | None) -> list[str]:
    assert since is not None
    checkout.fetch()
    return [commit.subject for commit in checkout.log(f"origin/{BRANCH}", since=since)]


def _push_at_approval(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    work_item: WorkItemSnapshot,
    handed_over: str | None,
) -> WorkItemSnapshot:
    state = work_item.document.state
    assert state is not None
    moved = state.model_copy(update={"stage": "approval", "handed_over": handed_over})
    document = WorkItemDocument(state=moved, body=work_item.document.body)
    human.push_file(BRANCH, work_item.path, boundaries.work_item_writer.render(document))
    checkout.fetch()
    text = checkout.show_file(f"origin/{BRANCH}", work_item.path)
    assert text is not None
    return work_item.model_copy(
        update={
            "branch_commit": checkout.resolve(f"origin/{BRANCH}"),
            "document": boundaries.work_item_reader.parse(text),
        }
    )


def test_the_copied_comments_are_committed_under_the_work_item_s_id(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    hosting.add_human_comment(pull_request, "Make the title shorter.")

    CommentCopier(boundaries).copy(work_item, pull_request)

    assert _subjects(checkout, work_item.branch_commit) == [
        "work item F0001-S0001: comments from the pull request"
    ]


def test_a_close_at_the_approval_commits_the_close_and_then_the_send_back(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    definition: PipelineDefinition,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    pushed = _push_at_approval(
        boundaries, human=human, checkout=checkout, work_item=work_item, handed_over="approval"
    )
    hosting.set_draft(pull_request, False)
    hosting.close_by_human(pull_request)

    ClosedHandler(boundaries, definition).handle(
        Event(kind="closed", work_item=pushed, remote_state="a" * 40)
    )

    assert _subjects(checkout, pushed.branch_commit) == [
        "work item F0001-S0001: sent back",
        "work item F0001-S0001: close recorded",
    ]


def test_the_move_back_names_the_work_item_and_both_stages(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    work_item: WorkItemSnapshot,
) -> None:
    pushed = _push_at_approval(
        boundaries, human=human, checkout=checkout, work_item=work_item, handed_over=None
    )
    main = checkout.resolve("origin/main")
    assert main is not None

    RejectHandler(boundaries).handle(Event(kind="reject", work_item=pushed, remote_state=main))

    assert _subjects(checkout, pushed.branch_commit) == [
        "work item F0001-S0001: stage approval -> doing, moved back"
    ]
