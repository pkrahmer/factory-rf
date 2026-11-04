"""The cost record of one agent run, attributed to a work item, a stage and a role."""

from decimal import Decimal
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    StringConstraints,
    field_validator,
    model_validator,
)

from factory.domain.agent_runs import EndReason, Login, TokenCounts
from factory.domain.identifiers import Name, WorkItemId
from factory.domain.times import UtcDatetime

RunId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{32}$")]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Duration = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Cost = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]
TOOL_NAME_PATTERN = r"^[A-Za-z0-9_.:-]{1,64}$"
ToolName = Annotated[str, StringConstraints(pattern=TOOL_NAME_PATTERN)]


def _is_none(value: object) -> bool:
    return value is None


class MachineMeasures(BaseModel):
    """The machine around one run; a measure `None` is unknown.

    The image sizes are those of the image the run ran in, measured when it was built or
    chosen. The memory peak is the user slice's high-water mark since it began, not the run's.
    The CPU time and the waits are the run's own, but count every container of the user.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    base_image_bytes: NonNegativeInt | None = None
    project_layer_bytes: NonNegativeInt | None = None
    store_free_bytes: NonNegativeInt | None = None
    dataset_free_bytes: NonNegativeInt | None = None
    memory_peak_since_boot_bytes: NonNegativeInt | None = None
    memory_total_bytes: NonNegativeInt | None = None
    cpu_seconds: Duration | None = None
    cpu_wait_seconds: Duration | None = None
    memory_wait_seconds: Duration | None = None


class TranscriptRef(BaseModel):
    """Where a run's transcript was kept and what it held when written.

    `path` is relative to the transcript folder, `<work item>/<run id>.<ext>.gz`; `sha256` is
    the SHA-256 of the file as written, so a reader can tell it is the file the record names.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    sha256: Sha256

    @field_validator("path")
    @classmethod
    def _relative_gz_path(cls, path: str) -> str:
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts or not path.endswith(".gz"):
            raise ValueError(f"{path} is not a relative .gz path inside the transcript folder")
        return path


class ToolUse(BaseModel):
    """One tool's calls in a run: how many, how many failed, and the seconds they took.

    `tool` is the name the runtime gave the tool; `seconds` is `None` when no call of it
    carried times. It holds nothing of a call's input or output.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tool: ToolName
    calls: NonNegativeInt
    failed: NonNegativeInt
    seconds: Duration | None

    @model_validator(mode="after")
    def _failed_within_calls(self) -> Self:
        if self.failed > self.calls:
            raise ValueError(f"{self.failed} failed calls of {self.tool} exceed its {self.calls}")
        return self


class CostRecord(BaseModel):
    """One agent run: started, or completed with its measures; a measure `None` is unknown.

    `image` and `instance` say where the run ran: the machine's image and the name of
    the instance; either may be `None` on a record written without settings.
    `denials` counts the tool calls the runtime reported as refused and `denied_paths`
    holds the files they named, each once; both are `None` when the runtime gave no reply.
    `login` says which login the run's calls were handed: an API key, the subscription's
    token, or neither; it is `None` when the runtime had no login file.
    `machine` holds the machine's measures; it is `None` on a record written without them,
    and each of its measures is `None` when the machine could not give it.
    `transcript` names the run's kept transcript; it is `None` when none was kept.
    `tools` sums up the run's tool calls, one entry per tool sorted by name, `[]` for a run
    without one; it is `None` when the run's tool calls could not be read.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    run: RunId
    work_item: WorkItemId
    stage: Name
    role: Name
    attempt: NonNegativeInt
    status: Literal["started", "completed"]
    started_at: UtcDatetime
    duration_seconds: Duration | None = None
    model_seconds: Duration | None = None
    end_reason: EndReason | None = None
    turns: NonNegativeInt | None = None
    tokens: TokenCounts | None = None
    cost_usd: Cost | None = None
    image: str | None = None
    instance: Name | None = None
    denials: NonNegativeInt | None = None
    denied_paths: list[str] | None = None
    transcript: TranscriptRef | None = None
    tools: list[ToolUse] | None = None
    # Left out of a dump when unknown, so that a record copied through one never claims to have
    # asked the machine; the writer writes it null where it was asked.
    machine: MachineMeasures | None = Field(default=None, exclude_if=_is_none)
    login: Login | None = None

    @field_validator("cost_usd", mode="before")
    @classmethod
    def _cost_is_never_a_number(cls, value: object) -> object:
        # A float would round the cost; only a Decimal or its text keeps every digit.
        if value is None or isinstance(value, Decimal | str):
            return value
        raise ValueError(f"a cost is a Decimal or a string, got {type(value).__name__}")

    @model_validator(mode="after")
    def _measures_only_when_completed(self) -> Self:
        if self.status == "started":
            measures = {
                "duration_seconds": self.duration_seconds,
                "model_seconds": self.model_seconds,
                "end_reason": self.end_reason,
                "turns": self.turns,
                "tokens": self.tokens,
                "cost_usd": self.cost_usd,
                "denials": self.denials,
                "denied_paths": self.denied_paths,
                "login": self.login,
                "machine": self.machine,
                "transcript": self.transcript,
                "tools": self.tools,
            }
            for field, value in measures.items():
                if value is not None:
                    raise ValueError(f"a started record has no {field}")
        else:
            for field, value in (
                ("duration_seconds", self.duration_seconds),
                ("end_reason", self.end_reason),
            ):
                if value is None:
                    raise ValueError(f"a completed record needs {field}")
        return self

    @property
    def ok(self) -> bool:
        """Whether the run completed and ended as completed."""
        return self.status == "completed" and self.end_reason == "completed"
