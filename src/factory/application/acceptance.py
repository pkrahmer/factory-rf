"""Opening a due feature acceptance and reading the facts its reviewer is given."""

from pydantic import BaseModel, ConfigDict

from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.application.costs import read_cost_records
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import (
    Target,
    WorkItemRecorder,
    commit_subject,
    move_with_cost_records,
    require_pull_request,
    target_of,
)
from factory.application.work_items import read_feature_file
from factory.domain.acceptance import (
    AcceptanceFacts,
    FeatureAcceptance,
    acceptance_description,
    acceptance_facts,
    acceptance_file_name,
    acceptance_head,
    book_merge,
    is_before_approval,
)
from factory.domain.archive import destination_path
from factory.domain.bills import bill, bills_by_stage, cost_line, cost_table
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CannotHandle, PushFailed, WorkItemFormatError
from factory.domain.events import Event
from factory.domain.git import CommitId
from factory.domain.hand_over import cost_table_key
from factory.domain.identifiers import (
    FeatureId,
    WorkItemId,
    branch_name,
    is_acceptance,
    parse_work_item_file_name,
)
from factory.domain.paths import (
    MAIN_BRANCH,
    REMOTE,
    cost_records_path,
    feature_file_path,
    work_item_path,
)
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import cost_table_post
from factory.domain.sections import title
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, require_state

_MAIN_REF = f"{REMOTE}/{MAIN_BRANCH}"
_KIND = "acceptance_due"
_HAND_OVER = "hand_over"
_MERGED = "merged"


class OpenedAcceptance(BaseModel):
    """An acceptance just opened: its id, its pushed branch, its report and the commit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: WorkItemId
    branch: str
    path: str
    commit: CommitId


class AcceptanceService:
    """Opens a due acceptance on its own branch and reads its reviewer's facts from main."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Work through `boundaries`; `ValueError` when `definition` has no acceptance stage."""
        if definition.acceptance_stage is None:
            raise ValueError("the pipeline definition has no acceptance stage")
        self._boundaries = boundaries
        self._stage = definition.acceptance_stage
        self._reader = AcceptanceReader(boundaries, definition)

    def open(self, feature: FeatureId) -> OpenedAcceptance:
        """Push a branch holding the head of the feature's next acceptance report, nothing more.

        Reads the last fetch only. Raises `CannotHandle` when the feature is not due,
        `WorkItemFormatError` when its feature file has no title, both before anything is
        written, and `PushFailed` when the push does not reach the remote.
        """
        acceptance = self._acceptance(feature)
        if acceptance.status != "due":
            raise CannotHandle(
                kind=_KIND, reason=f"feature {feature} is {acceptance.status}, not due"
            )
        head = acceptance_head(
            self._feature_title(acceptance.directory), self._stage, acceptance.archived
        )
        work_item = acceptance.next_acceptance
        branch = branch_name(work_item)
        path = work_item_path(acceptance.directory, "in-progress", acceptance_file_name(work_item))
        git = self._boundaries.git
        git.checkout(branch, start_point=_MAIN_REF)
        report = self._boundaries.checkout / path
        report.parent.mkdir(parents=True, exist_ok=True)
        self._boundaries.work_item_writer.write(report, head)
        commit = git.commit(f"{work_item} opens")
        outcome = git.push(branch)
        if outcome != "pushed":
            raise PushFailed(branch, outcome)
        return OpenedAcceptance(id=work_item, branch=branch, path=path, commit=commit)

    def facts(self, feature: FeatureId) -> AcceptanceFacts:
        """The reviewer's facts of the feature as `origin/main` holds it.

        Raises `ValueError` when the feature has no directory there.
        """
        directory = self._acceptance(feature).directory
        files = self._reader.feature_files(feature)
        records: list[CostRecord] = []
        for file_name in files.done:
            parsed = parse_work_item_file_name(file_name)
            if parsed is not None and not is_acceptance(parsed.id):
                records.extend(self._records(work_item_path(directory, "done", file_name)))
        return acceptance_facts(files, cost_line(bill(records)))

    def _acceptance(self, feature: FeatureId) -> FeatureAcceptance:
        for acceptance in self._reader.read():
            if acceptance.feature == feature:
                return acceptance
        raise ValueError(f"feature {feature} has no directory on {_MAIN_REF}")

    def _feature_title(self, directory: str) -> str:
        path = feature_file_path(directory)
        text = read_feature_file(self._boundaries.git, directory)
        if text is None:
            raise WorkItemFormatError(f"missing on {_MAIN_REF}", path)
        feature_title = title(text)
        if feature_title is None:
            raise WorkItemFormatError("the feature file has no title line", path)
        return feature_title

    def _records(self, story_path: str) -> list[CostRecord]:
        sidecar = cost_records_path(story_path)
        boundaries = self._boundaries
        return read_cost_records(boundaries.git, boundaries.cost_reader, _MAIN_REF, sidecar)


class AcceptanceDueHandler(Handler):
    """Opens the acceptance of the feature an `acceptance_due` event names."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Keep `boundaries` and `definition`; the service is built per event."""
        self._boundaries = boundaries
        self._definition = definition

    def handle(self, event: Event) -> None:
        """Open `event.feature`; `CannotHandle` for another kind, no feature or no stage."""
        if event.kind != _KIND:
            raise CannotHandle(kind=event.kind, reason=f"not an {_KIND} event")
        if event.feature is None:
            raise CannotHandle(kind=_KIND, reason="no feature")
        if self._definition.acceptance_stage is None:
            raise CannotHandle(kind=_KIND, reason="no acceptance stage")
        AcceptanceService(self._boundaries, self._definition).open(event.feature)


class AcceptanceHandOver(Handler):
    """Hands an acceptance over at its approval: description, ready flag, cost table, record."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Keep `boundaries` and `definition`; the reviewer's role is looked up per event."""
        self._boundaries = boundaries
        self._definition = definition

    def handle(self, event: Event) -> None:
        """Hand the acceptance over at its approval stage, unless it is handed over there already.

        Every effect before the record is safe to repeat, so a failure anywhere is retried whole.
        """
        if event.kind != _HAND_OVER:
            raise CannotHandle(kind=event.kind, reason=f"not a {_HAND_OVER} event")
        if event.work_item is None or not is_acceptance(event.work_item.id):
            raise CannotHandle(kind=_HAND_OVER, reason="not an acceptance")
        role = self._reviewer_role()
        target = target_of(event)
        self._require_approval(target)
        number = require_pull_request(target, _HAND_OVER)
        snapshot = target.snapshot
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(snapshot.branch)
        document = recorder.read(snapshot.path)
        no_state = CannotHandle(_HAND_OVER, "the work item on its branch has no state")
        state = require_state(document, no_state)
        if state.handed_over == state.stage:
            return
        self._show(number, snapshot, document, role)
        handed_over = state.model_copy(update={"handed_over": state.stage})
        recorder.record(
            snapshot.branch,
            snapshot.path,
            document.model_copy(update={"state": handed_over}),
            commit_subject(snapshot.id, f"handed over at {state.stage}"),
        )

    def _reviewer_role(self) -> str:
        name = self._definition.acceptance_stage
        stage = None if name is None else self._definition.stages.get(name)
        if stage is None or stage.role is None:
            raise CannotHandle(kind=_HAND_OVER, reason="no acceptance stage")
        return stage.role

    def _require_approval(self, target: Target) -> None:
        name = target.state.stage
        stage = self._definition.stages.get(name)
        if stage is None or not stage.approval:
            raise CannotHandle(kind=_HAND_OVER, reason=f"stage {name} is not an approval")

    def _show(
        self, number: int, snapshot: WorkItemSnapshot, document: WorkItemDocument, role: str
    ) -> None:
        sidecar = self._boundaries.checkout / cost_records_path(snapshot.path)
        records = self._boundaries.cost_reader.read(sidecar)
        hosting = self._boundaries.hosting
        hosting.set_description(number, acceptance_description(document, role))
        hosting.set_draft(number, False)
        table = cost_table_post(cost_table(bills_by_stage(records)))
        hosting.post_comment(number, table, cost_table_key(snapshot.id, document))


class AcceptanceMerged(Handler):
    """Books a merged acceptance `accepted` under `done/` on main, then deletes its branch."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Keep `boundaries` and `definition`; the acceptance stage is checked per event."""
        self._boundaries = boundaries
        self._definition = definition

    def handle(self, event: Event) -> None:
        """Book the merged acceptance on main unless it is booked already, then delete its branch.

        The merge decides the outcome, whatever the reviewer recommended.
        """
        self._require_bookable(event)
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(MAIN_BRANCH)
        snapshot = target_of(event).snapshot
        git = self._boundaries.git
        if git.show_file("HEAD", snapshot.path) is not None:
            self._book(recorder, snapshot)
        elif git.show_file("HEAD", destination_path(snapshot.path, "done")) is None:
            raise CannotHandle(kind=event.kind, reason="no report on the main branch")
        recorder.delete_branch(snapshot.branch)

    def _require_bookable(self, event: Event) -> None:
        if event.kind != _MERGED:
            raise CannotHandle(kind=event.kind, reason=f"not a {_MERGED} event")
        if event.work_item is None or not is_acceptance(event.work_item.id):
            raise CannotHandle(kind=event.kind, reason="not an acceptance")
        if self._definition.acceptance_stage is None:
            raise CannotHandle(kind=event.kind, reason="no acceptance stage")
        if event.pull_request is None or event.pull_request.state != "merged":
            raise CannotHandle(kind=event.kind, reason="pull request is not merged")

    def _book(self, recorder: WorkItemRecorder, snapshot: WorkItemSnapshot) -> None:
        boundaries = self._boundaries
        document = recorder.read(snapshot.path)
        # `HEAD` is the merged main, so the records are the acceptance's own and nothing else.
        sidecar = cost_records_path(snapshot.path)
        records = read_cost_records(boundaries.git, boundaries.cost_reader, "HEAD", sidecar)
        # The move comes first: `git mv` refuses a destination that already exists.
        destination = move_with_cost_records(boundaries.git, snapshot.path, "done")
        no_state = CannotHandle(kind=_MERGED, reason="the report on the main branch has no state")
        stage = require_state(document, no_state).stage
        before_approval = is_before_approval(self._definition, stage)
        booked = book_merge(document, bill(records), before_approval=before_approval)
        recorder.write(destination, booked)
        recorder.publish(MAIN_BRANCH, commit_subject(snapshot.id, "merged, archived"))


class SplitByWorkItemKind(Handler):
    """Sends a work item's event to the story's handler or to the acceptance's, by its id."""

    def __init__(self, story: Handler, acceptance: Handler) -> None:
        """Send stories' events to `story` and acceptances' events to `acceptance`."""
        self._story = story
        self._acceptance = acceptance

    def handle(self, event: Event) -> None:
        """Pass the event on by its work item's kind; `CannotHandle` when it names none."""
        if event.work_item is None:
            raise CannotHandle(kind=event.kind, reason="no work item")
        if is_acceptance(event.work_item.id):
            self._acceptance.handle(event)
        else:
            self._story.handle(event)

    @property
    def story(self) -> Handler:
        """The handler of a story's events."""
        return self._story

    @property
    def acceptance(self) -> Handler:
        """The handler of an acceptance's events."""
        return self._acceptance
