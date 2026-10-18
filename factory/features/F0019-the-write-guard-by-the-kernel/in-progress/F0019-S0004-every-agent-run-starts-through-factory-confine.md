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
- After every call with `confine_executable` set, the runtime runs `[SHELL_EXECUTABLE, "-c", CLEANUP_SCRIPT, "factory-cleanup", <temporary folder>]` (the removal's shell is `SHELL_EXECUTABLE`) through `run_process` with `CLEANUP_TIME_LIMIT`, prefixed by `[sudo_executable, "-n", "-u", <os_user>, "--"]` when the request has an `os_user`, in the request's working directory with an empty environment. Its exit status and output are not read, so a removal that fails changes no result; an `OSError` starting it is `AgentRuntimeError`, as for a call (not tested: no test can make `/bin/sh`, or a `sudo` that has just started the call, fail to start).
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
15. `make check` stays green.
16. docs: `docs/operator-guide.md`, section *The agent runs as a second user*, shows the new command line (`sudo -n -u agent -- timeout --signal=KILL <limit>s env -i ... factory-confine --rules /state/runs/confine-<session>.json -- /bin/sh -c ... claude ...`) and says what the wrapper does, which writes the kernel allows (the write paths as targets, the tool paths, `~/.claude`, the device files, `/tmp/factory-run-<session>` as `TMPDIR`) and that every other write is refused with `Permission denied`; that a `factory-confine:` line without a reply stops the run with an error, as a `sudo:` line does; that the temporary folder is removed after every call; and that `CLAUDE_CONFIG_DIR` moves `.claude.json` into `~/.claude`. `docs/project-guide.md`, section *The `claude -p` runtime*, the same for agents. `docs/decisions.md` gets an entry *Every agent run is confined by the kernel*, dated 2026-10-18 (F0019-S0004), with the reasons of the feature's decisions 9, 10, 11 and 13.

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
