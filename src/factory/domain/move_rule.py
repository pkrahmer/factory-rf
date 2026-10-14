"""The move rule: which stage changes the pipeline definition allows on a work item."""

from pydantic import BaseModel, ConfigDict

from factory.domain.identifiers import Name, WorkItemId
from factory.domain.pipeline_definition import DONE_STAGE, PipelineDefinition


class StageChange(BaseModel):
    """A stage change one commit made, and whether it appended the factory's `move_back` entry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    from_stage: Name
    to_stage: Name
    correction: bool = False


class FactoryMove(BaseModel):
    """A move the factory itself may make, derived from the pipeline definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    from_stage: Name
    to_stage: Name


class IllegalChange(BaseModel):
    """A stage change the pipeline definition does not allow, and the work item it was made on."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_item: WorkItemId
    change: StageChange


def is_legal_change(definition: PipelineDefinition, change: StageChange) -> bool:
    """Whether `definition` allows `change`: a correction, no move, a `next` move or an archive."""
    if change.correction or change.from_stage == change.to_stage:
        return True
    stage = definition.stages.get(change.from_stage)
    if stage is None:
        return False
    # The human's merge accepts an approval stage, so the factory's archive is always legal there.
    return change.to_stage in stage.next or (stage.approval and change.to_stage == DONE_STAGE)


def factory_moves(definition: PipelineDefinition) -> list[FactoryMove]:
    """Every move of every `next` in stage order, then each approval stage's move to done."""
    pairs = [(name, target) for name, stage in definition.stages.items() for target in stage.next]
    pairs += [(name, DONE_STAGE) for name, stage in definition.stages.items() if stage.approval]
    unique = dict.fromkeys(pairs)
    return [FactoryMove(from_stage=source, to_stage=target) for source, target in unique]
