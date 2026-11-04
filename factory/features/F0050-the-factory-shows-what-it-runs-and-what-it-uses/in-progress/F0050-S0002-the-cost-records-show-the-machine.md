---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 539
comments_read: [6628314128, 6628465356, 6628999669, 6629159081]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-04T11:14:19.376017Z'
  lease_duration: 60
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
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T10:23:40.265823Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-04T10:25:20.148185Z'
  stage: tests
  run: 1a7a8f1e3e0d4a97843a1f22c478e400
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-04T10:36:09.501400Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-04T10:36:34.345949Z'
  stage: tests
- number: 11
  speaker: factory
  kind: crash
  at: '2026-11-04T10:39:38.314684Z'
  stage: tests
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-04T10:39:46.787555Z'
  stage: tests
- number: 13
  speaker: factory
  kind: crash
  at: '2026-11-04T10:44:59.770405Z'
  stage: tests
- number: 14
  speaker: factory
  kind: question
  at: '2026-11-04T10:44:59.770405Z'
  stage: tests
  blocked: crash_cap
- number: 15
  speaker: human
  kind: comment
  at: '2026-11-04T11:03:17.144832Z'
  stage: tests
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-04T11:03:30.082813Z'
  stage: tests
- number: 17
  speaker: tester
  kind: question
  at: '2026-11-04T11:05:57.070105Z'
  stage: tests
  run: 965b23d040cc4e28894a26125f54ff9b
  blocked: question
- number: 18
  speaker: human
  kind: comment
  at: '2026-11-04T11:14:12.043901Z'
  stage: tests
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-04T11:14:19.376017Z'
  stage: tests
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
7. factory: started tests as vm.
8. tester: I stopped partway. Criteria 1 and 5 are written. They fail for the right reason: collection stops on `ImportError: cannot import name 'MachineMeasures' from 'factory.domain.cost_records'`. `make lint` is green.

   - criterion 1: tests/domain/test_cost_record_machine.py::test_a_completed_record_carries_the_machine_with_its_nine_fields, ::test_a_started_record_with_the_machine_is_refused, ::test_a_machine_measure_is_accepted_only_in_its_range (rows: each integer field at 0, large and -1; each float field at 0.0, large, -0.5 and NaN)
   - criterion 5: tests/domain/test_contract_version_4_2.py::test_the_records_contract_is_at_version_4_2_with_the_machine_measures
   - Files created: tests/domain/test_cost_record_machine.py, tests/domain/test_contract_version_4_2.py. Module the runner could not import: `MachineMeasures` from `factory.domain.cost_records`.

   Questions:

   1. Criteria 2, 3, 4, 6, 7, 8, 9 and 10 have no interface to test against. The Interface says "the coder decides through which interfaces they are read". A test that feeds a cgroup file, a `/proc/meminfo`, an image size or a build output into the factory needs a named seam. The current `ImageBuild` carries only `output_tail`, and `Images` has no size and no store-path operation. Options:
      (a) The Interface names the seams. This is what I would choose:
      - pure domain functions in a new `factory.domain.machine`: `count_warnings(output: str) -> int`, `gigabytes(size: int) -> str` (`1_580_000_000` → `"1.58"`), `pressure_total_seconds(text: str) -> float | None` (the `some` line's `total`), `cpu_usage_seconds(text: str) -> float | None` (from `cpu.stat`), `mem_total_bytes(meminfo: str) -> int | None`, and `machine_differences(start, end) -> ...`;
      - `Images` gains `size_bytes(image: str) -> int | None` and `store_path() -> Path | None`, and `ImageBuild` gains `warnings: NonNegativeInt`;
      - a new application interface `MachineReadings` (memory peak, MemTotal, CPU and pressure totals, each `None` when unreadable), with an adapter that takes the cgroup slice folder and the meminfo path as constructor arguments, so tests use `tmp_path`;
      - the two log lines tested through `project_image_settings(..., report=...)` and `FakeImages`, and the base line through the factory's start (which function?).
      (b) Only the domain criteria (1 and 5) are tested, and criteria 2 to 10 are left to the review and the smoke test. I would not choose this.
      (c) I invent the seams myself. That would be guessing, and the coder would be bound to my guess.

   2. Criterion 5 moves the contract to 4.2. Two tests of earlier stories assert `"4.1"`, so they will go red: tests/domain/test_contract_version_4.py (`_version` and the `committed_is_generated(entry, "4.1")` rows) and tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version (`== "4.1"`). The standing leave does not cover this change. May I change them? Options: (a) both compare against `RECORDS_CONTRACT`, and test_contract_version_4.py keeps only its no-left-branch row; (b) both are set to `"4.2"`. I would choose (a), so that the next version bump does not break them again.
9. 2026-11-04 human: Answers of the human:

   1. **(a)** "The Interface names the seams." Exactly as you list them: the pure functions in a new `factory.domain.machine` (`count_warnings`, `gigabytes`, `pressure_total_seconds`, `cpu_usage_seconds`, `mem_total_bytes`, `machine_differences`); `Images.size_bytes(image) -> int | None` and `Images.store_path() -> Path | None`; `ImageBuild.warnings: NonNegativeInt`; the application interface `MachineReadings` with an adapter that takes the cgroup slice folder and the meminfo path as constructor arguments. The two build lines are tested through `project_image_settings(..., report=...)` and `FakeImages`. The base line `stage image: base <GB> GB` is tested through the same `project_image_settings` call for a project without a stage file, which is what the factory's start runs (`_ProjectImageStart._choose` in `factory.entry.run`). The coder may add arguments these names need, and says so in its entry.

   2. **(b)** "Both are set to `"4.2"`." The pinned value stays a deliberate guard: a version change must show up as a changed test, as in F0049 (decision 8). Leave for the tester: in `tests/domain/test_contract_version_4.py` the `"4.1"` pins and in `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` the `"4.1"` become `"4.2"`; nothing else in those modules.
10. factory: started tests as vm.
11. factory: crash 1: the run of stage tests ended without a result. Its work is discarded back to commit 08adcd814b8178dbdbc2269b2d733cc5a14da5c2.
12. factory: started tests as vm.
13. factory: crash 2: the run of stage tests ended without a result. Its work is discarded back to commit 0f4d410b4d8c7da0407b784d26baf08d552320a4.
14. factory: Stage tests crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
15. 2026-11-04 human: Retry. Both crashes of the tests stage came after the tester had finished with its structured output (10:39:05 and 10:41:54 UTC): most likely the result push was refused during GitHub's incident of 2026-11-04 (Git Operations degraded). The tester's work in the journal and its answers (entries 8 and 9) stand; start the tests stage again from them.
16. factory: started tests as vm.
17. tester: I stopped partway again. Every criterion with a seam named in entry 9 now has a test. Criteria 2, 3, 7 and 9 measure the record itself, and nothing named yet reaches it. Two earlier tests also pin the old build log line. The run (`uv run pytest -q` over the files below) fails for the right reason: collection stops on `ImportError` for `MachineMeasures` from `factory.domain.cost_records` and for `factory.domain.machine`. `make lint` is green.

    Mapping so far:
    - criterion 1: tests/domain/test_cost_record_machine.py::test_a_completed_record_carries_the_machine_with_its_nine_fields, ::test_a_started_record_with_the_machine_is_refused, ::test_a_machine_measure_is_accepted_only_in_its_range
    - criterion 4 (parsing only: totals in seconds, a total that is not a number is `None`): tests/domain/test_machine.py::test_the_pressure_total_is_the_some_line_in_seconds, ::test_the_cpu_usage_is_the_usage_of_cpu_stat_in_seconds
    - criterion 5: tests/domain/test_contract_version_4_2.py::test_the_records_contract_is_at_version_4_2_with_the_machine_measures
    - criterion 6: tests/domain/test_machine.py::test_the_warnings_of_a_build_output_are_counted (rows: no warning, npm, podman, apt) and tests/entry/test_wiring_stage_image_sizes.py::test_a_built_image_logs_its_sizes_and_its_warnings
    - criterion 7 (MemTotal only): tests/domain/test_machine.py::test_the_memory_total_is_mem_total_in_bytes
    - criterion 8: tests/entry/test_wiring_stage_image_sizes.py::test_a_start_without_a_stage_file_logs_the_base_size_once, and tests/domain/test_machine.py::test_a_size_is_given_in_gigabytes_of_ten_to_the_nine_bytes
    - criterion 10: test_the_warnings_of_a_build_output_are_counted, rows `lowercase-warn` and `mixed-case-warning`

    Files created: tests/domain/test_machine.py, tests/entry/test_wiring_stage_image_sizes.py. They join tests/domain/test_cost_record_machine.py and tests/domain/test_contract_version_4_2.py from entry 8.

    Files changed under entry 9's leave: tests/domain/test_contract_version_4.py and tests/domain/test_contract.py (`"4.1"` → `"4.2"`, nothing else).

    The entry test fakes the sizes with a subclass of `FakeImages` in the test module, which implements `size_bytes` and `store_path`. This means `FakeImages` needs no size argument named by me.

    Questions:

    1. How does a test reach the record's `machine`? Criteria 2 (a reading fails, so the field is `None`, the run goes on, and with nothing read the record holds `"machine": null`), 3 (layer `0` without a stage file; sizes change only after a build or a return to the base), 4 (differences of start and end, the peak at completion) and 7 (`store_free_bytes`, `dataset_free_bytes`) are about the completed record. Entry 9 named the functions, but not their signatures or how the readings reach `CostRecorder`. Options:
       (a) This is what I would choose. Name these:
       - `factory.domain.machine.MachineTotals` (frozen: `cpu_seconds`, `cpu_wait_seconds`, `memory_wait_seconds`, each `float | None`) and `machine_differences(start: MachineTotals | None, end: MachineTotals) -> MachineTotals`.
       - `MachineReadings` in `factory.application.machine`, with `totals() -> MachineTotals`, `memory_peak_bytes() -> int | None` and `memory_total_bytes() -> int | None`.
       - Its adapter `factory.adapters.machine_files.CgroupMachineReadings(slice_folder: Path, meminfo: Path)`, which I test with files in `tmp_path` for the peak, MemTotal, the differences and missing files.
       - `Boundaries` gains `machine: MachineReadings`. The `boundaries` fixture in `tests/conftest.py` gets a fake under `tests/`, and `Boundaries` gets the image sizes the start measured.
       - Record-level tests then run one stage through the existing world fixtures and read the written cost record, for criteria 2, 3 and 7.
       (b) Test only the adapter and domain functions, and leave the record-level parts of 2, 3 and 7 to the review and the smoke test.
       (c) You name other seams.

    2. Criterion 9, "an adopted image": the code has no adoption. `project_image_settings` always calls `Images.build` when there is a stage file, and nothing reuses an existing image without a build. What is adoption? Options:
       (a) The start finds the project tag already present (a new `Images` operation, for example `exists(tag)`) and skips the build. That is new behaviour, beyond this story's description.
       (b) It means only a return to the base (stage file removed), whose sizes are read without a build. I would choose this, and test it as a second `project_image_settings` call after the stage file is removed.
       (c) Drop criterion 9.

    3. The new build line breaks two tests of an earlier story. tests/entry/test_run_project_image_rebuild.py pins the old form `stage image: built … in 3 s` at lines 243 and 349. The standing leave does not cover changing them. May I change both expected lines to the new form (`…, base <GB> GB, layer <GB> GB, <n> warnings`) and give their `FakeImages` sizes through a shared subclass? I would move `SizedImages` from my new test into a `tests/sized_images.py` support module. Nothing else in that file changes.
18. 2026-11-04 human: Answers of the human:

    1. **(a)** As you name them: `factory.domain.machine.MachineTotals` (frozen; `cpu_seconds`, `cpu_wait_seconds`, `memory_wait_seconds`, each `float | None`) and `machine_differences(start: MachineTotals | None, end: MachineTotals) -> MachineTotals`; `MachineReadings` in `factory.application.machine` with `totals()`, `memory_peak_bytes()` and `memory_total_bytes()`; the adapter `factory.adapters.machine_files.CgroupMachineReadings(slice_folder: Path, meminfo: Path)`; `Boundaries` gains `machine: MachineReadings` and the image sizes the start measured, with a fake under `tests/` for the `boundaries` fixture in `tests/conftest.py` (adapted to the new field only). The record-level tests run one stage through the existing world fixtures and read the written cost record. The coder may add arguments these names need and says so in its entry.

    2. **(b)** "It means only a return to the base (stage file removed), whose sizes are read without a build." The story's word "adopts" meant no more than that; no new `Images` operation.

    3. Yes. Leave for the tester: in `tests/entry/test_run_project_image_rebuild.py` the two expected build lines (lines 243 and 349) take the new form, and their `FakeImages` get sizes through the shared subclass, which you move to the new support module `tests/sized_images.py`; nothing else in that file changes.
19. factory: started tests as vm.
