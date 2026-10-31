---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 481
comments_read: [6545517612]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-31T15:37:43.120560Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-31T15:37:43.126780Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-31T15:38:04.318649Z'
  stage: intake
  run: 06e4182a36874f048ca3ad07e187ce5e
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-31T15:40:24.131159Z'
  stage: intake
---

# A snapshot adapter that copies a directory

## Description

The factory's stage environment needs a `Snapshots`: reset the dataset to its base, move the base forward, list what changed. Today there is one real adapter, `ZfsSnapshots`, and a fake that keeps the base as a copy beside the folder. A sandbox without ZFS (a Cloud Run job) needs the second one for real. This story promotes the fake: its logic moves to `CopySnapshots` in `factory.adapters`, with one change that matters when the folder holds a gigabyte (files are compared in chunks, never read whole into memory), and `FakeSnapshots` becomes a subclass with the same constructor so that no test of the suite changes. Two settings choose it: `FACTORY_SNAPSHOTS=copy` and `FACTORY_SNAPSHOT_BASE`, the base directory. With `copy` the dataset is not read; the preflight's `zfs` and `dataset` items give way to one item, `snapshots`, that checks the workspace and the base directory. Unchanged: the default (`zfs`), `ZfsSnapshots`, the `Snapshots` interface, every other setting, and what a copy costs (reset 1.6 s per GiB measured on a tree of 20000 files, the diff 0.2 s with rsync, so the first version is slower than that and a later one may use rsync). Left to later stories: the container profile (S0002).

## Interface

`factory.domain.settings` (domain): constants `SNAPSHOTS_VARIABLE = "FACTORY_SNAPSHOTS"` and `SNAPSHOT_BASE_VARIABLE = "FACTORY_SNAPSHOT_BASE"`, and the fields `InstanceSettings.snapshots: Literal["zfs", "copy"] = "zfs"` and `snapshot_base: Path | None = None`.

- `read_settings`: `FACTORY_SNAPSHOTS` unset or blank is `zfs`; `zfs` and `copy` are accepted; anything else is `SettingsInvalid(FACTORY_SNAPSHOTS, "is neither zfs nor copy")`.
- `FACTORY_SNAPSHOT_BASE` is read with the optional-path reader: unset or blank is `None`; a relative path is `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "is not an absolute path")`.
- With `copy`: a missing base is `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "missing")` when the boundaries are built (like the dataset today), not when the settings are read; a base that is the workspace, lies inside it, holds it, or is, holds or lies inside the checkout or the state directory is `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "<path> overlaps <workspace|checkout|state>")` when the settings are read. The model validator refuses the same combinations with a `ValidationError`.
- With `zfs`: a base set is `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "is only used with FACTORY_SNAPSHOTS=copy")`.

`factory.adapters.copy_snapshots` (adapters, new): `class CopySnapshots(Snapshots)` with the constructor `(folder: Path, base: Path)` and the three operations of `FakeSnapshots` today, with these rules:

- `reset` empties `folder` (the folder stays) and copies `base` into it, links as links; `advance` replaces `base` with a copy of `folder`; both raise `SnapshotError(<operation>, <the operating system's message>)` for an `OSError`. `reset` and `changed_paths` raise `SnapshotError(<operation>, "no base at <base>")` without a base, `reset` changing nothing.
- `changed_paths` lists every file and link whose mode, bytes or link target differ, by path, sorted, `added`, `modified` or `deleted`, never a directory; bytes are compared in chunks of at most 1 MiB, so memory use does not grow with the size of a file.

`factory.adapters.fake_snapshots` (adapters): `class FakeSnapshots(CopySnapshots)` with no body of its own beyond its docstring; every test of it passes unchanged.

`factory.application.preflight` (application): `def snapshots_item(workspace: Path, base: Path) -> PreflightItem`, the item `snapshots`: passes when both are directories, with the detail `workspace <w>, base <b>`; fails with `the workspace <w> is not a directory` or `the base <b> does not exist; make it empty with mkdir, the first advance fills it`.

`factory.entry.wiring` (entry): `_container_adapters` builds `CopySnapshots(workspace, base)` for `copy` (and then needs no dataset) and `ZfsSnapshots` as today for `zfs`; `_container_items` gives, for `copy`, `podman`, `snapshots` and `stage-image` and no `zfs` or `dataset` item. `build_boundaries` raises `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "missing")` first for `copy` without a base, then the workspace and image faults as today.

Tests (the tester writes them): `tests/domain/test_settings_snapshots.py`, `tests/adapters/test_copy_snapshots.py` (a real tree in `tmp_path`), `tests/application/test_preflight_snapshots_item.py`, `tests/entry/test_wiring_copy_snapshots.py`. `tests/adapters/test_fake_snapshots.py` passes unchanged.

## Acceptance criteria

1. With `FACTORY_SNAPSHOTS` unset the settings, the boundaries and the preflight items are those of before this story (rows: settings fields, the type of `Boundaries.snapshots`, the item names).
2. `FACTORY_SNAPSHOTS` is read, rows of one parametrized test: unset, blank and `zfs` give `zfs`; `copy` gives `copy`; `ZFS`, `btrfs` and `copy now` are refused as `is neither zfs nor copy`.
3. `FACTORY_SNAPSHOT_BASE` is read, rows of one test: unset and blank give `None`; `/var/base` gives that path; `base` is refused as not absolute; with `copy` and the workspace `/work`, the bases `/work`, `/work/b` and `/` are refused as overlapping the workspace; `/work2` is accepted; with the checkout `/srv/repo`, `/srv/repo` and `/srv` are refused as overlapping it and `/srv/base` is accepted; the same for the state directory; with `zfs` a base is refused as `is only used with FACTORY_SNAPSHOTS=copy`.
4. `InstanceSettings(snapshots="copy", snapshot_base=Path("/work/b"), workspace=Path("/work"))` is a `ValidationError`.
5. `CopySnapshots` over a real tree: after `advance`, a modified file, an added file and a deleted file, `changed_paths` is those three changes sorted by path; a directory-only change lists nothing; a changed mode is `modified`; a link that now points elsewhere is `modified`; `reset` brings the tree back byte for byte and mode for mode, links as links, and keeps the folder itself.
6. `CopySnapshots` without a base: `reset` and `changed_paths` raise `SnapshotError` whose detail is `no base at <base>` and `reset` leaves the folder as it was; `advance` makes the base.
7. A file of 3 MiB that differs from the base in its last byte is `modified`, and the comparison reads at most 1 MiB at a time (a test that wraps the file reader and checks the largest read).
8. An `OSError` of the copy (a base that is a file) is a `SnapshotError` naming the operation.
9. `FakeSnapshots` is a `CopySnapshots` and `tests/adapters/test_fake_snapshots.py` is unchanged and green.
10. `snapshots_item`: a workspace and a base that are directories pass with the detail `workspace <w>, base <b>`; a workspace that is a file, a missing workspace and a missing base each fail with the sentences of the Interface.
11. `build_boundaries` with `copy`, a workspace, a base and an image, and no dataset, gives `CopySnapshots` on those paths; without the base it raises `SettingsInvalid` naming `FACTORY_SNAPSHOT_BASE`; `machine_extras` for `copy` holds the items `podman`, `snapshots`, `stage-image` and `agent-run-probe` and none named `zfs` or `dataset`.
12. `make check` stays green.
13. docs: `docs/operator-guide.md`: the two variables in the configuration table, and a subsection *Without ZFS* under the stage environment: the copy adapter, the empty base made once with `mkdir`, the cost (reset about 1.6 s per GiB, both copies in memory in a memory-backed sandbox). `docs/project-guide/stage-environment.md`: *The snapshots* names `CopySnapshots`, and the fake's section says `FakeSnapshots` is its subclass. `docs/decisions.md`: an entry *A snapshot adapter that copies a directory*, from the feature's decisions 1 and 2. `README.md`: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run python - "$d" <<'PY'
import sys
from pathlib import Path
from factory.adapters.copy_snapshots import CopySnapshots
root = Path(sys.argv[1]); work = root / "w"; base = root / "b"; work.mkdir()
(work / "a.txt").write_text("one")
snapshots = CopySnapshots(work, base)
snapshots.advance()
(work / "a.txt").write_text("two"); (work / "n.txt").write_text("n")
print([(c.path, c.change) for c in snapshots.changed_paths()])
snapshots.reset()
print(sorted(p.name for p in work.iterdir()), (work / "a.txt").read_text())
PY
```
Expect: two lines, `[('a.txt', 'modified'), ('n.txt', 'added')]` and `['a.txt'] one`

```bash
uv run python -c "
from factory.domain.settings import read_settings, SettingsInvalid
env = {'FACTORY_REPOSITORY_URL': 'https://example.invalid/o/r.git', 'FACTORY_INSTANCE': 'vm', 'FACTORY_CLAUDE_HOME': '/x/claude'}
print(read_settings(env).snapshots)
try:
    read_settings({**env, 'FACTORY_SNAPSHOTS': 'btrfs'})
except SettingsInvalid as error:
    print(error)
"
```
Expect: two lines, `zfs` and a message that names `FACTORY_SNAPSHOTS` and `is neither zfs nor copy`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-31 human: created.
2. factory: started intake as vm.
3. intake: 1. Format check: passed. Nothing to add.
   2. The Interface says `build_boundaries` raises `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "missing")` "first ... then the workspace and image faults as today". Criterion 11 only tests the missing base on its own. No criterion checks the ordering, for example a copy setup with no base and also a missing workspace or image, which must name `FACTORY_SNAPSHOT_BASE`. Should I add that criterion, or drop "first" from the Interface? I would add the criterion.
   3. The Interface says "The model validator refuses the same combinations with a `ValidationError`." That covers a base that overlaps the workspace, the checkout or the state directory. Criterion 4 tests only the workspace case (`/work/b`). The checkout and state overlaps, and the "holds it" side (base `/`), have no model-level criterion. Should criterion 4 become rows covering the workspace, the checkout and the state directory (inside, equal, holding), plus an accepted non-overlapping base? I would add those rows.
   4. The `zfs` rule "a base set is `only used with FACTORY_SNAPSHOTS=copy`" is tested in `read_settings` (criterion 3). The Interface does not say whether the model validator also refuses `snapshots="zfs"` with a `snapshot_base`. Please state which, and add a criterion for it either way.
   5. `snapshots_item` fails when the "base does not exist". Criterion 10 does not say what happens when the base exists but is a file. The Interface says the item passes "when both are directories", so a file base should fail. The failure sentence ("does not exist") would then be misleading. Which sentence should a file base get? I would use a separate row with the same "does not exist" sentence, to keep the Interface as written.
   6. Criterion 8 names only a base that is a file, which gives the `OSError` for `reset`. The Interface also gives `advance` its own `OSError` to `SnapshotError` rule. Is a second row for `advance` wanted, for example with a read-only or unreadable folder? I would add it with the operation name `advance`.

   Checked and fine: the smoke test commands are runnable and neither runs pytest. The `Expect:` lines are checkable. The architecture is right: domain settings, adapters, application preflight, entry wiring. The scope matches the feature's S0001.
4. 2026-10-31 human: Answers to question 3:

   2. Add the criterion: with `copy`, no base and also no workspace (and a second row with no stage image), `build_boundaries` raises `SettingsInvalid` naming `FACTORY_SNAPSHOT_BASE`. Keep "first" in the Interface.
   3. Yes: criterion 4 becomes rows of one parametrized test, the base inside, equal to and holding each of the workspace, the checkout and the state directory, each a `ValidationError`, plus one accepted base that overlaps none.
   4. The model validator refuses `snapshots="zfs"` with a `snapshot_base` too, with a `ValidationError`, the same rule as `read_settings`. Add it as a row of criterion 4.
   5. A base that exists but is a file fails with its own sentence, `the base <b> is not a directory`; "does not exist" would mislead the operator. Change the Interface's `snapshots_item` line accordingly and add the row to criterion 10. The same for a workspace that is a file, which already has `is not a directory`.
   6. Yes, a row for `advance` with the operation name `advance`. Make the fault independent of the user the tests run as (a check container may run them as root, where a read-only folder is still writable): a base whose parent path is a regular file, so the copy raises `NotADirectoryError`.
