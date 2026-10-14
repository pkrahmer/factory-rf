"""The hand-over handler: at an approval the pull request shows the human what to decide."""

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import (
    WorkItemRecorder,
    commit_subject,
    require_pull_request,
    target_of,
)
from factory.domain.bills import bills_by_stage, cost_table
from factory.domain.errors import CannotHandle
from factory.domain.events import Event
from factory.domain.hand_over import hand_over_description
from factory.domain.hosting import PostKey
from factory.domain.journal import last_record
from factory.domain.paths import MAIN_BRANCH, cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import cost_table_post
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, require_state

_KIND = "hand_over"


def _no_state() -> CannotHandle:
    return CannotHandle(_KIND, "the work item on its branch has no state")


def _cost_table_key(snapshot: WorkItemSnapshot, document: WorkItemDocument) -> PostKey:
    latest = last_record(document, kind="result")
    n = 0 if latest is None else latest.number
    return PostKey(work_item=snapshot.id, kind="cost_table", n=str(n))


class HandOverHandler(Handler):
    """Describes the pull request, marks it ready, posts the cost table, then records it."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Act through the boundaries' git and hosting service; read approvals from `definition`."""
        self._boundaries = boundaries
        self._definition = definition

    def handle(self, event: Event) -> None:
        """Hand the work item over at its approval stage, unless it is handed over there already.

        Every effect before the record is safe to repeat, so a failure anywhere is retried whole.
        """
        target = target_of(event)
        number = require_pull_request(target, _KIND)
        snapshot = target.snapshot
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(snapshot.branch)
        document = recorder.read(snapshot.path)
        state = require_state(document, _no_state())
        stage = self._definition.stages.get(state.stage)
        if stage is None or not stage.approval:
            raise CannotHandle(_KIND, f"stage {state.stage} of {snapshot.id} is not an approval")
        if state.handed_over == state.stage:
            return
        self._show(number, snapshot, document)
        handed_over = state.model_copy(update={"handed_over": state.stage})
        recorder.record(
            snapshot.branch,
            snapshot.path,
            document.model_copy(update={"state": handed_over}),
            commit_subject(snapshot.id, f"handed over at {state.stage}"),
        )

    def _show(self, number: int, snapshot: WorkItemSnapshot, document: WorkItemDocument) -> None:
        sidecar = self._boundaries.checkout / cost_records_path(snapshot.path)
        records = self._boundaries.cost_reader.read(sidecar)
        commits = self._boundaries.git.log(
            f"origin/{snapshot.branch}", since=f"origin/{MAIN_BRANCH}"
        )
        hosting = self._boundaries.hosting
        hosting.set_description(number, hand_over_description(document, commits))
        hosting.set_draft(number, False)
        table = cost_table_post(cost_table(bills_by_stage(records)))
        hosting.post_comment(number, table, _cost_table_key(snapshot, document))
