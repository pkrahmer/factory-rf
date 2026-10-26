"""What the tests of the containers' extra environment share: the recorded words of each call."""

from collections.abc import Mapping, Sequence
from datetime import timedelta
from pathlib import Path
from typing import override

from adapters.claude_stand_in import Step, claude_request, write_stand_in
from adapters.container_runtime_support import container_environment, container_request, make_state
from adapters.opencode_stand_in import MODELS, write_opencode
from adapters.opencode_stand_in import REPLY as OPENCODE_REPLY
from adapters.test_claude_runtime_login import REPLY as CLAUDE_REPLY
from container_support import FIVE_MINUTES, Dataset
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.make_commands import ContainerMakeCommands
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.adapters.podman_runs import PodmanRuns
from factory.application.stage_environment import ContainerEnvironment
from factory.domain.containers import ContainerLaunch, ContainerResult, Mount
from factory.domain.git import CommitId
from podman_support import IMAGE

PROXY = "http://proxy.example.invalid:3128"
OTHER = "OTHER_HOST_NAME"
CA_NAMES = ("NODE_EXTRA_CA_CERTS", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE")
CHECK_LIMIT = timedelta(minutes=1)
COMMIT = CommitId("a" * 40)


class WordsRuns(FakeContainerRuns):
    """The fake's container runs, with the `podman run` words of each call recorded.

    A launch runs as the fake's; a run runs nothing and passes.
    """

    def __init__(self, workspace: Path) -> None:
        """Play `/work` as `workspace`; the words are those of `PodmanRuns` on it."""
        super().__init__(workspace)
        self._podman = PodmanRuns("podman", IMAGE, workspace)
        self.words: list[list[str]] = []

    def _record(
        self,
        command: Sequence[str],
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> None:
        launched = self._podman.launch(
            command,
            mounts=mounts,
            environment=environment,
            time_limit=time_limit,
            working_directory=working_directory,
        )
        self.words.append(launched.argv)

    @override
    def launch(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerLaunch:
        """Record the words, then launch as the fake does."""
        self._record(command, mounts, environment, time_limit, working_directory)
        return super().launch(
            command,
            mounts=mounts,
            environment=environment,
            time_limit=time_limit,
            working_directory=working_directory,
        )

    @override
    def run(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerResult:
        """Record the words and pass without running anything."""
        self._record(command, mounts, environment, time_limit, working_directory)
        return ContainerResult(
            exit_status=0,
            output="check: green (0.1 s)\n",
            timed_out=False,
            duration=timedelta(seconds=1),
        )


def write_bundle(tmp_path: Path) -> Path:
    """A CA bundle file on the machine, at an absolute path under `tmp_path`."""
    bundle = tmp_path.resolve() / "certs" / "ca.pem"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    bundle.write_text("not a certificate, read by no test\n", encoding="utf-8")
    return bundle


def env_words(words: Sequence[str]) -> dict[str, str]:
    """The `--env` pairs of `words`, by name; each name must stand once."""
    pairs = [words[index + 1] for index, word in enumerate(words[:-1]) if word == "--env"]
    names = [pair.partition("=")[0] for pair in pairs]
    assert len(names) == len(set(names)), names
    return dict(pair.partition("=")[::2] for pair in pairs)


def volume(path: Path) -> str:
    """The `--volume` word that mounts `path` read-only at its own path."""
    return f"{path}:{path}:ro"


def without_pairs(words: Sequence[str], flag: str, values: set[str]) -> list[str]:
    """`words` without each `flag` whose value is in `values`, nor that value."""
    kept: list[str] = []
    skip = False
    for index, word in enumerate(words):
        if skip:
            skip = False
            continue
        if word == flag and index + 1 < len(words) and words[index + 1] in values:
            skip = True
            continue
        kept.append(word)
    return kept


def sync_words(
    dataset: Dataset,
    *,
    extra: Mapping[str, str],
    bundle: Path | None,
) -> list[str]:
    """The words of the sync container of one prepare with `extra` and `bundle`."""
    runs = WordsRuns(dataset.workspace)
    environment = ContainerEnvironment(
        dataset.boundaries, dataset.snapshots, runs, extra_environment=extra, ca_bundle=bundle
    )
    environment.prepare(COMMIT, "main", sync_time_limit=FIVE_MINUTES)
    [words] = runs.words
    return words


def check_words(
    dataset: Dataset,
    *,
    extra: Mapping[str, str],
    bundle: Path | None,
) -> list[str]:
    """The words of the check container of one `make check` with `extra` and `bundle`."""
    runs = WordsRuns(dataset.workspace)
    boundaries = dataset.boundaries
    commands = ContainerMakeCommands(
        dataset.snapshots,
        runs,
        boundaries.git,
        checkout=boundaries.checkout,
        extra_environment=extra,
        ca_bundle=bundle,
    )
    commands.run("check", time_limit=CHECK_LIMIT)
    [words] = runs.words
    return words


def agent_words(
    tmp_path: Path,
    runtime: str,
    *,
    extra: Mapping[str, str],
    bundle: Path | None,
    request_environment: Mapping[str, str] | None = None,
) -> list[str]:
    """The words of the agent's container of one completed run of `runtime`.

    The request's environment is a container's, with `request_environment` added.
    """
    workspace = tmp_path / "workspace"
    (workspace / "checkout").mkdir(parents=True, exist_ok=True)
    (workspace / "home").mkdir(exist_ok=True)
    runs = WordsRuns(workspace)
    given = {**container_environment(tmp_path / "bin"), **(request_environment or {})}
    if runtime == "claude":
        executable = write_stand_in(tmp_path / "bin", [Step(stdout=CLAUDE_REPLY)])
        request = claude_request(tmp_path)
        agent: ClaudeCodeRuntime | OpencodeRuntime = ClaudeCodeRuntime(
            str(executable),
            make_state(tmp_path),
            containers=runs,
            extra_environment=extra,
            ca_bundle=bundle,
        )
    else:
        executable = write_opencode(tmp_path / "bin", [OPENCODE_REPLY])
        request = container_request(tmp_path)
        agent = OpencodeRuntime(
            str(executable),
            make_state(tmp_path),
            models=MODELS,
            containers=runs,
            extra_environment=extra,
            ca_bundle=bundle,
        )
    result = agent.run(request.model_copy(update={"environment": given}))
    assert result.end_reason == "completed", result
    [words] = runs.words
    return words
