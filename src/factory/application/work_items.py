"""The work items read from main's lifecycle folders and their branches on the remote."""

from pathlib import PurePosixPath

from factory.application.files import WorkItemReader
from factory.application.git import Git
from factory.domain.errors import WorkItemFormatError
from factory.domain.identifiers import (
    branch_name,
    feature_of,
    is_acceptance,
    parse_feature_directory_name,
    parse_work_item_file_name,
    work_item_order,
)
from factory.domain.paths import FEATURES_DIRECTORY, MAIN_BRANCH, REMOTE, LifecycleFolder, folder_of
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import (
    StoryFile,
    WorkItemDocument,
    WorkItemSnapshot,
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
        return [self._snapshot(story, first_stage) for story in self.list_stories("in-progress")]

    def _snapshot(self, story: StoryFile, first_stage: str) -> WorkItemSnapshot:
        branch = branch_name(story.id)
        branch_commit = self._git.resolve(f"{REMOTE}/{branch}")
        if branch_commit is None:
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
        try:
            return self._reader.parse(text)
        except WorkItemFormatError as error:
            raise WorkItemFormatError(error.fault, story.path) from error

    def _started_document(self, story: StoryFile, first_stage: str) -> WorkItemDocument:
        # The human starts a story by moving it into in-progress; any state its file claims is void.
        text = self._git.show_file(_MAIN_REF, story.path)
        if text is None:
            raise WorkItemFormatError(f"missing on {_MAIN_REF}", story.path)
        try:
            specification = self._reader.parse_specification(text)
        except WorkItemFormatError as error:
            raise WorkItemFormatError(error.fault, story.path) from error
        return WorkItemDocument(
            state=initial_state(first_stage),
            body=specification.body,
            ignored_keys=specification.ignored_keys,
        )


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
