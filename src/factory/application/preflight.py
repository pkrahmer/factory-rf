"""The preflight: the machine's checks, keyed to the image, and the probe of the main branch."""

import os
import stat as stat_module
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from factory.application.boundaries import Boundaries
from factory.application.stage_environment import stage_environment_of
from factory.application.stops import StopService
from factory.domain.agent_runs import (
    QUESTION,
    AgentDefinition,
    AgentRunRequest,
    Login,
)
from factory.domain.checks import CheckResult
from factory.domain.errors import (
    AgentDefinitionError,
    AgentRuntimeError,
    ContainerError,
    GitError,
    HostingServiceError,
    ProjectCommandError,
    SnapshotError,
)
from factory.domain.git import CommitId
from factory.domain.paths import MAIN_BRANCH, REMOTE
from factory.domain.preflight import (
    PreflightItem,
    PreflightReport,
    PreflightStamp,
    changes_only_stop_records,
    machine_stop,
    version_matches,
)
from factory.domain.settings import (
    API_LOGIN_FILE_VARIABLE,
    CLAUDE_VERSION_VARIABLE,
    OPENCODE_MODELS_VARIABLE,
    OPENCODE_VERSION_VARIABLE,
    InstanceSettings,
)
from factory.domain.stops import RepositoryStop, RepositoryStopReason, StopScope

REQUIRED_TOOLS = ("git", "uv", "make")
# A container instance runs make and the runtime only inside its containers.
CONTAINER_TOOLS = ("git", "uv")

PROBE_COMMAND = "lint"
# A constant, the default of every project command: the preflight needs no pipeline definition.
PROBE_TIME_LIMIT = timedelta(minutes=10)

_MAIN_REF = f"{REMOTE}/{MAIN_BRANCH}"
_SHORT_COMMIT = 12
_MAIN_FAILING: RepositoryStopReason = "main_branch_failing"
_PREFLIGHT_FAILED: RepositoryStopReason = "preflight_failed"

_HOSTING_ITEM = "hosting-service"
_AGENTS_ITEM = "agents"
_VERSION_ITEM = "agent-runtime-version"
_HOSTING_FILE_ITEM = "token-file"
_AGENT_ENVIRONMENT_ITEM = "agent-environment"
_OPENCODE_ITEM = "opencode"
_PROBE_ITEM = "agent-run-probe"
_DATASET_ITEM = "dataset"
_STAGE_IMAGE_ITEM = "stage-image"
_NO_MAIN_TO_PREPARE = "no origin/main to prepare the stage environment from"

PROBE_AGENT = "coder"
PROBE_PROMPT = "Probe: end with the decision question and the entry probe."
PROBE_BUDGET_USD = Decimal("0.10")
PROBE_RUN_TIME_LIMIT = timedelta(minutes=2)

# Any bit for group or others on the token's folder lets a second user reach the
# hosting-service token, whatever the file's own mode.
_GROUP_AND_OTHERS = 0o077
_MISSING_FILE_FAULT = "the token file does not exist"


def tool_item(name: str, which: Callable[[str], str | None]) -> PreflightItem:
    """Check that the tool `name` is on the `PATH`; a missing one is reported, never installed."""
    if which(name) is None:
        detail = f"{name} is not on the PATH; add it to the image"
        return PreflightItem(name=f"tool:{name}", passed=False, detail=detail)
    return PreflightItem(name=f"tool:{name}", passed=True)


def token_file_item(
    path: Path | None, *, uid: int, stat: Callable[[Path], os.stat_result]
) -> PreflightItem:
    """Check that the token file exists in a folder that `uid` alone may enter.

    The file's own owner and mode do not count: a bind mount shows the host's.
    """
    fault = _token_file_fault(path, uid, stat)
    if fault is None:
        return PreflightItem(name=_HOSTING_FILE_ITEM, passed=True)
    return PreflightItem(name=_HOSTING_FILE_ITEM, passed=False, detail=f"{path}: {fault}")


def _token_file_fault(
    path: Path | None, uid: int, stat: Callable[[Path], os.stat_result]
) -> str | None:
    if path is None:
        return "no token file is set"
    # The folder comes first: a file in a folder the factory's user cannot enter
    # would raise PermissionError, not name the folder.
    folder_fault = _token_folder_fault(path.parent, uid, stat)
    if folder_fault is not None:
        return folder_fault
    try:
        stat(path)
    except FileNotFoundError:
        return _MISSING_FILE_FAULT
    return None


def _token_folder_fault(
    folder: Path, uid: int, stat: Callable[[Path], os.stat_result]
) -> str | None:
    try:
        facts = stat(folder)
    except FileNotFoundError:
        return _MISSING_FILE_FAULT
    if facts.st_uid != uid:
        return f"the folder {folder} belongs to uid {facts.st_uid}, not to {uid}"
    mode = stat_module.S_IMODE(facts.st_mode)
    if mode & _GROUP_AND_OTHERS:
        return f"the folder {folder} has mode {mode:04o}; make it 0700"
    return None


def tool_version_item(name: str, version: Callable[[], str]) -> PreflightItem:
    """Check that the tool `name` answers `--version`: `version()` returns its line or raises."""
    try:
        line = version()
    except (SnapshotError, ContainerError) as error:
        detail = f"{name} does not answer --version: {error}"
        return PreflightItem(name=name, passed=False, detail=detail)
    # Logged once per image build, so the factory log names the tool's version.
    return PreflightItem(name=name, passed=True, detail=line)


def dataset_item(dataset: str, exists: Callable[[], bool]) -> PreflightItem:
    """Check that the ZFS dataset `dataset` exists."""
    try:
        found = exists()
    except SnapshotError as error:
        detail = f"cannot list the dataset {dataset}: {error}"
        return PreflightItem(name=_DATASET_ITEM, passed=False, detail=detail)
    if not found:
        detail = (
            f"the dataset {dataset} does not exist; make it with zfs create, "
            f"and its base with zfs snapshot {dataset}@base"
        )
        return PreflightItem(name=_DATASET_ITEM, passed=False, detail=detail)
    return PreflightItem(name=_DATASET_ITEM, passed=True)


def stage_image_item(image: str, exists: Callable[[], bool]) -> PreflightItem:
    """Check that the stage image `image` is built."""
    try:
        found = exists()
    except ContainerError as error:
        detail = f"cannot look for the stage image {image}: {error}"
        return PreflightItem(name=_STAGE_IMAGE_ITEM, passed=False, detail=detail)
    if not found:
        detail = f"the stage image {image} is not built; build it with podman build"
        return PreflightItem(name=_STAGE_IMAGE_ITEM, passed=False, detail=detail)
    return PreflightItem(name=_STAGE_IMAGE_ITEM, passed=True)


def agent_environment_item(
    environment: Mapping[str, str],
    is_directory: Callable[[Path], bool],
) -> PreflightItem:
    """Check that an agent run finds its login in `HOME`."""
    fault = _home_fault(environment, is_directory)
    if fault is not None:
        return PreflightItem(name=_AGENT_ENVIRONMENT_ITEM, passed=False, detail=fault)
    return PreflightItem(name=_AGENT_ENVIRONMENT_ITEM, passed=True)


def _path_fault(
    environment: Mapping[str, str], find: Callable[[str, str], str | None], command: str
) -> str | None:
    path = environment.get("PATH")
    if path is None:
        return "the agent run has no PATH"
    if find(command, path) is None:
        return f"{command} is not on the agent run's PATH {path}"
    return None


def _home_fault(environment: Mapping[str, str], is_directory: Callable[[Path], bool]) -> str | None:
    home = environment.get("HOME")
    if home is None:
        return "the agent run has no HOME"
    if not is_directory(Path(home)):
        return f"the agent run's HOME {home} is no directory"
    return None


def opencode_item(
    settings: InstanceSettings,
    environment: Mapping[str, str],
    find: Callable[[str, str], str | None],
    agent_models: Sequence[str],
) -> PreflightItem:
    """Check that an agent run finds opencode and that every alias the agents use has a model.

    A container instance's opencode is the stage image's, so only the aliases are checked.
    """
    # No login is checked here: a build may log in with a key file or with a login of its
    # own in the agent's home, and only the probe shows whether a run can log in.
    faults: list[str] = []
    if settings.stage_environment != "container":
        path_fault = _path_fault(environment, find, settings.opencode_executable)
        if path_fault is not None:
            faults.append(path_fault)
    faults.extend(
        f"no model is set for {alias} in {OPENCODE_MODELS_VARIABLE}"
        for alias in _unmapped_aliases(settings.opencode_models, agent_models)
    )
    if faults:
        return PreflightItem(name=_OPENCODE_ITEM, passed=False, detail="; ".join(faults))
    return PreflightItem(name=_OPENCODE_ITEM, passed=True)


def _unmapped_aliases(models: Mapping[str, str], agent_models: Sequence[str]) -> list[str]:
    # A model with a slash is already opencode's `provider/model` id and needs no mapping.
    return sorted({model for model in agent_models if "/" not in model and model not in models})


def installed_models(boundaries: Boundaries) -> list[str]:
    """Return the model of every installed agent, each once, in the order of the agents' names."""
    definitions = boundaries.agent_definitions
    try:
        models = [definitions.read(name).model for name in definitions.names()]
    except AgentDefinitionError:
        # The item `agents` reports agents that cannot be read.
        return []
    return list(dict.fromkeys(models))


def agent_run_probe_item(
    boundaries: Boundaries, settings: InstanceSettings, environment: Mapping[str, str]
) -> PreflightItem:
    """Run the agent runtime once with a stage's flags; it passes when the run completes."""
    # A flag the pinned runtime rejects would end every real run `died` without saying why.
    main = boundaries.git.resolve(_MAIN_REF)
    if main is None:
        return PreflightItem(name=_PROBE_ITEM, passed=False, detail=_NO_MAIN_TO_PREPARE)
    try:
        installed = boundaries.agent_definitions.read(PROBE_AGENT)
        agent = installed.model_copy(update={"budget_usd": PROBE_BUDGET_USD})
        request = _probe_request(boundaries, agent, environment)
        stage_environment = stage_environment_of(boundaries)
        stage_environment.prepare(main, MAIN_BRANCH, sync_time_limit=PROBE_TIME_LIMIT)
        sealed = stage_environment.run_agent(request)
    except (AgentDefinitionError, AgentRuntimeError, SnapshotError, ContainerError) as error:
        return PreflightItem(name=_PROBE_ITEM, passed=False, detail=str(error))
    if sealed.nested_repositories:
        detail = (
            "the probe run left a git repository in the work tree, which the factory removed: "
            + ", ".join(sealed.nested_repositories)
        )
        return PreflightItem(name=_PROBE_ITEM, passed=False, detail=detail)
    result = sealed.result
    if result.end_reason != "completed":
        detail = (
            f"the probe run ended {result.end_reason}; "
            f"run {_runtime_command(settings)} by hand as the factory user to see why"
        )
        detail += _login_hint(settings, result.login)
        return PreflightItem(name=_PROBE_ITEM, passed=False, detail=detail)
    return PreflightItem(
        name=_PROBE_ITEM, passed=True, detail=_login_detail(settings, result.login)
    )


def _runtime_command(settings: InstanceSettings) -> str:
    if settings.agent_runtime == "opencode":
        return f"{settings.opencode_executable} run"
    return "claude -p"


def _login_hint(settings: InstanceSettings, login: Login | None) -> str:
    if login == "api_key":
        return (
            f"; the agent's API key is read from {settings.api_login_file}: "
            "check that it is valid and that its account has credit"
        )
    if settings.agent_runtime == "opencode":
        return _opencode_login_hint(login)
    if settings.claude_login_file is None:
        return ""
    return (
        f"; the agent's login token is read from {settings.claude_login_file}: "
        "make it with claude setup-token if it is missing, empty or expired"
    )


def _opencode_login_hint(login: Login | None) -> str:
    # opencode reads no subscription token, so the token hint would send the operator astray.
    if login != "none":
        return ""
    return (
        "; the agent runs get no API key: log in once as "
        "the factory user with the opencode build's own login, "
        f"or put a key in the file {API_LOGIN_FILE_VARIABLE} names"
    )


def _login_detail(settings: InstanceSettings, login: Login | None) -> str:
    # Said once per image build in the factory log, so the operator sees which login is in force.
    if login == "api_key":
        return f"the agent runs log in with the API key from {settings.api_login_file}"
    if login == "subscription":
        return (
            f"the agent runs log in with the subscription token from {settings.claude_login_file}"
        )
    if login == "none":
        return (
            "the agent runs get no login from a file; the runtime uses the login kept in its home"
        )
    return ""


def _probe_request(
    boundaries: Boundaries, agent: AgentDefinition, environment: Mapping[str, str]
) -> AgentRunRequest:
    checkout = boundaries.checkout
    return AgentRunRequest(
        agent=agent,
        prompt=PROBE_PROMPT,
        allowed_decisions=[QUESTION],
        time_limit=PROBE_RUN_TIME_LIMIT,
        working_directory=checkout,
        environment=dict(environment),
    )


class MachineChecks:
    """The preflight's items: the tools, the hosting service, the agents, the runtime's version."""

    def __init__(
        self,
        boundaries: Boundaries,
        settings: InstanceSettings,
        which: Callable[[str], str | None],
        extra: Sequence[Callable[[], PreflightItem]] = (),
    ) -> None:
        """Check the machine through `boundaries`, as `settings` describe it."""
        self._boundaries = boundaries
        self._settings = settings
        self._which = which
        self._extra = extra

    def run(self) -> PreflightReport:
        """Run every item, whatever the earlier ones found, and report them all in order."""
        tools = self._tools()
        items = [tool_item(tool, self._which) for tool in tools]
        items.append(self._hosting_service())
        items.append(self._agents())
        items.append(self._agent_runtime_version())
        items.extend(check() for check in self._extra)
        return PreflightReport(items=items)

    def _hosting_service(self) -> PreflightItem:
        try:
            self._boundaries.hosting.find_open_pull_request(MAIN_BRANCH)
        except HostingServiceError as error:
            detail = (
                f"the hosting service failed {error.operation}: {error.detail}; "
                "check the token and the network"
            )
            return PreflightItem(name=_HOSTING_ITEM, passed=False, detail=detail)
        return PreflightItem(name=_HOSTING_ITEM, passed=True)

    def _agents(self) -> PreflightItem:
        agent_home = self._settings.agent_home
        try:
            names = self._boundaries.agent_definitions.names()
        except AgentDefinitionError as error:
            detail = f"cannot read the agents in {agent_home}: {error}; install them there"
            return PreflightItem(name=_AGENTS_ITEM, passed=False, detail=detail)
        if not names:
            detail = f"no agents are installed in {agent_home}; install them there"
            return PreflightItem(name=_AGENTS_ITEM, passed=False, detail=detail)
        return PreflightItem(name=_AGENTS_ITEM, passed=True)

    def _tools(self) -> tuple[str, ...]:
        # A container instance's runtime is the stage image's; its version item finds it there.
        if self._settings.stage_environment == "container":
            return CONTAINER_TOOLS
        return (*REQUIRED_TOOLS, self._runtime_executable())

    def _runtime_executable(self) -> str:
        if self._settings.agent_runtime == "opencode":
            return self._settings.opencode_executable
        return self._settings.claude_executable

    def _runtime_pin(self) -> tuple[str | None, str]:
        settings = self._settings
        if settings.agent_runtime == "opencode":
            return settings.pinned_opencode_version, OPENCODE_VERSION_VARIABLE
        return settings.pinned_agent_version, CLAUDE_VERSION_VARIABLE

    def _agent_runtime_version(self) -> PreflightItem:
        pinned, variable = self._runtime_pin()
        if pinned is None:
            detail = f"the image does not pin a version: {variable} is not set"
            return PreflightItem(name=_VERSION_ITEM, passed=False, detail=detail)
        try:
            reported = self._boundaries.agent_runtime.version()
        except AgentRuntimeError as error:
            detail = f"cannot read the agent runtime's version: {error.detail}"
            return PreflightItem(name=_VERSION_ITEM, passed=False, detail=detail)
        if not version_matches(reported, pinned):
            detail = (
                f"the agent runtime reports {reported}, the image pins {pinned}; "
                "rebuild the image or change the pinned version"
            )
            return PreflightItem(name=_VERSION_ITEM, passed=False, detail=detail)
        return PreflightItem(name=_VERSION_ITEM, passed=True)


class PreflightStampStore(ABC):
    """Keeps the stamp of the last preflight that passed; a cache, never the truth."""

    @abstractmethod
    def read(self) -> PreflightStamp | None:
        """The stored stamp; a missing, unreadable or invalid store reads as `None`."""

    @abstractmethod
    def write(self, stamp: PreflightStamp) -> None:
        """Replace the stored stamp with `stamp`; a failed write raises `OSError`."""


class Preflight:
    """Runs the machine's checks once per image build and probes `main` once per commit."""

    def __init__(
        self,
        boundaries: Boundaries,
        checks: MachineChecks,
        stamps: PreflightStampStore,
        stops: StopService,
        image: str | None,
    ) -> None:
        """Check the machine built as `image`, remembering what passed in `stamps`."""
        self._boundaries = boundaries
        self._checks = checks
        self._stamps = stamps
        self._stops = stops
        self._image = image

    def run(self) -> RepositoryStopReason | None:
        """Run what changed since the last pass; `None` when it passed, else the stop raised."""
        started_with = self._stamps.read()
        stamp = self._machine_items(started_with)
        if stamp is None:
            self._clear_stale_failing_stop(started_with)
            return _PREFLIGHT_FAILED
        try:
            reason = self._probe(stamp)
        except (GitError, ProjectCommandError, SnapshotError, ContainerError) as error:
            self._raise("machine", _PREFLIGHT_FAILED, f"the probe on main could not run: {error}")
            return _PREFLIGHT_FAILED
        # The machine's items have passed or been skipped, so no machine stop may stand.
        self._stops.clear_stop(_PREFLIGHT_FAILED)
        return reason

    def _machine_items(self, stamp: PreflightStamp | None) -> PreflightStamp | None:
        """The stamp to probe with, or `None` when the machine's items failed."""
        # No timer: only a new image build can change what the machine's items find.
        if self._image is not None and stamp is not None and stamp.image == self._image:
            return stamp
        report = self._checks.run()
        self._log_passed_details(report)
        stop = machine_stop(report, at=self._boundaries.clock.now())
        if stop is not None:
            self._stops.raise_stop(stop)
            return None
        # A new build forgets what was probed: the image may hold other tools.
        passed = PreflightStamp(image=self._image)
        self._stamps.write(passed)
        return passed

    def _log_passed_details(self, report: PreflightReport) -> None:
        for item in report.items:
            if item.passed and item.detail:
                self._boundaries.log.line(f"preflight: {item.name}: {item.detail}")

    def _clear_stale_failing_stop(self, stamp: PreflightStamp | None) -> None:
        # The machine cannot run the probe, but a stop naming a commit that is no longer
        # main is stale; the new main is probed once the machine's items pass again.
        if stamp is None or stamp.main_failed is None:
            return
        try:
            main = self._boundaries.git.resolve(_MAIN_REF)
        except GitError:
            return
        if main != stamp.main_failed and not self._changes_only_stop_records(stamp.main_failed):
            self._stops.clear_stop(_MAIN_FAILING)

    def _changes_only_stop_records(self, since: CommitId) -> bool:
        # Publishing the stops commits to main without fixing it; a commit the clone
        # cannot compare is treated as a fix, so a stop never outlives an unknown main.
        try:
            paths = self._boundaries.git.changed_paths(since)
        except GitError:
            return False
        return changes_only_stop_records(paths)

    def _probe(self, stamp: PreflightStamp) -> RepositoryStopReason | None:
        main = self._boundaries.git.resolve(_MAIN_REF)
        if main is None:
            return None
        if stamp.main_failed == main:
            self._keep_failing_stop(main)
            return _MAIN_FAILING
        if stamp.main_probed != main:
            return self._run_probe(stamp, main)
        self._stops.clear_stop(_MAIN_FAILING)
        return None

    def _run_probe(self, stamp: PreflightStamp, main: CommitId) -> RepositoryStopReason | None:
        # On main only: a work item's red branch is its own concern, not the machine's.
        git = self._boundaries.git
        git.checkout(MAIN_BRANCH, start_point=_MAIN_REF)
        git.reset_to(_MAIN_REF)
        stage_environment_of(self._boundaries).prepare(
            main, MAIN_BRANCH, sync_time_limit=PROBE_TIME_LIMIT
        )
        result = self._boundaries.project_commands.run(PROBE_COMMAND, time_limit=PROBE_TIME_LIMIT)
        if result.passed:
            self._stops.clear_stop(_MAIN_FAILING)
            self._stamps.write(PreflightStamp(image=stamp.image, main_probed=main))
            return None
        self._raise("repository", _MAIN_FAILING, _failing_detail(result, main))
        # Remembered, so that idle ticks run no project command until a fix is pushed.
        self._stamps.write(PreflightStamp(image=stamp.image, main_failed=main))
        return _MAIN_FAILING

    def _keep_failing_stop(self, main: CommitId) -> None:
        status = self._boundaries.health.read()
        if any(stop.reason == _MAIN_FAILING for stop in status.stops):
            return
        detail = f"{PROBE_COMMAND} is red on main at {main[:_SHORT_COMMIT]} (probed earlier)"
        self._raise("repository", _MAIN_FAILING, detail)

    def _raise(self, scope: StopScope, reason: RepositoryStopReason, detail: str) -> None:
        stop = RepositoryStop(
            scope=scope, reason=reason, detail=detail, at=self._boundaries.clock.now()
        )
        self._stops.raise_stop(stop)


def _failing_detail(result: CheckResult, main: CommitId) -> str:
    commit = main[:_SHORT_COMMIT]
    if result.status == "time_limit":
        return f"{PROBE_COMMAND} reached its time_limit on main at {commit}"
    return f"{PROBE_COMMAND} is red on main at {commit}: {result.last_line}"
