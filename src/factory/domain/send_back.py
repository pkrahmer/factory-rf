"""The rules of a send-back at an approval: the reason, the target stage and the round cap."""

from factory.domain.journal import JournalKind, JournalRecord
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument


def _records(document: WorkItemDocument) -> list[JournalRecord]:
    return [] if document.state is None else document.state.journal


def recorded_since_latest_result(document: WorkItemDocument, kind: JournalKind) -> bool:
    """Whether the journal holds a record of `kind` numbered after the latest `result` record.

    Any record of `kind` counts when there is no `result` record.
    """
    records = _records(document)
    latest_result = max((record.number for record in records if record.kind == "result"), default=0)
    return any(record.kind == kind and record.number > latest_result for record in records)


def reason_given(document: WorkItemDocument) -> bool:
    """Whether the human commented since the latest result, judged from the records alone.

    The text is never read: the code does not interpret what the human wrote.
    """
    return recorded_since_latest_result(document, "comment")


def send_back_target(definition: PipelineDefinition, approval: str) -> str | None:
    """The stage a close at `approval` sends the story back to, or None without one."""
    following = definition.stages[approval].next
    if len(following) < 2:
        return None
    return following[1]


def send_back_cap(definition: PipelineDefinition, approval: str) -> int | None:
    """The round cap of the first capped stage that hands over to `approval`, or None."""
    for stage in definition.stages.values():
        if stage.next and stage.next[0] == approval and stage.round_cap is not None:
            return stage.round_cap
    return None
