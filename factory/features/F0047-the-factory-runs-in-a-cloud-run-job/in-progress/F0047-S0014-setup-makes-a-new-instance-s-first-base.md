---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 495
comments_read: [6559346138]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-01T14:42:24.508460Z'
  lease_duration: 60
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
