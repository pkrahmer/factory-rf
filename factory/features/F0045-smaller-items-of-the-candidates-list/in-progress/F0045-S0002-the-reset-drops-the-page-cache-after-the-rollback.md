---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 467
comments_read: [6424960438]
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
2. The faults (rows of one parametrized test): a rollback that exits 1 raises `SnapshotError` whose `command` holds `rollback -r`, and the drop stand-in was not called; a drop that prints `sudo: a password is required` and exits 1 raises `SnapshotError` whose `command` is the drop's words joined by one space and whose `detail` holds `sudo: a password is required` and the exit status `1`; a drop whose program does not exist raises `SnapshotError` whose `command` is that path; a drop that sleeps 60 seconds under a `time_limit` of one second raises `SnapshotError` within `ROOMY_BOUND_SECONDS` of `tests/time_limits.py`.
3. Only the reset drops (rows of one parametrized test over `advance()`, `changed_paths()`, `version()` and `dataset_exists()`, the `zfs` stand-in answering each with success): the drop stand-in was called zero times.
4. The command must name a program (rows of one parametrized test): `drop_caches=()` raises `ValueError`; `drop_caches=("x",)` is accepted.
5. The wiring (one test over `build_boundaries` with the settings read from the fixture `hosted_environment`, its stand-in `zfs`, and a stand-in `sudo` first on `PATH` that records its words): `DROP_CACHES_COMMAND == ("sudo", "-n", "/usr/local/bin/factory-drop-caches")`; building the boundaries calls no `sudo`; `boundaries.snapshots.reset()` calls the stand-in `sudo` once, with the words `-n /usr/local/bin/factory-drop-caches`; and (read with `ast`) `ZfsSnapshots` is constructed in no module under `src/factory` but `factory.entry.wiring`, and there only with the keyword `drop_caches=DROP_CACHES_COMMAND`.
6. The script's step (rows of one parametrized test over the script's text with its comment lines dropped, the steps cut as `tests/vm_support.py` cuts them): the first `setup: sudoers: `, the first `setup: caches: ` and the first `setup: folders: ` come in that order; the step `caches` holds the helper's three lines in their order, `install -m 0755`, `/usr/local/bin/factory-drop-caches`, `/etc/sudoers.d/factory-drop-caches`, `chmod 0440`, `visudo -cf` and `rm -f /etc/sudoers.d/factory-drop-caches`, and does not hold `$sudoers` (the step runs on every run); the rule `factory ALL=(root) NOPASSWD: /usr/local/bin/factory-drop-caches` appears exactly once in the script, inside the step `caches`; `/proc/sys/vm/drop_caches` appears on no line outside that step.
7. The script stays valid (one test): `sh -n vm/setup.sh` exits 0.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`, `## The machine`, `### The script`: the step `caches` in the numbered list of steps (the two files, written on every run, the `visudo` refusal), the numbers after it following, and one paragraph on the page cache after a rollback (a page written through `mmap` survives `zfs rollback` in the page cache; the factory drops the clean cache after every reset through the helper; the drop is machine-wide, so the next sync reads from the disk). `docs/project-guide/stage-environment.md`, `## The ZFS adapter`: the constructor with `drop_caches`, the row of `reset()` in *The commands* (the rollback, then the drop), the drop's faults in *Faults*, the drop stand-in in *The stand-in*; and the row of `snapshots` in the wiring table with `drop_caches=DROP_CACHES_COMMAND`. `docs/decisions.md`: a new entry "The reset drops the page cache after the rollback" (F0045-S0002; the cause found on `vm` on 2026-10-25 and 2026-10-26; decisions 15 and 16 of `feature.md` with their rejected options). `README.md`: none.

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
