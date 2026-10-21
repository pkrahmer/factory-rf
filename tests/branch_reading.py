"""The work item on its branch and the factory's posts on its pull request, read and written."""

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.domain.hosting import PullRequestComment
from factory.domain.work_item import WorkItemDocument, WorkItemState
from human_clone import HumanClone
from stage_run_support import BRANCH, PATH

BODY = "# First story\n"


def remote_document(boundaries: Boundaries, checkout: GitCli) -> WorkItemDocument:
    """Fetch, then the work item the remote's branch holds."""
    checkout.fetch()
    text = checkout.show_file(f"origin/{BRANCH}", PATH)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def error_posts(hosting: FakeHostingService, number: int) -> list[PullRequestComment]:
    """The factory's posts of kind `error` on pull request `number`, in order."""
    return [
        post
        for post in hosting.factory_posts(number)
        if post.key is not None and post.key.kind == "error"
    ]


def push_state(human: HumanClone, state: WorkItemState) -> None:
    """Push the work item with `state` and the body `# First story` to the branch."""
    text = FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body=BODY))
    human.push_file(BRANCH, PATH, text)
