"""The one module that picks the concrete adapters behind the application's interfaces."""

import sys
from collections.abc import Mapping
from pathlib import Path

from factory.adapters.claude_guard import judge, read_guard_settings
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader
from factory.adapters.git_cli import GitCli
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.application.boundaries import Boundaries
from factory.application.costs import BillService
from factory.application.dispatcher import Handler
from factory.application.files import WorkItemReader
from factory.application.handlers.run import RunHandler
from factory.application.tick import HandlerFactory, IdleHandler
from factory.domain.events import EventKind
from factory.domain.identifiers import Name
from factory.domain.pipeline_definition import PipelineDefinition

__all__ = [
    "NOT_YET_HANDLED",
    "agent_environment",
    "build_bill_service",
    "build_handlers",
    "build_work_item_reader",
    "handler_factory",
    "judge",
    "production_environment",
    "read_guard_settings",
]

# The kinds with no handler yet, in the order of `EventKind`; registering one removes it here.
NOT_YET_HANDLED: tuple[EventKind, ...] = (
    "comment",
    "ask",
    "merged",
    "closed",
    "reject",
    "hand_over",
    "crash",
    "expired",
    "duplicate",
    "pull_request_lookup",
    "acceptance_due",
)

_SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"


def build_work_item_reader() -> WorkItemReader:
    """Return the reader of work item files."""
    return FrontmatterWorkItemReader()


def build_bill_service(checkout: Path) -> BillService:
    """Return the bill service that reads the remote-tracking refs of `checkout`."""
    return BillService(GitCli(checkout), JsonLinesCostRecordReader())


def agent_environment(scripts: Path, home: Path) -> dict[str, str]:
    """Return the agent run's environment: `scripts` first on the `PATH`, and `home`."""
    return {"PATH": f"{scripts}:{_SYSTEM_PATH}", "HOME": str(home)}


def production_environment() -> dict[str, str]:
    """Return the agent environment of this interpreter's scripts and the operator's home."""
    # The console scripts, `factory-guard` among them, sit next to the interpreter.
    return agent_environment(Path(sys.executable).parent, Path.home())


def build_handlers(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    instance: Name,
    environment: Mapping[str, str],
) -> dict[EventKind, Handler]:
    """Return the handler of every event kind that has one."""
    return {
        "idle": IdleHandler(),
        "run": RunHandler(boundaries, instance, definition, environment),
    }


def handler_factory(
    boundaries: Boundaries, instance: Name, environment: Mapping[str, str]
) -> HandlerFactory:
    """Return the factory that builds the handlers for each freshly loaded definition."""

    def handlers(definition: PipelineDefinition) -> dict[EventKind, Handler]:
        return build_handlers(boundaries, definition, instance, environment)

    return handlers
