"""The write paths of a stage, read from the pipeline definition at its stage-start commit."""

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.domain.agent_runs import WritePathSettings
from factory.domain.errors import PipelineDefinitionInvalid
from factory.domain.paths import PIPELINE_DEFINITION_FILE, folder_of
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition
from factory.domain.write_paths import PROTECTED_PATHS, expand_write_paths


class WritePathService:
    """The one source of what an agent may write, for the take.

    It parses the definition itself rather than through `PipelineLoader`: this read is not
    the tick's load, so it checks no installed agent file and raises or clears no stop.
    """

    def __init__(self, boundaries: Boundaries) -> None:
        """Read through the git, the pipeline reader and the checkout of `boundaries`."""
        self._boundaries = boundaries

    def at(self, stage_start: StageStart, work_item_path: str) -> WritePathSettings:
        """The write path settings of the claimed stage, as the definition was at its commit.

        `ValueError` when `work_item_path` is no work item path; `PipelineDefinitionInvalid`
        when the definition is absent or invalid at the commit, or the stage has no role.
        """
        if folder_of(work_item_path) is None:
            raise ValueError(f"not a work item path: {work_item_path!r}")
        definition = self._definition_at(stage_start.commit)
        role = _role_of(definition, stage_start.claim.stage)
        try:
            write_paths = expand_write_paths(
                role.write_paths,
                work_item_path=work_item_path,
                feature_path=_feature_path(work_item_path),
            )
        except ValueError as error:
            raise PipelineDefinitionInvalid(str(error)) from error
        return WritePathSettings(
            root=self._boundaries.checkout,
            write_paths=write_paths,
            protected_paths=list(PROTECTED_PATHS),
        )

    def _definition_at(self, commit: str) -> PipelineDefinition:
        # Never the work tree's copy: an agent that rewrites it must widen nothing.
        text = self._boundaries.git.show_file(commit, PIPELINE_DEFINITION_FILE)
        if text is None:
            raise PipelineDefinitionInvalid(f"{PIPELINE_DEFINITION_FILE} is missing at {commit}")
        return self._boundaries.pipeline_reader.parse(text)


def _role_of(definition: PipelineDefinition, stage: str) -> RoleDefinition:
    if stage not in definition.stages:
        raise PipelineDefinitionInvalid(f"stage {stage} is not in {PIPELINE_DEFINITION_FILE}")
    role = definition.role_of(stage)
    if role is None:
        raise PipelineDefinitionInvalid(f"stage {stage} has no role")
    return role


def _feature_path(work_item_path: str) -> str:
    return work_item_path.rsplit("/", 2)[0]
