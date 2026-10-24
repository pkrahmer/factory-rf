---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 410
comments_read: [6384920747]
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-24T13:42:27.152958Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T13:40:20.769216Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T13:40:20.774803Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-24T13:40:43.860909Z'
  stage: intake
  run: a26bd2b1ba2c4990be6609f0e77301e8
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-24T13:41:28.362261Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-24T13:41:47.117118Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-24T13:42:06.905169Z'
  stage: intake
  run: 86bc64a38ea744aab677dee12c357483
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-24T13:42:27.152958Z'
  stage: tests
---

# The take copies what the role may write from the dataset into the work tree

## Description

In v1.2 the agent works on the dataset and may write anywhere it reaches; nothing of that survives but what the factory takes (`planning/v1.2-plan.md`, "The cycle of a stage", step 6). The take is the write-path refusal rule applied the other way round: for every changed path under the dataset's `checkout/`, the path the role may write is copied from the dataset into the factory's own work tree on the host, a deletion mirrored and the executable bit kept; a path the role may not write (the refusal of `factory.domain.write_paths`, the protected paths, and the undo's second rule about every other file directly in an `in-progress/` folder) is left in the dataset and named, as the undo names it today. Paths the checkout's `.gitignore` ignores (`.venv/...`, `.reports/...`) are asked of the factory's own repository on the host with `git check-ignore`, never of the dataset's git, and are neither taken nor named; nor is anything with a `.git` component, nor anything outside `checkout/` (the agent's `home/`). Then the work item's state and journal are put back from the stage-start commit with `restore_state_and_journal`, exactly as the undo does. This story adds `TakeService` and `TakeReport` in `factory.application.take`, the shared copying of changed paths between two trees that S0009 (the check container) uses too, and the git operation `ignored`. The report has one list, `left`, so that S0005 can turn the undo's report into the same type and `AfterAgent` reads one type. Nothing calls the service yet: S0007 (the container environment) does. What stays: the undo's behaviour and `tests/application/test_undo.py`, untouched; `factory.application.undo` only makes public the three helpers the take shares (the Interface names them).

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

- `GitCli.ignored` checks every path with `check_repository_path` of `factory.domain.git` (as `revert_paths` does) and then runs `git check-ignore --verbose --non-matching -- <paths...>` in the checkout, in groups of at most `IGNORE_GROUP` (1,000) paths, one git call per group, the answers joined in the order given. (`-z` is refused by git without `--stdin`, which `run_process` does not feed; the argument form prints exactly one line per path, in the paths' order, a control character or a quote in a path escaped into that one line.) A line is `<source>:<line>:<pattern><TAB><path>`, or `::<TAB><path>` for a path no rule matches and for a tracked path; the path is ignored exactly when the text before the tab is not `::` and its pattern, the text after the second `:`, does not start with `!` (a negation). Exit status 0 and 1 are both answers read from the lines; any other status, and a call that printed fewer or more lines than it was given paths, is `GitError`. The tests `tests/application/test_git_interface.py` and `tests/application/test_interfaces.py` count twenty-six operations (decision 18 d of `feature.md`).

`factory.application.take` (`application`), new:

```python
class TakeReport(BaseModel):
    """What a take left in the dataset, and whether the work item's state and journal came back."""

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

- `copy_changed`: for an `added` or `modified` path, the entry at `target / path` is removed first when there is one (a link as the link, a folder with what it holds) and the entry at `source / path` is then placed, so nothing is ever written through a link that stood at the target: a regular file by its bytes and its mode (so an executable bit is kept), a symbolic link by a link with the same target text (never followed), the parent folders made as needed; for a `deleted` path, the entry at `target / path` is removed when there is one, a link as the link and its target untouched (a missing one, a dangling link included, is no fault). Every path is checked with `check_repository_path` of `factory.domain.git` before anything is copied: an absolute path or one with a `..` segment raises its `ValueError`, whose text names the path. It is the one copying of this feature: the take uses it, and S0009's check container uses it the other way round.
- `take(stage_start, work_item_path, changed_paths)`, in this order:
  1. The baseline: the work item at `stage_start.commit` through `boundaries.git.show_file` and `work_item_reader.parse`; absent or unreadable is `WorkItemFormatError` naming `work_item_path`, before anything changes, as in the undo.
  2. The write paths: `WritePathService(boundaries).at(stage_start, work_item_path)`.
  3. The candidates: of `changed_paths`, those whose `path` starts with `checkout/`, with that prefix removed; a path with a segment `.git` is dropped; of the rest, those `boundaries.git.ignored(...)` names are dropped. A path under `home/` or anywhere else is dropped. Dropped paths are neither taken nor listed.
  4. The refused: a candidate with `refusal(path, settings)` not `None`, or that is not `work_item_path` and lies directly in an `in-progress/` folder of a feature (`factory/features/<feature>/in-progress/<file>`, the undo's second rule, shared with the undo and not copied), goes to `left` and is not copied; the dataset is never written.
  5. The taken: every other candidate is copied with `copy_changed(mount_point / "checkout", boundaries.checkout, ...)`.
  6. The work item: its state and journal are put back from the baseline with `restore_state_and_journal`, the agent's edits to its sections kept; a work item that is deleted or whose front matter cannot be read comes back whole from the stage-start commit (`revert_paths`), and `restored_work_item` is true in both cases; it is false when nothing changed. A work item the role may not write is refused like any path (listed in `left`, not copied), and then it is not restored (`restored_work_item` false), as in the undo. This restore is the undo's, shared and not copied.
  7. `TakeReport(left=<sorted, no repeats>, restored_work_item=...)`.
- The service writes no commit, runs no git command on the dataset and never writes under `mount_point`.

Tests (the tester writes them): `tests/application/test_take.py` and `tests/application/test_take_edges.py`, built like `tests/application/test_undo.py` on `tests/undo_support.py` (`start_stage` for the claim and the stage-start commit), with a dataset folder in `tmp_path` whose `checkout/` the test fills as the agent would have, and the changed paths given by hand (`FakeSnapshots` of S0001 may compute them); `tests/adapters/test_git_cli_check_ignore.py` for the git operation (`test_git_cli_ignored.py` already holds the tests of `remove_ignored`), on the real local clone of the fixtures with a `.gitignore` pushed to `main`.

## Acceptance criteria

1. `GitCli.ignored` (rows of one parametrized test on the real clone, whose `main` holds the tracked `docs/kept.log` and a `.gitignore` with `.venv/`, `*.log` and `!keep.log`, the file pushed before the `.gitignore` because `GitCli.commit` stages no ignored file; none of the asked paths need exist in the checkout): `[".venv/bin/python", "src/a.py", "run.log"]` gives `[".venv/bin/python", "run.log"]` in that order, and `["run.log", ".venv/bin/python"]` gives them in that order; `["src/a.py"]` gives `[]`; `["keep.log"]` gives `[]` (the negation); `["docs/kept.log"]` gives `[]` (tracked, although `*.log` matches it); `[]` gives `[]` and runs no git, and `["/abs"]` and `["a/../b"]` raise `ValueError` and run no git (through a recording `GitOptions.executable` stand-in, no call is recorded). Through a stand-in `git` that records its arguments and answers `::<TAB><path>` for each path after `--`: 1,000 paths are one call and 1,001 paths two calls, the answer in the paths' order; a stand-in that exits 128 printing `fatal: boom`, and one that prints one line fewer than the paths it was given, each raise `GitError` (rows of the same test).
2. `copy_changed` (rows of one parametrized test): an `added` regular file arrives with the same bytes and mode (`0o755` stays `0o755`, `0o644` stays `0o644`), its parent folders made; a `modified` file replaces the target's bytes and mode; a `deleted` path removes the target's file, and a `deleted` path missing on the target raises nothing; an `added` symbolic link arrives as a link with the same target text, and the file it points to is not read; a `modified` file whose target entry is a symbolic link to a file outside the target tree replaces the link by a regular file with the source's bytes, and the outside file keeps its bytes; an `added` file whose target entry is a folder holding a file leaves no folder and no contents, and the target is a regular file with the source's bytes; a `deleted` path whose target entry is a link to a folder outside the target tree removes the link, and the folder stays; `/abs` and `a/../b` raise `ValueError` before anything is copied (the target tree is unchanged).
3. A changed path under `checkout/` inside the write paths (`checkout/src/new.py` added, `checkout/src/kept.py` modified, `checkout/src/old.py` deleted, role write paths `["src/*", "{work_item}"]`) is taken: after `take`, the host's `src/new.py` and `src/kept.py` hold the dataset's bytes, `src/old.py` is gone, and `left` is `[]`.
4. A changed path outside the write paths (`checkout/docs/guide.md` modified) is left: the host's `docs/guide.md` keeps its bytes, the dataset's `checkout/docs/guide.md` keeps the agent's bytes, and `left` is `["docs/guide.md"]`. A protected path inside a write path that matches it (write paths `["*"]`, `checkout/pyproject.toml` added and `checkout/factory/story-form.md` modified) is left too: `left` is `["factory/story-form.md", "pyproject.toml"]` and neither reaches the host (rows of one parametrized test with criterion 3's row as the taken side).
5. The undo's second rule: with write paths `["*"]`, a second work item `checkout/factory/features/F0001-example/in-progress/F0001-S0002-second.md` modified, the own cost record `...-S0001-first.costs.jsonl` added, `.../in-progress/notes.txt` added and `.../in-progress/sub/x` added are judged as `left` `["factory/features/F0001-example/in-progress/F0001-S0001-first.costs.jsonl", "factory/features/F0001-example/in-progress/F0001-S0002-second.md", "factory/features/F0001-example/in-progress/notes.txt"]`, while `.../in-progress/sub/x` is taken (rows of one parametrized test).
6. Dropped paths (rows of one parametrized test, each neither on the host afterwards nor in `left`): `checkout/.venv/bin/python` added when `.gitignore` holds `.venv/`; `checkout/.git/config` modified; `checkout/src/.git/HEAD` added; `home/.claude.json` added; `caches/uv/x` added; `checkout` itself is never among the changed paths (the snapshots list no directory) and a changed path exactly `checkout` would be dropped too.
7. The work item (rows of one parametrized test, the own work item in the write paths): the agent changed a section and the state (`stage: done` in the front matter) on the dataset's copy: after `take`, the host's work item has the agent's section text, the baseline's state and journal, and `restored_work_item` is true; the agent changed nothing of state or journal: `restored_work_item` is false; the agent deleted the work item (`deleted`): it is back whole from the stage-start commit, `restored_work_item` true, not in `left`; the agent broke its front matter: back whole, `restored_work_item` true; the role may not write the work item (write paths `["src/*"]`, the work item modified): `left` holds its path, the host's file is unchanged, `restored_work_item` false.
8. A work item absent at the stage-start commit, and one whose front matter at that commit cannot be read (a commit of the test that breaks it, as `tests/application/test_undo.py` builds both baselines), each raise `WorkItemFormatError` naming `work_item_path`, and nothing on the host changed (a changed `checkout/src/new.py` did not arrive) (rows of one parametrized test).
9. `left` is sorted and holds each path once when the same path is given twice among `changed_paths`; the report is frozen and refuses an unknown field (`tests/test_model_configuration.py` covers the model).
10. `make check` stays green.
11. docs: `docs/project-guide/stage-environment.md` gains the section *The take*: the seven steps in order, what is dropped, what is left, what is taken, the work item's restore shared with the undo, `copy_changed` and its two users, the errors, the tests; `docs/project-guide/git-and-hosting.md`, *The git wrapper*: the row for `ignored` in the operations table (the command, the groups, what is read from the lines, the three exit statuses), the count twenty-six, and a row for `ignored` in *Which part uses which operation* (the take, `stage-environment.md`); `docs/project-guide/README.md`, *The files*, names `factory.application.take` for the stage-environment file; `docs/project-guide/write-guard.md`, *The undo*: one sentence that the take (`stage-environment.md`) applies the same two rules the other way round, in the container environment. `docs/decisions.md`: none in this story.

## Smoke test

```bash
uv run pytest tests/application/test_take.py tests/application/test_take_edges.py tests/adapters/test_git_cli_ignored.py tests/adapters/test_git_cli_check_ignore.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1` (the last line pytest prints is one `<n> passed in <s>s` line that counts the take tests and both git test files together, the old `test_git_cli_ignored.py` staying in as the check that `remove_ignored` still works)

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

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: 1. The smoke test's first command runs `tests/adapters/test_git_cli_ignored.py`, the file that already holds the `remove_ignored` tests. The Interface and criterion 1 put the new `ignored` tests in `tests/adapters/test_git_cli_check_ignore.py`. As written, the smoke test never runs the new git tests, and the `Expect: 1` line would pass without them. Option A, which I would choose: name `tests/adapters/test_git_cli_check_ignore.py` in the command (add it, or replace the old file). Option B: keep it as it is, if the old file is meant to run as a regression check.

   2. `copy_changed` says that for an `added` or `modified` path, an existing entry at the target is removed first, "a link as the link, a folder with what it holds". Criterion 2 has rows for a link at the target (the `modified` row) and for a deleted link. It has no row for a folder at the target replaced by a file, or for a file replaced by a folder. Without a criterion, two coders could read that clause two ways and both pass the tests. Option A, which I would choose: add one criterion 2 row, an `added` file whose target entry is a folder holding a file, where the folder and its contents are gone and the target holds a regular file with the source's bytes. Option B: drop "a folder with what it holds" from the Interface.

   The format check passed and I found nothing else. The Interface is concrete, the failing sides are covered (`ValueError`, `GitError`, `WorkItemFormatError`, refused and dropped paths), the architecture fits the layers, and the story is within the feature's scope.
4. 2026-10-24 human: Answers to the intake (F0042-S0004, the take copies what the role may write from the dataset into the work tree):

   1. **A**, and add it: the smoke test's first command runs both `tests/adapters/test_git_cli_ignored.py` and `tests/adapters/test_git_cli_check_ignore.py`. The old file stays in as a check that `remove_ignored` still works. The `Expect:` line follows the command; please make it name what the two files print together.
   2. **A**: one more row in criterion 2. An `added` file whose target is a folder holding a file: afterwards the folder and its contents are gone, and the target is a regular file with the source's bytes. The clause "a folder with what it holds" stays in the Interface.

   Please write both into the Smoke test and the criteria as you accept.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete. `Git.ignored` is specified with its signature, `GitCli.ignored` with the exact command, the groups of 1,000, how the lines are read and the errors. `TakeReport`, `copy_changed` and `TakeService.take` are specified with their signatures and seven ordered steps.
   - Criteria: each is testable by a parametrized test. Every rule has its failing side: `ValueError` for an absolute path or one with `..`, `GitError` for exit 128 and for a short answer, `WorkItemFormatError` for an absent or unreadable baseline, and the refused, left and dropped paths. I carried in the human's answer 2 from journal entry 4: criterion 2 gains the row for an `added` file whose target is a folder holding a file. That clause was the one the Interface had without a criterion.
   - Smoke test: both commands are runnable. I carried in the human's answer 1 from journal entry 4: the first command now also runs `tests/adapters/test_git_cli_check_ignore.py` and keeps `test_git_cli_ignored.py`. Its `Expect:` line names the single `<n> passed in <s>s` line that covers both git files and the take tests. The second command prints two lines that can be checked against the `Expect:` line. The command passes no `-q`, and I did not check pytest's `addopts` for one.
   - Architecture: `application.take` and the `Git` operation sit in `application`, the `git check-ignore` call sits in `adapters.git_cli`, and no layer is crossed. The undo's helpers are made public and shared rather than copied.
   - Scope: the story is within F0042's scope, which lists `TakeService`, `TakeReport`, the shared copying and `ignored`, and it removes no layer. Decision 18 d gives the leave to change `test_git_interface.py` and `test_interfaces.py`.
7. factory: started tests as self.
