# Work items read from the remote-tracking refs

## Assignment (as of log entry 1)

Build the reader that turns the remote into the list of work items: the stories in `in-progress/` on `origin/main`, each with its state taken from its own remote branch `origin/work-item/<id>` and never from a local branch or the work tree, in plain id order. A story the human has started that has no branch yet is at the first stage with initial counters, whatever its file says. A work item of v1's format is not read as a work item but listed apart, so that the tick can stop on it. The caller fetches first (F0006-S0004); this reader only reads. Covers GH5.1, ST6.1 and R18 (and R26's recognition); keeps kept things 2 (a story starts only by the human's move to `in-progress/`), 3 (the remote is the truth) and 15 (id order). Uses `Git` (F0001-S0004), `WorkItemReader`, the identifiers and `initial_state` (F0002) and `PipelineDefinition` (F0003-S0003).

## Interface

`src/factory/domain/work_item.py` (added to the module F0002-S0002 created)

```python
V1_STATE_KEYS: tuple[str, ...] = ("comments_seen", "pr")   # front matter keys only v1 writes (R26)

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

class V1WorkItem(BaseModel):                  # a work item of v1's format (R26)
    path: str
    reason: Literal["v1_folder", "v1_state_key"]
    key: str | None = None                    # the v1 state key found; None for "v1_folder"

    @property
    def detail(self) -> str: ...
        # "v1_folder":    f"{path}: a work item of v1 (folder ongoing)"
        # "v1_state_key": f"{path}: a work item of v1 (state key {key})"

class WorkItemsRead(BaseModel):
    snapshots: list[WorkItemSnapshot]         # stories in in-progress/, plain id order, then path
    v1_items: list[V1WorkItem]                # in path order
```

`src/factory/application/work_items.py`

```python
class RemoteWorkItems:
    def __init__(self, git: Git, reader: WorkItemReader) -> None: ...
    def list_stories(self, folder: LifecycleFolder) -> list[StoryFile]: ...
    def read(self, definition: PipelineDefinition) -> WorkItemsRead: ...
        # WorkItemFormatError (with path set) for a story whose file is missing on its branch or cannot be read;
        # GitError from Git
```

Rules:

- Everything is read from `origin/main` and `origin/<branch>` through `Git.list_files`, `Git.resolve` and `Git.show_file`. No local branch and no file of the work tree is read.
- A story file is a `.md` file exactly three levels below `factory/features`: `<feature directory>/<folder>/<file name>`. The directory name must parse with `parse_feature_directory_name`, the file name with `parse_work_item_file_name`, the file's feature id must equal the directory's id, and `is_acceptance(id)` must be false. Everything else in the tree is ignored.
- `list_stories(folder)` returns the story files of that folder in the order of `work_item_order(id)`, then path.
- `read` makes one `WorkItemSnapshot` per story file in `in-progress/`, in the same order. Two story files with one id give two snapshots.
- With a branch (`Git.resolve("origin/" + branch)` is not `None`), `document` is `reader.parse` of the file at `origin/<branch>`, whether or not the branch is an ancestor of `origin/main`. A file missing at the branch tip, or a text `parse` refuses, is `WorkItemFormatError` with `path` set to the story's path.
- Without a branch, `branch_commit` is `None` and `document` is `WorkItemDocument(state=initial_state(definition.first_stage()), body=<parse_specification body>, ignored_keys=<parse_specification ignored_keys>)` from the file on `origin/main`: the file's own state fields are not applied (ST6.1).
- A story file in a `ongoing/` folder (same three-level rule) is a `V1WorkItem(reason="v1_folder")`. A story in `in-progress/` whose `parse_specification(...).ignored_keys` (from its branch file, else main's) contains a key of `V1_STATE_KEYS` is a `V1WorkItem(reason="v1_state_key", key=<the first such key in V1_STATE_KEYS order>)`. Neither kind is a snapshot. Stories in `backlog/` and `done/` are not read.

Tests: `tests/domain/test_v1_work_item.py` for `V1WorkItem.detail`; `tests/application/test_work_items.py` for the rest, with the shared fixtures `remote`, `checkout`, `human` and `boundaries`. The tests write stories and branches on the remote through `human.push_file` and `human.start`, and read through `RemoteWorkItems(checkout, FrontmatterWorkItemReader())` after `checkout.fetch()`.

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
14. `read` returns snapshots for the stories in `in-progress/` only: a story in `backlog/` and one in `done/` give none.
15. `read` returns the snapshots in plain id order (`F0001-S0002`, `F0001-S0010`, `F0002-S0001`), and two story files with one id in two features give two snapshots, ordered by path.
16. A story file in `factory/features/<feature directory>/ongoing/` is returned in `v1_items` as `V1WorkItem(path=<its path>, reason="v1_folder", key=None)` and is not a snapshot; two such files are returned in path order.
17. A story in `in-progress/` whose front matter holds `comments_seen` is returned in `v1_items` as `V1WorkItem(reason="v1_state_key", key="comments_seen")` and is not a snapshot, whether the key is in its branch file or in its file on `origin/main` without a branch.
18. A story whose front matter holds `pr` is returned in `v1_items` with `key == "pr"`, and one that holds both `pr` and `comments_seen` with `key == "comments_seen"`.
19. A story whose front matter holds only keys of the current format (`stage`, `pull_request`, `comments_read`, `journal`) is a snapshot and not in `v1_items`; a story file in `drafts/` is neither.
20. `V1WorkItem.detail` is `<path>: a work item of v1 (folder ongoing)` for `v1_folder` and `<path>: a work item of v1 (state key <key>)` for `v1_state_key`.
21. `make check` stays green.
22. docs: `docs/project-guide.md` states that work items are read from `in-progress/` on `origin/main` and from `origin/work-item/<id>`, never from a local branch, and that a started story without a branch is at the first stage; `docs/decisions.md` records why a branch that is an ancestor of `origin/main` is still read, and why `ongoing/` and the keys `comments_seen` and `pr` mean a work item of v1.

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
(feature / 'ongoing').mkdir()
(feature / 'in-progress/F0001-S0001-first.md').write_text('---\nstage: review\nattempts: 2\n---\n# First\n')
(feature / 'in-progress/F0001-S0002-second.md').write_text('# Second\n')
(feature / 'ongoing/F0001-S0003-old.md').write_text('# Old\n')
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
for s in result.snapshots:
    print(s.id, s.branch, s.branch_commit is not None, s.document.state.stage, s.document.state.attempts)
print([item.detail for item in result.v1_items])
"
```
Expect: three lines. The first two are `F0001-S0001 work-item/F0001-S0001 False intake 0` (no branch, so the first stage and attempts 0 although the file says `review` and 2) and `F0001-S0002 work-item/F0001-S0002 True tests 1` (read from its branch). The third is `['factory/features/F0001-demo/ongoing/F0001-S0003-old.md: a work item of v1 (folder ongoing)']`.

## Log (append only)

1. 2026-10-12 human: created.
