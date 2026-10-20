# Pre-check F0040, fresh round: agent code never runs with the factory's rights

I checked the feature and its four stories against today's `main` (`cbb7dac0`, 2026-10-20), after these merges: F0030-S0001 (the time-limit kill ends every process of the command's session, `factory.domain.sessions` and `factory.adapters.process`), all of F0027 (`factory.entry.leftovers` after every call of an agent runtime; `GitCli.remove_ignored` after every returned run and at the restore), all of F0041 (the hook guard removed, `CLAUDE.md` R12 reworded), F0041-S0004 (`PYTHONDONTWRITEBYTECODE` in the umask test), the Makefile changes (`COLUMNS=200`, `--dist worksteal`) and F0027's `CLAUDE.md` bullets. I read `factory/story-form.md`, `CLAUDE.md`, `factory/pipeline.yml`, the earlier pre-checks `F0040-*-1.md`, and the code and tests each story touches.

## What I ran

Throwaway containers of `factory-self-factory` (`--network none --cpus 2`), one at a time, on an LF copy of `HEAD` (`git archive`) under `C:/Users/pasca/AppData/Local/Temp/pc40`, with the copy's `src` on `PYTHONPATH` and the image's `/opt/factory/.venv/bin/python`. The container ran as the image's user `factory` with the image's `sudo` rule.

**Form check.** `factory-check-story` on all four stories (copied under a `factory/features/` tree, because the program refuses a path outside it): `ok`, exit 0, each.

**Prototype 1: the time-limit kill of a call as `agent`** (the real `run_process` and `launch`, the real `sudo`, `timeout` and `env`, a limit of 3 s):

| The command, as `agent` | Result | `agent` processes afterwards |
|---|---|---|
| `sleep 100 & sh -c 'sleep 100' & sleep 100` (a tree in one process group, as `make`, its recipes, pytest and its xdist workers are) | exit `-9` after 3.0 s | none |
| `setsid sleep 100 >/dev/null & timeout 100 sleep 100 >/dev/null & sleep 100` (a child in a session of its own, as `run_process` starts every child, and a nested `timeout` in a group of its own) | exit `-9` after 3.0 s | three: the `setsid` sleep, the nested `timeout` and its sleep |
| `setsid sleep 12 & sleep 100` (the escaped child keeps the output pipe) | exit `-9` after **12.0 s** | none (it ended by itself) |
| `sudo -n -u agent -- sleep 15` with no inner `timeout`, so only the factory's own kill (F0030's) acts at 3 s | `timed_out`, after **15.0 s** | none (it ended by itself) |

**Prototype 2: `git clean -X` as `factory` after files made as `agent`** (a repository made by `factory` under `/work`, which is `2775 factory:factory-work`, as in the image):

- Made as `agent` under `sudo`'s umask `0002`: `.venv` (by `uv venv`), `.reports`, `.mypy_cache`, and an empty `mkdtemp` folder inside it. All folders `rwxrwsr-x agent:factory-work`. `git clean --quiet --force --force -d -X` as `factory`: exit 0, everything removed.
- Made as `agent` under the umask `022` (what `tests/conftest.py` sets in every pytest process): `.reports/new/j.xml`, `.mypy_cache/3.12/a.json`, and a `mkdtemp` folder with a file. Folders `rwxr-sr-x` and `rwx--S---`. `git clean` as `factory`: **exit 1**, `warning: failed to remove .reports/new/j.xml: Permission denied`, the same for the others; nothing removed.

**Prototype 3: uv's link mode under `env -i`** (`/work` on a tmpfs, so the checkout and `/home/agent/.cache/uv` lie on different file systems, as the volume `work` and the container's layer do in the instance): `uv pip install --offline` of a local wheel into `.venv`, as `agent`, printed `warning: Failed to hardlink files; falling back to full copy. ...` (three lines) without `UV_LINK_MODE`; with `UV_LINK_MODE=copy` (which the image's `ENV` gives the factory's own make today) it printed none. The files in `.venv` were `-rw-rw-r-- agent`, one link each.

## The four questions

**1. Does the time-limit kill still reach a project command that runs as `agent`?** Only through the inner `timeout`, and only for its own process group. F0030's session kill (`_kill_session`) leaves out every process it may not signal, so it ends nothing of a call under `sudo`: prototype 1, last row, ran on until the `agent` child ended by itself. Under S0001 that kill fires only at the limit plus 30 s anyway. The inner `timeout --signal=KILL` kills its own group, which holds `make`, the recipe shells, `uv`, pytest and its xdist workers, so the check ends at its limit with `-9` and is judged `time_limit` (prototype 1, first row). What left the group survives as `agent`: in this repository every child a test starts through `run_process` (it uses `start_new_session=True`; F0030-S0003's draft saw a fake `claude` outlive the kill by its 60 s for this reason), and the `mutants` recipe's own `timeout`. F0027's leftovers program runs only after a call of an agent runtime, so these survivors run on through the next home reset (S0004) and the next project commands until the next agent call ends. So F0040 must add the leftovers program after every project command run as the agent's user. My recommendation (question A): S0001 owns it in the make class, as `CommandUser.leftovers`, using `leftovers_launch` and `leftovers_fault` of `agent_launch`, and S0002 wires `leftovers_command()` (off with `end_leftovers=False`, as for the runtimes). A survivor that keeps the output pipe makes `run_process` wait until it ends by itself (prototype 1, third row), and no kill bounds that wait. The project guide already names this as a known limit (*Starting a process*), and the agent runtimes share it (question D).

**2. Can `remove_ignored` (`git clean -X` as `factory`) still remove what the checks write as `agent`?** Yes, as long as every folder is made under `sudo`'s umask `0002` (prototype 2). Both users have the primary group `factory-work`, `/work` is setgid, and the sudoers file sets `umask=0002` with `umask_override`; the umask comes from `sudo`, not from the environment. A folder made under the tests' umask `022`, or by `mkdtemp`, stops it with exit 1 (a `GitError`). No make target makes one: `make test` makes `.reports` before pytest runs and passes `-p no:cacheprovider`, and mypy, ruff, import-linter and uv run outside pytest. What `env -i` must keep is `PYTHONDONTWRITEBYTECODE=1`, which S0002 already sets: without it, every `__pycache__` a pytest process writes in the checkout is made under `022` (F0041-S0004 added it for the one test that starts pytest in the checkout with its own environment). I also recommend `UV_LINK_MODE=copy` (question B): without it every sync after F0027-S0003's removal of `.venv` prints uv's three-line hardlink warning into the command's output, because the cache and the checkout lie on different file systems. Nothing else is needed: `TMPDIR` and `XDG_*` are unset in agent runs too, and `/etc/gitconfig`'s `safe.directory = /work/checkout` lets the agent's git read the checkout for `make secrets` (the checkout's path is fixed, `CHECKOUT_PATH`).

**3. Stale names, lines and wording.** All code names the stories use still exist with the stated signatures (`launch`, `killed_at_limit`, `SUDO_GRACE`, `SUDO_PREFIX`, `KILL_STATUSES`, `agent_run_environment`, `production_environment`, `scrub_environment`, `RecordingProjectCommands`, `machine_log`, `TimestampedFactoryLog`, `SystemClock`, `run_sealed`, `Preflight._run_probe`, `KnownResults._run`, `RUNTIME_FOLDER`; `agent_launch` still does not import `process`; `build_boundaries` gained `end_leftovers`, which no story contradicts). The documents' sections exist (`**Left for v2.**` in the operator guide, *The agent runs as a second user*, *The stops you will see here*, *What opencode keeps in the agent's home*; *Project commands*, *The shared launch module*, *Boundaries*; the two decision-log entries). Stale: the leave set of S0003 (F0027 added `factory.entry.leftovers`), the R12 insertion point of change 2 (F0027's sentence now sits between the two anchors), the place of change 1 (F0027's leftovers bullet now follows the anchor), *The human's changes* point 4 (F0030-S0001 and F0027 are built; F0030-S0002 and S0003 are new backlog stories), the operator's check 3.7 (it points at F0030 for what the leftovers call must do), the out-of-scope line on leftovers, and the lease arithmetic (question C). S0003's new section in `agents.md` would land between the shared launch module and the opencode runtime; after F0027's *Ending the agent's leftover processes* reads better (optional).

**4. Leaves.** The two granted leaves still name tests that exist under those names. `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` now expects `{"factory.entry.wiring", "factory.entry.confine", "factory.entry.leftovers"}`, so S0003's expected set must keep `leftovers` (required edit). `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module` now lists six importers (F0027 added `factory.entry.leftovers`, F0019 `factory.entry.confine`); S0004 says "expects `factory.adapters.agent_home` among the importers", which is still exact. No test that F0027, F0030 or F0041 wrote is touched without a leave: the tests that build boundaries with an agent user (`tests/entry/test_wiring_agent_user.py`, `test_wiring_extras.py`, `test_wiring_run.py`) take their project commands from fixtures, not from `build_boundaries`; `tests/entry/test_wiring_boundaries.py` builds without an agent user; `tests/test_agent_launch_search.py`, `tests/test_make_search.py`, `tests/entry/test_wiring_leftovers.py`, `tests/application/test_interfaces.py` (its interfaces are a fixed list; `Git` keeps its 25 operations) and `tests/adapters/test_process_session.py` stay green as drafted. With question A's answer, S0001's new tests can reuse `tests/leftovers_runtime_support.py` (`write_program`, `write_sudo`, `own_user`, `LEFTOVERS_LINE`) without changing it.

## Verdicts

- **S0001**: needs the edits for the leftovers call (question A, answer A); otherwise accepted as drafted.
- **S0002**: needs the wiring of the leftovers program (question A) and, with question B's answer A, `UV_LINK_MODE`; otherwise accepted.
- **S0003**: needs one required edit (the leave's set); otherwise accepted.
- **S0004**: accepted as drafted; two optional edits.
- **feature.md**: needs the edits below (point 4, change 2, check 3.7, the lease sentence, the leave, the new decision 16).

### F0040-S0001

Edit 1 (required, Description). Replace

```markdown
A command killed so is a `time_limit` result. A `sudo` that refuses (only `sudo:` lines and a failing status) is a `ProjectCommandError`, not a red check. Without a `CommandUser` the class runs exactly as today, so every existing test and caller keeps its behaviour. The wiring that hands the instance's agent user to the class, and the seal around each command, are S0002's.
```

with

```markdown
A command killed so is a `time_limit` result. The user's `timeout` kills only its own process group, and the factory's kill cannot signal the user's processes (F0030's kill leaves them out): a process that left the group, such as a test's child that `run_process` starts in a session of its own, outlives the command. So with a `leftovers` program in the `CommandUser`, every command run as that user is followed by that program, as that user, as every call of an agent runtime is (F0027). A `sudo` that refuses (only `sudo:` lines and a failing status) is a `ProjectCommandError`, not a red check. Without a `CommandUser` the class runs exactly as today, so every existing test and caller keeps its behaviour. The wiring that hands the instance's agent user and the leftovers program to the class, and the seal around each command, are S0002's.
```

Edit 2 (required, Interface). Replace

```markdown
    os_user: str
    sudo_executable: str
    environment: dict[str, str]
```

with

```markdown
    os_user: str
    sudo_executable: str
    environment: dict[str, str]
    leftovers: list[str] | None = None
```

Edit 3 (required, Interface). Replace

```markdown
- The class reuses `launch`, `killed_at_limit`, `SUDO_GRACE` and `SUDO_PREFIX` from `factory.adapters.agent_launch` and copies none of them; `agent_launch` still does not import `factory.adapters.process`.
```

with

```markdown
- With `user` whose `leftovers` is set and whose `os_user` is not this process's own user (`own_identity().user`), every command that started is followed, whatever its result (passed, failed, `time_limit` or refused), by the `Launch` that `leftovers_launch(user.leftovers, os_user=user.os_user, sudo_executable=user.sudo_executable)` gives, run through `run_process` with `cwd` `/`. When `leftovers_fault(exit_status=..., timed_out=..., stderr=...)` gives a fault, `run` raises `ProjectCommandError(command, <the fault>)`; a refusal of the command itself wins and is raised instead. A leftovers program that cannot be started raises `ProjectCommandError(command, "cannot end the agent's processes: <the operating system's message>")`. Without `leftovers`, or when `os_user` is the own user, no second call is made.
- The class reuses `launch`, `killed_at_limit`, `SUDO_GRACE`, `SUDO_PREFIX`, `leftovers_launch` and `leftovers_fault` from `factory.adapters.agent_launch` and copies none of them; `agent_launch` still does not import `factory.adapters.process`.
```

Edit 4 (required, Interface, the tests). Replace

```markdown
The real `timeout` and `env` of the machine run under it. `tests/adapters/test_make_commands.py` is not changed.
```

with

```markdown
The real `timeout` and `env` of the machine run under it. The leftovers program is always a stand-in (`write_program` of `tests/leftovers_runtime_support.py`, which records its arguments and exits with a planned status and standard error), never the real command (`CLAUDE.md`, *Tests*). `tests/adapters/test_make_commands.py` is not changed.
```

Edit 5 (required, Acceptance criteria). Replace

```markdown
8. `MakeProjectCommands(tmp_path).user` is `None`, and `MakeProjectCommands(tmp_path, user=u).user` is `u`.
9. `make check` stays green.
10. docs:
```

with

```markdown
8. `MakeProjectCommands(tmp_path).user` is `None`, and `MakeProjectCommands(tmp_path, user=u).user` is `u`.
9. The leftovers (rows of one parametrized test, a stand-in `sudo` that runs what follows `--`, a `CommandUser` whose `os_user` is `agent` and whose `leftovers` is a stand-in program): after `check` that passes, the stand-in `sudo` records a second call whose arguments are `["-n", "-u", "agent", "--", *<the stand-in's words>, "--user", "agent"]` and whose working directory is `/`, and the result is `passed`; after `slow` killed at its limit of 3 seconds, the same second call follows and the result is `time_limit`; a stand-in program that exits 1 with `factory-leftovers: 1 processes left after 50 rounds: 7` raises `ProjectCommandError` whose `detail` is `cannot end the agent's processes: factory-leftovers: 1 processes left after 50 rounds: 7`; a `CommandUser` without `leftovers`, and one whose `os_user` is the test's own user, make one call only.
10. `make check` stays green.
11. docs:
```

Edit 6 (required, Acceptance criteria, docs). Replace

```markdown
the refusal and its `ProjectCommandError`, and that without `user` nothing changes. `docs/project-guide/agents.md`, *The shared launch module*: that the make class also starts its commands through `launch` and `killed_at_limit`.
```

with

```markdown
the refusal and its `ProjectCommandError`, the leftovers program after every command run as another user and its fault, and that without `user` nothing changes. `docs/project-guide/agents.md`, *The shared launch module*: that the make class also starts its commands through `launch` and `killed_at_limit`; *Ending the agent's leftover processes*: that a project command run as the agent's user is followed by the same program.
```

### F0040-S0002

Edit 1 (required, Interface). Replace

```markdown
user=CommandUser(os_user=settings.agent_user, sudo_executable=<the sudo which finds, or SUDO_EXECUTABLE>, environment=project_command_environment(settings, production_environment()))), git, log), git, records, clock, log)`, the same `git` and `log` the boundaries hold.
```

with

```markdown
user=CommandUser(os_user=settings.agent_user, sudo_executable=<the sudo which finds, or SUDO_EXECUTABLE>, environment=project_command_environment(settings, production_environment()), leftovers=leftovers_command() if end_leftovers else None)), git, log), git, records, clock, log)`, the same `git` and `log` the boundaries hold; the leftovers program is the one the agent runtime gets.
```

Edit 2 (required, Acceptance criteria). Replace

```markdown
whose `user` is `CommandUser(os_user="agent", sudo_executable="/usr/bin/sudo", environment=project_command_environment(settings, production_environment()))`. Without `agent_user`, it is a `RecordingProjectCommands` around a `MakeProjectCommands` whose `user` is `None`. With `which` finding no `sudo`, the user's `sudo_executable` is `SUDO_EXECUTABLE`.
```

with

```markdown
whose `user` is `CommandUser(os_user="agent", sudo_executable="/usr/bin/sudo", environment=project_command_environment(settings, production_environment()), leftovers=leftovers_command())`. With `end_leftovers=False`, the user's `leftovers` is `None`. Without `agent_user`, it is a `RecordingProjectCommands` around a `MakeProjectCommands` whose `user` is `None`. With `which` finding no `sudo`, the user's `sudo_executable` is `SUDO_EXECUTABLE`.
```

Edit 3 (required with question B's answer A, Interface). Replace

```markdown
    """The environment of a project command run as the agent user: the agent run's, no bytecode."""
```

with

```markdown
    """The environment of a project command run as the agent user: the agent run's, no bytecode, uv copying."""
```

and replace

```markdown
- `project_command_environment` is `agent_run_environment(settings, base)` with `PYTHONDONTWRITEBYTECODE` set to `1`, and nothing else added.
```

with

```markdown
- `project_command_environment` is `agent_run_environment(settings, base)` with `PYTHONDONTWRITEBYTECODE` set to `1` and `UV_LINK_MODE` set to `copy`, and nothing else added.
```

Edit 4 (required with question B's answer A, Acceptance criteria). Replace

```markdown
gives `{"PATH": "/p", "HOME": "/home/agent", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}`;
```

with

```markdown
gives `{"PATH": "/p", "HOME": "/home/agent", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "UV_LINK_MODE": "copy"}`;
```

Edit 5 (required, Acceptance criteria, docs). Replace

```markdown
with the agent run's environment and `PYTHONDONTWRITEBYTECODE=1`, so code an agent wrote never runs as `factory` and no output tail can hold the hosting token. The git folder is sealed before every command and checked after it.
```

with

```markdown
with the agent run's environment, `PYTHONDONTWRITEBYTECODE=1` and `UV_LINK_MODE=copy`, so code an agent wrote never runs as `factory` and no output tail can hold the hosting token. The git folder is sealed before every command and checked after it, and every command is followed by the leftovers program as `agent` (**The end of the agent's processes.** says so for project commands too).
```

(Without question B's answer A, drop `UV_LINK_MODE=copy` from this text.)

Edit 6 (optional, Description). Replace

```markdown
A new application class, `SealedProjectCommands`, seals the git folder before the command and checks the seal and removes nested repositories after it, as `run_sealed` does for an agent run.
```

with

```markdown
A new application class, `SealedProjectCommands`, seals the git folder before the command and checks the seal and removes nested repositories after it, as `run_sealed` does for an agent run; unlike `run_sealed` it removes no git-ignored paths, so the `.venv` and the reports a check made stay for the next command (F0027's removal follows the next agent run and the restore).
```

### F0040-S0003

Edit 1 (required, Interface). Replace

```markdown
`tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` expects `{"factory.entry.wiring", "factory.entry.confine", "factory.entry.fresh_home"}`: the program runs as the agent's user and imports its adapter directly, as `factory.entry.confine` does. Nothing else in that test changes.
```

with

```markdown
`tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` expects `{"factory.entry.wiring", "factory.entry.confine", "factory.entry.leftovers", "factory.entry.fresh_home"}`: the program runs as the agent's user and imports its adapter directly, as `factory.entry.confine` and `factory.entry.leftovers` do. Nothing else in that test changes.
```

Edit 2 (optional, Acceptance criteria, docs). Replace

```markdown
13. docs: `docs/project-guide/agents.md`, a new section *The fresh home* after *The shared launch module*:
```

with

```markdown
13. docs: `docs/project-guide/agents.md`, a new section *The fresh home* after *Ending the agent's leftover processes*:
```

### F0040-S0004

No required edit.

Edit 1 (optional, Acceptance criteria, docs). Replace

```markdown
A row in the morning observations:
```

with

```markdown
A row in the **Morning observations.** of *The kernel refuses every other write*:
```

Edit 2 (optional, Acceptance criteria, docs). Replace

```markdown
`docs/project-guide/agents.md`, *The fresh home*: who starts the program, when (after the seal, before the run, once per stage run, and before each project command),
```

with

```markdown
`docs/project-guide/agents.md`, *The fresh home*: who starts the program, when (after the seal, before the run, once per stage run, and before each project command, whose leftovers program runs after it, S0001),
```

### feature.md

Edit A (required, Scope). Replace

```markdown
- `src/factory/adapters/make_commands.py`: `CommandUser`, the keyword `user` and the property `user` of `MakeProjectCommands`, the start through `launch`, the kill by the user's own `timeout`, the `sudo` refusal (S0001).
```

with

```markdown
- `src/factory/adapters/make_commands.py`: `CommandUser` (with its `leftovers`), the keyword `user` and the property `user` of `MakeProjectCommands`, the start through `launch`, the kill by the user's own `timeout`, the `sudo` refusal, the leftovers program after every command (S0001).
```

Edit B (required, Scope). Replace

```markdown
- `src/factory/entry/wiring.py`: `project_command_environment` and the project commands built for an agent user (S0002);
```

with

```markdown
- `src/factory/entry/wiring.py`: `project_command_environment` and the project commands built for an agent user, with the leftovers program (S0002);
```

Edit C (required, Out of scope). Replace

```markdown
- A process of `agent` that outlives a run or a project command (F0027's leftovers program; see *The human's changes*, 4).
```

with

```markdown
- A process of `agent` that outlives an agent run: F0027's leftovers program ends it after every call. After a project command S0001 runs the same program (decision 16). A survivor that keeps the command's output pipe still makes the call wait until it ends by itself (the project guide's known limit, shared with the agent runtimes).
```

Edit D (required, *The human's changes*, the lease; the text for question C's answer A). Replace

```markdown
The pipeline definition needs nothing either: the `SUDO_GRACE` of 30 seconds per command keeps every stage within its lease (doing: 40 + 8 + 2 minutes plus 1 minute of grace, 51 of 60; docs: 40 + 8 + 3 + 2 plus 1.5, 54.5 of 60).
```

with

```markdown
The pipeline definition needs nothing either. A stage's declared limits stay as they are (doing: 40 + 8 + 2 minutes, 50 of 60; docs: 40 + 8 + 3 + 2, 53 of 60), and the load-time rule counts only those. In the worst case, when every kill waits for its limit, each `sudo` call adds 30 seconds of grace (`SUDO_GRACE`), each call of the leftovers program 30 seconds (`LEFTOVERS_TIME_LIMIT`) and each reset 90 seconds (`FRESH_HOME_TIME_LIMIT` and its grace): doing 57.5 of 60, docs 63 of 60. A reset takes about a second and the leftovers program less, so the real overhead is seconds per stage; a stage that overran its lease would matter only to a second instance or after a crash.
```

Edit E (optional, change 1's place). Replace

```markdown
1. Before S0003 starts, one commit on `main`. In `CLAUDE.md`, *Tests*, after the bullet that starts "No network, no sleeps, no files outside `tmp_path`", a new bullet:
```

with

```markdown
1. Before S0003 starts, one commit on `main`. In `CLAUDE.md`, *Tests*, after the bullet that starts "No test, no smoke test and no command a stage runs by hand runs `factory.entry.leftovers`" (F0027's, a rule of the same kind), a new bullet:
```

Edit F (required, change 2). Replace

```markdown
2. After S0004 is merged, one commit on `main`, on the bullet as F0041's human's change 2 left it. In `CLAUDE.md`, *Architecture*, the bullet on the agent runtime (R12): after "its tool paths and its own temporary folder;" and before "the undo after the run reverts whatever else changed outside the write paths, and no hook judges a tool call.", insert:
```

with

```markdown
2. After S0004 is merged, one commit on `main`, on the bullet as F0041's and F0027's human's changes left it. In `CLAUDE.md`, *Architecture*, the bullet on the agent runtime (R12): after "so nothing a run leaves behind reaches the checks;" and before "the undo after the run reverts whatever else changed outside the write paths, and no hook judges a tool call.", insert:
```

and, in its block, replace

```markdown
   every project command runs as the agent's user too (`sudo`, the agent's own `timeout`, `env -i`), with the checkout's git folder sealed, and every agent run and every project command starts from a fresh agent home
```

with

```markdown
   every project command runs as the agent's user too (`sudo`, the agent's own `timeout`, `env -i`), with the checkout's git folder sealed, and is followed by the same end of the agent's processes; every agent run and every project command starts from a fresh agent home
```

Edit G (optional, a third change in the commit of change 1). After change 1's block, add:

```markdown
   In the same commit, in F0027's bullet "No test, no smoke test and no command a stage runs by hand runs `factory.entry.leftovers` ...", replace "(and under `make check`, the factory)" with "(and under a project command, the check itself)", and "A runtime test passes a stand-in program as `leftovers`" with "A runtime test and a make-commands test pass a stand-in program as `leftovers`": after S0002 `make check` runs as `agent`, and S0001's tests pass the program too.
```

Edit H (required, check 3.7). Replace

```markdown
   7. A check that reaches its time limit leaves no `make` of `agent`: `ps -o user,pid,args -U agent` after it (see *The human's changes*, 4, F0030).
```

with

```markdown
   7. A check that reaches its time limit leaves no process of `agent`: `docker exec factory-self-factory-1 ps -o user,pid,args -U agent` after it prints only the header (the user's `timeout` ended its group, the leftovers program the rest; decision 16).
```

Edit I (required, point 4). Replace the three bullets **F0030**, **F0027** and **F0041** of point 4, and its lead-in, that is

```markdown
4. **The drafts in `planning/overnight/stories/`**, the human's files, before they are built. The clashes, with what to change:
```

up to and including the bullet that ends "F0041's operator check on the transcripts is done before S0004 is merged.", with

```markdown
4. **The other features, as built on 2026-10-20.** Nothing in them is to change; what they mean for this feature:

   - **F0030** (*A command stopped at its time limit leaves no process running*): S0001 is built. Its session kill leaves out every process the factory may not signal (its decision 4), so it ends nothing of a call under `sudo` (tried in a throwaway container on 2026-10-20: a `sudo` call over its limit ran on until its `agent` child ended by itself). After S0001 here, the kill of a project command at its limit is the user's own `timeout`: it ends `make` and its process group (recipes, `uv`, pytest and its workers), not a process in a group or session of its own (a child a test starts through `run_process`, the `mutants` recipe's own `timeout`). The leftovers program after every project command ends those (decision 16). F0030-S0002 and F0030-S0003, proposed by its acceptance, wait in its backlog: S0003's text on the factory's kill of `make mutants` holds for an instance without an agent user only; if it is built after S0002, its documenter should say that with an agent user the user's `timeout` kills instead.
   - **F0027** (*Nothing a run leaves behind reaches the checks*), built. Its leftovers program runs after every call of an agent runtime, not after a project command; decision 16 adds that. Its `git clean -X` as `factory` removes what a project command wrote as `agent`, because `sudo`'s umask `0002` makes every folder group-writable in the group `factory-work` (tried: `.venv`, `.reports`, `.mypy_cache`, exit 0). A folder made under the tests' umask `022` or by `mkdtemp` would stop it (exit 1): no make target makes one, and `PYTHONDONTWRITEBYTECODE=1` (decision 5) keeps every `__pycache__` out. Its out-of-scope line on `~/.cache/*` ("the checks run as `factory`") no longer holds after S0002; S0004 closes it but for uv's kept cache (decision 9).
   - **F0041** (*The old hook guard is removed*), built. No story here relies on what it removed. Its R12 sentence and F0027's are in `CLAUDE.md` now; change 2 inserts after F0027's.
```

Edit J (required, decision 2). Replace

```markdown
The make class calls `launch`, `killed_at_limit` and `SUDO_GRACE` of `factory.adapters.agent_launch`,
```

with

```markdown
The make class calls `launch`, `killed_at_limit`, `SUDO_GRACE`, `leftovers_launch` and `leftovers_fault` of `factory.adapters.agent_launch`,
```

Edit K (required with question B's answer A, decision 5). Replace

```markdown
5. **The command's environment is the agent run's, plus `PYTHONDONTWRITEBYTECODE=1`, and no login** (S0002).
```

with

```markdown
5. **The command's environment is the agent run's, plus `PYTHONDONTWRITEBYTECODE=1` and `UV_LINK_MODE=copy`, and no login** (S0002).
```

and replace

```markdown
the bytecode switch is what the image's `ENV` gave make so far.
```

with

```markdown
the bytecode switch and the link mode are what the image's `ENV` gave make so far. The bytecode switch keeps every `__pycache__` out of the checkout, also one a pytest process would make under the tests' umask `022`, which F0027's `git clean -X` as `factory` could not remove. Without the link mode uv tries hard links from `~/.cache/uv` into `.venv`, which lie on different file systems, and prints a three-line warning into the output of every sync (tried 2026-10-20).
```

Edit L (required, decision 14). Replace

```markdown
expects `{"factory.entry.wiring", "factory.entry.confine", "factory.entry.fresh_home"}`: the program runs as the agent's user and imports its adapter directly, as `factory.entry.confine` does,
```

with

```markdown
expects `{"factory.entry.wiring", "factory.entry.confine", "factory.entry.leftovers", "factory.entry.fresh_home"}`: the program runs as the agent's user and imports its adapter directly, as `factory.entry.confine` and `factory.entry.leftovers` do,
```

Edit M (required, a new decision after 15). Add:

```markdown
16. **Every project command run as the agent is followed by the leftovers program** (S0001, S0002). The user's `timeout` kills only its own process group, and the factory's kill cannot signal the agent's processes (F0030's decision 4), so a process that took a group or a session of its own outlives the check; this repository's tests start every child in a session of its own (`run_process`). F0027 runs the program after every call of an agent runtime only, which would leave such a process running through the next reset and the next checks. The make class starts it as the runtimes do, through `leftovers_launch`, never for the factory's own user, and a fault of it is a `ProjectCommandError`. Options: A, this, in S0001 and S0002 (recommended); B, a story of its own after S0002; C, none, leaving the process to the next agent call.
```

## Questions for the human

Independent ones first.

**A. Where the leftovers program after a project command goes.** The time-limit kill misses every process that left the user's `timeout` group, and nothing ends it until the next agent call.

- A: S0001 adds `CommandUser.leftovers` and the call after every command, S0002 wires `leftovers_command()` (edits S0001-1 to 6, S0002-1, 2 and 5, feature A to C, H to J and M). Pro: one place, the same program and fault text as the runtimes, tests reuse F0027's helpers. Con: S0001 grows by one rule and one criterion.
- B: a fifth story after S0002. Pro: S0001 stays as reviewed. Con: one more story, and S0002 merges with the gap open until it lands.
- C: nothing; the next agent call ends the survivors. Con: they run through S0004's reset and the next checks, as `agent`.

Recommendation: A.

**B. `UV_LINK_MODE=copy` in the project commands' environment.**

- A: add it (edits S0002-3 to 5, feature K). Pro: what make has today; no hard-link attempt and no warning in every sync. Con: one more variable beside the allow list.
- B: leave it out. Con: uv's three warning lines in the output of every check that syncs `.venv`, which after F0027-S0003 is every first check after a run.

Recommendation: A.

**C. The worst-case time of a stage.** With a reset before every run and command and the leftovers program after every command, the worst case of the docs stage is 63 minutes against a lease of 60.

- A: keep `FRESH_HOME_TIME_LIMIT` at 60 seconds and write the worst case honestly (edit D). Pro: the first reset of 222 MB has room; a reset that needs its limit has failed anyway and raises. Con: the sentence admits a theoretical overrun.
- B: `FRESH_HOME_TIME_LIMIT` 10 seconds (docs worst case 59.7 of 60). Con: the first reset after the upgrade may need more on a slow disk and would then stop one run (the next reset goes on where it ended).

Recommendation: A.

**D. A survivor that holds the output pipe.** `run_process` waits for the pipe to close, and no kill bounds that wait when the holder runs as `agent` (prototype 1, third row). This is the project guide's known limit and holds for the agent runtimes too.

- A: leave it as a known limit, out of scope (edit C says so). Pro: no change to the process module or to earlier tests; pytest captures every test's output in files, so a test's child does not hold the pipe.
- B: a later feature bounds the wait for every call under `sudo` (for example `run_streaming`, which returns at the deadline). Con: touches the process module and the runtimes.

Recommendation: A now, and B as a note for a later feature.

## Side finding (not F0040's)

In prototype 1, last row, `_kill_session` raised no `PermissionError` at `os.killpg` on the group of a `sudo` call, although `docs/project-guide/processes-and-checks.md`, *Killing a session*, says a `PermissionError` (under `sudo`) propagates. The call simply waited for the `agent` child. Worth a look by F0030's documenter; F0040 does not depend on it.

## The human's answers

- Question A: answer A, the leftovers program after every project command, in S0001 and wired in S0002 (feature decision 16) (the human, 2026-10-20).
- Question B: answer A, `UV_LINK_MODE=copy` in the project commands' environment (feature decision 5) (the human, 2026-10-20).
- Question C: answer A, `FRESH_HOME_TIME_LIMIT` stays 60 seconds and the worst case is stated as it is (feature, *The human's changes*) (the human, 2026-10-20).
- Question D: answer B, not as recommended: F0040 itself bounds the wait for a survivor that holds a call's output pipe, for every call under `sudo`, the agent runtimes included (the human, 2026-10-20).

What was applied to the drafts: every required edit above and the edits of the answers (S0001 1 to 6, S0002 1 to 5, S0003 1, feature A to D, F, H to M, with C, D, I and M widened for answer D). The optional edits (S0002 6, S0003 2, S0004 1 and 2, feature E and G) were not applied.

### S0005, for answer D

A new story, `F0040-S0005`, *A call no longer waits for a process that keeps its output open after the call's own process ended*, built third (after S0002, before S0003 and S0004; its number is the order it was drafted in). It changes `factory.adapters.process` only: `run_process` and `run_streaming` check every 0.05 s whether the child has ended; once it has, they read on for at most `PIPE_DRAIN` (5 s), then close the pipes and return the child's own exit status, the output read and the new field `ProcessResult.output_abandoned` (default false, last). After its kill at the limit, `run_process` reads for at most the same 5 s instead of without a limit. `run_streaming` after a kill, a stop or an error is unchanged. The rule is for every call, not only for calls under `sudo`: one rule is simpler than a switch, and no caller needs the old wait.

**Prototype** (a throwaway container of `factory-self-factory`, `--network none --cpus 2`, the copy's `src` with `run_process` rebuilt on the module's `_LineReader` and a polling `_read_until_end`, about 40 lines):

| Call | Result | Returned after |
|---|---|---|
| child `echo done` beside a `setsid sleep 60` that holds stdout | exit 0, not timed out, abandoned | 5.0 s |
| plain `echo a; echo b`; `seq 1 200000` | exit 0, all output, not abandoned | 0.0 s |
| a line written 2 s after the child's end | kept, not abandoned | 2.0 s |
| as `agent` under `sudo`, the S0001 chain, `echo done` beside a holder | exit 0, abandoned | 5.1 s |
| as `agent`, inner kill at 3 s beside a holder of 60 s | exit `-9` (read as `time_limit` by `killed_at_limit`), abandoned | 8.0 s (12 s and more today) |
| as `agent`, inner kill at 3 s, no holder | exit `-9`, not abandoned | 3.0 s |

With the prototype in place, every test of `tests/adapters/test_process*.py`, `test_claude_runtime*.py`, `test_opencode_runtime*.py`, `test_make_commands*.py`, `test_agent_launch*.py`, `test_git_cli*.py`, `tests/application/test_sealed_runs.py` and `tests/test_process_search.py` passed unchanged (pytest from the host's pure-Python packages). So S0005 needs no leave. The smoke test's shell quoting was tried on today's code (which waited for the holder instead). Size: one module, about 40 lines, one new test module of five criteria; it fits one coder's 40 minutes.
