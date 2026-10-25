"""Constants and helpers the wiring and preflight tests share."""

from factory.application.boundaries import Boundaries
from factory.domain.preflight import PreflightItem
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import machine_extras

CREDENTIAL = "example-value"
ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}
HOSTED_URL = "https://github.com/example/project.git"


def every_tool(name: str) -> str | None:
    """Find every tool, each under `/usr/bin`."""
    return f"/usr/bin/{name}"


def machine_item(
    boundaries: Boundaries, settings: InstanceSettings, environment: dict[str, str], name: str
) -> PreflightItem:
    """Return the item `name` of `machine_extras`, running only the items before it."""
    # The items run in order up to the one asked for, so the agent run probe never starts.
    for check in machine_extras(boundaries, settings, environment):
        item = check()
        if item.name == name:
            return item
    raise AssertionError(name)
