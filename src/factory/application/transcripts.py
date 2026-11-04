"""Each agent run's transcript, kept compressed in a folder no container and no commit reaches."""

import gzip
from abc import ABC, abstractmethod
from pathlib import Path

from factory.application.agent_runtime import AgentRuntime
from factory.application.machine import FactoryLog
from factory.domain.agent_runs import AgentRunResult
from factory.domain.cost_records import TranscriptRef
from factory.domain.transcripts import Transcript

HOME_ON_THE_DATASET = "home"


class TranscriptStore(ABC):
    """The transcript folder: files written under it, readable by the factory's user alone."""

    @abstractmethod
    def write(self, path: str, data: bytes) -> str:
        """Write `data` to `path` under the folder with mode `0600`, replacing any file there.

        Return the SHA-256 of what was written, in lowercase hex; `OSError` when it cannot be.
        """


class TranscriptKeeper:
    """Keeps a run's transcript in the store under its run id, or logs why it did not."""

    def __init__(self, store: TranscriptStore, log: FactoryLog) -> None:
        """Write into `store` and log a transcript not kept to `log`."""
        self._store = store
        self._log = log

    def keep(self, work_item: str, run: str, transcript: Transcript) -> TranscriptRef | None:
        """Compress `transcript` to `<work item>/<run>.<extension>.gz` and name it.

        A run kept again replaces its file. `None`, and one log line, when it cannot be written.
        """
        path = f"{work_item}/{run}.{transcript.extension}.gz"
        try:
            sha256 = self._store.write(path, gzip.compress(transcript.content))
        except OSError as error:
            self.not_kept(run, str(error))
            return None
        return TranscriptRef(path=path, sha256=sha256)

    def not_kept(self, run: str, reason: str) -> None:
        """Log that the transcript of `run` was not kept, and why."""
        self._log.line(f"transcript: not kept for {run}: {reason}")


class SessionTranscripts:
    """Keeps the transcript of the session a run's result names, read from the agent's home."""

    def __init__(self, keeper: TranscriptKeeper, runtime: AgentRuntime, home: Path | None) -> None:
        """Read through `runtime` from `home`, the dataset's, and keep through `keeper`."""
        self._keeper = keeper
        self._runtime = runtime
        self._home = home

    def keep(self, work_item: str, run: str, result: AgentRunResult) -> TranscriptRef | None:
        """Keep the transcript of `result`'s session under `run`, before the dataset is reset.

        `None` and one log line when there is nothing to keep or it fails, so that a lost
        transcript never fails the run.
        """
        session = result.session
        if session is None:
            self._keeper.not_kept(run, "the run has no session")
            return None
        if self._home is None:
            self._keeper.not_kept(run, "the instance has no workspace")
            return None
        try:
            transcript = self._runtime.read_transcript(self._home, session)
        except OSError as error:
            self._keeper.not_kept(run, str(error))
            return None
        if transcript is None:
            self._keeper.not_kept(run, f"the runtime kept no transcript of session {session}")
            return None
        return self._keeper.keep(work_item, run, transcript)


def session_transcripts(
    store: TranscriptStore | None, log: FactoryLog, runtime: AgentRuntime, workspace: Path | None
) -> SessionTranscripts | None:
    """The transcripts of the runs on `workspace`'s home kept in `store`; `None` without one."""
    if store is None:
        return None
    home = None if workspace is None else workspace / HOME_ON_THE_DATASET
    return SessionTranscripts(TranscriptKeeper(store, log), runtime, home)
