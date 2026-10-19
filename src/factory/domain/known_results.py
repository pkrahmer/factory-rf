"""The key a project command's result depends on, its records, and the result known for a key."""

import hashlib
from collections.abc import Sequence
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from factory.domain.checks import CheckStatus, CommandName
from factory.domain.cost_records import Duration
from factory.domain.git import TreeId
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.times import UtcDatetime

DefinitionDigest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class ResultKey(BaseModel):
    """What a command's result depends on: the command, its tree, the definition, the image."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    command: CommandName
    tree: TreeId
    definition: DefinitionDigest
    image: str | None


class ResultRecord(BaseModel):
    """One run of a stage's project command under its key, or one reuse of an earlier passed run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: ResultKey
    at: UtcDatetime
    status: CheckStatus
    last_line: str
    duration_seconds: Duration
    reused: UtcDatetime | None = None

    @model_validator(mode="after")
    def _only_a_passed_result_is_reused(self) -> Self:
        if self.reused is not None and self.status != "passed":
            raise ValueError(f"a reused result has the status passed, not {self.status}")
        return self


def definition_digest(definition: PipelineDefinition) -> DefinitionDigest:
    """The SHA-256, in lower-case hex, of the definition's JSON."""
    return hashlib.sha256(definition.model_dump_json().encode("utf-8")).hexdigest()


def known_result(records: Sequence[ResultRecord], key: ResultKey) -> ResultRecord | None:
    """The last real run of `key` when it passed; `None` when there is none or it did not pass."""
    runs = [record for record in records if record.reused is None and record.key == key]
    if not runs or runs[-1].status != "passed":
        return None
    return runs[-1]
