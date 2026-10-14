# An expired lease, and notes that say retrying only when true

## Assignment (as of log entry 1)

Teach `RecoveryHandler` the `expired` event and fix the wording of the notes. An instance with another name does not rerun a stage whose claim it finds; when the lease of that claim has run out (the claim's age is at least its `lease_duration`, 60 minutes by default, as `ClaimService.status` decides) the watcher raises `expired`, and the handler treats it as a crash of a holder that is gone: the same discard, the same single commit (claim cleared, `crashes` + 1, `attempts` unchanged) with a journal entry of kind `expiry`, then a note on the pull request, then the rerun by this instance, or at the crash cap the crash-cap question of S0002 after the note. This story also registers the handler for `expired` in `factory.entry.wiring.build_handlers`, the same `RecoveryHandler` instance as for `crash`, and removes `expired` from `NOT_YET_HANDLED` (questionnaire 1, Q20). This replaces v1's `expired` handler, which charged an attempt and posted "Retrying." even when the next tick asked the human instead. The note says "retrying" only where a rerun follows: the expiry note, and the stall note of F0005, are now tested at both sides of their cap, and a search test keeps the word out of every other string in the code. Covers ST1.4 (a note of a stall or an expiry says "retrying" only where the factory retries; a test at the cap shows a note without it) and GH1.3 (the other-name case: no rerun until the lease has expired, a rerun at its first look after); also R23 (the expiry counted as a crash, answer 1 of the skeleton); keeps kept thing 14. The decision which claims are held, own or expired is the watcher's (F0006-S0002) and the lease functions are F0004's; this story builds neither. The stall half of ST1.4 is built and tested by F0005-S0004; criterion 3 only traces it. A note whose post is lost is not posted again (decision 16 of the feature).

## Interface

`src/factory/domain/post_texts.py` (`expiry_note` is built here; `stall_note` was built by F0005-S0004, which tests it in `tests/domain/test_stall_texts.py`)

```python
def expiry_note(crashes: int, crash_cap: int) -> str: ...
def stall_note(reason: StallReason, attempts: int, attempts_cap: int, *, detail: str = "") -> str: ...
```

- `expiry_note` returns exactly `f"The run that held this stage ended without finishing: its lease expired (crash {crashes} of {crash_cap}). Retrying."` when `crashes < crash_cap`, and exactly `f"The run that held this stage ended without finishing: its lease expired (crash {crashes} of {crash_cap}). The factory does not rerun it and asks you instead."` otherwise.
- `stall_note` is not changed by this story: its signature is the built one above, and it contains the word "retrying" (any case) exactly when `attempts < attempts_cap`. Criterion 3 repeats F0005-S0004's test at both sides of the cap as the ST1.4 trace, so it is green before the coder starts.

`src/factory/domain/recovery.py` (added)

```python
def expiry_entry_text(stage: str, crashes: int, head: CommitId) -> str: ...
```

- It returns exactly `f"expiry {crashes}: the lease of stage {stage} ran out. Its work is discarded back to commit {head}."` (one line, `crashes` being the count after this expiry, `head` as in S0001's `crash_entry_text`).

`src/factory/application/recovery.py` (changed)

```python
class RecoveryHandler(Handler):
    def handle(self, event: Event) -> None: ...                       # steps 1, 3 and 5 change, step 4b is new
```

- Step 1 (guards) now accepts two kinds. For `"crash"` the claim status must be `"own"` as before. For `"expired"` it must be `"expired"` (`claims.status(state)`); `"own"`, `"held"` and `"none"` raise `CannotHandle(kind="expired", reason=...)` before anything is touched. Any other kind raises `CannotHandle`, and `target_of(event)` and the missing branch commit are guarded as in S0001.
- Step 2 (discard) and step 4 (push) are as in S0001. The record in step 3 for an `"expired"` event uses `NewEntry(speaker=FACTORY, kind="expiry", text=expiry_entry_text(state.stage, <the new crashes>, head))`; at the crash cap it carries the question entry of S0002 as well.
- Step 4b (new, only for `"expired"`, after the push): the note is posted through `StopService(boundaries).post(WorkItemStop(key=PostKey(work_item=<id>, kind="expiry", n=str(<the expiry record's number>)), branch=<branch>, title=f"{id}: {title(body)}" (just `id` when the body has no title), pull_request=<state.pull_request>, text=expiry_note(<the new crashes>, definition.crash_cap)))`. When `StopPosted.opened` is true the new pull request number is recorded in `state.pull_request`, committed and pushed, exactly as `ask_crash_cap` does it (S0002: `check_out`, `read`, set the number, `record` with the subject `commit_subject(id, "pull request opened")`; a rejected push raises `PushFailed`). A `HostingServiceError` propagates; the expiry stays recorded and pushed. A note whose post fails is not posted again (decision 16 of the feature).
- Step 5 (rerun or ask) follows step 4b: below the cap `run.handle` is called once as in S0001, at the cap `ask_crash_cap` is called as in S0002 and `run` is not. Both are given the snapshot with the document as last written, so the pull request number that step 4b recorded is in it and the question is posted on the same pull request without a second write of the number.
- A `"crash"` event still posts nothing.

`src/factory/entry/wiring.py` (grown by S0001)

```python
NOT_YET_HANDLED: tuple[EventKind, ...] = ("acceptance_due",)
```

- `build_handlers` also registers `expired`: its value is the very `RecoveryHandler` instance that is the value of `crash`. The constant loses `expired`. This story changes no test of an earlier story: S0001 made the wiring tests of F0006-S0007 and F0007-S0010 independent of the constant's value and of the exact key set.

Tests: `tests/domain/test_post_texts_notes.py`, `tests/domain/test_recovery_expiry_text.py`, `tests/test_retrying_wording.py` (a source search, outside the layers), `tests/application/test_recovery_expiry.py` and `tests/entry/test_wiring_recovery_expired.py` (a new file: `tests/entry/test_wiring_recovery.py` is S0001's). The application tests use S0001's setup (its Tests paragraph): the stage is claimed by `ClaimService(boundaries, "factory-1", definition)`, the recovery handler is built with `ClaimService(boundaries, "factory-2", definition)`, and `clock.advance(timedelta(minutes=60))` makes the claim expire; for the cap the work item's state has `crashes` 1 before the claim. A pull request exists unless a test says otherwise.

## Acceptance criteria

1. `expiry_note(1, 2)` equals the first text given in the Interface with those values and ends with `Retrying.`.
2. `expiry_note(2, 2)` and `expiry_note(3, 2)` equal the second text given in the Interface with those values, and neither contains the word "retrying" in any case.
3. `stall_note` contains "retrying" (any case) for `attempts` 1 with `attempts_cap` 2, and does not for `attempts` 2 and 3 with `attempts_cap` 2, for every `StallReason` (parametrized).
4. No string literal in any module under `src/factory` other than `factory/domain/post_texts.py` contains "retrying" in any case; the test parses the modules with `ast` and skips module, class and function docstrings.
5. `expiry_entry_text("doing", 1, "b" * 40)` equals `"expiry 1: the lease of stage doing ran out. Its work is discarded back to commit " + "b" * 40 + "."`.
6. The lease limit decides: with the claim made by `factory-1`, the clock advanced by 59 minutes and 59 seconds, an `expired` event handled by `factory-2` raises `CannotHandle` with `kind == "expired"`, leaves `origin/<branch>` unchanged and does not call `run`; advanced by 60 minutes, the same event is handled.
7. An `expired` event raises `CannotHandle` and pushes nothing when the claim's status is `"own"` (handled by `factory-1`, also with the clock advanced by 60 minutes) and when the work item holds no claim (two cases).
8. Handling an `expired` event pushes a work item with `crashes` one higher, `attempts` unchanged, no claim, and `stage`, `blocked`, `round`, `pull_request`, `comments_read` and `handed_over` unchanged.
9. The pushed journal data ends with a record of speaker `factory` and kind `expiry` numbered one higher than the previous last record, and the visible text of that entry equals `expiry_entry_text(stage, 1, stage_start.commit)`.
10. The checkout is discarded before the record is made: a file left uncommitted and a local commit never pushed in the handling instance's checkout are gone afterwards, and `git.status().changes` is empty.
11. The note is posted once, after the push: `hosting.factory_posts(number)` has one comment, its `key` equals `PostKey(work_item=<id>, kind="expiry", n=<the expiry record's number as a string>)` and its body starts with `expiry_note(1, 2)`.
12. Below the cap the stage is rerun by the handling instance: `run` is called exactly once, inside the same `handle` call, with an event of kind `"run"` whose work item has `crashes` 1, no claim and `branch_commit` equal to the pushed commit.
13. At the cap (`crashes` 1 before, cap 2) the stage is not rerun: `run` is not called, the pushed state has `blocked` `crash_cap` and `crashes` 2, the journal ends with the `expiry` record and then a `question` record by `factory`, and `hosting.factory_posts(number)` has two comments in this order: the first with key kind `expiry` and a body that starts with `expiry_note(2, 2)` and does not contain "retrying", the second with key kind `crash_cap` whose body starts with `factory: ` followed by the question text.
14. When posting the note fails (`hosting.fail_next("post_comment")`), `handle` raises `HostingServiceError`, `origin/<branch>` already holds `crashes` 1 and no claim, and `run` is not called in that call.
15. For a work item without a pull request, below the cap, the note is posted on a draft pull request that the stop service opens with the title `<id>: <story title>` (`<id>` alone for a story whose body has no title line; two cases, one test), and the new number is in `state.pull_request` of the pushed work item and of the work item in the `run` event.
16. At the cap, for a work item without a pull request in its state, both posts land on one draft pull request: `handle` returns without an error, `hosting.pull_requests()` holds one pull request more than before, `state.pull_request` of the pushed work item is its number, the number is committed once, and `hosting.factory_posts(number)` has the `expiry` note and the `crash_cap` question in that order.
17. `build_handlers(...)["expired"]` is the very `RecoveryHandler` instance that `build_handlers(...)["crash"]` returns, `expired` is not in `NOT_YET_HANDLED`, and the kinds of `NOT_YET_HANDLED` are exactly the kinds of `EventKind` that are not keys.
18. make check stays green.
19. docs: `docs/operator-guide.md` explains the expiry (another instance's lease ran out, the stage is taken over and counted as a crash, the `expiry` entry and the note, the notes say "retrying" only where a rerun follows, a note whose post failed is not posted again) and states that instances need synchronised clocks; `docs/project-guide.md` states that `expired` is registered in `build_handlers` with the handler of `crash`, and that `NOT_YET_HANDLED` lists the kinds still without one; `docs/decisions.md` records that an expiry is a crash and costs no attempt. Where the operator guide and the project guide list `expired` as a kind without a handler, they now name its handler, the one of `crash`.

## Demo

The first command shows the note texts and the entry text.

```bash
uv run python -c "
from factory.domain.post_texts import expiry_note, stall_note
from factory.domain.recovery import expiry_entry_text
print(expiry_note(1, 2))
print(expiry_note(2, 2))
print('retrying' in stall_note('died', 1, 2).lower(), 'retrying' in stall_note('died', 2, 2).lower())
print(expiry_entry_text('doing', 1, 'b' * 40))
"
```
Expect: four lines. `The run that held this stage ended without finishing: its lease expired (crash 1 of 2). Retrying.`; `The run that held this stage ended without finishing: its lease expired (crash 2 of 2). The factory does not rerun it and asks you instead.`; `True False`; and `expiry 1: the lease of stage doing ran out. Its work is discarded back to commit ` followed by forty letters `b` and a full stop.

The second command lets instance `factory-1` claim a stage, advances the clock by the lease, and lets `factory-2` take the stage over.

```bash
uv run python -c "
import subprocess, tempfile
from datetime import UTC, date, datetime, timedelta
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
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.dispatcher import Handler
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
hosting = FakeHostingService()
pr = hosting.create_pull_request('work-item/F0001-S0001', 'F0001-S0001: Demo', '', draft=True)
doc = WorkItemDocument(state=initial_state('tests').model_copy(update={'pull_request': pr.number}), body='# Demo\n\n## Journal\n\n')
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
clock = ManualClock(datetime(2026, 10, 12, tzinfo=UTC))
boundaries = Boundaries(git=git, hosting=hosting, agent_runtime=FakeAgentRuntime(), project_commands=MakeProjectCommands(work), work_item_reader=FrontmatterWorkItemReader(), work_item_writer=writer, cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(), clock=clock, log=TimestampedFactoryLog(tmp / 'factory.log', clock), health=JsonHealthStatusFile(tmp / 'health.json'), pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(tmp / 'agents'), checkout=work)
ClaimService(boundaries, 'factory-1', definition).claim(branch, rel, doc, 'tests')
clock.advance(timedelta(minutes=60))
head = git.resolve('origin/' + branch)
reader = FrontmatterWorkItemReader()
snapshot = WorkItemSnapshot(id='F0001-S0001', path=rel, folder='in-progress', branch=branch, branch_commit=head, document=reader.parse(git.show_file('origin/' + branch, rel)))
class Rerun(Handler):
    def __init__(self):
        self.events = []
    def handle(self, event):
        self.events.append(event)
rerun = Rerun()
other = ClaimService(boundaries, 'factory-2', definition)
RecoveryHandler(boundaries, definition, other, rerun).handle(Event(kind='expired', work_item=snapshot, remote_state=head))
after = reader.parse(git.show_file('origin/' + branch, rel))
print(after.state.crashes, after.state.attempts, after.state.claim is None)
print(len(rerun.events))
posts = hosting.factory_posts(pr.number)
print(len(posts), posts[0].key.kind, posts[0].key.n)
print(posts[0].body.startswith('The run that held this stage ended without finishing: its lease expired (crash 1 of 2). Retrying.'))
"
```
Expect: four lines, `1 0 True` (counted as a crash, no attempt charged, claim cleared), `1` (the stage is rerun once), `1 expiry 3` (one post, of kind `expiry`, keyed by journal entry 3: entry 1 created, 2 started, 3 expiry) and `True`.

The third command shows the registration.

```bash
uv run python -c "
from types import SimpleNamespace
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.entry.wiring import NOT_YET_HANDLED, build_handlers
definition = PipelineDefinition(contract='1.0', roles={'tester': RoleDefinition(write_paths=['tests/*'])}, stages={'tests': StageDefinition(role='tester', next=['done']), 'done': StageDefinition()})
handlers = build_handlers(SimpleNamespace(), definition, 'factory-1', {})
print(handlers['expired'] is handlers['crash'], 'expired' in NOT_YET_HANDLED)
"
```
Expect: one line, `True False`: `expired` and `crash` share one handler, and `expired` is no longer listed in `NOT_YET_HANDLED`.

## Log (append only)

1. 2026-10-12 human: created.
