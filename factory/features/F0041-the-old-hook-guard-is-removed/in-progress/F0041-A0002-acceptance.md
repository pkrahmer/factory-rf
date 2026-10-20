---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 354
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T14:44:13.768768Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T14:49:46.952003Z'
  stage: acceptance
  run: 3e34ddddaba942a38b370ed1feb49cd7
stories: [F0041-S0001, F0041-S0002, F0041-S0003, F0041-S0004]
outcome: null
---

# Acceptance of The old hook guard is removed

## Recommendation

**accepted.** This is the second acceptance of F0041. The first, F0041-A0001, accepted S0001 to S0003, and the human merged it. Its one proposed story, S0004, has since been built and archived.

The four stories together still do what the Goal says:
- no runtime registers the hook;
- its command, adapter, constant, error, field and preflight search are gone;
- the documents name the kernel and the undo as the one write guard;
- the follow-mode test that stalled S0002 now reads only Python sources, and the umask test's child no longer writes bytecode into the checkout.

The feature smoke test is green through the real runtime and the real `factory-confine`, and `make check` is green. Nothing new needs a story. The open points are small and were already listed by A0001.

## 1 Scope

None. S0001 to S0003 match their Scope bullets as A0001 found. Their code and documents have not changed since: a search of `src/`, `claude/`, `image/`, `template/`, `demo/`, `pyproject.toml`, `CLAUDE.md`, `README.md`, `docs/operator-guide.md` and `docs/project-guide/` finds no `factory-guard`, `claude_guard`, `GUARD_COMMAND` or `GuardSettingsInvalid`.

S0004 matches its Scope bullet, "`tests/entry/test_watch.py`: the follow-mode search reads only the Python sources, under decision 14". Its diff (`git diff 21bf13ed d790a261`) touches only `tests/entry/test_watch.py` and `tests/test_tests_umask.py`, both named in decision 14, and nothing under `src/`:
- `_files_naming(root, text)` scans `root.rglob("*.py")`;
- `_names_the_replaced_phrases(root, path)` no longer has its `__pycache__` clause;
- `test_the_follow_mode_scan_reads_only_python_sources` has five rows;
- the umask test's child gets `PYTHONDONTWRITEBYTECODE=1`.

The human's changes 1 to 3 were made before A0001 (see its point 1). Nothing out of scope was touched.

## 2 Feature smoke test

The walk-through of one write guard and no hook, as an operator and a Claude Code run meet it:
- the console scripts beside the interpreter;
- the hook's modules;
- the preflight's two items, built from the real `production_environment()`, `abi_version` and `_which_on`;
- a Claude Code run through `ClaudeCodeRuntime`, once unconfined and once through the real `factory-confine`, with the write paths `src/*` and the twelve `PROTECTED_PATHS`. The stand-in `claude` (`tests/adapters/claude_stand_in.py`) records its arguments and files, then writes three files in order. Each write is then judged with the undo's `refusal`;
- the state directory after each run.

The script is `$TMPDIR/feature_smoke.py`, in a `mktemp -d` folder that is removed on exit. It builds its folders with `tests/confine_support.py`. It was run from the checkout's root:

```
$ PYTHONPATH=tests uv run python "$d/feature_smoke.py"; echo "exit $?"
1 console script factory-guard absent
1 console script factory-confine found
2 hook modules: None None
3 preflight: agent-environment True -
3 preflight: confinement True -
4 run unconfined | --settings: False | run files: instructions | end: completed
    src/inside.txt written | undo judges: keep
    src/.claude/settings.json written | undo judges: revert
    outside.txt written | undo judges: revert
5 state left: []
4 run confined | --settings: False | run files: instructions | end: died
    src/inside.txt written | undo judges: keep
    src/.claude/settings.json written | undo judges: revert
    outside.txt refused | undo judges: revert
5 state left: []
exit 0
```

Green, and it agrees with the feature:
- No run passes `--settings`. The only run file `claude` sees in the state directory is the instructions file; there is no `guard-` or `hooks-` file.
- With no hook in place, the kernel alone refuses the write to the checkout's root. The confined run ends `died` because the stand-in has no handler for the refused write and exits non-zero on its `PermissionError`; a real agent sees the refusal and goes on.
- A protected path inside a folder that a write path opens (`src/.claude/settings.json`) is written during the run and judged for reverting after it. This is decision 6 as the human accepted it.
- No run files are left after either run.
- The preflight passes without `factory-guard`.

A first try, with `outside.txt` written first, ended `died` before the two later writes. Only the order of the writes changed.

`make check` as I found it: `test: green (158.5 s)`, coverage 99.17 %, `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

S0004's entries noticed little. Its coder noticed nothing, and its documenter found nothing stale. Its reviewer chose not to count the docstring on the private `_files_naming` as a finding (the Interface prescribes it). Its smoke tester noted that criterion 3 is checked by `grep` only and that the umask rows were left to `make check`; they pass there (`[000]` to `[077]`, about 0.9 s each).

Evidence that S0004's fix holds:
- The checkout still holds 128 git-ignored `.pyc` files under `src/` and `tests/`, written by both `agent` and `factory` between 2026-10-18 and 12:34 today, so before S0004 merged.
- All of them are group-readable now.
- My `make check` added none.

Removing them is F0027-S0003's work. That story is still in F0027's backlog, although `CLAUDE.md` (*Architecture*, R12) already says the factory removes ignored paths after every run. That is F0027's business; I list it and propose nothing.

Carried over from A0001, still open and still unowned:
- **The stall's output drops the `E` lines** that `CLAUDE.md` (*Tests*) asks a coder to quote. This is a question about the factory's record of a red check. For the human; no story here.
- **`make duplicates`: `5 new, 33 known, 3 gone`**, the same five as before:
  - four similar-code pairs between `claude_runtime` and `opencode_runtime` (`due_leftovers_launch`, `call_refusal`, `_end_leftovers`, `version_printed`);
  - the unused `ManualWaiter` (`src/factory/adapters/clock.py:45`).

  They predate F0041. Accepting them into `security/duplicates-baseline.txt` or merging the launch code is the human's choice.
- **The two cosmetic test notes** of the S0001 and S0002 reviewers (`tests/test_claude_agent_no_hook.py:1`, `tests/test_hook_removed.py:91`). No story.

## 5 The documentation as a whole

None of weight. `README.md`, `docs/operator-guide.md` and `docs/project-guide/` name no hook as a guard. The remaining "hook" words are a remote's hook, `.git/hooks` and the refused agent-file key `hooks`. `make documents`: `documents ok`. S0004 changed no document (docs criterion `none`), and its documenter confirmed that `docs/project-guide/agents.md` (`PYTHONDONTWRITEBYTECODE=1`) stays true.

The two small points from A0001 are unchanged and still not worth a story of their own:
- The title of `docs/project-guide/write-guard.md` ("The write paths, the guard and the start wrapper"), its first line and its index line in `docs/project-guide/README.md:15` list "the guard" beside "the kernel's guard". No section of the file is called "the guard", so this reads as two guards. A later story that touches the file can fix it.
- The F0041 entry in `docs/decisions.md` cites the feature's decisions 2 and 3 without giving their reasons.

## 6 Decisions taken for the human

From `feature.md`, as built:
1. The documents change in one closing story, S0003 (A).
2. `agent-environment` checks the agent run's `HOME` only (A).
3. `GuardSettings.temporary_directory` is removed (A).
4. `GuardSettings` and `AgentRunRequest.guard` keep their names.
5. The hook's fail-open rule goes, with no replacement.
6. A protected path inside a folder that a write path opens is written and then reverted by the undo, not refused during the run (A). The human accepted this on 2026-10-20, and the feature smoke test shows it.
7. R14 loses its hook clause (S0001).
8. `test_the_guard_refuses_exactly_what_the_undo_puts_back` judges with `refusal` (A).
9. The leave for S0001, extended by the human on 2026-10-20.
10. The leave for S0002. The human accepted `test_agent_environment_item.py` as one test, as built (2026-10-20).
11. The order against other drafts: F0041 before F0040. The `factory-guard` row in F0038-S0002's README table still has to go.
12. The operator guide's section is rewritten as *The agent run's `PATH` and `HOME`*.
13. Five older entries of `docs/decisions.md` are marked superseded.
14. The leave for S0004 (granted 2026-10-20), covering `tests/entry/test_watch.py` and `tests/test_tests_umask.py`.

Earlier tests that the reviewers name as changed, each with its leave:
- S0001 to S0003: as listed in A0001, each under decision 9, decision 10 or the standing leave to move a shared helper.
- S0004: `tests/entry/test_watch.py` (F0006-S0006 and F0011-S0005) and `tests/test_tests_umask.py` (F0033-S0001), both under decision 14. Its reviewer (entry 9) confirmed that only the follow-mode helpers and the child's environment changed, and that one test was added.

No earlier test was changed without a named leave.

## 7 Slow checks

Beyond `make check`, the project offers the `make duplicates` record (`5 new, 33 known, 3 gone`, as in point 4) and `make documents` (`documents ok`). `make mutants` is point 3. There is no image scan and no SBOM.

From `.reports/junit.xml` (6222 test cases, 746.3 s summed over the workers; the wall time is 158.5 s), the slowest tests are:
- two rows of `tests/adapters/test_opencode_sudo_time_limit.py::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`, 11.5 s each;
- two tests of `tests/adapters/test_process_session.py`, 10.1 s each.

None of them was written by this feature. S0004's own tests:
- the seven follow-mode rows take 0.04 s each;
- the umask rows take 0.87 to 0.91 s each, as before.

Disk: at the start, `/work` had 0.5 GB used and `/state` and `/tmp` 0.0 GB. At acceptance the figures are the same. No growth.

## 8 Cost

The stories cost 33 runs, 53.3 min, 221 turns and $8.03 in all:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 10 | 16.3 | $2.67 |
| S0002 | 11 | 24.1 | $3.30 |
| S0003 | 6 | 7.4 | $1.15 |
| S0004 | 6 | 5.5 | $0.91 |

S0002 still stands out, for the reasons A0001 gave: one review round over two tests changed beyond decision 10's wording, and one stall from the flaky `test_watch` test.

S0004, the fix for that flake, cost $0.91, about the price of the stall it removes. Its coder run (126 s, $0.15) built nothing: it ran `make check` over a tester-only change, which the pipeline requires. The first acceptance, F0041-A0001, cost $2.02 more; that is not counted in the stories' sum.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human during its runs, because the feature's pre-checks (`planning/overnight/precheck/F0041-*`) settled the leaves and the order before each story started.

## Proposed stories

None. S0004, the only story proposed before, is built and archived. The open points in 4 and 5 are either the human's choice (the stall record, the duplicates baseline) or too small for a story of their own (the "the guard" wording in `write-guard.md`).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed
   1. Scope: none. S0001 to S0003 are unchanged since A0001, and no hook names remain in `src/`, `claude/`, `image/`, `template/`, `demo/`, `pyproject.toml`, `CLAUDE.md` or the documents. S0004's diff touches only `tests/entry/test_watch.py` and `tests/test_tests_umask.py`, as its Scope bullet and decision 14 say, and nothing under `src/`.
   2. Feature smoke test: green (exit 0). The real `ClaudeCodeRuntime` ran once unconfined and once under the real `factory-confine`. Neither run passed `--settings` or wrote a guard or hooks file. The kernel alone refused the write to the checkout's root. `src/.claude/settings.json` was written and judged for reverting (decision 6). Both preflight items pass without `factory-guard`, and no run files are left. `make check` is green (158.5 s, 99.17 %).
   3. Mutation testing: by sweep, not run here.
   4. Noticed: S0004's entries noticed nothing new. The fix holds: the checkout's 128 ignored `.pyc` files all predate S0004's merge and are group-readable, and my `make check` added none. Their removal is F0027-S0003's work, still in F0027's backlog. Still open from A0001: the stall record drops the `E` lines (for the human), and `make duplicates` shows 5 new findings that predate the feature.
   5. Documentation: none of weight, and `documents ok`. A0001's two small points remain: `write-guard.md`'s title and index line list "the guard" beside "the kernel's guard", and the decision entry cites decisions 2 and 3 without giving their reasons.
   6. Decisions: the feature's decisions 1 to 14 are listed, with the human's answers. S0004's two changed earlier tests are under decision 14, and no earlier test was changed without a named leave.
   7. Slow checks: only the `duplicates` record (5/33/3) and `make documents` (ok). The slowest tests are the opencode sudo time-limit rows (11.5 s); none was written by this feature. Disk: no growth.
   8. Cost: $8.03 over 33 runs and 53.3 min. S0002 stands out ($3.30, 11 runs: one review round and one stall). S0004 cost $0.91, about the price of the stall it removes. 0 questions, 0.0 h waited.
