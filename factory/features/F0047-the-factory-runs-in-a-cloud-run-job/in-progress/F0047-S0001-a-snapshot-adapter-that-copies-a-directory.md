---
stage: smoke-test
blocked: null
round: 1
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
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-31T15:50:34.517996Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-31T15:58:54.264002Z'
  stage: doing
  run: af62d7cb8c814acf9587af29c164a02c
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-31T15:59:14.800471Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-31T16:00:22.681633Z'
  stage: review
  run: 94dab09fe25940f7851e55e1d60b9c06
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-31T16:00:43.336177Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-31T16:01:02.650915Z'
  stage: doing
  run: 9946dd699a604a778641d23822a28aa8
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-31T16:01:25.009423Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-31T16:07:42.737131Z'
  stage: tests
  run: fe75fe6535cf40d2a4ec84e57c297e63
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-31T16:08:03.006206Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-31T16:14:21.587839Z'
  stage: doing
  run: 79487c6115304c4d9e2e136ffa98b6ff
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-31T16:14:43.777493Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-31T16:16:07.814522Z'
  stage: review
  run: 037b9d18bfe347b993f8a15fef7be69a
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-31T16:16:28.530925Z'
  stage: docs
- number: 22
  speaker: documenter
  kind: result
  at: '2026-10-31T16:17:50.250025Z'
  stage: docs
  run: 14a4f374b58b470fb8006516ee71ca4d
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
13. An `OSError` of `reset`'s copy that comes after the base is found is a `SnapshotError` naming `reset` whose detail is the operating system's message, not `no base at <base>`: a base that is a directory and a folder that is a regular file (`NotADirectoryError`, independent of the user the tests run as).
14. `build_boundaries` with `copy` and a base keeps today's faults after it, rows of one test: without the workspace it raises `SettingsInvalid` naming `FACTORY_WORKSPACE`; with the workspace and without the stage image, `SettingsInvalid` naming `FACTORY_STAGE_IMAGE`.
15. `make check` stays green.
16. docs: `docs/operator-guide.md`: the two variables in the configuration table, and a subsection *Without ZFS* under the stage environment: the copy adapter, the empty base made once with `mkdir`, the cost (reset about 1.6 s per GiB, both copies in memory in a memory-backed sandbox). `docs/project-guide/stage-environment.md`: *The snapshots* names `CopySnapshots`, and the fake's section says `FakeSnapshots` is its subclass. `docs/decisions.md`: an entry *A snapshot adapter that copies a directory*, from the feature's decisions 1 and 2. `README.md`: none.

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
9. factory: started doing as vm.
10. coder: Implemented the copy snapshots, the two settings, the `snapshots` preflight item and the wiring. `make check` is green (test: 167.1 s, then `check: green`). The four new test modules and `tests/adapters/test_fake_snapshots.py` pass, and I edited no test.

    What I built:
    - `src/factory/adapters/copy_snapshots.py` (new): `CopySnapshots(folder, base)`. It has the fake's three operations. `reset` and `advance` turn an `OSError` into `SnapshotError(<operation>, str(error))` through `_as_snapshot_error`. `reset` checks for the base before it empties the folder, so without a base the folder is left as it was. `changed_paths` first compares each entry's mode and size, or a link's mode and target. Only a file whose mode and size match is then read, in 1 MiB chunks (`_same_file_bytes`), so no file is ever read whole.
    - `src/factory/adapters/fake_snapshots.py`: `FakeSnapshots(CopySnapshots)`. Only its module docstring and class docstring are left.
    - `src/factory/domain/settings.py`:
      - New constants `SNAPSHOTS_VARIABLE` and `SNAPSHOT_BASE_VARIABLE`, the type `SnapshotsName`, and the fields `snapshots` (default `zfs`) and `snapshot_base`.
      - `_snapshots` reads the setting the same way `_agent_runtime` does. The base is read with `_optional_absolute_path`.
      - One public rule, `snapshot_base_fault`, serves both `read_settings` (as `SettingsInvalid`) and a new model validator (as `ValidationError`). It refuses a base under `zfs`, and a base that is, lies inside or holds the workspace, the checkout or the state directory, checked in that order. `snapshot_base` also joined the `_absolute` field validator.
    - `src/factory/application/preflight.py`: `snapshots_item(workspace, base)` with the Interface's sentences.
    - `src/factory/entry/wiring.py`: `_container_adapters` now picks `_copy_snapshots` or `_zfs_snapshots`. Each checks its own source first (the base or the dataset), then the workspace through `_required_workspace`. The stage image is checked after that.
      - Each returns a `_SnapshotAdapters` that holds the `Snapshots` and its preflight items: copy gives `snapshots`; zfs gives `zfs` and `dataset`, as before. `_container_items` places these between `podman` and `stage-image`.
      - `PodmanRuns` now takes the workspace from the snapshots' `mount_point`.

    Main choice: each kind of snapshots brings its own preflight items through `_SnapshotAdapters`. I rejected keeping `_ContainerAdapters` typed to `ZfsSnapshots` with a nullable `dataset` and branching on `settings.snapshots` again in `_container_items`. That puts the copy/zfs decision in two places and needs a narrowing of the dataset that the type cannot show.

    Second choice: compare mode and size before reading any bytes, so a changed size is found without reading the file. I rejected `filecmp.cmp`: its cache is keyed on size and mtime, and it could miss a same-size rewrite within the same mtime.

    Refactor pass: I read the diff and found nothing to change.

    The journal did not change the meaning of the task beyond what intake already wrote into the Description; I rewrote nothing.

    Noticed, not touched:
    - `changed_paths` does not turn an `OSError` into a `SnapshotError`, because the Interface names only `reset` and `advance`.
    - The `reset-on-a-file` row of the OS-fault test is caught by the no-base check, `no base at <base>`, not by an `OSError`. The test checks only the operation name and that the detail is not empty, so it passes either way.
    - I did not run `make duplicates`.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 41 known, 0 gone
11. factory: started review as vm.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (5 src files, 4 new test modules) against the work item. Group 1 (acceptance criteria) fails, so I stopped there. Both gaps are against the story, not the tester. Neither needs a change under `src/`, so I added a criterion for each before the two closing criteria, which are now 15 and 16.

    1. criterion 13 added: it needs its test. `tests/adapters/test_copy_snapshots.py::test_an_operating_system_fault_of_the_copy_is_a_snapshot_error_naming_the_operation`, row `reset-on-a-file`: the base that criterion 8 names (a file) is stopped by `CopySnapshots._require_base` (`src/factory/adapters/copy_snapshots.py:57`) with `no base at <base>`. So `_as_snapshot_error("reset", ...)` (`copy_snapshots.py:35`) is never reached, and the Interface's rule for `reset` (an `OSError` becomes `SnapshotError("reset", <the OS message>)`) has no test. The coder's entry 10 says the same. Fix: the tester adds the row from criterion 13 (the base is a directory and the folder is a regular file, so `_clear` raises `NotADirectoryError`) and asserts that the detail is not `no base at <base>`.
    2. criterion 14 added: it needs its test. The Interface says that with `copy`, `build_boundaries` raises the missing base first, "then the workspace and image faults as today". The new path `_copy_snapshots` → `_required_workspace` (`src/factory/entry/wiring.py:337-343`) and the stage-image check after it (`wiring.py:327`) have no test for a `copy` instance that has a base: `tests/entry/test_wiring_copy_snapshots.py` only tests a missing base. Fix: the tester adds one parametrized test to `tests/entry/test_wiring_copy_snapshots.py` with two rows, no workspace naming `FACTORY_WORKSPACE` and no stage image naming `FACTORY_STAGE_IMAGE`.

    The other criteria (1–7 and 9–12) each have a matching test, and the factory's `make check` after the coder was green (entry 10). I did not judge groups 2–5 because group 1 failed.

    Earlier tests: none. The diff adds only new test files (all status `A`), and `tests/adapters/test_fake_snapshots.py` is unchanged.
13. factory: started doing as vm.
14. coder: Round 1. The reviewer added two criteria. Each needs only its test, so I changed no code and no test, and I am sending the work item to the tester.

    - Criterion 13: a new row in `tests/adapters/test_copy_snapshots.py::test_an_operating_system_fault_of_the_copy_is_a_snapshot_error_naming_the_operation`. The base is a directory and the folder is a regular file. Expected: a `SnapshotError` naming `reset`, whose detail is not `no base at <base>`. I read the code without running it, and it should already pass. `CopySnapshots.reset` passes `_require_base` (`src/factory/adapters/copy_snapshots.py:56`). Then `_clear` calls `folder.iterdir()` on the file (`copy_snapshots.py:84`), inside `_as_snapshot_error("reset", ...)`, so the `NotADirectoryError` comes out as `SnapshotError("reset", <the operating system's message>)`.
    - Criterion 14: a new parametrized test in `tests/entry/test_wiring_copy_snapshots.py` for `copy` with a base. Row one has no workspace and expects `SettingsInvalid` naming `FACTORY_WORKSPACE`. Row two has a workspace but no stage image and expects `SettingsInvalid` naming `FACTORY_STAGE_IMAGE`. This should also pass already: `_copy_snapshots` checks the base and then calls `_required_workspace` (`src/factory/entry/wiring.py:337-343`), and `_container_adapters` checks the stage image after that (`wiring.py:327`).

    Main choice: end with `tests` and change no code, as the stage asks when a criterion needs only its test. I rejected adjusting `src/` ahead of the tests, because nothing in the findings calls for a code change.

    I did not run `make check` in this round because nothing changed.

    The journal changed nothing in the Description beyond the reviewer's two criteria, which are already in it.

    Noticed, not touched: as entry 10 says, `changed_paths` does not turn an `OSError` into a `SnapshotError`. The Interface names only `reset` and `advance`.
15. factory: started tests as vm.
16. tester: Round 1. I wrote the tests for the two criteria the reviewer added (13 and 14), which the coder's entry 14 handed to me. Each needed a new test and no existing test had to change. `make test` is green, because the code was already in place as the coder expected. `make lint` is green.

    - criterion 13: tests/adapters/test_copy_snapshots.py::test_an_operating_system_fault_after_the_base_is_found_is_a_reset_error_with_its_message
    - criterion 14: tests/entry/test_wiring_copy_snapshots.py::test_a_copy_instance_with_a_base_keeps_the_workspace_and_image_faults (rows `workspace`, `stage-image`)

    What the criterion 13 test does: the base is an existing directory and the folder is a regular file. It asserts three things about the result: the `SnapshotError` names `reset`, its detail is not `no base at <base>`, and the detail contains `os.strerror(errno.ENOTDIR)`, which is the operating system's message.

    Rejected: adding the criterion 13 case as a row of `test_an_operating_system_fault_of_the_copy_is_a_snapshot_error_naming_the_operation`, which is what the reviewer and the coder suggested. That test's `reset-on-a-file` row ends with `no base at <base>`, so the new row's assertions would not hold for it. A row would have needed a per-row conditional, so I wrote a test function of its own. That existing test is unchanged.

    What criterion 14 checks: the base stays set, one field is removed, and the test checks only `SettingsInvalid.variable`.

    Files changed: tests/adapters/test_copy_snapshots.py and tests/entry/test_wiring_copy_snapshots.py. Both were written by this story's tests stage. No new files.

    Modules the test run could not import: none.

    Nothing is open.

    `lint`: lint: green (0.2 s)
    `test`: test: green (167.0 s)
17. factory: started doing as vm.
18. coder: Round 1, back from the tester. The two criteria the reviewer added (13 and 14) now have tests, and both pass against the code from entry 10 without any change. I changed no code and no test in this round.

    - Criterion 13: `tests/adapters/test_copy_snapshots.py::test_an_operating_system_fault_after_the_base_is_found_is_a_reset_error_with_its_message` passes. `CopySnapshots.reset` gets past `_require_base`. Then `_clear` fails on the folder, which is a regular file, inside `_as_snapshot_error("reset", ...)` (`src/factory/adapters/copy_snapshots.py`). The error's detail is the operating system's message.
    - Criterion 14: `tests/entry/test_wiring_copy_snapshots.py::test_a_copy_instance_with_a_base_keeps_the_workspace_and_image_faults` passes with both rows. `_copy_snapshots` checks the base and then calls `_required_workspace`. `_container_adapters` checks the stage image after that (`src/factory/entry/wiring.py`).

    What I built: the paths are unchanged from entry 10: `src/factory/adapters/copy_snapshots.py`, `src/factory/adapters/fake_snapshots.py`, `src/factory/domain/settings.py`, `src/factory/application/preflight.py` and `src/factory/entry/wiring.py`.

    Main choice: leave `src/` as it is. The findings asked only for tests, and those tests pass. I rejected changing the code to make the `reset`-with-a-file-base row of criterion 8 reach the `OSError` path. The Interface says a missing base, which a file base is, gives `no base at <base>`, and the tester gave criterion 13 its own test.

    Refactor pass: nothing changed since entry 10's refactor pass, so there was nothing new to refactor.

    The journal changed nothing in the Description beyond the reviewer's criteria 13 and 14, which are already in it.

    Noticed, not touched: `changed_paths` still does not turn an `OSError` into a `SnapshotError`, because the Interface names only `reset` and `advance`.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 41 known, 0 gone
19. factory: started review as vm.
20. reviewer: Round 1. I reviewed `git diff main...HEAD -- . ':!factory'`: 5 files under `src/` and 4 new test modules, checked against the work item. I read the code and the tests rather than the earlier entries.

    no findings

    - Group 1 (acceptance criteria): every criterion from 1 to 14 has a test that checks what the criterion names. The rows of each rule are rows of one parametrized test. Criterion 13's test reaches `_as_snapshot_error("reset", ...)` through `_clear` on a folder that is a file, and checks that the detail is the operating system's message. Criterion 14 covers the faults that follow once a base is set. The `read_settings` test has no rows for a base inside the checkout or inside the state directory, but the model validator test covers those cases, and both paths go through the same `snapshot_base_fault` (`src/factory/domain/settings.py`). I did not count it as a gap. The factory's `make check` after the coder was green (entries 10 and 18). `make duplicates` reported 0 new.
    - Group 2 (architecture): the layers hold. The settings rule is in domain, `CopySnapshots` is in adapters, `snapshots_item` is in application and the wiring is in entry. `CopySnapshots` derives from `Snapshots`, and `FakeSnapshots(CopySnapshots)` has nothing but its docstring. `snapshots_item` is the only code in `factory.application` that stats the file system (`Path.is_dir`/`exists`). The Interface sets that signature, and no rule forbids it, so it is not a finding.
    - Group 3 (security): no markers, no secrets, no commands built from strings. The base is checked when the settings are read and again by the model validator.
    - Group 4 (quality): the names, docstrings and comments say why. There is no dead code. `_snapshots` follows the pattern of `_agent_runtime` but reads a different variable, so I did not count it as a copied helper.
    - Group 5 (hygiene): the Description matches what was built. The journal explains the main choice (`_SnapshotAdapters` carries each kind's preflight items) and what was rejected. Docs criterion 16 still describes what the reader needs.

    Earlier tests: none. Every test file in the diff is new (status `A`), and `tests/adapters/test_fake_snapshots.py` is unchanged.

    Notes:
    1. `tests/adapters/test_copy_snapshots.py` `_tree` and `_reset`: copies of the helpers of the same names in `tests/adapters/test_fake_snapshots.py`. Criterion 9 keeps that file unchanged, so the copy was the choice open to the tester.
    2. `tests/adapters/test_copy_snapshots.py` `_reset_on` and `_advance_on`: `_reset_on` is the same as `_reset` in the same module. One of them would do.
    3. Criterion 8's `reset-on-a-file` row stops at `no base at <base>`, not at an `OSError`. The real `OSError` path of `reset` is tested by criterion 13.
21. factory: started docs as vm.
22. documenter: Round 1, docs. I wrote the documentation the docs criterion (16) asks for. I changed only documents, so I did not run `make check`; the factory's checks decide. `make documents` passes ("documents ok"). I ran the story's first smoke-test script: it prints `[('a.txt', 'modified'), ('n.txt', 'added')]` and `['a.txt'] one`, as expected.

    Files changed:
    - `docs/operator-guide.md`: the rows `FACTORY_SNAPSHOTS` and `FACTORY_SNAPSHOT_BASE` in the configuration table, with the refusals the Interface gives. A new subsection *Without ZFS* before *The stage image*. It covers the copy adapter, the empty base made once with `mkdir -p` and the cost (reset about 1.6 s per GiB, both copies in memory in a memory-backed sandbox). A new `snapshots` row in *The preflight's items*, and the extras list now says it replaces `zfs` and `dataset` under `copy`.
    - `docs/project-guide/stage-environment.md`:
      - *The snapshots* names the two real implementations.
      - A new section *The copy snapshots* describes `CopySnapshots`: operations, the 1 MiB chunks, the errors, and no base.
      - *The fakes* now says `FakeSnapshots` is its subclass with no code of its own, and lists the tests.
      - In *The settings and the wiring*: the two settings rows, `snapshot_base_fault`, the order of the missing-setting faults and the `CopySnapshots` wiring. In *The preflight*: the `copy` item list and the `snapshots` item.
      - The module list at the top names `factory.adapters.copy_snapshots`.
    - `docs/decisions.md`: a new entry *A snapshot adapter that copies a directory*. I could not read the feature's `feature.md`, so I wrote it from the story's Description and Interface and the journal.
    - `README.md`: unchanged, as criterion 16 says.

    Cross-read and found current against the diff: `docs/project-guide/README.md` (index). The rest of `stage-environment.md` and the remaining stage-environment, preflight and settings text in `docs/operator-guide.md`. I did not run the second smoke-test command (the settings read).

    Not documented: the new `Boundaries.snapshots` wiring helpers (`_SnapshotAdapters`, `_required_workspace`) are private, so I left them out.

    No findings for the coder. The code matches the Interface. Two things I noticed and did not touch:
    - `changed_paths` does not turn an `OSError` into a `SnapshotError`. The Interface names only `reset` and `advance`, and I wrote the docs to say so.
    - `docs/operator-guide.md` line 91 still says an instance needs `FACTORY_DATASET` and the missing-variable order is "dataset, workspace, image". That is true for `zfs` only. I did not rewrite that paragraph. If you want it to mention `copy`, it is a small follow-up.

    `check`: check: green (not run again: passed on tree 2d71a41c35f1 at 2026-10-31T16:11:22Z)
    `secrets`: secrets: green (2.3 s)
    `documents`: documents ok
