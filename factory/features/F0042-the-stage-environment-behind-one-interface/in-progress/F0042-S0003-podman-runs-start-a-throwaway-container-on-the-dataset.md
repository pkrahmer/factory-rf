---
stage: review
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 409
comments_read: [6384531243]
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-24T13:33:23.502537Z'
  lease_duration: 60
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
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-24T13:02:12.552916Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-24T13:02:32.993670Z'
  stage: intake
  run: 13a99a69c6e94749b09787a213be7f60
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-24T13:02:53.769459Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-24T13:08:07.889183Z'
  stage: tests
  run: 24c8f5fdfa184b44a8badeced696ba9a
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-24T13:08:29.171103Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-24T13:13:13.210605Z'
  stage: doing
  run: 4f5c520f1348414780b8dba1ca4fca51
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-24T13:13:33.829923Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-24T13:15:10.506647Z'
  stage: review
  run: 1e200897652c40beaf8f7fe163da8969
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-24T13:15:32.011144Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-24T13:17:31.151875Z'
  stage: doing
  run: a3e7e79b7eb746dcbe8ed30e4262ee29
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-24T13:17:51.581655Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-24T13:20:28.010060Z'
  stage: tests
  run: 0a8080cb32b649a18b3b4b06fd0972de
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-24T13:20:49.686645Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-24T13:23:51.363159Z'
  stage: doing
  run: f0bd309f2297448aaada4dd1a8d73604
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-24T13:24:12.105379Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-24T13:25:55.940829Z'
  stage: review
  run: 2f7cf2db68704e7baa59407e68fd4620
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-24T13:26:16.824230Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-10-24T13:26:44.677227Z'
  stage: doing
  run: 30c5ea85a0874d058cf8d79f5494f06e
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-24T13:27:05.222247Z'
  stage: tests
- number: 24
  speaker: tester
  kind: result
  at: '2026-10-24T13:29:44.073440Z'
  stage: tests
  run: 98d83453161b4b3a8885e586bda07ab9
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-24T13:30:05.132096Z'
  stage: doing
- number: 26
  speaker: coder
  kind: result
  at: '2026-10-24T13:33:02.875788Z'
  stage: doing
  run: 63b12331ac7d41e8af254c2174e35c7d
- number: 27
  speaker: factory
  kind: started
  at: '2026-10-24T13:33:23.502537Z'
  stage: review
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

- `launch(command, *, mounts, environment, time_limit, working_directory)` returns `ContainerLaunch(argv=[executable, "run", "--rm", "--userns=keep-id", "--timeout", "<seconds>", "--env", "NAME=value", ..., "--volume", "<workspace>:/work", "--volume", "<source>:<target>", or "<source>:<target>:ro" for a read-only mount, ..., "--workdir", working_directory, image, *command], env=None, time_limit=time_limit + CONTAINER_GRACE)`. `<seconds>` is the time limit in whole seconds, rounded up (`30s` is `30`, 1.5 seconds is `2`). The `--env` pairs come in the order of `environment`; the `/work` volume comes first and the given mounts follow in their order. `env` is `None`: the `podman` program runs with the factory's own environment (`HOME`, `XDG_RUNTIME_DIR`, `PATH` and whatever the service sets for it), as `version()` does; the container gets none of it, since podman passes only the `--env` pairs and the image's own variables in. A mount whose target is `/work` or starts with `/work/`, and an empty `command`, raise `ValueError` (the interface's rule).
- `run(...)` runs `launch(...)` through `run_process` of `factory.adapters.process` with `cwd` `/` (podman reads no file from its working directory; a missing workspace is podman's own fault, status 125, not a start fault), `env` `None`, `time_limit` the launch's (the limit plus the grace) and `merge_stderr` true, and returns `ContainerResult`: `timed_out` is true when `run_process` says so, or when the exit status is in `KILL_STATUSES` of `factory.adapters.agent_launch` (137 or -9; imported, not copied) after at least `time_limit` (podman's `--timeout` sent the kill); then `exit_status` is `None`. Otherwise `exit_status` is podman's, which is the command's (podman exits 125 for its own faults, such as a missing image, and the result then says 125 with podman's message in `output`). `output` is the merged output, `duration` the process's. A `podman` that cannot start (`OSError`) is `ContainerError(command[0], <the operating system's message>)`, `command[0]` the first word of the command asked for, not `podman`. The structural test `tests/test_wrapper_search.py` names the module (decision 18 c of `feature.md`).
- `version()` runs `[executable, "--version"]` through `run_process` (`cwd` `workspace`, `env` `None`, `time_limit` the constructor's, `PODMAN_TIME_LIMIT` of 2 minutes by default, stderr merged) and returns the first non-blank line stripped (`podman version 4.9.3`). A fault is `ContainerError(f"{executable} --version", <detail>)`: an exit status other than 0 has the last non-blank output line as `detail`, or `exit status <n>` when the output has none; a time limit has `no end within <n> s`, `n` the whole seconds of the limit rounded up (`no end within 120 s` by default); exit status 0 without output has `printed nothing`; an executable that cannot be started (`OSError`) has the operating system's message, as `run` does. The preflight's `podman` item (S0011) reads a missing `podman` from this error, never from an `OSError`.
- `image_exists()` runs `[executable, "image", "exists", image]` the same way: exit status 0 is `True`, 1 is `False`, any other status is `ContainerError(f"{executable} image exists {image}", <the last non-blank output line or `exit status <n>`>)`; a time limit and an executable that cannot be started are the same faults as for `version()`, with this command.

Tests (the tester writes them): `tests/adapters/test_podman_runs.py` (the command line) and `tests/adapters/test_podman_runs_results.py` (the results and faults), with a stand-in `podman` written into `tmp_path` by a helper like `write_sudo` of `tests/sudo_support.py`: it records its arguments and its environment to a file, and either prints planned output and exits with a planned status after a planned wait, or, when its arguments hold the image word, runs the words after the image on the host (so that a test can see the command's own exit status and output pass through). No real `podman` is run anywhere.

## Acceptance criteria

1. `PodmanRuns(<stand-in>, "factory-stage:1", Path("/srv/factory/vm/work")).launch(["/bin/sh", "-c", "make sync"], mounts=[Mount(source=Path("/srv/factory/vm/repo/.git"), target="/upstream", read_only=True), Mount(source=Path("/home/factory/.claude-token"), target="/home/factory/.claude-token", read_only=True), Mount(source=Path("/state/runs/instructions-1.md"), target="/state/runs/instructions-1.md")], environment={"HOME": "/work/home", "PATH": "/usr/local/bin:/usr/bin:/bin"}, time_limit=timedelta(minutes=40), working_directory="/work/checkout")` returns `argv` exactly `[<stand-in>, "run", "--rm", "--userns=keep-id", "--timeout", "2400", "--env", "HOME=/work/home", "--env", "PATH=/usr/local/bin:/usr/bin:/bin", "--volume", "/srv/factory/vm/work:/work", "--volume", "/srv/factory/vm/repo/.git:/upstream:ro", "--volume", "/home/factory/.claude-token:/home/factory/.claude-token:ro", "--volume", "/state/runs/instructions-1.md:/state/runs/instructions-1.md", "--workdir", "/work/checkout", "factory-stage:1", "/bin/sh", "-c", "make sync"]`, `env` `None` and `time_limit` 40 minutes and 30 seconds.
2. The seconds of `--timeout` (rows of one parametrized test): 30 seconds gives `30`, 1.5 seconds gives `2`, 40 minutes gives `2400`. With no mounts and no environment the words hold one `--volume` (the workspace) and no `--env`.
3. `launch` and `run` raise `ValueError` for a mount with target `/work`, for one with target `/work/checkout`, and for a `command` of `[]`; a mount with target `/workspace` is accepted (rows of one parametrized test).
4. `run(["/bin/sh", "-c", 'echo out; echo err >&2; exit 3'], mounts=[], environment={}, time_limit=10 s, working_directory="/work")` with a stand-in that runs the words after the image gives `exit_status` 3, `timed_out` false and `output` holding `out` and `err`; the stand-in's recorded environment is the test's (the test sets `FACTORY_PROBE_VARIABLE` with `monkeypatch.setenv` and the record holds it); the stand-in's working directory is `/`.
5. The kill at the limit (rows of one parametrized test): a stand-in that exits 137 after 3 seconds, under `time_limit` 3 seconds, gives `timed_out` true and `exit_status` `None`; a stand-in that exits 137 at once under `time_limit` 30 seconds gives `timed_out` false and `exit_status` 137; a stand-in that exits -9 (kills itself with `SIGKILL`) after 2 seconds under `time_limit` 2 seconds gives `timed_out` true; with `run_process` of `factory.adapters.podman_runs` replaced by a `Recorder` (`tests/run_process_recorder.py`) that answers `ProcessResult(exit_status=None, stdout="", stderr="", timed_out=True, duration=timedelta(seconds=31))`, `run` under `time_limit` 1 second gives `timed_out` true and `exit_status` `None`, and the recorded request's `time_limit` is 31 seconds (the limit plus `CONTAINER_GRACE`), its `merge_stderr` true and its `cwd` `/`.
6. A stand-in that exits 125 at once printing `Error: factory-stage:1: image not known` gives `exit_status` 125, `timed_out` false and that line in `output`. `run(["/bin/true"], ...)` with an executable that does not exist raises `ContainerError` whose `command` is `/bin/true` and whose `detail` starts with `[Errno 2]`.
7. `version()` (rows of one parametrized test): planned to print `podman version 4.9.3` returns it and the call's arguments are `["--version"]`; planned to print nothing and exit 0 raises `ContainerError` with `detail` `printed nothing`; planned to exit 1 with `podman: command not found` raises it with that detail and `command` `<stand-in> --version`; planned to exit 2 printing nothing raises it with `detail` `exit status 2`; a stand-in that sleeps 60 seconds, under an adapter built with `time_limit` 1 second, raises it with `detail` `no end within 1 s` after at least 1 and less than 25 seconds; an executable `<tmp>/nowhere` raises it with `command` `<tmp>/nowhere --version` and `detail` starting with `[Errno 2]`. `PODMAN_TIME_LIMIT` is 2 minutes, and an adapter built without `time_limit` passes it to `run_process` (read from a recorded request, `run_process` of `factory.adapters.podman_runs` replaced by a `Recorder` of `tests/run_process_recorder.py` for that row).
8. `image_exists()` (rows of one parametrized test): exit 0 returns `True` and the call's arguments are `["image", "exists", "factory-stage:1"]`; exit 1 returns `False`; exit 125 with `Error: cannot connect` raises `ContainerError` with `command` `<stand-in> image exists factory-stage:1` and `detail` `Error: cannot connect`; exit 2 printing nothing raises it with `detail` `exit status 2`; an executable `<tmp>/nowhere` raises it with `command` `<tmp>/nowhere image exists factory-stage:1` and `detail` starting with `[Errno 2]`.
9. `PodmanRuns` is an instance of `ContainerRuns`, and `tests/test_wrapper_search.py` lists `factory.adapters.podman_runs` among the modules that import the process module (decision 18 c).
10. An exit status outside `KILL_STATUSES` at or after the limit is the command's, not a time limit (a row of criterion 5's test): with `run_process` of `factory.adapters.podman_runs` replaced by a `Recorder` that answers `ProcessResult(exit_status=1, stdout="", stderr="", timed_out=False, duration=timedelta(seconds=5))`, `run` under `time_limit` 1 second gives `timed_out` false and `exit_status` 1.
11. `version()` and `image_exists()` run with the workspace as their working directory: in the rows of criteria 7 and 8 that read the call's arguments, the stand-in's recorded working directory is the adapter's `workspace`.
12. `image_exists()` reaching its time limit is the fault `version()` gives, with its own command, the seconds rounded up (a row of criterion 8's test): a stand-in that sleeps 60 seconds, under an adapter built with `time_limit` 1.5 seconds, raises `ContainerError` with `command` `<stand-in> image exists factory-stage:1` and `detail` `no end within 2 s`, after at least 1.5 and less than 25 seconds.
13. `make check` stays green.
14. docs: `docs/project-guide/stage-environment.md` gains the section *The podman adapter*: the command line word by word and why each word is there (`--rm`, `--userns=keep-id`, `--timeout`, the `:ro` mounts as the protection of the host's repository and login files, the empty environment), the reading of the end (137 or -9 at or after the limit is the time limit; podman's 125), the 30 seconds of grace, `version` and `image_exists` for the preflight, the stand-in the tests use; `docs/project-guide/README.md`, *The files*, names `factory.adapters.podman_runs` for the file. `docs/decisions.md`: none.

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
Expect: three lines: `['run', '--rm', '--userns=keep-id', '--timeout', '90', '--env', 'HOME=/work/home', '--volume', 'D:/work', '--volume', 'D/repo.git:/upstream:ro', '--workdir', '/work/checkout', 'factory-stage:1', '/bin/sh', '-c', 'echo hi'] None 0:02:00`; `3 False ['out', 'err']`; `podman version 4.9.3 False`

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
5. factory: started intake as self.
6. intake: accepted
   - Interface: `factory.adapters.podman_runs` names `CONTAINER_GRACE`, `PODMAN_TIME_LIMIT`, `PodmanRuns(ContainerRuns)` with the constructor, `version()` and `image_exists()`, and `launch`/`run` with their DTOs. Concrete and in the `adapters` layer. Carried in from the human's answers in journal entry 4: the `launch` bullet and the `run` bullet now say `env=None` and `env` `None` where they said `{}`.
   - Criteria: each is testable by one parametrized test or one function. Every rule has its failing side: the `/work` mount and the empty command raise `ValueError` (3), podman's 125 (6), kill statuses 137 and -9 at and before the limit (5), and the faults of `version` and `image_exists` (7, 8). Carried in from entry 4: criterion 1 now reads `env` `None`, and criterion 5's Recorder row reads `cwd` `/` in place of "the workspace".
   - Smoke test: runnable with a stand-in `podman`; no pytest command, so no `-q` problem. Carried in from entry 4: the first Expect line ends `None 0:02:00` in place of `{} 0:02:00`. The other two Expect lines are checkable against the output.
   - Architecture: an adapter behind the `ContainerRuns` interface, and it reaches processes only through `run_process`. Criterion 9 covers the `test_wrapper_search.py` leave (decision 18 c). Nothing is wired, which fits S0010.
   - Scope: within the feature's scope list and decision 11. Nothing is removed and no new dependency is added.
   - Description: needs no rewrite. It states no `env` value, and entry 4's three answers are in the Interface and criteria.
7. factory: started tests as self.
8. tester: Wrote the tests of `factory.adapters.podman_runs` from the Interface and criteria 1–9. Each test runs against a stand-in `podman` that records its calls. No real podman is run.

   - criterion 1: tests/adapters/test_podman_runs.py::test_launch_pins_the_podman_command_line
   - criterion 2: tests/adapters/test_podman_runs.py::test_timeout_is_the_time_limit_in_whole_seconds_rounded_up (rows 30 s → `30`, 1.5 s → `2`, 40 min → `2400`; each row has no mounts and no environment and checks for one `--volume` (the workspace) and no `--env`)
   - criterion 3: tests/adapters/test_podman_runs.py::test_a_mount_on_the_dataset_or_no_command_is_refused (`launch` and `run` × the targets `/work`, `/work/checkout` and `/workspace`, plus `[]` as the command)
   - criterion 4: tests/adapters/test_podman_runs_results.py::test_a_run_passes_the_command_s_status_and_output_through
   - criterion 5: tests/adapters/test_podman_runs_results.py::test_a_kill_at_the_limit_is_a_timed_out_run (137 at the limit, 137 before it, -9 at the limit, the factory's own kill through a `Recorder` answer). Every row runs through a `Recorder` in place of `podman_runs.run_process`; with no answer queued, the `Recorder` runs the real process. So every row also checks the request: `time_limit` is the limit plus 30 s, `merge_stderr` is true, `cwd` is `/`.
   - criterion 6: tests/adapters/test_podman_runs_results.py::test_podman_s_own_fault_is_its_exit_status and ::test_a_podman_that_cannot_start_is_a_container_error_of_the_command
   - criterion 7: tests/adapters/test_podman_runs_results.py::test_version_is_the_first_line_podman_prints (six rows) and ::test_version_runs_under_two_minutes_by_default (`PODMAN_TIME_LIMIT`, and the default limit read from a `Recorder` request)
   - criterion 8: tests/adapters/test_podman_runs_results.py::test_image_exists_reads_podman_s_exit_status (five rows)
   - criterion 9: tests/adapters/test_podman_runs.py::test_podman_runs_are_container_runs, plus `factory.adapters.podman_runs` added to the expected set in tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module (the story names this test; decision 18 c)

   Files created: tests/podman_support.py (the stand-in `podman`, modelled on `write_sudo`, with plan fields stdout/stderr/wait/exit status, where -9 means it kills itself with SIGKILL; when its arguments contain the image word it runs the words after it), tests/adapters/test_podman_runs.py, tests/adapters/test_podman_runs_results.py.

   Files changed: tests/conftest.py (new fixture `podman`, the stand-in in `tmp_path`) and tests/test_wrapper_search.py (one added module name, as criterion 9 asks).

   In the stand-in, error messages go to stderr so that the merged output is exercised. I did not test the Interface's `cwd` of `version()`, because no criterion names it.

   `make test` result: the test runner could not import `factory.adapters.podman_runs`, so both new modules fail at collection. `test_wrapper_search` fails until the module exists. All three are red on purpose. `make lint`: green. I set no skill or step aside.

   `lint`: lint: green (0.6 s)
   `test`: ERROR tests/adapters/test_podman_runs_results.py - ImportError while importing test module '/work/checkout/tests/adapters/test_podman_runs_results.py'.
9. factory: started doing as self.
10. coder: I added `PodmanRuns`, the first real implementation of `ContainerRuns`. `make test` and `make check` are both green, and I changed no test.

    What I built:
    - `src/factory/adapters/podman_runs.py` (new): `CONTAINER_GRACE`, `PODMAN_TIME_LIMIT` and `PodmanRuns`, with `launch`, `run`, `version` and `image_exists`.
      - `launch` builds the `podman run` words in the order the Interface gives. It returns `env=None` and the time limit plus the grace.
      - `run` calls `run_process` with `cwd` `/`, `env` `None` and stderr merged. It counts the run as timed out in two cases: `run_process` says it timed out, or the exit status is in `KILL_STATUSES` (imported from `agent_launch`) after at least the time limit asked for. When `podman` cannot start, the `OSError` becomes `ContainerError(command[0], ...)`.
      - `version` and `image_exists` share a private `_query`: `cwd` is the workspace and the time limit is the one given to the constructor.
      - The check that refuses a `/work` mount reuses `beneath_or_at` and the `WORK` constant, as `FakeContainerRuns` does.
    - `src/factory/adapters/printed_output.py` (new): `printed_lines`, `first_printed_line`, `failure_detail(output, exit_status)` and `no_end_detail(time_limit)`. These were private helpers in `zfs_snapshots.py`, and podman's fault details needed the same ones. The module works on strings only, so it does not import `factory.adapters.process` and stays out of the list in `tests/test_wrapper_search.py`.
    - `src/factory/adapters/zfs_snapshots.py`: its private copies are gone and it uses the shared helpers. Its behaviour is unchanged and the zfs tests still pass.

    Main choice: I moved zfs's line helpers to one shared adapter module rather than copying them into `podman_runs.py`, because the reviewer counts a copy as a finding. The alternative I rejected was having `failure_detail` take a `ProcessResult`, as zfs's version did. That would have made the shared module import the process module, and the wrapper-search test would fail.

    Refactor pass: after `make check` was green I read the diff; nothing needed changing beyond what is described above.

    Noticed but did not touch:
    - `agent_launch._limit_argument` also rounds a time limit up to whole seconds (with an `s` suffix). `podman_runs` uses `math.ceil` inline for `--timeout`. I left both alone.
    - I could not run the smoke test: the command was not permitted in this session. The tests check every value in its three Expect lines through the same stand-in behaviour, but the work item's script itself has not run.

    The journal changed nothing that needs the Description rewritten: entry 4's answers (`env` `None`, `cwd` `/`) were already written into the Interface and criteria at intake.

    `check`: check: green
    `duplicates`: duplicates: 12 new, 38 known, 0 gone
11. factory: started review as self.
12. reviewer: 1. `src/factory/adapters/podman_runs.py:31-36` (`_check`): this is a copy of the empty-command and `/work`-mount checks in `FakeContainerRuns._accept`, `src/factory/adapters/fake_containers.py:81-85`. The two have the same messages, and `make duplicates` reports the pair as new similar code. Fix: move the check into one shared function that both adapters call, for example beside `WORK` in `factory.domain.containers` or in a small adapters module. Behaviour stays the same; the tests of criterion 3 and the fake's tests pin it.
    2. Gap in the story, now criterion 10, which needs its test. The rule "an exit status in `KILL_STATUSES` after at least `time_limit` counts as timed out" (`podman_runs.py:45-46`, Interface `run` bullet) has no test for a non-kill status at or after the limit. Every non-kill row ends at once: criteria 4 and 6. So if `result.exit_status in KILL_STATUSES` were dropped from `_killed_at_limit`, every test would still pass. Fix: the tester adds the criterion-10 row (a `Recorder` answer with exit 1 and a 5 s duration under a 1 s limit) to `tests/adapters/test_podman_runs_results.py::test_a_kill_at_the_limit_is_a_timed_out_run`.
    3. Criterion 11 added; it needs its test. The Interface says `version()` and `image_exists()` run with `cwd` the workspace (`podman_runs.py:163-166`), but no criterion or test pins it; the tester's entry 8 says so. Fix: in the success rows of `test_version_is_the_first_line_podman_prints` and `test_image_exists_reads_podman_s_exit_status`, assert that the recorded `working_directory` is the `workspace` fixture.

    The old closing criteria 10 and 11 are renumbered 12 and 13.

    Checked and fine: criteria 1–9 each have a test that checks what the criterion says. The boundary of 137 is tested at and before the limit. `KILL_STATUSES` is imported, not copied. The zfs helpers moved to `factory.adapters.printed_output` without a change in behaviour. The layers hold. There are no markers, secrets or shell strings. The coder's `make check` was green (entry 10). Of the other new `make duplicates` findings, the ones for `PodmanRuns` and `image_exists` are dead code only until the wiring story, S0010. The similar `_query` in podman and `_run` in zfs raise different error types, and I did not count them.

    Earlier tests:
    - tests/conftest.py: none needed (it only adds the `podman` fixture and its import).
    - tests/test_wrapper_search.py: the human's leave through the story (Interface `run` bullet and criterion 9, decision 18 c), one module name added.
13. factory: started doing as self.
14. coder: Round 1. I fixed reviewer finding 1 in the code. Findings 2 and 3 add criteria 10 and 11, which need only their tests, so I am handing over to the tester.

    Built (finding 1):
    - `src/factory/domain/containers.py`: new `check_container_call(command, mounts)`, placed beside `WORK`. It refuses an empty command and a mount whose target is at or under `/work`, using `beneath_or_at` of `factory.domain.agent_home`. The messages are the same as before.
    - `src/factory/adapters/podman_runs.py`: the private `_check` is gone; `launch` calls `check_container_call`.
    - `src/factory/adapters/fake_containers.py`: `_accept` calls `check_container_call` instead of its own copy of the checks.
    - Behaviour is unchanged and no test was touched. `make check` is green (`test: green (63.9 s)`, `check: green`). `make duplicates` now reports 11 new findings (12 before): the similar-code pair the reviewer named is gone.

    Main choice: I put the check in the domain, beside `WORK` and the `Mount` model it validates. It is a pure rule, and both adapters can import it there. The alternative I rejected was a small shared module under `factory.adapters`: the rule needs no I/O, so the domain is where it belongs.

    For the tester:
    - Criterion 10: add the row to `tests/adapters/test_podman_runs_results.py::test_a_kill_at_the_limit_is_a_timed_out_run`. A `Recorder` answers `ProcessResult(exit_status=1, stdout="", stderr="", timed_out=False, duration=timedelta(seconds=5))`; under `time_limit` 1 s the result is `timed_out` false and `exit_status` 1.
    - Criterion 11: in the success rows of `test_version_is_the_first_line_podman_prints` and `test_image_exists_reads_podman_s_exit_status`, assert that the stand-in's recorded working directory is the adapter's `workspace`.
    - The code already does both: `_killed_at_limit` checks `KILL_STATUSES`, and `_query` passes `cwd` the workspace.

    Refactor pass: I read the diff; nothing more needed changing.

    Noticed but did not touch: `make duplicates` lists `WORK_HOME` in `src/factory/domain/containers.py` as unused (vulture, 60 % confidence). This change did not cause it; the constant was already there. The journal changed nothing that calls for a rewrite of the Description: the reviewer had already written criteria 10 and 11 into it.
15. factory: started tests as self.
16. tester: Round 1. I wrote the tests for criteria 10 and 11, which the reviewer added and the coder's entry 14 handed over. They are already green, because the coder's code does both things. No test is red.

    - criterion 10: tests/adapters/test_podman_runs_results.py::test_a_kill_at_the_limit_is_a_timed_out_run. I added one row, `other-status-after-the-limit`. A `Recorder` answers `ProcessResult(exit_status=1, stdout="", stderr="", timed_out=False, duration=timedelta(seconds=5))`, and `run` under `time_limit` 1 s gives `timed_out` false and `exit_status` 1. The row also runs the test's existing request checks: limit plus 30 s, `merge_stderr` true, `cwd` `/`.
    - criterion 11: tests/adapters/test_podman_runs_results.py::test_version_is_the_first_line_podman_prints and ::test_image_exists_reads_podman_s_exit_status. Criterion 11 names the rows that read the call's arguments: `version` for the first test and `exists` for the second. In those rows the stand-in's recorded `working_directory` now equals the `workspace` fixture.

    Files changed: tests/adapters/test_podman_runs_results.py, a test module I wrote at this story's first tests stage. No files created, and no earlier test of another story changed. The test runner could import every module.

    `make test`: green (63.0 s). `make lint`: green. I set no skill or step aside.

    `lint`: lint: green (0.5 s)
    `test`: test: green (63.4 s)
17. factory: started doing as self.
18. coder: Round 1, second doing run. The tester's entry 16 added the tests for criteria 10 and 11 (in `tests/adapters/test_podman_runs_results.py`), and they pass against the code already in the tree. So nothing was left to build this run, and I changed no code and no test. Reviewer finding 1 (the duplicated call check) was fixed in entry 14 through `check_container_call` in `src/factory/domain/containers.py`. Findings 2 and 3 are now covered by the tester's rows.

    What the story built, unchanged in this run:
    - `src/factory/adapters/podman_runs.py` (new): `CONTAINER_GRACE`, `PODMAN_TIME_LIMIT` and `PodmanRuns`.
    - `src/factory/adapters/printed_output.py` (new): line helpers moved out of `zfs_snapshots.py`.
    - `src/factory/adapters/zfs_snapshots.py` now uses those shared helpers.
    - `src/factory/domain/containers.py` gains `check_container_call`.
    - `src/factory/adapters/fake_containers.py` now calls `check_container_call` instead of its own copy.

    Main choice (from entry 14): the shared call check lives in the domain, beside `WORK` and `Mount`, because it is a pure rule. I rejected a small shared module under `factory.adapters`.

    The branch has `origin/main` merged in (`269274f4`). `make check` is green on the merged tree: `test: green (63.7 s)`, `check: green`, coverage 99.17 %.

    Refactor pass: I reread `podman_runs.py` and the diff against `main`. Nothing needed changing.

    Noticed but did not touch:
    - `agent_launch._limit_argument` also rounds a limit up to whole seconds, as `podman_runs` does with `math.ceil` inline.
    - vulture reports `WORK_HOME` in `domain/containers.py` as unused. It predates this story.
    - The work item's smoke test has still not been run by the coder; it was not permitted in the first run, and I did not try it again here.

    The journal changed nothing that needs a Description rewrite: criteria 10 and 11 are already in it.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 38 known, 0 gone
19. factory: started review as self.
20. reviewer: 1. Criterion 12 added: it needs its test. Location: the Interface's `image_exists()` bullet ("a time limit and an executable that cannot be started are the same faults as for `version()`, with this command"), code in `src/factory/adapters/podman_runs.py` (`_query`, the `no_end_detail` raise). Problem: this rule's failing side has no test. `tests/adapters/test_podman_runs_results.py::test_image_exists_reads_podman_s_exit_status` covers "cannot start" but has no row for the time limit. The podman rows also never check that the fraction in the detail is rounded up (the `version()` row uses a whole 1 s). Criterion 8 left this out, so the gap is in the story, not in the tester's work. Fix: the tester adds one row to that parametrized test. A stand-in sleeps 60 s under an adapter built with `time_limit` 1.5 s. Expect `ContainerError` with command `<stand-in> image exists factory-stage:1` and detail `no end within 2 s`, after at least 1.5 s and under `ROOMY_BOUND_SECONDS`. The code already does this, so nothing under `src/` changes. The old closing criteria 12 and 13 are now 13 and 14.

    Checked and fine:
    - Criteria 1–11 each have a test that checks what the criterion says:
      - argv pinned word for word, with `env` `None` and the limit plus 30 s.
      - `--timeout` rounding with 30 s, 1.5 s and 40 min as rows.
      - `/work` and `/work/checkout` are refused and `/workspace` is accepted, for both `launch` and `run`.
      - The 137 kill is tested at the limit and before it; -9 at the limit; a non-kill status after the limit (criterion 10).
      - The recorded request has `cwd` `/`, `merge_stderr` true and the limit plus the grace.
      - `version` and `image_exists` run with the workspace as their working directory (criterion 11).
    - The factory's `make check` after the coder was green (entry 18).
    - Round-0 finding 1 is fixed. `check_container_call` in `src/factory/domain/containers.py` is a pure rule in the domain, and `fake_containers.py` and `podman_runs.py` both call it.
    - The zfs line helpers moved to `factory.adapters.printed_output`, which has no process import, and zfs behaves the same.
    - `KILL_STATUSES` is imported, not copied.
    - The layers hold. There are no markers, secrets or shell strings.
    - `make duplicates` reports 11 new findings, and none needs a fix here:
      - the dead `PodmanRuns` and `image_exists` stay unused until S0010 wires them;
      - two similar-code pairs are each a `ProcessRequest` built and its `OSError` mapped, but to different error types, which round 0 also did not count;
      - the rest predate the story.

    Earlier tests:
    - tests/conftest.py: none needed. The diff only adds the `podman` fixture and its import.
    - tests/test_wrapper_search.py: the human's leave through the story (the Interface's `run` bullet and criterion 9, decision 18 c), for one added module name.

    Notes:
    - tests/adapters/test_podman_runs_results.py:44-48: the module's own `recorder` fixture shadows the one in `tests/conftest.py:312-316`, with the same body for a different module. A shared fixture that takes the module to patch would remove the copy.
21. factory: started doing as self.
22. coder: Round 2. The reviewer's entry 20 adds criterion 12, and only a test is missing for it, so I'm handing over to the tester. I changed no code and no test.

    For the tester:
    - Criterion 12: add one row to `tests/adapters/test_podman_runs_results.py::test_image_exists_reads_podman_s_exit_status`.
      - Setup: a stand-in that sleeps 60 s, under an adapter built with `time_limit` 1.5 s.
      - Expected: `ContainerError` with `command` `<stand-in> image exists factory-stage:1` and `detail` `no end within 2 s`, after at least 1.5 s and under `ROOMY_BOUND_SECONDS`.
    - The new row is not in the test module yet. Its only `no end within` row is the `version()` row with 1 s.

    The code already does this, so I expect the row to pass at once:
    - In `src/factory/adapters/podman_runs.py`, `_query` (shared by `version` and `image_exists`) raises `ContainerError(self._command(arguments), no_end_detail(self._time_limit))` when the limit is reached.
    - `no_end_detail` in `src/factory/adapters/printed_output.py` rounds up with `math.ceil`, so 1.5 s gives `2`.

    What the story built is unchanged since entry 18: `src/factory/adapters/podman_runs.py`, `src/factory/adapters/printed_output.py`, `src/factory/adapters/zfs_snapshots.py` (uses the shared helpers), and `check_container_call` in `src/factory/domain/containers.py`, which `fake_containers.py` and `podman_runs.py` both call. The main choice is still the one from entry 14: the shared call check lives in the domain, not in a shared adapters module. With no code change in this run there was nothing to refactor, and I did not run `make check` again; the last green run is the one in entry 18, on the same code.

    Noticed but did not touch:
    - In the reviewer's note, the `recorder` fixture in `tests/adapters/test_podman_runs_results.py:44-48` repeats the one in `tests/conftest.py:312-316` for a different module. Under the standing leave the tester may move it to one shared fixture; the coder may not.
    - `agent_launch._limit_argument` and `podman_runs`' `--timeout` both round a limit up to whole seconds.
    - vulture reports `WORK_HOME` in `domain/containers.py` as unused. It predates this story.
    - No one has run the work item's smoke test yet.

    The journal changed nothing that calls for a Description rewrite: the reviewer already wrote criterion 12 into it.
23. factory: started tests as self.
24. tester: Round 2: I made the test change approved in the coder's entry 22, for criterion 12 (added by the reviewer in entry 20). This is a test-only change.

    Criterion 12: tests/adapters/test_podman_runs_results.py::test_image_exists_reads_podman_s_exit_status, new row `time-limit`.

    What changed, all in `tests/adapters/test_podman_runs_results.py` (no new files):
    - The new row uses a stand-in planned with `wait_seconds=60`, under an adapter built with `time_limit` 1.5 s.
    - It expects `ContainerError` with command `<stand-in> image exists factory-stage:1` and detail `no end within 2 s`.
    - The test now times every row, as `test_version_is_the_first_line_podman_prints` already does: `row.at_least_seconds <= elapsed < ROOMY_BOUND_SECONDS`. The new row sets `at_least_seconds=1.5`. `ROOMY_BOUND_SECONDS` is 25, which matches the criterion's "less than 25 seconds". The earlier rows keep the default `at_least_seconds` of 0, so all they gain is the upper bound.

    Results:
    - `make test`: green (65.0 s), coverage 99.17 %. The row passed at once, as the coder expected, because the code already did this.
    - `make lint`: green.
    - Every module imported; nothing failed to import.

    Not done: the reviewer's note about the duplicated `recorder` fixture. This mode allows only the named change, and nothing named that move. I set no skill aside.

    `lint`: lint: green (0.5 s)
    `test`: test: green (61.5 s)
25. factory: started doing as self.
26. coder: Round 2, after the tester's entry 24. The tester added the `time-limit` row for criterion 12 to `tests/adapters/test_podman_runs_results.py::test_image_exists_reads_podman_s_exit_status`. It passes against the code already in the tree, so this run changed no code and no test.

    What the story built, unchanged since entry 18:
    - `src/factory/adapters/podman_runs.py` (new): `CONTAINER_GRACE`, `PODMAN_TIME_LIMIT` and `PodmanRuns` (`launch`, `run`, `version`, `image_exists`).
      - `version` and `image_exists` share `_query`.
      - When `_query` reaches its time limit it raises `ContainerError(<command>, no_end_detail(time_limit))`, and `no_end_detail` rounds up, so 1.5 s gives `no end within 2 s`.
    - `src/factory/adapters/printed_output.py` (new): the line helpers, moved out of `zfs_snapshots.py`.
    - `src/factory/adapters/zfs_snapshots.py`: now uses those shared helpers.
    - `src/factory/domain/containers.py`: `check_container_call`, which both `fake_containers.py` and `podman_runs.py` call.

    Main choice (entry 14): the shared call check is a pure rule, so it lives in the domain beside `WORK` and `Mount`. I rejected a shared module under `factory.adapters`.

    Refactor pass: I reread `podman_runs.py`. Nothing needed changing.

    `make check` is green on this tree: `test: green (62.0 s)`, coverage 99.17 %, `check: green`.

    Noticed but did not touch:
    - The reviewer's note on the `recorder` fixture: `tests/adapters/test_podman_runs_results.py:44-48` repeats `tests/conftest.py:312-316` for a different module. The tester may move it under the standing leave; the coder may not.
    - `agent_launch._limit_argument` and the `--timeout` of `podman_runs` both round a limit up to whole seconds.
    - vulture reports `WORK_HOME` in `domain/containers.py` as unused. That predates this story.
    - No one has run the work item's smoke test yet.

    The journal changed nothing that calls for a Description rewrite: criterion 12 is already in it.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 38 known, 0 gone
27. factory: started review as self.
