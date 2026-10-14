---
stage: ready
pr: null
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
