"""The git values the factory reasons about."""

from typing import Annotated

from pydantic import StringConstraints

CommitId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
