---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 350
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T11:51:48.807673Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T11:59:36.117516Z'
  stage: acceptance
  run: a82fde26e244405c88c049797f9f59e4
stories: [F0041-S0001, F0041-S0002, F0041-S0003]
outcome: null
---

# Acceptance of The old hook guard is removed

## Recommendation

**accepted.** The three stories together remove the hook whole, as the Goal says. No runtime registers it, its code, constant, error, field and preflight search are gone, and the documents describe the kernel and the undo as the one write guard. The kernel's guard, the undo and `GuardSettings` keep working. The feature's smoke test is green end to end through the real runtime and the real `factory-confine`, and `make check` is green. The one proposed story is for a flaky test that the stories noticed but that belongs to no story; it breaks no promise of this feature.

## 1 Scope

None. Each Scope bullet has its story, and the code matches it:
- `claude_runtime.py`: no hook settings, no guard file, no `--settings` (S0001; `_RunFiles` holds the instructions and confine files only).
- R14 in the seven agents names no hook (S0001; `grep -i hook claude/agents/*.md` finds nothing).
- `claude_guard.py` and `entry/guard.py` are deleted. `GUARD_COMMAND`, `GuardSettingsInvalid`, `GuardSettings.temporary_directory`, the wiring's re-exports and the preflight's search for `factory-guard` are gone (S0002). `agent_environment_item(environment, is_directory)` is at `src/factory/application/preflight.py:151`.
- The hook's tests are deleted or changed under decisions 9 and 10 (see 6).
- The four documents are rewritten (S0003).

The human's changes are made:
- Change 1: `pyproject.toml` has six console scripts and no `factory-guard`, and the mutmut deselect line is gone.
- Change 2: the *Agent runtime (R12)* bullet in `CLAUDE.md` holds the new sentence.
- Change 3: the operator's check was met on 2026-10-20 (night log 13:40 and 14:05). Its point 1 printed `status 127` (dash's `sh`) where the feature wrote `status 1`. The feature's text was wrong; the check was met in substance.

Out of scope stayed out: `landlock`, `confinement`, `run_confinement`, the undo, `refusal`, `PROTECTED_PATHS`, the opencode runtime and `claude/settings.json` were not touched by any story's diff. A search of `src/`, `tests/`, `claude/`, `image/`, `template/`, `demo/`, `README.md` and `docs/` (outside the history in `docs/decisions.md`) finds the hook's names only in the tests that pin their absence.

## 2 Feature smoke test

The walk-through of one write guard and no hook, as an operator and a Claude Code run would meet it:
- the console scripts on the `PATH`;
- the hook's modules;
- the preflight's two items, built from the real `production_environment()`;
- a Claude Code run through `ClaudeCodeRuntime`, once unconfined and once through the real `factory-confine`, with the write paths `src/*` and the twelve `PROTECTED_PATHS`. The stand-in `claude` records its arguments and the run files and tries three writes. Each write is then judged with the undo's `refusal`;
- the state directory after both runs.

The script is `$TMPDIR/feature-smoke.sh` (61 lines; its own temporary folder, removed on exit), run from the checkout's root:

```
$ sh "$TMPDIR/feature-smoke.sh"; echo "exit $?"
1 console script factory-guard absent
1 console script factory-confine found
2 hook modules: None None
3 preflight: agent-environment True -
3 preflight: confinement True -
4 run unconfined False instructions completed
    outside.txt written | undo judges: revert
    src/inside.txt written | undo judges: keep
    src/.claude/settings.json written | undo judges: revert
4 run confined False confine instructions completed
    outside.txt refused | undo judges: revert
    src/inside.txt written | undo judges: keep
    src/.claude/settings.json written | undo judges: revert
5 state left: []
exit 0
```

Green, and it agrees with the feature:
- No run passes `--settings` or writes a guard or hooks file.
- The kernel alone refuses the write to the checkout's root.
- A protected path inside a folder a write path opens (`src/.claude/settings.json`) is written during the run and judged for reverting after it. This is decision 6 as the human accepted it.
- The run files are removed after each run.
- The preflight passes with `factory-confine` and no `factory-guard`.

That the undo reverts exactly what `refusal` refuses is pinned by `tests/application/test_undo.py::test_the_guard_refuses_exactly_what_the_undo_puts_back`.

`make check` as I found it: `test: green (134.7 s)`, coverage 99.19 %, `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **A flaky test, untraced** (S0002, coder entries 15 and 18, factory entry 16, and the reviewer and documenter after them). `tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode[--follow]` and `[factory-last-line]` failed twice under `make check` and passed alone and on the next run. One of these failures was the stall that cost S0002 a run. The test reads every file under `src/factory`, bytecode included, with `rglob("*")`. Today the two phrases are only in `domain/documents.py`. The cause cannot be quoted: the stall's output kept the `FAILED` lines and the coverage table, not the `E` lines. **Proposed: F0041-S0004.**
- **The stall's output drops the `E` lines** (same entries). The factory's stall entry keeps the tail of `make check`. Under xdist and coverage, that tail is the coverage table and the short summary, so the `E` lines that `CLAUDE.md` (*Tests*) asks a coder to quote are lost unless the coder's own run fails too. This is a question about the factory's record of a red check, not about F0041. I list it for the human and propose no story.
- **`make duplicates`: 5 new, 33 known, 3 gone**, unchanged through the feature (S0001 to S0003). The archived stories of F0036, F0037 and F0039 report the same count, so F0041 did not cause it. The new findings are:
  - four similar-code pairs between `claude_runtime` and `opencode_runtime` (`call_refusal`, `cleanup_launch`, `version_printed`, the `confine_executable` branch);
  - the unused `ManualWaiter` in `src/factory/adapters/clock.py:45`.

  The coder and the reviewer of S0001 explained the pairs as line shifts against the baseline. That explanation is wrong: the baseline's keys hold no line numbers (`factory.entry.check_duplicates`), and these keys are simply not in `security/duplicates-baseline.txt`. Accepting them into the baseline, or merging the two runtimes' launch code (F0039-S0001 drafts the last part), is the human's choice.
- **Stale run files on `self`** (night log 13:40): `/state/runs` holds `guard-`, `hooks-`, `confine-` and `instructions-` files of a run of 2026-10-19 11:38 UTC that never removed them. That is before this feature, and the runtime removes its files whenever a run ends (smoke test, line 5). For the operator to delete. F0027's draft "nothing a run leaves behind" is the place for a rule.
- **A leftover bytecode file and `mutants/`** (S0002 coder): `src/factory/adapters/__pycache__/claude_guard.cpython-312.pyc` is ignored by git, and `find_spec` gives `None`. `mutants/` still holds copies of the old guard tests, and the next sweep removes it first. Nothing to do.
- **Reviewer notes, not findings:**
  - `tests/test_claude_agent_no_hook.py:1`: the module docstring says the write-paths rule names no hook, but the test checks the whole body (S0001 entry 17).
  - `tests/test_hook_removed.py:91`: criterion 2's rows are module-level callables where plain data rows would read more simply (S0002 entry 20).

  Both are cosmetic. No story; a later story that touches either file can fix it.
- **Documenter notes** (S0003 entry 11): `docs/operator-guide.md:457` speaks of "a guard that gives no write path". That is the `GuardSettings` name (decision 4) and is correct.

## 5 The documentation as a whole

None of weight. I read `README.md`, `docs/operator-guide.md`, `docs/project-guide/` and the new entry of `docs/decisions.md` as a newcomer:
- "Six commands exist" in `README.md` and the operator guide's opening list name the same six console scripts that `pyproject.toml` installs.
- *The agent run's `PATH` and `HOME`* (`docs/operator-guide.md:222`) and the preflight rows `agent-environment` and `confinement` (`:450`, `:451`) agree with the code.
- `docs/project-guide/agents.md` lists exactly the run files the smoke test saw.
- No passage still names a hook as a guard: the remaining "hook" words are git remote hooks, `core.hooksPath` and the refused agent-file key `hooks`.
- `make documents`: `documents ok`.

Two small points, not worth a story of their own:
- The title of `docs/project-guide/write-guard.md` ("The write paths, the guard and the start wrapper") and its index line in `docs/project-guide/README.md:15` ("the write paths, the guard, the undo, the kernel's guard") still list "the guard" beside "the kernel's guard". That reads as two guards, where there is now one.
- The new decision entry cites the feature's decisions 2 and 3 in its date line, but its body gives reasons only for the hook's removal and for decision 6.

## 6 Decisions taken for the human

From `feature.md`, as built:
1. The documents change in one closing story, S0003 (A). For two merges the documents described a removed hook.
2. `agent-environment` checks the agent run's `HOME` only (A). A missing `PATH` is reported by `confinement` alone.
3. `GuardSettings.temporary_directory` is removed (A). A value that names it is refused.
4. `GuardSettings` and `AgentRunRequest.guard` keep their names.
5. The hook's fail-open rule goes, with no replacement.
6. A protected path inside a folder that a write path opens is written and reverted by the undo after the run, not refused during it (A). Accepted in the human's answers of 2026-10-20 and seen in the feature smoke test. The agent learns of it only from the undo record.
7. R14 loses its hook clause in S0001.
8. `test_the_guard_refuses_exactly_what_the_undo_puts_back` judges with `refusal` (A).
9. The leave for S0001, extended by the human's answer of 2026-10-20.
10. The leave for S0002.
11. The order against other drafts: F0041 before F0040 (the human's answer). The README table in F0038-S0002's draft has to drop its `factory-guard` row (now six rows). F0039-S0001 and F0027-S0002 now build on a runtime without guard or hooks files.
12. The operator guide's `factory-guard` section is rewritten as *The agent run's `PATH` and `HOME`* (the human).
13. Five older entries of `docs/decisions.md` are marked superseded (the human). They are at lines 146, 315, 378, 604 and 613.

Earlier tests that the reviewers name as changed, each with its leave:
- S0001, under decision 9:
  - `tests/adapters/test_claude_runtime.py`, `test_claude_runtime_file_modes.py` and `claude_stand_in.py` (its `--settings` block and `shlex` import);
  - `tests/adapters/test_claude_runtime_login.py` and `test_claude_runtime_resume.py` (decision 9 as extended on 2026-10-20);
  - `tests/test_claude_agent_refusal.py` (`_WRITE_PATHS_RULE` only);
  - `tests/adapters/test_claude_runtime_guard_temporary.py`, deleted.
- S0002, under decision 10:
  - `tests/adapters/test_claude_guard.py`, `test_claude_guard_temporary.py`, `tests/entry/test_guard.py` and `tests/guard_support.py`, deleted;
  - `tests/application/test_undo.py`, `tests/test_model_configuration.py` and `tests/application/test_agent_run_probe.py`. The probe test was brought back to the decision's exact wording after review finding 1;
  - `tests/entry/test_wiring_handlers.py`, likewise after review finding 2;
  - `tests/entry/test_wiring_extras_path.py`, which lost its two rows.
- S0002, under the standing leave to move a shared helper: `tests/entry/test_wiring_extras_path.py` (`_item` moved to `tests/wiring_support.py` as `machine_item`) and `tests/wiring_support.py`.
- **For the human to confirm:** `tests/application/test_agent_environment_item.py` was rewritten as one test, `test_the_agent_environment_checks_the_home_only`. Decision 10 named two tests instead: `test_an_existing_home_passes_whatever_the_path_holds`, and `test_a_fault_in_the_environment_fails_with_its_detail` with the rows `no-home` and `home-not-a-directory`. The reviewer accepted the change because S0002's own Interface and criterion 3, written by the human, ask for the one test. The names that decision 10 gave do not exist on `main`.

No earlier test was changed without a named leave.

New for the human, from the proposed story: F0041-S0004 changes `tests/entry/test_watch.py`, a test of F0006-S0006 and F0011-S0005. It needs a leave that `feature.md` does not give yet.

## 7 Slow checks

Beyond `make check` the project offers:
- `make duplicates`, a record: `5 new, 33 known, 3 gone`, as in 4;
- `make documents`: `documents ok`;
- `make mutants`, which is check 3.

There is no image scan and no SBOM.

From `.reports/junit.xml` (6138 test cases, 651.9 s summed over the workers; the wall time is 134.7 s), the slowest tests are:
- `tests/adapters/test_opencode_sudo_time_limit.py::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`, rows `sigkill-past-the-limit` and `status-1-past-the-limit`, 11.5 s each;
- three rows of `tests/adapters/test_process_session.py`, 10.1 s each.

None of them is a test this feature wrote.

Disk: `/work` 0.5 GB used at the start and now, `/state` and `/tmp` 0.0 GB at both. No growth.

## 8 Cost

27 runs, 47.8 min, 192 turns, $7.12 in all:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 10 | 16.3 | $2.67 |
| S0002 | 11 | 24.1 | $3.30 |
| S0003 | 6 | 7.4 | $1.15 |

S0002 stands out:
- One review round: the tester changed two earlier tests (`test_agent_run_probe.py` and `test_wiring_handlers.py`) beyond the exact wording of decision 10's leave, and the tester and the coder then ran again.
- One stall from the flaky `test_watch` test of 4, which cost a coder run.

S0001 also had one review round, for two test-only findings (a dead `shlex` import and a duplicate test).

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human during its run, because the feature's pre-check had settled the leaves and the order before S0001 started.

## Proposed stories

- `backlog/F0041-S0004-the-follow-mode-test-reads-only-the-python-sources.md`: makes `test_no_source_file_knows_the_follow_mode` read only `*.py` sources. It failed twice under `make check` during S0002, cost one stall, and could not be traced. It needs the human's leave for another story's test.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed
   1. Scope: none. Each Scope bullet has its story, and the human's changes 1 to 3 are made. Point 1 of the operator's check printed `status 127` where the feature wrote `status 1`; it was met in substance. Nothing out of scope was touched.
   2. Feature smoke test: green (exit 0). Through the real `ClaudeCodeRuntime`, once unconfined and once under the real `factory-confine`: no `--settings`, and no guard or hooks file. The kernel alone refuses the write to the checkout's root. A protected path inside a write path's folder (`src/.claude/settings.json`) is written and judged for reverting (decision 6). Both preflight items pass without `factory-guard`, and no run files are left. `make check` is green (99.19 %).
   3. Mutation testing: by sweep, not run here.
   4. Noticed: the `test_watch` follow-mode test failed twice under `make check` with no traced cause and stalled S0002 once (proposed: F0041-S0004). The stall's output drops the `E` lines that `CLAUDE.md` asks a coder to quote (for the human). `make duplicates` shows 5 new findings that predate the feature; S0001 explained them as line shifts, which is wrong, since the baseline's keys hold no line numbers. Stale run files from 2026-10-19 sit in `/state/runs` on `self`. Two cosmetic test notes from the reviewers.
   5. Documentation: none of weight. Two small points: `write-guard.md`'s title and its index line still list "the guard" beside "the kernel's guard", and the new decision entry cites decisions 2 and 3 without giving their reasons.
   6. Decisions: the feature's decisions 1 to 13 are listed. Every changed earlier test has a named leave. For the human to confirm: `test_agent_environment_item.py` became one test, as S0002's criterion 3 asks, not the two tests decision 10 named. F0041-S0004 needs a new leave.
   7. Slow checks: nothing beyond `make check` besides the `duplicates` record and `make documents` (ok). The slowest tests are the opencode sudo time-limit rows (11.5 s); none was written by this feature. Disk: no growth.
   8. Cost: $7.12 over 27 runs. S0002 stands out ($3.30, 11 runs) for one review round over two tests changed beyond decision 10's wording and one stall from the flake. 0 questions, 0.0 h waited.
