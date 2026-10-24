---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 409
comments_read: [6384531243]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T13:00:18.704831Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T13:00:18.711283Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-24T13:00:36.695983Z'
  stage: intake
  run: 5b2c48fbf75643d4800ddf82be1ee79d
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-24T13:01:53.563030Z'
  stage: intake
---

# Podman runs start a throwaway container on the dataset

## Description

Every step of a v1.2 stage runs in a container that is thrown away when it ends (`planning/v1.2-plan.md`, "The cycle of a stage", steps 3, 5 and 7): the stage image, started with `--rm`, the dataset mounted at `/work`, rootless with `--userns=keep-id` so that the container's user is the host's `factory`, and `--timeout` so that the container runtime ends the run at its limit. This story adds the first real implementation of the `ContainerRuns` interface of S0001, `PodmanRuns`. Its `launch` builds the `podman run` command line and adds `CONTAINER_GRACE`, 30 seconds, to the time limit of the process request, so that podman's `--timeout` kills first and the factory's own kill fires only when it did not (`feature.md`, decision 11, as the agent's own `timeout` under `sudo` today); its `run` runs that line through `run_process` and reads podman's exit status as the command's, a container that `--timeout` ended (exit status 137 or -9 at or after the limit, the statuses the sudo chain reads today) as ended by the time limit. That podman exits 137 for a container its `--timeout` ended is this story's assumption; F0043's story 4 measures it on the VM (the plan's risk "Podman's `--timeout`"). The command line is pinned by a test, the read-only mounts above all: a rootless container cannot write a `:ro` bind mount, and that mount is the whole protection of the host's repository and of the login files (the plan's risk "The private repository"). It also offers `version()` and `image_exists()`, which S0011 (the preflight) reads. The adapter is tested on a stand-in `podman` that records its arguments and answers as planned; the real `podman` runs only on the VM, in F0043's story 4. Nothing wires the class yet (S0010); the runtimes start using `launch` in S0008, the environment `run` in S0007 and S0009.

## Interface

`factory.adapters.podman_runs` (`adapters`), new:

```python
CONTAINER_GRACE = timedelta(seconds=30)
PODMAN_TIME_LIMIT = timedelta(minutes=2)


class PodmanRuns(ContainerRuns):
    """Throwaway containers of one image, started rootless by the `podman` executable."""

    def __init__(
        self, executable: str, image: str, workspace: Path, *, time_limit: timedelta = PODMAN_TIME_LIMIT
    ) -> None: ...

    def version(self) -> str:
        """The first non-blank line `<podman> --version` prints; `ContainerError` when it fails."""

    def image_exists(self) -> bool:
        """Whether `<podman> image exists <image>` finds the image; `ContainerError` for any other failure."""
```

- `launch(command, *, mounts, environment, time_limit, working_directory)` returns `ContainerLaunch(argv=[executable, "run", "--rm", "--userns=keep-id", "--timeout", "<seconds>", "--env", "NAME=value", ..., "--volume", "<workspace>:/work", "--volume", "<source>:<target>", or "<source>:<target>:ro" for a read-only mount, ..., "--workdir", working_directory, image, *command], env={}, time_limit=time_limit + CONTAINER_GRACE)`. `<seconds>` is the time limit in whole seconds, rounded up (`30s` is `30`, 1.5 seconds is `2`). The `--env` pairs come in the order of `environment`; the `/work` volume comes first and the given mounts follow in their order. `env` is `None`: the `podman` program runs with the factory's own environment (`HOME`, `XDG_RUNTIME_DIR`, `PATH` and whatever the service sets for it), as `version()` does; the container gets none of it, since podman passes only the `--env` pairs and the image's own variables in. A mount whose target is `/work` or starts with `/work/`, and an empty `command`, raise `ValueError` (the interface's rule).
- `run(...)` runs `launch(...)` through `run_process` of `factory.adapters.process` with `cwd` `/` (podman reads no file from its working directory; a missing workspace is podman's own fault, status 125, not a start fault), `env` `{}`, `time_limit` the launch's (the limit plus the grace) and `merge_stderr` true, and returns `ContainerResult`: `timed_out` is true when `run_process` says so, or when the exit status is in `KILL_STATUSES` of `factory.adapters.agent_launch` (137 or -9; imported, not copied) after at least `time_limit` (podman's `--timeout` sent the kill); then `exit_status` is `None`. Otherwise `exit_status` is podman's, which is the command's (podman exits 125 for its own faults, such as a missing image, and the result then says 125 with podman's message in `output`). `output` is the merged output, `duration` the process's. A `podman` that cannot start (`OSError`) is `ContainerError(command[0], <the operating system's message>)`, `command[0]` the first word of the command asked for, not `podman`. The structural test `tests/test_wrapper_search.py` names the module (decision 18 c of `feature.md`).
- `version()` runs `[executable, "--version"]` through `run_process` (`cwd` `workspace`, `env` `None`, `time_limit` the constructor's, `PODMAN_TIME_LIMIT` of 2 minutes by default, stderr merged) and returns the first non-blank line stripped (`podman version 4.9.3`). A fault is `ContainerError(f"{executable} --version", <detail>)`: an exit status other than 0 has the last non-blank output line as `detail`, or `exit status <n>` when the output has none; a time limit has `no end within <n> s`, `n` the whole seconds of the limit rounded up (`no end within 120 s` by default); exit status 0 without output has `printed nothing`; an executable that cannot be started (`OSError`) has the operating system's message, as `run` does. The preflight's `podman` item (S0011) reads a missing `podman` from this error, never from an `OSError`.
- `image_exists()` runs `[executable, "image", "exists", image]` the same way: exit status 0 is `True`, 1 is `False`, any other status is `ContainerError(f"{executable} image exists {image}", <the last non-blank output line or `exit status <n>`>)`; a time limit and an executable that cannot be started are the same faults as for `version()`, with this command.

Tests (the tester writes them): `tests/adapters/test_podman_runs.py` (the command line) and `tests/adapters/test_podman_runs_results.py` (the results and faults), with a stand-in `podman` written into `tmp_path` by a helper like `write_sudo` of `tests/sudo_support.py`: it records its arguments and its environment to a file, and either prints planned output and exits with a planned status after a planned wait, or, when its arguments hold the image word, runs the words after the image on the host (so that a test can see the command's own exit status and output pass through). No real `podman` is run anywhere.

## Acceptance criteria

1. `PodmanRuns(<stand-in>, "factory-stage:1", Path("/srv/factory/vm/work")).launch(["/bin/sh", "-c", "make sync"], mounts=[Mount(source=Path("/srv/factory/vm/repo/.git"), target="/upstream", read_only=True), Mount(source=Path("/home/factory/.claude-token"), target="/home/factory/.claude-token", read_only=True), Mount(source=Path("/state/runs/instructions-1.md"), target="/state/runs/instructions-1.md")], environment={"HOME": "/work/home", "PATH": "/usr/local/bin:/usr/bin:/bin"}, time_limit=timedelta(minutes=40), working_directory="/work/checkout")` returns `argv` exactly `[<stand-in>, "run", "--rm", "--userns=keep-id", "--timeout", "2400", "--env", "HOME=/work/home", "--env", "PATH=/usr/local/bin:/usr/bin:/bin", "--volume", "/srv/factory/vm/work:/work", "--volume", "/srv/factory/vm/repo/.git:/upstream:ro", "--volume", "/home/factory/.claude-token:/home/factory/.claude-token:ro", "--volume", "/state/runs/instructions-1.md:/state/runs/instructions-1.md", "--workdir", "/work/checkout", "factory-stage:1", "/bin/sh", "-c", "make sync"]`, `env` `{}` and `time_limit` 40 minutes and 30 seconds.
2. The seconds of `--timeout` (rows of one parametrized test): 30 seconds gives `30`, 1.5 seconds gives `2`, 40 minutes gives `2400`. With no mounts and no environment the words hold one `--volume` (the workspace) and no `--env`.
3. `launch` and `run` raise `ValueError` for a mount with target `/work`, for one with target `/work/checkout`, and for a `command` of `[]`; a mount with target `/workspace` is accepted (rows of one parametrized test).
4. `run(["/bin/sh", "-c", 'echo out; echo err >&2; exit 3'], mounts=[], environment={}, time_limit=10 s, working_directory="/work")` with a stand-in that runs the words after the image gives `exit_status` 3, `timed_out` false and `output` holding `out` and `err`; the stand-in's recorded environment is the test's (the test sets `FACTORY_PROBE_VARIABLE` with `monkeypatch.setenv` and the record holds it); the stand-in's working directory is `/`.
5. The kill at the limit (rows of one parametrized test): a stand-in that exits 137 after 3 seconds, under `time_limit` 3 seconds, gives `timed_out` true and `exit_status` `None`; a stand-in that exits 137 at once under `time_limit` 30 seconds gives `timed_out` false and `exit_status` 137; a stand-in that exits -9 (kills itself with `SIGKILL`) after 2 seconds under `time_limit` 2 seconds gives `timed_out` true; with `run_process` of `factory.adapters.podman_runs` replaced by a `Recorder` (`tests/run_process_recorder.py`) that answers `ProcessResult(exit_status=None, stdout="", stderr="", timed_out=True, duration=timedelta(seconds=31))`, `run` under `time_limit` 1 second gives `timed_out` true and `exit_status` `None`, and the recorded request's `time_limit` is 31 seconds (the limit plus `CONTAINER_GRACE`), its `merge_stderr` true and its `cwd` the workspace.
6. A stand-in that exits 125 at once printing `Error: factory-stage:1: image not known` gives `exit_status` 125, `timed_out` false and that line in `output`. `run(["/bin/true"], ...)` with an executable that does not exist raises `ContainerError` whose `command` is `/bin/true` and whose `detail` starts with `[Errno 2]`.
7. `version()` (rows of one parametrized test): planned to print `podman version 4.9.3` returns it and the call's arguments are `["--version"]`; planned to print nothing and exit 0 raises `ContainerError` with `detail` `printed nothing`; planned to exit 1 with `podman: command not found` raises it with that detail and `command` `<stand-in> --version`; planned to exit 2 printing nothing raises it with `detail` `exit status 2`; a stand-in that sleeps 60 seconds, under an adapter built with `time_limit` 1 second, raises it with `detail` `no end within 1 s` after at least 1 and less than 25 seconds; an executable `<tmp>/nowhere` raises it with `command` `<tmp>/nowhere --version` and `detail` starting with `[Errno 2]`. `PODMAN_TIME_LIMIT` is 2 minutes, and an adapter built without `time_limit` passes it to `run_process` (read from a recorded request, `run_process` of `factory.adapters.podman_runs` replaced by a `Recorder` of `tests/run_process_recorder.py` for that row).
8. `image_exists()` (rows of one parametrized test): exit 0 returns `True` and the call's arguments are `["image", "exists", "factory-stage:1"]`; exit 1 returns `False`; exit 125 with `Error: cannot connect` raises `ContainerError` with `command` `<stand-in> image exists factory-stage:1` and `detail` `Error: cannot connect`; exit 2 printing nothing raises it with `detail` `exit status 2`; an executable `<tmp>/nowhere` raises it with `command` `<tmp>/nowhere image exists factory-stage:1` and `detail` starting with `[Errno 2]`.
9. `PodmanRuns` is an instance of `ContainerRuns`, and `tests/test_wrapper_search.py` lists `factory.adapters.podman_runs` among the modules that import the process module (decision 18 c).
10. `make check` stays green.
11. docs: `docs/project-guide/stage-environment.md` gains the section *The podman adapter*: the command line word by word and why each word is there (`--rm`, `--userns=keep-id`, `--timeout`, the `:ro` mounts as the protection of the host's repository and login files, the empty environment), the reading of the end (137 or -9 at or after the limit is the time limit; podman's 125), the 30 seconds of grace, `version` and `image_exists` for the preflight, the stand-in the tests use; `docs/project-guide/README.md`, *The files*, names `factory.adapters.podman_runs` for the file. `docs/decisions.md`: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cat > "$d/podman" <<'EOF'
#!/bin/sh
printf '%s\n' "$*" >> "$(dirname "$0")/calls.txt"
case "$1" in
  --version) echo "podman version 4.9.3"; exit 0 ;;
  image) exit 1 ;;
esac
while [ $# -gt 0 ]; do [ "$1" = "factory-stage:1" ] && shift && exec "$@"; shift; done
exit 125
EOF
chmod +x "$d/podman"
uv run python - "$d" <<'EOF'
import sys
from datetime import timedelta
from pathlib import Path

from factory.adapters.podman_runs import PodmanRuns
from factory.domain.containers import Mount

d = Path(sys.argv[1])
podman = PodmanRuns(str(d / "podman"), "factory-stage:1", d)
launch = podman.launch(
    ["/bin/sh", "-c", "echo hi"],
    mounts=[Mount(source=d / "repo.git", target="/upstream", read_only=True)],
    environment={"HOME": "/work/home"},
    time_limit=timedelta(seconds=90),
    working_directory="/work/checkout",
)
print([w.replace(str(d), "D") for w in launch.argv[1:]], launch.env, launch.time_limit)
result = podman.run(["/bin/sh", "-c", "echo out; echo err >&2; exit 3"], mounts=[], environment={}, time_limit=timedelta(seconds=10), working_directory="/work")
print(result.exit_status, result.timed_out, result.output.splitlines())
print(podman.version(), podman.image_exists())
EOF
```
Expect: three lines: `['run', '--rm', '--userns=keep-id', '--timeout', '90', '--env', 'HOME=/work/home', '--volume', 'D:/work', '--volume', 'D/repo.git:/upstream:ro', '--workdir', '/work/checkout', 'factory-stage:1', '/bin/sh', '-c', 'echo hi'] {} 0:02:00`; `3 False ['out', 'err']`; `podman version 4.9.3 False`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: 1. The story contradicts itself on the `env` of the launch and of the `run_process` call. The Interface's first bullet writes `ContainerLaunch(..., env={}, ...)` and then says "`env` is `None`". Criterion 1 and the smoke test's Expect line (`{}`) say `{}`. Feature decision 11 says `PodmanRuns.launch` returns `None`. The same split is in `run`: its bullet says `env` `{}`, but criterion 4 requires the stand-in's recorded environment to hold the test's `FACTORY_PROBE_VARIABLE`, so the environment must be inherited (`None`). Which is it? I would choose `None` for both the launch and the `run_process` call, as decision 11 and criterion 4 say. That means criterion 1 reads `env` `None` and the smoke test's first Expect line prints `None`, not `{}`.

   2. The `cwd` of the `run_process` call in `run` is stated two ways. The Interface and criterion 4 say `/`, and criterion 4 expects the stand-in's working directory to be `/`. Criterion 5's Recorder row says the recorded request's `cwd` is "the workspace". I would choose `/` and change criterion 5 to say so.

   3. After the answers, the smoke test's first Expect line must match the chosen `env`. The pipeline's other checks are fine: the Interface names concrete signatures, the criteria are testable, the layer placement is right, and the story is within scope.
4. 2026-10-24 human: Answers to the intake (F0042-S0003, podman runs start a throwaway container on the dataset):

   1. **`None` for both**, as decision 11 says: the host-side podman inherits the factory's environment. `launch` returns `ContainerLaunch(..., env=None, ...)`, and the `run_process` call in `run` passes `env=None`, which is what criterion 4's inherited `FACTORY_PROBE_VARIABLE` needs. Criterion 1 reads `env` `None`, and the smoke test's first `Expect:` line prints `None`. The Interface's `env={}` and the `run` bullet's `{}` are slips of the draft.
   2. **`/`**: the host-side `cwd` of the `run_process` call is `/`. The working directory inside the container is `--workdir`, not the host's `cwd`. Criterion 5's Recorder row says `/` in place of "the workspace".
   3. Yes: the smoke test's first `Expect:` line follows answer 1.

   Please write these three into the Description, the Interface and the criteria as you accept.
