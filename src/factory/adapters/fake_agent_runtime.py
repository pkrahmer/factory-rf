"""The fake agent runtime the tests use: scripted runs applied to the working directory."""

from collections import deque
from pathlib import Path, PurePath

from pydantic import BaseModel, ConfigDict

from factory.application.agent_runtime import AgentRuntime
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.cost_records import ToolUse
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import KillPoint, KillPoints
from factory.domain.transcripts import Transcript


class ScriptedRun(BaseModel):
    """What one fake run does: files it writes and deletes, its result, and whether it dies.

    `transcript` is what the runtime keeps of the result's session once the run has played.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    writes: dict[str, str] = {}
    deletes: list[str] = []
    result: AgentRunResult
    kill: bool = False
    transcript: Transcript | None = None


class FakeAgentRuntime(AgentRuntime):
    """An agent runtime that plays queued scripted runs and records every request."""

    def __init__(self, kill_points: KillPoints | None = None, version: str = "fake") -> None:
        """Start with nothing queued, on `kill_points`, reporting `version`."""
        self._kill_points = kill_points
        self._version = version
        self._queue: deque[ScriptedRun] = deque()
        self._requests: list[AgentRunRequest] = []
        self._played: list[ScriptedRun] = []

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
        self._played.append(scripted)
        _apply(scripted, request.working_directory)
        if scripted.kill and self._kill_points is not None:
            self._kill_points.reach(KillPoint.AGENT_RUN)
        return scripted.result

    def version(self) -> str:
        """The version given at construction."""
        return self._version

    def read_transcript(self, home: Path, session: str) -> Transcript | None:
        """The transcript of the latest played run whose result has `session`, wherever `home`."""
        del home
        for scripted in reversed(self._played):
            if scripted.result.session == session:
                return scripted.transcript
        return None

    def tool_uses(self, transcript: Transcript) -> list[ToolUse] | None:
        """No tool calls are read from a scripted transcript: always `None`."""
        del transcript
        return None


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
