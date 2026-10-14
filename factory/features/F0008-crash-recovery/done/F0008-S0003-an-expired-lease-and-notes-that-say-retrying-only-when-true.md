---
stage: done
pr: 97
blocked: null
comments_seen: 0
round: 2
attempts: 0
---
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
2. intake: accepted.
   - Interface: names concrete modules and signatures (`post_texts.expiry_note`, `stall_note` as already built, `recovery.expiry_entry_text`, `RecoveryHandler.handle` steps 1, 3, 4b and 5, `wiring.NOT_YET_HANDLED` and `build_handlers`). Every text and behaviour it states is exact: the two note wordings, the entry text, the guard per claim status, the step 4b post key, and the pull request number recorded when the stop opens one.
   - Criteria: each is testable by one test function. Criteria 1 and 2 cover both sides of the note cap, 3 both sides for `stall_note`, 6 both sides of the lease limit (59:59 and 60:00), 7 the refused statuses (`own` and no claim; `held` is the 59:59 case in 6), 12 and 13 the rerun below the cap and the question at it, and 14 a failed post. Criteria 15 and 16 cover a missing pull request below and at the cap, and 17 covers the wiring and `NOT_YET_HANDLED`. Every rule has its failing side.
   - Demo: all three commands are runnable. Each `Expect:` line is checkable against the output (`1 0 True`, `1`, `1 expiry 3`, `True`, and `True False`).
   - Architecture: the texts and the entry text are in `domain`, the handler is in `application`, and the registration is in `entry.wiring`, so the layering holds. The post goes through `StopService`.
   - Scope: inside F0008's scope item "expired lease handled as a crash" and its notes wording. It builds neither the watcher nor the lease functions, and the stall half belongs to F0005-S0004. Decisions 11, 12, 13 and 16 of FEATURE.md are carried out as written.
3. tester: Tests written from the Interface and the criteria. They use S0001's setup: `factory-1` claims the stage through `tests/crash_support.py::claim`, `factory-2` handles the event, and `clock.advance` runs the lease out.
   - criterion 1: tests/domain/test_post_texts_notes.py::test_the_expiry_note_below_the_crash_cap_says_retrying
   - criterion 2: tests/domain/test_post_texts_notes.py::test_the_expiry_note_at_or_past_the_crash_cap_asks_and_does_not_say_retrying (crashes 2 and 3)
   - criterion 3: tests/domain/test_post_texts_notes.py::test_the_stall_note_says_retrying_only_below_the_attempts_cap (every StallReason × attempts 1/2/3, cap 2)
   - criterion 4: tests/test_retrying_wording.py::test_no_string_outside_the_post_texts_says_retrying (ast over `source_search.modules()`, skips module, class and function docstrings)
   - criterion 5: tests/domain/test_recovery_expiry_text.py::test_the_expiry_entry_names_the_stage_the_count_and_the_commit
   - criterion 6: tests/application/test_recovery_expiry.py::test_an_expired_event_is_handled_only_once_the_lease_has_run_out (59:59 refused, 60:00 handled)
   - criterion 7: tests/application/test_recovery_expiry.py::test_an_expired_event_on_an_own_claim_or_no_claim_is_refused_and_pushes_nothing (own at 0 and at 60 minutes, no claim)
   - criterion 8: tests/application/test_recovery_expiry.py::test_an_expiry_counts_one_crash_clears_the_claim_and_charges_no_attempt
   - criterion 9: tests/application/test_recovery_expiry.py::test_the_journal_ends_with_a_factory_expiry_entry_naming_the_stage_start
   - criterion 10: tests/application/test_recovery_expiry.py::test_the_checkout_is_discarded_before_the_expiry_is_recorded
   - criterion 11: tests/application/test_recovery_expiry.py::test_the_expiry_note_is_posted_once_under_the_expiry_entrys_key
   - criterion 12: tests/application/test_recovery_expiry.py::test_below_the_cap_the_handling_instance_reruns_the_stage_once
   - criterion 13: tests/application/test_recovery_expiry.py::test_at_the_cap_the_note_and_then_the_question_are_posted_and_nothing_reruns
   - criterion 14: tests/application/test_recovery_expiry.py::test_a_failed_note_raises_after_the_expiry_is_pushed_and_nothing_reruns
   - criterion 15: tests/application/test_recovery_expiry.py::test_without_a_pull_request_the_note_opens_a_draft_whose_number_is_recorded_and_rerun (titled and untitled)
   - criterion 16: tests/application/test_recovery_expiry.py::test_at_the_cap_without_a_pull_request_both_posts_land_on_one_new_draft. "The number is committed once" is checked as exactly two commits after the stage start: the expiry commit and the commit of the pull request number.
   - criterion 17: tests/entry/test_wiring_recovery_expired.py::test_expired_shares_the_crash_handler_and_is_no_longer_listed_as_unhandled

   New files: tests/domain/test_post_texts_notes.py, tests/domain/test_recovery_expiry_text.py, tests/test_retrying_wording.py, tests/application/test_recovery_expiry.py, tests/entry/test_wiring_recovery_expired.py.

   One run of `make test`: three collection errors, as intended. `expiry_note` cannot be imported from `factory.domain.post_texts` (this breaks tests/domain/test_post_texts_notes.py and tests/application/test_recovery_expiry.py), and `expiry_entry_text` cannot be imported from `factory.domain.recovery` (tests/domain/test_recovery_expiry_text.py). The wiring test collects and fails, because `expired` is not registered yet.

   The tests for criteria 3 and 4 already describe the current code. For criterion 3 the ticket says so. For criterion 4, today only `post_texts.py` contains the word, so that test is a guard rather than a red test.

   `make lint` is green. The type check was skipped, as this stage says.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built the expiry takeover. `make check` is green, with coverage at 99.14 %. Commits: 23e1676 (feat), f2fc903 (refactor).
      - `src/factory/domain/post_texts.py`: added `expiry_note`. It ends with "Retrying." only below the crash cap.
      - `src/factory/domain/recovery.py`: added `expiry_entry_text`.
      - `src/factory/application/recovery.py` (`RecoveryHandler`):
        - Guards: the handler now accepts `crash` (the claim must be `own`) and `expired` (the claim must be `expired`), using the `_REQUIRED_STATUS` map. Any other kind is refused, and every `CannotHandle` it raises carries the event's kind.
        - Record: for `expired` the journal entry is of kind `expiry`, with the text from `expiry_entry_text`, in the same single commit as a crash. At the cap that commit also holds the crash-cap question. The commit subject is "expiry of stage X recorded".
        - Note (new `_note_expiry`): runs after the push. It posts through `StopService` under key `expiry:<entry number>`.
        - Step 5: the rerun or `ask_crash_cap` gets the snapshot as last written. That means the PR number recorded with the note is already in it, so at the cap the question lands on the same draft without a second write of the number.
        - `_record_pull_request` now returns the updated snapshot (new commit and document) instead of None.
        - The stop title logic is shared in `_stop_title`, which `ask_crash_cap` now uses too.
      - `src/factory/entry/wiring.py`: one `RecoveryHandler` instance is registered under both `crash` and `expired`. `NOT_YET_HANDLED` is now `("acceptance_due",)`.
      - Design decision: I extended the existing handler, choosing the journal kind from the event kind. I rejected a separate `ExpiryHandler` or a subclass: the discard, record and push steps and the cap logic are identical, and the ticket asks for the same instance under both keys.
      - Refactor: I removed a docstring from the private `_note_expiry`, since the project gives none to private names. Nothing else needed changing.
      - Noticed, not touched:
        - The `expiry is None` guard in `_note_expiry` cannot be reached, because the entry was appended just before. It is uncovered, and it mirrors the guard on the question in `ask_crash_cap`.
        - `_state_of` and `_remote_head` still raise `CannotHandle` with kind `crash`, as they did before this story.
        - Docs are left to the documenter (criterion 19).

   `make check`: check: green
5. reviewer: one finding, in group 4 (quality). Groups 1 to 3 pass. Every criterion from 1 to 17 has a test that checks what the criterion says. Both sides of the lease limit are tested (59:59 and 60:00), and both sides of each note cap (1 against 2 and 3). The refused statuses own, own after the lease, no claim and held are each tested. The coder's entry reports `make check` green. The layers hold, the post goes through `StopService`, and the diff adds no markers that silence a check. The diff also contains `CLAUDE.md`, `docs/runs/` and `planning/`; those changes are the human's commit b6af571, so I did not review them.

   1. `src/factory/application/recovery.py:43` (`_REQUIRED_STATUS: dict[EventKind, str]`): the values are typed `str`, but they are compared with the `ClaimStatus` that `ClaimService.status` returns. Under `mypy --strict` a mistyped status ("expird") would therefore type-check and make the guard refuse every event. The map is also a second hand-kept copy, reversed, of `_CLAIM_EVENTS` in `src/factory/domain/evaluation.py:46` (own → crash, expired → expired). Fix: derive the required status from the domain's mapping by making it or its inverse public in `factory.domain`, and if that is not possible, at least type the values as `factory.domain.lease.ClaimStatus`.
6. coder: coder (round 1): Fixed the reviewer's one finding in commit b0bb531. `make check` is green, with coverage at 99.14 %.
      - `src/factory/domain/evaluation.py`: renamed the private `_CLAIM_EVENTS` to the public `CLAIM_EVENTS` (typed `dict[ClaimStatus, EventKind]`, with a docstring) and added `required_claim_status(kind: EventKind) -> ClaimStatus | None`, the inverse lookup. `claim_event` evaluation uses the renamed map; its behaviour is unchanged.
      - `src/factory/application/recovery.py`: removed `_REQUIRED_STATUS`. The guard in `_dead_run` now calls `required_claim_status(event.kind)`, so the required status is typed `ClaimStatus` and comes from the domain's one map. A kind the map does not raise (anything other than `crash` or `expired`) still yields None and is refused with `CannotHandle`. Dropped the import of `EventKind`, which is no longer used.
      - Rejected: only retyping the values of the local map as `ClaimStatus`. That would still keep a second copy of the map by hand, which the finding names.
      - No tests changed. Nothing else was touched.

   `make check`: check: green
7. reviewer: reviewer (round 1): one finding, in group 4 (quality). Groups 1 to 3 pass.

   - Every criterion from 1 to 17 has a test that checks what the criterion says.
   - Both sides of the lease limit are tested (59:59 refused as `held`, 60:00 handled). Both note caps are tested on both sides (1 against 2 and 3, for every `StallReason`). The refused statuses own, own after the lease, and no claim are each tested.
   - The rejected push of the pull-request number goes through the shared `_record_pull_request`, which S0002's test covers.
   - The coder's entry reports `make check` green. The layers hold, the post goes through `StopService`, and the diff adds no marker that silences a check.
   - Last round's finding is fixed: `required_claim_status` in `src/factory/domain/evaluation.py` derives the required status from the one `CLAIM_EVENTS` map, typed `ClaimStatus`.
   - The diff also holds changes to `CLAUDE.md`, `docs/runs/` and `planning/`. They come from the human's commit, so I did not review them.

   1. `src/factory/application/recovery.py:190` (`_remote_head`): for an `expired` event it raises `CannotHandle(_KIND, ...)`, which names the kind `crash`. That breaks the contract of `CannotHandle` ("the event's kind", `src/factory/domain/errors.py:178`). It also disagrees with the guard on the missing branch commit in `_dead_run`, which this diff changed to `event.kind` for the same case. The coder's entry noticed this and left it. Fix: pass the event's kind into `_remote_head` (from `handle`) and raise with it, as `_dead_run` does. `_state_of` in `ask_crash_cap` may keep `crash`.
8. coder: coder (round 2): Fixed the reviewer's one finding in commit 8b346b7. `make check` is green, with coverage at 99.14 %.
      - `src/factory/application/recovery.py`: `_remote_head` now takes the event's kind (`kind: EventKind`), which `handle` passes as `event.kind`. When the branch is gone from the remote it raises `CannotHandle(kind, ...)`. An expiry is no longer reported as `crash`, and this matches the guards in `_dead_run`. `EventKind` is now imported from `factory.domain.events`.
      - As the finding allows, `_state_of` in `ask_crash_cap` still raises with `crash`.
      - Rejected: storing the event's kind on the handler. It would add state to a handler that is shared between `crash` and `expired`. A parameter is simpler.
      - No refactor was needed for this one-line change. No tests were changed.

      `make check`: check: green

   `make check`: check: green
9. reviewer: reviewer (round 2): no findings. All five groups pass.

   - Acceptance criteria: each of criteria 1 to 17 has a test that checks what the criterion says. Both sides of the lease limit are tested: 59:59 is refused as `held` with kind `expired`, and 60:00 is handled. Both note caps are tested on both sides: the expiry note at 1, 2 and 3 crashes, and the stall note for every `StallReason` at attempts 1, 2 and 3 against a cap of 2. The refused statuses are each tested: own, own after the lease, and no claim. For the other refusals, the existing test for a kind other than `crash` or `expired` (`tests/application/test_recovery_crash.py`, kind `run`) still holds after the guard moved to `required_claim_status`, and the S0001 tests still cover the missing state and the missing branch commit. The coder's entry reports `make check` green.
   - Last round's finding is fixed: `_remote_head` in `src/factory/application/recovery.py` now takes the event's kind and raises `CannotHandle(kind, ...)`. This matches the guards in `_dead_run`. `_state_of` in `ask_crash_cap` keeps `crash`, as the finding allowed.
   - Architecture: the note and entry texts are in `factory.domain`, and `required_claim_status` derives from the one `CLAIM_EVENTS` map in `factory/domain/evaluation.py`. The handler is in `factory.application`, the note is posted through `StopService`, and the registration is in `factory.entry.wiring`, with the same instance under `crash` and `expired`.
   - Security: the diff adds no marker that silences a check, and builds no shell or SQL from strings.
   - Quality: `_stop_title` is shared with `ask_crash_cap` rather than copied. The guard `expiry is None` in `_note_expiry` narrows the type of `last_record`'s result for mypy, as the coder's entry says. It is not dead logic.
   - Ticket hygiene: the log names the main decision, extending `RecoveryHandler` rather than writing an `ExpiryHandler`, and what was rejected. `Assignment` matches what was built. Criterion 19 still says what the documenter has to write.
   - Not reviewed: the diff also changes `CLAUDE.md`, `docs/runs/` and `planning/`. Those changes come from the human's commit b6af571.
10. documenter: docs (round 2): wrote the documentation for criterion 19. `make check` is green (coverage 99.14 %). I found no contradictions between the code and the Interface, so there are no findings.

    Files changed:
    - `docs/operator-guide.md`: new section "An expired lease". It covers the takeover of another instance's expired claim, counting it as a crash with no attempt charged, the `expiry` entry, the note (both texts) and the crash-cap question that follows it. It also says that notes say "retrying" only where a rerun follows, that a note whose post failed is not posted again, and that your own claim is never an expiry. I updated the lists that named `expired` as unhandled: the dispatcher section (only `acceptance_due` is left) and the restart section. The clock paragraph in "Claims, leases and the clock" already required synchronised clocks and now points to the new section.
    - `docs/project-guide.md`: `build_handlers` now has twelve kinds, with `expired` registered as the same `RecoveryHandler` instance as `crash`. `NOT_YET_HANDLED` is now only `acceptance_due`. `RecoveryHandler`'s description now covers `expired`: the guard through `required_claim_status`, the `expiry` entry text, step 4b (the note, its key, the pull-request number record, no repost) and the note that a `crash` still posts nothing.
    - `docs/decisions.md`: new entry saying an expiry is a crash and costs no attempt. It records why one handler instance serves both kinds and why the expiry note is posted. It also records the rejected v1 behaviour, which charged an attempt and said "Retrying." even when the next tick asked the human.

    Cross-read and found current: the stall-note sections of the operator guide, the claims and lease section of the project guide, and the earlier crash decisions. I ran no examples because I wrote no runnable ones. The note and entry texts in the guides match the Interface strings.

    Stale but not touched: none seen.

    `make check`: check: green
11. demo: demo (round 2): ran the three commands under `## Demo` from the repository root, as written and in order. All three exited 0, and each output matches its `Expect:` line. Nothing in the output contradicts any acceptance criterion. No findings.

    1. Note texts and entry text:
    ```
    The run that held this stage ended without finishing: its lease expired (crash 1 of 2). Retrying.
    The run that held this stage ended without finishing: its lease expired (crash 2 of 2). The factory does not rerun it and asks you instead.
    True False
    expiry 1: the lease of stage doing ran out. Its work is discarded back to commit bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.
    ```
    Met. These are the four expected lines. The note below the cap ends with `Retrying.` (criterion 1). The note at the cap does not contain "retrying" (criterion 2). The stall note says "retrying" below its cap and not at it (criterion 3). The entry text is exact (criterion 5).

    2. `factory-1` claims the stage, the clock advances by 60 minutes, and `factory-2` takes the stage over:
    ```
    1 0 True
    1
    1 expiry 3
    True
    ```
    Met. The expiry is counted as a crash, no attempt is charged and the claim is cleared (criterion 8). The stage is rerun once (criterion 12). There is one post, of kind `expiry`, keyed by journal entry 3 (criteria 9 and 11). The body starts with `expiry_note(1, 2)` (criterion 11).

    3. Registration:
    ```
    True False
    ```
    Met. `expired` shares the `crash` handler instance, and `expired` is no longer in `NOT_YET_HANDLED` (criterion 17).

    Open: none. The demo does not run the cap side, the lease limit at 59:59, the refused statuses or the missing pull request (criteria 6, 7, 13 to 16). The reviewer reports tests for each of them, and nothing in the demo contradicts them.
12. done (pull request merged); cost: 10 runs, 20.3 min, 84 turns, 289k tokens in (1763k more from cache), 40k out, $3.22
