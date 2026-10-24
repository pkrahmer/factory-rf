---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 408
comments_read: [6383983454, 6384181638]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T12:03:27.602768Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T12:03:27.609452Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-24T12:03:48.462994Z'
  stage: intake
  run: a82df3871ab5413b9471660bef0892ca
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-24T12:05:06.383847Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-24T12:05:24.394519Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-24T12:05:46.571528Z'
  stage: intake
  run: 67a7b64249d84542a8cec3f648751ed3
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-24T12:06:06.993656Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-24T12:12:55.974897Z'
  stage: tests
  run: 4bdacb36410d447da6c8dfb994d79f73
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-24T12:13:16.642623Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-24T12:17:32.587141Z'
  stage: doing
  run: 95cb37d0d0d644ea99ff8fee3c26f659
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-24T12:17:54.336794Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-24T12:19:10.000638Z'
  stage: review
  run: b631ce38ecf54c5faf4844beba7f1e2e
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-24T12:19:30.559944Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-24T12:21:56.765538Z'
  stage: doing
  run: 82b591788b7e46c59dd380a11bfab51c
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-24T12:22:17.366644Z'
  stage: tests
- number: 16
  speaker: tester
  kind: question
  at: '2026-10-24T12:24:10.783530Z'
  stage: tests
  run: 12c8b75232834d948523d125660b2bba
  blocked: question
- number: 17
  speaker: human
  kind: comment
  at: '2026-10-24T12:25:29.486990Z'
  stage: tests
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-24T12:25:47.648551Z'
  stage: tests
- number: 19
  speaker: tester
  kind: result
  at: '2026-10-24T12:28:41.092353Z'
  stage: tests
  run: 896ebbfa83054863b0a9713a128db3eb
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-24T12:29:02.076559Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-10-24T12:32:15.401897Z'
  stage: doing
  run: 9d3415f63eb64c5aa418aad7e51db0e3
---

# ZFS snapshots roll back, advance and diff the dataset

## Description

On the VM of v1.2 the dataset is a ZFS dataset (`<pool>/factory/<instance>`, mounted at `/srv/factory/<instance>/work`) and its base is the one snapshot `@base` (`planning/v1.2-plan.md`, "The cycle of a stage", steps 2, 4 and 6). This story adds the first real implementation of the `Snapshots` interface of S0001, `ZfsSnapshots`, over five `zfs` commands: `rollback -r` for the reset, `list` and `destroy` and `snapshot` for the advance, `diff -FH` for the changed paths. It runs the executable it is given through `run_process`, parses `zfs diff`'s lines into `ChangedPath`s relative to the mount point, and turns every failure into `SnapshotError` naming the command and the last line of its output. It also offers `version()` and `dataset_exists()`, which S0011 (the preflight) reads. The adapter is tested on a stand-in `zfs` that records its arguments and answers as planned; the real `zfs` runs only on the VM, in F0043's story 4. The `sudoers` fallback of the human's decision 3 is the operator's: one executable is run, and a wrapper script can stand in its place (decision 14 of `feature.md`). Nothing wires the class yet (S0010).

## Interface

`factory.adapters.zfs_snapshots` (`adapters`), new:

```python
BASE_SNAPSHOT = "base"
SNAPSHOT_TIME_LIMIT = timedelta(minutes=10)


class ZfsSnapshots(Snapshots):
    """The dataset of a ZFS pool and its snapshot `@base`, reached through the `zfs` executable."""

    def __init__(
        self,
        dataset: str,
        mount_point: Path,
        *,
        executable: str = "zfs",
        time_limit: timedelta = SNAPSHOT_TIME_LIMIT,
    ) -> None: ...

    def version(self) -> str:
        """The first non-blank line `<zfs> --version` prints; `SnapshotError` when it fails."""

    def dataset_exists(self) -> bool:
        """Whether `<zfs> list -H -o name <dataset>` names it; a fault is `SnapshotError`."""
```

- `mount_point` is the path given, as given.
- Every command runs through `run_process` of `factory.adapters.process` with `argv` `[executable, ...]`, `cwd` `/`, `env` `None` (the factory's own environment), `time_limit` the one given (`SNAPSHOT_TIME_LIMIT`, 10 minutes, by default; a test shortens it) and `merge_stderr` true. The structural test `tests/test_wrapper_search.py` names the module (decision 18 b of `feature.md`).
- `reset()` runs `<zfs> rollback -r <dataset>@base`.
- `advance()` runs `<zfs> list -H -o name -t snapshot <dataset>@base`: exit status 0 means the base exists and `<zfs> destroy <dataset>@base` follows; exit status 1 means there is none and nothing is destroyed; any other status is a fault. Then `<zfs> snapshot <dataset>@base`.
- `changed_paths()` runs `<zfs> diff -FH <dataset>@base` and reads each non-blank line as tab-separated fields `<change> <kind> <path>` or, for `R`, `<change> <kind> <old path> <new path>`; a field after those (`(+1)` on an `M` line: the change of a link count, as a hard link makes it) is ignored. `M` is `modified`, `+` is `added`, `-` is `deleted`, `R` is `deleted` for the old path and `added` for the new one. A line whose kind is `/` (a directory) is left out whatever its change. Every path must be the mount point or lie under it (`<mount point>/...`; `<mount point>x/...` is outside); it is made relative to the mount point with `/` separators, and `zfs`'s octal escapes (`\ooo`, one per byte outside printable ASCII and for the backslash: `\040` is a space, `\303\251` is `é`, `\134` is `\`) are decoded to bytes and read as UTF-8. A path that two lines name (one removes it and one adds it: a file removed and made anew, a rename onto a removed path) is listed once, as `added`. The result is sorted by path. An empty output is `[]`.
- A fault is `SnapshotError(command, detail)`, `command` the words run joined by one space (`zfs rollback -r tank/factory/vm@base`), `detail` the last non-blank line of the output, or `exit status <n>` when the output has none, or `no end within <n> s` (`n` the whole seconds of the time limit, rounded up) when the command reached its time limit, or the operating system's message when it could not start (`OSError`). Faults: an exit status other than 0 for `rollback`, `destroy`, `snapshot`, `diff` and `--version`; a status other than 0 or 1 for the two `list` commands; a `diff` line with a change other than `M`, `+`, `-`, `R`, with fewer fields than its form needs, or with a path outside the mount point (`detail` then `cannot read the line <line>` or `<path> is outside <mount point>`).
- `version()` runs `<zfs> --version` and returns its first non-blank line stripped (`zfs-2.2.2-0ubuntu9.1`); an output without one is a fault with `detail` `printed nothing`.
- `dataset_exists()` runs `<zfs> list -H -o name <dataset>`: exit status 0 whose first line is the dataset is `True`; exit status 1 is `False`; exit status 0 with another first line is a fault with `detail` `named <line>, not <dataset>`.

Tests (the tester writes them): `tests/adapters/test_zfs_snapshots.py` and `tests/adapters/test_zfs_snapshots_diff.py`, with a stand-in `zfs` written into `tmp_path` by a helper modelled on `write_sudo` of `tests/sudo_support.py`: it records its arguments to a file and, by a plan keyed on its first argument (`rollback`, `list`, `destroy`, `snapshot`, `diff`, `--version`), prints planned standard output and standard error and exits with a planned status, or sleeps past a short limit. No real `zfs` is run anywhere.

## Acceptance criteria

1. `ZfsSnapshots("tank/factory/vm", Path("/srv/factory/vm/work"), executable=<stand-in>).reset()` makes exactly one call with the arguments `["rollback", "-r", "tank/factory/vm@base"]`, and `mount_point` is `Path("/srv/factory/vm/work")`.
2. `advance()` (rows of one parametrized test): with `list` planned to exit 0, the calls are `["list", "-H", "-o", "name", "-t", "snapshot", "tank/factory/vm@base"]`, `["destroy", "tank/factory/vm@base"]`, `["snapshot", "tank/factory/vm@base"]` in that order; with `list` planned to exit 1 and print `cannot open 'tank/factory/vm@base': dataset does not exist` to standard error, the calls are the `list` and the `snapshot` only; with `list` planned to exit 2, `SnapshotError` is raised whose `command` is `<stand-in> list -H -o name -t snapshot tank/factory/vm@base` and nothing else is called; with `list` planned to exit 0 and `destroy` planned to exit 1 and print `cannot destroy 'tank/factory/vm@base': dataset is busy`, `SnapshotError` is raised whose `command` is `<stand-in> destroy tank/factory/vm@base` and whose `detail` is that printed line, and `snapshot` is not called; with `list` planned to exit 0 and `snapshot` planned to exit 1 and print `cannot create snapshot 'tank/factory/vm@base': out of space`, `SnapshotError` is raised whose `command` is `<stand-in> snapshot tank/factory/vm@base` and whose `detail` is that printed line.
3. `changed_paths()` with `diff` planned to print, tab-separated, `M\t/\t/srv/factory/vm/work/checkout`, `+\t/\t/srv/factory/vm/work/checkout/newdir`, `M\tF\t/srv/factory/vm/work/checkout/src/a.py`, `+\tF\t/srv/factory/vm/work/checkout/new.txt`, `-\tF\t/srv/factory/vm/work/home/.claude.json`, `R\tF\t/srv/factory/vm/work/checkout/old.md\t/srv/factory/vm/work/checkout/renamed.md`, `-\tF\t/srv/factory/vm/work/checkout/renamed.md`, `+\t@\t/srv/factory/vm/work/checkout/link`, `+\tF\t/srv/factory/vm/work/checkout/with\040space.txt`, `+\tF\t/srv/factory/vm/work/checkout/caf\303\251.txt`, `+\tF\t/srv/factory/vm/work/checkout/back\134slash.txt`, `M\tF\t/srv/factory/vm/work/home/.cache/uv/w\t(+1)` returns exactly `[ChangedPath("checkout/back\\slash.txt", "added"), ChangedPath("checkout/café.txt", "added"), ChangedPath("checkout/link", "added"), ChangedPath("checkout/new.txt", "added"), ChangedPath("checkout/old.md", "deleted"), ChangedPath("checkout/renamed.md", "added"), ChangedPath("checkout/src/a.py", "modified"), ChangedPath("checkout/with space.txt", "added"), ChangedPath("home/.cache/uv/w", "modified"), ChangedPath("home/.claude.json", "deleted")]` (the two directories left out, `checkout/renamed.md` once although two lines name it, the link-count field ignored), and the one call has the arguments `["diff", "-FH", "tank/factory/vm@base"]`. An empty output returns `[]`.
4. `changed_paths()` faults (rows of one parametrized test, each `SnapshotError` with `command` `<stand-in> diff -FH tank/factory/vm@base`): the line `M\tF\t/elsewhere/a.py` gives `detail` `/elsewhere/a.py is outside /srv/factory/vm/work`, and so does `M\tF\t/srv/factory/vm/workx/a` with `/srv/factory/vm/workx/a is outside /srv/factory/vm/work`; the line `X\tF\t/srv/factory/vm/work/a` gives `cannot read the line X\tF\t/srv/factory/vm/work/a`; the line `M\tF` gives `cannot read the line M\tF`; the line `R\tF\t/srv/factory/vm/work/a` gives `cannot read the line R\tF\t/srv/factory/vm/work/a`; the line `R\tF\t/srv/factory/vm/work/a\t/elsewhere/b` gives `/elsewhere/b is outside /srv/factory/vm/work`; `diff` planned to exit 1 with standard error `cannot open 'tank/factory/vm@base': dataset does not exist` gives `detail` `cannot open 'tank/factory/vm@base': dataset does not exist`.
5. The fault's `detail` (rows of one parametrized test, on `reset()`): exit status 1 with the two lines `warning` and `rollback: dataset is busy` gives `rollback: dataset is busy`; exit status 1 with no output gives `exit status 1`; a stand-in that sleeps 60 seconds, under an adapter built with `time_limit` 1.5 seconds, gives `no end within 2 s` (the seconds rounded up) after at least 1 and less than 25 seconds; an executable that does not exist raises `SnapshotError` whose `command` starts with `/nowhere/zfs rollback` and whose `detail` starts with `[Errno 2]`. `SNAPSHOT_TIME_LIMIT` is 10 minutes, and an adapter built without `time_limit` passes it to `run_process` (read from a recorded `run_process` request: the module's `run_process` replaced by a `Recorder` of `tests/run_process_recorder.py`, as the `recorder` fixture of `tests/conftest.py` does for the runtime; a stand-in cannot see the limit it runs under).
6. Standard error is merged, the working directory is the root and the environment is the factory's own: a `reset()` whose stand-in exits 1 writing `boom` to standard error only raises `SnapshotError` with `detail` `boom`, the stand-in's recorded working directory is `/`, and its recorded environment holds a variable the test set with `monkeypatch.setenv`.
7. `version()` with `--version` planned to print `zfs-2.2.2-0ubuntu9.1\nzfs-kmod-2.2.2-0ubuntu9.1` returns `zfs-2.2.2-0ubuntu9.1`; planned to print nothing and exit 0 raises `SnapshotError` with `detail` `printed nothing`; planned to exit 1 with `zfs: command not found` raises it with that detail (rows of one parametrized test).
8. `dataset_exists()` (rows of one parametrized test): `list` planned to exit 0 and print `tank/factory/vm` returns `True` and the call's arguments are `["list", "-H", "-o", "name", "tank/factory/vm"]`; exit 1 returns `False`; exit 0 printing `tank/other` raises `SnapshotError` with `detail` `named tank/other, not tank/factory/vm`; exit 2 raises it with the output's last line.
9. `ZfsSnapshots` is an instance of `Snapshots`, and `tests/test_wrapper_search.py` lists `factory.adapters.zfs_snapshots` among the modules that import the process module (decision 18 b).
10. `changed_paths()` with `diff` planned to print the line `+\tF\t/srv/factory/vm/work/bad\377` (an escape whose byte is not UTF-8) raises `SnapshotError` with `command` `<stand-in> diff -FH tank/factory/vm@base` and `detail` `cannot read the line +\tF\t/srv/factory/vm/work/bad\377` (a row of criterion 4's parametrized test).
11. `make check` stays green.
12. docs: `docs/project-guide/stage-environment.md` gains the section *The ZFS adapter*: the five commands and when each runs, the reading of `zfs diff -FH` (the kinds, the rename, the escapes, the mount point), the faults and their details, `version` and `dataset_exists` for the preflight, the stand-in the tests use; `docs/project-guide/README.md`, *The files*, names `factory.adapters.zfs_snapshots` for the file. `docs/operator-guide.md`: nothing yet (S0010 writes the settings, S0011 the items). `docs/decisions.md`: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cat > "$d/zfs" <<'EOF'
#!/bin/sh
echo "$@" >> "$(dirname "$0")/calls.txt"
case "$1" in
  rollback|destroy|snapshot) exit 0 ;;
  list) [ "$6" = "snapshot" ] && exit 1; echo "tank/factory/vm"; exit 0 ;;
  diff) printf 'M\t/\t/srv/factory/vm/work/checkout\nM\tF\t/srv/factory/vm/work/checkout/src/a.py\n+\tF\t/srv/factory/vm/work/checkout/with\\040space.txt\nR\tF\t/srv/factory/vm/work/checkout/old.md\t/srv/factory/vm/work/checkout/new.md\n-\tF\t/srv/factory/vm/work/home/x\n'; exit 0 ;;
  --version) echo "zfs-2.2.2-0ubuntu9.1"; echo "zfs-kmod-2.2.2-0ubuntu9.1"; exit 0 ;;
esac
echo "zfs: unknown $1" >&2; exit 2
EOF
chmod +x "$d/zfs"
uv run python - "$d" <<'EOF'
import sys
from pathlib import Path

from factory.adapters.zfs_snapshots import ZfsSnapshots
from factory.domain.errors import SnapshotError

d = Path(sys.argv[1])
zfs = ZfsSnapshots("tank/factory/vm", Path("/srv/factory/vm/work"), executable=str(d / "zfs"))
zfs.reset()
zfs.advance()
print([(c.path, c.change) for c in zfs.changed_paths()])
print(zfs.version(), zfs.dataset_exists())
try:
    ZfsSnapshots("tank/factory/vm", Path("/srv/factory/vm/work"), executable=str(d / "nowhere")).reset()
except SnapshotError as error:
    print(error.command.endswith("nowhere rollback -r tank/factory/vm@base"), error.detail.startswith("[Errno 2]"))
print((d / "calls.txt").read_text(encoding="utf-8"), end="")
EOF
```
Expect: three lines of Python output, `[('checkout/new.md', 'added'), ('checkout/old.md', 'deleted'), ('checkout/src/a.py', 'modified'), ('checkout/with space.txt', 'added'), ('home/x', 'deleted')]`, `zfs-2.2.2-0ubuntu9.1 True`, `True True`; then the recorded calls, one per line: `rollback -r tank/factory/vm@base`, `list -H -o name -t snapshot tank/factory/vm@base`, `snapshot tank/factory/vm@base`, `diff -FH tank/factory/vm@base`, `--version`, `list -H -o name tank/factory/vm`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: The format check passed. The Interface, architecture, scope and smoke test are fine, but two rules in the Interface have no criterion for their failing side:

   1. The Interface says a nonzero exit status from `destroy` or `snapshot` is a fault, and criterion 2 covers only the `list` failure. Nothing tests a failing `destroy` or a failing `snapshot` inside `advance()`. Should criterion 2 gain two rows, or a new criterion? I would add two rows: `destroy` planned to exit 1 raises `SnapshotError` with `command` `<stand-in> destroy tank/factory/vm@base` and `snapshot` is not called, and `snapshot` planned to exit 1 raises it with `command` `<stand-in> snapshot tank/factory/vm@base`. Each row would also say what `detail` is.

   2. The Interface says an `R` line with fewer fields than its form needs is a fault, meaning four fields: `<change> <kind> <old path> <new path>`. Criterion 4 covers only `M\tF` (too few fields) and `X\tF\t...` (unknown change). Nothing covers an `R` line with only three fields, or an `R` line whose new path is outside the mount point. I would add two rows to criterion 4. First, `R\tF\t/srv/factory/vm/work/a` gives `cannot read the line R\tF\t/srv/factory/vm/work/a`. Second, `R\tF\t/srv/factory/vm/work/a\t/elsewhere/b` gives `/elsewhere/b is outside /srv/factory/vm/work`.

   Smaller gap, no question needed if you agree: no criterion has the backslash escape `\134`, which the Interface names. I would add a `\134` path to criterion 3 or to a row of its own.
4. 2026-10-24 human: All as you propose, in your exact words:

   1. Yes: two rows in criterion 2. `destroy` planned to exit 1 raises `SnapshotError` with `command` `<stand-in> destroy tank/factory/vm@base` and `snapshot` is not called; `snapshot` planned to exit 1 raises it with `command` `<stand-in> snapshot tank/factory/vm@base`. Each row says what `detail` is (the last non-blank line of the stand-in's output, as the Interface says for every failed command).
   2. Yes: two rows in criterion 4. `R\tF\t/srv/factory/vm/work/a` gives `cannot read the line R\tF\t/srv/factory/vm/work/a`; `R\tF\t/srv/factory/vm/work/a\t/elsewhere/b` gives `/elsewhere/b is outside /srv/factory/vm/work`.
   3. Yes: add a `\134` path to criterion 3 (a row of its own is fine too).

   You have leave to edit the Acceptance criteria for exactly these additions; the Interface and the Description stay as they are.
5. factory: started intake as self.
6. intake: accepted
   - Interface: `factory.adapters.zfs_snapshots` names the constants, the `ZfsSnapshots(Snapshots)` constructor and signatures, `version()` and `dataset_exists()`. Every command, argv, cwd/env/time_limit/merge_stderr setting and fault form is stated concretely.
   - Criteria: each is testable by one parametrized or plain test. Every rule has both sides: pass/fail for `list` exit 0/1/other, the diff change letters, the mount point (outside, `workx`), too few fields, timeouts, `OSError`, and `version`/`dataset_exists`. I carried in the human's answer (journal entry 4), which is the human's edit and not an improvement of mine. Criterion 2 gained two rows (`destroy` exit 1 with `snapshot` not called, and `snapshot` exit 1; each `detail` is the printed last line). Criterion 3 gained a `\134` path (`back\134slash.txt` → `checkout/back\slash.txt`, sorted first in the expected list). Criterion 4 gained the two `R` rows (three fields, and the new path outside the mount point). The Interface and Description are unchanged.
   - Smoke test: the command is runnable. The stand-in script and the Python check cover reset, advance, diff, version, dataset_exists and the missing executable. The `Expect:` line is checkable against the output. It runs no pytest. The smoke test is unchanged, and the new `\134` and `destroy`/`snapshot` rows are covered by the tests only.
   - Architecture: the new module is in `adapters`, reaches `zfs` only through `run_process` from `factory.adapters.process`, and implements the application-layer interface `Snapshots`. The layer rules and the wrapper rule (R5) hold. The wrapper-search leave is decision 18 b of `feature.md`.
   - Scope: within F0042's scope, which lists `zfs_snapshots` as S0002. Nothing is wired, which is S0010's job. The docs criterion names the guide file and the README row.
7. factory: started tests as self.
8. tester: I wrote the tests for every criterion against the Interface, on a stand-in `zfs`. The stand-in records each call's arguments, environment and working directory, and answers by a plan keyed on its first argument.

   Mapping:
   - criterion 1: tests/adapters/test_zfs_snapshots.py::test_reset_rolls_back_to_the_base_and_keeps_the_mount_point
   - criterion 2: tests/adapters/test_zfs_snapshots.py::test_advance_replaces_the_base_by_what_list_says (rows base, no-base, list-2, destroy-fails, snapshot-fails)
   - criterion 3: tests/adapters/test_zfs_snapshots_diff.py::test_changed_paths_reads_the_diff_relative_to_the_mount_point (rows lines, empty)
   - criterion 4: tests/adapters/test_zfs_snapshots_diff.py::test_a_diff_it_cannot_read_is_a_fault (rows outside, sibling, unknown-change, short, short-rename, rename-outside, fails)
   - criterion 5: tests/adapters/test_zfs_snapshots.py::test_a_failed_reset_names_its_detail (rows last-line, silent, time-limit with 1.5 s and elapsed in [1, ROOMY_BOUND_SECONDS), missing `/nowhere/zfs`); tests/adapters/test_zfs_snapshots.py::test_the_default_time_limit_is_ten_minutes_and_reaches_run_process (the module's `run_process` replaced by a `Recorder` with one planned result)
   - criterion 6: tests/adapters/test_zfs_snapshots.py::test_a_command_merges_stderr_runs_at_the_root_in_the_factorys_environment
   - criterion 7: tests/adapters/test_zfs_snapshots.py::test_version_is_the_first_line_zfs_prints (rows first-line, nothing, fails)
   - criterion 8: tests/adapters/test_zfs_snapshots.py::test_dataset_exists_reads_what_list_names (rows named, none, other, fails). The exit-2 row prints `warning` and then `cannot open 'tank/factory/vm': permission denied`, so the expected detail is the last line.
   - criterion 9: tests/adapters/test_zfs_snapshots.py::test_the_adapter_implements_the_snapshots_interface; tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module
   - criteria 10 and 11: no test (make check, docs).

   Files created:
   - tests/zfs_support.py: the shared stand-in (`write_zfs`, `Answer`, `Zfs`, `ZfsCall`), the constants `DATASET` and `MOUNT_POINT`, and `snapshots_on`. Both test modules use it, so it lives in one place.
   - tests/adapters/test_zfs_snapshots.py
   - tests/adapters/test_zfs_snapshots_diff.py

   Earlier test file changed: tests/test_wrapper_search.py. It now has `factory.adapters.zfs_snapshots` in the expected set. Criterion 9 of this story names that test and that change; the test's name and docstring are unchanged.

   The stand-in prints planned output to standard output for the rows where criteria 2, 5, 7 and 8 say "print". It prints to standard error only where a criterion names it (criterion 6's `boom`, the `list`/`diff` exit-1 rows), so the multi-line rows have a set order under the merge.

   The one `make test` run failed for the right reasons. Both new modules raised ImportError at collection, because `factory.adapters.zfs_snapshots` does not exist; `tests/zfs_support.py` imports it too. The wrapper-search test failed its assertion because the module does not import the process module yet. After that run I fixed only lint and format (ruff format and the parameter layout of the reset test); no test changed meaning. `make lint` is green. The type check was skipped, as the stage says.

   Could not be imported: `factory.adapters.zfs_snapshots`.

   `lint`: lint: green (0.8 s)
   `test`: ERROR tests/adapters/test_zfs_snapshots_diff.py - ImportError while importing test module '/work/checkout/tests/adapters/test_zfs_snapshots_diff.py'.
9. factory: started doing as self.
10. coder: I built `src/factory/adapters/zfs_snapshots.py`: `BASE_SNAPSHOT`, `SNAPSHOT_TIME_LIMIT` and `ZfsSnapshots(Snapshots)` with `reset`, `advance`, `changed_paths`, `version` and `dataset_exists`, as the Interface describes. Every command goes through one private `_run`. It builds the `ProcessRequest` (cwd `/`, env `None`, the time limit given, `merge_stderr` true) and turns an `OSError`, a timed-out run or an exit status outside the accepted ones into `SnapshotError(command, detail)`. The two `list` commands accept 0 and 1. Every other command accepts only 0. `make check` is green (`check: green`). The tester's tests all pass unchanged, and the new module has 98 % branch coverage.

    Main choice: `zfs diff -FH` is read line by line into a dict from path to change. A path that two lines name is recorded once by one rule in `_record`: it is `added` when either of the two lines adds it, otherwise the later line's change. That covers both cases the Interface names: a file removed and made anew, and a rename onto a removed path. The rejected alternative was to collect every pair and then merge only the remove/add pairs; that is more code for the same result. The mount-point check uses `PurePosixPath.is_relative_to`, so `<mount point>x/...` counts as outside without any string-prefix handling. Octal escapes are decoded on bytes before that check, so the detail names the decoded path.

    Refactor: `_first_line` and `_last_line` built the same list, so that moved into one shared helper, `_printed_lines`. I also added the type annotation mypy needed on the rename's pair of changes. Nothing else needed changing.

    Noticed, not touched:
    - After decoding, a path that is not valid UTF-8 is reported as the fault `cannot read the line <line>`. The Interface does not say what should happen there. This is the only uncovered code in the module (lines 50-51), because no criterion has such a line. The reviewer may want a criterion for it, or a different reading.
    - A line that names the mount point itself is made relative as `.`. In practice that line is always a directory and is left out.
    - `make_commands._last_line` exists but skips make's own messages, so it is not the same helper. The adapter has its own small `_last_line`.

    `check`: check: green
    `duplicates`: duplicates: 8 new, 38 known, 0 gone
11. factory: started review as self.
12. reviewer: Review, round 0. I read the work item and `git diff main...HEAD -- . ':!factory'` against criteria 1 to 9 and the Interface. Criteria 1 to 9 each have a test that checks what they say. The faults of `list` (status 0, 1 and other), of the field counts (`M` 3 fields, `R` 4), of the mount point (outside and the `workx` sibling) and of the time limit (1.5 s rounded up to 2) are tested on both sides. I did not run `make check`: per the journal, the factory's run after the coder was green. I did run `make duplicates`. Its two new findings in this module (`ZfsSnapshots` and `dataset_exists` unused) are expected until S0010 wires the class, so they are not findings. `pipeline_yaml._first_line` and the non-blank-lines idiom in `agent_home` are private to their own modules, and no shared helper holds them, so no copy finding. I stopped at group 1, as the checklist says.

    Findings:
    1. criterion 10 added: it needs its test. `src/factory/adapters/zfs_snapshots.py:45-51` (`_unescape`) raises `cannot read the line <line>` when a decoded path is not UTF-8. No criterion names this behaviour, and lines 50-51 are the module's only uncovered code. The fix is a row in `tests/adapters/test_zfs_snapshots_diff.py::test_a_diff_it_cannot_read_is_a_fault` with the line `+\tF\t/srv/factory/vm/work/bad\377`. The old criteria 10 and 11 are now 11 and 12.
    2. `src/factory/adapters/zfs_snapshots.py:117-122` (`dataset_exists`): when `list -H -o name <dataset>` exits 0 and prints nothing, `named` is `None` and the detail reads `named None, not tank/factory/vm`, which leaks a Python value into the fault. The Interface's rule covers only "another first line", and no criterion covers an empty output. Fix: give an empty output its own detail, `printed nothing` as `version()` does, and add a row for it to criterion 8's parametrized test. This needs a code change, so I did not add the criterion myself. If the coder reads the Interface as leaving this open, it is a question for the human.

    Earlier tests:
    - tests/test_wrapper_search.py: the human's leave. Criterion 9 of the story, as the human wrote it, names this test and the added `factory.adapters.zfs_snapshots`. The change only adds that one name to the expected set, and the test keeps its name.
13. factory: started doing as self.
14. coder: Round 1. I addressed the reviewer's two findings. Both now need only tests.

    1. Criterion 10 (added by the reviewer) needs its test and no code change: a row in `tests/adapters/test_zfs_snapshots_diff.py::test_a_diff_it_cannot_read_is_a_fault` whose `diff` prints `+\tF\t/srv/factory/vm/work/bad\377`, expecting `command` `<stand-in> diff -FH tank/factory/vm@base` and `detail` `cannot read the line +\tF\t/srv/factory/vm/work/bad\377`. `src/factory/adapters/zfs_snapshots.py` (`_unescape`) already raises this. The row covers that path, which until now no test reached.

    2. An empty output from `dataset_exists()`. In `src/factory/adapters/zfs_snapshots.py`, `dataset_exists` now raises `SnapshotError` with `detail` `printed nothing` when `list -H -o name <dataset>` exits 0 and prints nothing. Before, it gave `named None, not <dataset>`. I chose this detail because `version()` uses the same wording for an empty output. Rejected alternative: asking the human first. The Interface already calls a status-0 output that does not name the dataset a fault and only lacked this detail, and the reviewer proposed this fix. For the tester: please add a row to `tests/adapters/test_zfs_snapshots.py::test_dataset_exists_reads_what_list_names` where `list` exits 0 and prints nothing, expecting `SnapshotError` with `detail` `printed nothing`. I tried to write this rule into the work item (the Interface's `dataset_exists()` bullet and criterion 8), but the work item is outside my write paths (`Permission denied`), so it is still missing from the text. Whoever may write the work item should add it.

    Refactor: the diff is two lines, so nothing needed changing. `make check` is green after the change (`check: green`). No test was touched.

    Noticed, not touched: none beyond round 0's notes.
15. factory: started tests as self.
16. tester: Round 1, a test change the coder's entry 14 names. I made one of its two changes and stopped before the other, which no criterion covers.

    Done:
    - criterion 10: tests/adapters/test_zfs_snapshots_diff.py::test_a_diff_it_cannot_read_is_a_fault, new row `not-utf-8`. `diff` prints `+\tF\t/srv/factory/vm/work/bad\377` and the test expects `detail` `cannot read the line +\tF\t/srv/factory/vm/work/bad\377`. Its `command` is checked by the test's shared assertion. The reviewer added this criterion and only its test was missing, so step 0 lets me write it. The code already behaves this way, so the row passes.

    Not done, and this is the question: the coder asked for a row in tests/adapters/test_zfs_snapshots.py::test_dataset_exists_reads_what_list_names where `list -H -o name tank/factory/vm` exits 0, prints nothing, and raises `SnapshotError` with `detail` `printed nothing`. The coder has already changed `dataset_exists` to do that. But neither the Interface nor criterion 8 says what an empty status-0 output should give. Criterion 8 covers only "another first line" (`named <line>, not <dataset>`). No human answer has approved this rule; it was the coder's own call, because they could not write the work item. I test what the criteria say, so this open case goes to you. Options:
      (a) Add the rule to the work item: in the Interface's `dataset_exists()` bullet, "exit status 0 with no non-blank line is a fault with `detail` `printed nothing`", and in criterion 8 a row "exit 0 printing nothing raises `SnapshotError` with `detail` `printed nothing`". Then I add that row. This is the one I would choose, because it matches `version()`'s wording and the code already does it.
      (b) Treat an empty output as `False` (the dataset is not named). That changes the code and gets a row of its own.
      (c) Leave the case untested and unspecified.
    Please also say who writes the work item's text for (a): the human, or the tester with your leave.

    Files changed: tests/adapters/test_zfs_snapshots_diff.py (one row added; this story's own test). No other test file changed.
    Every module imports; `factory.adapters.zfs_snapshots` now exists.
    `make test`: test: green (72.0 s). `make lint`: lint: green (0.2 s).
17. 2026-10-24 human: Answer to the tester's question (F0042-S0002, ZFS snapshots roll back, advance and diff the dataset): **(a)**.

    The rule is the human's from this answer: in `dataset_exists()`, an exit status 0 with no non-blank line is a fault, `SnapshotError` with `detail` `printed nothing`, worded like `version()`. It is a new row of criterion 8.

    Who writes what: the tester adds the row to `tests/adapters/test_zfs_snapshots.py::test_dataset_exists_reads_what_list_names` now. The test is this story's own, so no leave is needed. The tester does not edit the work item, which lies outside its write paths. The reviewer, whose write path is the work item, writes the rule into the Interface's `dataset_exists()` bullet and the row into criterion 8 in its round, citing this answer.

    The coder's change to `dataset_exists` stands as it is.
18. factory: started tests as self.
19. tester: Round 1: the test change the coder's entry 14 asked for, which the human approved as option (a) in entry 17.

    Changed:
    - criterion 8: tests/adapters/test_zfs_snapshots.py::test_dataset_exists_reads_what_list_names has a new row, `nothing`. `list -H -o name tank/factory/vm` exits 0 and prints nothing, and the test expects `SnapshotError` with `detail` `printed nothing`. The test's shared assertion also checks the arguments of the call. The coder's change to `dataset_exists` already does this, so the row passes.

    Files changed: tests/adapters/test_zfs_snapshots.py (one row added; this story's own test). I created no files and changed no other test file. I did not edit the work item. Per entry 17, the reviewer writes the rule into the Interface's `dataset_exists()` bullet and adds the row to criterion 8.

    Every module imports. `make test`: test: green (70.9 s). `make lint`: lint: green (0.2 s).

    `lint`: lint: green (0.7 s)
    `test`: test: green (71.1 s)
20. factory: started doing as self.
21. coder: Round 1, after the tester's entry 19. Both of the reviewer's findings from entry 12 are now covered by code and by tests, so I made no code change this run.

    - Finding 1 (criterion 10): `src/factory/adapters/zfs_snapshots.py` (`_unescape`) already raises `cannot read the line <line>` for a path whose escapes do not decode as UTF-8. The tester's row `not-utf-8` in `tests/adapters/test_zfs_snapshots_diff.py::test_a_diff_it_cannot_read_is_a_fault` now tests it.
    - Finding 2: `dataset_exists` raises `SnapshotError` with `detail` `printed nothing` when `list` exits 0 and prints nothing. I made that change in entry 14, and the human approved it as option (a) in entry 17. The tester's row `nothing` in `tests/adapters/test_zfs_snapshots.py::test_dataset_exists_reads_what_list_names` tests it.

    Main choice: I left the code as it is, since both rows pass against it. The alternative was another touch to `dataset_exists`. I rejected it because entry 17 says the coder's change stands as it is.

    Refactor: I re-read `src/factory/adapters/zfs_snapshots.py` and found nothing to change. `make check` is green (`check: green`, total coverage 99.16 %). I touched no test.

    Description and Interface: entry 17 changed the meaning of the task. In `dataset_exists()`, an exit status 0 with no non-blank line is a fault with `detail` `printed nothing`, and criterion 8 gains that row. Per entry 17, the reviewer writes that into the Interface's `dataset_exists()` bullet and criterion 8, so I left the work item's text untouched.

    Noticed, not touched: nothing new beyond the notes from round 0.

    `check`: check: green
    `duplicates`: duplicates: 8 new, 38 known, 0 gone
