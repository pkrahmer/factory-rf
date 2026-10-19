"""The watcher: reads the remote and evaluates it into one event for this instance."""

from factory.application.acceptance_reading import AcceptanceReader, running_work_items
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.work_items import RemoteWorkItems
from factory.domain.errors import GitError
from factory.domain.evaluation import EvaluationInput, PullRequestObservation, evaluate
from factory.domain.events import Event
from factory.domain.git import CommitId
from factory.domain.identifiers import Name
from factory.domain.move_rule import IllegalChange, is_legal_change
from factory.domain.paths import MAIN_BRANCH, REMOTE
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemSnapshot

_MAIN_REF = f"{REMOTE}/{MAIN_BRANCH}"


class Watcher:
    """Turns the remote-tracking refs and the one pull request lookup into one event."""

    def __init__(self, boundaries: Boundaries, instance: Name, *, observer: bool = False) -> None:
        """Read through `boundaries`; judge claims as `instance`, from outside if `observer`."""
        self._boundaries = boundaries
        self._instance = instance
        self._observer = observer

    def evaluate(self, definition: PipelineDefinition) -> Event:
        """The event the remote shows now under `definition`.

        Raises `GitError`, also when origin/main does not resolve, and `WorkItemFormatError`
        for a work item file that cannot be read.
        """
        main_commit = self._main_commit()
        boundaries = self._boundaries
        work_items = RemoteWorkItems(boundaries.git, boundaries.work_item_reader)
        acceptances = AcceptanceReader(boundaries, definition)
        snapshots = running_work_items(work_items, acceptances, definition)
        facts = EvaluationInput(
            definition=definition,
            snapshots=snapshots,
            main_commit=main_commit,
            illegal_changes=_illegal_changes(work_items, snapshots, definition),
            due=acceptances.due_features(),
        )
        claims = ClaimService(boundaries, self._instance, definition)
        # A tick never looks while its own stage runs; an observer may, so it needs the lease.
        status_of = claims.observed_status if self._observer else claims.status
        return evaluate(facts, self._lookup, status_of)

    def _main_commit(self) -> CommitId:
        commit = self._boundaries.git.resolve(_MAIN_REF)
        if commit is None:
            raise GitError(f"resolve {_MAIN_REF}", None, f"{_MAIN_REF} does not resolve")
        return commit

    def _lookup(self, number: int) -> PullRequestObservation:
        hosting = self._boundaries.hosting
        view = hosting.get_pull_request(number)
        # Comments matter only while the pull request is open; skipping them saves a call.
        comments = hosting.list_comments(number) if view.state == "open" else []
        return PullRequestObservation(view=view, comments=comments)


def _illegal_changes(
    work_items: RemoteWorkItems,
    snapshots: list[WorkItemSnapshot],
    definition: PipelineDefinition,
) -> list[IllegalChange]:
    illegal: list[IllegalChange] = []
    for snapshot in snapshots:
        change = work_items.last_stage_change(snapshot)
        if change is not None and not is_legal_change(definition, change):
            illegal.append(IllegalChange(work_item=snapshot.id, change=change))
    return illegal
