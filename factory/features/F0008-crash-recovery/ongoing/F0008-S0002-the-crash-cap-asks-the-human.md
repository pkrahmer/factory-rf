# The crash cap asks the human

## Assignment (as of log entry 1)

Add the crash cap to `RecoveryHandler`. When the count after a crash reaches `PipelineDefinition.crash_cap` (default 2), the stage is not rerun: in the same commit that records the crash the work item gets `blocked` set to `crash_cap` and a journal entry of kind `question` by `factory`; the commit is pushed, and only then is the question posted on the pull request, once, under the key `PostKey(kind="crash_cap", n=<the question's journal number>)`, opening the draft pull request first when there is none (through `StopService`). Recording before posting is kept thing 10; the keyed post makes a repeat a no-op. The counter's two resets are built by others and used here: a forward move of the stage resets `crashes` in the result commit (F0005-S0007, F0005 decision 17), and the human's answer to the question, a non-blank comment written after the question's post, goes through F0007's `unblock` and `CommentHandler` (F0007-S0007, F0007 decision 15), which clears `blocked` and sets `crashes` to 0; a rework move and a stall keep the counter, so the cap counts the crashes since the last forward move. This story changes neither place; one criterion walks the answer through F0007's handler. The story also states and tests the path that F0005 decision 8 hands to this feature: a boundary error after a pushed claim leaves the claim, the next tick reruns the stage as a crash, and an error that repeats reaches the crash cap and ends with this question, not with the error cap's report. Covers GH2.4 and R23 (the cap, the question); keeps kept thing 14 (the crash is counted apart from rounds and attempts) and kept thing 10 (ask, record and commit, then post). Posting the recorded question again after a kill between its record and its post is the `ask` event's job (F0007-S0002); this story gives that handler the recorded form it needs and offers `ask_crash_cap` for the post, whose body is the one `AskHandler` posts. The close sentence of the question promises that the branch and the bill are deleted, which holds after a kill only because of S0004 (F0007 decision 21).

## Interface

`src/factory/domain/recovery.py` (added to S0001's module)

```python
def at_crash_cap(state: WorkItemState, crash_cap: int) -> bool: ...
def asking_crash_cap(state: WorkItemState) -> WorkItemState: ...
```

- `at_crash_cap` is true exactly when `state.crashes >= crash_cap`.
- `asking_crash_cap` returns a copy with `blocked` set to `"crash_cap"`; every other field is as it was.

`src/factory/domain/post_texts.py` (added)

```python
def crash_cap_question(stage: str, crashes: int, crash_cap: int) -> str: ...
```

- It returns exactly `f"Stage {stage} crashed {crashes} times, which is the crash cap of {crash_cap}. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted."`

`src/factory/application/recovery.py` (changed and added)

```python
class RecoveryHandler(Handler):
    def handle(self, event: Event) -> None: ...                       # step 3 and step 5 change
    def ask_crash_cap(self, work_item: WorkItemSnapshot) -> StopPosted: ...
```

- Step 3 of `handle` (record) now also checks `at_crash_cap(<the crashed state>, definition.crash_cap)`. At the cap the new document is `asking_crash_cap` of the crashed state, with the `crash` entry followed by `append_entry(document, NewEntry(speaker=FACTORY, kind="question", text=crash_cap_question(stage, crashes, definition.crash_cap)))`: one commit holds both entries.
- Step 5 of `handle` (rerun) is skipped at the cap: after the push, `handle` calls `self.ask_crash_cap(<the snapshot with the new document and the pushed commit>)` and returns without calling `run`. Below the cap nothing changes from S0001.
- `ask_crash_cap(work_item)` raises `CannotHandle(kind="crash", reason=...)` when the state's `blocked` is not `"crash_cap"`, and when `last_record(document, speaker=FACTORY, kind="question")` is `None`. Otherwise it posts `StopService(boundaries).post(WorkItemStop(key=PostKey(work_item=<id>, kind="crash_cap", n=str(<that record's number>)), branch=<branch>, title=f"{id}: {title(body)}" (just `id` when the body has no title), pull_request=<state.pull_request>, text=f"{FACTORY}: {entry_text(document, <that number>)}"))` and returns the `StopPosted`. The text is the body that `AskHandler` (F0007-S0002) posts for a recorded question, so a post made here and a repost made by that handler after a kill are the same comment under the same key.
- `ask_crash_cap` reads the question's text with `entry_text` for display only, as `AskHandler` does; the speaker and the number come from the record. `tests/test_no_journal_reading.py` (F0005-S0009, changed by F0007-S0009) allows `entry_text` only in the modules of its set `ALLOWED["entry_text"]`, so this story adds `"factory.application.recovery"` to that set and changes nothing else in that file; the tester makes the change.
- When `StopPosted.opened` is true, `ask_crash_cap` records the new pull request number: `recorder = WorkItemRecorder(boundaries)`, `recorder.check_out(branch)` (the checkout may be on `main` when the method is called on its own), the work item read with `recorder.read(path)`, its `state.pull_request` set to the returned number, and `recorder.record(branch, path, document, commit_subject(id, "pull request opened"))`; a push that is not `"pushed"` raises `PushFailed` (F0007-S0001).
- `HostingServiceError` from the post propagates; the question stays recorded and pushed.
- A boundary error after a pushed claim (F0005 decision 8: `HostingServiceError`, `AgentRuntimeError`, `ProjectCommandError`, `GitError` or a rejected result push) leaves the claim on the remote. The next tick finds an own claim and raises `crash`; this handler records it as any crash. A rerun that fails again after its claim reaches the cap as the second crash: the error cap of F0006's dispatcher does not apply, because each rerun is a new `crash` event on a new remote state.

Tests: `tests/domain/test_recovery_cap.py` (a new file: `tests/domain/test_recovery.py` is S0001's), `tests/domain/test_post_texts_crash_cap.py`, `tests/application/test_recovery_cap.py` and `tests/application/handlers/test_comments_crash_cap.py`. The application tests use S0001's setup (its Tests paragraph) with the work item's state set to `crashes` 1 before the claim (so that the next crash reaches the default cap of 2) and a pull request created with `hosting.create_pull_request` and recorded in the state, except where a criterion says there is none. The boundary-error test uses a `run` stand-in, a subclass of `Handler`, that claims the stage again with `ClaimService(boundaries, "factory-1", definition).claim(...)` on the event's work item and then raises `HostingServiceError`. The comment test calls F0007's `CommentHandler` with `hosting.add_human_comment`; this story names no new function in F0005 or F0007. The tester also makes the one-line change to `ALLOWED["entry_text"]` in `tests/test_no_journal_reading.py` that the Interface names.

## Acceptance criteria

1. `at_crash_cap(state, 2)` is false for `crashes` 1 and true for `crashes` 2 and 3; `at_crash_cap(state, 1)` is true for `crashes` 1.
2. The handler asks exactly when the count after the crash reaches the cap, and reruns otherwise (one parametrized test over crashes before the crash and cap): (0, 1) asks, (0, 2) reruns, (1, 2) asks, (1, 3) reruns, (2, 3) asks.
3. At the cap the `run` handler is not called, and no stage-start commit is pushed: the remote head after `handle` is the crash commit.
4. At the cap the pushed work item has `blocked` equal to `"crash_cap"`, `crashes` equal to the cap, `attempts` unchanged and no claim.
5. The crash commit at the cap holds both entries and nothing else is added: the journal data ends with a record of kind `crash` and then a record of kind `question` by `factory`, with consecutive numbers, and `git.log` between the stage-start commit and the remote head lists exactly one commit.
6. The visible text of the question entry equals `crash_cap_question(stage, crashes, cap)`.
7. The question is posted once on the work item's pull request after the push: `hosting.factory_posts(number)` has one comment, its `key` equals `PostKey(work_item=<id>, kind="crash_cap", n=<the question's number as a string>)` and its body starts with `factory: ` followed by the question text.
8. Recording comes before posting: with `hosting.fail_next("post_comment")` the `handle` call raises `HostingServiceError`, `origin/<branch>` already holds `blocked` `crash_cap` and the question entry, and a later `ask_crash_cap(<snapshot read from origin/<branch>>)` posts exactly one comment.
9. A repeated `ask_crash_cap` posts nothing: the second call returns a `StopPosted` whose `outcome` is `"already_posted"` and `hosting.factory_posts(number)` still has one comment.
10. At the cap, `handle` for a work item without a pull request in its state opens the draft pull request with the title `<id>: <story title>`, posts the question there once, and leaves `state.pull_request` of the work item on `origin/<branch>` equal to its number, with no error and one commit for the number beside the crash commit; for a story whose body has no title line the pull request's title is `<id>` alone (two cases, one test).
11. `ask_crash_cap` called on its own, with the checkout on `main` (`checkout.checkout("main", start_point="origin/main")`) and the work item without a pull request in its state, records the new number on `origin/<branch>`: the commit lands on the work item's branch, `origin/main` is unchanged, and the question is posted once.
12. `ask_crash_cap` raises `CannotHandle` for a work item whose `blocked` is not `"crash_cap"`, and posts nothing.
13. `ask_crash_cap` raises `CannotHandle` for a work item with `blocked` `"crash_cap"` that has no journal record of kind `question` by `factory`, and posts nothing.
14. `crash_cap_question("tests", 2, 2)` equals the text given in the Interface with those values, and the text names the stage, the count and the cap.
15. A non-blank human comment written after the crash-cap post (`hosting.add_human_comment`), handled by F0007's `CommentHandler`, leaves the pushed state with `blocked` `None`, `crashes` 0 and `attempts` unchanged; this story adds no code to the comments handler.
16. A boundary error after a pushed claim ends at the crash cap: with `crashes` 0 and the default cap of 2, a `run` handler that pushes its own claim through `ClaimService.claim` and then raises `HostingServiceError` is called by the first `crash` event, whose `handle` raises that error with `origin/<branch>` holding `crashes` 1 and the new claim; a second `crash` event built from `origin/<branch>` then records `crashes` 2, `blocked` `crash_cap` and no claim, posts the crash-cap question once, and does not call the `run` handler a second time.
17. `asking_crash_cap` returns a state with `blocked` `"crash_cap"` and every other field equal, from a state with `crashes` 2, `attempts` 1, `round` 1 and a pull request number, and leaves its argument unchanged.
18. make check stays green.
19. docs: `docs/operator-guide.md` has the crash-cap stop: what the question says, that a comment resets the counter and reruns the stage, that closing discards the story, that a boundary error that repeats after a claim ends here and not in the error report, and the `crash_cap` key of the pipeline definition with its default of 2; `docs/project-guide.md` states that `crash_cap` is a pipeline definition key and that the cap counts the crashes since the last forward move; `docs/project-guide.md`'s section "No code reads data from the journal's text" names `factory.application.recovery` among the modules that may reference `entry_text`, for the display text of the crash-cap question; `docs/decisions.md` records that a rework move and a stall keep the counter, and that a lost crash-cap question for a story without a pull request is not posted again.

## Demo

The first command shows the pure rules and the question text.

```bash
uv run python -c "
from factory.domain.answers import unblock
from factory.domain.post_texts import crash_cap_question
from factory.domain.recovery import asking_crash_cap, at_crash_cap
from factory.domain.work_item import initial_state
state = initial_state('doing').model_copy(update={'crashes': 2, 'attempts': 1})
print([at_crash_cap(state.model_copy(update={'crashes': n}), 2) for n in (1, 2, 3)])
print(asking_crash_cap(state).blocked)
answered = unblock(asking_crash_cap(state))
print(answered.blocked, answered.crashes, answered.attempts)
print(crash_cap_question('doing', 2, 2))
"
```
Expect: four lines. `[False, True, True]`; `crash_cap`; `None 0 1`; and `Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.`

The second command handles a second crash against a real local bare remote and the fake hosting service.

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
doc = WorkItemDocument(state=initial_state('tests').model_copy(update={'crashes': 1, 'pull_request': pr.number}), body='# Demo\n\n## Journal\n\n')
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
claims = ClaimService(boundaries, 'factory-1', definition)
claims.claim(branch, rel, doc, 'tests')
head = git.resolve('origin/' + branch)
reader = FrontmatterWorkItemReader()
snapshot = WorkItemSnapshot(id='F0001-S0001', path=rel, folder='in-progress', branch=branch, branch_commit=head, document=reader.parse(git.show_file('origin/' + branch, rel)))
class Rerun(Handler):
    def __init__(self):
        self.events = []
    def handle(self, event):
        self.events.append(event)
rerun = Rerun()
RecoveryHandler(boundaries, definition, claims, rerun).handle(Event(kind='crash', work_item=snapshot, remote_state=head))
after = reader.parse(git.show_file('origin/' + branch, rel))
print(after.state.crashes, after.state.attempts, after.state.blocked, after.state.claim is None)
print(len(rerun.events))
posts = hosting.factory_posts(pr.number)
print(len(posts), posts[0].key.kind, posts[0].key.n)
print(posts[0].body.startswith('factory: Stage tests crashed 2 times, which is the crash cap of 2.'))
"
```
Expect: four lines, `2 0 crash_cap True` (the second crash reached the cap, no attempt charged, blocked, claim cleared), `0` (no rerun), `1 crash_cap 4` (one post, of kind `crash_cap`, keyed by journal entry 4: entry 1 created, 2 started, 3 crash, 4 question) and `True`.

## Log (append only)

1. 2026-10-12 human: created.
