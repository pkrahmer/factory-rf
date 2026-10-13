"""The pipeline definition: the project's stages, roles, caps and project commands."""

import re
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, model_validator

from factory.domain.identifiers import Name

WORK_ITEM_PLACEHOLDER = "{work_item}"
FEATURE_PLACEHOLDER = "{feature}"
CONTRACT_MAJOR = 1
DONE_STAGE = "done"
RESERVED_NAMES = ("human", "factory", "question")

_CONTRACT_FORM = re.compile(r"([0-9]+)\.[0-9]+")
_FAULT_SEPARATOR = "; "


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

    @model_validator(mode="after")
    def _follows_the_rules(self) -> Self:
        # The faults of one text are reported together, so the operator fixes them in one go.
        faults = [fault for rule in _RULES for fault in rule(self)]
        if faults:
            raise ValueError(_FAULT_SEPARATOR.join(faults))
        return self

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


def _contract_faults(definition: PipelineDefinition) -> list[str]:
    form = _CONTRACT_FORM.fullmatch(definition.contract)
    if form is None:
        return [f"contract must look like <major>.<minor>, got '{definition.contract}'"]
    major = form.group(1)
    if int(major) != CONTRACT_MAJOR:
        return [
            f"contract major {major} is not supported (this factory reads major {CONTRACT_MAJOR})"
        ]
    return []


def _done_stage_faults(definition: PipelineDefinition) -> list[str]:
    done = definition.stages.get(DONE_STAGE)
    if done is None:
        return [f"stages must hold a stage named {DONE_STAGE}"]
    if done.role is not None or done.next:
        return [f"stage {DONE_STAGE} must have no role and no next"]
    return []


def _next_faults(definition: PipelineDefinition) -> list[str]:
    return [
        f"stage {name}: next names unknown stage {target}"
        for name, stage in definition.stages.items()
        for target in stage.next
        if target not in definition.stages
    ]


def _role_faults(definition: PipelineDefinition) -> list[str]:
    undefined = [
        f"stage {name}: role {stage.role} is not defined in roles"
        for name, stage in definition.stages.items()
        if stage.role is not None and stage.role not in definition.roles
    ]
    without_paths = [
        f"role {name}: write_paths is empty"
        for name, role in definition.roles.items()
        if not role.write_paths
    ]
    approval_with_role = [
        f"stage {name}: an approval stage has no role"
        for name, stage in definition.stages.items()
        if stage.approval and stage.role is not None
    ]
    return undefined + without_paths + approval_with_role


def _reserved_name_faults(definition: PipelineDefinition) -> list[str]:
    stages = [
        f"stage name {name} is reserved" for name in definition.stages if name in RESERVED_NAMES
    ]
    roles = [f"role name {name} is reserved" for name in definition.roles if name in RESERVED_NAMES]
    return stages + roles


def _command_faults(definition: PipelineDefinition) -> list[str]:
    faults: list[str] = []
    for name, stage in definition.stages.items():
        faults += [
            f"stage {name}: check {command} is not a project command"
            for command in stage.checks
            if command not in definition.project_commands
        ]
        faults += [
            f"stage {name}: report {command} is not a project command"
            for command in stage.reports
            if command not in definition.project_commands
        ]
    return faults


def _minutes_at_stage(
    definition: PipelineDefinition, stage: StageDefinition, role: RoleDefinition
) -> int:
    commands = definition.project_commands
    listed = [*stage.checks, *stage.reports]
    return role.time_limit + sum(commands[name].time_limit for name in listed if name in commands)


def _lease_faults(definition: PipelineDefinition) -> list[str]:
    # The lease must outlast the agent run and every check and report after it, or another
    # claimant could take the work item over while the stage is still running.
    faults: list[str] = []
    for name, stage in definition.stages.items():
        role = definition.roles.get(stage.role) if stage.role is not None else None
        if role is None:
            continue
        total = _minutes_at_stage(definition, stage, role)
        if total > role.lease_duration:
            faults.append(
                f"role {stage.role} at stage {name}: {total} min exceed "
                f"lease_duration {role.lease_duration} min"
            )
    return faults


def _acceptance_stage_faults(definition: PipelineDefinition) -> list[str]:
    name = definition.acceptance_stage
    if name is None:
        return []
    stage = definition.stages.get(name)
    if stage is None or stage.role is None:
        return [f"acceptance_stage {name} is not a stage with a role"]
    return []


_RULES = (
    _contract_faults,
    _done_stage_faults,
    _next_faults,
    _role_faults,
    _reserved_name_faults,
    _command_faults,
    _lease_faults,
    _acceptance_stage_faults,
)
