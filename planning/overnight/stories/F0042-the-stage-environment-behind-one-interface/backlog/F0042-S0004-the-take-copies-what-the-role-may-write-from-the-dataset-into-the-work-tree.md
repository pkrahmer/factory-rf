# The take copies what the role may write from the dataset into the work tree

## Description

In v1.2 the agent works on the dataset and may write anywhere it reaches; nothing of that survives but what the factory takes (`planning/v1.2-plan.md`, "The cycle of a stage", step 6). The take is the write-path refusal rule applied the other way round: for every changed path under the dataset's `checkout/`, the path the role may write is copied from the dataset into the factory's own work tree on the host, a deletion mirrored and the executable bit kept; a path the role may not write (the refusal of `factory.domain.write_paths`, the protected paths, and the undo's second rule about every other file directly in an `in-progress/` folder) is left in the dataset and named, as the undo names it today. Paths the checkout's `.gitignore` ignores (`.venv/...`, `.reports/...`) are asked of the factory's own repository on the host with `git check-ignore`, never of the dataset's git, and are neither taken nor named; nor is anything with a `.git` component, nor anything outside `checkout/` (the agent's `home/`). Then the work item's state and journal are put back from the stage-start commit with `restore_state_and_journal`, exactly as the undo does. This story adds `TakeService` and `TakeReport` in `factory.application.take`, the shared copying of changed paths between two trees that S0009 (the check container) uses too, and the git operation `ignored`. The report has one list, `left`, so that S0005 can turn the undo's report into the same type and `AfterAgent` reads one type. Nothing calls the service yet: S0007 (the container environment) does. What stays: the undo and its tests, untouched.

## Interface

`factory.application.git` (`application`), the `Git` interface gains one operation, its twenty-sixth; `factory.adapters.git_cli.GitCli` implements it:

```python
    @abstractmethod
    def ignored(self, paths: Sequence[str]) -> list[str]:
        """Those of `paths` that the checkout's ignore rules ignore, in the order given.

        A tracked path is never ignored. `[]` for no paths, without running git. A path that
        is absolute or holds a `..` segment raises `ValueError` before git runs.
        """
```

- `GitCli.ignored` runs `git check-ignore -z -- <paths...>` in the checkout: exit status 0 gives the NUL-separated paths it printed, exit status 1 gives `[]`, any other status is `GitError`. The tests `tests/application/test_git_interface.py` and `tests/application/test_interfaces.py` count twenty-six operations (decision 18 d of `feature.md`).

`factory.application.take` (`application`), new:

```python
class TakeReport(BaseModel):
    """What a take left in the dataset, and whether the work item's state and journal were put back."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    left: list[str]
    restored_work_item: bool


def copy_changed(source: Path, target: Path, changed: Sequence[ChangedPath]) -> None:
    """Mirror each of `changed` from the tree at `source` into the tree at `target`."""


class TakeService:
    """Takes from the dataset into the work tree what the stage's role may write; the rest stays."""

    def __init__(self, boundaries: Boundaries, mount_point: Path) -> None: ...

    def take(
        self, stage_start: StageStart, work_item_path: str, changed_paths: Sequence[ChangedPath]
    ) -> TakeReport: ...
```

- `copy_changed`: for an `added` or `modified` path, the entry at `source / path` replaces the one at `target / path`: a regular file by its bytes and its mode (so an executable bit is kept), a symbolic link by a link with the same target text (never followed), the parent folders made as needed; for a `deleted` path, the entry at `target / path` is removed when it exists (a missing one is no fault). A path that is absolute or holds a `..` segment raises `ValueError` before anything is copied. It is the one copying of this feature: the take uses it, and S0009's check container uses it the other way round.
- `take(stage_start, work_item_path, changed_paths)`, in this order:
  1. The baseline: the work item at `stage_start.commit` through `boundaries.git.show_file` and `work_item_reader.parse`; absent or unreadable is `WorkItemFormatError` naming `work_item_path`, before anything changes, as in the undo.
  2. The write paths: `WritePathService(boundaries).at(stage_start, work_item_path)`.
  3. The candidates: of `changed_paths`, those whose `path` starts with `checkout/`, with that prefix removed; a path with a segment `.git` is dropped; of the rest, those `boundaries.git.ignored(...)` names are dropped. A path under `home/` or anywhere else is dropped. Dropped paths are neither taken nor listed.
  4. The refused: a candidate with `refusal(path, settings)` not `None`, or that is not `work_item_path` and lies directly in an `in-progress/` folder of a feature (`factory/features/<feature>/in-progress/<file>`, the undo's second rule, shared with the undo and not copied), goes to `left` and is not copied; the dataset is never written.
  5. The taken: every other candidate is copied with `copy_changed(mount_point / "checkout", boundaries.checkout, ...)`.
  6. The work item: its state and journal are put back from the baseline with `restore_state_and_journal`, the agent's edits to its sections kept; a work item that is deleted or whose front matter cannot be read comes back whole from the stage-start commit (`revert_paths`), and `restored_work_item` is true in both cases; it is false when nothing changed. A work item the role may not write is refused like any path (listed in `left`, not copied), and then it is not restored (`restored_work_item` false), as in the undo. This restore is the undo's, shared and not copied.
  7. `TakeReport(left=<sorted, no repeats>, restored_work_item=...)`.
- The service writes no commit, runs no git command on the dataset and never writes under `mount_point`.

Tests (the tester writes them): `tests/application/test_take.py` and `tests/application/test_take_edges.py`, built like `tests/application/test_undo.py` on `tests/undo_support.py` (`start_stage` for the claim and the stage-start commit), with a dataset folder in `tmp_path` whose `checkout/` the test fills as the agent would have, and the changed paths given by hand (`FakeSnapshots` of S0001 may compute them); `tests/adapters/test_git_cli_ignored.py` for the git operation, on the real local clone of the fixtures with a `.gitignore` pushed to `main`.

## Acceptance criteria

1. `GitCli.ignored` (rows of one parametrized test, the checkout's `.gitignore` holding `.venv/` and `*.log`): `[".venv/bin/python", "src/a.py", "run.log"]` gives `[".venv/bin/python", "run.log"]` in that order; `["src/a.py"]` gives `[]`; `[]` gives `[]` and runs no git (the recorded git calls, through a `GitOptions.executable` stand-in that records, show none); a tracked file that matches a pattern (`docs/kept.log`, committed) is not in the result; `["/abs"]` and `["a/../b"]` raise `ValueError`.
2. `copy_changed` (rows of one parametrized test): an `added` regular file arrives with the same bytes and mode (`0o755` stays `0o755`, `0o644` stays `0o644`), its parent folders made; a `modified` file replaces the target's bytes and mode; a `deleted` path removes the target's file, and a `deleted` path missing on the target raises nothing; an `added` symbolic link arrives as a link with the same target text, and the file it points to is not read; `/abs` and `a/../b` raise `ValueError` before anything is copied (the target tree is unchanged).
3. A changed path under `checkout/` inside the write paths (`checkout/src/new.py` added, `checkout/src/kept.py` modified, `checkout/src/old.py` deleted, role write paths `["src/*", "{work_item}"]`) is taken: after `take`, the host's `src/new.py` and `src/kept.py` hold the dataset's bytes, `src/old.py` is gone, and `left` is `[]`.
4. A changed path outside the write paths (`checkout/docs/guide.md` modified) is left: the host's `docs/guide.md` keeps its bytes, the dataset's `checkout/docs/guide.md` keeps the agent's bytes, and `left` is `["docs/guide.md"]`. A protected path inside a write path that matches it (write paths `["*"]`, `checkout/pyproject.toml` added and `checkout/factory/story-form.md` modified) is left too: `left` is `["factory/story-form.md", "pyproject.toml"]` and neither reaches the host (rows of one parametrized test with criterion 3's row as the taken side).
5. The undo's second rule: with write paths `["*"]`, a second work item `checkout/factory/features/F0001-example/in-progress/F0001-S0002-second.md` modified, the own cost record `...-S0001-first.costs.jsonl` added, `.../in-progress/notes.txt` added and `.../in-progress/sub/x` added are judged as `left` `["factory/features/F0001-example/in-progress/F0001-S0001-first.costs.jsonl", "factory/features/F0001-example/in-progress/F0001-S0002-second.md", "factory/features/F0001-example/in-progress/notes.txt"]`, while `.../in-progress/sub/x` is taken (rows of one parametrized test).
6. Dropped paths (rows of one parametrized test, each neither on the host afterwards nor in `left`): `checkout/.venv/bin/python` added when `.gitignore` holds `.venv/`; `checkout/.git/config` modified; `checkout/src/.git/HEAD` added; `home/.claude.json` added; `caches/uv/x` added; `checkout` itself is never among the changed paths (the snapshots list no directory) and a changed path exactly `checkout` would be dropped too.
7. The work item (rows of one parametrized test, the own work item in the write paths): the agent changed a section and the state (`stage: done` in the front matter) on the dataset's copy: after `take`, the host's work item has the agent's section text, the baseline's state and journal, and `restored_work_item` is true; the agent changed nothing of state or journal: `restored_work_item` is false; the agent deleted the work item (`deleted`): it is back whole from the stage-start commit, `restored_work_item` true, not in `left`; the agent broke its front matter: back whole, `restored_work_item` true; the role may not write the work item (write paths `["src/*"]`, the work item modified): `left` holds its path, the host's file is unchanged, `restored_work_item` false.
8. A work item absent at the stage-start commit raises `WorkItemFormatError` naming `work_item_path`, and nothing on the host changed (a changed `checkout/src/new.py` did not arrive).
9. `left` is sorted and holds each path once when the same path is given twice among `changed_paths`; the report is frozen and refuses an unknown field (`tests/test_model_configuration.py` covers the model).
10. `make check` stays green.
11. docs: `docs/project-guide/stage-environment.md` gains the section *The take*: the seven steps in order, what is dropped, what is left, what is taken, the work item's restore shared with the undo, `copy_changed` and its two users, the errors, the tests; `docs/project-guide/git-and-hosting.md`, *The git wrapper*: the table row for `ignored` and the count twenty-six; `docs/project-guide/README.md`, *The files*, names `factory.application.take` for the stage-environment file; `docs/project-guide/write-guard.md`, *The undo*: one sentence that the take (`stage-environment.md`) applies the same two rules the other way round, in the container environment. `docs/decisions.md`: none in this story.

## Smoke test

```bash
uv run pytest tests/application/test_take.py tests/application/test_take_edges.py tests/adapters/test_git_cli_ignored.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run python - "$d" <<'EOF'
import os
import sys
from pathlib import Path

from factory.application.take import copy_changed
from factory.domain.git import ChangedPath

d = Path(sys.argv[1])
source, target = d / "source", d / "target"
(source / "src").mkdir(parents=True)
(target / "src").mkdir(parents=True)
(source / "src" / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
(source / "src" / "run.sh").chmod(0o755)
(source / "src" / "kept.py").write_text("new\n", encoding="utf-8")
(target / "src" / "kept.py").write_text("old\n", encoding="utf-8")
(target / "src" / "old.py").write_text("gone\n", encoding="utf-8")
os.symlink("kept.py", source / "src" / "link")
copy_changed(source, target, [ChangedPath(path="src/run.sh", change="added"), ChangedPath(path="src/kept.py", change="modified"), ChangedPath(path="src/old.py", change="deleted"), ChangedPath(path="src/link", change="added"), ChangedPath(path="src/never.py", change="deleted")])
print(oct((target / "src" / "run.sh").stat().st_mode & 0o777), (target / "src" / "kept.py").read_text(encoding="utf-8").strip(), (target / "src" / "old.py").exists(), os.readlink(target / "src" / "link"))
try:
    copy_changed(source, target, [ChangedPath(path="src/../x", change="added")])
except ValueError as error:
    print("refused", "src/../x" in str(error))
EOF
```
Expect: two lines, `0o755 new False kept.py` and `refused True`

## Journal
