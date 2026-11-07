# SPDX-License-Identifier: Apache-2.0
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
        # JSON writers leave U+2028, U+2029 and U+0085 raw in strings; splitlines breaks at them.
        return transcript.content.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        return None
