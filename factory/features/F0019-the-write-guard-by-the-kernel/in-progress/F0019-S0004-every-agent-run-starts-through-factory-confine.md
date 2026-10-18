---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 223
comments_read: [6251814997, 6251898687]
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-18T15:50:11.558909Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T15:39:43.731966Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T15:39:43.738533Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-18T15:40:08.426822Z'
  stage: intake
  run: 55978e7abfd14267856b1a40b2b090df
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-18T15:41:23.957800Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-18T15:41:41.723498Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-18T15:41:58.976296Z'
  stage: intake
  run: 552491052c8649a6ac61cb6d17fc0f56
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-18T15:42:19.260308Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-18T15:48:37.426477Z'
  stage: tests
  run: b99dfcfb64b74437bd231ab9a9f2527e
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-18T15:49:53.969287Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-18T15:50:11.558909Z'
  stage: tests
---

# Every agent run starts through `factory-confine`

## Description

With the adapter (S0001), the wrapper (S0002) and the targets (S0003) in place, the `claude -p` runtime starts every call of a run through `factory-confine`. For each run it writes the run's rules (`Confinement`) to `confine-<session>.json` in its state directory beside the guard's files: the targets of the request's write paths and tool paths, the runtime's own folder in the agent's home (`<HOME>/.claude`), the device files that exist, and the run's own temporary folder `<temporary root>/factory-run-<session>`. It sets `CLAUDE_CONFIG_DIR` to `<HOME>/.claude`, so that Claude Code keeps its `.claude.json` inside a folder the rules allow rather than in the home's root (feature decision 9). After every call, also one killed at its time limit, it removes the temporary folder as the run's user (feature decision 11). A wrapper that refuses ends the run with `AgentRuntimeError`, as a refused `sudo` does. The runtime confines only when it is built with the wrapper's command, which the wiring gives by default (feature decision 13); the tests of earlier stories build the runtime without it and keep their command lines, and the two earlier tests that run a call through `build_boundaries` pass `confine_executable=None`. The hook stays registered as before, as the cross-check (feature decision 16); the undo stays as the backstop. The guard is live only once the image is rebuilt and the human's change 5 names factory-rf's tool paths.

## Interface

`factory.domain.confinement` (`domain`):

```python
DEVICE_FILES: tuple[str, ...] = ("/dev/null", "/dev/zero", "/dev/full", "/dev/random", "/dev/urandom", "/dev/tty")
DEVICE_FOLDERS: tuple[str, ...] = ("/dev/shm",)
```

`factory.adapters.claude_runtime` (`adapters`):

```python
CONFIG_VARIABLE = "CLAUDE_CONFIG_DIR"
RUNTIME_FOLDER = ".claude"
TEMPORARY_PREFIX = "factory-run-"
CLEANUP_SCRIPT = 'chmod -R u+rwX -- "$1" 2>/dev/null; rm -rf -- "$1"'
CLEANUP_TIME_LIMIT = timedelta(seconds=60)
CONFINE_PREFIX = "factory-confine:"

class ClaudeCodeRuntime(AgentRuntime):
    def __init__(
        self,
        executable: str,
        state_directory: Path,
        kill_points: KillPoints | None = None,
        *,
        version_time_limit: timedelta = VERSION_TIME_LIMIT,
        sudo_executable: str = SUDO_EXECUTABLE,
        login_file: Path | None = None,
        confine_executable: str | None = None,
        temporary_root: Path | None = None,
    ) -> None: ...

    @property
    def confine_executable(self) -> str | None:
        """The wrapper every call starts through, or `None` when calls are not confined."""
```

- `temporary_root` `None` is `Path(tempfile.gettempdir())`; the run's temporary folder is `temporary_root / f"factory-run-{session}"`, the same for a first call and its resume.
- With `confine_executable` `None`, the command line, the environment and the files of a run are exactly as before this story.
- With `confine_executable` set, every call (a first one and a resumed one) is started as `[confine_executable, "--rules", <rules file>, "--", *<the call's command as before>]`, where the call's command is the login shell and `claude` with their arguments. Without an `os_user` that list is the program the process starts; with one it follows `env -i` and its assignments, after `sudo -n -u <user> -- timeout --signal=KILL <limit>s`.
- The rules file is `state_directory / f"confine-{session}.json"`, the `Confinement` as `model_dump_json()`, mode `0o640`, written with the run's other files and removed with them after the run, also when a call raises.
- The `Confinement` is `confinement_of(write_targets(guard, home=home), root=guard.root, existing_files=..., extras=..., temporary_directory=<the run's temporary folder>)`, where `guard` is the request's guard settings, or `GuardSettings(root=request.working_directory, write_paths=[], protected_paths=[])` when it has none; `home` is `Path(request.environment["HOME"])`, or `None` when the environment has no `HOME`; `existing_files` holds the file targets that are files (`Path.is_file`); `extras` is the folder target `home / ".claude"` (when `home` is not `None`), then a folder target for each of the `DEVICE_FOLDERS` that exists, then a file target for each of the `DEVICE_FILES` that exists.
- With `confine_executable` set and a `HOME` in the request's environment, the call's environment gains `CLAUDE_CONFIG_DIR=<HOME>/.claude`; without `HOME` it does not. The login variable and the three switches stay as they are.
- After every call with `confine_executable` set, the runtime runs `["/bin/sh", "-c", CLEANUP_SCRIPT, "factory-cleanup", <temporary folder>]` through `run_process` with `CLEANUP_TIME_LIMIT`, prefixed by `[sudo_executable, "-n", "-u", <os_user>, "--"]` when the request has an `os_user`, in the request's working directory with an empty environment. Its exit status and output are not read, so a removal that fails changes no result; an `OSError` starting it is `AgentRuntimeError`, as for a call (not tested: no test can make `/bin/sh`, or a `sudo` that has just started the call, fail to start).
- A call that ends without a usable reply (none that parses, or one cut short by the time limit) and whose standard error holds a line starting `factory-confine:` raises `AgentRuntimeError` with the detail `f"{confine_executable} refused the agent run: {line}"`; such a line before a usable reply is ignored. A `sudo:` refusal is checked first, as before.

`factory.entry.wiring` (`entry`):

- `build_boundaries(settings, token, *, hosting=None, which=shutil.which, confine_executable: str | None = CONFINE_COMMAND)` builds the `ClaudeCodeRuntime` with that `confine_executable`; its callers in the package (`factory.entry.run` and `boundaries_from_environment`) pass none, so every run of the factory is confined.

Tests (the tester writes them): `tests/adapters/test_claude_runtime_confinement.py` (with the stand-in `claude` of `tests/adapters/claude_stand_in.py` and the real installed `factory-confine`, found beside `sys.executable`, as the confine executable, the temporary root and the checkout under `tmp_path`; the `sudo` rows with a stand-in `sudo` as `tests/adapters/test_claude_runtime_os_user.py` writes one; the stand-in records its calls in its own folder, so that folder must be one the rules allow, for example the tool path `stand-in/*` with the stand-in under the checkout), `tests/entry/test_wiring_confinement.py`. Criteria 2, 4, 5 and 11 use a stand-in confine executable that records its arguments and the rules file's text and mode before it runs what follows `--` (or plays its line); a request without guard settings (criterion 8) keeps the stand-in `claude` under `<HOME>/.claude`, which the rules allow; criterion 9's agent (a subfolder of mode `0o000` in `$TMPDIR`, the folder's listing at each call) and criterion 10's `sudo` (refusing only the removal) are scripts of the test module's own. Changed under the feature's decision 13, by the tester only: `tests/entry/test_wiring_boundaries.py`, the test `test_the_built_agent_runtime_keeps_its_run_files_under_runs`, and `tests/entry/test_wiring_login.py`, the test `test_the_built_runtime_hands_the_login_file_s_token_to_claude`: each one's `build_boundaries` call gains `confine_executable=None` (their requests have no `PATH`, and their stand-in records its calls in a folder no rule allows); nothing else in those modules changes.

## Acceptance criteria

1. A runtime built without `confine_executable` starts a call with the same command line and environment as before this story and writes no `confine-*.json` (its `confine_executable` is `None`).
2. With `confine_executable` a stand-in that records its arguments, the text and mode of the file after `--rules`, and then runs what follows `--`, and no `os_user`, the stand-in receives `--rules <state>/confine-<session>.json --` followed by the call's command as before (the stand-in `claude` and its arguments), and the run's result is the stand-in `claude`'s reply (`completed`, its decision and entry).
3. With `confine_executable` and an `os_user`, the stand-in `sudo` receives `-n -u agent -- timeout --signal=KILL <limit>s env -i <assignments> <confine executable> --rules <file> -- ...`, with `CLAUDE_CONFIG_DIR=<HOME>/.claude` among the assignments.
4. The rules file holds the `Confinement` of the request while the call runs, with mode `0o640`, and is gone after the run, also after a call that raises `AgentRuntimeError` (rows of one parametrized test).
5. For a request with write paths `["src/*", "README.md", "docs/openapi.json"]`, tool paths `[".venv/*", "~/.cache/*"]`, `README.md` existing and `docs/openapi.json` not, and `HOME` `<tmp>/home`, the rules hold the folders `<checkout>/src`, `<checkout>/docs`, `<checkout>/.venv`, `<tmp>/home/.cache`, `<tmp>/home/.claude` and then `/dev/shm` when it exists, the files `<checkout>/README.md` and then the device files that exist, and the temporary folder `<temporary root>/factory-run-<session>`.
6. Through the real wrapper, a stand-in step that writes `<checkout>/src/a.txt` completes and leaves the file; a step that writes `<checkout>/other/b.txt` ends the run `died` and leaves no such file (rows of one parametrized test).
7. The stand-in sees `TMPDIR` equal to the run's temporary folder, which exists while it runs, `CLAUDE_CONFIG_DIR` equal to `<HOME>/.claude` and the three switches of `SWITCHES`; for a request whose environment has no `HOME`, `CLAUDE_CONFIG_DIR` is not set, the switches are, and the rules hold no `.claude` folder and no folder of a `~/` tool path (rows of one parametrized test).
8. A request without guard settings is confined with no path of the checkout: a stand-in step that writes in the working directory ends the run `died` and leaves no file.
9. After a run, the temporary folder is gone, also when the agent left a subfolder of mode `0o000` in it, after a call killed at its time limit (a limit of a few seconds, the stand-in waiting longer), and after a budget stop and its resume, whose two calls each start with an empty temporary folder at the same path (rows of one parametrized test).
10. With an `os_user`, the removal is started through `<sudo> -n -u agent -- /bin/sh -c <CLEANUP_SCRIPT> factory-cleanup <folder>`; a removal that fails (the stand-in `sudo` exits 1 for it) leaves the run's result as the call made it (rows of one parametrized test).
11. A wrapper line `factory-confine: the kernel offers Landlock ABI 2, the write guard needs ABI 3 or higher` on standard error with no reply raises `AgentRuntimeError` whose detail is `<confine executable> refused the agent run: factory-confine: the kernel offers Landlock ABI 2, the write guard needs ABI 3 or higher`; the same line followed by a usable reply is ignored and the run completes (rows of one parametrized test, the line played by a stand-in confine executable).
12. `build_boundaries` called without `confine_executable` builds a `ClaudeCodeRuntime` whose `confine_executable` is `factory-confine`, and called with `confine_executable=None` one whose `confine_executable` is `None` (rows of one parametrized test).
13. A runtime built without `temporary_root` makes the run's temporary folder in `tempfile.gettempdir()`: with `tempfile.tempdir` set to a folder under `tmp_path` (`monkeypatch`) before the runtime is built, the stand-in sees `TMPDIR` equal to `<that folder>/factory-run-<session>`.
14. With an `os_user`, a call with no reply whose standard error holds a `sudo:` line and a `factory-confine:` line raises the `AgentRuntimeError` of the `sudo` refusal (`<sudo> refused the agent run: sudo: ...`), not the wrapper's.
15. A call killed at its time limit (a limit of a few seconds, the stand-in confine executable playing a `factory-confine:` line and then waiting longer) raises `AgentRuntimeError` whose detail is `<confine executable> refused the agent run: <that line>`.
16. The removal of the temporary folder runs in the request's working directory with an empty environment: the stand-in `sudo` (with an `os_user`) and a recording `/bin/sh` path without an `os_user` each see the request's working directory and an empty environment for it (rows of one parametrized test).
17. `boundaries_from_environment` yields a runtime whose `confine_executable` is `factory-confine`, and the source of `factory.entry.run` passes no `confine_executable` to `build_boundaries` (a source check).
18. `make check` stays green.
19. docs: `docs/operator-guide.md`, section *The agent runs as a second user*, shows the new command line (`sudo -n -u agent -- timeout --signal=KILL <limit>s env -i ... factory-confine --rules /state/runs/confine-<session>.json -- /bin/sh -c ... claude ...`) and says what the wrapper does, which writes the kernel allows (the write paths as targets, the tool paths, `~/.claude`, the device files, `/tmp/factory-run-<session>` as `TMPDIR`) and that every other write is refused with `Permission denied`; that a `factory-confine:` line without a reply stops the run with an error, as a `sudo:` line does; that the temporary folder is removed after every call; and that `CLAUDE_CONFIG_DIR` moves `.claude.json` into `~/.claude`. `docs/project-guide.md`, section *The `claude -p` runtime*, the same for agents. `docs/decisions.md` gets an entry *Every agent run is confined by the kernel*, dated 2026-10-18 (F0019-S0004), with the reasons of the feature's decisions 9, 10, 11 and 13.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/checkout/src" "$d/checkout/other" "$d/home" "$d/runs" "$d/tmp"
cat > "$d/claude" <<'EOF'
#!/bin/sh
src=refused; other=refused; tmp=shared
echo x > src/a.txt 2>/dev/null && src=written
{ echo x > other/b.txt; } 2>/dev/null && other=written
case "$TMPDIR" in */factory-run-*) [ -d "$TMPDIR" ] && tmp=own ;; esac
printf '{"type": "result", "subtype": "success", "is_error": false, "num_turns": 1, "total_cost_usd": 0.01, "usage": {"input_tokens": 1, "output_tokens": 1}, "permission_denials": [], "structured_output": {"decision": "question", "entry": "src %s, other %s, temporary folder %s, config %s"}}\n' "$src" "$other" "$tmp" "${CLAUDE_CONFIG_DIR##*/}"
EOF
chmod +x "$d/claude"
uv run -q python -c '
import os, sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, GuardSettings
d = Path(sys.argv[1])
runtime = ClaudeCodeRuntime(str(d / "claude"), d / "runs", confine_executable="factory-confine", temporary_root=d / "tmp")
agent = AgentDefinition(name="coder", model="sonnet", tools=["Bash"], budget_usd=Decimal("1"), instructions="Probe.")
guard = GuardSettings(root=d / "checkout", write_paths=["src/*"], protected_paths=[])
request = AgentRunRequest(agent=agent, prompt="Probe.", allowed_decisions=["question"], time_limit=timedelta(minutes=1), working_directory=d / "checkout", environment={"PATH": os.environ["PATH"], "HOME": str(d / "home")}, guard=guard)
result = runtime.run(request)
print(result.end_reason, "|", result.entry)
print(sorted(os.listdir(d / "tmp")), sorted(os.listdir(d / "runs")))
' "$d"
```
Expect: two lines, `completed | src written, other refused, temporary folder own, config .claude` and then `[] []`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: Questions. The format check passed, so there are no form findings. Three Interface clauses have no criterion. The smoke test, the architecture and the scope are fine.

   1. The Interface says a call "cut short by the time limit" whose standard error holds a `factory-confine:` line raises `AgentRuntimeError`. Criterion 11 covers only "no reply" and "line before a usable reply". The time-limit branch of that "or" has no criterion. Option A: add a criterion that a call killed at its time limit with a `factory-confine:` line on standard error raises the wrapper's `AgentRuntimeError`. Option B: remove the clause from the Interface. I would choose A.

   2. The Interface says the removal runs "in the request's working directory with an empty environment". No criterion checks the working directory or the environment of the removal. Criterion 10 checks only the command line. Option A: add a criterion that the stand-in `sudo` and the no-`os_user` removal see the request's working directory and an empty environment. Option B: drop the clause. I would choose A.

   3. The Interface says the callers of `build_boundaries` in the package (`factory.entry.run` and `boundaries_from_environment`) pass no `confine_executable`, "so every run of the factory is confined". Decision 13 says "a test pins the default". Criterion 12 tests only `build_boundaries` itself. Option A: add a criterion that `boundaries_from_environment` yields a runtime whose `confine_executable` is `factory-confine`, and that `factory.entry.run` passes no `confine_executable` (a source check). Option B: say in the Interface that only the default is tested. I would choose A.
4. 2026-10-18 human: A on all three:
   1. Add the criterion: a call killed at its time limit with a `factory-confine:` line on standard error raises the wrapper's `AgentRuntimeError`.
   2. Add the criterion: the stand-in `sudo` and the no-`os_user` removal each see the request's working directory and an empty environment.
   3. Add the criterion: `boundaries_from_environment` yields a runtime whose `confine_executable` is `factory-confine`, and `factory.entry.run` passes no `confine_executable` (a source check).
   Each before the two closing criteria.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete modules and signatures (`factory.domain.confinement` constants, `ClaudeCodeRuntime.__init__` and `confine_executable`, `build_boundaries`). Each comment-level behaviour now has a criterion. Writing the removal's working directory and empty environment into the Interface was not needed: criterion 16 covers it.
   - Criteria: each is testable by one parametrized test function. Both sides of each rule are covered: wrapper line with no reply (11), before a usable reply (11), cut short by the time limit (new 15), `sudo` before wrapper (14), failing removal (10), allowed and refused writes (6), with and without `HOME` (7). I carried in the human's answer (journal entry 4, A on all three) as new criteria 15 (time-limit branch), 16 (removal's working directory and empty environment) and 17 (`boundaries_from_environment` and the source check of `factory.entry.run`), before the two closing criteria. The closing ones are now 18 (`make check`) and 19 (`docs:`).
   - Smoke test: runnable with the installed `factory-confine`. The `Expect:` line is checkable: two exact output lines.
   - Architecture: constants in domain, runtime changes in adapters, wiring in entry. Layers are respected, and the process and cleanup calls go through `run_process`.
   - Scope: within F0019 S0004 of the feature's scope list. Nothing from "Out of scope" is touched. The leave to change the two earlier wiring tests is named, with the human's decision 13.
7. factory: started tests as self.
8. tester: Question: criterion 16, the row without an `os_user`. The criterion asks for "a recording `/bin/sh` path" that sees the removal's working directory and environment. The Interface says the removal runs the literal `["/bin/sh", "-c", CLEANUP_SCRIPT, ...]`. A test cannot put a recording program in place of `/bin/sh`. Through `/bin/sh` itself the removal's working directory and environment cannot be seen, because `chmod` and `rm` come from the shell's built-in default `PATH`. So the row needs a way in, and choosing one means deciding how the code is built. The options I see:
   - A (my choice): the removal builds its command from the module's existing `SHELL_EXECUTABLE` constant (value `"/bin/sh"`). The test sets `factory.adapters.claude_runtime.SHELL_EXECUTABLE` with `monkeypatch` to a script that records and then runs `/bin/sh`. Criterion 10's `sudo` row still expects the literal `/bin/sh`. The Interface would get one line: "the removal's shell is `SHELL_EXECUTABLE`".
   - B: wrap `run_process`, as `factory.adapters.claude_runtime` imports it, with a recording function that hands on to the real one, and read the `ProcessRequest` of the removal. This fakes a dependency that has no interface.
   - C: drop the row and test only the `sudo` side.
   I have already written row A, which is `tests/adapters/test_claude_runtime_confinement.py::test_the_removal_runs_in_the_working_directory_with_an_empty_environment[shell]`. If the answer is B or C, I change only that row.

   Tests written (red on purpose):
   criterion 1: tests/adapters/test_claude_runtime_confinement.py::test_without_a_confine_executable_a_call_starts_as_before_and_writes_no_rules
   criterion 2: tests/adapters/test_claude_runtime_confinement.py::test_a_call_starts_through_the_confine_executable_with_its_rules_file
   criterion 3: tests/adapters/test_claude_runtime_confinement.py::test_with_a_user_sudo_starts_the_confine_executable_after_env_i_with_the_config_folder
   criterion 4: tests/adapters/test_claude_runtime_confinement.py::test_the_rules_file_holds_the_confinement_while_the_call_runs_and_is_gone_after (rows completed, refused)
   criterion 5: tests/adapters/test_claude_runtime_confinement.py::test_the_rules_hold_the_targets_of_write_and_tool_paths_the_home_s_runtime_folder_and_devices
   criterion 6: tests/adapters/test_claude_runtime_confinement.py::test_through_the_wrapper_only_a_write_the_rules_allow_is_made (rows write-path, elsewhere; real `factory-confine`)
   criterion 7: tests/adapters/test_claude_runtime_confinement.py::test_the_agent_sees_its_temporary_folder_the_config_folder_and_the_switches (rows home, no-home)
   criterion 8: tests/adapters/test_claude_runtime_confinement.py::test_a_request_without_guard_settings_is_confined_with_no_path_of_the_checkout
   criterion 9: tests/adapters/test_claude_runtime_confinement.py::test_the_temporary_folder_is_empty_at_each_call_and_gone_after_the_run (rows locked-subfolder, time-limit, budget-and-resume)
   criterion 10: tests/adapters/test_claude_runtime_confinement.py::test_with_a_user_the_removal_runs_through_sudo_and_its_failure_changes_no_result (rows removed, removal-fails)
   criterion 11: tests/adapters/test_claude_runtime_confinement.py::test_a_wrapper_line_without_a_reply_is_a_runtime_error_and_before_a_reply_is_ignored (rows no-reply, reply-after-the-line)
   criterion 12: tests/entry/test_wiring_confinement.py::test_build_boundaries_confines_the_runtime_unless_told_not_to (rows default, none)
   criterion 13: tests/adapters/test_claude_runtime_confinement.py::test_without_a_temporary_root_the_run_s_folder_lies_in_the_system_temporary_folder
   criterion 14: tests/adapters/test_claude_runtime_confinement.py::test_a_sudo_refusal_is_reported_before_a_wrapper_line
   criterion 15: tests/adapters/test_claude_runtime_confinement.py::test_a_wrapper_line_of_a_call_killed_at_its_time_limit_is_a_runtime_error
   criterion 16: tests/adapters/test_claude_runtime_confinement.py::test_the_removal_runs_in_the_working_directory_with_an_empty_environment (rows sudo, shell; the shell row depends on the question above)
   criterion 17: tests/entry/test_wiring_confinement.py::test_every_run_of_the_factory_builds_a_confined_runtime (the behaviour of `boundaries_from_environment` and an ast source check of `factory.entry.run`)

   Files created: tests/adapters/test_claude_runtime_confinement.py, tests/entry/test_wiring_confinement.py. The adapter module holds its own probe agent (records `TMPDIR`, the folder's listing and the rules files in the state directory; it can leave a `0o000` subfolder, wait and play a budget stop), a stand-in confine executable, a `sudo` that refuses only the removal, and a recording shell. The stand-in `claude` and the probe sit under `<checkout>/stand-in` with the tool path `stand-in/*`; in criterion 8 the stand-in sits under `<HOME>/.claude/stand-in`. `_without_locale` is imported from `tests/adapters/test_claude_runtime_os_user.py`, unchanged.

   Earlier tests changed under feature decision 13, as the description names them: tests/entry/test_wiring_boundaries.py::test_the_built_agent_runtime_keeps_its_run_files_under_runs and tests/entry/test_wiring_login.py::test_the_built_runtime_hands_the_login_file_s_token_to_claude. In each, the `build_boundaries` call gained `confine_executable=None` and nothing else changed.

   Not importable by the test run: `tests/adapters/test_claude_runtime_confinement.py` fails at collection with ImportError (`CLEANUP_SCRIPT`, `CONFIG_VARIABLE` in `factory.adapters.claude_runtime`; `DEVICE_FILES`, `DEVICE_FOLDERS` in `factory.domain.confinement`). The wiring tests fail on the missing `confine_executable` keyword and property. `make lint` is green.

   Open for the coder: the source check in criterion 17 reads `factory.entry.run` and may need adding to the structural tests that mutmut leaves out in `pyproject.toml`. That is outside my write paths.
9. 2026-10-18 human: A: the removal builds its command from `SHELL_EXECUTABLE`, the test patches it with a recording script, and the Interface gets the line "the removal's shell is `SHELL_EXECUTABLE`"; criterion 10's `sudo` row keeps the literal `/bin/sh`.
   Your open note: done on main (`84c9bde9`): `[tool.mutmut]` now deselects `tests/entry/test_wiring_confinement.py::test_every_run_of_the_factory_builds_a_confined_runtime`; keep that test's name.
10. factory: started tests as self.
