---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 467
comments_read: [6424960438, 6425166909, 6425444781]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T19:07:38.338745Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T19:07:38.344777Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-26T19:08:05.983084Z'
  stage: intake
  run: cfc5a10b4ae348729679b2a2426bb404
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-26T19:09:24.930116Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-26T19:09:42.712601Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-26T19:10:09.936118Z'
  stage: intake
  run: 38f29d502f9e4719b5399469d70af190
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-26T19:10:30.477630Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-26T19:17:06.823371Z'
  stage: tests
  run: e7b1b9fe75f54cebbeaf15a822316aee
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-26T19:19:28.492168Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-26T19:19:46.642840Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-10-26T19:25:56.732951Z'
  stage: tests
  run: 310d1e335ef340959314d313873c18fe
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-26T19:26:17.344951Z'
  stage: doing
- number: 13
  speaker: coder
  kind: question
  at: '2026-10-26T19:31:19.619125Z'
  stage: doing
  run: 937f33f43732483b866c0f5255ac6ba4
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-10-26T19:33:42.377699Z'
  stage: doing
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-26T19:34:00.294096Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-10-26T19:34:21.035985Z'
  stage: doing
  run: d3fcf2979a3e4bfaaac2d4926e52ced9
---

# The reset drops the page cache after the rollback

## Description

A page that a stage wrote through `mmap` survives `zfs rollback` in the kernel's page cache: after the rollback the file has the snapshot's size but the newer page's content, so a file the stage made shorter reads as zero bytes past its end and one of the same size reads as the stage's text cut off. Git's stat cache then calls the file clean, the sync does not repair it, and the fault reaches `@base` (found and reproduced on `vm` on 2026-10-25 and 2026-10-26, `planning/v1.2-candidates.md`, "The cause of the zero bytes found"). Dropping the clean page cache after the rollback clears it. Today `vm` does that through a wrapper made by hand (`FACTORY_ZFS=/usr/local/bin/zfs-fresh`, which runs `sudo -n /usr/local/bin/factory-drop-caches` after a rollback). This story moves the fix into the factory and the machine's script, so that no setting can leave it out (decision 15 of `feature.md`): `ZfsSnapshots.reset()` runs the cache drop command right after a rollback that succeeded, and a fault of that command is a `SnapshotError` like a fault of `zfs`; the wiring gives every `ZfsSnapshots` the one command `sudo -n /usr/local/bin/factory-drop-caches`; and `vm/setup.sh` gains the step `caches`, which writes that helper and the one `sudoers` rule that lets `factory` run it, on every run, with or without `--sudoers`. What stays: the four `zfs` commands and their faults, `advance`, `changed_paths`, `version` and `dataset_exists` (none of them drops the cache), `FACTORY_ZFS` and the `--sudoers` fallback, the fake snapshots, every other step of the script. The sync's check of content against git's stat cache is not built (decision 16).

## Interface

`factory.adapters.zfs_snapshots` (`adapters`):

```python
DROP_CACHES_COMMAND = ("sudo", "-n", "/usr/local/bin/factory-drop-caches")

class ZfsSnapshots(Snapshots):
    def __init__(
        self,
        dataset: str,
        mount_point: Path,
        *,
        drop_caches: tuple[str, ...],
        executable: str = "zfs",
        time_limit: timedelta = SNAPSHOT_TIME_LIMIT,
    ) -> None: ...
```

- `drop_caches` is required and names the program first; an empty tuple raises `ValueError`.
- `reset()`: runs `zfs rollback -r <dataset>@base` as today; when that exits 0, runs `drop_caches` under the same `time_limit` and returns when it exits 0. A failed rollback raises its `SnapshotError` as today, and the drop is not run.
- A fault of the drop is `SnapshotError(command, detail)` with `command` the drop's words joined by one space (`sudo -n /usr/local/bin/factory-drop-caches`) and `detail` formed as for the `zfs` commands: the failure's exit status and last printed line, the time limit reached, or the error of a program that cannot be started.
- `advance()`, `changed_paths()`, `version()` and `dataset_exists()` run no drop.

`factory.entry.wiring` (`entry`): `_container_adapters`, the one place that builds a `ZfsSnapshots` (for `build_boundaries` and for the preflight's items), builds `ZfsSnapshots(settings.dataset, settings.workspace, drop_caches=DROP_CACHES_COMMAND, executable=settings.zfs_executable)`; so every reset of an instance drops the cache, the agent-run probe's included. No setting names the command.

`vm/setup.sh` (POSIX `sh`), a new step `caches` right after the step `sudoers` and before the step `folders`, on every run (it does not depend on `--sudoers`), one line on standard output beginning `setup: caches: ` with what it changed or what it found:

- `/usr/local/bin/factory-drop-caches`, written by root with `install -m 0755` only when its text differs, holding exactly these three lines:

  ```sh
  #!/bin/sh
  sync
  echo 1 > /proc/sys/vm/drop_caches
  ```

- `/etc/sudoers.d/factory-drop-caches`, mode `0440`, written only when its text differs, holding exactly one rule, `factory ALL=(root) NOPASSWD: /usr/local/bin/factory-drop-caches`, checked with `visudo -cf`; a refused check removes the file, prints `setup: caches: visudo -cf refused /etc/sudoers.d/factory-drop-caches; removed it` to standard error and exits 1, as the step `sudoers` does.

Both texts equal the files `vm` holds today (made by hand from `planning/overnight/gcp-trial-checklist-2026-10-26.md`), so the first run on `vm` reports them found.

Tests (the tester writes and changes them; the leave is decision 22 of `feature.md`): new tests at the tester's choice, for example `tests/adapters/test_zfs_snapshots_drop_caches.py` (a stand-in for the drop written under `tmp_path`, never the real `sudo`), `tests/entry/test_wiring_drop_caches.py` and `tests/test_vm_setup_caches.py`. Earlier tests, each keeping its name and what it checks:

- `tests/zfs_support.py`: `snapshots_on` passes a drop stand-in that succeeds and records nothing the existing tests read.
- `tests/adapters/test_zfs_snapshots.py`: the constructions of `ZfsSnapshots` in `test_a_failed_reset_names_its_detail`, `test_the_default_time_limit_is_ten_minutes_and_reaches_run_process` and `test_the_time_limit_is_named_in_whole_seconds_rounded_up` gain `drop_caches`; where the `Recorder` of `tests/run_process_recorder.py` answers the rollback with success, the test reads the rollback's request, not a count of all requests.
- `STEPS` of `tests/vm_support.py` gains `caches` right after `sudoers`; `ORDERED_COMMANDS` of `tests/test_vm_setup_text.py` may gain `/etc/sudoers.d/factory-drop-caches` between `/etc/sudoers.d/factory-zfs` and `/home/factory/.secrets`.

## Acceptance criteria

1. The reset drops after the rollback (one test, a stand-in `zfs` and a stand-in drop under `tmp_path` that append their words to one shared file): `reset()` of `ZfsSnapshots("tank/factory/vm", <mount>, drop_caches=(<drop stand-in>,), executable=<zfs stand-in>)` leaves exactly two lines in the file, `rollback -r tank/factory/vm@base` from the `zfs` stand-in first, then the drop stand-in's line.
2. The faults (rows of one parametrized test): a rollback that exits 1 raises `SnapshotError` whose `command` holds `rollback -r`, and the drop stand-in was not called; a drop that prints `sudo: a password is required` and exits 1 raises `SnapshotError` whose `command` is the drop's words joined by one space and whose `detail` holds `sudo: a password is required` and the exit status `1`; a drop whose program does not exist raises `SnapshotError` whose `command` is that path; a drop that sleeps 60 seconds under a `time_limit` of one second raises `SnapshotError` within `ROOMY_BOUND_SECONDS` of `tests/time_limits.py`, whose `detail` equals `no_end_detail(<the time_limit>)` of `factory.adapters.printed_output`, the text the `zfs` commands' time-limit fault holds.
3. Only the reset drops (rows of one parametrized test over `advance()`, `changed_paths()`, `version()` and `dataset_exists()`, the `zfs` stand-in answering each with success): the drop stand-in was called zero times.
4. The command must name a program (rows of one parametrized test): `drop_caches=()` raises `ValueError`; `drop_caches=("x",)` is accepted.
5. The wiring (one test over `build_boundaries` with the settings read from the fixture `hosted_environment`, its stand-in `zfs`, and a stand-in `sudo` first on `PATH` that records its words): `DROP_CACHES_COMMAND == ("sudo", "-n", "/usr/local/bin/factory-drop-caches")`; building the boundaries calls no `sudo`; `boundaries.snapshots.reset()` calls the stand-in `sudo` once, with the words `-n /usr/local/bin/factory-drop-caches`; and (read with `ast`) `ZfsSnapshots` is constructed in no module under `src/factory` but `factory.entry.wiring`, and there only with the keyword `drop_caches=DROP_CACHES_COMMAND`.
6. The script's step (rows of one parametrized test over the script's text with its comment lines dropped, the steps cut as `tests/vm_support.py` cuts them): the first `setup: sudoers: `, the first `setup: caches: ` and the first `setup: folders: ` come in that order; the step `caches` holds the helper's three lines in their order, `install -m 0755`, `/usr/local/bin/factory-drop-caches`, `/etc/sudoers.d/factory-drop-caches`, `chmod 0440`, `visudo -cf` and `rm -f /etc/sudoers.d/factory-drop-caches`, and does not hold `$sudoers` (the step runs on every run); the rule `factory ALL=(root) NOPASSWD: /usr/local/bin/factory-drop-caches` appears exactly once in the script, inside the step `caches`; `/proc/sys/vm/drop_caches` appears on no line outside that step.
7. The script stays valid (one test): `sh -n vm/setup.sh` exits 0.
8. The refused check of the step (one test over the step `caches` of the script's text, comment lines dropped): the step holds `setup: caches: visudo -cf refused /etc/sudoers.d/factory-drop-caches; removed it` with `>&2` on its line, and `exit 1` follows it inside the step.
9. Writes only when the text differs (rows of one parametrized test over the step `caches`, one row for the helper and one for the `sudoers` file): the step compares the installed file with its wanted text before writing it (a `cmp`, `diff` or `grep -x` test on that file's path precedes its `install` or write), and its `setup: caches: ` output has a `found` form and a `wrote` form for that file, as the other steps' lines have.
10. `make check` stays green.
11. docs: `docs/operator-guide.md`, `## The machine`, `### The script`: the step `caches` in the numbered list of steps (the two files, written on every run, the `visudo` refusal), the numbers after it following, and one paragraph on the page cache after a rollback (a page written through `mmap` survives `zfs rollback` in the page cache; the factory drops the clean cache after every reset through the helper; the drop is machine-wide, so the next sync reads from the disk). `docs/project-guide/stage-environment.md`, `## The ZFS adapter`: the constructor with `drop_caches`, the row of `reset()` in *The commands* (the rollback, then the drop), the drop's faults in *Faults*, the drop stand-in in *The stand-in*; and the row of `snapshots` in the wiring table with `drop_caches=DROP_CACHES_COMMAND`. `docs/decisions.md`: a new entry "The reset drops the page cache after the rollback" (F0045-S0002; the cause found on `vm` on 2026-10-25 and 2026-10-26; decisions 15 and 16 of `feature.md` with their rejected options). `README.md`: none.

## Smoke test

```bash
uv run python - <<'EOF'
import inspect
from factory.adapters.zfs_snapshots import DROP_CACHES_COMMAND, ZfsSnapshots
print(DROP_CACHES_COMMAND)
print(inspect.signature(ZfsSnapshots.__init__).parameters["drop_caches"].kind.name)
EOF
sh -n vm/setup.sh && echo syntax-ok
grep -c 'factory ALL=(root) NOPASSWD: /usr/local/bin/factory-drop-caches' vm/setup.sh
```
Expect: four lines: `('sudo', '-n', '/usr/local/bin/factory-drop-caches')`; `KEYWORD_ONLY`; `syntax-ok`; `1`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed, so there are no format findings):

   1. The Interface states a failure rule for the step `caches` that no criterion tests. After a refused `visudo -cf`, the step prints `setup: caches: visudo -cf refused /etc/sudoers.d/factory-drop-caches; removed it` to standard error and exits 1. Criterion 6 only looks for the words `visudo -cf` and `rm -f /etc/sudoers.d/factory-drop-caches` in the text. Nothing checks the message, that it goes to standard error, or the exit status 1. Two coders could read this two ways and both pass. Should I add a criterion? I would choose one that checks the message text and the `>&2` and `exit 1` in the step. The alternative is a test that runs the step against a stand-in `visudo`; the existing tests in `tests/test_vm_setup.py` may already support that.

   2. The clause "written by root with `install -m 0755` only when its text differs" has no criterion for its second half. The same holds for the `sudoers` file ("written only when its text differs"). Criterion 6 checks that `install -m 0755` is present, but not that the write is conditional. A script that overwrites every time would pass. The report line "found" versus "written" is a second behaviour with no criterion. Should I add one? I would choose a text criterion that the step compares the current file with the wanted text before writing, with a separate `found` and `written` report in the `setup: caches: ` line.

   3. The helper's exact text is a stated rule: three lines, in that order. Criterion 6 checks the lines and their order, so this one is covered. I found no gap here.

   4. Criterion 2's last row says the drop "raises `SnapshotError` within `ROOMY_BOUND_SECONDS`". It does not say what the `detail` holds for the time limit reached. The Interface says "formed as for the `zfs` commands". Should the row also assert the same detail text that the `zfs` time-limit test asserts? I would choose yes, so that the time-limit side of the detail is tested, as the exit-status side is.

   Checked and fine:
   - Interface: it names the modules and signatures, `DROP_CACHES_COMMAND` and the keyword-only `drop_caches` with a `ValueError` on an empty tuple.
   - Architecture: the adapter holds the command and the wiring is the one place that builds `ZfsSnapshots`, which fits the layers in `CLAUDE.md`.
   - Scope: this is decision 15 of `feature.md`, with no content check, as decision 16 says.
   - Test leaves: decision 22 gives the leave for the earlier tests the Interface names.
   - Smoke test: the commands run and no pytest is involved. The `Expect:` line lists four checkable lines.
4. 2026-10-26 human: 1. Yes, a text criterion: the step's refused branch prints that message with `>&2` and ends `exit 1`. No stand-in `visudo` run.
   2. Yes, a text criterion: the step compares each file with its wanted text before writing (helper and sudoers file alike), and its `setup: caches: ` line reports `found` or `wrote` as the other steps do.
   3. Agreed, covered.
   4. Yes: the time-limit row asserts the same detail text the `zfs` time-limit test asserts.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: concrete. It names `factory.adapters.zfs_snapshots` with `DROP_CACHES_COMMAND` and the keyword-only `drop_caches` (an empty tuple raises `ValueError`). It names `factory.entry.wiring._container_adapters` and the script step `caches` with the exact text of both files.
   - Criteria: the human's answers in journal entry 4 are carried in. Criterion 2's time-limit row now asserts `detail == no_end_detail(<time_limit>)` (answer 4; `no_end_detail` is what `ZfsSnapshots` uses for the `zfs` time-limit fault). New criterion 8 covers the refused `visudo` branch: the message, `>&2` and `exit 1` (answer 1). New criterion 9 covers write-only-when-different and the found/wrote report for both files (answer 2). `make check` and `docs:` are now 10 and 11. Every other rule has its passing and failing side: the rollback and drop faults, the empty and one-word command, and the four methods that do not drop.
   - Smoke test: runnable. There is no pytest, and the `Expect:` line lists four checkable lines.
   - Architecture: the adapter holds the command, the wiring is the one place that builds `ZfsSnapshots`, and the script is the machine's side. The layers hold.
   - Scope: decisions 15 and 16 of `feature.md` (no content check). The leave for the earlier tests is decision 22.
7. factory: started tests as vm.
8. tester: Tests are written for criteria 1 to 9, and `make lint` is green. In the one `make test` run they fail for the right reason: `vm/setup.sh` has no `setup: caches: ` text (`step_texts` raises "no 'setup: caches: ' text"). The adapter tests need `DROP_CACHES_COMMAND` and the keyword `drop_caches`, which do not exist yet. I skipped the type check as this stage says. I stopped on three questions. The first is a contradiction in the work item. The other two are criteria I had to interpret.

   1. Criterion 2's drop-fails row and the Interface disagree about the detail. The row says the detail holds `sudo: a password is required` **and** the exit status `1`. The Interface says the detail is "formed as for the `zfs` commands". But that format, `failure_detail` in `src/factory/adapters/printed_output.py:18`, gives only the last printed line, and gives `exit status <n>` only when nothing was printed. `test_a_failed_reset_names_its_detail` pins that format exactly for `zfs`. My options:
      - (a) The drop's detail follows `failure_detail`. The row then checks only for `sudo: a password is required`.
      - (b) The drop's detail holds both, for example `sudo: a password is required (exit status 1)`. The drop then has its own format, unlike the `zfs` commands.
      I would choose (a), because it is what "formed as for the `zfs` commands" says. The test currently asserts what the criterion says (`REFUSAL in detail and "1" in detail`), so under (a) I would drop the `"1"`.

   2. Criterion 6 checks the helper's three lines in the script's text with its comment lines dropped. But `#!/bin/sh` starts with `#`, so dropping the comment lines removes it. My test reads the three lines as consecutive lines of the raw script. It reads `sync` and `echo 1 > /proc/sys/vm/drop_caches` in order inside the step `caches` of the text without comments. Is that right? I would keep it.

   3. Criterion 9 asks for "a `cmp`, `diff` or `grep -x` test on that file's path". The script's own way to do that is `unchanged <path>`, a function whose body is `cmp -s`. My test accepts a line that holds the path and either a comparison command or a call of a function in the script whose body holds one. A write is any line with the path and `install`, `cp`, `mv` or `tee`, or a `>` into the path. The step must also hold `wrote <path>`, and a line with `found` and the path. Is that right? I would keep it.

   If you agree with (a), 2 and 3, the next tests run changes only the drop-fails row and ends with `doing`.

   Criterion to test (as written now):
   - criterion 1: tests/adapters/test_zfs_snapshots_drop_caches.py::test_the_reset_drops_the_cache_after_the_rollback
   - criterion 2: tests/adapters/test_zfs_snapshots_drop_caches.py::test_a_fault_of_the_rollback_or_the_drop_is_a_snapshot_error (rows rollback-fails, drop-fails, drop-missing, drop-time-limit). The `zfs` stand-ins here are `sh` scripts, so the rollback ends within the one-second limit even under load.
   - criterion 3: tests/adapters/test_zfs_snapshots_drop_caches.py::test_only_the_reset_drops_the_cache
   - criterion 4: tests/adapters/test_zfs_snapshots_drop_caches.py::test_the_drop_command_must_name_a_program
   - criterion 5: tests/entry/test_wiring_drop_caches.py::test_every_reset_of_the_wired_instance_drops_the_cache_through_sudo
   - criterion 6: tests/test_vm_setup_caches.py::test_the_caches_step_writes_the_helper_and_its_rule
   - criterion 7: tests/test_vm_setup.py::test_the_script_parses_and_starts_with_its_shebang_and_set_eu. This existing test already runs `sh -n vm/setup.sh`, so I wrote no second copy.
   - criterion 8: tests/test_vm_setup_caches.py::test_a_refused_visudo_check_removes_the_rule_and_ends_the_script
   - criterion 9: tests/test_vm_setup_caches.py::test_the_caches_step_writes_a_file_only_when_its_text_differs (rows helper, sudoers)

   Files created: tests/adapters/test_zfs_snapshots_drop_caches.py, tests/entry/test_wiring_drop_caches.py, tests/test_vm_setup_caches.py.

   Earlier test files changed under the leave in the Interface (decision 22):
   - tests/zfs_support.py: new `Drop` and `write_drop`, a `sh` stand-in that adds its path to a record file. `snapshots_on` passes one that succeeds and records into `drop-calls.txt`, which no existing test reads.
   - tests/adapters/test_zfs_snapshots.py: the three named tests gain `drop_caches=DROP`. The ten-minute test answers both calls with success and reads the rollback's request, not a count of all requests.
   - tests/vm_support.py: `STEPS` gains `caches` after `sudoers`.
   - tests/test_vm_setup_text.py: `ORDERED_COMMANDS` gains `/etc/sudoers.d/factory-drop-caches`.

   Modules the test run could not import: none fails at import time. `DROP_CACHES_COMMAND` (from `factory.adapters.zfs_snapshots`) is missing, so the wiring test module will fail at collection, and the tests that use `snapshots_on` fail on the unknown keyword `drop_caches`.
9. 2026-10-26 human: 1. (a): the drop's detail follows `failure_detail` as the `zfs` commands do; the row checks only for `sudo: a password is required`.
   2. Agreed, keep it.
   3. Agreed, keep it.
10. factory: started tests as vm.
11. tester: I applied the human's answer in entry 9. The test files from entry 8 are already on the branch, so this run changed one row. In `tests/adapters/test_zfs_snapshots_drop_caches.py::test_a_fault_of_the_rollback_or_the_drop_is_a_snapshot_error`, row `drop-fails` now checks only that `detail` contains `sudo: a password is required`. It no longer checks for the exit status `1` (answer 1(a): the drop's detail follows `failure_detail`, as the `zfs` commands' does). Answers 2 and 3 confirmed the readings in entry 8, so those tests are unchanged.

    I ran `make test` once and it is red, as intended. The `vm/setup.sh` tests fail with "no 'setup: caches: ' text", because the step does not exist yet. The adapter and wiring tests need `DROP_CACHES_COMMAND` and the keyword `drop_caches`, which do not exist yet either. `make lint` is green. I skipped the type check, as this stage says.

    Criterion to test:
    - criterion 1: tests/adapters/test_zfs_snapshots_drop_caches.py::test_the_reset_drops_the_cache_after_the_rollback
    - criterion 2: tests/adapters/test_zfs_snapshots_drop_caches.py::test_a_fault_of_the_rollback_or_the_drop_is_a_snapshot_error (rows rollback-fails, drop-fails, drop-missing, drop-time-limit)
    - criterion 3: tests/adapters/test_zfs_snapshots_drop_caches.py::test_only_the_reset_drops_the_cache
    - criterion 4: tests/adapters/test_zfs_snapshots_drop_caches.py::test_the_drop_command_must_name_a_program
    - criterion 5: tests/entry/test_wiring_drop_caches.py::test_every_reset_of_the_wired_instance_drops_the_cache_through_sudo
    - criterion 6: tests/test_vm_setup_caches.py::test_the_caches_step_writes_the_helper_and_its_rule
    - criterion 7: tests/test_vm_setup.py::test_the_script_parses_and_starts_with_its_shebang_and_set_eu (an existing test that already runs `sh -n vm/setup.sh`)
    - criterion 8: tests/test_vm_setup_caches.py::test_a_refused_visudo_check_removes_the_rule_and_ends_the_script
    - criterion 9: tests/test_vm_setup_caches.py::test_the_caches_step_writes_a_file_only_when_its_text_differs (rows helper, sudoers)

    Files created (in the previous tests run): tests/adapters/test_zfs_snapshots_drop_caches.py, tests/entry/test_wiring_drop_caches.py, tests/test_vm_setup_caches.py. Earlier test files changed under decision 22 (in the previous run, as entry 8 lists): tests/zfs_support.py, tests/adapters/test_zfs_snapshots.py, tests/vm_support.py, tests/test_vm_setup_text.py.

    Modules the test run could not import: no module is missing. The name `DROP_CACHES_COMMAND` is missing from `factory.adapters.zfs_snapshots`, and the keyword `drop_caches` of `ZfsSnapshots` does not exist yet.

    `lint`: lint: green (0.2 s)
    `test`: ERROR tests/test_vm_setup_text.py::test_the_folders_step_refuses_a_link_at_state_or_repo[exit-1] - AssertionError: no 'setup: caches: ' text
12. factory: started doing as vm.
13. coder: I stopped with the implementation written and `make check` red. The cause is two problems in the tests, and I cannot fix either without changing a test (R9).

    What I built, left in the working tree:
    - `src/factory/adapters/zfs_snapshots.py`: `DROP_CACHES_COMMAND`, and a required keyword-only `drop_caches` (an empty tuple raises `ValueError`). `reset()` runs the drop after the rollback succeeds. I split `_run` into `_run(arguments)`, which puts `zfs` in front, and `_execute(argv)`, which names the command by its words joined with spaces. So the drop has the same faults as the `zfs` commands: `failure_detail`, `no_end_detail`, and the `OSError` text. I rejected a separate drop runner because it would be a second copy of the fault handling.
    - `src/factory/entry/wiring.py`: `_container_adapters` now passes `drop_caches=DROP_CACHES_COMMAND`.
    - `vm/setup.sh`: a new step `caches` between `sudoers` and `folders`, on every run. It stages each file and writes it only when `unchanged` (which uses `cmp -s`) reports a difference: the helper with `install -m 0755`, and the `sudoers` file with `cp`, `chmod 0440` and `visudo -cf`. A refused check runs `rm -f`, prints the message with `>&2` and runs `exit 1`. The step's output line has `wrote` and `found` forms, like the step `sudoers`.

    Every new test passes except one row. Four earlier tests fail.

    Question 1: two of the tester's checks cannot both pass. Row `install-helper` of `tests/test_vm_setup_caches.py::test_the_caches_step_writes_the_helper_and_its_rule` asks that the first `install -m 0755` in the step come before the first `/usr/local/bin/factory-drop-caches`. But row `helper` of `test_the_caches_step_writes_a_file_only_when_its_text_differs` (criterion 9) asks for a comparison line that holds that path, before the `install` line. That comparison line is itself the first mention of the path (offset 86, against 129 for `install -m 0755`). So no script that meets criterion 9 passes `install-helper`. Options:
    - (a) The tester changes `install-helper` to look for one line that holds both `install -m 0755` and the helper's path.
    - (b) The tester changes it to look only for the presence of both strings in the step.
    - (c) I write the script so that `install -m 0755` appears earlier, for example through a variable. That would be contrived.
    I would choose (a).

    Question 2: earlier wiring tests now call the real `sudo`. Every `reset()` built through the wiring now runs `sudo -n /usr/local/bin/factory-drop-caches`. This machine has no `sudo`, so four earlier tests fail with `SnapshotError: snapshot command sudo -n /usr/local/bin/factory-drop-caches failed: [Errno 2] No such file or directory: 'sudo'`:
    - `tests/entry/test_wiring_container_extra.py::test_every_container_of_a_stage_carries_both_settings_and_no_hosting_token[claude]` and `[opencode]`
    - `tests/entry/test_wiring_stage_environment.py::test_a_container_instance_gets_the_dataset_s_adapters_and_asks_for_no_tool` (the failure is reached from `tests/entry/test_wiring_stage_environment.py:101` through `src/factory/adapters/zfs_snapshots.py:78`)
    - `tests/entry/test_wiring_command_records.py::test_the_built_project_commands_record_a_run_in_the_state_directory` (it fails as `ProjectCommandError ... snap...`)

    The Interface lists no test change for these. Under decision 22, I see two ways the tester could give them a stand-in `sudo`:
    - (a) A shared fixture in `tests/conftest.py`, beside `hosted_environment`, that writes a `sudo` stand-in which exits 0 and puts it first on `PATH` through `monkeypatch`. These tests would use it, and so would the new wiring test, which has its own copy now.
    - (b) Each test sets up its own stand-in.
    I would choose (a). The production code stays as the Interface says: no setting names the command.

    Not done yet: the refactor pass and a green `make check`. Both wait on these answers.

    While building, a Python heredoc of mine broke on the script's `EOF`, and its remaining lines ran in the shell. Every command failed: `stage`, `unchanged` and `visudo` were missing, and `install` and `cp` had no file to copy. I checked afterwards that neither `/usr/local/bin/factory-drop-caches` nor `/etc/sudoers.d/factory-drop-caches` exists.
14. 2026-10-26 human: 1. (a): the tester changes row `install-helper` to look for one line that holds both `install -m 0755` and the helper's path.
    2. (a): a shared fixture in `tests/conftest.py` writes a `sudo` stand-in that exits 0 and puts it first on `PATH` through `monkeypatch`; the four earlier tests you name and the new wiring test use it. The leave of decision 22 widens to exactly that: those four tests gain the fixture, each keeps its name and its assertions. No setting names the command.
15. factory: started doing as vm.
16. coder: Both of the human's answers in entry 14 change tests, so I changed no code. I am sending the work item to the tester. The implementation from entry 13 is already on the branch, unchanged: `src/factory/adapters/zfs_snapshots.py`, `src/factory/entry/wiring.py` and `vm/setup.sh`. The refactor pass and a green `make check` come when the work item returns to doing.

    Test changes for the tester:
    1. In `tests/test_vm_setup_caches.py::test_the_caches_step_writes_the_helper_and_its_rule`, change row `install-helper` so that it looks for one line of the step that holds both `install -m 0755` and `/usr/local/bin/factory-drop-caches`. It should no longer check that the first `install -m 0755` comes before the first mention of the path. This is answer 1(a).
    2. In `tests/conftest.py`, add a shared fixture that writes a `sudo` stand-in that exits 0 and puts it first on `PATH` through `monkeypatch`. The following tests use it, and each keeps its name and its assertions (answer 2(a), under the leave of decision 22 as the human widened it):
       - `tests/entry/test_wiring_container_extra.py::test_every_container_of_a_stage_carries_both_settings_and_no_hosting_token` (both rows, `claude` and `opencode`)
       - `tests/entry/test_wiring_stage_environment.py::test_a_container_instance_gets_the_dataset_s_adapters_and_asks_for_no_tool`
       - `tests/entry/test_wiring_command_records.py::test_the_built_project_commands_record_a_run_in_the_state_directory`
       - `tests/entry/test_wiring_drop_caches.py::test_every_reset_of_the_wired_instance_drops_the_cache_through_sudo`: its own copy of the stand-in is replaced by the shared fixture. It still needs to record the stand-in's words, so the fixture may need to record them too, or let the test read them.

    The production code stays as the Interface says: no setting names the drop command.

    The Description is unchanged. Entry 14 settles how the tests are written but does not change what the task means.
