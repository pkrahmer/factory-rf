"""The opening of a work item: its branch prepared from the remote and its draft pull request."""

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.domain.errors import WorkItemFormatError
from factory.domain.hosting import PullRequestView
from factory.domain.identifiers import WorkItemId, branch_name
from factory.domain.journal import HUMAN, NewEntry, append_entry
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.sections import JOURNAL, sections, title
from factory.domain.work_item import WorkItemDocument, initial_state

_MAIN = "origin/main"


class PreparedWorkItem(BaseModel):
    """A work item's branch checked out and its document, ready to be claimed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_item: WorkItemId
    branch: str
    path: str
    document: WorkItemDocument
    branch_existed: bool
    merge_conflict: bool


def _with_journal_section(body: str) -> str:
    if any(section.heading == JOURNAL for section in sections(body)):
        return body
    text = body.rstrip("\n")
    return f"{text}\n\n## {JOURNAL}\n"


class WorkItemOpening:
    """Prepares a started work item's branch and ensures its draft pull request."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Open work items through `boundaries`, starting them at `definition`'s first stage."""
        self._boundaries = boundaries
        self._definition = definition

    def prepare(self, work_item: WorkItemId, path: str) -> PreparedWorkItem:
        """Check out the work item's branch as the remote holds it and read its document.

        Reads only remote-tracking refs, never fetches, commits or pushes. A new branch starts
        at `origin/main` with a first document; an existing one is reset to the remote's and
        has `origin/main` merged in, a conflict aborted.
        """
        branch = branch_name(work_item)
        branch_existed = self._boundaries.git.resolve(f"origin/{branch}") is not None
        if branch_existed:
            document, merge_conflict = self._reopen(branch, path)
        else:
            document, merge_conflict = self._open_new(branch, path), False
        return PreparedWorkItem(
            work_item=work_item,
            branch=branch,
            path=path,
            document=document,
            branch_existed=branch_existed,
            merge_conflict=merge_conflict,
        )

    def _reopen(self, branch: str, path: str) -> tuple[WorkItemDocument, bool]:
        # The remote is the truth: whatever a local branch of this name held is dropped.
        self._boundaries.git.checkout(branch, start_point=f"origin/{branch}")
        merge_conflict = self._boundaries.git.merge(_MAIN) == "conflict"
        document = self._boundaries.work_item_reader.read(self._boundaries.checkout / path)
        return document, merge_conflict

    def _open_new(self, branch: str, path: str) -> WorkItemDocument:
        self._boundaries.git.checkout(branch, start_point=_MAIN)
        text = self._boundaries.git.show_file(_MAIN, path)
        if text is None:
            raise WorkItemFormatError("the work item file is not on origin/main", path)
        # The backlog file's own front matter is the human's draft, never the pipeline's state.
        specification = self._boundaries.work_item_reader.parse_specification(text)
        document = WorkItemDocument(
            state=initial_state(self._definition.first_stage()),
            body=_with_journal_section(specification.body),
        )
        now = self._boundaries.clock.now()
        created = NewEntry(speaker=HUMAN, kind="created", text="created.", on=now.date())
        return append_entry(document, created, at=now)

    def ensure_pull_request(
        self, work_item: WorkItemId, document: WorkItemDocument
    ) -> PullRequestView:
        """The work item's open pull request, or a new draft; a closed or merged one is not reused.

        Changes no file. Raises `WorkItemFormatError` when the body has no title line.
        """
        hosting = self._boundaries.hosting
        branch = branch_name(work_item)
        recorded = None if document.state is None else document.state.pull_request
        if recorded is not None:
            pull = hosting.get_pull_request(recorded)
            if pull.state == "open":
                return pull
        found = hosting.find_open_pull_request(branch)
        if found is not None:
            return found
        heading = title(document.body)
        if heading is None:
            raise WorkItemFormatError("the work item has no title line")
        return hosting.create_pull_request(
            branch, f"{work_item}: {heading}", document.body, draft=True
        )
