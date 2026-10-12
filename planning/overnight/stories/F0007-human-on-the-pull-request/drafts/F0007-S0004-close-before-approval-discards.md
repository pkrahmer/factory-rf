# A close before the approval discards the story

## Assignment (as of log entry 1)

Build the discard, the first half of the handler of `closed` events. When the human closes a story's pull request while the story is at any stage that is not an approval, the human has said that they do not want this version: the handler moves the story back from `in-progress/` to `backlog/` on the main branch, with the human's text exactly as the human wrote it, then deletes the work item's branch (and with it the branch's journal and cost records), and posts nothing; the pull request stays closed. A story started again therefore starts with an empty bill. The close at an approval stage is the send-back of S0005 and is not specified here. It covers GH4.3 and keeps kept thing 2 (a discard returns the human's text untouched). Acceptances are F0009's. No morning observation.

## Interface

`src/factory/application/handlers/closed.py`

```python
class ClosedHandler:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `handle` takes `target_of(event)`. When the stage `target.state.stage` is not an approval stage of `definition` (`definition.stages[stage].approval` is false), it discards the story. What it does at an approval stage is S0005's and is not specified here.
- The discard calls `WorkItemRecorder.check_out(MAIN_BRANCH)`, moves the story with `Git.move(snapshot.path, destination_path(snapshot.path, "backlog"))`, and publishes with the subject `commit_subject(id, "closed before the approval, back in the backlog")` through `WorkItemRecorder.publish(MAIN_BRANCH, ...)`. The file is moved and not rewritten, so its text is the one on `origin/main`, which is the human's. A push that is not `pushed` raises `PushFailed`.
- After the move is pushed, the branch is deleted: `Git.delete_remote_branch(snapshot.branch)` when `origin/<branch>` resolves, and `Git.delete_branch(snapshot.branch)` when the local branch resolves. A branch that is already gone is not an error.
- The handler makes no call to the hosting service: it posts nothing and does not touch the pull request.

Tests: `tests/application/handlers/test_closed.py`. The tests start a story with `human.start`, put a work item branch with a state and a cost record file beside it on the remote with `human.push_file`, close the pull request in the fake with `close_by_human`, and read `origin/main` afterwards.

## Acceptance criteria

1. With the story at stage `doing`, after `ClosedHandler.handle` it is on `origin/main` under `backlog/` with its file name, and no longer under `in-progress/`.
2. The file under `backlog/` is identical, byte for byte, to the text the story had on `origin/main` before the close, whatever the branch held.
3. A story at each of the stages `intake`, `tests`, `review`, `docs` and `smoke-test` is discarded the same way (five cases, one test).
4. The discard commit changes only that story: `changed_paths` for it shows exactly one path deleted and one path added.
5. After the move is pushed, the branch `work-item/<id>` no longer exists on the remote or in the checkout.
6. After a discard and a new start by the human (`human.start` on the file under `backlog/`), no cost record file of the story exists on `origin/main`, and no remote branch of the story exists: the bill of the story is empty, `bill([]).runs == 0` (GH4.3).
7. A story whose branch is already gone from the remote is discarded without an error.
8. A kill at `before-push` leaves `origin/main` and the branch as they were, and handling the event again discards the story once.
9. A kill at `after-push` leaves the story under `backlog/` on `origin/main` and the branch still on the remote: the branch is deleted only after the move is pushed.
10. When the remote's main branch moved since the checkout (the human pushed to it), `handle` raises `PushFailed` with outcome `rejected`, and the branch is not deleted.
11. A discard posts nothing, and the pull request is still `closed` afterwards.
12. make check stays green.
13. docs: `docs/operator-guide.md` says what a close before the approval does (the story returns to the backlog as the human wrote it, its branch and its bill are deleted, nothing is posted, the pull request stays closed) and that a branch left behind by a kill must be deleted by hand before the story is started again; the other three documents do not change.

## Demo

```bash
uv run python -c "
import subprocess, tempfile
from pathlib import Path
from types import SimpleNamespace
from factory.adapters.git_cli import GitCli
from factory.application.handlers.closed import ClosedHandler
from factory.domain.events import Event
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState

def git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

def identify(cwd):
    git(cwd, 'config', 'user.name', 'demo')
    git(cwd, 'config', 'user.email', 'demo@example.invalid')

root = Path(tempfile.mkdtemp())
git(root, 'init', '--bare', '-b', 'main', 'origin.git')
git(root, 'clone', 'origin.git', 'human')
human = root / 'human'
identify(human)
git(human, 'symbolic-ref', 'HEAD', 'refs/heads/main')
story = 'factory/features/F0001-todo/in-progress/F0001-S0001-model.md'
(human / story).parent.mkdir(parents=True)
(human / story).write_text('# Model\n\nThe human wrote this.\n')
git(human, 'add', '-A')
git(human, 'commit', '-m', 'start')
git(human, 'push', 'origin', 'main')
git(human, 'checkout', '-b', 'work-item/F0001-S0001')
(human / story).write_text('worked on by the factory\n')
git(human, 'commit', '-am', 'stage result')
git(human, 'push', 'origin', 'work-item/F0001-S0001')
head = git(human, 'rev-parse', 'HEAD')
factory = root / 'factory'
checkout = GitCli(factory)
checkout.clone(str(root / 'origin.git'))
identify(factory)
definition = PipelineDefinition(contract='1.0', roles={'coder': {'write_paths': ['src/*']}}, stages={'doing': {'role': 'coder', 'next': ['approval']}, 'approval': {'approval': True, 'next': ['done', 'doing']}, 'done': {}})
document = WorkItemDocument(state=WorkItemState(stage='doing', pull_request=1), body='# Model\n')
snapshot = WorkItemSnapshot(id='F0001-S0001', path=story, folder='in-progress', branch='work-item/F0001-S0001', branch_commit=head, document=document)
boundaries = SimpleNamespace(git=checkout, checkout=factory, work_item_reader=None, work_item_writer=None, cost_reader=None, cost_writer=None, hosting=None, clock=None)
ClosedHandler(boundaries, definition).handle(Event(kind='closed', work_item=snapshot, remote_state=head))
print(git(factory, 'ls-tree', '-r', '--name-only', 'origin/main'))
print(git(factory, 'show', 'origin/main:factory/features/F0001-todo/backlog/F0001-S0001-model.md'))
print(git(root / 'origin.git', 'for-each-ref', '--format=%(refname:short)', 'refs/heads'))
"
```
Expect: the first line is exactly `factory/features/F0001-todo/backlog/F0001-S0001-model.md`; then the file's text, `# Model`, an empty line and `The human wrote this.` (the human's text, not `worked on by the factory`); then, as the last line, `main`: the work item branch is gone from the remote.

## Log (append only)

1. 2026-10-12 human: created.
