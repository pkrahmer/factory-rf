# A crash discards the stage and reruns it free

## Assignment (as of log entry 1)

Build the first half of crash recovery: `RecoveryHandler`, the handler of the `crash` event, which the watcher raises at its first look when the work item's claim is this instance's own (`ClaimService.status` is `own`), that is after a restart with the same instance name. The handler throws away everything the dead stage did that is not on the remote (uncommitted files, untracked files, local commits never pushed, and with them the cost records of the discarded agent runs), records the crash in one commit on top of the pushed stage-start commit (claim cleared, `crashes` + 1, `attempts` unchanged, a journal entry of kind `crash`), pushes it, and reruns the stage in the same call through the `run` handler it is given, so nothing waits for the lease or for an idle pause. An own crash posts nothing on the pull request. This replaces v1's recovery of a dirty tree, which committed the leftovers of a killed run with `git add -A`, and v1's expired run record, which charged the story an attempt. Covers GH2.1, GH2.2, GH2.3, GH1.3 (the same-name case here; the other-name case again in S0003), R23 and R24 (the discarded cost records); keeps kept thing 13 (recover by construction) and kept thing 14 (the crash, a fifth way not to move forward). The crash cap comes in S0002 and the expired lease of another instance in S0003, so every test of this story starts from `crashes` 0 under the pipeline definition's default crash cap of 2. The event is raised by the watcher (F0006-S0002) and registered in the dispatcher's mapping by the entry's wiring; this story builds neither.

## Interface

`src/factory/domain/recovery.py`

```python
def crashed(state: WorkItemState) -> WorkItemState: ...
def crash_entry_text(stage: str, crashes: int, stage_start: CommitId) -> str: ...
```

- `crashed` returns a copy of `state` with `crashes` one higher; every other field is as it was, the claim included (releasing the claim is `ClaimService.release`, not this function). The argument is not changed.
- `crash_entry_text` returns exactly `f"crash {crashes}: the run of stage {stage} ended without a result. Its work is discarded. Stage-start commit: {stage_start}."` (one line, `crashes` being the count after this crash).

`src/factory/application/recovery.py`

```python
class RecoveryHandler:  # a Handler (factory.application.dispatcher); this story handles "crash" events
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition,
                 claims: ClaimService, run: Handler) -> None: ...
    def handle(self, event: Event) -> None: ...
```

`handle` does these steps in this order:

1. Guards. It raises `CannotHandle(kind=event.kind, reason=...)`, before it touches the checkout or the remote, when `event.kind` is not `"crash"`, when `event.work_item` is `None`, or when `claims.status(state)` of the work item's state is anything but `"own"` (`"held"`: another name's claim within its lease; `"expired"`; `"none"`).
2. Discard. `boundaries.git.reset_to("HEAD")` (drops uncommitted and untracked changes), then `boundaries.git.checkout(branch, start_point=f"origin/{branch}")` (drops local commits that were never pushed), `branch` being `event.work_item.branch`. After this the work tree and the local branch equal the remote-tracking branch. Its head, `boundaries.git.resolve(f"origin/{branch}")`, is the stage-start commit: the factory pushes nothing to the work item's branch between a stage-start push and the stage's result push.
3. Record. A new document is built from the event's snapshot: `state` replaced by `crashed(state)`, then `claims.release(document)`, then `append_entry(document, NewEntry(speaker=FACTORY, kind="crash", text=crash_entry_text(state.stage, <the new crashes>, <stage-start commit>)))`. It is written with `boundaries.work_item_writer.write(boundaries.checkout / event.work_item.path, document)` and committed with `boundaries.git.commit(f"{id}: crash of stage {stage} recorded")` (free text, never parsed).
4. Push. `boundaries.git.push(branch)`; any outcome but `"pushed"` raises `PushFailed(branch=branch, outcome=<the outcome>)`.
5. Rerun. It calls `run.handle(Event(kind="run", work_item=<the snapshot with branch_commit set to the pushed commit and document set to the new document>, pull_request=event.pull_request, remote_state=<the pushed commit>))` once and returns.

- Nothing is posted on the pull request in any step.
- A `GitError` from the git wrapper, an exception from `run.handle` and `InjectedKill` leave `handle` unchanged and uncaught.
- The cost records of the dead stage are in the work tree only (R24), so step 2 removes them; records committed earlier are in the stage-start commit and stay.

Tests: `tests/domain/test_recovery.py` and `tests/application/test_recovery_crash.py`. The application tests build a claimed stage with the shared fixtures `remote`, `checkout`, `human`, `hosting`, `boundaries`, `clock` and `kill_points`: `human.start` moves a backlog story to `in-progress/`, the branch is checked out with `checkout.checkout(branch, start_point="origin/main")`, and `ClaimService(boundaries, "factory-1", definition).claim(...)` pushes the stage-start commit. The dead run is simulated by writing files in the work tree (and by `checkout.commit` without a push); the tests do not need an agent run. `run` is a plain class in the test module that implements `Handler` and appends each event to a list. A restart is a new `ClaimService` and a new `RecoveryHandler` built with the same instance name `factory-1`.

## Acceptance criteria

1. After a `crash` event is handled, no commit on any remote branch contains a file that the dead run wrote: for a file left uncommitted and untracked in the work tree and for a file committed locally and never pushed, `git.show_file(f"origin/{name}", path)` is `None` for every name in `git.remote_branches()`.
2. After the event is handled, the local checkout holds none of the dead run's writes either: `git.status().changes` is empty, the untracked file is gone from the disk, and the local work item branch resolves to the same commit as `origin/<branch>`.
3. The stage-start commit returned by `ClaimService.claim` is still an ancestor of `origin/<branch>` after the event is handled (`git.is_ancestor`), and the journal still holds its record of kind `started` with the same number and the same visible text (`entry_text`).
4. Between the stage-start commit and the new head of `origin/<branch>` the only changed path is the work item's own file, as `ChangedPath(path=<its path>, change="modified")` (`git.changed_paths`), also when the dead run left other files in the work tree.
5. In the pushed work item `crashes` is 1 where it was 0, `attempts` is unchanged (tested with attempts 0 and 1), `claim` is `None`, and `stage`, `blocked`, `round`, `pull_request`, `comments_read` and `handed_over` are unchanged.
6. The pushed journal data ends with a record of speaker `factory` and kind `crash` whose number is the previous last number plus one, and every earlier record is unchanged.
7. The visible text of the new entry, read with `entry_text(document, number)`, equals `crash_entry_text(stage, 1, stage_start.commit)`, where `stage_start.commit` is the commit returned by `ClaimService.claim`.
8. The crash commit is pushed: `git.resolve("origin/<branch>")` equals the local branch head, differs from the stage-start commit, and the work item read from `git.show_file` at it has `crashes` 1.
9. The cost records of the dead stage are gone and earlier ones stay: with a record of stage `intake` committed in the stage-start commit and an uncommitted `started` record of the dead stage added to the sidecar file, the sidecar file at `cost_records_path(path)` read with `JsonLinesCostRecordReader` holds exactly the `intake` record after the event is handled.
10. An own crash posts nothing: after the event is handled `hosting.factory_posts(number)` is empty and `hosting.pull_requests()` is unchanged, with the work item's pull request existing.
11. The stage reruns at the first look: the `run` handler is called exactly once, inside the same `handle` call and with the `ManualClock` still at the time of the claim (inside the lease, no wait), with an event of kind `"run"` whose work item has `crashes` 1, no claim, `branch_commit` equal to the pushed crash commit and `remote_state` equal to that commit; the same holds after a restart, that is with a new `ClaimService` and a new `RecoveryHandler` of the same instance name.
12. A claim of another instance name within its lease is not rerun: with a `RecoveryHandler` whose `ClaimService` is named `factory-2` and the clock at the time of the claim, a `crash` event raises `CannotHandle` with `kind == "crash"`, `origin/<branch>` is unchanged and the `run` handler is not called.
13. An event that is not a `crash` event, and a `crash` event without a work item, each raise `CannotHandle` before anything is touched: the remote head is unchanged and the dead run's untracked file is still on the disk (two cases).
14. A `crash` event for a work item whose state holds no claim raises `CannotHandle` and pushes nothing.
15. When the push of the crash commit is rejected, `handle` raises `PushFailed` with `outcome == "rejected"` and `branch` set, and the `run` handler is not called; the rejection is made by `human.push_file(branch, path, text)` after the snapshot was read.
16. A kill at the push is counted once: with `kill_points.arm(KillPoint.BEFORE_PUSH)` the first `handle` raises `InjectedKill` and leaves `origin/<branch>` at the stage-start commit; after a restart (a new handler of the same instance name) the second `handle` leaves `origin/<branch>` with `crashes` 1 and exactly one record of kind `crash`.
17. An exception from the `run` handler propagates out of `handle` unchanged, and the crash stays recorded: `origin/<branch>` holds `crashes` 1 and no claim.
18. `crashed` returns a state with `crashes` one higher and every other field equal, from `crashes` 0 and from `crashes` 5, and leaves its argument unchanged.
19. `make check` stays green.
20. docs: `docs/operator-guide.md` explains what a restart does to a stage that was running (the same instance name reruns it at its first look, the dead run's work is discarded, the journal gets a `crash` entry and `crashes` rises, no attempt is charged, nothing is posted); `docs/decisions.md` records that a crash is charged only to a held claim and that the rerun happens in the same call.

## Demo

The first command shows the pure part.

```bash
uv run python -c "
from factory.domain.recovery import crash_entry_text, crashed
from factory.domain.work_item import initial_state
before = initial_state('doing')
after = crashed(before)
print(before.crashes, after.crashes, after.attempts, after.stage)
print(crash_entry_text('doing', 1, 'a' * 40))
"
```
Expect: two lines. The first is `0 1 0 doing`. The second is `crash 1: the run of stage doing ended without a result. Its work is discarded. Stage-start commit: ` followed by forty letters `a` and a full stop.

The second command kills nothing but leaves a stage claimed with a file of the dead run in the work tree, then handles the `crash` event against a real local bare remote.

```bash
uv run python -c "
import subprocess, tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.clock import ManualClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.run_record_file import JsonRunRecordFile
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.recovery import RecoveryHandler
from factory.domain.events import Event
from factory.domain.journal import NewEntry, append_entry
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, initial_state
tmp = Path(tempfile.mkdtemp())
work = tmp / 'work'
def sh(*args, cwd=tmp):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)
sh('git', 'init', '--bare', '-b', 'main', 'remote.git')
sh('git', 'clone', 'remote.git', 'work')
sh('git', 'config', 'user.name', 'demo', cwd=work)
sh('git', 'config', 'user.email', 'demo@example.com', cwd=work)
sh('git', 'checkout', '-B', 'main', cwd=work)
rel = 'factory/features/F0001-demo/in-progress/F0001-S0001-demo.md'
doc = WorkItemDocument(state=initial_state('tests'), body='# Demo\n\n## Journal\n\n')
doc = append_entry(doc, NewEntry(speaker='human', kind='created', text='created.', on=date(2026, 10, 12)))
(work / rel).parent.mkdir(parents=True)
writer = FrontmatterWorkItemWriter()
writer.write(work / rel, doc)
sh('git', 'add', '-A', cwd=work)
sh('git', 'commit', '-m', 'start', cwd=work)
sh('git', 'push', 'origin', 'main', cwd=work)
git = GitCli(work)
branch = 'work-item/F0001-S0001'
git.checkout(branch, start_point='origin/main')
definition = PipelineDefinition(contract='1.0', roles={'tester': RoleDefinition(write_paths=['tests/*'])}, stages={'tests': StageDefinition(role='tester', next=['done']), 'done': StageDefinition()})
clock = ManualClock(datetime(2026, 10, 12, 12, 0, tzinfo=UTC))
boundaries = Boundaries(git=git, hosting=FakeHostingService(), agent_runtime=FakeAgentRuntime(), project_commands=MakeProjectCommands(work), work_item_reader=FrontmatterWorkItemReader(), work_item_writer=writer, cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(), clock=clock, log=TimestampedFactoryLog(tmp / 'factory.log', clock), health=JsonHealthStatusFile(tmp / 'health.json'), pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(tmp / 'agents'), run_record=JsonRunRecordFile(tmp / 'run-record.json'), checkout=work)
claims = ClaimService(boundaries, 'factory-1', definition)
start = claims.claim(branch, rel, doc, 'tests')
(work / 'src').mkdir()
(work / 'src' / 'dead.py').write_text('x = 1\n')
head = git.resolve('origin/' + branch)
reader = FrontmatterWorkItemReader()
snapshot = WorkItemSnapshot(id='F0001-S0001', path=rel, folder='in-progress', branch=branch, branch_commit=head, document=reader.parse(git.show_file('origin/' + branch, rel)))
class Rerun:
    def __init__(self):
        self.events = []
    def handle(self, event):
        self.events.append(event)
rerun = Rerun()
RecoveryHandler(boundaries, definition, claims, rerun).handle(Event(kind='crash', work_item=snapshot, remote_state=head))
after = reader.parse(git.show_file('origin/' + branch, rel))
print(after.state.crashes, after.state.attempts, after.state.claim is None)
print((work / 'src' / 'dead.py').exists())
print(len(rerun.events), rerun.events[0].kind, rerun.events[0].work_item.document.state.crashes)
print(git.is_ancestor(start.commit, 'origin/' + branch))
"
```
Expect: four lines, `1 0 True` (one crash counted, no attempt charged, claim cleared), `False` (the dead run's file is gone from the work tree), `1 run 1` (the stage is rerun once, with `crashes` 1), and `True` (the stage-start commit is still in the remote history).

## Log (append only)

1. 2026-10-12 human: created.
