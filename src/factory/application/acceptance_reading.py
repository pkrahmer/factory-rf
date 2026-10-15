"""Reading each feature's acceptance status from the remote-tracking refs alone."""

from collections.abc import Sequence
from pathlib import PurePosixPath

from factory.application.boundaries import Boundaries
from factory.application.work_items import parse_at
from factory.domain.acceptance import (
    AcceptanceState,
    FeatureAcceptance,
    FeatureFiles,
    ReportFacts,
    acceptance_status,
    next_acceptance_id,
    story_file_ids,
)
from factory.domain.board import FeatureRow
from factory.domain.errors import WorkItemFormatError
from factory.domain.identifiers import (
    FeatureId,
    WorkItemId,
    feature_of,
    is_acceptance,
    parse_feature_directory_name,
    parse_work_item_file_name,
    work_item_of_branch,
)
from factory.domain.paths import (
    FEATURES_DIRECTORY,
    MAIN_BRANCH,
    REMOTE,
    LifecycleFolder,
    work_item_path,
)
from factory.domain.pipeline_definition import PipelineDefinition

_MAIN_REF = f"{REMOTE}/{MAIN_BRANCH}"
_REPORT_FOLDERS: tuple[LifecycleFolder, ...] = ("in-progress", "done")


class AcceptanceReader:
    """Reads the acceptance status of every feature from the last fetch; it writes nothing."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Read through the git and the work item reader of `boundaries`, under `definition`."""
        self._git = boundaries.git
        self._reader = boundaries.work_item_reader
        self._definition = definition

    def feature_files(self, feature: FeatureId, *, ref: str = _MAIN_REF) -> FeatureFiles:
        """The file names directly in the feature's lifecycle folders at `ref`."""
        directory = self._directories(ref).get(feature)
        if directory is None:
            return FeatureFiles(feature=feature)
        return self._files(feature, directory, ref)

    def read(self) -> list[FeatureAcceptance]:
        """One entry per feature directory on the remote's main, in feature id order.

        Raises `WorkItemFormatError`, its path the report's, for a report that cannot be read.
        """
        branches = self._acceptance_branches()
        return [
            self._feature_acceptance(feature, directory, branches)
            for feature, directory in sorted(self._directories(_MAIN_REF).items())
        ]

    def due_features(self) -> list[FeatureId]:
        """The features whose acceptance is due, ascending; none without an acceptance stage."""
        if self._definition.acceptance_stage is None:
            return []
        return [entry.feature for entry in self.read() if entry.status == "due"]

    def fill_board(self, rows: Sequence[FeatureRow]) -> list[FeatureRow]:
        """The rows in order, each with its known feature's acceptance status."""
        if self._definition.acceptance_stage is None:
            return list(rows)
        statuses = {entry.feature: entry.status for entry in self.read()}
        return [
            row.model_copy(update={"acceptance": statuses[row.feature]})
            if row.feature in statuses
            else row
            for row in rows
        ]

    def _directories(self, ref: str) -> dict[FeatureId, str]:
        names = {
            PurePosixPath(path).relative_to(FEATURES_DIRECTORY).parts[0]
            for path in self._git.list_files(ref, FEATURES_DIRECTORY)
        }
        directories: dict[FeatureId, str] = {}
        for name in sorted(names):
            parsed = parse_feature_directory_name(name)
            if parsed is not None:
                directories.setdefault(parsed.id, name)
        return directories

    def _files(self, feature: FeatureId, directory: str, ref: str) -> FeatureFiles:
        return FeatureFiles(
            feature=feature,
            backlog=self._names(ref, directory, "backlog"),
            in_progress=self._names(ref, directory, "in-progress"),
            done=self._names(ref, directory, "done"),
        )

    def _names(self, ref: str, directory: str, folder: LifecycleFolder) -> list[str]:
        folder_path = f"{FEATURES_DIRECTORY}/{directory}/{folder}"
        relative = (
            PurePosixPath(path).relative_to(folder_path)
            for path in self._git.list_files(ref, folder_path)
        )
        return [path.name for path in relative if len(path.parts) == 1]

    def _acceptance_branches(self) -> dict[WorkItemId, str]:
        branches: dict[WorkItemId, str] = {}
        for branch in self._git.remote_branches():
            work_item = work_item_of_branch(branch.name)
            if work_item is not None and is_acceptance(work_item):
                branches[work_item] = branch.name
        return branches

    def _feature_acceptance(
        self, feature: FeatureId, directory: str, branches: dict[WorkItemId, str]
    ) -> FeatureAcceptance:
        files = self._files(feature, directory, _MAIN_REF)
        reports = [
            *self._main_reports(directory, files),
            *self._branch_reports(feature, directory, branches),
        ]
        return FeatureAcceptance(
            feature=feature,
            directory=directory,
            status=acceptance_status(files, reports),
            archived=story_file_ids(files.done),
            next_acceptance=next_acceptance_id(feature, (report.id for report in reports)),
        )

    def _main_reports(self, directory: str, files: FeatureFiles) -> list[ReportFacts]:
        names = {"in-progress": files.in_progress, "done": files.done}
        reports: list[ReportFacts] = []
        for folder in _REPORT_FOLDERS:
            for file_name in names[folder]:
                parsed = parse_work_item_file_name(file_name)
                if parsed is not None and is_acceptance(parsed.id):
                    path = work_item_path(directory, folder, file_name)
                    reports.append(self._report(parsed.id, folder, _MAIN_REF, path))
        return reports

    def _branch_reports(
        self, feature: FeatureId, directory: str, branches: dict[WorkItemId, str]
    ) -> list[ReportFacts]:
        reports: list[ReportFacts] = []
        for work_item, branch in sorted(branches.items()):
            if feature_of(work_item) != feature:
                continue
            ref = f"{REMOTE}/{branch}"
            for file_name in self._names(ref, directory, "in-progress"):
                parsed = parse_work_item_file_name(file_name)
                if parsed is not None and parsed.id == work_item:
                    path = work_item_path(directory, "in-progress", file_name)
                    reports.append(self._report(work_item, "in-progress", ref, path))
        return reports

    def _report(
        self, work_item: WorkItemId, folder: LifecycleFolder, ref: str, path: str
    ) -> ReportFacts:
        text = self._git.show_file(ref, path)
        if text is None:
            raise WorkItemFormatError(f"missing on {ref}", path)
        state = parse_at(self._reader.parse, text, path).state
        if not isinstance(state, AcceptanceState):
            raise WorkItemFormatError("not an acceptance's state", path)
        return ReportFacts(id=work_item, folder=folder, state=state, on_branch=ref != _MAIN_REF)
