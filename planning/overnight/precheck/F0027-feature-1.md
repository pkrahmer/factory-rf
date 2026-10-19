# Pre-check F0027, round 1: the feature, its human's changes and its decisions

I checked the feature `F0027-nothing-a-run-leaves-behind-reaches-the-checks` and its four stories against these sources:

- v1.1's roles and forms: `claude/agents/*.md`, `factory/story-form.md`, `factory/feature-form.md`;
- `factory/pipeline.yml`, `CLAUDE.md`, the `Makefile`, `pyproject.toml` and the image (`image/Dockerfile`, `sudoers-factory-agent`, `entrypoint.sh`, `compose.yml`);
- the code each story touches;
- F0020 (S0008 in progress; `wiring.py` already builds either runtime), F0023 and F0024 as drafted and pre-checked.

I built prototypes of S0001 to S0004 in a copy in the temporary folder. I ran the whole suite (with the S0001 to S0003 prototypes in), the smoke tests and probes in throwaway containers of v1.1's image (`--network none`, `--cpus 1`, no volume, no secret), one at a time. I ran mypy cold and warm on the host. The stories' results are in `F0027-S0001-1.md` to `F0027-S0004-1.md`.

## The stories in short

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 the program | question: "without repeats" has no row | coder stops at `test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` (no leave); smoke block 3 prints `<Signals.SIGKILL: 9>` |
| S0002 the runtimes | question: a raised call, `version()`, the opencode row | coder stops: the criteria's `os_user` `agent` is the tests' own user in a stage, so the program never runs there |
| S0003 the removal | question: `run_sealed`'s `GitError` | the story itself is fine; after the rebuild the instance stops at the first `make test` of an agent (point 1) |
| S0004 kept folders | question: two clauses without rows | coder stops: git 2.39.5 removes `mutants/` when the pathspecs hold `mutants-old/` and one more entry |

All four pass `factory-check-story`.

## The two routes (decision 1): confirmed

- **Ignored state.** S0003's smoke test 2 on today's code leaves `.venv/lib/standin.pth`, the `.pyc` and the hidden `tests/hidden/conftest.py` in the checkout after `run_sealed`. With the prototype they are gone, and the untracked `src/new.py` stays.
- **A leftover process.** A `setsid sleep` and a `nohup sleep` of `agent` lived on after their `sudo` call ended. A stand-in program run as `agent` through the image's `sudo` rule (`os.kill(-1, SIGKILL)`) ended both. It survived itself and exited 0, `sudo` returned its status, and the factory's processes stayed.

## Points for the human, with recommended answers

### 1. What the agent leaves cannot be removed by the factory (blocking for S0003)

The removal runs as the factory's user and reaches the agent's files only through the group `factory-work`. The image relies on `sudo`'s `umask=0002` for that, and the operator guide says so: a `755` folder of the agent's makes the restore fail. factory-rf's own recipes undo it:

- `make test` and `make mutants` set `umask 022`;
- a `python -I` child (S0001's criterion 11, and every isolated child after it) writes `__pycache__` despite `PYTHONDONTWRITEBYTECODE`.

Measured in a throwaway container, as `agent` under `umask 022`:

- `uv venv .venv`, `mkdir -p mutants/src` and a `python -I` import made `drwxr-sr-x agent` folders;
- `git clean --quiet --force --force -d -X` as the factory then exited 1 with `Permission denied` for every file in them.

Today nothing removes ignored state, so this never showed. After S0003 every stage starts without `.venv`. The tester's and the coder's first make target is `make test` (`tester.md` step 2; `coder.md`, "Start by running `make test`"), which builds `.venv` under `022`. So the first tests stage after the rebuild ends with `iteration failed: GitError`, and the next restore stops the repository with `checkout_restore_failed`. Unattended, that costs a night.

- **a (recommended):** a new story, built between S0002 and S0003, in which the runtime opens what the agent made in the checkout for the group after every call. It runs as the run's user, after the leftovers program (so no agent process can race it) and before the temporary folder's removal, in the same way `CLEANUP_SCRIPT` already opens the temporary folder: `sudo -n -u <user> -- /bin/sh -c 'chmod -R g+rwX -- "$1" 2>/dev/null; exit 0' factory-open <working directory>`, status not read.
  - Prototype in the container: it took 4 ms. It opened a `755` and a `0555` folder of the agent's. GNU `chmod -R` did not follow a link to an agent folder outside (it stayed `700`), and it left the factory's own `.git` as it was. `git clean` then exited 0.
  - It is generic: any project's tool, any umask, a folder the agent closed on purpose.
  - It also closes the gap decision 11 accepts for an untracked agent folder in a write path.
  - It touches only `agent_launch` and the two runtimes' `_call`, beside S0002's lines, and is tested with the stand-in `sudo` and with the script run as the tests' own user on `tmp_path`.
  - The crash case (the factory killed during a run) is still left to the stop, which is rare.
- **b:** the human's changes only: in the `Makefile`'s `test` and `mutants` recipes, `uv run --quiet true` before `umask 022`, and `chmod -R g+rwX mutants` in the `mutants` trap; `-I -B` in S0001's criterion 11. It is cheaper, but brittle: every later recipe, tool or isolated child that writes under a stricter mode stops the instance again.
- **c:** accept the stops. Not recommended.

### 2. A kept `mutants/` is code the factory runs (decision 3)

Decision 3's claim "No check reads `mutants/`" holds. But F0024 makes `make mutants` a report that the factory runs after the coder, as the factory's user. mutmut 3.8:

- runs the tests inside `mutants/`;
- puts `mutants/src` first on `sys.path`;
- keeps a copied source file that already exists (`copy_src_dir`);
- copies `tests/` over `mutants/tests` without removing extra files.

So with S0004 and change 3, a `conftest.py` that any role left in `mutants/tests/` (a tool path for every role) runs at the next story's report, hidden from the diff. That is the route this feature closes for the checks, reopened for a report.

- **a (recommended):** answer A, together with an addition to F0024's change 1 recipe, before its `mutmut run`: `find mutants -type f ! -name '*.meta' ! -name 'mutmut-stats.json' -delete 2>/dev/null || true`. Then what mutmut runs is copied fresh from git, and only its JSON results and stats carry over. Whether mutmut 3.8 keeps a result whose mutated copy it regenerates is F0024's to check in its next pre-check.
- **b:** answer A with `mutants/*` moved out of `tool_paths` into the acceptance reviewer's `write_paths`, the only role that runs mutmut. This narrows the route but does not close it.
- **c:** answer B or C.

Without F0024, decision 3's answer C stands (S0004 moved out of `backlog/` unbuilt).

### 3. The order

- **F0020:** start after it is archived. That is right, and S0002 then needs the opencode row (S0002 edit F), since `build_boundaries` already picks `OpencodeRuntime` by `agent_runtime`.
- **F0023:** either order works. Both add a `Git` operation (`twenty_four` or `twenty_five`) and raise the records contract's minor (`1.3` or `1.4`), and decision 16 and S0004 already say "from the value it holds when the story starts".
- **F0024:** if F0024's change 2 (the `mutants` report) is already in force, S0003's rebuild must be followed at once by S0004, its rebuild and change 3. Otherwise every restore removes `mutants/` before the reviewer reads it. If F0027 goes first, F0024's change 2 waits for F0027's change 3. F0024's recipe also needs point 1 (answer b), or answer a in force: its `umask 022` and `mutants/` folders are the agent's at the acceptance.

Recommended: F0020, then F0027 (S0001, S0002, the new story of point 1, S0003, S0004, change 3), then F0024's change 2.

### 4. The cost of the removal (decision 4): accept

Measured offline in the image from a warm uv cache, one CPU, copy mode:

- the image's no-dev environment (36 MB, 913 files) took 0.37 s to build and 0.04 s to sync again;
- scaled by files to factory-rf's development environment (7,610 files), that is about 3 s per build, so about 6 s per stage with checks (the agent's build and the factory's).
- mypy over the 571 files of `src` and `tests`, on the host, took 6 s cold and 1 s warm, so about 5 s more per `make check`, since `.mypy_cache` goes too. import-linter's cache adds a little.

So the removal costs well under half a minute per stage against a `make check` of about 46 s, roughly a minute or two per story. On top come one full download for each user after every rebuild of `self` (both uv caches lie in the container's layer) and, without kept `mutants/`, mutmut's cold start per run (F0024 measured 131 s).

The agent's runs have no `UV_LINK_MODE=copy` (the image's variable reaches only the factory), so each `uv run` without `-q` that builds `.venv` prints uv's hardlink warning. It is harmless, and the engine should not learn uv's variables (R8, R11).

### 5. The human's change 1 is too narrow

It forbids running the program as its own user in tests and smoke tests, but not by hand in a stage. A coder who tries `python -m factory.entry.leftovers --user agent` "to see it work" ends its own run.

Recommended (edit B): name the stages too.

### 6. The human's change 4, step 2, cannot show its expected line

Step 1's command sends the program's standard error to `/dev/null`, and step 2 is "the same container" with only `--user` changed. So `factory-leftovers: runs as agent, not factory` never appears. Under `--network none` every `sudo` call also prints `sudo: unable to resolve host <id>` (seen).

Recommended: edit C.

### 7. The 30-second limit of the program (decisions 9 and 11)

At the limit, the factory's kill of the process group ends `sudo`, whose real uid is the factory's (seen: `killpg` succeeded and `sudo` died). It cannot end the program running as `agent`, so `run_process` then waits for the program to close its output. The program's own 50 rounds are the real bound, and `no end within 30 s` is reported after that. An inner `timeout` would not help: the program's `kill(-1)` would kill it, since it is the program's parent and runs as `agent`.

Recommended: S0002's optional edit G records this.

Beside the feature: the operator guide's sentence "The factory cannot signal `sudo`, which is owned by root" (paragraph *A `time_limit` under `sudo`*) is not what I saw. The factory can signal `sudo`, just not the agent's processes under it. The conclusion of that paragraph holds.

### 8. No test or smoke test runs the program as the tests' or the factory's user

- S0001's tests inject `kill`, `processes`, `identity` and `sleep`, and its one child names `factory-test-nobody`.
- Smoke blocks 1 and 2 stop at the usage line and the refusal (seen), and block 3 injects everything.
- S0002's tests and smoke test pass a stand-in program.
- No existing test runs a real runtime with an OS user: the ticks with `agent_user="agent"` use the fake runtime, and the wiring tests call `_request(tmp_path, None)`.
- A slip still refuses rather than kills: a stand-in `sudo` does not switch users, and the program refuses unless it runs as the user it is told.

Decision 10 holds.

### 9. `git clean -ffdX` cannot remove what the factory needs

- The instance's state (`/state`), the agent's home (`/home/agent`), the factory's home and its interpreter (`/opt/factory/.venv`, which the agents' `PATH`, the guard hook and `factory-confine` use) all lie outside `/work/checkout`.
- In the checkout, every target of `make check`, `duplicates` and `documents` reaches `.venv` only through `uv run`, which builds it first. `licenses` runs `uv export --frozen` (no environment) before its `uv run`.
- The factory's own files in the checkout (work items, `.costs.jsonl` sidecars, `factory/stops.jsonl`) are tracked or untracked-and-not-ignored, which `-X` keeps.
- Nothing of the factory reads `.reports/` across stages: the acceptance reviewer reads `junit.xml` from its own `make test`.

## The decisions

1. **Confirmed** (above).
2. **Remove, not verify:** right; answer A.
3. **`mutants/` across stages:** A only with point 2's addition.
4. **The cost:** accept (point 4).
5. **Where the removal runs:** right. The restore's order before the switch is needed for a branch's own `.gitignore` (S0003's criterion 6, seen in the prototype's suite run).
6. **`git clean -ffdX`:** right for S0003. For S0004, see decision 13.
7. **Un-ignoring is accepted:** right; the result shows in the diff.
8. **`kill(-1)` as the agent:** right; answer A. The agent's user must serve agent runs only. That now includes an operator's `docker exec -u agent` shell, which the next call ends (S0002 edit E).
9. **A module run through the one `sudo` rule:** right (point 7 for the limit).
10. **The three guards:** right (point 8).
11. **Fail closed:** right; answer A. Point 1 is what keeps "a folder the factory cannot empty" from being the normal case.
12. **The order after a call:** right. With point 1(a) it becomes the call, the program, the opening, the removal.
13. **`kept_ignored`'s listing:** wrong for git 2.39.5. Replace it by negated `-e` patterns (S0004 edit 1, with the replacement text of this decision).
14. **The records contract:** right.
15. **F0020, F0023, F0024, F0026:** right, with point 3's order.
16. **The leaves:** S0001 needs one: `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` (edit F). The others are confirmed by the suite run: exactly S0003's three tests change.
17. **Sizing:** each story fits 40 minutes. The new story of point 1(a) is smaller than S0002.
18. **Testing:** right.

## Verdict

Not to be built as drafted: point 1 blocks S0003, and every story is refused at intake. It is buildable with the stories' edits and edits A to F below, once points 1 and 2 are answered.

Edit A (required, *Stories*, on answer a of point 1): the list becomes

```markdown
- S0001: A program ends every other process of the user it runs as
- S0002: The agent runtimes end the agent's leftover processes after every call
- S0005: The agent runtimes open the agent's files in the checkout for the factory after every call
- S0003: The factory removes the git-ignored files after every agent run and at the restore
- S0004: A project keeps the ignored folders it names (only on the answer A of decision 3; otherwise move it out of `backlog/` unbuilt)
```

Add a decision 19 (S0005 is to be drafted from it):

```markdown
19. **The factory can remove what the agent made** (S0005). The removal runs as the factory's user and reaches the agent's files through the group alone; `sudo`'s umask `0002` makes them group-writable, but a project command can set a stricter one (factory-rf's `make test` and `make mutants` set `022`), and a `python -I` child writes bytecode despite `PYTHONDONTWRITEBYTECODE`: in the pre-check, `git clean -ffdX` as `factory` then failed with `Permission denied` on the agent's `755` folders. So after the leftovers program and before the temporary folder's removal, the runtime runs, as the run's user, `/bin/sh -c 'chmod -R g+rwX -- "$1" 2>/dev/null; exit 0' factory-open <working directory>` through the one `sudo` rule (`opening_launch` in `factory.adapters.agent_launch`, time limit 60 s), whenever it ran the program; its status is not read. GNU `chmod -R` does not follow a symbolic link met in the walk, and the factory's own files, `.git` among them, are not the agent's to change. The order after a call is the call, the program, the opening, the removal.
```

Edit B (required, the human's change 1): in the bullet, "No test and no smoke test runs `factory.entry.leftovers` as the user it names" becomes "No test, no smoke test and no command a stage runs by hand runs `factory.entry.leftovers` as the user it names".

Edit C (required, the human's change 4, step 2): replace with

```markdown
   2. In a new throwaway container of the same kind, with the stand-in `sleep` started as in step 1: `MSYS_NO_PATHCONV=1 docker run --rm --init --network none --entrypoint /bin/sh factory-self-factory -c 'sudo -n -u agent -- sh -c "setsid sleep 300 >/dev/null 2>&1 </dev/null &" 2>/dev/null; cd / && sudo -n -u agent -- /opt/factory/.venv/bin/python -I -m factory.entry.leftovers --user factory 2>&1 | grep -v "unable to resolve host"; ps -h -U agent | wc -l'`. Expected: `factory-leftovers: runs as agent, not factory`, then `1` (the stand-in `sleep` is still there).
```

Edit D (required, *Out of scope*, on answer a of point 2): after the bullet "A folder an agent makes that the factory cannot empty: ..." insert

```markdown
- What F0024's `mutants` report runs from a kept `mutants/`: F0024's recipe deletes every file there but mutmut's results before `mutmut run` (pre-check of F0027, point 2).
```

Edit E (required, decision 13): from "The removal lists the ignored entries" to "listed only the file `[a].log`." becomes the replacement text in `F0027-S0004-1.md`, edit 1.

Edit F (required, decision 16): "S0001 and S0002: none. Every existing runtime test ..." becomes

```markdown
- S0001: `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer`, whose expected set `{"factory.entry.wiring", "factory.entry.confine"}` gains `"factory.entry.leftovers"`; its name and every other line stay. S0002: none. Every existing runtime test ...
```

The rest of that bullet stays.
