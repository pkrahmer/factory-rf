"""The journal of a work item: the record of each entry the front matter lists."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, PositiveInt

from factory.domain.identifiers import Name

HUMAN = "human"
FACTORY = "factory"

Speaker = Name
JournalKind = Literal[
    "created",
    "started",
    "result",
    "question",
    "comment",
    "close",
    "stall",
    "crash",
    "expiry",
    "move_back",
    "send_back",
    "done",
]


class JournalRecord(BaseModel):
    """One journal entry as the state lists it: its number, who spoke and what kind it is."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    number: PositiveInt
    speaker: Speaker
    kind: JournalKind
