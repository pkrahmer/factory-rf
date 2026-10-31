---
stage: doing
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
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-31T15:40:41.810451Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-31T15:41:11.715745Z'
  stage: intake
  run: eb8ad0dc3f124a58a34ea049a75f6652
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-31T15:41:32.139328Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-31T15:50:12.327985Z'
  stage: tests
  run: cc0b8bd4ec7143eba3c13eb29f9a7de9
---

# A snapshot adapter that copies a directory

## Description

The factory's stage environment needs a `Snapshots`: reset the dataset to its base, move the base forward, list what changed. Today there is one real adapter, `ZfsSnapshots`, and a fake that keeps the base as a copy beside the folder. A sandbox without ZFS (a Cloud Run job) needs the second one for real. This story promotes the fake: its logic moves to `CopySnapshots` in `factory.adapters`, with one change that matters when the folder holds a gigabyte (files are compared in chunks, never read whole into memory), and `FakeSnapshots` becomes a subclass with the same constructor so that no test of the suite changes. Two settings choose it: `FACTORY_SNAPSHOTS=copy` and `FACTORY_SNAPSHOT_BASE`, the base directory. With `copy` the dataset is not read; the preflight's `zfs` and `dataset` items give way to one item, `snapshots`, that checks the workspace and the base directory. Unchanged: the default (`zfs`), `ZfsSnapshots`, the `Snapshots` interface, every other setting, and what a copy costs (reset 1.6 s per GiB measured on a tree of 20000 files, the diff 0.2 s with rsync, so the first version is slower than that and a later one may use rsync). Left to later stories: the container profile (S0002).

## Interface

`factory.domain.settings` (domain): constants `SNAPSHOTS_VARIABLE = "FACTORY_SNAPSHOTS"` and `SNAPSHOT_BASE_VARIABLE = "FACTORY_SNAPSHOT_BASE"`, and the fields `InstanceSettings.snapshots: Literal["zfs", "copy"] = "zfs"` and `snapshot_base: Path | None = None`.

- `read_settings`: `FACTORY_SNAPSHOTS` unset or blank is `zfs`; `zfs` and `copy` are accepted; anything else is `SettingsInvalid(FACTORY_SNAPSHOTS, "is neither zfs nor copy")`.
- `FACTORY_SNAPSHOT_BASE` is read with the optional-path reader: unset or blank is `None`; a relative path is `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "is not an absolute path")`.
- With `copy`: a missing base is `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "missing")` when the boundaries are built (like the dataset today), not when the settings are read; a base that is the workspace, lies inside it, holds it, or is, holds or lies inside the checkout or the state directory is `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "<path> overlaps <workspace|checkout|state>")` when the settings are read. The model validator refuses the same combinations with a `ValidationError`.
- With `zfs`: a base set is `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "is only used with FACTORY_SNAPSHOTS=copy")`; the model validator refuses `snapshots="zfs"` with a `snapshot_base` too, with a `ValidationError`.

`factory.adapters.copy_snapshots` (adapters, new): `class CopySnapshots(Snapshots)` with the constructor `(folder: Path, base: Path)` and the three operations of `FakeSnapshots` today, with these rules:

- `reset` empties `folder` (the folder stays) and copies `base` into it, links as links; `advance` replaces `base` with a copy of `folder`; both raise `SnapshotError(<operation>, <the operating system's message>)` for an `OSError`. `reset` and `changed_paths` raise `SnapshotError(<operation>, "no base at <base>")` without a base, `reset` changing nothing.
- `changed_paths` lists every file and link whose mode, bytes or link target differ, by path, sorted, `added`, `modified` or `deleted`, never a directory; bytes are compared in chunks of at most 1 MiB, so memory use does not grow with the size of a file.

`factory.adapters.fake_snapshots` (adapters): `class FakeSnapshots(CopySnapshots)` with no body of its own beyond its docstring; every test of it passes unchanged.

`factory.application.preflight` (application): `def snapshots_item(workspace: Path, base: Path) -> PreflightItem`, the item `snapshots`: passes when both are directories, with the detail `workspace <w>, base <b>`; fails with `the workspace <w> is not a directory`, `the base <b> does not exist; make it empty with mkdir, the first advance fills it` or, for a base that exists but is not a directory, `the base <b> is not a directory`.

`factory.entry.wiring` (entry): `_container_adapters` builds `CopySnapshots(workspace, base)` for `copy` (and then needs no dataset) and `ZfsSnapshots` as today for `zfs`; `_container_items` gives, for `copy`, `podman`, `snapshots` and `stage-image` and no `zfs` or `dataset` item. `build_boundaries` raises `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "missing")` first for `copy` without a base, then the workspace and image faults as today.

Tests (the tester writes them): `tests/domain/test_settings_snapshots.py`, `tests/adapters/test_copy_snapshots.py` (a real tree in `tmp_path`), `tests/application/test_preflight_snapshots_item.py`, `tests/entry/test_wiring_copy_snapshots.py`. `tests/adapters/test_fake_snapshots.py` passes unchanged.

## Acceptance criteria

1. With `FACTORY_SNAPSHOTS` unset the settings, the boundaries and the preflight items are those of before this story (rows: settings fields, the type of `Boundaries.snapshots`, the item names).
2. `FACTORY_SNAPSHOTS` is read, rows of one parametrized test: unset, blank and `zfs` give `zfs`; `copy` gives `copy`; `ZFS`, `btrfs` and `copy now` are refused as `is neither zfs nor copy`.
3. `FACTORY_SNAPSHOT_BASE` is read, rows of one test: unset and blank give `None`; `/var/base` gives that path; `base` is refused as not absolute; with `copy` and the workspace `/work`, the bases `/work`, `/work/b` and `/` are refused as overlapping the workspace; `/work2` is accepted; with the checkout `/srv/repo`, `/srv/repo` and `/srv` are refused as overlapping it and `/srv/base` is accepted; the same for the state directory; with `zfs` a base is refused as `is only used with FACTORY_SNAPSHOTS=copy`.
4. The model validator of `InstanceSettings`, rows of one parametrized test: with `snapshots="copy"`, a `snapshot_base` inside, equal to and holding each of the workspace, the checkout and the state directory (for the workspace `/work`: `/work/b`, `/work`, `/`) is a `ValidationError`; one base that overlaps none is accepted; `snapshots="zfs"` with a `snapshot_base` is a `ValidationError`.
5. `CopySnapshots` over a real tree: after `advance`, a modified file, an added file and a deleted file, `changed_paths` is those three changes sorted by path; a directory-only change lists nothing; a changed mode is `modified`; a link that now points elsewhere is `modified`; `reset` brings the tree back byte for byte and mode for mode, links as links, and keeps the folder itself.
6. `CopySnapshots` without a base: `reset` and `changed_paths` raise `SnapshotError` whose detail is `no base at <base>` and `reset` leaves the folder as it was; `advance` makes the base.
7. A file of 3 MiB that differs from the base in its last byte is `modified`, and the comparison reads at most 1 MiB at a time (a test that wraps the file reader and checks the largest read).
8. An `OSError` of the copy is a `SnapshotError` naming the operation, rows of one test: `reset` with a base that is a file; `advance` with a base whose parent path is a regular file (`NotADirectoryError`, independent of the user the tests run as), operation name `advance`.
9. `FakeSnapshots` is a `CopySnapshots` and `tests/adapters/test_fake_snapshots.py` is unchanged and green.
10. `snapshots_item`: a workspace and a base that are directories pass with the detail `workspace <w>, base <b>`; a workspace that is a file, a missing workspace, a missing base and a base that is a file each fail with the sentences of the Interface (the base that is a file with `the base <b> is not a directory`).
11. `build_boundaries` with `copy`, a workspace, a base and an image, and no dataset, gives `CopySnapshots` on those paths; without the base it raises `SettingsInvalid` naming `FACTORY_SNAPSHOT_BASE`; `machine_extras` for `copy` holds the items `podman`, `snapshots`, `stage-image` and `agent-run-probe` and none named `zfs` or `dataset`.
12. `build_boundaries` with `copy` and no base raises `SettingsInvalid` naming `FACTORY_SNAPSHOT_BASE`, also when the workspace is missing (one row) and when the stage image is missing (a second row).
13. `make check` stays green.
14. docs: `docs/operator-guide.md`: the two variables in the configuration table, and a subsection *Without ZFS* under the stage environment: the copy adapter, the empty base made once with `mkdir`, the cost (reset about 1.6 s per GiB, both copies in memory in a memory-backed sandbox). `docs/project-guide/stage-environment.md`: *The snapshots* names `CopySnapshots`, and the fake's section says `FakeSnapshots` is its subclass. `docs/decisions.md`: an entry *A snapshot adapter that copies a directory*, from the feature's decisions 1 and 2. `README.md`: none.

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
5. factory: started intake as vm.
6. intake: accepted
   Carried in from journal entry 4 (the human's answers to entry 3), written into the story as their edit, nothing of mine added: (2) new criterion 12 for the `build_boundaries` ordering (no base plus a missing workspace, and plus a missing stage image, both naming `FACTORY_SNAPSHOT_BASE`), "first" kept; `make check` and `docs:` are now 13 and 14. (3) criterion 4 is rows of one test: base inside, equal to and holding the workspace, the checkout and the state directory are each a `ValidationError`, plus one accepted non-overlapping base. (4) the Interface says the model validator also refuses `zfs` with a base, and criterion 4 has that row. (5) the Interface's `snapshots_item` line gains `the base <b> is not a directory`, and criterion 10 gains the file-base row. (6) criterion 8 has rows for `reset` (base is a file) and `advance` (base whose parent is a regular file, `NotADirectoryError`, independent of the user).
   - Interface: concrete modules and signatures (`factory.domain.settings`, `factory.adapters.copy_snapshots.CopySnapshots(folder, base)`, `FakeSnapshots(CopySnapshots)`, `snapshots_item(workspace, base)`, `factory.entry.wiring` functions). Fault sentences are exact.
   - Criteria: each is testable by one parametrized test function. Every Interface rule has both sides: read-settings values and refusals, the overlap refusals and acceptances, the zfs-with-base refusal, no-base errors, the OSError rules for `reset` and `advance`, the 1 MiB chunk limit, the three `snapshots_item` failures. The model-validator rules are covered by criterion 4.
   - Smoke test: both commands are runnable (neither runs pytest), and the `Expect:` lines are checkable against printed output.
   - Architecture: settings in domain, the adapter in adapters, the item in application, the wiring in entry. Layers are respected, no new dependency.
   - Scope: within F0047's S0001 scope, nothing from S0002 onward, and nothing in the feature's "Out of scope". `tests/adapters/test_fake_snapshots.py` stays unchanged, so no other story's test is touched.
7. factory: started tests as vm.
8. tester: Wrote the tests for every acceptance criterion. `make test` fails as expected: all four new modules fail to import because `factory.adapters.copy_snapshots`, `snapshots_item` in `factory.application.preflight`, and `SNAPSHOTS_VARIABLE` / `SNAPSHOT_BASE_VARIABLE` in `factory.domain.settings` do not exist yet. `make lint` is green.

   - criterion 1: tests/entry/test_wiring_copy_snapshots.py::test_without_the_snapshots_setting_the_instance_is_the_zfs_one_of_before (rows: settings-fields, snapshots-type, item-names)
   - criterion 2: tests/domain/test_settings_snapshots.py::test_the_snapshots_setting_is_zfs_or_copy
   - criterion 3: tests/domain/test_settings_snapshots.py::test_the_snapshot_base_is_an_absolute_path_apart_from_the_factory_s_paths
   - criterion 4: tests/domain/test_settings_snapshots.py::test_instance_settings_built_directly_keep_the_snapshot_base_apart
   - criterion 5: tests/adapters/test_copy_snapshots.py::test_changed_paths_lists_the_changed_files_and_links_sorted_by_path and ::test_reset_brings_the_tree_back_byte_for_byte_and_keeps_the_folder
   - criterion 6: tests/adapters/test_copy_snapshots.py::test_without_a_base_reset_and_changed_paths_fail_and_leave_the_folder and ::test_advance_without_a_base_makes_the_base
   - criterion 7: tests/adapters/test_copy_snapshots.py::test_a_large_file_is_compared_in_chunks_of_at_most_a_mebibyte
   - criterion 8: tests/adapters/test_copy_snapshots.py::test_an_operating_system_fault_of_the_copy_is_a_snapshot_error_naming_the_operation
   - criterion 9: tests/adapters/test_copy_snapshots.py::test_the_fake_snapshots_are_copy_snapshots (tests/adapters/test_fake_snapshots.py not touched)
   - criterion 10: tests/application/test_preflight_snapshots_item.py::test_the_snapshots_item_passes_only_when_the_workspace_and_the_base_are_directories
   - criterion 11: tests/entry/test_wiring_copy_snapshots.py::test_a_copy_instance_gets_copy_snapshots_on_its_workspace_and_base, ::test_a_copy_instance_checks_its_snapshots_and_neither_zfs_nor_a_dataset, and the `base` row of ::test_a_copy_instance_without_a_base_names_the_base_first
   - criterion 12: tests/entry/test_wiring_copy_snapshots.py::test_a_copy_instance_without_a_base_names_the_base_first (rows `base-and-workspace`, `base-and-stage-image`)
   - criteria 13, 14: no test (`make check`; docs).

   Files created:
   - tests/domain/test_settings_snapshots.py
   - tests/adapters/test_copy_snapshots.py
   - tests/application/test_preflight_snapshots_item.py
   - tests/entry/test_wiring_copy_snapshots.py

   Modules the test run could not import:
   - `factory.adapters.copy_snapshots`
   - `factory.application.preflight.snapshots_item`
   - `factory.domain.settings.SNAPSHOTS_VARIABLE` and `SNAPSHOT_BASE_VARIABLE`

   Notes for the coder:
   - **Overlap message:** the Interface's fault `<path> overlaps <workspace|checkout|state>` is tested exactly. `<path>` is the base, followed by the literal word, for example `/work/b overlaps workspace`. A base of `/` overlaps all three paths and is expected to name `workspace`, which follows the Interface's order: workspace, then checkout, then state.
   - **Fixed paths in the settings tests:** the workspace is `/work`, the checkout `FACTORY_CHECKOUT=/srv/repo` and the state directory `FACTORY_STATE=/opt/state`. The checkout has to be set because the default `/work/checkout` would lie inside the workspace `/work`.
   - **How criterion 7 counts reads:** the test wraps `builtins.open`, `io.open`, `os.open` and `os.read` while `changed_paths` runs. It records the bytes each read returns for files under `tmp_path`, and asserts that at least one read was seen and none was larger than 1 MiB.
   - **Criterion 8 assertions:** only the operation name is checked, plus a non-empty detail.
   - **What criterion 11 checks:** `machine_extras` must hold `podman`, `snapshots`, `stage-image` and `agent-run-probe`, and must hold neither `zfs` nor `dataset`. The order is not checked, because the criterion does not state one.

   Rejected: putting the passing and failing rows of `snapshots_item` in separate test functions; they are rows of one parametrized test, as the rules ask.

   Nothing is open.

   `lint`: lint: green (0.2 s)
   `test`: ERROR tests/entry/test_wiring_copy_snapshots.py - ImportError while importing test module '/work/checkout/tests/entry/test_wiring_copy_snapshots.py'.
