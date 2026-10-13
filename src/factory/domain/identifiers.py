"""The identifiers of the factory's work items."""

from typing import Annotated

from pydantic import StringConstraints

WorkItemId = Annotated[str, StringConstraints(pattern=r"^F\d{4}-[SA]\d{4}$")]

Name = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$")]
