"""The preflight: the machine's checks, keyed to the image, and the probe of the main branch."""

import os
import stat as stat_module
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from datetime import timedelta
from pathlib import Path

from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.domain.checks import CheckResult
from factory.domain.errors import (
    AgentDefinitionError,
    AgentRuntimeError,
    GitError,
    HostingServiceError,
    ProjectCommandError,
)
from factory.domain.git import CommitId
from factory.domain.paths import MAIN_BRANCH, REMOTE
from factory.domain.preflight import (
    PreflightItem,
    PreflightReport,
    PreflightStamp,
    machine_stop,
    version_matches,
)
from factory.domain.settings import CLAUDE_VERSION_VARIABLE, InstanceSettings
from factory.domain.stops import RepositoryStop, RepositoryStopReason, StopScope

REQUIRED_TOOLS = ("git", "uv", "make")

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
_AGENT_USER_ITEM = "agent-user"
_NO_AGENT_USER = (
    "FACTORY_AGENT_USER is not set: every agent would run as the factory's user, "
    "who can read the token file"
)
# Any bit for group or others lets a second user read the hosting-service token.
_GROUP_AND_OTHERS = 0o077


def tool_item(name: str, which: Callable[[str], str | None]) -> PreflightItem:
    """Check that the tool `name` is on the `PATH`; a missing one is reported, never installed."""
    if which(name) is None:
        detail = f"{name} is not on the PATH; add it to the image"
        return PreflightItem(name=f"tool:{name}", passed=False, detail=detail)
    return PreflightItem(name=f"tool:{name}", passed=True)


def token_file_item(
    path: Path | None, *, uid: int, stat: Callable[[Path], os.stat_result]
) -> PreflightItem:
    """Check that the token file exists, belongs to `uid` and is readable by its owner alone."""
    fault = _token_file_fault(path, uid, stat)
    if fault is None:
        return PreflightItem(name=_HOSTING_FILE_ITEM, passed=True)
    return PreflightItem(name=_HOSTING_FILE_ITEM, passed=False, detail=f"{path}: {fault}")


def _token_file_fault(
    path: Path | None, uid: int, stat: Callable[[Path], os.stat_result]
) -> str | None:
    if path is None:
        return "no token file is set"
    try:
        facts = stat(path)
    except FileNotFoundError:
        return "the token file does not exist"
    if facts.st_uid != uid:
        return f"the token file belongs to uid {facts.st_uid}, not to {uid}"
    mode = stat_module.S_IMODE(facts.st_mode)
    if mode & _GROUP_AND_OTHERS:
        return f"the token file has mode {mode:04o}; make it 0600 or 0400"
    return None


def agent_user_item(settings: InstanceSettings, exists: Callable[[Path], bool]) -> PreflightItem:
    """Check that no agent would run as the factory's user while a token file is there to read."""
    token_file = settings.token_file
    if settings.agent_user is None and token_file is not None and exists(token_file):
        return PreflightItem(name=_AGENT_USER_ITEM, passed=False, detail=_NO_AGENT_USER)
    return PreflightItem(name=_AGENT_USER_ITEM, passed=True)


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
        tools = (*REQUIRED_TOOLS, self._settings.claude_executable)
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

    def _agent_runtime_version(self) -> PreflightItem:
        pinned = self._settings.pinned_agent_version
        if pinned is None:
            detail = f"the image does not pin a version: {CLAUDE_VERSION_VARIABLE} is not set"
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
        stamp = self._machine_items(self._stamps.read())
        if stamp is None:
            return _PREFLIGHT_FAILED
        try:
            reason = self._probe(stamp)
        except (GitError, ProjectCommandError) as error:
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
        stop = machine_stop(self._checks.run(), at=self._boundaries.clock.now())
        if stop is not None:
            self._stops.raise_stop(stop)
            return None
        # A new build forgets what was probed: the image may hold other tools.
        passed = PreflightStamp(image=self._image)
        self._stamps.write(passed)
        return passed

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
