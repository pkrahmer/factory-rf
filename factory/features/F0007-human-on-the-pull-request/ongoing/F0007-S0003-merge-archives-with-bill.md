---
stage: doing
pr: 84
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A merge archives the story with its bill

## Assignment (as of log entry 1)

Build the handler of `merged` events for stories. When the human merges a story's pull request, whatever stage the story has reached, the handler archives it on the main branch: the story file moves from `in-progress/` to `done/` (its cost record file with it), its state becomes `done` with no wait and no claim, a `done` entry is added to its journal that carries the bill computed from the cost records, and the work item's branch is deleted, locally and on the remote, after the archive is pushed. The handler trusts the event and posts nothing. The story also builds `destination_path`, the one function that maps a work item path to the same file in another lifecycle folder, which S0004 reuses. It keeps kept thing 2 (a merge accepts the story as it is) and kept thing 20 (the bill is written into the journal at the archive). Acceptances are F0009's and are not handled here. No morning observation.

## Interface

`src/factory/domain/archive.py`

```python
def destination_path(path: str, folder: LifecycleFolder) -> str: ...
```

`src/factory/domain/post_texts.py` (adds one function)

```python
def done_entry_text(bill: Bill) -> str: ...
```

`src/factory/application/handlers/merged.py`

```python
class MergedHandler(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `destination_path(path, folder)` returns the same file name in the folder `folder` of the same feature directory (`factory/features/F0001-slug/in-progress/F0001-S0001-x.md` becomes `factory/features/F0001-slug/done/F0001-S0001-x.md`). A path that `folder_of` places in no lifecycle folder raises `ValueError`.
- `done_entry_text(bill)` is `done (pull request merged); cost: ` followed by `cost_line(bill)`.
- `handle` takes `target_of(event)`. It calls `WorkItemRecorder.check_out(MAIN_BRANCH)`, so it works on the remote's main branch, and reads the story at `snapshot.path`. The bill is `bill(records)` of the records that `CostRecordReader.read` returns for `cost_records_path(snapshot.path)`; a missing record file gives no records.
- The archived document has `stage == "done"` (the constant `DONE_STAGE`), `blocked` unset and `claim` unset; every other state field is as it was. The claim is dropped by setting the field to `None` in the state, not through `ClaimService.release`, because that service is built for an instance name and a pipeline definition that this handler does not hold (`MergedHandler(boundaries)`); `tests/test_claim_ownership.py` forbids only building a claim and judging a lease outside the service. One journal entry is appended: `NewEntry(speaker=FACTORY, kind="done", text=done_entry_text(<the bill>))`.
- The story file is moved with `Git.move(snapshot.path, destination_path(snapshot.path, "done"))`, and its cost record file the same way when it exists at `HEAD`; the document is written at the new path. The commit has the subject `commit_subject(id, "merged, archived")` and is pushed with `WorkItemRecorder.publish(MAIN_BRANCH, ...)`; a push that is not `pushed` raises `PushFailed`.
- After the archive is pushed, the branch is deleted: `Git.delete_remote_branch(snapshot.branch)` and then `Git.delete_branch(snapshot.branch)`. A branch that is already gone is not an error: F0001's `delete_remote_branch` counts it as `"pushed"` and clears the stale `origin/<branch>`, and `delete_branch` ignores a missing branch. Any outcome of `delete_remote_branch` other than `"pushed"` (`"rejected"`, `"unreachable"`) raises `PushFailed(branch, outcome)`; the archive stays pushed, no event is raised for the story again (it is under `done/`), and the branch is left as after a kill (decision 6 of the feature).
- The handler posts nothing and does not touch the pull request.

Tests: `tests/domain/test_archive.py`, `tests/domain/test_archive_texts.py` (a new file: `tests/domain/test_post_texts.py` is F0003-S0003's) and `tests/application/handlers/test_merged.py`. The tests set a story up on a work item branch with `human`, merge it with `human.merge(branch, "merge")`, and read `origin/main` afterwards; the rejected deletion is made by setting `receive.denyDeletes` to `true` in the bare remote's configuration.

## Acceptance criteria

1. `destination_path("factory/features/F0001-todo/in-progress/F0001-S0001-x.md", "done")` is `factory/features/F0001-todo/done/F0001-S0001-x.md`, and with `"backlog"` it is the same file name in `backlog/`.
2. `destination_path` raises `ValueError` for a path that is in no lifecycle folder.
3. `done_entry_text(bill)` starts with `done (pull request merged); cost: ` and ends with `cost_line(bill)`.
4. After `MergedHandler.handle`, the story is on `origin/main` under `done/` with its file name, and no longer under `in-progress/`.
5. In the archived file `stage` is `done`, `blocked` is unset and `claim` is unset (a story merged while it held a claim included), and `round`, `attempts`, `crashes`, `pull_request`, `comments_read`, `handed_over` and the old journal records are as they were.
6. A story merged while it was at `tests`, at `doing` and at `approval` is archived the same way (three cases, one test).
7. The archived journal gains one entry numbered after the last: speaker `factory`, kind `done`, text `done_entry_text(bill(records))`, with a matching record in `state.journal`.
8. The bill in that entry counts every record of the story's cost record file: a file with three records, one of them with `end_reason == "died"` and one with an unknown cost, gives an entry text equal to `done_entry_text` of the bill of those three.
9. The cost record file moves beside the archived story under `done/`, and none is left under `in-progress/`.
10. A story with no cost record file is archived, and its entry text is `done_entry_text(bill([]))`.
11. After the archive is pushed, the branch `work-item/<id>` no longer exists on the remote or in the checkout.
12. A story whose branch is already gone from the remote (the hosting service deleted it) is archived without an error.
13. A kill at `before-push` leaves `origin/main` and the branch as they were, and handling the event again archives the story once.
14. A kill at `after-push` leaves the archive on `origin/main` and the branch still on the remote: the branch is deleted only after the archive is pushed.
15. When the remote's main branch moved since the checkout (the human pushed to it), `handle` raises `PushFailed` with outcome `rejected`, and the branch is not deleted.
16. A merge posts nothing: the pull request has no factory post afterwards.
17. When the remote refuses the deletion of the branch (`receive.denyDeletes` set in the bare remote), `handle` raises `PushFailed` with outcome `rejected` after the archive is pushed: `origin/main` holds the archive and the branch is still on the remote.
18. make check stays green.
19. docs: `docs/operator-guide.md` says that a merge, by any method, archives the story at whatever stage it has reached, writes its bill into the journal, moves its cost records beside it and deletes its branch, and what to do about a branch that a kill or a refused deletion left behind.

## Demo

```bash
uv run python -c "
from factory.domain.archive import destination_path
from factory.domain.bills import bill
from factory.domain.post_texts import done_entry_text
path = 'factory/features/F0001-todo/in-progress/F0001-S0001-model.md'
print(destination_path(path, 'done'))
print(destination_path(path, 'backlog'))
print(done_entry_text(bill([])).startswith('done (pull request merged); cost: '))
try:
    destination_path('README.md', 'done')
except ValueError:
    print('ValueError')
"
```
Expect: four lines: `factory/features/F0001-todo/done/F0001-S0001-model.md`, then `factory/features/F0001-todo/backlog/F0001-S0001-model.md`, then `True`, then `ValueError`.

```bash
uv run python -c "
import subprocess, tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.git_cli import GitCli
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.handlers.merged import MergedHandler
from factory.domain.agent_runs import TokenCounts
from factory.domain.cost_records import CostRecord
from factory.domain.events import Event
from factory.domain.journal import JournalRecord
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
sidecar = 'factory/features/F0001-todo/in-progress/F0001-S0001-model.costs.jsonl'
(human / story).parent.mkdir(parents=True)
(human / story).write_text('# Model\n\nThe human wrote this.\n')
git(human, 'add', '-A')
git(human, 'commit', '-m', 'start')
git(human, 'push', 'origin', 'main')
git(human, 'checkout', '-b', 'work-item/F0001-S0001')
state = WorkItemState(stage='approval', pull_request=1, journal=[JournalRecord(number=1, speaker='human', kind='created')])
body = '# Model\n\n## Journal\n\n1. 2026-10-12 human: created.\n'
(human / story).write_text(FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body=body)))
record = CostRecord(run='a' * 32, work_item='F0001-S0001', stage='doing', role='coder', attempt=0, status='completed', started_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC), duration_seconds=60.0, end_reason='completed', turns=3, tokens=TokenCounts(input=10, output=5), cost_usd=Decimal('0.5'))
(human / sidecar).write_text(JsonLinesCostRecordWriter().render([record]))
git(human, 'add', '-A')
git(human, 'commit', '-m', 'stage result')
git(human, 'push', 'origin', 'work-item/F0001-S0001')
head = git(human, 'rev-parse', 'HEAD')
git(human, 'checkout', 'main')
git(human, 'merge', '--no-ff', '-m', 'merge', 'work-item/F0001-S0001')
git(human, 'push', 'origin', 'main')
factory = root / 'factory'
checkout = GitCli(factory)
checkout.clone(str(root / 'origin.git'))
identify(factory)
snapshot = WorkItemSnapshot(id='F0001-S0001', path=story, folder='in-progress', branch='work-item/F0001-S0001', branch_commit=head, document=WorkItemDocument(state=state, body=body))
boundaries = SimpleNamespace(git=checkout, checkout=factory, work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(), cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(), hosting=None, clock=None)
MergedHandler(boundaries).handle(Event(kind='merged', work_item=snapshot, remote_state=head))
print(git(factory, 'ls-tree', '-r', '--name-only', 'origin/main'))
archived = FrontmatterWorkItemReader().parse(git(factory, 'show', 'origin/main:factory/features/F0001-todo/done/F0001-S0001-model.md'))
print(archived.state.stage, archived.state.blocked, [(r.number, r.speaker, r.kind) for r in archived.state.journal])
print('2. factory: done (pull request merged); cost: ' in archived.body)
print(git(root / 'origin.git', 'for-each-ref', '--format=%(refname:short)', 'refs/heads'))
"
```
Expect: the files on `origin/main` are exactly `factory/features/F0001-todo/done/F0001-S0001-model.costs.jsonl` and `factory/features/F0001-todo/done/F0001-S0001-model.md` (one per line); then `done None [(1, 'human', 'created'), (2, 'factory', 'done')]`; then `True`; then, as the last line, `main`: the work item branch is gone from the remote.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`domain/archive.py: destination_path`, `post_texts.done_entry_text`, `application/handlers/merged.py: MergedHandler(boundaries)` with `handle`). Its rules fix the git calls, the commit subject, the state changes and the order of push and branch deletion.
   - Criteria: each is testable by one test function. Every stated rule has a criterion for its failing side. `ValueError` for a path in no lifecycle folder is criterion 2. A push that is not `pushed` is criterion 15. A refused branch deletion is criterion 17. A missing cost record file is criterion 10. A branch already gone is criterion 12. The kills are criteria 13 and 14. The `done_entry_text` format is criterion 3, the bill content is criterion 8, and the "posts nothing" rule is criterion 16.
   - Demo: both blocks are runnable. Each `Expect:` line names exact output (the four lines, the file list, the stage and journal tuples, and `main` as the only branch left on the remote), so the output can be checked against it.
   - Architecture: the pure path function and text are in `domain`. The handler is in `application` and reaches git, readers and writers only through `Boundaries`. Dropping the claim by setting the field to `None` is allowed, per decision 22 and `tests/test_claim_ownership.py`.
   - Scope: this is within the feature's Merge item (feature decisions 5, 6, 8 and 22). It leaves out the acceptance's merge, which is F0009's, and the discard, which is S0004's. `destination_path` is built here for S0004 to reuse, as the feature plans.
3. tester: wrote red tests for criteria 1–17 against the Interface.
      - criterion 1: tests/domain/test_archive.py::test_the_destination_is_the_same_file_in_the_folder_of_the_same_feature (done and backlog)
      - criterion 2: tests/domain/test_archive.py::test_a_path_in_no_lifecycle_folder_has_no_destination (README.md, a feature.md, a non-lifecycle folder)
      - criterion 3: tests/domain/test_archive_texts.py::test_the_done_entry_names_the_merge_and_ends_with_the_cost_line (empty bill and a bill of three records)
      - criterion 4: tests/application/handlers/test_merged.py::test_the_merged_story_is_moved_under_done_on_main (also checks the one commit on main, subject `work item F0001-S0001: merged, archived`)
      - criterion 5: …::test_the_archived_state_is_done_unblocked_and_unclaimed_and_keeps_the_rest (blocked, claimed, round/attempts/crashes/comments_read/handed_over set, two old records)
      - criterion 6: …::test_a_story_is_archived_the_same_way_at_whatever_stage_it_was_merged (tests, doing, approval)
      - criterion 7: …::test_the_archive_appends_one_done_entry_of_the_factory_with_the_bill
      - criterion 8: …::test_the_bill_counts_every_record_whatever_its_end_and_known_cost
      - criterion 9: …::test_the_cost_records_move_beside_the_archived_story
      - criterion 10: …::test_a_story_without_cost_records_is_archived_with_an_empty_bill
      - criterion 11: …::test_after_the_archive_the_branch_is_gone_from_the_remote_and_the_checkout (the local branch is checked out before handling, so its deletion is observable)
      - criterion 12: …::test_a_story_whose_branch_is_already_gone_is_archived_without_an_error (the human deletes the remote branch after the merge)
      - criterion 13: …::test_a_kill_before_the_push_changes_nothing_and_a_second_run_archives_once
      - criterion 14: …::test_a_kill_after_the_archive_is_pushed_leaves_the_branch_on_the_remote
      - criterion 15: …::test_a_main_moved_since_the_checkout_rejects_the_archive_and_keeps_the_branch
      - criterion 16: …::test_a_merge_posts_nothing_on_the_pull_request
      - criterion 17: …::test_a_refused_branch_deletion_fails_after_the_archive_is_pushed (receive.denyDeletes in the bare remote; asserts PushFailed.branch == work-item/F0001-S0001 and outcome rejected)
      Setup: a `merge` fixture in test_merged.py starts the seeded backlog story with `human.start` and pushes the state (and optionally a cost record file from `bill_support`) to the work item branch. It merges with `human.merge(branch, "merge")`, then fetches the checkout. Results are read from `origin/main` and the bare remote. It uses the `pull_request` fixture from tests/application/handlers/conftest.py.
      Files created: tests/domain/test_archive.py, tests/domain/test_archive_texts.py, tests/application/handlers/test_merged.py.
      `make test`: 3 collection errors, as intended. The modules `factory.domain.archive` and `factory.application.handlers.merged` do not exist, and `factory.domain.post_texts` has no `done_entry_text`. `make lint` is green. Type check skipped as the stage says.
      No criterion needed interpretation. Not tested: whether a story without a cost record file gets one under `done/`. The criteria leave this open.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
