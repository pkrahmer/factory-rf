---
stage: done
pr: 144
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0010-S0001, F0010-S0002, F0010-S0003, F0010-S0004, F0010-S0005, F0010-S0006, F0010-S0007, F0010-S0008, F0010-S0009, F0010-S0010, F0010-S0011, F0010-S0012, F0010-S0013, F0010-S0014, F0010-S0015, F0010-S0016, F0010-S0017, F0010-S0018, F0010-S0019, F0010-S0020, F0010-S0021, F0010-S0022, F0010-S0024]
outcome: accepted
---
# Acceptance of The machine

## Verdict

**accepted**, as a recommendation. This is the third acceptance of F0010. The second proposed two drafts. The human applied S0023 by hand: the operator guide now states the first pause as the code does, and the project guide's git table names its users. S0024 is archived, and its three rows kill the one survivor of the last pass. `make check` is green, the feature demo is green end to end (now with a step for the `sudo:` rule), and a new hand mutation pass killed 12 of 12, including that survivor. No finding is of weight. One draft, S0025, gives an owner to a small duplication that three acceptances noticed and nobody took. The five product points that the first acceptance raised still have no answer; they are listed under section 6 for the human.

## 1 Scope

None. The first acceptance's table (scope item → stories → code) still holds, and the second acceptance found S0018 to S0022 inside the scope. Since then, two changes:

- **S0024.** Tests only: one parametrized test in `tests/adapters/test_claude_runtime_os_user.py` replaces S0014's single refusal test, as FEATURE decision 38 allows. Nothing under `src/` changed. It pins the existing rule "a line that starts with `sudo:`" from the preflight and agent-user scope item.
- **S0023, applied by hand** (commit `e1b2c24`). It changed one sentence each in `docs/operator-guide.md:44` and `docs/project-guide.md:203`, and no code.

The Goal's conditions are each shown by a test, or, for Docker, root and the second user, by a static test of the files plus the morning observations. Out of scope stayed out:

- no watchdog;
- no preflight of the project's setup or the token's expiry;
- no sandbox;
- the project commands still run as `factory` (decision 24);
- no `time_limit` enforced under `sudo` (decision 30, open);
- no skill file.

## 2 Feature demo

**Green.** This is the second acceptance's walk, run again unchanged, with one step added for S0024. The walk covers:

- the image's environment and the settings read from it;
- one instance's loop through `Scheduler`, `RepositoryWaiter`, `CheckoutPreparer` and one `build_tick` tick for the whole run, with `activity` as `activity_tick` applies it;
- the container's health check after each step.

It runs against a real bare remote with a human clone, the shipped `claude/` copied into an agent home, the template's pipeline definition, and the production `build_boundaries`, with `FakeHostingService` and `FakeAgentRuntime` in place of the hosting service and `claude -p`. Step 8 uses the production `ClaudeCodeRuntime` with a `sudo` stand-in, a shell script that writes one line to standard error and exits 1.

The script is the first acceptance's (pasted in that report's section 2), plus the second acceptance's steps 5 to 7 (pasted in that report's section 2), plus these lines. It lies outside the repository at `/tmp/f10demo3/demo.py`, because the guard refuses other paths:

```python
print("== 8. a sudo refusal is an error only when its line starts with `sudo:` ==")
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.errors import AgentRuntimeError
req = runtime.requests()[-1].model_copy(update={"working_directory": tmp / "work8", "os_user": "agent"})
(tmp / "work8").mkdir()
for n, line in enumerate(["sudo: a password is required", "bash: sudo: command not found", "  sudo: a password is required"]):
    sudo = tmp / f"sudo{n}"; sudo.write_text(f"#!/bin/sh\nprintf '%s\\n' '{line}' >&2\nexit 1\n"); sudo.chmod(0o755)
    rt = ClaudeCodeRuntime("/bin/false", tmp / f"state8-{n}", sudo_executable=str(sudo))
    try:
        result = rt.run(req); print(f"   {line!r:34} -> end reason {result.end_reason}")
    except AgentRuntimeError as e:
        print(f"   {line!r:34} -> AgentRuntimeError: {e.detail}")
```

```bash
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 uv run python /tmp/f10demo3/demo.py 2>&1 | sed "s|/tmp/tmp[a-z0-9_]*|<tmp>|g"
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
2026-10-16T21:03:23Z stop repository main_branch_failing: lint is red on main at e50d79863f1f: E501 line too long
   tick 3: event=None dispatch=None stopped=main_branch_failing -> activity=False
   sleep 30 s
   factory-health exit 1: 'main_branch_failing (repository): lint is red on main at e50d79863f1f: E501 line too long (since 2026-10-16T21:03:23Z)'
   -- human pushes the fix --
2026-10-16T21:03:23Z stop cleared main_branch_failing
   tick 4: event=idle dispatch=handled stopped=None -> activity=False
   sleep 60 s
   factory-health exit 0: 'healthy'
   -- operator's coder.md gains a dead key `skills: [x]` --
2026-10-16T21:03:23Z stop repository agent_definition_invalid: coder: key not applied by the agent runtime: skills
   tick 5: event=None dispatch=None stopped=agent_definition_invalid -> activity=False
   sleep 120 s
   factory-health exit 1: 'agent_definition_invalid (repository): coder: key not applied by the agent runtime: skills (since 2026-10-16T21:03:23Z)'
   -- coder.md restored; the checkout is deleted --
2026-10-16T21:03:23Z stop cleared agent_definition_invalid
   tick 6: event=idle dispatch=handled stopped=None -> activity=False
   sleep 120 s
   checkout recloned: True | factory-health exit 0: 'healthy'
pauses: [15, 15, 30, 60, 120, 120] | agent runs: ['coder', 'intake']
== 3. a new image build: the machine items run again; sudo missing ==
2026-10-16T21:03:23Z stop machine preflight_failed: tool:sudo: sudo is not on the PATH; add it to the image
   stopped: preflight_failed | agent runs started by the preflight: 1
   factory-health exit 1: 'preflight_failed (machine): tool:sudo: sudo is not on the PATH; add it to the image (since 2026-10-16T21:03:23Z)'
2026-10-16T21:03:23Z stop cleared preflight_failed
   with sudo: stopped: None | factory-health exit 0: 'healthy'
== 4. factory-run and factory-watch with an invalid environment ==
   factory-run exit: 2 | factory-health exit 1: 'preflight_failed (machine): FACTORY_INSTANCE: missing (since 2026-10-16T21:03:23Z)'
   log tail: 2026-10-16T21:03:23Z settings invalid: FACTORY_INSTANCE: missing
   factory-watch exit: 2 | stderr: factory-watch: settings invalid: FACTORY_INSTANCE: missing
== 5. factory-run with a state directory it cannot write ==
   factory-run exit: 2 | stdout: settings invalid: FACTORY_INSTANCE: missing | stderr: ['factory-run: settings invalid: FACTORY_INSTANCE: missing', "factory-run: cannot write the machine stop: NotADirectoryError: [Errno 20] Not a directory: '<tmp>/file/state'"]
== 6. the loop survives a git error and an OSError in the tick ==
   sleeps: [30.0, 60.0] | log: ['iteration failed: GitError: git fetch origin failed (exit 128): could not read from remote', 'iteration failed: OSError: disk full']
== 7. the shipped settings refuse git add and git commit ==
   allowed git: ['Bash(git status*)', 'Bash(git diff*)', 'Bash(git log*)', 'Bash(git show*)', 'Bash(git rev-parse*)'] | denied add/commit: ['Bash(git add*)', 'Bash(git commit*)']
== 8. a sudo refusal is an error only when its line starts with `sudo:` ==
   'sudo: a password is required'     -> AgentRuntimeError: <tmp>/sudo0 refused the agent run: sudo: a password is required
   'bash: sudo: command not found'    -> end reason died
   '  sudo: a password is required'   -> end reason died
```

The stamp's probed commit is replaced by a placeholder, so that `make secrets` does not flag a high-entropy string. Steps 1 to 7 print what they printed in the second acceptance, apart from time stamps and commits.

- **Step 2, the pauses.** The first tick ran the intake stage, and the pause after it is 15 seconds. That is what the repaired operator guide now says (`docs/operator-guide.md:44`).
- **Step 8 (S0024).** A refusal at column 0 is an `AgentRuntimeError` naming its line. A `sudo:` in the middle of a line, or after leading spaces, is the stall `died`.

The README's commands outside the image, from a shell with an empty environment:

```bash
for c in factory-run factory-watch factory-health; do env -i PATH="$PATH" HOME="$HOME" uv run $c; echo "$c exit=$?"; done
```

```text
2026-10-16T21:03:26Z settings invalid: FACTORY_REPOSITORY_URL: missing
factory-run: settings invalid: FACTORY_REPOSITORY_URL: missing
factory-run: cannot write the machine stop: PermissionError: [Errno 13] Permission denied: '/state'
factory-run exit=2
factory-watch: settings invalid: FACTORY_REPOSITORY_URL: missing
factory-watch exit=2
healthy
factory-health exit=0
```

This is unchanged since the second acceptance. `factory-health` prints `healthy` because no health file exists; that is open point 6 under section 6.

## 3 Mutation score

The project still has no `make mutants` target, so I ran a hand pass again: **12 of 12 killed**. The script lies outside the repository (`/tmp/f10mut3/mutate.py`, run with `uv run python -I`) and is the second pass's script with a new list. It applies one textual mutant at a time, after checking that the target text occurs exactly once, and runs the targeted tests (`pytest -x -q --no-cov`). If those stay green, it runs the whole `tests` suite. It then restores the file from a copy. Afterwards, `git status` showed only this report.

P1 reruns the second pass's survivor. P2 to P12 probe rules of the feature that neither earlier pass touched.

| Mutant | Module | Result |
|---|---|---|
| P1 `line.startswith(SUDO_PREFIX)` → `SUDO_PREFIX in line` (second pass's N6) | `adapters/claude_runtime.py` | killed (targeted) |
| P2 any user part of the URL counts as a password (`and ":" in user_information` dropped) | `domain/settings.py` | killed (targeted) |
| P3 a comma in the repository URL is accepted | `domain/settings.py` | killed (targeted) |
| P4 the version matches anywhere in the reported text (`words[0] == pinned` → `pinned in reported`) | `domain/preflight.py` | killed (targeted) |
| P5 the pause caps at 240 seconds | `application/scheduler.py` | killed (targeted) |
| P6 an `idle` event counts as activity | `entry/run.py` | killed (targeted) |
| P7 the stamp ignores the image build | `application/preflight.py` | killed (targeted) |
| P8 the `agent-user` item fails without a token file | `application/preflight.py` | killed (targeted) |
| P9 the files of an agent run are group-writable (`0o640` → `0o660`) | `adapters/claude_runtime.py` | killed (targeted) |
| P10 an unapplied agent key passes | `adapters/agent_files.py` | killed (targeted) |
| P11 a failed `main` is not remembered (`lint` runs again on every tick) | `application/preflight.py` | killed (targeted) |
| P12 the token file accepts read by others (`0o077` → `0o070`) | `application/preflight.py` | killed (targeted) |

Over the three passes, every rule probed is now pinned by a test. No survivor groups into a missing criterion.

## 4 What the stories noticed

From the coder, reviewer, documenter and demo entries of S0024:

1. **S0024, coder.** "Coverage still misses `claude_runtime.py` lines 384 and 408-409." I checked both.
   - Line 384 is the resume path when the first call has used up the whole `time_limit`. It is a clock-dependent branch, and the runtime has no injected clock to drive it without a sleep.
   - Lines 408-409 are an `OSError` while writing the run files into an existing state directory.

   Both lines are F0001's code, not this feature's, and the module is at 99 %. No draft.
2. **S0024, reviewer, documenter and demo.** No remarks. The documenter cross-read the rule in `docs/operator-guide.md:90`, `docs/project-guide.md:300` and `docs/decisions.md:293`, and all three agree with the code.

Still standing from the earlier acceptances, unowned:

- **The default git identity is written twice.** It is `DEFAULT_GIT_IDENTITY` in `src/factory/domain/settings.py:18` and the literal default of `GitOptions.identity` in `src/factory/domain/git.py:46`. Both earlier acceptances left it "for the next story that touches `domain/git.py`", and no such story came. This is the feature's last chance to give it an owner, so it is draft F0010-S0025.
- **`sudo` is looked up in two ways.** `ClaudeCodeRuntime` starts the fixed `SUDO_EXECUTABLE` (`/usr/bin/sudo`), while the item `tool:sudo` searches the `PATH`. The `agent-run-probe` goes through the real call, so a mismatch is still found as a machine stop. No draft.
- **No `make mutants` target.** The shipped texts mention `make mutants` "if the project has" it, and this project still does not. That is why section 3 is a hand pass in all three acceptances. Adding the target means a new dependency (`mutmut`), which is the human's to decide (`CLAUDE.md`, "Not without asking"). Listed under 6.

Closed since the second acceptance: the `make check` timeout. `CLAUDE.md` now gives it the 600000 ms timeout (commit `0a92218`), and this stage ran `make check` in the foreground with that timeout.

## 5 The documentation as a whole

I reread `README.md`, the operator guide's sections on the loop, the preflight and the stamp, the stops table and the tick, and the project guide's git table. I also grepped all four documents for "first pause", "first iteration", "not yet", "until F0010" and "no story names". The S0023 repairs hold:

- `docs/operator-guide.md:44` states the first pause as the code and the demo's step 2 show: 15 seconds after a tick with activity, 30 after an idle one.
- `docs/project-guide.md:203` names the users of `fetch` … `push`, including `clone` for the checkout preparer.

The remaining "not yet" sentences (`README.md:3`, `docs/operator-guide.md:3` and `:134`) are about the real container and its build, which are indeed not observed. Every example I ran gave what the docs say: the README's three commands outside the image, the operator guide's settings and pauses through the demo, and S0024's demo command (12 tests pass, as its Demo expects).

One remark, no finding: `docs/decisions.md:275` (S0009) ends with "Open: the preflight does not fetch, and a `main_branch_failing` stop stays when the machine's items fail; the tick story decides both". The tick story's entry (`docs/decisions.md:279`, S0010) decides the first part: the tick fetches before the preflight. It does not mention the second part. The second part is open point 5 below, so the sentence is true as history, and the decision log is the place where the human's answer would go. No draft.

## 6 Decisions taken for the human

`FEATURE.md` lists 38 decisions, and the code contradicts none of them. To accept or revisit:

1. **Decisions 1 to 36.** Accept as recorded. Decision 30 (the `time_limit` under `sudo`) is still open, and neither repair is built. It waits for the morning observation.
2. **Decisions 37 and 38.** Each was "recorded by the session for the human, for the human to confirm". Both test changes were made exactly as described. For 38, S0024's tester replaced only `test_a_sudo_refusal_is_a_runtime_error_naming_its_line`, with one parametrized test whose first row is its case, and nothing else in the file changed (`git diff b7eed89..HEAD -- tests/`). Confirm both.

The open points of the first acceptance, which the night log of 2026-10-16 lists "for the morning" and no log has answered since. Each stands as built until the human says otherwise:

3. **The token file's default lives only in the image's `ENV`** (`image/Dockerfile:39`), not in `InstanceSettings`. Accept, or move it into the settings.
4. **The agent can rewrite `/home/agent/.claude`** (decision 21). That includes the agent files and `settings.json` that the loader reads on every tick, so one run can widen the tools, budget or permissions of later runs until the container restarts. Revisit whether that waits for v2.
5. **A standing `main_branch_failing` stays while the machine items fail**, even if `main` was fixed meanwhile (see also `docs/decisions.md:275`).
6. **A missing health file reads `healthy`.** Section 2 shows it outside the image: `factory-run` ends with status 2 while `factory-health` says `healthy`.
7. **The template's write paths.** The coder has `src/*` only, and neither coder nor tester has `{work_item}` (`template/factory/pipeline.yml:11-12`).

New in this acceptance:

8. **A `make mutants` target.** It needs `mutmut` as a development dependency, which is the human's to allow. Without it, every feature acceptance runs a hand pass like section 3's.

Answers in S0024's log: none. It ran without a question.

## 7 The slow checks

None beyond `make check`, which was green when I started and is green now (coverage 99.54 %). The project has no `make mutants` target, no image scan and no SBOM target. The morning observations are still unobserved:

- the image build, which needs the human's pins first: the base image digest and the eight Debian package versions are placeholders (decision 6);
- a running container that `docker compose ps` reports healthy;
- the agent run as `agent`;
- the umask of agent-made files;
- the `time_limit` under `sudo` (decision 30).

## 8 Cost

171 runs, 505.9 minutes and $46.33 for 23 stories. The second acceptance counted 165 runs, 494.4 minutes and $45.75 for 22, so S0024 cost 6 runs, 11.5 minutes and $0.58 (its log: 29 turns). It went through in the minimum six runs, with no question and no rework, and it cost less than each of the five repairs before it ($0.73 to $1.26). Nothing stands out.

For scale, the acceptances themselves now cost more than the repairs they propose. The second acceptance's own log entry says 2 runs, 58.7 minutes and $6.75, against $0.58 for S0024. The night-log row for that acceptance (`docs/runs/2026-10-12-overnight/night-log.md`) says "1 run, 20 minutes, $2.02". The two figures disagree; the human's file is the one to check.

## Proposed stories

- `drafts/F0010-S0025-one-default-git-identity.md`: the default commit identity `factory <factory@noreply.invalid>` becomes one constant in `factory.domain.git`, which `GitOptions` and the settings both use, with a source search that finds the email literal once. A one-line refactor that three acceptances noticed and nobody owned. No behaviour changes.

## Log (append only)

1. acceptor: accepted; 1 draft proposed; make mutants 12/12 (hand pass: the project has no `make mutants` target)

   This is the third acceptance of F0010. Since the second, the human applied S0023 by hand and S0024 was archived. `make check` was green when I started and is green now (coverage 99.54 %). I changed nothing under `src/`, `tests/` or `docs/`. Every mutant was restored from a copy, and `git status` shows only this report and `drafts/`.

   1. Scope: no finding. S0024 is tests only and pins the existing `sudo:` rule. S0023 repaired two docs sentences. Out-of-scope items stayed out.
   2. Feature demo: green. The second acceptance's walk ran again unchanged. A new step 8 runs the production `ClaudeCodeRuntime` with a `sudo` stand-in: a refusal line at column 0 raises `AgentRuntimeError`, while a mid-line or indented `sudo:` gives the stall `died`. The README's commands in an empty environment behave as before: `factory-run` and `factory-watch` exit 2, and `factory-health` prints `healthy`.
   3. Mutation: 12 of 12 killed. The second pass's survivor (N6, `startswith` → `in`) is now killed. Eleven new mutants were all killed: the URL password and comma rules, the version match, the 120-second pause cap, idle versus activity, the stamp's image key, the `agent-user` item, the run-file mode, unapplied agent keys, the remembered red `main`, and the token file mode.
   4. Noticed: S0024's coder left two lines of `claude_runtime.py` uncovered (384, 408-409). Both are F0001 code, so no draft. The doubled default git identity has stood through three acceptances and is now draft S0025. The two ways of finding `sudo` remain, with no draft. The `make check` timeout is closed by `CLAUDE.md`.
   5. Docs: the S0023 repairs hold, and every example I ran matches. One remark, not a finding: the "Open:" sentence at `docs/decisions.md:275` is only half answered by the S0010 entry; the other half is open point 5.
   6. Decisions: 38 in `FEATURE.md`, none contradicted by the code. Decision 30 is still open. Decisions 37 and 38 are to confirm; I checked that both test changes were made exactly as described. Five open points from the first acceptance are still unanswered. New point: a `make mutants` target, which needs `mutmut`, the human's dependency call.
   7. Slow checks: none beyond `make check`. The morning observations and the image pins are still pending.
   8. Cost: 171 runs, 505.9 min and $46.33 in total. S0024 took 6 runs, 11.5 min and $0.58, nothing stands out. The second acceptance's own cost disagrees between its log entry ($6.75) and the night log ($2.02).
2. done (pull request merged); cost: 3 runs, 72.2 min, 161 turns, 391k tokens in (14665k more from cache), 108k out, $8.23
