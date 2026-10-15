"""Opening a due feature acceptance and reading the facts its reviewer is given."""

from pydantic import BaseModel, ConfigDict

from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.application.costs import read_cost_records
from factory.application.dispatcher import Handler
from factory.application.work_items import read_feature_file
from factory.domain.acceptance import (
    AcceptanceFacts,
    FeatureAcceptance,
    acceptance_facts,
    acceptance_file_name,
    acceptance_head,
)
from factory.domain.bills import bill, cost_line
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CannotHandle, PushFailed, WorkItemFormatError
from factory.domain.events import Event
from factory.domain.git import CommitId
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
from factory.domain.sections import title

_MAIN_REF = f"{REMOTE}/{MAIN_BRANCH}"
_KIND = "acceptance_due"


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
