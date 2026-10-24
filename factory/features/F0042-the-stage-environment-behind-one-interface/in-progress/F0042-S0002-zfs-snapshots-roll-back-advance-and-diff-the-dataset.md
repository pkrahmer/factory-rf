---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 408
comments_read: [6383983454]
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-24T12:06:06.993656Z'
  lease_duration: 60
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
10. `make check` stays green.
11. docs: `docs/project-guide/stage-environment.md` gains the section *The ZFS adapter*: the five commands and when each runs, the reading of `zfs diff -FH` (the kinds, the rename, the escapes, the mount point), the faults and their details, `version` and `dataset_exists` for the preflight, the stand-in the tests use; `docs/project-guide/README.md`, *The files*, names `factory.adapters.zfs_snapshots` for the file. `docs/operator-guide.md`: nothing yet (S0010 writes the settings, S0011 the items). `docs/decisions.md`: none.

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
