---
stage: done
pr: 68
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Work items read from the remote-tracking refs

## Assignment (as of log entry 1)

Build the reader that turns the remote into the list of work items: the stories in `in-progress/` on `origin/main`, each with its state taken from its own remote branch `origin/work-item/<id>` and never from a local branch or the work tree, in plain id order. A story the human has started that has no branch yet is at the first stage with initial counters, whatever its file says. The caller fetches first (F0006-S0004); this reader only reads. Covers GH5.1, ST6.1 and R18; keeps kept things 2 (a story starts only by the human's move to `in-progress/`), 3 (the remote is the truth) and 15 (id order). Uses `Git` (F0001-S0005), `WorkItemReader`, the identifiers, `folder_of` and `initial_state` (F0002) and `PipelineDefinition` (F0003-S0004).

## Interface

`src/factory/domain/work_item.py` (added to the module F0002-S0002 created)

```python
class WorkItemSnapshot(BaseModel):            # one work item as the remote shows it (R18)
    id: WorkItemId
    path: str                                 # its path on origin/main
    folder: LifecycleFolder                   # "in-progress" for every snapshot RemoteWorkItems.read returns
    branch: str                               # branch_name(id)
    branch_commit: CommitId | None            # head of origin/<branch>; None when the branch does not exist
    document: WorkItemDocument                # from origin/<branch> when it exists; else main's text read with
                                              # parse_specification and state=initial_state(first stage)

class StoryFile(BaseModel):                   # one story file listed on origin/main
    id: WorkItemId                            # from the file name
    path: str                                 # repository-relative POSIX path
    feature_directory: str                    # "F0001-slug": the folder under factory/features
    file_name: str                            # "F0001-S0001-slug.md"
    folder: LifecycleFolder
```

Every model here is frozen and forbids unknown keys.

`src/factory/application/work_items.py`

```python
class RemoteWorkItems:
    def __init__(self, git: Git, reader: WorkItemReader) -> None: ...
    def list_stories(self, folder: LifecycleFolder) -> list[StoryFile]: ...
    def read(self, definition: PipelineDefinition) -> list[WorkItemSnapshot]: ...
        # WorkItemFormatError (with path set) for a story whose file is missing on its branch or cannot be read,
        # on its branch or on origin/main; GitError from Git
```

Rules:

- Everything is read from `origin/main` and `origin/<branch>` through `Git.list_files`, `Git.resolve` and `Git.show_file`. No local branch and no file of the work tree is read.
- A story file is a path for which `folder_of(path)` (`factory.domain.paths`) is not `None`, whose file name's feature id equals its directory's feature id, and whose work item id is not an acceptance (`is_acceptance`). Everything else in the tree is ignored; a file in `ongoing/` or `drafts/` is therefore not a story file.
- `list_stories(folder)` returns the story files whose `folder_of` is `folder`, in the order of `work_item_order(id)`, then path. Stories in `backlog/` and `done/` are listed on request and are never read by `read`.
- `read` makes one `WorkItemSnapshot` per story file in `in-progress/`, in the same order. Two story files with one id give two snapshots.
- With a branch (`Git.resolve("origin/" + branch)` is not `None`), `document` is `reader.parse` of the file at `origin/<branch>`, whether or not the branch is an ancestor of `origin/main`. A file missing at the branch tip, or a text `parse` refuses, is `WorkItemFormatError` with `path` set to the story's path.
- Without a branch, `branch_commit` is `None` and `document` is `WorkItemDocument(state=initial_state(definition.first_stage()), body=<parse_specification body>, ignored_keys=<parse_specification ignored_keys>)` from the file on `origin/main`: the file's own state fields are not applied (ST6.1). A text on `origin/main` that `parse_specification` refuses is `WorkItemFormatError` with `path` set to the story's path.

Tests: `tests/domain/test_work_item_snapshot.py` for the two models; `tests/application/test_work_items.py` for the rest, with the shared fixtures `remote`, `checkout`, `human` and `boundaries`. The tests write stories and branches on the remote through `human.push_file` and `human.start`, and read through `RemoteWorkItems(checkout, FrontmatterWorkItemReader())` after `checkout.fetch()`. The closed-model tests build the models through a variable typed `type[BaseModel]` and assign with `setattr`, the field's name in a variable.

## Acceptance criteria

1. `list_stories("in-progress")` returns one `StoryFile` for each story file on `origin/main` at `factory/features/<feature directory>/in-progress/<file name>`, with `id`, `path`, `feature_directory`, `file_name` and `folder` filled from the path and the file name.
2. `list_stories` reads `origin/main`: a story file that exists only in the checkout's work tree, or only in a local commit that was not pushed, is not listed.
3. `list_stories` orders by plain id order: pushed as `F0002-S0001`, `F0001-S0010`, `F0001-S0002` it returns `F0001-S0002`, `F0001-S0010`, `F0002-S0001`.
4. Files that are not story files are not listed: a `.gitkeep` in the folder, `feature.md` in the feature directory, a `.md` file one directory deeper, a file whose name is not a work item name, a file `F0002-S0001-x.md` inside the directory `F0001-demo`, and an acceptance file `F0001-A0001-report.md`.
5. `list_stories("backlog")` and `list_stories("done")` return only the story files of that folder.
6. For a story with a remote branch, `read` returns a snapshot with `id`, `path` on `origin/main`, `folder == "in-progress"`, `branch == "work-item/<id>"`, `branch_commit` equal to the head of `origin/work-item/<id>`, and `document` parsed from the file at that head, state and body.
7. GH5.1: when the human pushes a new commit to a story's remote branch while a stale local branch of the same name exists in the checkout, `read` after a fetch returns the pushed state and the pushed `branch_commit`, not the local branch's.
8. A branch that exists only in the checkout (never pushed, with a state in its file) is not read: the story is read as a story without a branch.
9. ST6.1: a story whose file carries the front matter `stage: review`, `attempts: 2`, `round: 1` and `blocked: question`, started by the human and without a branch, is read with `state == initial_state(<first stage>)`, `branch_commit is None` and all counters at their initial values.
10. For that story `document.body` is the text of the file on `origin/main` after its front matter, and `document.ignored_keys` lists `stage`, `attempts`, `round` and `blocked`.
11. A branch whose tip is an ancestor of `origin/main` (the human merged it with a merge commit and the story file is still in `in-progress/`) is read from the branch: the snapshot has that branch's state and `branch_commit`.
12. A story with a branch whose file is missing at the branch tip makes `read` raise `WorkItemFormatError` whose `path` is the story's path.
13. A story whose branch file has front matter that cannot be read makes `read` raise `WorkItemFormatError` whose `path` is the story's path.
14. A started story without a branch whose file on `origin/main` holds `---\n[\n---\n# T\n` makes `read` raise `WorkItemFormatError` whose `path` is the story's path.
15. `read` returns snapshots for the stories in `in-progress/` only: a story in `backlog/` and one in `done/` give none.
16. `read` returns the snapshots in plain id order (`F0001-S0002`, `F0001-S0010`, `F0002-S0001`), and two story files with one id in two features give two snapshots, ordered by path.
17. A file `factory/features/F0001-demo/ongoing/F0001-S0003-x.md` and one in `drafts/` are neither listed nor read.
18. `WorkItemSnapshot` and `StoryFile` refuse an unknown key and an assignment to a field; `branch_commit` of 40 lower-case hex characters and `None` are accepted, while 39 characters and 40 with an upper-case letter raise `ValidationError`; `folder` `"in-progress"` is accepted and `"ongoing"` raises `ValidationError`; an `id` of `F0001-S0001` is accepted and `F001-S0001` raises `ValidationError`.
19. make check stays green.
20. docs: `docs/project-guide.md` states that work items are read from `in-progress/` on `origin/main` and from `origin/work-item/<id>`, never from a local branch, and that a started story without a branch is at the first stage; `docs/operator-guide.md` says that the hosting setting that deletes head branches on merge must be off, because a merged story whose branch is gone is read as a new start; `docs/decisions.md` records why a branch that is an ancestor of `origin/main` is still read.

## Demo

```bash
uv run python -c "
import os, subprocess, tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.application.work_items import RemoteWorkItems
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
os.environ.update(GIT_AUTHOR_NAME='d', GIT_AUTHOR_EMAIL='d@example.com', GIT_COMMITTER_NAME='d', GIT_COMMITTER_EMAIL='d@example.com')
base = Path(tempfile.mkdtemp())
def sh(*args, cwd=base):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)
sh('git', 'init', '--bare', '-b', 'main', 'remote.git')
sh('git', 'clone', 'remote.git', 'seed')
seed = base / 'seed'
feature = seed / 'factory/features/F0001-demo'
(feature / 'in-progress').mkdir(parents=True)
(feature / 'in-progress/F0001-S0001-first.md').write_text('---\nstage: review\nattempts: 2\n---\n# First\n')
(feature / 'in-progress/F0001-S0002-second.md').write_text('# Second\n')
sh('git', 'add', '-A', cwd=seed)
sh('git', 'commit', '-m', 'seed', cwd=seed)
sh('git', 'push', 'origin', 'HEAD:main', cwd=seed)
sh('git', 'checkout', '-b', 'work-item/F0001-S0002', cwd=seed)
(feature / 'in-progress/F0001-S0002-second.md').write_text('---\nstage: tests\nattempts: 1\n---\n# Second\n')
sh('git', 'commit', '-am', 'state', cwd=seed)
sh('git', 'push', 'origin', 'work-item/F0001-S0002', cwd=seed)
git = GitCli(base / 'checkout')
git.clone(str(base / 'remote.git'))
git.fetch()
definition = PipelineDefinition(contract='1.0', stages={'intake': StageDefinition(role='intake', next=['done']), 'done': StageDefinition()}, roles={'intake': RoleDefinition(write_paths=['{work_item}'])})
result = RemoteWorkItems(git, FrontmatterWorkItemReader()).read(definition)
for s in result:
    print(s.id, s.branch, s.branch_commit is not None, s.document.state.stage, s.document.state.attempts)
"
```
Expect: two lines: `F0001-S0001 work-item/F0001-S0001 False intake 0` (no branch, so the first stage and attempts 0 although the file says `review` and 2) and `F0001-S0002 work-item/F0001-S0002 True tests 1` (read from its branch).

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory.domain.work_item`: `WorkItemSnapshot`, `StoryFile`; `factory.application.work_items`: `RemoteWorkItems.__init__/list_stories/read`) and the errors raised (`WorkItemFormatError` with `path`, `GitError`). I found nothing left to decide.
   - Criteria: each is testable by one test function. Every behaviour the Interface comments state has a criterion: order (3, 16), `folder` (6, 15), `branch_commit` None/hex (6, 9, 18), the document source with and without a branch (6, 8, 9, 10). Every rule has its failing side: a missing branch file (12), unreadable branch front matter (13), unreadable main text (14), a non-story file (4), a local-only branch or file (2, 8), ongoing/drafts (17), a bad `branch_commit`, `folder` or `id` (18).
   - Demo: runnable, and uses the stated API. Its `Expect:` line gives the two exact output lines, which can be checked.
   - Architecture: the reader is in `factory.application` and uses only the `Git` interface and `WorkItemReader`. The DTOs are frozen Pydantic models in `factory.domain`. No lower layer imports a higher one.
   - Scope: within F0006 "Reading work items (R18)". The caller's fetch is left to S0004, and nothing in Out of scope is touched.
3. tester: wrote red tests for every criterion, one test function (or one parametrized test) per criterion.
   - criterion 1: tests/application/test_work_items.py::test_in_progress_stories_are_listed_with_their_parts
   - criterion 2: tests/application/test_work_items.py::test_stories_only_in_the_checkout_are_not_listed (a file only in the work tree, then the same file in an unpushed local commit)
   - criterion 3: tests/application/test_work_items.py::test_stories_are_listed_in_plain_id_order
   - criterion 4: tests/application/test_work_items.py::test_files_that_are_not_story_files_are_not_listed (parametrized over the six non-story files, each next to one real story)
   - criterion 5: tests/application/test_work_items.py::test_backlog_and_done_list_only_their_own_stories
   - criterion 6: tests/application/test_work_items.py::test_a_story_with_a_remote_branch_is_read_from_its_head
   - criterion 7: tests/application/test_work_items.py::test_a_pushed_branch_wins_over_a_stale_local_branch
   - criterion 8: tests/application/test_work_items.py::test_a_branch_only_in_the_checkout_is_not_read
   - criterion 9: tests/application/test_work_items.py::test_a_started_story_without_a_branch_is_at_the_first_stage
   - criterion 10: tests/application/test_work_items.py::test_a_started_story_without_a_branch_keeps_its_body_and_ignores_its_keys
   - criterion 11: tests/application/test_work_items.py::test_a_branch_merged_into_main_is_still_read_from_the_branch
   - criterion 12: tests/application/test_work_items.py::test_a_story_missing_on_its_branch_is_a_format_error (the branch is pushed before the start, so the in-progress file is missing at its tip)
   - criterion 13: tests/application/test_work_items.py::test_unreadable_front_matter_on_the_branch_is_a_format_error
   - criterion 14: tests/application/test_work_items.py::test_unreadable_front_matter_on_main_without_a_branch_is_a_format_error
   - criterion 15: tests/application/test_work_items.py::test_only_in_progress_stories_are_read
   - criterion 16: tests/application/test_work_items.py::test_snapshots_come_in_plain_id_order_and_one_per_story_file (F0001-S0002 appears twice, in F0001-alpha and in F0001-beta, and the two are ordered by path)
   - criterion 17: tests/application/test_work_items.py::test_ongoing_and_drafts_files_are_neither_listed_nor_read (parametrized over ongoing and drafts; checks every lifecycle folder's list and `read`)
   - criterion 18: tests/domain/test_work_item_snapshot.py::test_an_unknown_key_is_refused, ::test_a_field_cannot_be_assigned, ::test_branch_commit_is_forty_lower_case_hex_characters_or_none, ::test_folder_is_a_lifecycle_folder, ::test_id_is_a_work_item_id. Each is parametrized over both models where the field exists. The models are built through `type[BaseModel]`, and fields are assigned with `setattr` and a field name held in a variable.
   - criteria 19 and 20 are for `make check` and the documenter; no tests.
   Files created: tests/domain/test_work_item_snapshot.py, tests/application/test_work_items.py. The pipeline definition comes from `boundaries.pipeline_reader.parse(PIPELINE_YAML)`, whose first stage is `intake`. Branch heads are compared with `remote_commit(remote, branch)`.
   `make test` fails as expected at collection: `factory.domain.work_item` has no `StoryFile` or `WorkItemSnapshot` yet, and the module `factory.application.work_items` does not exist. `make lint` is green. I ran `ruff format` on the two new files only. Nothing needed interpreting, so nothing is open.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: built the remote reader for work items; all tests pass and `make check` is green (total coverage 99.35 %). I ran the ticket's demo and it prints the two expected lines.
      - `src/factory/domain/work_item.py`: added `WorkItemSnapshot` and `StoryFile`, both frozen with `extra="forbid"`. `branch_commit` uses `CommitId` from `factory.domain.git`, `folder` uses `LifecycleFolder` from `factory.domain.paths` and `id` uses `WorkItemId`.
      - `src/factory/application/work_items.py`: added `RemoteWorkItems`. `list_stories` filters `Git.list_files("origin/main", "factory/features")` through `_story_file`, which keeps a path only if `folder_of` accepts it, its feature id matches its directory's and it is not an acceptance. The result is sorted by `(work_item_order(id), path)`. `read` turns each `in-progress` story into a snapshot. If `Git.resolve("origin/work-item/<id>")` finds a branch, the document is `reader.parse` of the file at that tip, with no ancestor check. Otherwise the state is `initial_state(definition.first_stage())`, and body and ignored keys come from `parse_specification` of main's text. A missing file or a `WorkItemFormatError` from the reader is raised again as `WorkItemFormatError(fault, story.path)`.
      - Main design decision: the work item id and the feature directory are taken from `folder_of` and the identifier parsers in `factory.domain`. I rejected writing a second path regex in the application layer, because two copies of the path rules could drift apart.
      - Commits: 08bf3d5 adds the feature. 2acdd21 is the refactor: the two identical try/except blocks that added the path became one helper, `_parsed`.
      - Noticed, not touched: two defensive lines are not covered (`work_items.py:85` and `:106`). Line 85 handles a listed file missing on main; line 106 handles the case where the name parsers return None after `folder_of` accepted the path. No test can reach either one, but mypy needs them to narrow the types.

   `make check`: check: green
5. reviewer: no findings.
      - Scope: `src/factory/application/work_items.py`, `src/factory/domain/work_item.py`, `tests/application/test_work_items.py` and `tests/domain/test_work_item_snapshot.py`. The diff stat also lists changes in `planning/`, `docs/runs/` and `planning/.../F0009*`. Those come from the human's commit aa2b4fc on origin/main, which reached this branch through the merge 9900f73. The coder did not write them, so they are not reviewed.
      - Criteria: each of 1–18 has a test that checks what the criterion says. The rules that can fail are tested on the failing side: a listed file missing at the branch tip (12), unreadable front matter on the branch (13) and on main (14), local-only files, commits and branches (2, 8), non-story files including a feature mismatch and an acceptance (4), ongoing/drafts (17), and a bad `branch_commit`/`folder`/`id` (18). The coder's entry reports the factory's `make check` as green.
      - Architecture: `RemoteWorkItems` sits in `factory.application` and imports only the `Git` and `WorkItemReader` interfaces and `factory.domain`. It reads only through `list_files`/`resolve`/`show_file` on `origin/main` and `origin/<branch>`. The two DTOs are frozen, use `extra="forbid"`, and reuse `CommitId`, `WorkItemId` and `LifecycleFolder`.
      - Security: no strings are built into a command, and no suppression markers were added.
      - Quality: the error is wrapped with the path in one place (`_parsed`). Path rules come from `folder_of` and the identifier parsers rather than a second regex. The two uncovered defensive branches (`work_items.py:85`, `:106`) are explained in the coder's entry, and mypy needs them for narrowing. Docstrings and the why-comments on `_branch_document`/`_started_document` meet `CLAUDE.md`.
      - Hygiene: the log gives the main decision and the rejected alternative, the Assignment matches what was built, and criterion 20 still describes what the documenter has to write.
6. documenter: wrote the three things criterion 20 asks for; `make check` is green.
   - docs/project-guide.md: new section "The remote's work items" (before "Reading and writing a work item file"). It covers the two DTOs and `RemoteWorkItems`. Work items are read from `in-progress/` on `origin/main` and from `origin/work-item/<id>`, never from a local branch or the work tree. A started story without a branch is at the first stage and its state keys are ignored. The section also states which files count as story files, the order, and the errors.
   - docs/operator-guide.md: new section "Branch deletion on merge must be off". A merged story whose branch is gone is read as a new start.
   - docs/decisions.md: new entry on why a branch that is an ancestor of `origin/main` is still read.
   - Cross-read against the diff and found current: README.md; the git wrapper and the "Identity, order and places" sections of the project guide, which `RemoteWorkItems` only uses. "The document and its error" is also current.
   - The code matches the Interface and the criteria, so there are no findings.
   - Stale but unrelated, not touched: the diff stat shows planning/ and F0009 changes from the human's merge commit; they are not mine.
   - I did not run the ticket's demo myself; I checked the new prose against the code instead.

   `make check`: check: green
7. demo: I ran the one `## Demo` command from the repository root exactly as written. It exited 0 and its output matched the `Expect:` line. No findings.

   Command 1 (`uv run python -c "…"`: seeds a bare remote, pushes two in-progress stories and a `work-item/F0001-S0002` branch, clones, fetches, then runs `RemoteWorkItems(...).read(definition)`):
   ```
   F0001-S0001 work-item/F0001-S0001 False intake 0
   F0001-S0002 work-item/F0001-S0002 True tests 1
   ```
   - It met its `Expect:` line. There are exactly the two expected lines, in plain id order.
   - F0001-S0001 has no branch. It is at the first stage `intake` with attempts 0, even though its file on `origin/main` says `stage: review` and `attempts: 2` (ST6.1, criterion 9).
   - F0001-S0002 is read from its remote branch: `branch_commit` is set, and the state (`tests`, 1) comes from the branch tip (criterion 6).

   Criteria cross-check: the demo contradicts none of criteria 1–18.
   - Only the `in-progress/` stories appear (criterion 15).
   - They come in id order (criteria 3 and 16).
   - `branch` is `work-item/<id>` for both, including the one without a branch (Interface: `branch_name(id)`).
   - The demo did not exercise the other criteria (error paths, local-only branches, ancestor branches, model validation). Per the earlier entries, the tester's tests cover them and the reviewer checked them.

   Open: nothing.
8. done (pull request merged); cost: 6 runs, 9.2 min, 49 turns, 159k tokens in (1115k more from cache), 29k out, $1.84
