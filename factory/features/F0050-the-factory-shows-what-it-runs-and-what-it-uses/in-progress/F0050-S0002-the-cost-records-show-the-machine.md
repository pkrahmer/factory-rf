---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 539
comments_read: [6628314128]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T10:12:34.641436Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T10:12:34.648884Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T10:13:28.161841Z'
  stage: intake
  run: 6e70f038875745769734c3dc9db62f8b
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T10:21:39.749988Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T10:22:00.661881Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T10:22:47.457610Z'
  stage: intake
  run: 737b2ea3370c4482a31df1a77a922565
---

# The cost records show the image sizes, the free disk, the memory and the CPU

## Description

The growth that F0050 removes came as a surprise: nothing the factory writes says how large its images are, how much disk is left, or how much memory and CPU the containers took. On 2026-11-04 factory-vm held a 2.4 GB image of an idle instance, a stage image that was two thirds leftovers, and a memory peak of 8.1 GB of 15.6 GB, and each was found only by hand; npm's `EBADENGINE` warning was printed by every build for days before anyone read it. This story adds one object, `machine`, to every completed cost record, so that the records on GitHub and the Factory Timeline show the machine from a distance: the sizes of the base image and of the project's layer, the free space of the image store and of the stage's dataset, the memory peak and total, and the run's own CPU time and the time its work waited for a CPU or for memory. The waits are the measures that say whether the machine is too small. Every value is read from a file or a command the factory already reaches, at the run's start and end; nothing samples during the run.

The memory peak is the kernel's high-water mark of the cgroup that holds the factory user's containers, which cannot be reset on the kernels in use (6.8 on factory-vm): it is the highest use since that cgroup began, on a VM with lingering since boot, not the peak of the run. Its name says so, and the first record in which it rises names the run that raised it. The CPU time and the two waits are differences of the kernel's running totals between the run's start and end, so they are the run's own; they count every container of the factory user, so two instances that run at once on one machine see each other's load. A value the machine cannot give is `None`, and a machine that gives none has `"machine": null`. The factory's log line for each built image also gives the sizes and the count of the build's warnings.

## Interface

- A new model `MachineMeasures` in `factory.domain.cost_records`, frozen, unknown keys refused, every field optional (`None` when unknown):
  - `base_image_bytes` (`NonNegativeInt`): the size of the base image (`FACTORY_STAGE_IMAGE`) the run's image was built on;
  - `project_layer_bytes` (`NonNegativeInt`): the project image's size minus the base's; `0` when the project has no stage file;
  - `store_free_bytes` (`NonNegativeInt`): the free space of the file system that holds podman's image store;
  - `dataset_free_bytes` (`NonNegativeInt`): the free space of the stage's dataset (`FACTORY_WORKSPACE`), which on ZFS respects the dataset's quota;
  - `memory_peak_since_boot_bytes` (`NonNegativeInt`): `memory.peak` of the cgroup v2 slice of the user that runs the containers (`/sys/fs/cgroup/user.slice/user-<uid>.slice/`);
  - `memory_total_bytes` (`NonNegativeInt`): the machine's memory (`MemTotal` of `/proc/meminfo`);
  - `cpu_seconds` (non-negative finite float): the slice's `usage_usec` of `cpu.stat` at the run's end minus at its start;
  - `cpu_wait_seconds` (non-negative finite float): the `total` of the `some` line of the slice's `cpu.pressure`, end minus start;
  - `memory_wait_seconds` (non-negative finite float): the same of the slice's `memory.pressure`.
- `CostRecord` gets `machine: MachineMeasures | None = None`; like the other measures, a `started` record carries none.
- The two image sizes are measured when the factory builds or adopts an image (at start and after a changed stage file, F0049), not at every run; the free space, the memory peak and total, and the end readings at the record's completion; the start readings when the run starts. A start reading that is missing makes its difference `None`. The coder decides through which interfaces they are read, within the wrappers rule; the existing disk-space interface serves the free space.
- The records contract moves from `4.1` to `4.2` (an added optional field), and its schemas are regenerated with `uv run python -m factory.entry.contract`.
- The log line of a built project image becomes `stage image: built <identity> at <commit> in <s> s, base <GB> GB, layer <GB> GB, <n> warnings` (sizes with two decimals, a GB being 10^9 bytes: 1_580_000_000 gives `1.58`; the warnings are the build output's lines that hold `WARN` or `warning`, case ignored, except apt's `update-alternatives: warning:` lines, which a slim base prints for every manual page it lacks: 23 in each build of F0050-S0001's image on 2026-11-04); the factory's start writes `stage image: base <GB> GB` for an instance without a stage file.

## Acceptance criteria

1. A completed record carries `machine` with its nine fields; a `started` record with `machine` is refused, as for the other measures. Rows for each integer field at `0`, at a large value and at `-1` (refused); rows for each float field at `0.0`, at a large value, at `-0.5` and at NaN (both refused).
2. A measure that cannot be read (no such cgroup file, an image inspect without a size, a file system that cannot be read) is `None` in `machine` and does not fail the run or stop the factory; when nothing can be read, the record holds `"machine": null`.
3. `project_layer_bytes` is `0` for a project without a stage file and the difference of the two sizes for one with it; the two image sizes change only after a build or a return to the base.
4. `memory_peak_since_boot_bytes` is the value the slice's file holds at the record's completion. `cpu_seconds`, `cpu_wait_seconds` and `memory_wait_seconds` are the end reading minus the start reading in seconds; rows: a run whose totals grew, a run whose start reading is missing (`None`), and readings with a total that is not a number (`None`).
5. The records contract is `4.2`, and its schemas match the models.
6. The two log lines have the form of the Interface; rows for the warnings count: a build output with no warning (`0 warnings`), with npm's `npm warn EBADENGINE` line, with podman's `WARNING:` line, and with apt's `update-alternatives: warning: skip creation of ...` line (`0 warnings`).
7. `store_free_bytes` is the free space of the file system that holds podman's image store, `dataset_free_bytes` the free space of `FACTORY_WORKSPACE`, and `memory_total_bytes` is `MemTotal` of `/proc/meminfo` converted from kB to bytes (x1024); one row per field.
8. The line `stage image: base <GB> GB` is written once, at the factory's start, for an instance without a stage file; a row for its form. The sizes in both log lines are in GB of 10^9 bytes: 1_580_000_000 gives `1.58`.
9. An adopted image (an existing one reused with no build) gives both image sizes without a build; a row.
10. The warnings count is case-insensitive: a lowercase `warn` line and a mixed-case `Warning` line are each counted; one row each.
11. `make check` stays green.
12. docs: `docs/operator-guide.md`: in the section on cost records, the `machine` object and each of its fields, that the memory peak is a high-water mark since the slice began (since boot on a VM with lingering) and not the run's own peak, that the CPU time and the waits are the run's own but count every container of the factory user, and how to read them (CPU time over duration as the cores in use; a wait above zero as the machine being too small); in *The project's stage file*, the new log lines. `docs/decisions.md`: one entry that the records carry the machine's measures, why the peak is the slice's high-water mark (no reset before kernel 6.12, and sampling during a run was not worth its cost), and why the CPU and the waits are differences of running totals. `README.md` and the project guide: none.

## Smoke test

```bash
grep -cE '^RECORDS_CONTRACT = "4\.2"$' src/factory/domain/contract.py
grep -oE 'base_image_bytes|project_layer_bytes|store_free_bytes|dataset_free_bytes|memory_peak_since_boot_bytes|memory_total_bytes|cpu_seconds|cpu_wait_seconds|memory_wait_seconds' src/factory/domain/cost_records.py | sort -u | wc -l
uv run pytest tests/domain 2>&1 | tail -1
```

Expect: `1`, `9`, then a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: Questions (format check passed):

   1. Smoke test, third command: `uv run pytest tests/domain -q 2>&1 | tail -1`. `pyproject.toml` already sets `addopts = "-q ..."`, so the extra `-q` gives `-qq` and pytest prints no summary line. The `Expect:` ("a line that ends in `passed`") cannot be met. Proposed: drop the `-q` from the command.

   2. Interface: `store_free_bytes`, `dataset_free_bytes` and `memory_total_bytes` each state a source and a behaviour, but no criterion tests their values. Criterion 2 covers only the `None` side, and criterion 4 covers the peak and the CPU and wait fields. Proposed: add a criterion with a row per field. `store_free_bytes` is the free space of the file system holding podman's image store, `dataset_free_bytes` is the free space of `FACTORY_WORKSPACE`, and `memory_total_bytes` is `MemTotal` of `/proc/meminfo`, converted from kB.

   3. Interface: the log line shows "<GB> GB" with two decimals, but not whether a GB is 10^9 or 2^30 bytes. Two coders will read it two ways and both will pass any test. The Description's "2.4 GB" gives no hint. Proposed: 10^9 bytes, with a criterion row such as 1_580_000_000 giving `1.58`.

   4. Criterion 6 names rows only for the warnings count. The Interface also states a second log line, `stage image: base <GB> GB`, for an instance without a stage file, and the `built ... in <s> s, ... at <commit>` fields. The base-only line needs its own criterion row (the form, and that it is written at the factory's start).

   5. The Interface says the image sizes are measured "when the factory builds or adopts an image". Criterion 3 only says they change after a build or a return to the base. Adopting an image (reusing an existing one with no build) has no criterion. Proposed: add a row where an adopted image gives the sizes without a build.

   6. The warnings rule has no criterion for case-insensitivity ("WARN" or "warning", case ignored) beyond the three listed rows. For example, a lowercase `warn` line and a mixed-case `Warning` line. Proposed: one row for each.
4. 2026-11-04 human: Answers of the human: all six as proposed.

   1. Yes: drop the `-q` from the third command (`uv run pytest tests/domain 2>&1 | tail -1`); the `Expect:` stays.
   2. Yes: one criterion with a row per field: `store_free_bytes` is the free space of the file system that holds podman's image store, `dataset_free_bytes` the free space of `FACTORY_WORKSPACE`, `memory_total_bytes` is `MemTotal` of `/proc/meminfo` converted from kB to bytes (×1024).
   3. Yes: a GB in the log lines is 10^9 bytes; a row where 1_580_000_000 gives `1.58`.
   4. Yes: a row for `stage image: base <GB> GB`, its form, and that it is written once at the factory's start for an instance without a stage file.
   5. Yes: a row where an adopted image (an existing one reused with no build) gives both sizes without a build.
   6. Yes: one row for a lowercase `warn` line and one for a mixed-case `Warning` line, each counted.
5. factory: started intake as vm.
6. intake: accepted. The human's answers (journal entry 4) changed the story, and I wrote exactly those changes in: the smoke test's third command lost its `-q`; criteria 7 to 10 are new (the free-space and MemTotal rows, the base-only log line with the 10^9-byte GB, the adopted image, the case-insensitive warnings rows) and `make check` and `docs:` are now 11 and 12; the Interface's log line now says a GB is 10^9 bytes.
   - Interface: `MachineMeasures` and `CostRecord.machine` are named in `factory.domain.cost_records`, with each field's type and source; the log lines are given as exact forms. Concrete enough.
   - Criteria: each is testable by rows of one test. Every rule has a failing side: negative and NaN values refused, an unreadable measure is `None`, a missing start reading is `None`, a non-numeric total is `None`, and the warnings rows cover the 0-warning and counted cases, including case.
   - Smoke test: the three commands are runnable. Pytest's config sets `-q` already, so the third now has none and its `Expect:` can be met. Each expectation (`1`, `9`, a line ending in `passed`) is checkable.
   - Architecture: the measures sit in the domain DTOs, and reading is left to wrappers and the existing disk-space interface, which fits the layering.
   - Scope: it is within F0050's S0002 scope (the `machine` object, the log lines, contract 4.2) and touches nothing in "Out of scope".
