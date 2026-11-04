"""The transcript of one agent session, in the form its runtime keeps it."""

from pydantic import BaseModel, ConfigDict


class Transcript(BaseModel):
    """A session's whole conversation: its bytes, and the extension of the form they are in."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    extension: str
    content: bytes
