---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 495
comments_read: [6559346138]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-01T14:31:04.958121Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-01T14:31:04.964527Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-01T14:31:25.317949Z'
  stage: intake
  run: c6304173e89b475190dad749c89f528f
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-01T14:33:43.012449Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-01T14:34:00.823800Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-01T14:34:20.242310Z'
  stage: intake
  run: 89a9e095d2b947c08a45562a99e74804
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-01T14:34:40.477772Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-01T14:42:04.050054Z'
  stage: tests
  run: d19fdbf24b9e4d2db108b3516168f994
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-01T14:42:24.508460Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-01T14:48:37.502014Z'
  stage: doing
  run: 54be69606ef74694ba633b99da6eb67b
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-01T14:48:57.693066Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-01T14:49:47.976473Z'
  stage: review
  run: 99df4a7b75ef4b918a84776a398883a7
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-01T14:50:08.445188Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-01T14:50:22.034675Z'
  stage: doing
  run: a966809a286149318bb5c505e73a88e2
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-01T14:50:42.709818Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-01T14:56:40.258406Z'
  stage: tests
  run: 7b6f666db7c6407c87b31ccfa376bd9d
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-01T14:57:00.626663Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-01T15:03:06.269215Z'
  stage: doing
  run: d0a00eeaaa0d42fd8931583bc4785009
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-01T15:03:26.826763Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-11-01T15:03:57.608126Z'
  stage: review
  run: c59955f7f7624bae8989a6d1bd1249a8
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-01T15:04:17.946665Z'
  stage: docs
- number: 22
  speaker: documenter
  kind: result
  at: '2026-11-01T15:04:44.910258Z'
  stage: docs
  run: 3752b2a622b84a3e98ca8707166cfaf6
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-01T15:05:05.463633Z'
  stage: smoke-test
- number: 24
  speaker: smoke-tester
  kind: result
  at: '2026-11-01T15:05:27.613062Z'
  stage: smoke-test
  run: cd530a1ca6ab4768a496cbd3276db0d9
---

# Setup makes a new instance's first base

## Description

A new instance made by `vm/setup.sh` stops at its first preflight: `snapshot command zfs rollback -r <dataset>@base failed: cannot open '<dataset>@base': dataset does not exist` (the Kumpel trial of 2026-11-01, the instance `demo`). The script makes the dataset but not its base; the operator guide names the step only in the error text of the preflight's `dataset` item ("make it with zfs create, and its base with zfs snapshot <dataset>@base"). Worse, the failed first start left a folder in the dataset owned by a uid mapped from a container, and a base taken afterwards by hand kept it, so every later rollback restored the wrong owner (`/work/checkout/.git: Permission denied`) until the folder was removed and the base taken again. This story makes the step `datasets` take the first base itself, right after the dataset is made and given to `factory`, while it is still empty and rightly owned. Unchanged: an instance that already has a base (its base is never touched), every other step, the step names and their order, and the factory's own handling of the base.

## Interface

`vm/setup.sh` (shell), the step `datasets`: after the dataset exists, has its quota and its mount point belongs to `factory`, when `zfs list -H -o name -t snapshot <dataset>@base` finds no snapshot, the script runs `zfs snapshot <dataset>@base` and reports `changed "made the first base <dataset>@base"`; when the base exists, nothing is done. The step's closing line reads `setup: datasets: found <pool>/factory and <dataset> at <base>/work with the quota <quota> and its base` (or the `said` form with the changes, as today). A failing `zfs snapshot` stops the script as any other failing command of the step does today.

Tests (the tester writes them): `tests/test_vm_setup_first_base.py`, through `tests/vm_support.py::run_setup` with a stand-in `zfs` that records its calls and answers `list` for the dataset and, by row, for its base. `tests/test_vm_setup.py` and `tests/test_vm_setup_text.py` pass unchanged, except where they compare the step's closing line, which may change under this story's leave to that exact line.

## Acceptance criteria

1. A run where the dataset is made and has no base calls `zfs snapshot <dataset>@base` once, after the dataset's `create`, its quota and the ownership of its mount point, and the step's output names `made the first base <dataset>@base`.
2. A run where the base exists calls no `zfs snapshot` and changes nothing in the step.
3. The `zfs snapshot` call comes before the step `delegation` (the first base is root's, taken before the factory's rights are given).
4. The step's closing line ends with `and its base`.
5. A run where the stand-in `zfs` exits non-zero on `snapshot` exits non-zero, and the step's closing line is not printed.
6. A run where the dataset already exists without a base calls `zfs snapshot <dataset>@base` once and the step's output names `made the first base <dataset>@base`.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`, the script's steps: the step `datasets` makes the first base; the `dataset` item's row no longer asks the operator to take the base by hand for an instance made by the script (it still names the command for a dataset made by hand). `docs/decisions.md`: none. `README.md`: none.

## Smoke test

```bash
grep -c 'zfs snapshot "$dataset@base"' vm/setup.sh
```
Expect: `1`

```bash
uv run pytest tests/test_vm_setup_first_base.py tests/test_vm_setup.py 2>&1 | tail -1
```
Expect: one line that holds `passed` and neither `failed` nor `error`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-11-01 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. Questions:
   1. The Interface says a failing `zfs snapshot` stops the script like any other failing command of the step. No criterion tests that failing side (stand-in `zfs` exits non-zero on `snapshot`: the script exits non-zero and the step's closing line is not printed). I would add it as a criterion before `make check`.
   2. The Interface takes the snapshot whenever `<dataset>@base` is missing, whatever the dataset's origin. Criterion 1 covers only "the dataset is made and has no base". The case of a dataset that already exists (made by hand) without a base has no criterion: a coder could take the base only inside the `zfs create` branch and still pass criteria 1 and 2. I would reword criterion 1 to cover both ("the base is missing, with the dataset just made or already there") or add a second criterion for the existing dataset without a base. I would add the second criterion.
   3. The Interface says the closing line may take the `said` form with the changes "as today". Criterion 4 tests only the ending `and its base`. The change message `made the first base <dataset>@base` appearing in the `said` form is covered by criterion 1 only loosely ("the step's output names..."). I would accept it as written if you confirm that criterion 1 covers it; otherwise add the closing-line form with the change.
   4. Criterion 1 orders the snapshot after create, quota and ownership. Criterion 3 orders it before `delegation`. Both can be tested by the stand-in's call log, but ownership is a `stat`/`install` call and not a `zfs` call. State how the test sees "after ownership" (for example, through the `install` call recorded by the harness, or through the text order in `vm/setup.sh`). I would choose the recorded call order if `run_setup` records `install`, otherwise drop the ownership part from the criterion.
4. 2026-11-01 human: Answers to question 3:

   1. Yes: add the criterion, a stand-in `zfs` that fails on `snapshot`: the script exits non-zero and the step's closing line is not printed.
   2. Yes: a second criterion for a dataset that already exists without a base (the base is taken), beside criterion 2 (an existing base: nothing is done).
   3. Confirmed: criterion 1's "the step's output names `made the first base <dataset>@base`" covers the `said` form with the change; no further criterion.
   4. The run's recorded `zfs` calls give the order against `create` and the quota; the order against the ownership of the mount point is tested from the script's text (the `zfs snapshot` line comes after the `install -d -o factory` line of the step), as the setup tests already test order from the text.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: `vm/setup.sh`, step `datasets`, names the command (`zfs snapshot <dataset>@base`), the check (`zfs list -H -o name -t snapshot`), the change message and the exact closing line; the tests are named (`tests/test_vm_setup_first_base.py` through `tests/vm_support.py::run_setup`). Each stated behaviour has a criterion: the base taken (1, 6), an existing base left alone (2), the closing line (4), the failing `zfs snapshot` (5).
   - Criteria: each is testable by one test function. Criterion 1's order against `create` and the quota is read from the recorded `zfs` calls. Its order against the ownership of the mount point is read from the script's text (the `zfs snapshot` line after the `install -d -o factory` line), as the human said in journal entry 4, answer 4. Both sides of the base rule are covered (no base: 1, 6; base present: 2), and so is the failing `zfs snapshot` (5). Per entry 4, answers 1 and 2, I added two criteria, 5 (stand-in `zfs` fails on `snapshot`: non-zero exit, no closing line) and 6 (existing dataset without a base gets the base); the closing two are now 7 and 8. Answer 3 confirmed that criterion 1 covers the `said` form with the change, so no more was added.
   - Smoke test: `grep -c 'zfs snapshot "$dataset@base"' vm/setup.sh` is runnable with `Expect: 1`. The pytest command passes no `-q`, and the `Expect:` (a line with `passed`, neither `failed` nor `error`) can be checked against the output.
   - Architecture: the change is confined to `vm/setup.sh` (the coder's write path) and the operator guide; no layer of `src/factory` is touched.
   - Scope: within F0047's scope. S0014 is listed in the feature's stories, and decision 22 of the feature names it. It touches none of the feature's out-of-scope items.
7. factory: started tests as vm.
8. tester: Wrote the tests for the step `datasets` taking the first base. They run `vm/setup.sh` for real through `tests/vm_support.py::run_setup`, with stand-ins placed first on `PATH`. The stand-ins are `id`, `mktemp` (which writes into `tmp_path`), `dpkg-query`, `grep`, `zpool`, `loginctl`, `stat`, `install` and `zfs`, and each one records its calls. The stand-in `zfs` answers `list` for `tank/factory` and, depending on the row, for the dataset and for `<dataset>@base`. It answers `get` with lz4/off and the quota, and it can fail on `snapshot`. It also exits 1 on `zfs allow -u`, which ends every run at the step `delegation`, so the script writes nothing outside `tmp_path`.

   Criteria → tests:
   - criterion 1: tests/test_vm_setup_first_base.py::test_a_made_dataset_gets_its_first_base_after_its_create_and_quota. One `zfs snapshot tank/factory/vm@base`, recorded after the `create` and the `set quota=` calls. The order against ownership is checked from the script's text, as entry 4 answer 4 says: the `install -d -o factory` line comes before `zfs snapshot` in the step. The step's output must name `made the first base …`.
   - criterion 2: tests/test_vm_setup_first_base.py::test_an_existing_base_is_left_alone_and_the_step_changes_nothing. No `snapshot`, `create` or `set` call and no `install` call; the step's one line is the full `found … and its base` line.
   - criterion 3: tests/test_vm_setup_first_base.py::test_the_first_base_is_taken_before_the_delegation. The snapshot call comes before the first `zfs allow` call.
   - criterion 4: tests/test_vm_setup_first_base.py::test_the_step_s_closing_line_ends_with_its_base
   - criterion 5: tests/test_vm_setup_first_base.py::test_a_failing_snapshot_stops_the_script_before_the_step_s_closing_line
   - criterion 6: tests/test_vm_setup_first_base.py::test_an_existing_dataset_without_a_base_gets_its_first_base
   - criteria 7 and 8: none (`make check` and docs).

   Files created: tests/test_vm_setup_first_base.py. No existing test file was changed.

   `make test`: only the 6 new tests fail, each for the right reason. Five find no `snapshot` call. The other one gets `setup: datasets: found … with the quota 30G` without `and its base`. The runs reached the step's closing line, so the stand-ins work. Every module imported, so there are no collection errors. `make lint` is green.

   Open: none. The coder will see that `tests/test_vm_setup_text.py` does not compare the step's closing line today, so the leave to change that exact line is not needed so far.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/test_vm_setup_first_base.py::test_an_existing_dataset_without_a_base_gets_its_first_base - AssertionError: assert [] == [['snapshot',...ory/vm@base']]
9. factory: started doing as vm.
10. coder: Built: the step `datasets` in `vm/setup.sh` now takes the first base. It does this after the ownership check of `$base/work` and before the step's closing line. If `zfs list -H -o name -t snapshot "$dataset@base"` finds no snapshot, the step runs `zfs snapshot "$dataset@base"` and records `changed "made the first base $dataset@base"`. The closing line now ends with `and its base`. Under `set -eu`, a failing `zfs snapshot` stops the script before that line. All six tests in `tests/test_vm_setup_first_base.py` pass, `tests/test_vm_setup.py` and `tests/test_vm_setup_text.py` pass unchanged, and `make check` is green.

    Main choice: the base check stands on its own after the dataset, quota and ownership checks, so a dataset that already exists without a base gets one too. The alternative I rejected was to take the snapshot inside the `zfs create` branch. That would skip a dataset made by hand without a base, and the human's answer 2 in entry 4 rules it out. A one-line comment says why the base is taken there: the dataset is still empty and belongs to factory, and every rollback restores that owner.

    Refactor: I read the diff (one `if` block and the changed closing line) and found nothing to change.

    Description: the journal changed nothing in the meaning beyond what intake already wrote into the criteria.

    Noticed, not touched: the operator guide's steps and the `dataset` item's row still tell the operator to take the base by hand. That is criterion 8, for the docs stage.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
11. factory: started review as vm.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`: the changes to `vm/setup.sh` and the new `tests/test_vm_setup_first_base.py`. I read them against the criteria and the Interface.

    The script change does what the Interface says. The base check comes after the `create`, the quota and the `install -d -o factory` ownership step, and before the closing line. It runs `zfs list -H -o name -t snapshot "$dataset@base"`, then `zfs snapshot` and `changed "made the first base …"`. The closing line ends with `and its base`. Because the script runs under `set -eu` and the snapshot sits in the body of the `if`, not its condition, a failing snapshot stops the step. Each of criteria 1 to 6 has a test that checks what the criterion says. The rule's failing side, a failing `zfs snapshot`, is tested (criterion 5). The coder's journal entry 10 records `check: green` and `duplicates: 0 new`. The new stand-in rig is not a copy of an existing helper: the rigs in `tests/vm_support.py::run_job_start`, `tests/zfs_support.py` and `tests/test_vm_setup_code_url.py::_stand_ins` differ in what they record and answer. This review is round 0, so a point about the test file's quality still counts as a finding.

    Findings:
    1. `tests/test_vm_setup_first_base.py::test_a_made_dataset_gets_its_first_base_after_its_create_and_quota` and `::test_an_existing_dataset_without_a_base_gets_its_first_base`. These are two rows of one rule, "a missing base is taken once and named", written as separate test functions that repeat the same two assertions. One asserts that the snapshot calls equal `[["snapshot", BASE]]`, the other that `MADE_BASE` appears in `datasets_lines()`. CLAUDE.md *Tests* says the sides of one rule are rows of one parametrized test. Fix: the tester merges them into one parametrized test with rows for a dataset that was just made and a dataset that already exists, ids naming the case. The order checks of criterion 1 (against `create`, the quota and the `install -d -o factory` text) stay in their own test on the `made` fixture.

    Earlier tests: none. `git diff --name-status main...HEAD` shows only the added test file `tests/test_vm_setup_first_base.py`, and `vm/setup.sh` is not a test.
13. factory: started doing as vm.
14. coder: The review's only finding (entry 12, finding 1) asks for a change to the tests, not to the code. Coders never edit tests, so the tester makes this change. The tester merges `tests/test_vm_setup_first_base.py::test_a_made_dataset_gets_its_first_base_after_its_create_and_quota` and `::test_an_existing_dataset_without_a_base_gets_its_first_base` into one parametrized test. That test asserts one `snapshot` call equal to `[["snapshot", BASE]]` and that `MADE_BASE` appears in the step's lines. It has two rows, one for a dataset that was just made and one for a dataset that already exists, each with an id that names its case. The order checks of criterion 1 stay in their own test on the `made` fixture: against `create` and the quota from the recorded calls, and against `install -d -o factory` from the script's text.

    I changed no code. The reviewer found `vm/setup.sh` correct against every criterion, and `make check` was green in round 0 (entry 10). Noticed, not touched: the operator guide still tells the operator to take the base by hand. That is criterion 8, for the docs stage.
15. factory: started tests as vm.
16. tester: Made the test change from the reviewer's finding 1 (entry 12), which the coder's entry 14 names. The file is this story's own test file, `tests/test_vm_setup_first_base.py`; I changed no other test file.

    Change: I merged `test_a_made_dataset_gets_its_first_base_after_its_create_and_quota` and `test_an_existing_dataset_without_a_base_gets_its_first_base` into one parametrized test, `test_a_missing_base_is_taken_once_and_named`. It asserts that the `zfs` calls hold exactly one snapshot, `[["snapshot", BASE]]`, and that `MADE_BASE` appears in the step's lines. It has two rows: `made` (no dataset, quota `none`, owner `root:root`, the same machine as the `made` fixture) and `existing` (the dataset exists, with no base). Criterion 1's order checks are in their own test, `test_a_made_dataset_s_first_base_follows_its_create_quota_and_owner`, on the `made` fixture: the snapshot comes after `create` and the quota in the recorded calls, and after `install -d -o factory` in the script's text. Nothing that was asserted before was dropped.

    Criteria → tests now:
    - criterion 1: tests/test_vm_setup_first_base.py::test_a_missing_base_is_taken_once_and_named[made] and ::test_a_made_dataset_s_first_base_follows_its_create_quota_and_owner
    - criterion 2: tests/test_vm_setup_first_base.py::test_an_existing_base_is_left_alone_and_the_step_changes_nothing
    - criterion 3: tests/test_vm_setup_first_base.py::test_the_first_base_is_taken_before_the_delegation
    - criterion 4: tests/test_vm_setup_first_base.py::test_the_step_s_closing_line_ends_with_its_base
    - criterion 5: tests/test_vm_setup_first_base.py::test_a_failing_snapshot_stops_the_script_before_the_step_s_closing_line
    - criterion 6: tests/test_vm_setup_first_base.py::test_a_missing_base_is_taken_once_and_named[existing]
    - criteria 7 and 8: none (`make check` and docs).

    Files changed: tests/test_vm_setup_first_base.py. No files were created. Every module imported. `make test`: green, because the code from entry 10 is already in place. `make lint`: green.

    `lint`: lint: green (0.2 s)
    `test`: test: green (163.7 s)
17. factory: started doing as vm.
18. coder: Round 1: the review's only finding (entry 12, finding 1) was a change to the tests. The tester made it in entry 16: two test functions in `tests/test_vm_setup_first_base.py` became one parametrized test, `test_a_missing_base_is_taken_once_and_named[made|existing]`, and the order checks became their own test. I changed no code, because the finding needs none. The code is the round-0 change to `vm/setup.sh`, step `datasets` (entry 10), which the reviewer found correct against every criterion.

    Built, unchanged since round 0: `vm/setup.sh`. After the dataset, quota and ownership checks, `zfs list -H -o name -t snapshot "$dataset@base"` looks for the base. If there is none, `zfs snapshot "$dataset@base"` takes it and the step records `changed "made the first base …"`. The closing line ends with `and its base`.

    Main choice, unchanged: the base check runs on its own after the ownership check, so a dataset made by hand without a base also gets one. I rejected taking the snapshot inside the `zfs create` branch, which entry 4 answer 2 rules out.

    Refactor: no new diff this round, so nothing to change. The journal did not change the meaning of the Description.

    Noticed, not touched: the operator guide still tells the operator to take the base by hand. That is criterion 8, for the docs stage.

    `check`: check: green (test: green (165.1 s))

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
19. factory: started review as vm.
20. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (the change to `vm/setup.sh` and the new `tests/test_vm_setup_first_base.py`) against the work item's criteria and Interface. This is round 1.

    What I checked:
    - `vm/setup.sh`, step `datasets`. The base check comes after the `create`, the quota and the `install -d -o factory` ownership block, and before the closing line. If `zfs list -H -o name -t snapshot "$dataset@base"` finds nothing, the step runs `zfs snapshot "$dataset@base"` and then `changed "made the first base $dataset@base"`. The closing line ends with `and its base`. The snapshot sits in the body of the `if`, not its condition, so under `set -eu` a failing snapshot stops the step before the closing line. An existing base is left alone. This matches the Interface and the Description.
    - Each criterion's test:
      - Criteria 1 and 6: `test_a_missing_base_is_taken_once_and_named[made|existing]`. It checks for exactly one `["snapshot", BASE]` call and that the change message is printed.
      - Criterion 1's order: `test_a_made_dataset_s_first_base_follows_its_create_quota_and_owner`. The recorded calls give the order against `create` and the quota. The script's text gives the order against the ownership, as the human said in entry 4, answer 4.
      - Criterion 2: `test_an_existing_base_is_left_alone_and_the_step_changes_nothing`. No snapshot, create, set or install call, and the step prints only the full `FOUND` line.
      - Criterion 3: `test_the_first_base_is_taken_before_the_delegation`.
      - Criterion 4: `test_the_step_s_closing_line_ends_with_its_base`.
      - Criterion 5: `test_a_failing_snapshot_stops_the_script_before_the_step_s_closing_line`.
    - The Interface states one failing side, the failing `zfs snapshot`, and criterion 5 tests it. The Interface states no numeric limit.
    - Round 0's finding (two test functions for one rule) is fixed: they are now one parametrized test.
    - The coder's entry 18 records `check: green` and `duplicates: 0 new`.
    - The Description matches what was built. Criterion 8 (docs) still says what the operator guide must say.

    no findings

    Earlier tests: none changed. `git diff --name-status main...HEAD` lists only `A tests/test_vm_setup_first_base.py` among the tests. `tests/test_vm_setup.py` and `tests/test_vm_setup_text.py` are untouched.
21. factory: started docs as vm.
22. documenter: Docs for S0014, read against `vm/setup.sh` (the step `datasets` takes the first base).

    Changed: `docs/operator-guide.md`, two places.
    - The script's step 5 (`datasets`) now says it takes the first base `<pool>/factory/<instance>@base`. It takes it after the quota and the ownership of the mount point and before the delegation of step 6. An existing base is never touched, and a dataset that exists without a base gets one.
    - The preflight's `dataset` row still gives the `zfs create` / `zfs snapshot <dataset>@base` message. It now adds that an instance made by `vm/setup.sh` already has both, and that the message concerns a dataset made by hand.

    Cross-read and found current: README.md (no mention of the base). The operator guide's definition of the dataset and base (line 370), the sudoers paragraph (`zfs snapshot` on `<dataset>@base`), and the `agent-run-probe` text on a missing `@base`. All of these match the script.

    I did not run `make check`, because I changed only documents. No findings for the coder. `docs/decisions.md` and `README.md` need no change, as criterion 8 says. I found no stale text outside this story.

    `check`: check: green (not run again: passed on tree 5f8ee8a1ccbb at 2026-11-01T15:00:10Z)
    `secrets`: secrets: green (1.2 s)
    `documents`: documents ok
23. factory: started smoke-test as vm.
24. smoke-tester: Ran both smoke test commands from the repository root, as written and in order. I fixed nothing.

    1. `grep -c 'zfs snapshot "$dataset@base"' vm/setup.sh`
    ```
    1
    ```
    Met `Expect: 1`.

    2. `uv run pytest tests/test_vm_setup_first_base.py tests/test_vm_setup.py 2>&1 | tail -1`
    ```
    17 passed in 2.63s
    ```
    Met the `Expect:` line: one line with `passed`, and neither `failed` nor `error`.

    Read against the acceptance criteria once more. I read `vm/setup.sh` lines 204–220 and `docs/operator-guide.md` (step 5 at line 557, the `dataset` row at line 1034). Nothing contradicts a criterion:
    - Criteria 1 and 6: in the script, the snapshot check (`zfs list -H -o name -t snapshot "$dataset@base"`) stands on its own after the `create`, the quota and the `install -d -o factory` block. When it finds no base, it runs `zfs snapshot` and `changed "made the first base $dataset@base"`.
    - Criterion 3: the check comes before the `delegation` step.
    - Criterion 4: the closing line ends with `and its base`.
    - Criterion 8: step 5 of the operator guide says the step takes the first base. The `dataset` row still names `zfs snapshot <dataset>@base` for a dataset made by hand, and says an instance made by the script already has both.
    - Criterion 7 (`make check`): I did not run it in this stage. Entry 18 records it green, and the docs stage reused that passed result (entry 22).

    Findings: none.
