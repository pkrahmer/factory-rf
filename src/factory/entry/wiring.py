"""The one module that picks the concrete adapters behind the application's interfaces."""

import os
import re
import shutil
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from factory.adapters import claude_runtime, opencode_runtime
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.agent_home import SudoAgentHome
from factory.adapters.claude_runtime import SUDO_EXECUTABLE, ClaudeCodeRuntime
from factory.adapters.clock import SleepingWaiter, SystemClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.disk_space import ShutilDiskSpace
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.landlock import abi_version
from factory.adapters.make_commands import CommandUser, MakeProjectCommands
from factory.adapters.opencode_runtime import RUNTIME_FOLDERS, OpencodeRuntime
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.adapters.pygithub_hosting import pygithub_service
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.acceptance import (
    AcceptanceClosed,
    AcceptanceDueHandler,
    AcceptanceHandOver,
    AcceptanceMerged,
    SplitByWorkItemKind,
)
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.costs import BillService
from factory.application.dispatcher import Handler
from factory.application.files import PipelineDefinitionReader, WorkItemReader
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
from factory.application.machine import Clock, FactoryLog, HealthStatusStore
from factory.application.preflight import (
    MachineChecks,
    Preflight,
    agent_environment_item,
    agent_run_probe_item,
    agent_user_item,
    confinement_item,
    installed_models,
    opencode_item,
    token_file_item,
    tool_item,
)
from factory.application.project_agents import ProjectAgentDefinitions
from factory.application.project_commands import ProjectCommands, RecordingProjectCommands
from factory.application.recovery import RecoveryHandler
from factory.application.sealed_runs import SealedProjectCommands
from factory.application.stops import StopService
from factory.application.tick import HandlerFactory, IdleHandler, Tick
from factory.domain.agent_home import kept_paths
from factory.domain.agent_runs import CONFINE_COMMAND, scrub_environment
from factory.domain.command_records import CommandRecord
from factory.domain.disk import DiskRecord
from factory.domain.errors import SettingsInvalid
from factory.domain.events import EventKind
from factory.domain.git import GitOptions
from factory.domain.identifiers import Name
from factory.domain.known_results import ResultRecord
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.preflight import PreflightItem
from factory.domain.settings import (
    CREDENTIAL_FILE_VARIABLE,
    REPOSITORY_URL_VARIABLE,
    RUNS_DIRECTORY_NAME,
    InstanceSettings,
    read_setting_file,
    read_settings,
)
from factory.domain.stops import StopRecord

__all__ = [
    "CREDENTIAL_HELPER",
    "FRESH_HOME_MODULE",
    "UV_CACHE_FOLDER",
    "agent_environment",
    "agent_home_of",
    "agent_run_environment",
    "boundaries_from_environment",
    "build_bill_service",
    "build_boundaries",
    "build_handlers",
    "build_preflight",
    "build_tick",
    "build_work_item_reader",
    "fresh_home_command",
    "git_environment",
    "git_options",
    "handler_factory",
    "health_store",
    "leftovers_command",
    "machine_extras",
    "machine_log",
    "production_environment",
    "project_command_environment",
    "read_environment_settings",
    "read_hosting_token",
    "repository_name",
    "system_clock",
]

_SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"

CREDENTIAL_HELPER = "/usr/local/bin/git-credential-factory"

LEFTOVERS_MODULE = "factory.entry.leftovers"
FRESH_HOME_MODULE = "factory.entry.fresh_home"
# uv's package cache, which every run and command of the agent's user writes and reads.
UV_CACHE_FOLDER = ".cache/uv"

_LOG_FILE_NAME = "factory.log"
_HEALTH_FILE_NAME = "health.json"
_PREFLIGHT_STAMP_FILE_NAME = "preflight-stamp.json"
_COMMAND_RECORDS_PATH = Path("records", "project-commands.jsonl")
_DISK_RECORDS_PATH = Path("records", "disk.jsonl")
_STOP_RECORDS_PATH = Path("records", "stops.jsonl")
_RESULT_RECORDS_PATH = Path("records", "known-results.jsonl")

_SEGMENT = r"[A-Za-z0-9._-]+"
# The host and its separator for https, scp-like ssh and ssh URLs; then owner and name.
_REPOSITORY_URL = re.compile(
    r"(?:https://[^/\s]+/|ssh://git@[^/\s]+/|git@[^:/\s]+:)"
    rf"(?P<owner>{_SEGMENT})/(?P<name>{_SEGMENT}?)(?:\.git)?/?"
)


def build_work_item_reader() -> WorkItemReader:
    """Return the reader of work item files."""
    return FrontmatterWorkItemReader()


def build_pipeline_definition_reader() -> PipelineDefinitionReader:
    """Return the reader of the pipeline definition."""
    return RuamelPipelineDefinitionReader()


def git_environment(helper: str = CREDENTIAL_HELPER) -> dict[str, str]:
    """Return the git configuration of the factory as environment entries."""
    # Git reads no system or global configuration here, so the environment carries it:
    # the credential helper is the only route to the token. The shared mode makes what git
    # writes in `.git` readable and not writable by the group, so the agent's git can read
    # the repository and cannot change it; the work tree is outside this setting and stays
    # group-writable through the umask. This git runs as the user who can read the token,
    # so it runs no hooks; as command-line configuration this wins over the checkout's own.
    # A child git started for a nested repository inherits these pairs, so that repository's
    # `core.fsmonitor` never runs as this user either.
    return {
        "GIT_CONFIG_COUNT": "4",
        "GIT_CONFIG_KEY_0": "credential.helper",
        "GIT_CONFIG_VALUE_0": helper,
        "GIT_CONFIG_KEY_1": "core.sharedRepository",
        "GIT_CONFIG_VALUE_1": "0640",
        "GIT_CONFIG_KEY_2": "core.hooksPath",
        "GIT_CONFIG_VALUE_2": os.devnull,
        "GIT_CONFIG_KEY_3": "core.fsmonitor",
        "GIT_CONFIG_VALUE_3": "false",
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
    return read_setting_file(CREDENTIAL_FILE_VARIABLE, path, _read_utf8)


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_environment_settings(environ: Mapping[str, str]) -> InstanceSettings:
    """Return the settings of `environ`, the image identity read from the file it names.

    The temporary directory is the process's own, so it is read here and not from `environ`.
    """
    settings = read_settings(environ, read_file=_read_utf8)
    return settings.model_copy(update={"temporary_directory": Path(tempfile.gettempdir())})


def boundaries_from_environment(
    environ: Mapping[str, str], *, hosting: HostingService | None = None
) -> tuple[InstanceSettings, Boundaries]:
    """Return the settings of `environ` and their boundaries; `hosting` replaces PyGithub."""
    settings = read_environment_settings(environ)
    token = read_hosting_token(settings.token_file)
    return settings, build_boundaries(settings, token, hosting=hosting)


def system_clock() -> Clock:
    """Return the machine's clock."""
    return SystemClock()


def machine_log(state_directory: Path, clock: Clock | None = None) -> FactoryLog:
    """Return the factory log in `state_directory`, stamped by `clock` or the machine's clock."""
    return TimestampedFactoryLog(
        state_directory / _LOG_FILE_NAME, system_clock() if clock is None else clock
    )


def health_file(state_directory: Path) -> Path:
    """Return the path of the health file in `state_directory`."""
    return state_directory / _HEALTH_FILE_NAME


def health_store(state_directory: Path) -> HealthStatusStore:
    """Return the health status file in `state_directory`."""
    return JsonHealthStatusFile(health_file(state_directory))


def build_boundaries(
    settings: InstanceSettings,
    token: str,
    *,
    hosting: HostingService | None = None,
    which: Callable[[str], str | None] = shutil.which,
    confine_executable: str | None = CONFINE_COMMAND,
    end_leftovers: bool = True,
) -> Boundaries:
    """Return the boundaries of the instance of `settings`; `hosting` replaces PyGithub.

    The agent runtime starts the `sudo` that `which` finds, the one the preflight checks,
    and every call through `confine_executable`, unless it is `None`. With `end_leftovers`,
    every call as the agent's user is followed by the program that ends its processes.
    """
    if hosting is None:
        hosting = pygithub_service(repository_name(settings.repository_url), token)
    state = settings.state_directory
    clock = SystemClock()
    git = GitCli(settings.checkout, git_options(settings))
    log = machine_log(state, clock)
    sudo_executable = which("sudo") or SUDO_EXECUTABLE
    leftovers = leftovers_command() if end_leftovers else None
    agent_home = agent_home_of(settings, sudo_executable)
    return Boundaries(
        git=git,
        hosting=hosting,
        agent_runtime=_agent_runtime(settings, sudo_executable, confine_executable, leftovers),
        project_commands=RecordingProjectCommands(
            _project_commands(
                settings, git, log, sudo_executable, leftovers, agent_home=agent_home
            ),
            git,
            JsonLinesRecordLog(state / _COMMAND_RECORDS_PATH, CommandRecord),
            clock,
            log,
        ),
        work_item_reader=build_work_item_reader(),
        work_item_writer=FrontmatterWorkItemWriter(),
        cost_reader=JsonLinesCostRecordReader(),
        cost_writer=JsonLinesCostRecordWriter(),
        pipeline_reader=RuamelPipelineDefinitionReader(),
        agent_definitions=ProjectAgentDefinitions(
            git, FrontmatterAgentDefinitionReader(settings.agent_home)
        ),
        clock=clock,
        log=log,
        health=health_store(state),
        checkout=settings.checkout,
        settings=settings,
        disk=ShutilDiskSpace(),
        disk_records=JsonLinesRecordLog(state / _DISK_RECORDS_PATH, DiskRecord),
        stop_records=JsonLinesRecordLog(state / _STOP_RECORDS_PATH, StopRecord),
        waiter=SleepingWaiter(),
        result_records=JsonLinesRecordLog(state / _RESULT_RECORDS_PATH, ResultRecord),
        agent_home=agent_home,
    )


def leftovers_command() -> list[str]:
    """The words that start the leftovers program with this interpreter, isolated."""
    return [sys.executable, "-I", "-m", LEFTOVERS_MODULE]


def fresh_home_command() -> list[str]:
    """The words that start the fresh-home program with this interpreter, isolated."""
    # `-I` ignores PYTHONDONTWRITEBYTECODE; `-B` keeps the agent's user from writing
    # bytecode beside the factory's source, which the checkout's restore cannot remove.
    return [sys.executable, "-I", "-B", "-m", FRESH_HOME_MODULE]


def agent_home_of(settings: InstanceSettings, sudo_executable: str) -> SudoAgentHome | None:
    """The agent's home of the instance, or `None` when its agents run as no second user."""
    if settings.agent_user is None:
        return None
    # The agent home is the `.claude` folder inside the agent user's own home.
    home = settings.agent_home.parent
    # Both runtimes' logins, whichever runs: the operator may switch without a reset between.
    kept = kept_paths(
        home,
        login_files=[settings.claude_login_file, settings.api_login_file],
        state_files=[claude_runtime.LOGIN_STATE_FILE, opencode_runtime.LOGIN_STATE_FILE],
        folders=[UV_CACHE_FOLDER, *settings.opencode_folders],
    )
    return SudoAgentHome(
        home,
        kept,
        os_user=settings.agent_user,
        sudo_executable=sudo_executable,
        program=fresh_home_command(),
    )


def _project_commands(
    settings: InstanceSettings,
    git: GitCli,
    log: FactoryLog,
    sudo_executable: str,
    leftovers: list[str] | None,
    *,
    agent_home: SudoAgentHome | None,
) -> ProjectCommands:
    if settings.agent_user is None:
        return MakeProjectCommands(settings.checkout)
    # A project command runs code an agent wrote, so it runs with the agent's rights, which
    # reach neither the hosting token nor a writable git folder.
    user = CommandUser(
        os_user=settings.agent_user,
        sudo_executable=sudo_executable,
        environment=project_command_environment(settings, production_environment()),
        leftovers=leftovers,
    )
    return SealedProjectCommands(
        MakeProjectCommands(settings.checkout, user=user), git, log, agent_home
    )


def _agent_runtime(
    settings: InstanceSettings,
    sudo_executable: str,
    confine_executable: str | None,
    leftovers: list[str] | None,
) -> AgentRuntime:
    runs = settings.state_directory / RUNS_DIRECTORY_NAME
    if settings.agent_runtime == "opencode":
        return OpencodeRuntime(
            settings.opencode_executable,
            runs,
            models=settings.opencode_models,
            settings_file=settings.agent_home / "settings.json",
            sudo_executable=sudo_executable,
            api_login_file=settings.api_login_file,
            confine_executable=confine_executable,
            provider_limit=settings.provider_limit,
            runtime_folders=(*RUNTIME_FOLDERS, *settings.opencode_folders),
            leftovers=leftovers,
        )
    return ClaudeCodeRuntime(
        settings.claude_executable,
        runs,
        sudo_executable=sudo_executable,
        login_file=settings.claude_login_file,
        api_login_file=settings.api_login_file,
        confine_executable=confine_executable,
        provider_limit=settings.provider_limit,
        leftovers=leftovers,
    )


def build_bill_service(checkout: Path) -> BillService:
    """Return the bill service that reads the remote-tracking refs of `checkout`."""
    return BillService(GitCli(checkout), JsonLinesCostRecordReader())


def agent_environment(scripts: Path, home: Path) -> dict[str, str]:
    """Return the agent run's environment: `scripts` first on the `PATH`, and `home`."""
    return {"PATH": f"{scripts}:{_SYSTEM_PATH}", "HOME": str(home)}


def production_environment() -> dict[str, str]:
    """Return the agent environment: the allowed names of the process, its own `PATH` and home."""
    # The console scripts, `factory-confine` among them, sit next to the interpreter.
    own = agent_environment(Path(sys.executable).parent, Path.home())
    return scrub_environment({**os.environ, **own})


def agent_run_environment(settings: InstanceSettings, base: Mapping[str, str]) -> dict[str, str]:
    """Return a copy of `base`, its `HOME` the agent user's home when the agents run as one."""
    environment = dict(base)
    if settings.agent_user is not None:
        # The agent home is the `.claude` folder inside the agent user's own home.
        environment["HOME"] = str(settings.agent_home.parent)
    return environment


def project_command_environment(
    settings: InstanceSettings, base: Mapping[str, str]
) -> dict[str, str]:
    """The environment of a project command run as the agent user: no bytecode, uv copying."""
    # Bytecode folders, and files hard-linked from uv's cache in the agent's home, would leave
    # the checkout holding files the factory's own cleanup cannot remove or replace.
    return {
        **agent_run_environment(settings, base),
        "PYTHONDONTWRITEBYTECODE": "1",
        "UV_LINK_MODE": "copy",
    }


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


def build_preflight(
    boundaries: Boundaries,
    settings: InstanceSettings,
    which: Callable[[str], str | None],
    extra: Sequence[Callable[[], PreflightItem]] = (),
) -> Preflight:
    """Return the preflight of the machine of `settings`, its stamp in the state directory."""
    return Preflight(
        boundaries,
        MachineChecks(boundaries, settings, which, extra),
        JsonPreflightStampFile(settings.state_directory / _PREFLIGHT_STAMP_FILE_NAME),
        StopService(boundaries),
        settings.image,
    )


def machine_extras(
    boundaries: Boundaries,
    settings: InstanceSettings,
    which: Callable[[str], str | None],
    environment: Mapping[str, str],
) -> list[Callable[[], PreflightItem]]:
    """Return the preflight's items after the runtime's version, in the operator guide's order."""
    extras: list[Callable[[], PreflightItem]] = [
        lambda: token_file_item(settings.token_file, uid=os.getuid(), stat=os.stat),
        lambda: agent_user_item(settings, Path.exists),
    ]
    if settings.agent_user is not None:
        extras.append(lambda: tool_item("sudo", which))
    extras.append(lambda: agent_environment_item(environment, Path.is_dir))
    extras.append(lambda: confinement_item(abi_version, environment, _which_on))
    if settings.agent_runtime == "opencode":
        extras.append(
            lambda: opencode_item(settings, environment, _which_on, installed_models(boundaries))
        )
    extras.append(lambda: agent_run_probe_item(boundaries, settings, environment))
    return extras


def _which_on(name: str, path: str) -> str | None:
    return shutil.which(name, path=path)


def build_tick(
    boundaries: Boundaries,
    settings: InstanceSettings,
    which: Callable[[str], str | None] = shutil.which,
) -> Tick:
    """Return a new tick of the instance of `settings`, its agents in the production environment."""
    instance = settings.instance
    environment = agent_run_environment(settings, production_environment())
    extras = machine_extras(boundaries, settings, which, environment)
    return Tick(
        boundaries,
        instance,
        handler_factory(boundaries, instance, environment),
        preflight=build_preflight(boundaries, settings, which, extras),
    )
