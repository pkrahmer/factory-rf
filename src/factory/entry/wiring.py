"""The one module that picks the concrete adapters behind the application's interfaces."""

import re
import sys
from collections.abc import Mapping
from pathlib import Path

from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.claude_guard import judge, read_guard_settings
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.clock import SystemClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.pygithub_hosting import pygithub_service
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.acceptance import (
    AcceptanceClosed,
    AcceptanceDueHandler,
    AcceptanceHandOver,
    AcceptanceMerged,
    SplitByWorkItemKind,
)
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.costs import BillService
from factory.application.dispatcher import Handler
from factory.application.files import WorkItemReader
from factory.application.handlers.closed import ClosedHandler
from factory.application.handlers.comments import CommentHandler
from factory.application.handlers.hand_over import HandOverHandler
from factory.application.handlers.lookups import DuplicateHandler, PullRequestLookupHandler
from factory.application.handlers.merged import MergedHandler
from factory.application.handlers.questions import AskHandler
from factory.application.handlers.reject import RejectHandler
from factory.application.handlers.run import RunHandler
from factory.application.handlers.run_gate import RunGate
from factory.application.hosting import HostingService
from factory.application.recovery import RecoveryHandler
from factory.application.tick import HandlerFactory, IdleHandler
from factory.domain.errors import SettingsInvalid
from factory.domain.events import EventKind
from factory.domain.git import GitOptions
from factory.domain.identifiers import Name
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.settings import (
    CREDENTIAL_FILE_VARIABLE,
    REPOSITORY_URL_VARIABLE,
    RUNS_DIRECTORY_NAME,
    InstanceSettings,
)

__all__ = [
    "CREDENTIAL_HELPER",
    "NOT_YET_HANDLED",
    "agent_environment",
    "build_bill_service",
    "build_boundaries",
    "build_handlers",
    "build_work_item_reader",
    "git_environment",
    "git_options",
    "handler_factory",
    "judge",
    "production_environment",
    "read_guard_settings",
    "read_hosting_token",
    "repository_name",
]

# The kinds with no handler yet, in the order of `EventKind`; registering one removes it here.
NOT_YET_HANDLED: tuple[EventKind, ...] = ()

_SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"

CREDENTIAL_HELPER = "/usr/local/bin/git-credential-factory"

_SEGMENT = r"[A-Za-z0-9._-]+"
# The host and its separator for https, scp-like ssh and ssh URLs; then owner and name.
_REPOSITORY_URL = re.compile(
    r"(?:https://[^/\s]+/|ssh://git@[^/\s]+/|git@[^:/\s]+:)"
    rf"(?P<owner>{_SEGMENT})/(?P<name>{_SEGMENT}?)(?:\.git)?/?"
)


def build_work_item_reader() -> WorkItemReader:
    """Return the reader of work item files."""
    return FrontmatterWorkItemReader()


def git_environment(helper: str = CREDENTIAL_HELPER) -> dict[str, str]:
    """Return the git configuration of the factory as environment entries."""
    # Git reads no system or global configuration here, so the environment carries it:
    # the credential helper is the only route to the token, and the shared group keeps
    # the files git creates writable for both users of the checkout.
    return {
        "GIT_CONFIG_COUNT": "2",
        "GIT_CONFIG_KEY_0": "credential.helper",
        "GIT_CONFIG_VALUE_0": helper,
        "GIT_CONFIG_KEY_1": "core.sharedRepository",
        "GIT_CONFIG_VALUE_1": "group",
    }


def git_options(settings: InstanceSettings) -> GitOptions:
    """Return the git wrapper's options: the identity of `settings` and the git environment."""
    return GitOptions(identity=settings.git_identity, environment=git_environment())


def repository_name(url: str) -> str:
    """Return the `owner/name` of a hosted repository's URL; any other text is refused."""
    match = _REPOSITORY_URL.fullmatch(url)
    if match is None:
        raise SettingsInvalid(REPOSITORY_URL_VARIABLE, "names no owner/name on a host")
    return f"{match['owner']}/{match['name']}"


def read_hosting_token(path: Path | None) -> str:
    """Return the token held in the file at `path`, without surrounding whitespace."""
    if path is None:
        raise SettingsInvalid(CREDENTIAL_FILE_VARIABLE, "missing")
    try:
        token = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise SettingsInvalid(CREDENTIAL_FILE_VARIABLE, f"cannot read {path}: {error}") from error
    if not token:
        raise SettingsInvalid(CREDENTIAL_FILE_VARIABLE, f"{path} is empty")
    return token


def build_boundaries(
    settings: InstanceSettings, token: str, *, hosting: HostingService | None = None
) -> Boundaries:
    """Return the boundaries of the instance of `settings`; `hosting` replaces PyGithub."""
    if hosting is None:
        hosting = pygithub_service(repository_name(settings.repository_url), token)
    state = settings.state_directory
    clock = SystemClock()
    return Boundaries(
        git=GitCli(settings.checkout, git_options(settings)),
        hosting=hosting,
        agent_runtime=ClaudeCodeRuntime(settings.claude_executable, state / RUNS_DIRECTORY_NAME),
        project_commands=MakeProjectCommands(settings.checkout),
        work_item_reader=build_work_item_reader(),
        work_item_writer=FrontmatterWorkItemWriter(),
        cost_reader=JsonLinesCostRecordReader(),
        cost_writer=JsonLinesCostRecordWriter(),
        pipeline_reader=RuamelPipelineDefinitionReader(),
        agent_definitions=FrontmatterAgentDefinitionReader(settings.agent_home),
        clock=clock,
        log=TimestampedFactoryLog(state / "factory.log", clock),
        health=JsonHealthStatusFile(state / "health.json"),
        checkout=settings.checkout,
        settings=settings,
    )


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
    closed = SplitByWorkItemKind(
        ClosedHandler(boundaries, definition), AcceptanceClosed(boundaries, definition)
    )
    merged = SplitByWorkItemKind(
        MergedHandler(boundaries), AcceptanceMerged(boundaries, definition)
    )
    # Every agent run passes the gate, so a close or merge found then is handled first;
    # the gate holds the splits, so an acceptance never reaches the story's handlers.
    run = RunGate(
        boundaries, RunHandler(boundaries, instance, definition, environment), closed, merged
    )
    recovery = RecoveryHandler(
        boundaries, definition, ClaimService(boundaries, instance, definition), run
    )
    return {
        "idle": IdleHandler(),
        "run": run,
        "crash": recovery,
        "expired": recovery,
        "comment": CommentHandler(boundaries),
        "ask": AskHandler(boundaries, definition),
        "merged": merged,
        "closed": closed,
        "reject": RejectHandler(boundaries),
        "hand_over": SplitByWorkItemKind(
            HandOverHandler(boundaries, definition), AcceptanceHandOver(boundaries, definition)
        ),
        "acceptance_due": AcceptanceDueHandler(boundaries, definition),
        "duplicate": DuplicateHandler(),
        "pull_request_lookup": PullRequestLookupHandler(),
    }


def handler_factory(
    boundaries: Boundaries, instance: Name, environment: Mapping[str, str]
) -> HandlerFactory:
    """Return the factory that builds the handlers for each freshly loaded definition."""

    def handlers(definition: PipelineDefinition) -> dict[EventKind, Handler]:
        return build_handlers(boundaries, definition, instance, environment)

    return handlers
