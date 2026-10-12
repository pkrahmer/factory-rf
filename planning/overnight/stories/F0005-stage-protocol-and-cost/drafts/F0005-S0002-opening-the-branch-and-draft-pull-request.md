# Opening the work item's branch and its draft pull request

## Assignment (as of log entry 1)

Build the preparation that runs before a stage is claimed. For a work item that was started and has no branch on the remote, create its branch from `origin/main` and build its first document: the initial state of the pipeline definition's first stage, the backlog file's own state fields and journal dropped (ST6.1), and journal entry 1 (`human`, `created`) written by code. For a work item that has a branch, reset the local branch to the remote's, merge `origin/main` into it and abort the merge on a conflict, so that the baseline of the undo (taken at the stage-start commit, S0003) comes after every preparation step. Also ensure the work item's draft pull request, reusing only an open one. Nothing is committed or pushed here: the claim of S0003 makes the first commit, which for a new branch is also the opening commit. Covers ST6.1; keeps kept things 2 (a branch and a pull request per work item), 3 (the remote is read, never a local branch) and 4 (each stage starts from the committed work item).

## Interface

`src/factory/application/opening.py`

```python
class PreparedWorkItem(BaseModel):
    work_item: WorkItemId
    branch: str
    path: str
    document: WorkItemDocument
    branch_existed: bool
    merge_conflict: bool

class WorkItemOpening:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def prepare(self, work_item: WorkItemId, path: str) -> PreparedWorkItem: ...
    def ensure_pull_request(
        self, work_item: WorkItemId, document: WorkItemDocument
    ) -> PullRequestView: ...
```

Types: `WorkItemDocument` from `factory.domain.work_item`, `PullRequestView` from `factory.domain.hosting`, `Boundaries` from `factory.application.boundaries`, `PipelineDefinition` from `factory.domain.pipeline_definition`. `PreparedWorkItem` is a frozen model that forbids unknown keys. `path` is the work item's repository-relative path under its feature's `in-progress/` folder; it is the same on `main` and on the work item's branch.

- `prepare` reads only remote-tracking refs and never fetches (the tick fetched before). It never commits and never pushes. When it returns, the checkout is on `branch` and its work tree is clean. `branch` is `branch_name(work_item)`.
- A work item whose branch `origin/<branch>` does not exist is new: the local branch is created at `origin/main` with `checkout(branch, start_point="origin/main")`; the text of `path` is read with `show_file("origin/main", path)`; an absent file raises `WorkItemFormatError` whose `path` is the given path. The document is `WorkItemDocument(state=initial_state(definition.first_stage()), body=<the specification's body>)`; everything the file's front matter carried is dropped; `append_entry` then adds `NewEntry(speaker="human", kind="created", text="created.", on=<today's date from Clock.now()>)`. `branch_existed` and `merge_conflict` are `False`.
- A work item whose branch exists: the local branch is reset to `origin/<branch>` with `checkout(branch, start_point="origin/<branch>")`, whatever a local branch of that name held; then `Git.merge("origin/main")` runs. On the outcome `"conflict"` (already aborted by the wrapper) `merge_conflict` is `True`. The document is read from the work tree with `WorkItemReader.read` after the merge. `branch_existed` is `True`.
- `ensure_pull_request` returns the pull request in `document.state.pull_request` when it is open; otherwise the open pull request of the branch from `find_open_pull_request`; otherwise a new draft made by `create_pull_request(branch, f"{work_item}: {title}", document.body, draft=True)`. A pull request that is closed or merged is never reused. It does not change the document or the files.
- The title is `title(document.body)`; a body without a title line raises `WorkItemFormatError` with `fault` `the work item has no title line`.
- A `HostingServiceError` from the hosting service propagates unchanged.

Tests: `tests/application/test_opening.py`. It uses the `remote`, `checkout`, `human`, `hosting`, `clock` and `boundaries` fixtures; backlog files are written with `human.push_file` and started with `human.start`.

## Acceptance criteria

1. `prepare` for a started work item without a remote branch leaves the checkout on `work-item/<id>` with its head equal to the head of `origin/main`, sets `branch_existed` and `merge_conflict` to `False`, pushes nothing (`origin/work-item/<id>` still does not exist) and leaves the work tree clean.
2. The new document's state equals `initial_state(first stage)`, where the first stage is the first key of the pipeline definition's `stages`.
3. A backlog file whose front matter says `stage: doing`, `attempts: 1`, `blocked: question` and carries a `journal` list gives a document whose state is the initial state; the writer's rendering of the document contains none of those values.
4. The new document's journal has exactly one record, number 1, speaker `human`, kind `created`, and the writer's rendering of the document shows the line `1. 2026-10-12 human: created.` for the fixture clock.
5. `prepare` raises `WorkItemFormatError` with `path` equal to the given path when the file is absent at `origin/main`.
6. For a work item with a branch on the remote, `branch_existed` is `True` and the document is read from the branch: a branch whose file says `stage: doing` and `round: 1` gives that state.
7. A stale local branch of the same name, with a commit that exists only locally, is replaced: after `prepare` that commit is not in the work tree and the local head equals the head of `origin/<branch>`, which includes a file the human pushed to that branch after the last prepare.
8. A file the human added on `main` after the branch was opened is in the work tree after `prepare` (`origin/main` is merged in) and `merge_conflict` is `False`.
9. When `origin/main` and the branch changed the same line of the same file, `prepare` sets `merge_conflict` to `True`, leaves the work tree clean, leaves the head equal to the head of `origin/<branch>` (the merge is aborted) and returns the branch's document.
10. `ensure_pull_request` for a document without a pull request number and a branch without a pull request creates one draft, titled `<id>: <title>`, with the document's body as its description, of the work item's branch; the fake holds exactly one pull request.
11. `ensure_pull_request` returns the open pull request of the branch when one exists and creates no second one.
12. `ensure_pull_request` returns the pull request whose number is in `document.state.pull_request` when that one is open, and creates none.
13. A pull request that the human closed is not reused: with its number in `document.state.pull_request`, `ensure_pull_request` creates a new draft whose number differs.
14. A document whose body has no title line makes `ensure_pull_request` raise `WorkItemFormatError`, and no pull request is created.
15. A `HostingServiceError` raised by the hosting service during `ensure_pull_request` (armed with `fail_next("create_pull_request")`) propagates unchanged.
16. `make check` stays green.
17. docs: `docs/project-guide.md` explains how a started work item is opened (branch from `origin/main`, initial state, entry 1, the backlog file's own front matter ignored, the `## Journal` section of a backlog story left empty) and that only an open pull request is reused.

## Demo

```bash
uv run pytest tests/application/test_opening.py
```
Expect: the last line reports `passed` and the output contains neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
