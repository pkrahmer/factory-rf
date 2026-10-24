---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 417
comments_read: [6388142770]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T18:46:54.534148Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T18:46:54.540080Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-24T18:47:20.323443Z'
  stage: intake
  run: 839f3930045745b3a7e36f268f070e5c
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-24T18:49:40.760480Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-24T18:49:58.659027Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-24T18:50:20.685252Z'
  stage: intake
  run: 0b59bccede91402db1d836f71031781c
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-24T18:50:42.109531Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-24T18:56:56.806381Z'
  stage: tests
  run: 7c61b85e5b5f4dc8b07a32b94e40dab4
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-24T18:57:17.441777Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-24T19:05:29.875911Z'
  stage: doing
  run: 4f0f338ead6c4b8393e7d388f9feaff3
---

# The agent runtimes start their process in a container

## Description

Step 5 of the cycle (`planning/v1.2-plan.md`, "The cycle of a stage"): the agent's container runs today's chain minus `sudo`, `env -i` and `factory-confine`: the stage image, `/work` mounted, the login file mounted read-only, the request's allow-list environment as `--env` entries, the instructions file mounted read-only, `HOME=/work/home`, `--timeout` as the time limit, `--rm`. The two runtimes, `ClaudeCodeRuntime` and `OpencodeRuntime`, are not duplicated: each gets an optional `ContainerRuns`, and when it has one, every call's words come from `ContainerRuns.launch` instead of the `sudo` chain of the shared launch module, at the same place (`run_launch`). The call's files (the instructions file, opencode's configuration file) and the login files are mounted read-only at their own paths, so the words of the call do not change; the working directory inside the container is `/work/checkout`; a container ended by `--timeout` (exit status 137 or -9 at or after the limit) is read as `time_limit`, as the agent's own `timeout` under `sudo` is read today. No rules file, no temporary folder, no leftovers program and no `CLAUDE_CONFIG_DIR` in a container: those belong to the layers the container replaces. `version()` runs `<executable> --version` in a container too, so the preflight's `agent-runtime-version` reads the stage image's runtime. The runtimes are tested on `FakeContainerRuns` with the stand-in `claude` and `opencode` of the existing tests on the `PATH`; the wiring that gives a `container` instance's runtimes their `PodmanRuns` is S0010's. What stays: a runtime without a container behaves exactly as today, and every existing runtime test is unchanged.

## Interface

`factory.adapters.agent_launch` (`adapters`):

```python
def container_launch(
    containers: ContainerRuns,
    argv: Sequence[str],
    environment: Mapping[str, str],
    *,
    files: Sequence[Path],
    time_limit: timedelta,
) -> Launch:
    """`argv` with `environment` in a container; `files` mounted read-only at their own paths."""


def login_paths(files: LoginFiles) -> list[Path]:
    """The login files that are set, the subscription file first."""


def version_launch(
    executable: str, *, containers: ContainerRuns | None, time_limit: timedelta
) -> Launch:
    """The call of `<executable> --version`, on the host or in a container."""


def killed_at_limit(
    *,
    os_user: str | None,
    exit_status: int | None,
    duration: timedelta,
    time_limit: timedelta,
    in_container: bool = False,
) -> bool: ...


def read_call_end(
    end: CallEnd,
    *,
    time_limit: timedelta,
    os_user: str | None,
    starters: Starters,
    in_container: bool = False,
) -> bool: ...
```

- `container_launch` is `containers.launch(argv, mounts=[Mount(source=f, target=str(f), read_only=True) for f in files], environment=environment, time_limit=time_limit, working_directory=WORK_CHECKOUT)` turned into `Launch(argv=<its argv>, env=<its env>, time_limit=<its time_limit>)`; the files in the order given, each once. It raises what `launch` raises.
- `killed_at_limit` and `read_call_end` with `in_container` true judge the kill as they do for a call with an `os_user`: exit status 137 or -9 after at least `time_limit` is the time limit; before it, it is not. With `in_container` false (the default) nothing changes, so every existing caller and test is unchanged. The `sudo:` and `factory-confine:` refusals are not read for a container call (`os_user` is `None` and the confine executable too).
- `agent_launch` still does not import the process module.
- `Launch.env` becomes `dict[str, str] | None` (decision 11 of `feature.md`): `None` is the process's own environment, as `ProcessRequest.env` reads it, and is what `PodmanRuns.launch` gives; `container_launch` passes the `ContainerLaunch`'s `env` through as it is. Every existing caller passes a dict and is unchanged.
- `login_paths` is `[subscription, api]` with the unset ones left out; both runtimes mount `[*login_paths(files), <the call's file>]`.
- `version_launch` is `Launch(argv=[executable, "--version"], env=None, time_limit=time_limit)` without `containers` (today's call: the process's own environment) and `container_launch(containers, [executable, "--version"], {}, files=[], time_limit=time_limit)` with them; both runtimes' `version()` start it through `run_process` with `cwd` the current directory and read the first word as today.

`factory.adapters.claude_runtime.ClaudeCodeRuntime` and `factory.adapters.opencode_runtime.OpencodeRuntime` (`adapters`): the constructors gain the keyword `containers: ContainerRuns | None = None`.

- A runtime built with `containers` and a `confine_executable` raises `ValueError` at construction: a container run is not confined by the kernel. Built with `containers` alone, it stores them; `containers` is a read-only property returning what was given (`None` by default).
- With `containers`, `run(request)`: a request whose `os_user` is set raises `AgentRuntimeError("a run in a container has no operating-system user")` before any file is written or call made. Otherwise the run's files are written as today into the state directory (the instructions file for Claude Code, the configuration file for opencode; no rules file, as without a confine executable), and each call's process request is `container_launch(containers, <the login shell words and the runtime's words, as today>, {**without_login(request.environment), **<the runtime's switches>}, files=[<the login files that are set, in the order subscription then API>, <the call's file>], time_limit=<the call's time limit>)` with `cwd` `request.working_directory`; `--workdir` inside is `/work/checkout` (through `container_launch`). The runtime's switches are Claude Code's `SWITCHES` (no `CLAUDE_CONFIG_DIR`: that is set only with a confine executable, as today) and opencode's `SWITCHES` with `OPENCODE_CONFIG` naming its configuration file at its own path. No leftovers program runs (no `os_user`), no temporary folder is removed (none was made).
- The end of a call in a container is read with `in_container=True`: a call that ends with exit status 137 or -9 at or after its time limit is `time_limit`, not resumed, its measures unknown; before the limit it is `died`. A call that completes is read exactly as today (the JSON reply, the events, the login line `factory-login-used:` from the mounted login files).
- `version()` with `containers` runs `version_launch(executable, containers=containers, time_limit=<the version time limit>)` through `run_process` with `cwd` the current directory and reads the first word as today.
- Without `containers` every behaviour is as today.

Tests (the tester writes them): `tests/adapters/test_claude_runtime_container.py` and `tests/adapters/test_opencode_runtime_container.py`, each with a `FakeContainerRuns(workspace)` on `tmp_path` whose folders `<workspace>/checkout` and `<workspace>/home` the test makes (the fake's shell enters the mapped working directory before the command, so without `checkout/` every call, `version()` included, ends with `cd: can't cd to ...`), the stand-ins `write_stand_in` of `tests/adapters/claude_stand_in.py` and of `tests/adapters/opencode_stand_in.py` on the request's `PATH`, the request's `working_directory` an existing folder under `tmp_path`, `HOME` `/work/home` (which the fake maps to `<workspace>/home`); `tests/adapters/test_agent_launch_container.py` for `container_launch`, `killed_at_limit` and `read_call_end` with `in_container`. The existing runtime and launch tests are unchanged.

## Acceptance criteria

1. `container_launch(fake, ["/bin/sh", "-c", "x"], {"HOME": "/work/home"}, files=[Path("/state/runs/instructions-1.md"), Path("/home/factory/.claude-token")], time_limit=timedelta(minutes=2))` returns a `Launch` whose `argv`, `env` and `time_limit` are the fake's `ContainerLaunch` fields, and the fake's recorded call has the mounts `[Mount(source=Path("/state/runs/instructions-1.md"), target="/state/runs/instructions-1.md", read_only=True), Mount(source=Path("/home/factory/.claude-token"), target="/home/factory/.claude-token", read_only=True)]`, the working directory `/work/checkout`, the environment and the time limit as given. `container_launch(fake, ["x"], {}, files=[Path("/work/x")], time_limit=timedelta(seconds=1))` raises `ValueError` (the fake's refusal of a target under `/work`) and the fake recorded no call. `Launch(argv=["/bin/true"], env=None, time_limit=timedelta(seconds=1))` is accepted with `env` `None`, and `container_launch` on a `ContainerRuns` of the test (a subclass of `FakeContainerRuns` whose `launch` returns the fake's `ContainerLaunch` with `env=None`) returns a `Launch` whose `env` is `None` (rows of one parametrized test).
2. `killed_at_limit` (rows of one parametrized test): `in_container=True`, exit 137, duration 61 s, limit 60 s is `True`; `in_container=True`, exit -9, duration 60 s, limit 60 s is `True`; `in_container=True`, exit 137, duration 59 s is `False`; `in_container=True`, exit 1, duration 61 s is `False`; `in_container=False`, `os_user=None`, exit 137, duration 61 s is `False` (today's rule); `read_call_end` with `in_container=True` and an end of exit 137 after the limit returns `True` and raises nothing, even when `stderr` holds a `sudo:` line.
3. `ClaudeCodeRuntime(<stand-in>, state, containers=fake, confine_executable="factory-confine")` raises `ValueError`; `ClaudeCodeRuntime(<stand-in>, state, containers=fake).containers is fake`; without the keyword `containers` is `None` (rows of one parametrized test; the same three rows for `OpencodeRuntime`).
4. A Claude Code run in a container: the stand-in `claude` on the request's `PATH` prints a completed reply; `run(request)` returns a completed result with the decision and entry, the fake's recorded call has the command `[<login shell words when a login file is set>, <stand-in>, "-p", ...]` with the instructions file's path among the words, the mounts `[<the login file>, <the instructions file>]` read-only at their own paths, the environment the request's less the logins plus `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` and `PYTHONDONTWRITEBYTECODE=1` and without `CLAUDE_CONFIG_DIR`, the time limit the request's, the working directory `/work/checkout`; the stand-in's recorded working directory is `<workspace>/checkout` and its `HOME` is `<workspace>/home`; no rules file was written into the state directory and the instructions file is removed after the run. A second row with both `login_file` and `api_login_file` set has the mounts `[<the token file>, <the API file>, <the instructions file>]` in that order (the Interface's order, subscription then API). In both rows the token file's text stands in no word of the recorded command and in no value of its environment (decision 16). One more row: a run with a login file set returns the login the stand-in's shell reports (`factory-login-used:`) from the mounted file.
5. An opencode run in a container: the same with the stand-in `opencode`, the mounts `[<the API login file when set>, <the configuration file>]`, the environment holding `OPENCODE_CONFIG=<the configuration file's path>` and `PYTHONDONTWRITEBYTECODE=1`, the configuration file removed after the run. One more row: a run with the API login file set returns the login the stand-in's shell reports (`factory-login-used:`) from the mounted file.
6. A request with `os_user="agent"` on a runtime with containers raises `AgentRuntimeError` whose `detail` is `a run in a container has no operating-system user`, and the fake recorded no call and the state directory holds no run file (rows for both runtimes).
7. The kill at the limit (rows of one parametrized test, both runtimes): a stand-in that exits 137 after 3 seconds under a request with `time_limit` 3 seconds gives `end_reason` `time_limit` with `cost_usd`, `turns` and `tokens` `None`, and the fake made exactly one call (no resume); a stand-in that exits 137 at once under `time_limit` 30 seconds gives `died`. The reading of podman's kill, which the fake cannot play (it adds no grace, so the factory's own kill fires at the limit too): with the call answered by a recorded `ProcessResult(exit_status=137, stdout=<a completed reply, or the events of one step for opencode>, stderr="", timed_out=False, duration=<d>)`, `d` of 30 seconds under `time_limit` 30 seconds gives `time_limit` and 29.9 seconds gives `died` (rows for both runtimes: the `recorder` fixture for Claude Code; for opencode `run_streaming` of `factory.adapters.opencode_runtime` replaced with `monkeypatch` by a function of the test that keeps the request and answers that result).
8. A Claude Code budget stop in a container is resumed as today: the stand-in's first reply has the budget subtype, the second completes; the fake recorded two calls, the second's command holding `--resume` and the same mounts.
9. `version()` with containers: the fake's recorded call has the command `[<stand-in>, "--version"]`, no mounts, an empty environment, the working directory `/work/checkout` and the version time limit (the runtime's constructor argument `version_time_limit`, default `factory.adapters.agent_launch.VERSION_TIME_LIMIT`: a row builds the runtime with its own `version_time_limit` and asserts the recorded call has exactly that limit, and one row with the default compares against `VERSION_TIME_LIMIT` by name); the return value is the stand-in's first word (rows for both runtimes). One more row pins `version_launch("claude", containers=None, time_limit=timedelta(seconds=30)) == Launch(argv=["claude", "--version"], env=None, time_limit=timedelta(seconds=30))`.
10. Without `containers`, `run` and `version` behave as today: `tests/adapters/test_claude_runtime*.py`, `test_opencode_*.py` and `test_agent_launch*.py` are unchanged and green, and one row of the new modules runs the same completed request through a runtime without containers and sees the stand-in's recorded working directory equal to the request's `working_directory`.
11. A runtime built with a `leftovers` program and `containers` never starts it: a stand-in `leftovers` that writes a record file leaves the record absent after a run; and no temporary folder is made or removed for a call in a container (rows for both runtimes).
12. `make check` stays green.
13. docs: `docs/project-guide/agents.md`, *The agent runtime* and *The shared launch module*: the `containers` keyword, `container_launch` beside `launch`, what a call in a container gets (the mounts, the environment, `/work/checkout`, `HOME`), what it does not (no `sudo`, no `factory-confine`, no rules file, no leftovers, no temporary folder, no `CLAUDE_CONFIG_DIR`), the reading of `--timeout`'s kill through `in_container`, `version` in the container, the `ValueError` and the `AgentRuntimeError`; `docs/project-guide/stage-environment.md` gains the section *The agent's container* (one paragraph pointing to `agents.md` and naming step 5 of the cycle); `docs/operator-guide.md`, *The agent runtime*: one paragraph on what the chain is on a `container` instance (`podman run ... <image> /bin/sh -c <login shell> ... claude -p ...`), with the `:ro` mounts of the login and instructions files, pointing to the stage image of F0043. `docs/decisions.md`: none.

## Smoke test

```bash
uv run pytest tests/adapters/test_claude_runtime_container.py tests/adapters/test_opencode_runtime_container.py tests/adapters/test_agent_launch_container.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/work/checkout" "$d/state"
uv run python - "$d" <<'EOF'
import sys
from datetime import timedelta
from pathlib import Path

from factory.adapters.agent_launch import container_launch, killed_at_limit
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_containers import FakeContainerRuns

d = Path(sys.argv[1])
fake = FakeContainerRuns(d / "work")
started = container_launch(fake, ["/bin/sh", "-c", 'pwd; echo "$HOME"'], {"HOME": "/work/home"}, files=[d / "state" / "instructions-1.md"], time_limit=timedelta(seconds=5))
print(started.argv[4].replace(str(d), "D"), {name: value.replace(str(d), "D") for name, value in (started.env or {}).items()}, fake.calls[0].mounts[0].read_only, fake.calls[0].working_directory)
print(killed_at_limit(os_user=None, exit_status=137, duration=timedelta(seconds=61), time_limit=timedelta(seconds=60), in_container=True), killed_at_limit(os_user=None, exit_status=137, duration=timedelta(seconds=61), time_limit=timedelta(seconds=60)))
try:
    ClaudeCodeRuntime("claude", d / "state", containers=fake, confine_executable="factory-confine")
except ValueError:
    print("refused", ClaudeCodeRuntime("claude", d / "state", containers=fake).containers is fake)
EOF
```
Expect: three lines, `D/work/checkout {'HOME': 'D/work/home'} True /work/checkout`, `True False`, `refused True`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: Questions (format check: passed; no findings from it). I checked the Interface, the criteria, the smoke test, the architecture and the scope. The Interface, architecture, scope and smoke test are fine. The criteria have gaps:

   1. The Interface says a call that completes in a container is read "exactly as today (the JSON reply, the events, the login line `factory-login-used:` from the mounted login files)". No criterion tests the login line in a container. Criteria 4 and 5 check the result, the command, the mounts and the environment, but not that the login line is read from the mounted login files. Should I add a criterion to criterion 4, and the same for opencode in criterion 5, that a run with a login file set returns the login line the stand-in's shell prints from that file? I would add it.

   2. The Interface says "No leftovers program runs (no `os_user`), no temporary folder is removed (none was made)". No criterion tests either statement. Should I add one that a runtime built with a `leftovers` program and `containers` never starts it, and one that no temporary folder is made or removed? I would add both, with a stand-in `leftovers` that writes a record file and a check that the record is absent. If you think these statements are only explanatory, say so and I will accept as is.

   3. Criterion 9 says the version call gets "the version time limit", but neither the story nor the criterion names the value. Is it the existing constant of the runtimes? If so, please name it (module and name), so the test can assert it and not copy a number.

   My choice: answer yes to 1 and 2, and name the constant for 3. I would then accept.
4. 2026-10-24 human: Answers to the intake (F0042-S0008, the agent runtimes start their process in a container):

   1. **Yes**: criterion 4 gains a row that a run in a container with a login file set returns the login the stand-in's shell reports (`factory-login-used:`) from the mounted file, and criterion 5 the same for opencode.
   2. **Yes, both**: one row that a runtime built with a `leftovers` program and `containers` never starts it (a stand-in `leftovers` that writes a record file; the record stays absent), and one that no temporary folder is made or removed for a call in a container.
   3. The value is the runtime's constructor argument `version_time_limit`, whose default is `factory.adapters.agent_launch.VERSION_TIME_LIMIT` (30 seconds). The row builds the runtime with its own `version_time_limit` and asserts that the recorded call has exactly that limit, plus one row with the default that compares against `VERSION_TIME_LIMIT` by name, not by a copied number.

   Please write the three into the criteria as you accept.
5. factory: started intake as self.
6. intake: accepted. The three changes below are the human's answers in journal entry 4, written into the criteria as they asked. They are not my own improvements.
   - Interface: accepted. It names concrete modules and signatures (`agent_launch.container_launch`, `login_paths`, `version_launch`, `killed_at_limit`, `read_call_end`; the `containers` keyword and property on both runtimes). The `Launch.env` change and the `ValueError` and `AgentRuntimeError` rules are stated exactly.
   - Criteria: accepted, with the answers carried in.
     - Criteria 4 and 5 each gain a row: a run with a login file set returns the login line `factory-login-used:` read from the mounted file.
     - Criterion 9 now names the version time limit: the runtime's constructor argument `version_time_limit`, default `factory.adapters.agent_launch.VERSION_TIME_LIMIT`. One row passes its own value and asserts it; one row compares the default against `VERSION_TIME_LIMIT` by name.
     - New criterion 11 covers answer 2: a runtime built with a `leftovers` program and `containers` never starts it, and no temporary folder is made or removed. `make check` and `docs:` are now criteria 12 and 13, still last.
     - Each Interface rule has a criterion for both sides: the `ValueError` and its construction without it (3), `os_user` refused (6), kill at or after the limit and before it (2 and 7), and no container behaviour when `containers` is absent (10).
   - Smoke test: accepted. Both commands are runnable. The pytest command passes no `-q`, and the `Expect:` lines can be checked against the output (`1`, and three exact lines).
   - Architecture: accepted. All of it sits in `factory.adapters`, which imports `factory.application.containers` and `factory.domain.containers`. `agent_launch` stays free of the process module.
   - Scope: accepted. The story is feature `F0042`'s S0008, as listed in `feature.md`. Wiring is left to S0010 and no existing test is changed.
7. factory: started tests as self.
8. tester: I wrote the red tests from the Interface and the 13 criteria. `make test` fails for the right reasons: an ImportError for the new names in `factory.adapters.agent_launch`, and `TypeError: ... unexpected keyword argument 'containers'` from both runtimes. `make lint` is green. I skipped the type check, as this stage's instructions say.

   Criteria → tests:
   - criterion 1: tests/adapters/test_agent_launch_container.py::test_a_container_launch_mounts_the_files_read_only_at_their_own_paths. Three rows:
     - `mounted`: the two files mounted in order, the working directory `/work/checkout`, the environment and the time limit as given.
     - `own-environment`: a subclass of `FakeContainerRuns` whose `launch` returns `env=None`. The expected `Launch(env=None)` is built in the test, which also checks that the model accepts `None`.
     - `mount-under-work`: `/work/x` raises `ValueError` and the fake records no call.
   - criterion 2:
     - tests/adapters/test_agent_launch_container.py::test_in_a_container_a_kill_status_at_the_limit_is_the_limit, with five rows covering both sides of the limit and today's rule.
     - tests/adapters/test_agent_launch_container.py::test_a_container_call_killed_at_the_limit_is_read_as_the_limit_and_no_refusal, with two rows: no stderr, and a `sudo:` line in stderr.
   - criterion 3: test_claude_runtime_container.py and test_opencode_runtime_container.py, each ::test_a_runtime_keeps_its_containers_and_refuses_them_with_a_confine_executable (three rows each).
   - criterion 4: tests/adapters/test_claude_runtime_container.py::test_a_run_in_a_container_mounts_the_logins_and_instructions_and_completes (rows: token file; token and API files), plus ::test_a_run_in_a_container_reports_the_login_read_from_the_mounted_file.
   - criterion 5: tests/adapters/test_opencode_runtime_container.py::test_a_run_in_a_container_mounts_the_login_and_configuration_and_completes (rows: no login; API login), plus ::test_a_run_in_a_container_reports_the_login_read_from_the_mounted_file.
   - criterion 6: in both runtime modules, ::test_a_request_with_an_operating_system_user_is_refused_in_a_container.
   - criterion 7: in both runtime modules:
     - ::test_a_container_killed_at_its_limit_ends_time_limit_without_a_resume, a real stand-in exiting 137 (3 s at a 3 s limit; at once under 30 s).
     - ::test_podman_s_kill_status_at_the_limit_is_read_as_the_time_limit, a recorded `ProcessResult` with 137 at 30 s and at 29.9 s. Claude Code uses the `recorder` fixture; opencode replaces `run_streaming` via `monkeypatch`.
   - criterion 8: tests/adapters/test_claude_runtime_container.py::test_a_budget_stop_in_a_container_is_resumed_with_the_same_mounts.
   - criterion 9:
     - in both runtime modules, ::test_the_version_runs_in_a_container_with_the_version_time_limit (rows: the default, compared against `VERSION_TIME_LIMIT` by name; a given 7 s).
     - tests/adapters/test_agent_launch_container.py::test_the_version_call_on_the_host_has_the_process_s_own_environment, for the `version_launch(..., containers=None)` row.
   - criterion 10: in both runtime modules, ::test_without_containers_the_call_runs_in_the_request_s_working_directory. No existing test was changed.
   - criterion 11: in both runtime modules, ::test_a_call_in_a_container_starts_no_leftovers_program_and_no_temporary_folder.
     - A stand-in `leftovers` writes a record file, and the record stays absent.
     - The `temporary_root` folder stays empty.
     - No call other than the agent's goes through `run_process`: Claude Code counts the `recorder` fixture's requests; opencode monkeypatches `run_process` with a `Recorder`.
   - criteria 12 and 13: not for this stage (`make check`; docs).

   Files created:
   - tests/adapters/container_runtime_support.py: shared helpers (the played workspace with `checkout/` and `home/`, the container environment with `HOME=/work/home` and the stand-in on `PATH`, the `read_only` mount, the record-writing program, the files in a folder).
   - tests/adapters/test_agent_launch_container.py
   - tests/adapters/test_claude_runtime_container.py
   - tests/adapters/test_opencode_runtime_container.py

   What the test run could not import, or failed on:
   - tests/adapters/test_agent_launch_container.py is a collection error: `container_launch` and `version_launch` do not exist in `factory.adapters.agent_launch` yet.
   - The two runtime modules import; their tests fail with `TypeError` on the `containers` keyword.

   Choices I made:
   - The criteria spread the "rows for both runtimes" over the two runtime modules the Interface names. Each module has its own parametrized test, not one test across both modules.
   - The constructor's `ValueError` is checked only for being raised; its message is not pinned, because the Interface gives none.

   Nothing is open.

   `lint`: lint: green (0.8 s)
   `test`: ERROR tests/adapters/test_agent_launch_container.py - ImportError while importing test module '/work/checkout/tests/adapters/test_agent_launch_container.py'.
9. factory: started doing as self.
10. coder: Both agent runtimes can now start each call in a container. The tester's new tests pass without changes and `make check` is green: lint, types, layers, sast, secrets, licenses, and test (65.3 s), ending with `check: green`.

    What I built:
    - `src/factory/adapters/agent_launch.py`:
      - New `container_launch`: mounts the given files read-only at their own paths, in order, each once, sets the working directory to `WORK_CHECKOUT`, and turns the `ContainerLaunch` into a `Launch`.
      - New `login_paths`, `version_launch` and `run_environment`; `run_environment` is the request's environment without the logins, plus the runtime's switches. `run_launch` now uses it and otherwise works as before.
      - New constant `CONTAINER_OS_USER`: the error text both runtimes share.
      - `Launch.env` is now `dict[str, str] | None`.
      - `killed_at_limit` and `read_call_end` gain `in_container: bool = False`. With it true, exit status 137 or -9 at or after the limit counts as the time limit, as it does for a call with an `os_user`. The default changes nothing.
      - The module still does not import the process module.
    - `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py`:
      - New keyword `containers` and a read-only `containers` property. Combining `containers` with a `confine_executable` raises `ValueError`.
      - With containers, `run` raises `AgentRuntimeError(CONTAINER_OS_USER)` before writing any file when the request has an `os_user`.
      - `_process_request` calls `container_launch` with the mounts `[*login_paths(...), <the call's file>]`. The call's end is read with `in_container=True`.
      - `version()` in both runtimes now goes through `version_launch`. On the host it behaves as before, since `env=None` was already the default of `ProcessRequest`.
      - No leftovers program runs and no temporary folder is made or removed. That already followed from `os_user is None` and no confine executable, so it needed no new code.

    Main decision, and the alternative I rejected:
    - The Interface wanted the container call made inside `run_launch`, with two more keywords (`containers`, `mounted`). That broke ruff's argument limit (PLR0913, 7 > 5). A `# noqa: PLR0913` then failed `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`, so I removed it.
    - Instead `run_launch` keeps its old signature, and each runtime's `_process_request` picks `run_launch` or `container_launch`. Both get their environment from the shared `run_environment`.
    - I also rejected a holder type carrying `containers` and the mounted files (a dataclass, or `ContainerRuns` added to `Starters` with `arbitrary_types_allowed`). It would have added a new type only to get under the argument limit.
    - The cost: the reviewer will see a new similar-code finding in `make duplicates` for the `if self._containers is None:` branch in both runtimes.

    Refactor pass: I read the diff once, and the `run_launch` restructuring above came out of it. Nothing else needed changing.

    Noticed but did not touch:
    - `make duplicates` reports 15 new findings. Mine are the container branch and the constructor and property lines in both runtimes; some others look like known similar code whose line ranges moved. It also reports `FakeContainerRuns`, `PodmanRuns`, `FakeSnapshots` and `ZfsSnapshots` as unused (vulture, 60 %), because nothing wires them yet; that is for S0010.
    - The journal did not change what the task means, so the Description stays as it is.

    `check`: check: green
    `duplicates`: duplicates: 15 new, 36 known, 2 gone
