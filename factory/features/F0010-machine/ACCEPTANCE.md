---
stage: accept
pr: 142
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0010-S0001, F0010-S0002, F0010-S0003, F0010-S0004, F0010-S0005, F0010-S0006, F0010-S0007, F0010-S0008, F0010-S0009, F0010-S0010, F0010-S0011, F0010-S0012, F0010-S0013, F0010-S0014, F0010-S0015, F0010-S0016, F0010-S0017, F0010-S0018, F0010-S0019, F0010-S0020, F0010-S0021, F0010-S0022]
---
# Acceptance of The machine

## Verdict

**accepted with drafts**, as a recommendation. This is the second acceptance of the feature. The first was `not accepted` and proposed S0018 to S0022, and all five are archived and do what they promised:

- the README and the guides no longer announce the machine as future work;
- `factory-run` ends with status 2 and two lines on standard error, not a traceback, when `/state` cannot be written;
- the shipped settings deny `git add` and `git commit`;
- the two surviving mutants of the first pass are now killed.

The feature demo is green end to end, `make check` is green, and a new hand mutation pass killed 11 of 12. Two small things remain, each with a draft. One sentence of the operator guide says the first pause is always 30 seconds, while a first tick with activity pauses 15 seconds. I judge that low weight: it misstates a timing, and no operator action depends on it. If the human holds it to be a misleading contradiction, `not accepted` is the verdict for the same report. The other is one surviving mutant on the `sudo:` line rule.

## 1 Scope

None. The table of the first acceptance (scope item → stories → code) still holds, and the five repair stories stayed inside the scope:

- **S0018.** Documentation only: `README.md`, `docs/operator-guide.md`, `docs/project-guide.md`.
- **S0019.** `_report_the_invalid_settings` in `src/factory/entry/run.py`, under "The boundaries … the run".
- **S0020.** `claude/settings.json`, under "the settings … each key with an effect". It closes the near-miss the first acceptance found.
- **S0021 and S0022.** Tests only, in `tests/application/test_scheduler.py` and `tests/adapters/test_claude_runtime_os_user.py` (plus `Step.stdout_before_wait` in `tests/adapters/claude_stand_in.py`, FEATURE decision 37).

The Goal's conditions are each shown by a test, or, for Docker, root and the second user, by a static test of the files plus the morning observations the operator guide lists. Out of scope stayed out:

- no watchdog;
- no preflight of the project's setup or the token's expiry;
- no sandbox;
- the project commands still run as `factory` (decision 24);
- no `time_limit` enforced under `sudo` (decision 30, open);
- no skill file.

## 2 Feature demo

**Green.** The walk is the first acceptance's operator walk, run again unchanged, with three sections added for what S0019, S0020 and S0021 built. It covers:

- the image's environment and the settings read from it;
- one instance's loop through `Scheduler`, `RepositoryWaiter`, `CheckoutPreparer` and one `build_tick` tick for the whole run, with `activity` as `activity_tick` applies it;
- the container's health check after each step.

It runs against:

- a real bare remote with a human clone;
- the shipped `claude/` copied into the agent home;
- the template's pipeline definition;
- the production `build_boundaries`, with `FakeHostingService` given as `hosting` and `FakeAgentRuntime` in place of `claude -p`.

The settings' fixed `/work/checkout` and `/state` are moved into a temporary directory, as the tests do. The script lies outside the repository (`/tmp/f10demo2/demo.py`, the guard refuses other paths). It is the first acceptance's script, which is pasted in that report's section 2, with these lines appended:

```python
print("== 5. factory-run with a state directory it cannot write ==")
blocker = tmp / "file"; blocker.write_text("x")
out, err = io.StringIO(), io.StringIO()
with redirect_stderr(err), redirect_stdout(out): code = run.main(bad, state_directory=blocker / "state")
print("   factory-run exit:", code, "| stdout:", out.getvalue().strip()[21:], "| stderr:", err.getvalue().strip().replace(str(tmp), "<tmp>").splitlines())

print("== 6. the loop survives a git error and an OSError in the tick ==")
from factory.domain.errors import GitError
errs = [GitError("git fetch origin", 128, "could not read from remote"), OSError("disk full")]
def failing_tick():
    raise errs.pop(0)
sl = []
logged = io.StringIO()
with redirect_stdout(logged):
    Scheduler(prepare=lambda: True, tick=failing_tick, sleep=sl.append, should_stop=lambda: len(sl) >= 2, log=b.log).run()
print("   sleeps:", sl, "| log:", [l[21:] for l in logged.getvalue().strip().splitlines()])

print("== 7. the shipped settings refuse git add and git commit ==")
import json
perm = json.loads((REPO / "claude/settings.json").read_text())["permissions"]
print("   allowed git:", [p for p in perm["allow"] if "git" in p], "| denied add/commit:", [p for p in perm["deny"] if "add" in p or "commit" in p])
```

```bash
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 uv run python /tmp/f10demo2/demo.py 2>&1 | sed "s|/tmp/tmp[a-z0-9_]*|<tmp>|g"
```

```text
== 1. settings from the environment ==
instance: factory-1 | checkout: /work/checkout | state: /state | image: build-1 | agent user: agent
git environment: {'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_0': 'credential.helper', 'GIT_CONFIG_VALUE_0': '/usr/local/bin/git-credential-factory', 'GIT_CONFIG_KEY_1': 'core.sharedRepository', 'GIT_CONFIG_VALUE_1': 'group'}
== 2. the loop: reclone, preflight, a stage, idle, red main, fix, dead key, reclone ==
   tick 1: event=run dispatch=handled stopped=None -> activity=True
   sleep 15 s
   requests so far: [('coder', 'agent', datetime.timedelta(seconds=120)), ('intake', 'agent', datetime.timedelta(seconds=2400))]
   stage run environment names: ['HOME', 'LANG', 'PATH'] | token in it: False
   stamp: {"image":"build-1","main_probed":"<the 40-character commit of main>","main_failed":null}
   tick 2: event=ask dispatch=handled stopped=None -> activity=True
   sleep 15 s
   -- human pushes a red lint to main --
2026-10-16T20:09:42Z stop repository main_branch_failing: lint is red on main at 0babef56879c: E501 line too long
   tick 3: event=None dispatch=None stopped=main_branch_failing -> activity=False
   sleep 30 s
   factory-health exit 1: 'main_branch_failing (repository): lint is red on main at 0babef56879c: E501 line too long (since 2026-10-16T20:09:42Z)'
   -- human pushes the fix --
2026-10-16T20:09:42Z stop cleared main_branch_failing
   tick 4: event=idle dispatch=handled stopped=None -> activity=False
   sleep 60 s
   factory-health exit 0: 'healthy'
   -- operator's coder.md gains a dead key `skills: [x]` --
2026-10-16T20:09:42Z stop repository agent_definition_invalid: coder: key not applied by the agent runtime: skills
   tick 5: event=None dispatch=None stopped=agent_definition_invalid -> activity=False
   sleep 120 s
   factory-health exit 1: 'agent_definition_invalid (repository): coder: key not applied by the agent runtime: skills (since 2026-10-16T20:09:42Z)'
   -- coder.md restored; the checkout is deleted --
2026-10-16T20:09:42Z stop cleared agent_definition_invalid
   tick 6: event=idle dispatch=handled stopped=None -> activity=False
   sleep 120 s
   checkout recloned: True | factory-health exit 0: 'healthy'
pauses: [15, 15, 30, 60, 120, 120] | agent runs: ['coder', 'intake']
== 3. a new image build: the machine items run again; sudo missing ==
2026-10-16T20:09:42Z stop machine preflight_failed: tool:sudo: sudo is not on the PATH; add it to the image
   stopped: preflight_failed | agent runs started by the preflight: 1
   factory-health exit 1: 'preflight_failed (machine): tool:sudo: sudo is not on the PATH; add it to the image (since 2026-10-16T20:09:42Z)'
2026-10-16T20:09:42Z stop cleared preflight_failed
   with sudo: stopped: None | factory-health exit 0: 'healthy'
== 4. factory-run and factory-watch with an invalid environment ==
   factory-run exit: 2 | factory-health exit 1: 'preflight_failed (machine): FACTORY_INSTANCE: missing (since 2026-10-16T20:09:42Z)'
   log tail: 2026-10-16T20:09:42Z settings invalid: FACTORY_INSTANCE: missing
   factory-watch exit: 2 | stderr: factory-watch: settings invalid: FACTORY_INSTANCE: missing
== 5. factory-run with a state directory it cannot write ==
   factory-run exit: 2 | stdout: settings invalid: FACTORY_INSTANCE: missing | stderr: ['factory-run: settings invalid: FACTORY_INSTANCE: missing', "factory-run: cannot write the machine stop: NotADirectoryError: [Errno 20] Not a directory: '<tmp>/file/state'"]
== 6. the loop survives a git error and an OSError in the tick ==
   sleeps: [30.0, 60.0] | log: ['iteration failed: GitError: git fetch origin failed (exit 128): could not read from remote', 'iteration failed: OSError: disk full']
== 7. the shipped settings refuse git add and git commit ==
   allowed git: ['Bash(git status*)', 'Bash(git diff*)', 'Bash(git log*)', 'Bash(git show*)', 'Bash(git rev-parse*)'] | denied add/commit: ['Bash(git add*)', 'Bash(git commit*)']
```

(The probed commit in the stamp is replaced by a placeholder, so that `make secrets` does not flag a high-entropy string.) What the walk shows:

- Every step of the first acceptance's walk is unchanged: the preflight and its stamp, runs as `agent` with no token in their environment, a red main as a stop that a fix clears, a dead agent key as a stop, the reclone, the pauses following activity, a new image re-running the machine items, a missing `sudo` as a machine stop.
- **Step 5 (S0019).** An unwritable state directory now gives status 2, the time-stamped line on standard output and two `factory-run:` lines on standard error.
- **Step 6 (S0021).** A `GitError` and an `OSError` from the tick are one log line each and count as idle, and the loop goes on.
- **Step 7 (S0020).** The shipped settings allow only the read git commands and deny `git add` and `git commit`.

Note the first pause in step 2: the first tick ran the intake stage, and the pause after it is 15 seconds. The operator guide says the first pause is 30 seconds whatever the tick found (section 5).

The same commands outside the image, from a shell with an empty environment, the README's getting-started path:

```bash
env -i PATH="$PATH" HOME="$HOME" uv run factory-run; echo "factory-run exit=$?"
env -i PATH="$PATH" HOME="$HOME" uv run factory-watch; echo "factory-watch exit=$?"
env -i PATH="$PATH" HOME="$HOME" uv run factory-health; echo "factory-health exit=$?"
```

```text
2026-10-16T20:09:47Z settings invalid: FACTORY_REPOSITORY_URL: missing
factory-run: settings invalid: FACTORY_REPOSITORY_URL: missing
factory-run: cannot write the machine stop: PermissionError: [Errno 13] Permission denied: '/state'
factory-run exit=2
factory-watch: settings invalid: FACTORY_REPOSITORY_URL: missing
factory-watch exit=2
healthy
factory-health exit=0
```

In the first acceptance, `factory-run` ended here with two tracebacks and status 1. It now does what the README says. `factory-health` prints `healthy` because no health file exists; that is open item 6 under section 6.

## 3 Mutation score

The project still has no `make mutants` target, so I ran a hand pass again: **11 of 12 killed**. I used a script outside the repository (`/tmp/f10mut/mutate.py`, run with `uv run python -I`). It applies one textual mutant at a time and checks that the target text occurs exactly once. It runs the targeted test modules (`pytest -x -q --no-cov`), and the whole `tests` suite when those stay green, then restores the file from a copy. `git status` afterwards showed only this report.

The pass reruns the two survivors of the first pass (N1, N2). It adds mutants on what S0019 and S0020 built (N3 to N5), and probes rules of the feature that the first pass did not touch (N6 to N12).

| Mutant | Module | Result |
|---|---|---|
| N1 `except Exception` narrowed to `except ValueError` (first pass's M10) | `application/scheduler.py` | killed (targeted) |
| N2 `and not process.timed_out` dropped from `_sudo_refusal` (first pass's M23) | `adapters/claude_runtime.py` | killed (targeted) |
| N3 `factory-run` catches `PermissionError` only | `entry/run.py` | killed (targeted) |
| N4 `factory-run` drops the `settings invalid` line on standard error | `entry/run.py` | killed (targeted) |
| N5 `Bash(git commit*)` dropped from the deny list | `claude/settings.json` | killed (targeted) |
| N6 `line.startswith(SUDO_PREFIX)` → `SUDO_PREFIX in line` | `adapters/claude_runtime.py` | **survived** (whole suite) |
| N7 the token file's owner unchecked | `application/preflight.py` | killed (whole suite) |
| N8 `TZ` dropped from the agent environment's allow list | `domain/agent_runs.py` | killed (targeted) |
| N9 `pause_after` accepts `-1` | `application/scheduler.py` | killed (targeted) |
| N10 `factory-health` prints no stop lines | `entry/health.py` | killed (targeted) |
| N11 the token file accepts group read (`0o077` → `0o037`) | `application/preflight.py` | killed (whole suite) |
| N12 the guard allows a path outside the checkout | `adapters/claude_guard.py` | killed (targeted) |

N2 also settles what S0022's coder, reviewer and demo left open: none of them ran the mutation by hand. It fails the first row of S0022's test.

The survivor is the `sudo:` line's column. The rule (`_sudo_line`, the operator guide's "a line that starts `sudo:`") is tested only with lines that start with `sudo:`. Under N6, a dead run whose standard error holds `bash: sudo: command not found`, or an indented `sudo:`, becomes an `AgentRuntimeError` on the error path instead of the stall `died`. I checked the three rows the draft proposes against the current code with a scratch test outside the repository: `sudo: a password is required` → `AgentRuntimeError`, `bash: sudo: command not found` → `died`, `  sudo: a password is required` → `died`. Draft F0010-S0024.

N7 and N11 are killed only outside `tests/application/test_preflight.py` (by the wiring tests). That is no gap, but the token file's rule is pinned far from its module.

## 4 What the stories noticed

From the coder, reviewer, documenter and demo entries of S0018 to S0022:

1. **S0019, coder.** The time-stamped line still reaches standard output before the log file is opened, so it appears even when the state directory cannot be written. Deliberate, and the operator guide says so. No draft.
2. **S0020, coder.** The project guide's "the read and commit git commands" and the operator guide's denied list were stale. The documenter fixed both in the same story. Closed.
3. **S0021, documenter.** `make check` ran longer than the tool's 120-second default timeout, and the tool moved it to the background by itself. `CLAUDE.md` forbids background runs. A stage that calls `make check` without a longer timeout risks exactly that. This is for the human (`CLAUDE.md` and the shipped agent texts are outside every write path); listed under 6. No draft.
4. **S0022, coder, reviewer and demo.** No stage ran the mutation that the story pins: the coder's attempt was refused by the permission layer, and the reviewer reasoned from the code instead. I ran it (N2, killed). Closed.
5. **S0022, documenter.** The operator guide's `sudo` paragraph did not say that a timed-out call counts as one without a usable reply. S0018 added that clause (`docs/operator-guide.md:90`). Closed.

Still standing from the first acceptance's list, unowned:

- **The default git identity is written twice.** It is `DEFAULT_GIT_IDENTITY` in `src/factory/domain/settings.py:18` and the default of `GitOptions.identity` in `src/factory/domain/git.py:46`. The two agree. It is a one-line refactor for the next story that touches `domain/git.py`. No draft.
- **`sudo` is looked up in two ways.** `ClaudeCodeRuntime` starts the fixed `SUDO_EXECUTABLE` (`/usr/bin/sudo`), while `tool:sudo` searches the `PATH`. The `agent-run-probe` goes through the real call, so a mismatch is still seen.
- **The shipped texts mention `make mutants` "if the project has" it.** This project still does not have it, which is why sections 3 of both acceptances are hand passes.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md` (the sections on settings, start, loop, runtime, image, users, token, health, preflight and stamp) and `docs/project-guide.md`'s runtime, wiring and git sections from the top. I also grepped all three, and `docs/decisions.md`, for announcements of F0010 ("until F0010", "not yet", "yet"). S0018's repairs hold:

- `README.md` names six commands and describes `factory-health` as it behaves;
- the operator guide's login sentence agrees with "The agent runs as a second user";
- the project guide describes `os_user`, the `sudo -n -u … -- env -i` call, `RUN_FILE_MODE` and the `sudo:` rule.

The remaining "not yet" sentences are about the real container and the real build, which are indeed not observed.

Two findings:

- **`docs/operator-guide.md:44`, "The loop and its pauses".** "The first iteration is idle whatever the tick found, so the first pause is 30 seconds." This contradicts the code. `Scheduler.run` and `activity_tick` treat the first iteration like any other, and the demo's first tick ran a stage and paused 15 seconds. A direct call shows both sides:

  ```bash
  uv run python -c "
  from factory.application.scheduler import Scheduler
  for active in (True, False):
      sleeps = []
      Scheduler(prepare=lambda: True, tick=lambda: active, sleep=sleeps.append, should_stop=lambda: len(sleeps) >= 1, log=None).run()
      print(active, sleeps)
  "
  ```

  ```text
  True [15.0]
  False [30.0]
  ```

  The sentence comes from S0004's criterion 9. Its remote has nothing to do, so its tick is idle, and its parenthesis "whatever the tick found" describes that setup; the documenter took it for a rule. It is a timing misstated in the operator guide, and no operator action depends on it. Draft F0010-S0023.
- **`docs/project-guide.md:203`.** The git wrapper's table row for `fetch` … `push` still says "no story names a single user yet". The tick, the stages, the claim and the checkout preparer use them. This is stale wording from F0001, folded into draft F0010-S0023.

No example in the docs failed when I ran it. I ran the README's three commands outside the image (section 2), the operator guide's settings through the demo, and the S0018 and S0019 demo commands as their stories give them.

## 6 Decisions taken for the human

`FEATURE.md` lists 37 decisions, and the code contradicts none of them. To accept or revisit:

1. **Decisions 1 to 36.** Accept as recorded. Decision 30 (the `time_limit` under `sudo`) is still open, and neither repair is built. It waits for the morning observation.
2. **Decision 37.** The leave for the two test changes of S0020 and S0022 was "recorded by the session for the human, for the human to confirm". Both changes were made exactly as described: S0020 changed only the two lists of `SETTINGS`, and S0022 changed only the `Step` field. Confirm.

The first acceptance's open points have had no answer in any log since. Each stands as built until the human says otherwise:

3. **The token file's default lives only in the image's `ENV`, not in `InstanceSettings`.** Accept, or move it into the settings.
4. **The agent can rewrite `/home/agent/.claude`** (decision 21). That includes the agent files and `settings.json` that the loader reads on every tick, so a run can widen later runs' tools, budget or permissions until the container restarts. Revisit whether that waits for v2.
5. **A standing `main_branch_failing` stays while the machine items fail**, even if `main` was fixed meanwhile.
6. **A missing health file reads `healthy`.** Section 2 shows it outside the image: `factory-run` ends with status 2 while `factory-health` says `healthy`.
7. **The template's write paths.** The coder has `src/*` only, and neither coder nor tester has `{work_item}`.
8. **New: `make check` takes more than 120 seconds here** (section 4, item 3). Consider a sentence in `CLAUDE.md` or the shipped agent texts telling a stage to give the command a longer timeout, so that the tool does not move it to the background against `CLAUDE.md`'s rule.

Answers in the logs of S0018 to S0022: none. Each of the five ran without a question.

## 7 The slow checks

None beyond `make check`, which was green when I started and is green now (coverage 99.54 %). The project has no `make mutants` target, no image scan and no SBOM target. The morning observations are still unobserved:

- the image build, which needs the human's pins first: the base image digest and the eight Debian versions are placeholders (decision 6);
- a running container that `docker compose ps` reports healthy;
- the agent run as `agent`;
- the umask of agent-made files;
- the `time_limit` under `sudo`.

## 8 Cost

165 runs, 494.4 minutes and $45.75 for 22 stories. The first 17 cost 135 runs, 405.4 minutes and $41.30 (see the first acceptance). The five repair stories cost 30 runs, 89.0 minutes and $4.45 together:

| Story | Runs | Minutes | Dollars |
|---|---|---|---|
| S0018 | 6 | 11.0 | 0.82 |
| S0019 | 6 | 19.7 | 1.26 |
| S0020 | 6 | 32.0 | 0.88 |
| S0021 | 6 | 13.9 | 0.73 |
| S0022 | 6 | 12.4 | 0.76 |

Each repair went through in the minimum six runs, with no question and no rework, at a third of the earlier stories' average cost ($0.89 against $2.43). Only S0020 stands out, for time: 32 minutes for two list edits in a data file. Its log does not say why. Its tests stage was red as it should be, and none of its entries reports a retry.

## Proposed stories

- `drafts/F0010-S0023-the-first-pause-in-the-operator-guide.md`: the operator guide states the first pause as the code does (15 seconds after a first tick with activity, 30 after an idle one), and the project guide's git table loses "no story names a single user yet". Documentation only.
- `drafts/F0010-S0024-a-sudo-line-starts-at-column-0.md`: pins the refused side of "a line that starts with `sudo:`" with a mid-line and an indented row beside the refusal row, which kills the surviving mutant N6. Tests only.

## Log (append only)

1. acceptor: accepted with drafts; 2 drafts proposed; make mutants 11/12 (hand pass: the project has no `make mutants` target)

   This is the second acceptance of F0010. The five repair stories the first one proposed (S0018 to S0022) are archived and work. `make check` was green when I started and is green now (coverage 99.54 %). I changed nothing under `src/`, `tests/` or `docs/`. Every mutant was restored from a copy, and `git status` shows only this report and `drafts/`. In the pasted demo output, the stamp's 40-character commit is replaced by a placeholder so that `make secrets` does not flag it.

   The verdict is a recommendation. One operator-guide sentence contradicts the code: it says the first pause is always 30 seconds, but it is 15 after a first tick with activity. I judged it low weight because no operator action depends on it. If the human counts it as misleading, `not accepted` fits the same report.

   1. Scope: no finding. S0018 to S0022 stayed inside the scope, and out-of-scope items stayed out.
   2. Feature demo: green. The first acceptance's walk ran again unchanged, plus three new steps: an unwritable `/state` gives status 2 and two lines on stderr (S0019), a `GitError` or `OSError` in the tick counts as idle (S0021), and the settings deny `git add` and `git commit` (S0020). Run with an empty environment, `factory-run` now ends with status 2, not tracebacks.
   3. Mutation: 11 of 12 killed. The first pass's survivors (M10, M23) are now killed, and so are the mutants on S0019 and S0020. One survivor: `startswith("sudo:")` → `"sudo:" in line` in `_sudo_line` (S0024).
   4. Noticed by the stories: the S0018 to S0022 items are closed. I ran the mutation S0022 left open (killed). `make check` takes over 120 s and was once moved to the background by the tool. Still standing from the first acceptance: two copies of the default git identity, and two ways of finding `sudo`.
   5. Docs: S0018's repairs hold. `docs/operator-guide.md:44`'s "first iteration is idle whatever the tick found, so the first pause is 30 seconds" contradicts the code. Also, `docs/project-guide.md:203` still says "no story names a single user yet". Both go to S0023.
   6. Decisions: the 37 FEATURE decisions, with decision 30 still open and decision 37 to confirm. Five open points from the first acceptance were never answered: the token default, the agent can rewrite its agent home, the standing `main_branch_failing`, a missing health file reads healthy, and the template's write paths. New: the `make check` timeout guidance.
   7. Slow checks: none beyond `make check`. The morning observations and the image pins are still pending.
   8. Cost: 165 runs, 494.4 min, $45.75 in total. The five repairs took 30 runs, 89 min and $4.45, each in six runs with no rework. S0020 took 32 min for two list edits, and its log does not say why.
