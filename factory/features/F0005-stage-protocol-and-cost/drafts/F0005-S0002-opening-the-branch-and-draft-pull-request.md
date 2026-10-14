# Opening the work item's branch and its draft pull request

## Assignment (as of log entry 1)

Build the preparation that runs before a stage is claimed. For a work item that was started and has no branch on the remote, create its branch from `origin/main` and build its first document: the initial state of the pipeline definition's first stage, the backlog file's own state fields and journal dropped (ST6.1), and journal entry 1 (`human`, `created`) written by code. For a work item that has a branch, reset the local branch to the remote's, merge `origin/main` into it and abort the merge on a conflict, so that the baseline of the undo (taken at the stage-start commit, S0003) comes after every preparation step. Also ensure the work item's draft pull request, reusing only an open one. Nothing is committed or pushed here: the claim of S0003 makes the first commit, which for a new branch is also the opening commit. Covers ST6.1 (the opening; F0006-S0001 uses it); keeps kept things 2 (a branch and a pull request per work item), 3 (the remote is read, never a local branch) and 4 (each stage starts from the committed work item).

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

Types: `WorkItemDocument` from `factory.domain.work_item`, `PullRequestView` from `factory.domain.hosting`, `Boundaries` from `factory.application.boundaries`, `PipelineDefinition` from `factory.domain.pipeline_definition`. `PreparedWorkItem` is a frozen model that forbids unknown keys, which criterion 20 tests. `path` is the work item's repository-relative path under its feature's `in-progress/` folder; it is the same on `main` and on the work item's branch.

- `prepare` reads only remote-tracking refs and never fetches (the tick fetched before): a commit pushed after the last fetch is not in the work tree when it returns. It never commits and never pushes. When it returns, the checkout is on `branch` and its work tree is clean. `branch` is `branch_name(work_item)`.
- A work item whose branch `origin/<branch>` does not exist is new: the local branch is created at `origin/main` with `checkout(branch, start_point="origin/main")`; the text of `path` is read with `show_file("origin/main", path)`; an absent file raises `WorkItemFormatError` whose `path` is the given path. The document is `WorkItemDocument(state=initial_state(definition.first_stage()), body=<the specification's body>)`; everything the file's front matter carried is dropped. A body without a `## Journal` section gets an empty one: the body with its trailing newlines removed, then a blank line, the line `## Journal` (written with `factory.domain.sections.JOURNAL`) and a final newline. A body whose `## Journal` section already holds entries is left as it is; the entry numbers of the text and the one record of the state then disagree, which the story form check reports to intake (`check_story_form`, the journal data and the text). `append_entry` then adds `NewEntry(speaker="human", kind="created", text="created.", on=<today's date from Clock.now()>)`. `branch_existed` and `merge_conflict` are `False`.
- A work item whose branch exists: the local branch is reset to `origin/<branch>` with `checkout(branch, start_point="origin/<branch>")`, whatever a local branch of that name held; then `Git.merge("origin/main")` runs. On the outcome `"conflict"` (already aborted by the wrapper) `merge_conflict` is `True`. The document is read from the work tree with `WorkItemReader.read` after the merge. `branch_existed` is `True`.
- `ensure_pull_request` returns the pull request in `document.state.pull_request` when it is open; otherwise the open pull request of the branch from `find_open_pull_request`; otherwise a new draft made by `create_pull_request(branch, f"{work_item}: {title}", document.body, draft=True)`. A pull request that is closed or merged is never reused. It does not change the document or any file: the work tree is clean before and after.
- The title is `title(document.body)`; a body without a title line raises `WorkItemFormatError` with `fault` `the work item has no title line`.
- A `HostingServiceError` from the hosting service propagates unchanged.

Tests: `tests/application/test_opening.py`. It uses the `remote`, `checkout`, `human`, `hosting`, `clock` and `boundaries` fixtures; backlog files are written with `human.push_file` and started with `human.start`.

## Acceptance criteria

1. `prepare` for a started work item without a remote branch leaves the checkout on `work-item/<id>` with its head equal to the head of `origin/main`, sets `branch_existed` and `merge_conflict` to `False`, pushes nothing (`origin/work-item/<id>` still does not exist) and leaves the work tree clean.
2. The new document's state equals `initial_state(first stage)`, where the first stage is the first key of the pipeline definition's `stages`.
3. A backlog file whose front matter says `stage: doing`, `attempts: 1`, `blocked: question` and carries a `journal` list gives a document whose state is the initial state; the writer's rendering of the document contains neither `stage: doing`, `attempts: 1` nor `blocked: question`, and its journal list holds the one record of entry 1.
4. The new document's journal has exactly one record, number 1, speaker `human`, kind `created`, and the writer's rendering of the document shows the line `1. 2026-10-12 human: created.` for the fixture clock, under a `## Journal` section that the backlog story already had.
5. A backlog story without a `## Journal` section (the body `# First story\n`) gets one: the new document's body is exactly `# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n` (the text, a blank line, `## Journal`, a blank line and the entry).
6. A backlog story whose `## Journal` section already holds an entry (`1. 2026-10-10 human: created.`) is not refused: `prepare` returns a document whose state has one record, and `check_story_form(document, form, folder="in-progress")` reports `the journal data lists 1 entries but the text shows 2`.
7. `prepare` raises `WorkItemFormatError` with `path` equal to the given path when the file is absent at `origin/main`.
8. For a work item with a branch on the remote, `branch_existed` is `True` and the document is read from the branch: a branch whose file says `stage: doing` and `round: 1` gives that state.
9. A stale local branch of the same name, with a commit that exists only locally, is replaced: after `prepare` that commit is not in the work tree and the local head equals the head of `origin/<branch>`, which includes a file the human pushed to that branch after the last prepare.
10. A file the human added on `main` after the branch was opened is in the work tree after `prepare` (`origin/main` is merged in) and `merge_conflict` is `False`.
11. When `origin/main` and the branch changed the same line of the same file, `prepare` sets `merge_conflict` to `True`, leaves the work tree clean, leaves the head equal to the head of `origin/<branch>` (the merge is aborted) and returns the branch's document.
12. `prepare` never fetches: a file the human pushed to `main` after the checkout's last fetch is not in the work tree when `prepare` returns, and `origin/main` still resolves to the old commit.
13. `ensure_pull_request` for a document without a pull request number and a branch without a pull request creates one draft, titled `<id>: <title>`, with the document's body as its description, of the work item's branch; the fake holds exactly one pull request.
14. `ensure_pull_request` returns the open pull request of the branch when one exists and creates no second one.
15. `ensure_pull_request` returns the pull request whose number is in `document.state.pull_request` when that one is open, and creates none.
16. A pull request that the human closed, and one that was merged (`merge_by_human`; parametrised), is not reused: with its number in `document.state.pull_request`, `ensure_pull_request` creates a new draft whose number differs.
17. A document whose body has no title line makes `ensure_pull_request` raise `WorkItemFormatError` with fault `the work item has no title line`, and no pull request is created.
18. A `HostingServiceError` raised by the hosting service during `ensure_pull_request` (armed with `fail_next("create_pull_request")`) propagates unchanged.
19. `ensure_pull_request` changes no file: the work tree is clean and the work item file has the same bytes after the call as before it.
20. `PreparedWorkItem` is frozen and forbids unknown keys: assigning to `branch` (through `setattr`, the field's name in a variable) and building it with an unknown field both raise `ValidationError`.
21. make check stays green.
22. docs: `docs/project-guide.md` explains how a started work item is opened (branch from `origin/main`, initial state, entry 1, the backlog file's own front matter ignored, an empty `## Journal` section added when the story has none, entries already in it left for the form check) and that only an open pull request is reused; `docs/decisions.md` records that the local branch is reset to the remote's (R18), so v1's fast-forward stall does not exist.

## Demo

```bash
uv run pytest tests/application/test_opening.py
```
Expect: the last line reports `passed` and the output contains neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
