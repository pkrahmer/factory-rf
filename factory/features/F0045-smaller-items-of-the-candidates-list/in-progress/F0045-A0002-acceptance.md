---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 480
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-27T04:48:12.607615Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-27T04:57:17.772098Z'
  stage: acceptance
  run: 8f5bf0a4250d4775b04d50982d69a2d7
stories: [F0045-S0001, F0045-S0002, F0045-S0003, F0045-S0004, F0045-S0005, F0045-S0006, F0045-S0007, F0045-S0008, F0045-S0009, F0045-S0010, F0045-S0011, F0045-S0013, F0045-S0014]
outcome: null
---

# Acceptance of Smaller items of the candidates list

## Recommendation

**Accepted.** All thirteen stories are merged and `make check` is green on this branch. The feature's smoke test walked every promise of the Goal through its real entry points with no fault, including S0013's `run_or_raise` under the three wrappers. A0001's three proposals are closed: S0012 by the human on `main`, S0013 and S0014 as stories. `make duplicates` is back to `0 new, 41 known, 0 gone`. What is left is one stale sentence in the project guide (and a missing comma), which gives one small documents story, plus three items only the human can act on (a mutmut deselect line in `pyproject.toml`, change 3, and the disk).

## 1 Scope

None. Every scope line of `feature.md` has its archived story. A0001 read S0001 to S0011 against `main`, and I checked again that their code is still in place (the smoke test below exercises each one). The two stories added from A0001:
- S0013: `ROOT` and `run_or_raise` are in `src/factory/adapters/process.py`. `ZfsSnapshots._execute`, `SystemctlPowerOff.power_off` and `PodmanRuns._query` call it (`src/factory/adapters/power_off.py`, `src/factory/adapters/podman_runs.py:166`). No `_ROOT` remains, and `PodmanRuns.run` keeps its own request with `cwd=ROOT`. `make duplicates` prints `duplicates: 0 new, 41 known, 0 gone`; the human removed the gone line in `345ce9227`.
- S0014: the five leftovers are gone. `in_order` and `lines_with` are in `tests/vm_support.py`, there is one `SCHEMAS`, `committed` and `values` have no underscore, `record_get_repo` is public, the suite's smoke test has `next: [approval, doing, docs]`, and the preparer's test is a plain check of `log`.

S0012 was done on `main` by the human (decision 33), and its three passages are true now (`docs/operator-guide.md:337`, the `FACTORY_IDLE_SHUTDOWN_MINUTES` row at line 71, "fifteen step names" at `docs/project-guide/README.md:93`). No story went outside the scope, and nothing from *Out of scope* was built.

## 2 Feature smoke test

Green. One Python walk ran through the real entry points, from a `mktemp -d` folder (`<tmp>` below), as `uv run python walk.py <tmp>`. It used `sh` stand-ins for `zfs`, the drop, `podman` and `sudo`, and a manual clock. Output (uv's `Bytecode compiled` line left out):

```text
1 template/factory/pipeline.yml ['approval', 'doing', 'docs'] 3
1 factory/pipeline.yml ['approval', 'doing', 'docs'] 2
1 demo/todo-service/project/factory/pipeline.yml ['approval', 'doing', 'docs'] 3
1 decide docs -> docs round 1
2 reset: ['zfs rollback -r tank/factory/vm@base', 'drop']
2 failed drop: snapshot command <tmp>/baddrop failed: sudo: a password is required | cause: NoneType
2 missing drop: snapshot command <tmp>/missing failed: [Errno 2] No such file or directory: '<tmp>/missing' | cause: FileNotFoundError
2 wired command: sudo -n /usr/local/bin/factory-drop-caches
4 False 4.0
5 refused: FACTORY_CLAUDE_HOME: missing
5 refused: FACTORY_CLAUDE_HOME: is not an absolute path
5 refused: FACTORY_CONTAINER_ENV: holds HOME, which the factory sets itself
5 refused: FACTORY_IMAGE_ID_FILE: missing
5 read: /srv/c
6 refused: Field required
6 refused: Value error, is not an absolute path
7 ['exit_status', 'stdout', 'stderr', 'timed_out', 'duration', 'stopped']
13 default cwd: / | ROOT: /
13 podman version: podman version 5.0.0
13 podman fault: container command <tmp>/podman-fault --version failed: boom
13 podman limit: container command <tmp>/podman-limit --version failed: no end within 1 s
8 granted minute 10: idle -> []
8 granted minute 29: idle -> []
8 granted minute 30: error -> []
8 granted minute 59: idle -> []
8 granted minute 60: idle -> ['idle shutdown: idle for 30 minutes, powering the machine off']
8 refused minute 10: idle -> []
8 refused minute 29: idle -> []
8 refused minute 30: error -> []
8 refused minute 59: idle -> []
8 refused minute 60: idle -> ['idle shutdown: idle for 30 minutes, powering the machine off', 'idle shutdown: power off failed: sudo: a password is required; the factory runs on']
8 missing minute 10: idle -> []
8 missing minute 29: idle -> []
8 missing minute 30: error -> []
8 missing minute 59: idle -> []
8 missing minute 60: idle -> ['idle shutdown: idle for 30 minutes, powering the machine off', "idle shutdown: power off failed: cannot start <tmp>/no-sudo: [Errno 2] No such file or directory: '<tmp>/no-sudo'; the factory runs on"]
8 sudo was asked: sudo -n /usr/bin/systemctl poweroff
11 ['self', 'git', 'settings']
```

The model's `container_env`, built directly through a variable typed `type[BaseModel]`:

```text
6 refused: Value error, holds HOME, which the factory sets itself
6 refused: Value error, holds NOT A NAME, which is not a variable name
6 built: ('HTTP_PROXY',)
```

The shell part, from the root of the checkout, with a stand-in `id` that prints `1000` first on `PATH` (the usage text that follows each refusal is cut here):

```text
$ sh -n vm/setup.sh && echo syntax-ok
syntax-ok
$ grep -c 'not installed; install it from your own copy of vm/' vm/setup.sh
2
--idle-shutdown 0: exit 2: setup.sh: --idle-shutdown takes at least 1 minute, not 0
--idle-shutdown x: exit 2: setup.sh: --idle-shutdown takes a whole number of minutes, not x
--idle-shutdown 30: exit 2: setup.sh: run as root
$ sh vm/setup.sh --help | grep -c -- --idle-shutdown
2
$ grep -rlE "def _in_order|def _lines_with|def _record_get_repo" tests | wc -l
0
$ grep -c "^_ROOT = " src/factory/adapters/{zfs_snapshots,power_off,podman_runs}.py
src/factory/adapters/zfs_snapshots.py:0
src/factory/adapters/power_off.py:0
src/factory/adapters/podman_runs.py:0
$ uv run pytest tests/test_shared_imports.py tests/test_suite_held_once.py tests/test_suite_leftovers.py tests/adapters/test_run_or_raise.py -p no:cacheprovider | tail -1
38 passed in 5.15s
```

What the walk shows:
- The reset's drop, `PodmanRuns.version` and the power-off now go through `run_or_raise`. Their error texts are those the stories promised: the start failure stays chained from its `OSError`, and the power-off keeps its prefix `cannot start <sudo>: `.
- A tick that handled its event with `error` at minute 30 starts a new stretch, so the machine is powered off only at minute 60.
- A refused or missing `sudo` is one log line, and the loop runs on.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

A0001 collected S0001 to S0011's observations (its check 4). Items 1 and 2 there became S0013 and S0014, and both are done. Items 3 to 6 stand as A0001 left them, each without a story:
- the three `sudoers` blocks of `vm/setup.sh`;
- the trailing space in `need_minutes`'s empty-value message (`vm/setup.sh:43`);
- the stale comment at `src/factory/application/stalls.py:112`, which still speaks of what "the agent left on the other branch";
- the look-alike `sh` stand-ins.

New from S0013 and S0014:

1. **The project guide's list of process users is stale.** `docs/project-guide/processes-and-checks.md:46` says the git wrapper, the make class and the `claude -p` runtime reach their tool through `run_process` and "no other module calls a command-line tool". Eight modules import `factory.adapters.process` (`tests/test_wrapper_search.py` pins them), and three of them now use `run_or_raise`, which the same section describes four paragraphs on. S0013's documenter noticed it (entry 21). Also, the `vm_support.py` line of `docs/project-guide/README.md:93` lacks a comma before "`entries`" (S0014 smoke tester, entry 27). → S0015.
2. **The new `ast` test of S0013 is not in mutmut's deselect list.** S0013's tester and coder flagged this (entries 8, 17). `tests/adapters/test_run_or_raise.py::test_the_wrappers_hold_no_copy_of_the_run_or_raise_block` reads the source through `source_search.SRC` (the imported package's folder) and checks that `ProcessRequest(` is built only in the function `run` of `podman_runs`. mutmut rewrites each method into trampoline copies with other names, so by my reading the test fails on mutmut's clean run and stops a sweep that includes `factory.adapters.podman_runs`. I did not run it (check 3). The fix is one `--deselect` line in `pyproject.toml`'s `[tool.mutmut]`, which is outside every write path. → for the human (6.4); no story.
3. **A one-off red test without a traceback.** `tests/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_process-group]` failed once under the factory's `make check` with `OSError: [Errno 22] Invalid argument` (S0014 entry 11). It passed in every later run, including mine. Only pytest's summary line is on record, so the cause cannot be traced. If it comes back, the `--tb=short` lines are needed. No story.
4. **The test name `test_only_the_three_wrappers_import_the_process_module`** in `tests/test_wrapper_search.py` checks a set of eight modules; its name is the same stale count as item 1. Renaming it needs the human's leave. I named it in S0015's Description for the human to add when refining, and gave it no story of its own.
5. `make types`' segfault (`Error 139`, A0001's item 7) did not recur in S0013's or S0014's journals.

## 5 Documentation

I read `README.md`, `docs/operator-guide.md` (*The machine*, the environment file's table, *The script*) and `docs/project-guide/` (the index, *Shared test helpers*, `processes-and-checks.md`, `stage-environment.md`) for the feature's subjects. A0001's three passages are repaired on `main`. S0013's paragraph on `run_or_raise` and S0014's lines in *Shared test helpers* agree with the code. One contradiction is left, inside one section: the first paragraph of *Starting a process* names three users of `run_process` and says there is no other, while the paragraph on `run_or_raise` in the same section names three more. It misleads an agent, not an operator, so it is a documentation repair and not a broken promise. → S0015, together with the missing comma. I found no example that no longer runs: S0013's and S0014's smoke commands still print their `Expect:` (shown in 2).

## 6 Decisions taken for the human

Accept or revisit:
1. Everything A0001 listed under its check 6: `feature.md` decisions 1 to 32, and the journal answers of S0002, S0003 and S0008 to S0011. Decision 33 is the human's own (S0012 done on `main`).
2. New answers and defaults in the journals:
   - S0013 entry 4: two rows added to criterion 1, the `OSError` text and a refused status printed on standard error.
   - S0013 entry 11: option A. Four earlier tests patch `run_process` on `factory.adapters.process`, and `run_or_raise` gets no extra keyword.
   - S0013 coder's default (entry 17, accepted by the reviewer in entry 19): `SystemctlPowerOff.power_off` catches a `PowerOffError` caused by an `OSError` and raises it again with the prefix `cannot start <sudo>: `, so that the text stays without a second fault argument on the helper.
   - S0014 entry 4: the leave for items 3 to 5, a row for `committed` and `values`, the `inspect.signature` check, and the rule that plain and annotated assignments count and imports do not.
3. Earlier tests changed. Each has its leave named in its reviewer's entry, and I found none without one:
   - S0013 (reviewer entry 19), under the human's leave of entry 11: `tests/adapters/test_zfs_snapshots.py` (three tests) and `tests/adapters/test_podman_runs_results.py::test_version_runs_under_two_minutes_by_default`.
   - S0014 (reviewer entry 23):
     - under the human's leave of entry 4: `tests/application/test_checkout_preparer.py`, `tests/git_support.py`, `tests/wiring_support.py`, `tests/entry/test_wiring_boundaries.py`, `tests/entry/test_wiring_one_environment.py` and `tests/test_suite_held_once.py`;
     - under the standing leave: `tests/vm_support.py`, `tests/test_vm_setup_text.py`, `tests/test_vm_setup_caches.py`, `tests/test_vm_setup_idle_shutdown.py`, `tests/contract_login_support.py`, `tests/domain/test_contract_login.py` and `tests/domain/test_contract_provider_limit.py`. The last is a follow-on of the rename that the Interface did not name, which the reviewer checked against the standing leave.
4. **The human's own, open:**
   - (a) The `--deselect` line for `tests/adapters/test_run_or_raise.py::test_the_wrappers_hold_no_copy_of_the_run_or_raise_block` in `pyproject.toml` (4.2), before the next sweep that mutates `podman_runs`.
   - (b) Change 3 is still not made. `factory/features/F0044-the-layers-go/feature.md` still has two decisions numbered 29 (lines 179 and 180), and `planning/v1.2-candidates.md:84-85` still says "decision 29 (b)" and "29 (c)". As A0001 noted, the change as written would leave two decisions numbered 30.
   - (c) Change 2 on `vm` (remove `zfs-fresh` and its `FACTORY_ZFS` line) cannot be seen from here.

## 7 Slow checks

The project offers nothing beyond `make check` but `make duplicates`, which prints `0 new, 41 known, 0 gone` (clean since S0013), and `make documents`, which is the docs stage's check. `make mutants` belongs to the sweep (check 3).

`make check` ran green here (`test: green (167.1 s)`, coverage 99.57 %, 7609 tests in `.reports/junit.xml`). The slowest tests take ten seconds each, all of them waits on a time limit:
- the `[255-at-the-limit]` and `[137-at-the-limit]` rows of `tests/adapters/test_podman_timeout_status.py`;
- six rows of `tests/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_group`;
- `tests/adapters/test_claude_runtime_provider_limit.py::test_a_call_past_its_time_limit_ends_time_limit_though_it_named_the_limit`;
- the `[timed-out-with-events]` row of `tests/adapters/test_opencode_resume_session.py`.

None of them is this feature's. S0013's slowest row (`[time-limit]`) takes one second.

Disk: at the previous record (`disk start`), `/srv/factory/vm` had 43.3 GB free with 1.2 GB used by the dataset. Now (`disk acceptance`) it has 40.7 GB free, with 1.2 GB used. The 2.6 GB less lies outside the dataset, on the volume that `state` and `/tmp` share. Neither story explains it: S0013 added one helper and S0014 changed only tests, with no dependency, image pin or large file.

It is the same pattern A0001 saw (48.5 to 45.8 GB). Across the two acceptances' records the volume lost 7.8 GB outside the dataset. At that rate, the remaining 40.7 GB lasts some fifteen more stories with a rebuild each. The likely cause, not checked from here, is the stage images and caches the rebuilds after each merge leave behind. `podman system df` and `podman image prune` on `vm` would tell. I left a `mktemp -d` folder of the smoke walk in `/tmp` (`/tmp/tmp.0d2swaasnp`, a few kilobytes) because its removal was refused in this stage; it goes with the stage's container.

## 8 Cost

156 runs, 303.8 min, 1242 turns, $46.84 for thirteen stories, about $3.60 a story. S0013 and S0014, the two stories added from A0001, cost 22 runs and $5.16 together:
- S0013: 10 runs, 22.2 min, $2.23. One coder stop for a test contradiction, answered in entry 11.
- S0014: 12 runs, 25.7 min, $2.93. One stall on the one-off red test (entry 11) and one review round over a copied helper and two split rows (entry 15).

**S0008 still stands out**: 24 runs, 46.1 min, $9.10, about a fifth of the feature, for the reasons A0001 gave (two intake questions, three review rounds that added criteria, the round cap). S0002 is second ($5.57). S0007 is the cheapest by cost ($2.10) and S0005 by runs (6).

Human interventions: 14 questions answered (13 questions, 1 round cap), and 0.4 h waited in all. Since A0001 there were three more: S0013 ×2 (entries 4 and 11) and S0014 ×1 (entry 4). S0008 needed the human most, with four interventions (three questions and the round cap), because its Interface stated behaviours that no criterion tested and its review kept adding criteria. S0002 is next with three.

## Proposed stories

- `backlog/F0045-S0015-the-project-guide-names-every-module-that-starts-a-process.md`: the first paragraph of *Starting a process* names the eight modules that start a program through `factory.adapters.process`, not three, so that it agrees with the `run_or_raise` paragraph below it. Also the missing comma in *Shared test helpers*. Documents only (4.1, 5).

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 1 story proposed

   1 Scope: none. All thirteen stories are merged, and their code is on the branch. S0013 holds the run-or-raise block once (`run_or_raise` and `ROOT`, no `_ROOT`, and `make duplicates` reports `0 new, 41 known, 0 gone`). S0014 cleared the five test leftovers. S0012 was done by the human on `main`. Nothing from *Out of scope* was built.
   2 Feature smoke test: green. One walk exercised every promise through its real entry point, with `sh` stand-ins and a manual clock: the definitions and `decide`, the reset and its drop, contract `4.0`, the settings reading and model, `ProcessResult`, `run_or_raise` through `PodmanRuns`, the idle shutdown with `sudo` granted, refused and missing, and `CheckoutPreparer`. It also ran `vm/setup.sh` and the guards (`38 passed`). The output is pasted in the report.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: `docs/project-guide/processes-and-checks.md:46` names three users of `run_process` where eight exist, and a comma is missing in *Shared test helpers*; this gives S0015. S0013's `ast` test is not in mutmut's deselect list in `pyproject.toml`; by my reading it would stop a sweep of `podman_runs`, and the fix is the human's. `test_process_session[run_process-group]` failed once with EINVAL (no traceback, passed since). `test_only_the_three_wrappers_import_the_process_module` checks eight modules. A0001's items 3 to 6 stand.
   5 Documentation: A0001's three passages are repaired. One contradiction remains within *Starting a process*, three users against the `run_or_raise` paragraph's three more; this gives S0015. No example fails to run.
   6 Decisions: A0001's list stands. New: S0013 entries 4 and 11 and the coder's power-off prefix default, and S0014 entry 4. Every earlier test that was changed has its leave. Open for the human: the mutmut `--deselect` line, change 3 (F0044 still has two decisions numbered 29), and change 2 on `vm`, which I cannot see from here.
   7 Slow checks: nothing beyond `make check` (green, 167.1 s, 99.57 %, 7609 tests). The slowest tests are 10 s time-limit waits, none of them this feature's. Free disk fell from 43.3 to 40.7 GB outside the dataset, 7.8 GB over the two acceptances' records; the feature's changes do not explain it, and stage images or caches on `vm` are likely. One `mktemp` folder was left in `/tmp` because its removal was refused.
   8 Cost: $46.84 over 156 runs, about $3.60 a story. S0013 and S0014 cost $5.16 together. S0008 stands out ($9.10, 24 runs). 14 human interventions (13 questions, 1 round cap) and 0.4 h waited; S0008 needed the human most (4).
