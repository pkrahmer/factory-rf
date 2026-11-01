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
