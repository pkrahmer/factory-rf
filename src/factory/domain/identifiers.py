"""The identifiers of the factory's work items."""

from typing import Annotated

from pydantic import StringConstraints

WorkItemId = Annotated[str, StringConstraints(pattern=r"^F\d{4}-[SA]\d{4}$")]
