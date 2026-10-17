"""The work items read from main's lifecycle folders and their branches on the remote."""

from collections.abc import Callable
from pathlib import PurePosixPath

from factory.application.files import WorkItemReader
from factory.application.git import Git
from factory.domain.errors import WorkItemFormatError
from factory.domain.git import CommitId
from factory.domain.identifiers import (
    branch_name,
    feature_of,
    is_acceptance,
    parse_feature_directory_name,
    parse_work_item_file_name,
    work_item_order,
)
from factory.domain.move_rule import StageChange
from factory.domain.paths import (
    FEATURES_DIRECTORY,
    MAIN_BRANCH,
    REMOTE,
    LifecycleFolder,
    feature_file_path,
    folder_of,
)
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import (
    StoryFile,
    WorkItemDocument,
    WorkItemSnapshot,
    WorkItemState,
    initial_state,
)

_MAIN_REF = f"{REMOTE}/{MAIN_BRANCH}"


class RemoteWorkItems:
    """Reads stories from the remote-tracking refs only, never a local branch or the work tree."""

    def __init__(self, git: Git, reader: WorkItemReader) -> None:
        """Read the refs through `git` and the work item files through `reader`."""
        self._git = git
        self._reader = reader

    def list_stories(self, folder: LifecycleFolder) -> list[StoryFile]:
        """The story files in `folder` on the remote's main, in work item order, then path."""
        stories = [
            story
            for story in (
                _story_file(path) for path in self._git.list_files(_MAIN_REF, FEATURES_DIRECTORY)
            )
            if story is not None and story.folder == folder
        ]
        return sorted(stories, key=lambda story: (work_item_order(story.id), story.path))

    def read(self, definition: PipelineDefinition) -> list[WorkItemSnapshot]:
        """One snapshot per story in progress, its state from its remote branch if it has one.

        Raises `WorkItemFormatError`, its path the story's, for a file that cannot be read.
        """
        first_stage = definition.first_stage()
        seen: set[str] = set()
        snapshots: list[WorkItemSnapshot] = []
        for story in self.list_stories("in-progress"):
            snapshots.append(self._snapshot(story, first_stage, duplicate=story.id in seen))
            seen.add(story.id)
        return snapshots

    def last_stage_change(self, snapshot: WorkItemSnapshot) -> StageChange | None:
        """The stage change of the newest commit beyond origin/main that touched the file.

        `None` when there is no such commit, when it is a merge or the branch's opening commit,
        when the file is missing before or after it, when the earlier text cannot be read, or
        when the stage stayed the same.
        """
        if snapshot.branch_commit is None:
            return None
        commits = self._git.log(f"{REMOTE}/{snapshot.branch}", since=_MAIN_REF, path=snapshot.path)
        if not commits or len(commits[0].parents) != 1:
            return None
        commit, parent = commits[0].commit, commits[0].parents[0]
        # The opening commit's parent is the text the human started on main, not a stage change.
        if self._git.is_ancestor(parent, _MAIN_REF):
            return None
        before = self._state_at(parent, snapshot.path)
        after = self._state_at(commit, snapshot.path)
        if before is None or after is None or before.stage == after.stage:
            return None
        return StageChange(
            from_stage=before.stage, to_stage=after.stage, correction=_is_correction(before, after)
        )

    def _state_at(self, commit: CommitId, path: str) -> WorkItemState | None:
        text = self._git.show_file(commit, path)
        if text is None:
            return None
        try:
            return self._reader.parse(text).state
        except WorkItemFormatError:
            return None

    def _snapshot(self, story: StoryFile, first_stage: str, *, duplicate: bool) -> WorkItemSnapshot:
        branch = branch_name(story.id)
        branch_commit = self._git.resolve(f"{REMOTE}/{branch}")
        # The branch of an id holds only its first file; a later file of that id is read from
        # main, so the duplicate reaches the dispatcher instead of failing the whole read.
        if branch_commit is None or duplicate:
            document = self._started_document(story, first_stage)
        else:
            document = self._branch_document(story, branch)
        return WorkItemSnapshot(
            id=story.id,
            path=story.path,
            folder=story.folder,
            branch=branch,
            branch_commit=branch_commit,
            document=document,
        )

    def _branch_document(self, story: StoryFile, branch: str) -> WorkItemDocument:
        # A branch already merged into main is still read: its tip holds the latest state.
        text = self._git.show_file(f"{REMOTE}/{branch}", story.path)
        if text is None:
            raise WorkItemFormatError(f"missing on branch {branch}", story.path)
        return parse_at(self._reader.parse, text, story.path)

    def _started_document(self, story: StoryFile, first_stage: str) -> WorkItemDocument:
        # The human starts a story by moving it into in-progress; any state its file claims is void.
        text = self._git.show_file(_MAIN_REF, story.path)
        if text is None:
            raise WorkItemFormatError(f"missing on {_MAIN_REF}", story.path)
        specification = parse_at(self._reader.parse_specification, text, story.path)
        return WorkItemDocument(
            state=initial_state(first_stage),
            body=specification.body,
            ignored_keys=specification.ignored_keys,
        )


def _is_correction(before: WorkItemState, after: WorkItemState) -> bool:
    appended = len(after.journal) > len(before.journal)
    return appended and after.journal[-1].kind == "move_back"


def read_feature_file(git: Git, feature_directory: str) -> str | None:
    """The text of the feature file of `feature_directory` on main, or `None` when it is missing."""
    return git.show_file(_MAIN_REF, feature_file_path(feature_directory))


def parse_at(parse: Callable[[str], WorkItemDocument], text: str, path: str) -> WorkItemDocument:
    """Parse `text` with `parse`; a `WorkItemFormatError` it raises names `path`."""
    try:
        return parse(text)
    except WorkItemFormatError as error:
        raise WorkItemFormatError(error.fault, path) from error


def _story_file(path: str) -> StoryFile | None:
    folder = folder_of(path)
    if folder is None:
        return None
    parts = PurePosixPath(path).parts
    feature_directory, file_name = parts[-3], parts[-1]
    directory = parse_feature_directory_name(feature_directory)
    name = parse_work_item_file_name(file_name)
    if directory is None or name is None:
        return None
    if is_acceptance(name.id) or feature_of(name.id) != directory.id:
        return None
    return StoryFile(
        id=name.id,
        path=path,
        feature_directory=feature_directory,
        file_name=file_name,
        folder=folder,
    )
