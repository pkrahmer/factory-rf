"""The transcript of one agent session, in the form its runtime keeps it."""

from pydantic import BaseModel, ConfigDict


class Transcript(BaseModel):
    """A session's whole conversation: its bytes, and the extension of the form they are in."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    extension: str
    content: bytes


def transcript_lines(transcript: Transcript) -> list[str] | None:
    """The transcript's lines as UTF-8 text; `None` when its bytes are not UTF-8."""
    try:
        return transcript.content.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return None
