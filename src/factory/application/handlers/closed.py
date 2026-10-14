"""The closed handler: a close before the approval moves the story back to the backlog."""

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import WorkItemRecorder, commit_subject, target_of
from factory.domain.archive import destination_path
from factory.domain.events import Event
from factory.domain.paths import MAIN_BRANCH
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemSnapshot


class ClosedHandler(Handler):
    """Discards a story closed before its approval: back to the backlog, branch deleted."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Record through the boundaries' git; read the approval stages from the definition."""
        self._boundaries = boundaries
        self._definition = definition

    def handle(self, event: Event) -> None:
        """Discard the story unless it stands at an approval stage; post nothing."""
        target = target_of(event)
        if self._definition.stages[target.state.stage].approval:
            # A close at an approval stage is a send-back, which this handler does not make.
            return
        self._discard(target.snapshot)

    def _discard(self, snapshot: WorkItemSnapshot) -> None:
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(MAIN_BRANCH)
        # Moved, not rewritten: main holds the human's text, the branch the factory's.
        self._boundaries.git.move(snapshot.path, destination_path(snapshot.path, "backlog"))
        subject = commit_subject(snapshot.id, "closed before the approval, back in the backlog")
        recorder.publish(MAIN_BRANCH, subject)
        recorder.delete_branch(snapshot.branch)
