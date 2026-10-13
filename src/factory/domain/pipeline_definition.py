"""The pipeline definition: the project's stages, roles, caps and project commands."""

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from factory.domain.identifiers import Name

WORK_ITEM_PLACEHOLDER = "{work_item}"
FEATURE_PLACEHOLDER = "{feature}"


class RoleDefinition(BaseModel):
    """What an agent of one role may write and how long its runs may take, in minutes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    write_paths: list[str]
    lease_duration: PositiveInt = 60
    time_limit: PositiveInt = 40


class StageDefinition(BaseModel):
    """One stage: who works there, where it may move and what is checked after the agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Name | None = None
    # next[0] is the forward move; the others are moves back.
    next: list[Name] = []
    approval: bool = False
    checks: list[str] = []
    reports: list[str] = []
    round_cap: PositiveInt | None = None


class ProjectCommandDefinition(BaseModel):
    """One project command and the minutes it may run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    time_limit: PositiveInt = 10


def _default_project_commands() -> dict[str, ProjectCommandDefinition]:
    return {name: ProjectCommandDefinition() for name in ("check", "lint", "test")}


class PipelineDefinition(BaseModel):
    """The whole pipeline definition; the order of `stages` is the pipeline's order."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract: str
    stages: dict[Name, StageDefinition]
    roles: dict[Name, RoleDefinition]
    project_commands: dict[Name, ProjectCommandDefinition] = Field(
        default_factory=_default_project_commands
    )
    attempts_cap: PositiveInt = 2
    crash_cap: PositiveInt = 2
    acceptance_stage: Name | None = None

    def first_stage(self) -> str:
        """The stage a work item starts in: the first one of `stages`."""
        return next(iter(self.stages))

    def role_of(self, stage: str) -> RoleDefinition | None:
        """The role that works in `stage`, or `None` where no agent runs; `KeyError` if unknown."""
        role = self.stages[stage].role
        return None if role is None else self.roles[role]

    def position(self, stage: str) -> int:
        """The index of `stage` in the pipeline's order."""
        return list(self.stages).index(stage)
