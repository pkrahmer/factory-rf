---
stage: accept
pr: 85
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A close before the approval discards the story

## Assignment (as of log entry 1)

Build the discard, the first half of the handler of `closed` events. When the human closes a story's pull request while the story is at any stage that is not an approval, the human has said that they do not want this version: the handler moves the story back from `in-progress/` to `backlog/` on the main branch, with the human's text exactly as the human wrote it, then deletes the work item's branch (and with it the branch's journal and cost records), and posts nothing; the pull request stays closed. A story started again therefore starts with an empty bill. The close at an approval stage is the send-back of S0005 and is not specified here. It covers GH4.3 and keeps kept thing 2 (a discard returns the human's text untouched). Acceptances are F0009's. No morning observation.

## Interface

`src/factory/application/handlers/closed.py`

```python
class ClosedHandler(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `handle` takes `target_of(event)`. When the stage `target.state.stage` is not an approval stage of `definition` (`definition.stages[stage].approval` is false), it discards the story. What it does at an approval stage is S0005's and is not specified here.
- The discard calls `WorkItemRecorder.check_out(MAIN_BRANCH)`, moves the story with `Git.move(snapshot.path, destination_path(snapshot.path, "backlog"))`, and publishes with the subject `commit_subject(id, "closed before the approval, back in the backlog")` through `WorkItemRecorder.publish(MAIN_BRANCH, ...)`. The file is moved and not rewritten, so its text is the one on `origin/main`, which is the human's. A push that is not `pushed` raises `PushFailed`.
- After the move is pushed, the branch is deleted: `Git.delete_remote_branch(snapshot.branch)` and then `Git.delete_branch(snapshot.branch)`. A branch that is already gone is not an error: F0001's `delete_remote_branch` counts it as `"pushed"` and clears the stale `origin/<branch>`, and `delete_branch` ignores a missing branch. Any outcome of `delete_remote_branch` other than `"pushed"` (`"rejected"`, `"unreachable"`) raises `PushFailed(branch, outcome)`; the move stays pushed, the story is no longer in `in-progress/`, so no event is raised for it again, and the branch is left as after a kill (decision 8 of the feature).
- The handler makes no call to the hosting service: it posts nothing and does not touch the pull request.

Tests: `tests/application/handlers/test_closed.py`. The tests start a story with `human.start`, put a work item branch with a state and a cost record file beside it on the remote with `human.push_file`, close the pull request in the fake with `close_by_human`, and read `origin/main` afterwards; the rejected deletion is made by setting `receive.denyDeletes` to `true` in the bare remote's configuration.

## Acceptance criteria

1. With the story at stage `doing`, after `ClosedHandler.handle` it is on `origin/main` under `backlog/` with its file name, and no longer under `in-progress/`.
2. The file under `backlog/` is identical, byte for byte, to the text the story had on `origin/main` before the close, whatever the branch held.
3. A story at each of the stages `intake`, `tests`, `review`, `docs` and `smoke-test` is discarded the same way (five cases, one test).
4. The discard commit changes only that story: with the checkout at the discard commit, `Git.changed_paths(<the commit before it>)` lists exactly one deleted path (under `in-progress/`) and one added path (under `backlog/`), and no other.
5. After the move is pushed, the branch `work-item/<id>` no longer exists on the remote or in the checkout.
6. After a discard and a new start by the human (`human.start` on the file under `backlog/`) and a fetch, no cost record file of the story exists on `origin/main`, no remote branch of the story exists, and `BillService(boundaries.git, boundaries.cost_reader).for_work_item(<id>)` (F0005-S0009) is a bill whose `total.runs` is 0 (GH4.3).
7. A story whose branch is already gone from the remote is discarded without an error.
8. A kill at `before-push` leaves `origin/main` and the branch as they were, and handling the event again discards the story once.
9. A kill at `after-push` leaves the story under `backlog/` on `origin/main` and the branch still on the remote: the branch is deleted only after the move is pushed.
10. When the remote's main branch moved since the checkout (the human pushed to it), `handle` raises `PushFailed` with outcome `rejected`, and the branch is not deleted.
11. A discard posts nothing, and the pull request is still `closed` afterwards.
12. When the remote refuses the deletion of the branch (`receive.denyDeletes` set in the bare remote), `handle` raises `PushFailed` with outcome `rejected` after the move is pushed: `origin/main` holds the story under `backlog/` and the branch is still on the remote.
13. make check stays green.
14. docs: `docs/operator-guide.md` says what a close before the approval does (the story returns to the backlog as the human wrote it, its branch and its bill are deleted, nothing is posted, the pull request stays closed) and that a branch left behind by a kill or a refused deletion must be deleted by hand before the story is started again.

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
2. intake: accepted
   - Interface: `ClosedHandler(Handler)` in `src/factory/application/handlers/closed.py` has a constructor and `handle`. The Git and recorder calls (`check_out`, `move`, `publish`, `delete_remote_branch`, `delete_branch`, `destination_path`, `commit_subject`) are named. The order is stated: the move is pushed first, then the remote branch is deleted, then the local one.
   - Criteria: each one is testable by one test function. The Interface rules and their failing sides are covered:
     - A push that is not `pushed` raises `PushFailed`: criterion 10, with the branch kept.
     - A refused branch deletion raises `PushFailed`: criterion 12, via `receive.denyDeletes`.
     - A branch that is already gone is not an error: criterion 7.
     - No hosting-service call: criterion 11.
     - The kill points: criteria 8 and 9.
     - The unreachable outcome of `delete_remote_branch` has no criterion of its own. It takes the same path as `rejected`, so I did not make it a question.
     - The approval-stage close is S0005's and is excluded.
   - Demo: the Python block is runnable and self-contained. Its `Expect:` line is checkable: the first line is the backlog path, then the human's text, and the last line is `main`.
   - Architecture: the handler sits in `factory.application` and uses only the Git and recorder boundaries. It makes no hosting call and has no layer violation.
   - Scope: this is decision 7 of FEATURE.md, the discard in its Scope list. The approval-stage close and the acceptance are excluded. Decision 21, the leftover branch when the human starts the story again, is flagged in FEATURE.md for the human and is not an intake finding.
3. tester: wrote the red tests for `ClosedHandler` in a new file, `tests/application/handlers/test_closed.py`. It is modelled on `test_merged.py` and uses the shared handler fixtures (`pull_request`, `boundaries`, `human`, `checkout`). The `close` fixture does five things: starts the story with `human.start`, pushes a state at the given stage to `work-item/F0001-S0001` with a different body, pushes a cost record file beside it, closes the pull request with `close_by_human`, and fetches. The definition is `boundaries.pipeline_reader.parse(PIPELINE_YAML)`.

   Criteria mapped to tests:
   - criterion 1: tests/application/handlers/test_closed.py::test_a_story_closed_at_doing_is_moved_back_under_backlog_on_main. It also checks the commit subject from the Interface.
   - criterion 2: tests/application/handlers/test_closed.py::test_the_discarded_story_keeps_the_text_main_held_whatever_the_branch_held
   - criterion 3: tests/application/handlers/test_closed.py::test_a_story_closed_at_any_stage_before_the_approval_is_discarded_the_same_way, parametrized over intake, tests, review, docs and smoke-test.
   - criterion 4: tests/application/handlers/test_closed.py::test_the_discard_commit_moves_only_that_story. It fetches, does `reset_to("origin/main")`, then calls `changed_paths(<main before>)`. The expected result is exactly [backlog path added, in-progress path deleted].
   - criterion 5: tests/application/handlers/test_closed.py::test_after_the_discard_the_branch_is_gone_from_the_remote_and_the_checkout
   - criterion 6: tests/application/handlers/test_closed.py::test_a_story_started_again_after_a_discard_has_an_empty_bill
   - criterion 7: tests/application/handlers/test_closed.py::test_a_story_whose_branch_is_already_gone_is_discarded_without_an_error
   - criterion 8: tests/application/handlers/test_closed.py::test_a_kill_before_the_push_changes_nothing_and_a_second_run_discards_once
   - criterion 9: tests/application/handlers/test_closed.py::test_a_kill_after_the_move_is_pushed_leaves_the_branch_on_the_remote
   - criterion 10: tests/application/handlers/test_closed.py::test_a_main_moved_since_the_checkout_rejects_the_discard_and_keeps_the_branch
   - criterion 11: tests/application/handlers/test_closed.py::test_a_discard_posts_nothing_and_leaves_the_pull_request_closed
   - criterion 12: tests/application/handlers/test_closed.py::test_a_refused_branch_deletion_fails_after_the_move_is_pushed, using `receive.denyDeletes` in the bare remote.
   - criteria 13 and 14 (`make check`, docs) have no tests in this stage.

   Files created: tests/application/handlers/test_closed.py.

   `make test` fails at collection, as expected: ModuleNotFoundError: No module named 'factory.application.handlers.closed'. That is the only module the runner could not import. `make lint` is green.

   Left out on purpose:
   - The close at an approval stage, which is S0005's.
   - The `unreachable` outcome of `delete_remote_branch`. No criterion names it, and the intake judged it the same path as `rejected`.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: built `ClosedHandler` in `src/factory/application/handlers/closed.py`. All 16 tests in `tests/application/handlers/test_closed.py` pass, and `make check` is green (total coverage 99.24 %).

   What it does:
   - `handle` takes `target_of(event)`.
   - When `definition.stages[stage].approval` is false, it discards the story:
     - `WorkItemRecorder.check_out(MAIN_BRANCH)`.
     - `Git.move(path, destination_path(path, "backlog"))`. The file is moved, not rewritten, so the text in the backlog is the human's text from main.
     - `recorder.publish(MAIN_BRANCH, commit_subject(id, "closed before the approval, back in the backlog"))`. `publish` raises `PushFailed` itself on a push that is not `pushed`.
     - Then the branch is deleted, the remote branch first and then the local one.
   - It makes no hosting-service call.

   Commits:
   - 1675721 feat: the handler.
   - 2c6c0de refactor: the "delete the remote branch, raise `PushFailed` unless `pushed`, then delete the local branch" sequence was identical in `MergedHandler`. It is now `WorkItemRecorder.delete_branch(branch)` in `src/factory/application/handlers/recording.py`, and both handlers call it. Behaviour is unchanged.

   Design decision: at an approval stage, `handle` returns without doing anything. That path belongs to S0005, and an early return leaves it a single place to fill in. I rejected raising `CannotHandle` there, because that would invent behaviour this story does not specify.

   Open:
   - Line 26 of `closed.py` (that approval-stage return) is the one uncovered line in the file (92 %). S0005's tests will cover it.
   - The `unreachable` outcome of the branch deletion takes the same `PushFailed` path as `rejected`, as intake noted. It has no test of its own.
   - Nothing else noticed.

   `make check`: check: green
5. reviewer: no findings.
      - Acceptance criteria: each of criteria 1–12 has a test in `tests/application/handlers/test_closed.py`, and each test checks the criterion it is named after.
        - Criterion 2 compares the backlog file with main's text from before the close, while the branch holds a different body.
        - Criterion 3 covers all five stages, and each one is a non-approval stage in `PIPELINE_YAML`.
        - Criterion 4 checks the exact list of `ChangedPath`.
        - Criterion 5 checks the remote ref, the local ref and `origin/<branch>`.
        - Criterion 8 checks that a second run makes exactly one commit.
        - Criteria 10 and 12 test the failing sides of the push rules: main rejected with the branch kept, and the deletion refused after the move.
        - The coder's entry says `make check` was green.
        - The `unreachable` outcome of `delete_remote_branch` has no test. It goes through the same `outcome != "pushed"` branch as `rejected`, which is tested. Intake and tester already recorded this, so it is not a gap in the story.
      - Architecture: `src/factory/application/handlers/closed.py` imports only from `factory.application` and `factory.domain`. It makes no call to the hosting service and none to a tool.
      - Security: none of the checklist's issues are present. No suppression markers.
      - Quality: commit 2c6c0de pulls the remote-then-local branch deletion that `MergedHandler` duplicated into `WorkItemRecorder.delete_branch` (`src/factory/application/handlers/recording.py`). Behaviour is the same, and it leaves no dead imports in `merged.py`. The docstrings are present and accurate. The early return at an approval stage (`closed.py`) is the one uncovered line. It is the place S0005 fills in, its comment says why, and this story specifies no behaviour there. I accepted it rather than ask for an invented error.
      - Ticket hygiene: the log gives the main decision (approval-stage return, `CannotHandle` rejected) and the refactor. `Assignment` matches the code. The docs criterion (criterion 14) still says what the operator must know.
6. documenter: wrote the documentation for the close-before-approval discard; no findings. `make check` is green.

   Files changed:
   - `docs/operator-guide.md`: new section "A close before the approval discards the story".
     - What the handler does: the story is moved back to `backlog/` as the human wrote it, the branch and its bill are deleted, nothing is posted, and the pull request stays closed.
     - The handler is not registered yet.
     - It lists the failure cases: a rejected push, a kill before the push, and a kill after the push or a refused deletion.
     - A branch left behind must be deleted by hand before the story is started again. This is the criterion 14 text.
   - `docs/project-guide.md`:
     - New section on `ClosedHandler`, in order, including the early return at an approval stage.
     - `WorkItemRecorder.delete_branch` added to the recorder description. The merged and closed handlers share it.
     - The "F0007-S0004 reuses it" note now points at the new section.

   Cross-read and found current: README (it doesn't mention handlers), the existing "A merge archives the story" section, the `NOT_YET_HANDLED` lists in both guides (`closed` is still unregistered, so they are still true), and the rest of the operator guide.

   I did not run the ticket's demo script.

   Stale but not touched: none seen.

   `make check`: check: green
7. demo: ran the one command under `## Demo` from the repository root, exactly as written. It exited 0. There are no findings.

   Command 1 (the `uv run python -c` script: a story at `doing` on main, a work item branch with a different body, then `ClosedHandler.handle` on a `closed` event):

   ```
   factory/features/F0001-todo/backlog/F0001-S0001-model.md
   # Model

   The human wrote this.
   main
   ```

   This meets its `Expect:` line on all three points:
   - The first line is exactly the path under `backlog/`. It is the only file on `origin/main`, so nothing is left under `in-progress/`.
   - The file's text is `# Model`, an empty line, then `The human wrote this.`. That is the human's text from main, not the branch's `worked on by the factory`.
   - The last line is `main`, so `work-item/F0001-S0001` is gone from the remote.

   Checked against the acceptance criteria:
   - The demo agrees with criteria 1, 2 and 5 (the remote side).
   - It agrees with criterion 11: the demo passes `hosting=None`, and the handler ran without error, so it made no call to the hosting service.
   - It contradicts no other criterion. Criteria 3, 4 and 6–10 and 12 are not exercised by the demo. The tests the reviewer checked in `tests/application/handlers/test_closed.py` cover them.

   Open: none.
