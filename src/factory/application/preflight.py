"""The checks of the machine the preflight runs, each reported whatever the others found."""

from collections.abc import Callable, Sequence

from factory.application.boundaries import Boundaries
from factory.domain.errors import AgentDefinitionError, AgentRuntimeError, HostingServiceError
from factory.domain.paths import MAIN_BRANCH
from factory.domain.preflight import PreflightItem, PreflightReport, version_matches
from factory.domain.settings import CLAUDE_VERSION_VARIABLE, InstanceSettings

REQUIRED_TOOLS = ("git", "uv", "make")

_HOSTING_ITEM = "hosting-service"
_AGENTS_ITEM = "agents"
_VERSION_ITEM = "agent-runtime-version"


def tool_item(name: str, which: Callable[[str], str | None]) -> PreflightItem:
    """Check that the tool `name` is on the `PATH`; a missing one is reported, never installed."""
    if which(name) is None:
        detail = f"{name} is not on the PATH; add it to the image"
        return PreflightItem(name=f"tool:{name}", passed=False, detail=detail)
    return PreflightItem(name=f"tool:{name}", passed=True)


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
