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
2. `advance()` (rows of one parametrized test): with `list` planned to exit 0, the calls are `["list", "-H", "-o", "name", "-t", "snapshot", "tank/factory/vm@base"]`, `["destroy", "tank/factory/vm@base"]`, `["snapshot", "tank/factory/vm@base"]` in that order; with `list` planned to exit 1 and print `cannot open 'tank/factory/vm@base': dataset does not exist` to standard error, the calls are the `list` and the `snapshot` only; with `list` planned to exit 2, `SnapshotError` is raised whose `command` is `<stand-in> list -H -o name -t snapshot tank/factory/vm@base` and nothing else is called.
3. `changed_paths()` with `diff` planned to print, tab-separated, `M\t/\t/srv/factory/vm/work/checkout`, `+\t/\t/srv/factory/vm/work/checkout/newdir`, `M\tF\t/srv/factory/vm/work/checkout/src/a.py`, `+\tF\t/srv/factory/vm/work/checkout/new.txt`, `-\tF\t/srv/factory/vm/work/home/.claude.json`, `R\tF\t/srv/factory/vm/work/checkout/old.md\t/srv/factory/vm/work/checkout/renamed.md`, `-\tF\t/srv/factory/vm/work/checkout/renamed.md`, `+\t@\t/srv/factory/vm/work/checkout/link`, `+\tF\t/srv/factory/vm/work/checkout/with\040space.txt`, `+\tF\t/srv/factory/vm/work/checkout/caf\303\251.txt`, `M\tF\t/srv/factory/vm/work/home/.cache/uv/w\t(+1)` returns exactly `[ChangedPath("checkout/café.txt", "added"), ChangedPath("checkout/link", "added"), ChangedPath("checkout/new.txt", "added"), ChangedPath("checkout/old.md", "deleted"), ChangedPath("checkout/renamed.md", "added"), ChangedPath("checkout/src/a.py", "modified"), ChangedPath("checkout/with space.txt", "added"), ChangedPath("home/.cache/uv/w", "modified"), ChangedPath("home/.claude.json", "deleted")]` (the two directories left out, `checkout/renamed.md` once although two lines name it, the link-count field ignored), and the one call has the arguments `["diff", "-FH", "tank/factory/vm@base"]`. An empty output returns `[]`.
4. `changed_paths()` faults (rows of one parametrized test, each `SnapshotError` with `command` `<stand-in> diff -FH tank/factory/vm@base`): the line `M\tF\t/elsewhere/a.py` gives `detail` `/elsewhere/a.py is outside /srv/factory/vm/work`, and so does `M\tF\t/srv/factory/vm/workx/a` with `/srv/factory/vm/workx/a is outside /srv/factory/vm/work`; the line `X\tF\t/srv/factory/vm/work/a` gives `cannot read the line X\tF\t/srv/factory/vm/work/a`; the line `M\tF` gives `cannot read the line M\tF`; `diff` planned to exit 1 with standard error `cannot open 'tank/factory/vm@base': dataset does not exist` gives `detail` `cannot open 'tank/factory/vm@base': dataset does not exist`.
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
