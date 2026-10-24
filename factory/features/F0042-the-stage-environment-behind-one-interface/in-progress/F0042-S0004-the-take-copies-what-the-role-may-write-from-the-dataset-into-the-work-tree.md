---
stage: doing
blocked: null
round: 1
attempts: 1
crashes: 0
pull_request: 411
comments_read: [6386154578, 6386353501]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T15:39:27.156256Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T15:39:27.161611Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-24T15:39:49.304745Z'
  stage: intake
  run: 8990f54f66674414bb4064f56d1864e5
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-24T15:42:10.728644Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-24T15:42:28.635491Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-24T15:42:46.674332Z'
  stage: intake
  run: 4754a858818e49b1a2a322076c28cc25
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-24T15:43:07.067570Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-24T15:48:46.735356Z'
  stage: tests
  run: 8f412e333f2c4659b795d18cd90ed1ae
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-24T15:49:08.723875Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-24T15:52:40.234471Z'
  stage: doing
  run: 03abec51b738400297d7e6b4031497f3
- number: 11
  speaker: factory
  kind: stall
  at: '2026-10-24T15:52:40.268302Z'
  stage: doing
  run: 03abec51b738400297d7e6b4031497f3
  reason: check_red
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-24T15:53:03.039000Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-10-24T15:56:02.460237Z'
  stage: doing
  run: 4fe1b3939b4648df968fa852150687df
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-24T15:56:23.163657Z'
  stage: review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-10-24T15:58:06.222848Z'
  stage: review
  run: bd23e10c76e84ee19c75fd2c850cc8db
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-24T15:58:26.876598Z'
  stage: doing
- number: 17
  speaker: coder
  kind: question
  at: '2026-10-24T15:59:06.416455Z'
  stage: doing
  run: 2eae9d8867be4fbeb4110cfeff5d219a
  blocked: question
- number: 18
  speaker: human
  kind: comment
  at: '2026-10-24T16:00:22.546159Z'
  stage: doing
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
10. The other sides of two rules the Interface states: a stand-in `git` that prints one line more than the paths it was given raises `GitError` (a row of criterion 1's stand-in test, beside the line-short row); a `deleted` path whose target entry is a dangling symbolic link removes the link and raises nothing (a row of criterion 2's test).
11. The dataset is not written: after `take` with criterion 3's rows and a work item restore (criterion 7's first row), every file under `mount_point` has the same bytes and mode as before, the listing under `mount_point` is unchanged, and the fixtures' git history has no new commit.
12. `make check` stays green.
13. docs: `docs/project-guide/stage-environment.md` gains the section *The take*: the seven steps in order, what is dropped, what is left, what is taken, the work item's restore shared with the undo, `copy_changed` and its two users, the errors, the tests; `docs/project-guide/git-and-hosting.md`, *The git wrapper*: the row for `ignored` in the operations table (the command, the groups, what is read from the lines, the three exit statuses), the count twenty-six, and a row for `ignored` in *Which part uses which operation* (the take, `stage-environment.md`); `docs/project-guide/README.md`, *The files*, names `factory.application.take` for the stage-environment file; `docs/project-guide/write-guard.md`, *The undo*: one sentence that the take (`stage-environment.md`) applies the same two rules the other way round, in the container environment. `docs/decisions.md`: none in this story.

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
3. intake: 1. The Interface says "The service writes no commit, runs no git command on the dataset and never writes under `mount_point`", and step 4 says "the dataset is never written". Only the left paths have a check for this (criterion 4: the dataset's `checkout/docs/guide.md` keeps the agent's bytes). No criterion covers the taken paths (criterion 3), the restored work item (criterion 7) or the dataset as a whole. Two coders could read this two ways and both would pass the tests. Option A, the one I would choose: add a criterion before the two closing ones. After `take` with criterion 3's rows plus a work item restore, every file under `mount_point` has the same bytes, mode and listing as before, and the fixtures' git history has no new commit. Option B: drop the sentence from the Interface, which would be your edit. Intake otherwise found the story buildable, and the Format check passed. The checks I did:
   - **Interface:** names concrete modules and signatures.
   - **Criteria:** each is testable. Both sides of every other rule have a criterion.
   - **Smoke test:** the commands are runnable. pyproject sets `-q` in `addopts`, and the pytest command passes none, so the `N passed in` line exists.
   - **Architecture:** the layering is right.
   - **Scope:** within F0042.
4. 2026-10-24 human: Answer to the intake (F0042-S0004, the take copies what the role may write from the dataset into the work tree): **A**. Add a criterion before the two closing ones: after `take` with criterion 3's rows and a work item restore, every file under `mount_point` has the same bytes and mode as before, the listing under `mount_point` is unchanged, and the fixtures' git history has no new commit. The Interface's sentence stays. Please write it into the criteria as you accept.
5. factory: started intake as self.
6. intake: accepted
   - Interface: names concrete modules and signatures (`Git.ignored`, `GitCli.ignored`, `TakeReport`, `copy_changed`, `TakeService.__init__` and `take`). Every behaviour stated in it has a criterion: the grouping at 1,000 and 1,001, the order, the negation, tracked paths, the three exit statuses, the line count (short and long), `ValueError` for absolute and `..` paths, the removal of links, the sorted report.
   - Criteria: each is testable by one parametrized test. Every rule has both sides: taken and left, dropped paths, the work item's four restore cases, both baseline faults, the paths that fail `check_repository_path`. Per the human's answer in journal entry 4 (option A) I wrote the new criterion 11 (the dataset is not written: same bytes and mode, same listing, no new commit in the fixtures' history). The closing two are now 12 (`make check`) and 13 (`docs:`).
   - Smoke test: both commands are runnable. pyproject sets `-q` in `addopts` and the pytest command passes none, so the `N passed in` line exists. Each `Expect:` line can be checked against the output.
   - Architecture: `factory.application.take` and the `Git` operation sit in `application`, `GitCli.ignored` in `adapters`, with no import against the layers. This matches CLAUDE.md.
   - Scope: inside F0042's scope (S0004, decisions 10 and 18 d). Nothing is in "Out of scope". The story changes tests that other stories wrote only where decision 18 d gives the leave.
7. factory: started tests as self.
8. tester: Wrote the red tests for the take and for the git operation `ignored`. One `make test` run: the failures are the right ones. `GitCli` has no attribute `ignored`, the Git interface tests count twenty-six operations and find twenty-five, and the two take modules fail at collection because `factory.application.take` does not exist yet. `make lint` is green. I did not run the type check (stage rule).

   Criterion → test:
   - criterion 1: tests/adapters/test_git_cli_check_ignore.py::test_ignored_names_the_paths_the_rules_ignore_in_the_order_given (real clone; `main` has `docs/kept.log` pushed before the `.gitignore`), ::test_ignored_runs_no_git_for_no_paths_or_a_refused_path (`[]`, `/abs`, `a/../b`; a recording stand-in records no call), ::test_ignored_asks_git_in_groups_and_refuses_an_answer_it_cannot_read (1,000 → one call, 1,001 → two calls, the paths asked in order, `check-ignore --verbose --non-matching` just before `--`; exit 128 `fatal: boom` and a line short raise `GitError`)
   - criterion 2: tests/application/test_take_edges.py::test_copy_changed_mirrors_each_changed_path_into_the_target
   - criterion 3: tests/application/test_take.py::test_a_changed_path_is_taken_only_where_the_role_may_write[inside-the-write-paths]
   - criterion 4: tests/application/test_take.py::test_a_changed_path_is_taken_only_where_the_role_may_write[outside-the-write-paths, protected]
   - criterion 5: tests/application/test_take.py::test_every_other_file_directly_in_an_in_progress_folder_is_left
   - criterion 6: tests/application/test_take_edges.py::test_a_dropped_path_is_neither_taken_nor_left
   - criterion 7: tests/application/test_take.py::test_the_work_items_state_and_journal_come_back_from_the_stage_start
   - criterion 8: tests/application/test_take_edges.py::test_a_missing_or_unreadable_baseline_raises_before_anything_is_taken
   - criterion 9: tests/application/test_take.py::test_left_ascends_and_holds_a_path_given_twice_once (the model's frozen and unknown-key checks stay with tests/test_model_configuration.py)
   - criterion 10: row `line-long` of criterion 1's stand-in test; row `deleted-dangling-link` of criterion 2's test
   - criterion 11: tests/application/test_take.py::test_the_take_writes_nothing_in_the_dataset_and_no_commit
   - criteria 12 and 13: no test (`make check` and docs)

   Files created:
   - tests/adapters/test_git_cli_check_ignore.py
   - tests/application/test_take.py
   - tests/application/test_take_edges.py
   - tests/take_support.py: shared helpers for both take modules. It makes a dataset under `tmp_path/dataset` by copying the host checkout without `.git`, writes the agent's files there, builds the `ChangedPath` list, runs `TakeService` and snapshots a tree (kind, mode, bytes).

   Earlier test files I changed, under decision 18 d that the Interface cites:
   - tests/application/test_git_interface.py: `ignored` added to `OPERATIONS`, and the test renamed from `..._twenty_five_...` to `..._twenty_six_...`.
   - tests/application/test_interfaces.py: the same rename.

   tests/application/test_undo.py and tests/undo_support.py are untouched.

   Module the test run could not import: `factory.application.take`, giving collection errors in test_take.py and test_take_edges.py. `GitCli.ignored` is missing too.

   How some tests read the criteria:
   - Criterion 6: "neither on the host" is tested as the host work tree outside `.git` and its `.git/config` being unchanged.
   - The "the file a link points to is not read" row uses a dangling source link.
   - The `ValueError` rows put a valid path before the refused one and check the target tree is unchanged.

   Rejected: reusing the private `_recording_executable` from test_git_cli_arguments.py. The new stand-in also has to answer `check-ignore` lines, so it is a different helper, not a copy.

   `lint`: lint: green (0.5 s)
   `test`: ERROR tests/application/test_take_edges.py - ImportError while importing test module '/work/checkout/tests/application/test_take_edges.py'.
9. factory: started doing as self.
10. coder: Built the take and the git operation `ignored`; `make check` is green.

    What I built (paths):
    - src/factory/application/git.py: `Git.ignored`, the twenty-sixth operation.
    - src/factory/adapters/git_cli.py: `GitCli.ignored`. It checks every path with `check_repository_path` first; `[]` runs no git. It then runs `git check-ignore --verbose --non-matching -- <paths>` per group of `IGNORE_GROUP` (1,000). Exit 0 and `NONE_IGNORED` (1) are both read as answers; any other exit status raises `GitError`, and so does a line count different from the path count (`_ignored_group`). A path is ignored when the rule before the tab is not `NO_RULE` (`::`) and its pattern, the text after the second colon, does not start with `!` (`_is_ignoring`).
    - src/factory/application/take.py (new): `TakeReport`, `copy_changed`, `TakeService.take`. `copy_changed` checks every path before copying anything. It removes the target entry by `lstat`, so a link goes as the link, a folder with what it holds, and a missing entry is no fault. For added or modified it then places the source: a link by its target text, a regular file by `shutil.copyfile(follow_symlinks=False)` plus `chmod` to the source's mode, parents made. `take` follows the seven steps: baseline, write paths, candidates (under `checkout/`, prefix removed, no `.git` segment, minus `git.ignored`), refused into a sorted, deduplicated `left`, copy, work item restore unless refused, report.
    - src/factory/application/undo.py: `_baseline`, `_restore_work_item` and `_is_refused` became the public module functions `read_baseline`, `restore_work_item` and `is_refused`, each taking `Boundaries` where it needs it. The take imports them, so nothing is copied. The undo's behaviour is unchanged, and tests/application/test_undo.py passes untouched.

    Main decision: the take skips the restore through `work_item_path not in left`, which gives "a refused work item is not restored" directly. Rejected: always running the restore and relying on it returning false because the host's copy is unchanged. That holds only while the host's copy still equals the stage-start commit.

    Refactor pass: renamed `tracked` to `outside_git` in `_candidates` (those paths are not about git tracking) and shortened two docstrings for the line length. Nothing else needed changing.

    Noticed, not touched:
    - `copy_changed` does not check whether a parent folder on the target is a symbolic link, so it would write through such a parent. The Interface only requires that the entry itself is never written through; this could be a follow-up story if wanted.
    - `_is_ignoring` takes the pattern after the second colon. An ignore-file path holding a colon, or a pattern holding a tab, would be misread.
    - `make duplicates` (a record, not a check): three new dead-code findings in take.py (`TakeService`, `take`, `restored_work_item`). They are expected, because nothing calls the service until S0007. A fourth, `WORK_HOME` in src/factory/domain/containers.py, does not come from this story.
    - One `make check` run ended in `make types` with exit 139 (a mypy segfault, not a type error). The rerun was green throughout.
    - A `git stash` I tried in order to compare the duplicates baseline created no stash and changed nothing; the working tree is intact.
11. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
    Using CPython 3.12.15 interpreter at: /usr/local/bin/python3.12
    Creating virtual environment at: .venv
    Installed 106 packages in 97ms
    Bytecode compiled 4164 files in 368ms
    All checks passed!
    Bytecode compiled 4164 files in 128ms
    lint: green (0.6 s)
    Bytecode compiled 4164 files in 89ms
    make: *** [Makefile:39: types] Error 139
12. factory: started doing as self.
13. coder: The work is unchanged from the previous attempt (entry 10), and a fresh `make check` run is green throughout, `types` included. The stall in entry 11 was `make types` ending with exit 139, which is a mypy segfault and not a type error. It did not happen again: the full run ended with `test: green (65.9 s)`, total coverage 99.18 %, and `check: green`. I changed no code in this attempt.

    What I built (paths, as entry 10 lists them):
    - src/factory/application/git.py: adds `Git.ignored`, the twenty-sixth operation.
    - src/factory/adapters/git_cli.py: adds `GitCli.ignored`. It first checks every path with `check_repository_path`. It then runs `check-ignore --verbose --non-matching --` in groups of `IGNORE_GROUP` (1,000) paths, and exit statuses 0 and `NONE_IGNORED` (1) both count as answers. A line count that differs from the path count raises `GitError`. A `::` rule or a `!` pattern means the path is not ignored.
    - src/factory/application/take.py (new): `TakeReport`, `copy_changed` and `TakeService.take`, which runs the seven steps in order.
    - src/factory/application/undo.py: three helpers are now public (`read_baseline`, `restore_work_item`, `is_refused`). The take shares them, so nothing is copied. The undo behaves as before, and tests/application/test_undo.py is untouched.

    Main decision: the take skips the restore of the work item when the work item is in `left`, so a refused work item is never restored. I rejected always running the restore and relying on it returning false: that holds only while the host's copy still equals the stage-start commit.

    Refactor: I read the diff again (take.py, git_cli.py) and found nothing to change.

    Noticed, not touched (as in entry 10):
    - `copy_changed` does not check whether a parent folder on the target is a symbolic link, so it can write through a linked parent. The Interface only requires that the entry itself is never written through.
    - `_is_ignoring` reads the pattern as the text after the second colon. An ignore-file path that holds a colon, or a pattern that holds a tab, would be misread.
    - `make duplicates` shows dead-code findings for `TakeService`, `take` and `restored_work_item`. They are expected until S0007 calls the service.
    - The mypy segfault happened once and has not come back. If it recurs, it is a fault of the tool, not of this code.

    `check`: check: green
    `duplicates`: duplicates: 14 new, 38 known, 0 gone
14. factory: started review as self.
15. reviewer: Review, round 0. I read the work item, `git diff main...HEAD -- . ':!factory'` (src: `git_cli.py`, `git.py`, `take.py`, `undo.py`; tests: `test_git_cli_check_ignore.py`, `test_take.py`, `test_take_edges.py`, `take_support.py`, and the two renamed interface tests) and the coder's journal. The factory's `make check` after the coder was green (entry 13). Group 1 (acceptance criteria) fails, so I stopped there and did not judge groups 2 to 5.

    Findings:
    1. `tests/adapters/test_git_cli_check_ignore.py::test_ignored_asks_git_in_groups_and_refuses_an_answer_it_cannot_read`, rows `one-group` and `two-groups`: criterion 1 says 1,001 paths give two calls "the answer in the paths' order". The stand-in answers `::<TAB><path>` for every path, so `cli.ignored(paths)` is always `[]`. The rows never check how the two groups' answers are joined. A `GitCli.ignored` that kept only the last group's answer (`found = ...` instead of `found.extend(...)`) would still pass. Fix (tester): make the stand-in answer an ignoring rule line (e.g. `.gitignore:1:*.log<TAB><path>`) for some paths in both groups, e.g. every path whose name ends in `.log`. Then assert that the returned list holds exactly those paths from both groups, in the order given.
    2. `src/factory/application/take.py:_place` / `copy_changed`, and the story's Interface: the Interface says "nothing is ever written through a link that stood at the target". No criterion covers its failing side for a link at a parent folder of the path (target `src/evil -> <folder outside>`, `src/evil/x` added). The code does `entry.parent.mkdir(..., exist_ok=True)` and `shutil.copyfile`, so it writes through such a link and out of the work tree; the coder noted this in entry 10. This gap is in the story, not in the tester's work. Fix: either a new row in criterion 2's test (a parent folder on the target that is a link to a folder outside: nothing is written outside, and the target ends as a real folder holding the source's file) plus the code to match, or the human narrows the Interface's sentence to the entry itself. Because it needs a code change or the human's word, the coder should ask (`question`) unless the answer is already clear.

    Earlier tests (item 6):
    - `tests/application/test_git_interface.py`: under the human's leave, feature.md decision 18 (d), which the story's Interface cites (`OPERATIONS` gains `ignored`, test renamed to twenty-six). It stays within that leave.
    - `tests/application/test_interfaces.py`: under the same leave, 18 (d) (`test_git_abstract_methods_are_exactly_its_twenty_five_operations` renamed to twenty-six, assertion unchanged). It stays within that leave.
16. factory: started doing as self.
17. coder: Round 1. I read the reviewer's two findings (entry 15) and `src/factory/application/take.py`. I changed no code. Finding 1 needs only a test change. Finding 2 needs your word on the scope before I or the tester can act.

    **Question (finding 2): should `copy_changed` also refuse to write through a symbolic link at a *parent* folder of a path on the target?**

    The Interface says the entry at `target / path` is removed before the source is placed, "so nothing is ever written through a link that stood at the target". `_place` (`src/factory/application/take.py:100`) calls `entry.parent.mkdir(parents=True, exist_ok=True)` and then `shutil.copyfile`. When the target holds `src/evil -> <folder outside>` and `src/evil/x` is added, the file is written outside the work tree. The same holds for a `deleted` path: `_remove_entry` on `src/evil/x` would remove the outside file. A link like that can reach the host's work tree through an earlier commit, since the take itself copies links the role may write. No criterion covers this side.

    Options:
    - **A (my choice):** widen the rule to every parent folder and add a criterion before the two closing ones. Before a path is placed or removed, each parent folder from `target` down to the entry is checked with `lstat`.
      - For `added`/`modified`, a parent that is a link or not a folder is removed (the link as the link) and made a real folder. The source's file then lands inside the target tree, and nothing outside is written.
      - For `deleted`, a parent that is a link or missing means the entry is not in the tree, so nothing is removed and nothing is followed.
      - The tester adds two rows to criterion 2's test: (a) target `src/evil` a link to an outside folder, `src/evil/x` added. The outside folder is unchanged, and `src/evil` ends as a real folder holding the source's `x`. (b) The same link, `src/evil/x` deleted. The outside file stays.
      - I then implement it in `copy_changed`, a small helper beside `_remove_entry`.
    - **B:** narrow the Interface's sentence to the entry itself ("nothing is ever written through a link that stood at the entry's own place on the target"). The code stays as it is, and the parent-link case becomes a separate backlog story if you want one.

    **Finding 1, after your answer.** This is only a test change, so I will end with `tests` and name it. In `tests/adapters/test_git_cli_check_ignore.py::test_ignored_asks_git_in_groups_and_refuses_an_answer_it_cannot_read`, rows `one-group` and `two-groups`, the stand-in should answer an ignoring line (`.gitignore:1:*.log<TAB><path>`) for the paths ending in `.log`, and the assertion should check the joined result: those paths from both groups, in the order given. The code already joins with `extend`, so I expect it to pass unchanged. With A, the same `tests` hand-over also names the two new rows of criterion 2's test, and I write the code once the tester has added them.

    Noticed, not touched: as entry 10 says, `_is_ignoring` misreads an ignore-file path that holds a colon. `make duplicates` reports dead code for `TakeService`, which is expected until the container environment calls it.
18. 2026-10-24 human: Answer to the coder (F0042-S0004, the take copies what the role may write from the dataset into the work tree): **A**, as you propose.

    The take must never write or remove anything outside the work tree, through any link, so the rule covers every parent folder:
    - **added or modified:** before the entry is placed, every parent folder from `target` down to the entry is checked with `lstat`. A parent that is a link, or no folder, is removed (a link as the link) and made a real folder; the source's file then lands inside the target tree.
    - **deleted:** a parent that is a link or is missing means the entry is not in the tree, so nothing is removed and nothing is followed.

    Add one criterion before the two closing ones, tested as the two rows you name in criterion 2's test: (a) target `src/evil` a link to a folder outside, `src/evil/x` added: the outside folder is unchanged, and `src/evil` ends as a real folder holding the source's `x`; (b) the same link, `src/evil/x` deleted: the outside file stays. Finding 1 as you describe it: a test change only.

    Please write the rule into the Interface and the criterion into the criteria.
