"""The fake agent runtime the tests use: scripted runs applied to the working directory."""

from collections import deque
from pathlib import Path, PurePath

from pydantic import BaseModel, ConfigDict

from factory.application.agent_runtime import AgentRuntime
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import KillPoint, KillPoints


class ScriptedRun(BaseModel):
    """What one fake run does: files it writes and deletes, its result, and whether it dies."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    writes: dict[str, str] = {}
    deletes: list[str] = []
    result: AgentRunResult
    kill: bool = False


class FakeAgentRuntime(AgentRuntime):
    """An agent runtime that plays queued scripted runs and records every request."""

    def __init__(self, kill_points: KillPoints | None = None, version: str = "fake") -> None:
        """Start with nothing queued, on `kill_points`, reporting `version`."""
        self._kill_points = kill_points
        self._version = version
        self._queue: deque[ScriptedRun] = deque()
        self._requests: list[AgentRunRequest] = []

    def queue(self, run: ScriptedRun) -> None:
        """Add `run` to be played by a later call of `run`."""
        self._queue.append(run)

    def requests(self) -> list[AgentRunRequest]:
        """Every request received, in order, those that raised included."""
        return list(self._requests)

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Play the oldest queued run in the request's working directory."""
        self._requests.append(request)
        if not self._queue:
            raise AgentRuntimeError("no scripted run is queued")
        scripted = self._queue.popleft()
        _apply(scripted, request.working_directory)
        if scripted.kill and self._kill_points is not None:
            self._kill_points.reach(KillPoint.AGENT_RUN)
        return scripted.result

    def version(self) -> str:
        """The version given at construction."""
        return self._version


def _apply(scripted: ScriptedRun, directory: Path) -> None:
    # Check every path first, so that a bad one leaves the directory untouched.
    writes = {_inside(directory, path): text for path, text in scripted.writes.items()}
    deletes = [_inside(directory, path) for path in scripted.deletes]
    for target, text in writes.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    for target in deletes:
        target.unlink(missing_ok=True)


def _inside(directory: Path, path: str) -> Path:
    relative = PurePath(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise AgentRuntimeError(f"path {path} leaves the working directory")
    return directory / relative
