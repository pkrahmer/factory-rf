---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 495
comments_read: []
handed_over: null
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
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, the script's steps: the step `datasets` makes the first base; the `dataset` item's row no longer asks the operator to take the base by hand for an instance made by the script (it still names the command for a dataset made by hand). `docs/decisions.md`: none. `README.md`: none.

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
