"""The watcher: reads the remote and evaluates it into one event for this instance."""

from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.work_items import RemoteWorkItems
from factory.domain.errors import GitError
from factory.domain.evaluation import EvaluationInput, PullRequestObservation, evaluate
from factory.domain.events import Event
from factory.domain.git import CommitId
from factory.domain.identifiers import Name
from factory.domain.paths import MAIN_BRANCH, REMOTE
from factory.domain.pipeline_definition import PipelineDefinition

_MAIN_REF = f"{REMOTE}/{MAIN_BRANCH}"


class Watcher:
    """Turns the remote-tracking refs and the one pull request lookup into one event."""

    def __init__(self, boundaries: Boundaries, instance: Name) -> None:
        """Read through `boundaries` and judge claims as `instance`."""
        self._boundaries = boundaries
        self._instance = instance

    def evaluate(self, definition: PipelineDefinition) -> Event:
        """The event the remote shows now under `definition`.

        Raises `GitError`, also when origin/main does not resolve, and `WorkItemFormatError`
        for a work item file that cannot be read.
        """
        main_commit = self._main_commit()
        boundaries = self._boundaries
        snapshots = RemoteWorkItems(boundaries.git, boundaries.work_item_reader).read(definition)
        facts = EvaluationInput(definition=definition, snapshots=snapshots, main_commit=main_commit)
        claims = ClaimService(boundaries, self._instance, definition)
        return evaluate(facts, self._lookup, claims.status)

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
