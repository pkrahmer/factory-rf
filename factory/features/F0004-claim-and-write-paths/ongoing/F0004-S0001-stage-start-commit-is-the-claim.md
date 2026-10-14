---
stage: review
pr: 48
blocked: null
comments_seen: 2
round: 1
attempts: 0
---
# The stage-start commit is the claim

## Assignment (as of log entry 1)

Build the first half of the claim service. `ClaimService.claim` writes the claim and a "started" journal entry into a work item, commits them as the stage-start commit and pushes that commit. The push is the claim (R19, R20): whoever pushes first owns the stage, and a rejected or unreachable push is no claim, so the caller (F0005) starts no agent run. The claim records the instance's configured name, the start time from the clock and the `lease_duration` of the stage's role, copied at claim time (R21). Status, expiry and release come in S0002. The stage-start commit is the last commit before the agent run: whatever the caller left uncommitted (for a new branch, the opening) becomes part of this commit, which is the baseline of the guard and the undo (S0003 to S0005). Covers GH1.2 (the stage-start commit records the instance's name and the start time), R19, R20 and R21 (the lease runs from this commit); keeps kept thing 13 (recovery from what is on the remote). Morning observation: none; a real push against the hosting service's git remote is seen in the baseline run.

## Interface

`src/factory/domain/errors.py` gains one type in the existing hierarchy:

```python
class PushFailed(FactoryError):
    branch: str
    outcome: PushOutcome
    def __init__(self, branch: str, outcome: PushOutcome) -> None: ...
```

`src/factory/application/claims.py`

```python
class StageStart(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    commit: CommitId  # the pushed stage-start commit
    claim: Claim

def started_text(stage: str, instance: str) -> str: ...  # "started <stage> as <instance>."

class ClaimService:
    def __init__(self, boundaries: Boundaries, instance: str, definition: PipelineDefinition) -> None: ...
    def claim(self, branch: str, path: str, document: WorkItemDocument, stage: str) -> StageStart: ...
```

`path` is the work item's repository-relative POSIX path; the file is written at `boundaries.checkout / path`. `Claim`, `WorkItemDocument`, `NewEntry`, `append_entry`, `PipelineDefinition`, `Boundaries`, `CommitId` and `PushOutcome` are the interface sheet's.

Rules:

- `instance` must match `^[a-z][a-z0-9-]*$`; otherwise `ClaimService(...)` raises `ValueError` before anything else.
- `claim` checks these preconditions, in this order, before it writes anything. Each violation raises `ValueError` and leaves the work tree, the branch and the remote as they were: `document.state` is not `None`; `stage` equals `document.state.stage`; `stage` is a stage of the definition and has a role; `branch` equals `branch_name(<the id in the file name of path>)` (`parse_work_item_file_name` of the last segment of `path`; a file name that is no work item's raises `ValueError` too), so a claim is made only on the work item's own branch; `boundaries.git.status().branch` equals `branch`.
- The claim is `Claim(instance=<instance>, stage=<stage>, started_at=boundaries.clock.now(), lease_duration=<the stage's role's lease_duration>)`; `started_at` is UTC. The lease is copied from the definition the caller loaded and gave to `ClaimService(...)` (normally the load of `origin/main`, which the stage-start commit contains); S0003 reads the write paths from the definition as the stage-start commit holds it.
- The new document is the given one with `state.claim` set to the claim and one journal entry appended with `append_entry(document, NewEntry(speaker="factory", kind="started", text=started_text(stage, instance)))`. Nothing else changes: the other state fields and the body outside the journal section stay as given. A claim already in the document is replaced; whether to claim at all is the caller's judgement (S0002 gives it `status`).
- The document is written at `path` with `boundaries.work_item_writer`, committed with `boundaries.git.commit("<stage> starts as <instance>")` (which stages every change in the work tree, the caller's uncommitted preparation included) and pushed with `boundaries.git.push(branch)`. `StageStart.commit` is the commit's id.
- A push outcome other than `"pushed"` raises `PushFailed(branch, outcome)`. Its message names the branch and the outcome. The local commit stays on the local branch; the remote is unchanged, so there is no claim. Recovering the local branch is the next tick's restore (F0006).
- `InjectedKill` raised inside `push` (the `BEFORE_PUSH` point) is not caught.

Tests: `tests/application/test_claims.py`, with the shared fixtures `remote`, `checkout`, `human`, `clock` and `boundaries`. The test reads what the remote holds through a second `GitCli` clone of `remote`; a rejected push is made by `human.push_file(branch, path, text)` on the work item's branch; an unreachable remote by moving the bare repository away. Each test sets the work item up on the branch before `claim`: push the definition to `main` where it needs another one, `checkout.fetch()`, `checkout.checkout(branch_name(id), start_point="origin/main")`, then write a work item with `initial_state(stage)`, journal entry 1 and a `## Journal` section at `factory/features/F0001-example/in-progress/F0001-S0001-first.md` (the fixture's backlog story has no state and no journal section, so `append_entry` would raise `WorkItemFormatError` on it). A helper in the test module does this. Criterion 17 builds the model through a variable typed `type[BaseModel]` and assigns with `setattr(instance, field, value)`, the field's name in a variable, as `CLAUDE.md` asks under *Tests*.

## Acceptance criteria

1. `claim` returns a `StageStart` whose `claim.instance` is the service's instance, whose `claim.stage` is the stage and whose `claim.started_at` equals `boundaries.clock.now()` at the call, in UTC.
2. `claim.lease_duration` is the `lease_duration` of the stage's role: 60 for the fixture's `intake` role, which sets none, and 45 for a definition that sets 45 on it.
3. `StageStart.commit` is pushed: after the call `origin/<branch>` resolves to it, the local branch's head is the same commit, and a second clone of the remote shows it as the head of the branch.
4. The stage-start commit is one commit directly on top of the branch's previous head, and its subject is `<stage> starts as <instance>`.
5. The work item as the remote holds it at that commit has a `state.claim` equal to the returned claim.
6. At that commit the journal has gained exactly one record, numbered n + 1 for n earlier entries, with speaker `factory` and kind `started`, and the body's journal section ends with the line `<n + 1>. factory: started <stage> as <instance>.`
7. Every other state field and the body outside the journal section equal those of the document passed in.
8. A document that already carries a claim is claimed anew: the new claim replaces the old one and the journal gains a second `started` record.
9. When the push is rejected (the human pushed a commit to the work item's branch after the checkout's last fetch), `claim` raises `PushFailed` with `branch` and `outcome == "rejected"` and a message naming both; the remote's branch head is unchanged, so the remote holds no claim; the local commit stays on the local branch.
10. When the remote is unreachable, `claim` raises `PushFailed` with `outcome == "unreachable"`.
11. With the kill point `BEFORE_PUSH` armed, `InjectedKill` leaves `claim` uncaught, the remote's branch holds no claim, and the local branch holds the commit.
12. `claim` raises `ValueError` and writes nothing (the file, the branch and the remote are as before) when `document.state` is `None`, when `stage` differs from `document.state.stage`, and when `stage` has no role (the fixture's `approval`) or is not a stage of the definition.
13. `claim` raises `ValueError` and writes nothing when the checkout is on another branch than `branch`.
14. `ClaimService(...)` raises `ValueError` for the instance names `Factory-1`, `1factory`, `factory_1` and the empty string, and accepts `factory-1` and `f`.
15. `claim` raises `ValueError` and writes nothing when `branch` is not the work item's own branch: `claim("work-item/F0001-S0002", <path of F0001-S0001>, ...)` with that other branch checked out, and a `path` whose file name is no work item's (`factory/features/F0001-example/in-progress/notes.md`).
16. On a local branch created from `origin/main` that does not exist on the remote, with the work item written in the work tree but not committed (the opening), `claim` makes one commit directly on top of the head of `origin/main` whose tree holds the work item with the claim, and after the push `origin/<branch>` resolves to that commit.
17. `StageStart` is frozen, forbids unknown fields and holds a `CommitId`: assigning to `commit` raises `ValidationError`, building it with an unknown field `extra` raises `ValidationError`, and building it with a `commit` of 39 characters (`"a" * 39`) or an uppercase one (`"A" * 40`) raises `ValidationError`, while `"a" * 40` is accepted.
18. make check stays green.
19. docs: `docs/project-guide.md` describes the claim (the stage-start commit with its "started" entry and the `claim` in the state, that the push is the claim, that the stage-start commit is the last commit before the agent run, and that whatever the caller left uncommitted, for a new branch its opening, is part of it); `docs/decisions.md` records why the push is the claim (R19, R20) and that a rejected push leaves the local commit to the next tick's restore.

## Demo

```bash
uv run python - <<'EOF'
import os, subprocess, tempfile
from dataclasses import replace
from datetime import UTC, datetime
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
from factory.domain.errors import PushFailed
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, initial_state

for name in ('GIT_AUTHOR_NAME', 'GIT_COMMITTER_NAME'):
    os.environ[name] = 'demo'
for name in ('GIT_AUTHOR_EMAIL', 'GIT_COMMITTER_EMAIL'):
    os.environ[name] = 'demo@example.com'

PIPELINE = """contract: "1.0"
stages:
  coder: {role: coder, next: [done]}
  done: {}
roles:
  coder: {write_paths: ["src/*", "{work_item}"]}
"""
BRANCH = 'work-item/F0004-S0001'
PATH = 'factory/features/F0004-demo/in-progress/F0004-S0001-demo.md'
BODY = '# Demo story\n\n## Description\n\nOriginal.\n\n## Journal\n\n1. 2026-10-12 human: created.\n'

root = Path(tempfile.mkdtemp())
remote, seed, work, work2 = root / 'remote.git', root / 'seed', root / 'work', root / 'work2'

def sh(*args, cwd=None):
    subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True)

state = initial_state('coder').model_copy(update={'journal': [JournalRecord(number=1, speaker='human', kind='created')]})
sh('init', '--bare', '-b', 'main', str(remote))
sh('clone', str(remote), str(seed))
(seed / 'factory').mkdir()
(seed / 'factory' / 'pipeline.yml').write_text(PIPELINE)
(seed / PATH).parent.mkdir(parents=True)
(seed / PATH).write_text(FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body=BODY)))
sh('add', '-A', cwd=seed)
sh('commit', '-m', 'seed', cwd=seed)
sh('push', 'origin', 'HEAD:main', cwd=seed)
sh('push', 'origin', 'HEAD:refs/heads/' + BRANCH, cwd=seed)

clock = ManualClock(datetime(2026, 10, 12, tzinfo=UTC))
git, git2 = GitCli(work), GitCli(work2)
for g in (git, git2):
    g.clone(str(remote))
    g.checkout(BRANCH, start_point='origin/' + BRANCH)
b = Boundaries(git=git, hosting=FakeHostingService(), agent_runtime=FakeAgentRuntime(), project_commands=MakeProjectCommands(work), work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(), cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(), clock=clock, log=TimestampedFactoryLog(root / 'factory.log', clock), health=JsonHealthStatusFile(root / 'health.json'), pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(root / 'claude'), checkout=work)
b2 = replace(b, git=git2, project_commands=MakeProjectCommands(work2), checkout=work2)
definition = b.pipeline_reader.parse(PIPELINE)

start = ClaimService(b, 'factory-1', definition).claim(BRANCH, PATH, b.work_item_reader.read(work / PATH), 'coder')
print(start.claim.instance, start.claim.stage, start.claim.lease_duration)
print(git.resolve('origin/' + BRANCH) == start.commit)
text = git.show_file('origin/' + BRANCH, PATH)
shown = b.work_item_reader.parse(text)
print(shown.state.claim == start.claim, [(r.number, r.speaker, r.kind) for r in shown.state.journal])
print([line for line in text.splitlines() if line.startswith('2. ')])
try:
    ClaimService(b2, 'factory-2', definition).claim(BRANCH, PATH, b2.work_item_reader.read(work2 / PATH), 'coder')
except PushFailed as error:
    print(type(error).__name__, error.branch, error.outcome)
rev = subprocess.run(['git', '--git-dir', str(remote), 'rev-parse', BRANCH], capture_output=True, text=True)
print(rev.stdout.strip() == start.commit)
EOF
```
Expect: six lines. `factory-1 coder 60`; `True`; `True [(1, 'human', 'created'), (2, 'factory', 'started')]`; `['2. factory: started coder as factory-1.']`; `PushFailed work-item/F0004-S0001 rejected` (the second instance, whose clone had not seen the first claim, does not get the stage); `True` (the remote's branch is still the first instance's stage-start commit).

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory.domain.errors.PushFailed`, `factory.application.claims` with `StageStart`, `started_text`, `ClaimService.__init__` and `claim`). Every rule is stated exactly: the instance regex, the order of the preconditions, the claim's fields, the commit subject, the journal text and the push handling. The format check passed.
   - Criteria: each is testable by one test function. Every Interface rule has a criterion for its failing side. Instance name: 14. Preconditions (no state, stage mismatch, no role, unknown stage): 12. Wrong checked-out branch: 13. Branch not the item's own, and a file name that is no work item's: 15. Push rejected: 9. Push unreachable: 10. Kill before push: 11. `StageStart` field limits (39 characters, uppercase, unknown field, frozen): 17. Pass sides are covered by 1–8 and 16. Interface behaviours (lease copy, UTC, journal line, the previous claim replaced, the uncommitted opening) map to 2, 1, 6, 8 and 16.
   - Demo: runnable as written, using only the interface sheet's adapters. Each `Expect:` line gives checkable output: six lines with exact values, including the rejected second instance and the unchanged remote head.
   - Architecture: `ClaimService` is in `factory.application` and reaches git and the clock only through `Boundaries`. The error is in `factory.domain`. The DTO is frozen Pydantic. No layer violation and no new dependency.
   - Scope: within the feature's Scope (first bullet) and the FEATURE.md decisions 1–4, 17 and 18. Nothing from "Out of scope" (agent start, status, release, write paths) is touched.
3. tester: wrote the red tests for the claim service in one new file, `tests/application/test_claims.py`. A helper `_prepare` fetches, checks out `work-item/F0001-S0001` from `origin/main` and writes the work item at `factory/features/F0001-example/in-progress/F0001-S0001-first.md`. The work item has `initial_state("intake")`, journal entry 1 and a `## Journal` section. By default the helper commits and pushes it; with `committed=False` it leaves the item uncommitted, the opening for criterion 16. The remote side is read through a second `GitCli` clone and `git_support.remote_commit`. The "writes nothing" checks compare a snapshot before and after `claim`: `git.status()`, the file text and the remote's head of the branch.

   Criterion → test:
   - criterion 1: tests/application/test_claims.py::test_claim_records_instance_stage_and_start_time_in_utc
   - criterion 2: tests/application/test_claims.py::test_claim_copies_the_lease_duration_of_the_stages_role (parametrized: the fixture's role gives 60; with 45 set on `intake`, pushed to main and passed to the service, it gives 45)
   - criterion 3: tests/application/test_claims.py::test_stage_start_commit_is_pushed_to_the_remote
   - criterion 4: tests/application/test_claims.py::test_stage_start_commit_is_one_commit_on_the_previous_head_with_its_subject
   - criterion 5: tests/application/test_claims.py::test_pushed_work_item_holds_the_returned_claim
   - criterion 6: tests/application/test_claims.py::test_claim_appends_one_started_journal_entry (also checks `started_text`)
   - criterion 7: tests/application/test_claims.py::test_claim_keeps_every_other_state_field_and_the_body_outside_the_journal
   - criterion 8: tests/application/test_claims.py::test_a_document_with_a_claim_is_claimed_anew
   - criterion 9: tests/application/test_claims.py::test_a_rejected_push_raises_push_failed_and_leaves_the_remote_without_claim
   - criterion 10: tests/application/test_claims.py::test_an_unreachable_remote_raises_push_failed (the bare remote is renamed away)
   - criterion 11: tests/application/test_claims.py::test_a_kill_before_push_is_not_caught_and_leaves_the_remote_without_claim
   - criterion 12: tests/application/test_claims.py::test_claim_refuses_a_document_or_stage_it_cannot_claim_and_writes_nothing (parametrized: no state, other stage, `approval`, unknown stage `nowhere`)
   - criterion 13: tests/application/test_claims.py::test_claim_refuses_when_another_branch_is_checked_out_and_writes_nothing
   - criterion 14: tests/application/test_claims.py::test_service_refuses_an_instance_name_that_is_no_name and ::test_service_accepts_an_instance_name
   - criterion 15: tests/application/test_claims.py::test_claim_refuses_a_branch_that_is_not_the_work_items_own_and_writes_nothing and ::test_claim_refuses_a_path_whose_file_name_is_no_work_items_and_writes_nothing
   - criterion 16: tests/application/test_claims.py::test_claim_on_a_new_branch_commits_the_uncommitted_opening_on_main
   - criterion 17: tests/application/test_claims.py::test_stage_start_is_frozen, ::test_stage_start_forbids_an_unknown_field and ::test_stage_start_commit_is_a_commit_id (parametrized: `"a"*40` accepted, `"a"*39` and `"A"*40` refused)
   - criteria 18 and 19 are not tested here: 18 is `make check`, 19 is the docs stage.

   Files created: tests/application/test_claims.py.

   Not importable: `factory.application.claims` (ModuleNotFoundError at collection), so the whole module fails to collect, as intended. `factory.domain.errors.PushFailed` is missing too. `make lint` is green.

   Rejected: a separate domain test for `PushFailed`. Criterion 9 already checks its fields and message, and no other criterion names it.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: the claim service is built and committed (3ac70cc): `PushFailed` is in `src/factory/domain/errors.py` and `StageStart`, `started_text` and `ClaimService` are in `src/factory/application/claims.py`. `make lint`, types, layers, sast, secrets and licences are green. Of the tests, everything passes except one, and that one fails because of a fault in the test itself, not in the code.

   Failing test: `tests/application/test_claims.py::test_claim_copies_the_lease_duration_of_the_stages_role[role-default]`. In both cases the test first runs `human.push_file("main", PIPELINE_FILE, pipeline)`. In the `role-default` case `pipeline` is `PIPELINE_YAML`, and the fixture's `main` already holds exactly that text at `factory/pipeline.yml`. So the human's commit has nothing to commit and `HumanClone.push_file` raises `NothingToCommit` before `claim` is called. No implementation can make this case pass. The `role-sets-45` case passes.

   Options:
   (a) The tester skips the push to `main` when `pipeline == PIPELINE_YAML`. For example, the parametrization could carry `None` for "keep the fixture's definition" and push only when it is set.
   (b) The tester drops the push from the test and passes only the parsed definition to `ClaimService`. The lease is read from the definition given to the constructor, not from the file on `main`, so the push is not what criterion 2 checks.
   (c) Change `HumanClone.push_file` so it tolerates an unchanged file. This touches a shared test helper and changes its behaviour for every test, so I would not do it.

   I would choose (a). It keeps the "the definition on main holds 45" setup for the 45 case, and the default case becomes a plain claim against the fixture's definition. After your answer I will end with `tests` and name exactly that change.

   Not refactored yet: the refactor pass comes after the tests are green.
5. human (pull request comment, 2026-10-14): (a): the parametrization carries `None` for "keep the fixture's definition", and the test pushes to `main` only when it is set; the `role-sets-45` case keeps its push. Leave `HumanClone.push_file` as it is. End with `tests` and name exactly that change.
6. coder: the human's answer (entry 5, option (a)) calls for one test change. The code in 3ac70cc is unchanged and I did not touch the test. Change for the tester: in `tests/application/test_claims.py::test_claim_copies_the_lease_duration_of_the_stages_role`, the `role-default` case's parameter becomes `None` instead of `PIPELINE_YAML`, meaning "keep the fixture's definition". The test calls `human.push_file("main", PIPELINE_FILE, pipeline)` and builds the definition from `pipeline` only when it is set; when it is `None`, the test claims with the fixture's definition, as the other tests do through `_claim(boundaries, document)`. The `role-sets-45` case keeps its push of `LEASE_45_YAML` and its expected 45, and `HumanClone.push_file` stays as it is. Still open after the tests come back: the refactor pass, then `review`. `## Assignment` is unchanged, because the answer does not change what the task means.
7. tester: tester (test change the human approved, entry 5 option (a), named in the coder's entry 6): changed one test, `tests/application/test_claims.py::test_claim_copies_the_lease_duration_of_the_stages_role`. The `role-default` case's parameter is now `None` instead of `PIPELINE_YAML`, meaning "keep the fixture's definition", and `pipeline` is typed `str | None`. Only when `pipeline` is set does the test call `human.push_file("main", PIPELINE_FILE, pipeline)` and build the definition with `_definition(boundaries, pipeline)`. Otherwise it passes `None` to `_claim`, which falls back to the fixture's definition the way the other tests do. The `role-sets-45` case still pushes `LEASE_45_YAML` and expects 45. The `role-default` case still expects 60. I left `HumanClone.push_file` and every other test unchanged.

   Why: the fixture's `main` already holds `PIPELINE_YAML`, so pushing it again raised `NothingToCommit` before `claim` was called. No implementation could make that case pass.

   `make test`: green, total coverage 99.72%. `make lint`: green.

   `make lint`: lint: green
   `make test`: test: green
8. coder: the claim service from 3ac70cc now passes every test. The tester's change from entry 7 fixed the one failing case, and the code needed no change for it. `make check` is green and coverage is 99.72%.

   Built:
   - `src/factory/domain/errors.py`: `PushFailed(FactoryError)`, which carries `branch` and `outcome` and has the message "push of <branch> failed: <outcome>".
   - `src/factory/application/claims.py`: `StageStart` (frozen, forbids extra fields, holds a `CommitId` and a `Claim`), `started_text`, and `ClaimService`.
     - The constructor checks the instance name against the full pattern `[a-z][a-z0-9-]*` and raises `ValueError` otherwise.
     - `claim` checks the preconditions in the Interface's order before it writes anything: there is a state, the stage matches, the stage is in the definition and has a role (this check also yields the lease), the branch is the work item's own branch, and the checkout is on that branch.
     - It then builds the claim from `clock.now()`, sets `state.claim`, and adds the "started" entry with `append_entry`. It writes the work item at `checkout / path`, commits it as "<stage> starts as <instance>" and pushes.
     - Any push outcome other than "pushed" raises `PushFailed`. `InjectedKill` from the push is not caught.

   Main decision: the lease is read from the `PipelineDefinition` passed to the constructor, not loaded again from `origin/main`. This follows the Interface: the caller loads the definition once. I rejected having the service read the definition through `pipeline_reader` itself, because that would give it a second source of truth for the definition.

   Refactor pass: I read the diff (`git diff main...HEAD -- src`) and found nothing to rename, simplify or remove, so there is no refactor commit.

   Noticed, not touched:
   - `_with_claim` gets the state through `_state_of` a second time. This is harmless because the preconditions have already guaranteed a state exists.
   - The docs criterion (19) is left to the documenter stage.

   `make check`: check: green
9. reviewer: groups 1–3 pass, group 4 (quality) fails.

   - Criteria: I read every one of criteria 1–17 against its test in `tests/application/test_claims.py`. Each test checks what its criterion says.
   - Failing sides: every failing side the Interface states is tested. That covers the instance regex (four refused names, two accepted), each precondition with a writes-nothing snapshot, a rejected push, an unreachable remote, `BEFORE_PUSH` through the `kill_points` fixture that `boundaries` shares, and the `CommitId` limits (39, uppercase, 40).
   - Checks: the coder's entry 8 reports `make check` green.
   - Architecture: `ClaimService` reaches git, the clock and the writer only through `Boundaries`. `PushFailed` sits in `factory.domain.errors` and imports only `factory.domain.git`.
   - Security: no strings passed to a shell, no suppression markers, no secrets.

   Findings:
   1. `src/factory/application/claims.py:83-89` (`_lease_duration_of`): this repeats the stage-to-role lookup that `PipelineDefinition.role_of` (`src/factory/domain/pipeline_definition.py:83`) already does. It also names a `StageDefinition` `definition`, right next to `self._definition`, which is the pipeline definition. Fix: refuse `stage not in self._definition.stages`, then use `self._definition.role_of(stage)`, raise `ValueError` when it is `None`, and return its `lease_duration`.
   2. `src/factory/application/claims.py:92` (`_with_claim`): this calls `_state_of(document)` a second time, after `_check_preconditions` (line 71) has already narrowed the state, so the `ValueError` branch can never run on this path. Fix: pass the narrowed `WorkItemState` from `claim` into `_with_claim`, for example by having `_check_preconditions` return it with the lease, so the check happens once.

   Not a finding: `StageStart` is a Pydantic model in `factory.application`. That is where the Interface puts it, and intake accepted it.
10. coder: coder (round 1): I fixed both of the reviewer's findings from entry 9 in one refactor commit, 2c15695. It changes only `src/factory/application/claims.py`. Behaviour and tests are unchanged. `make check` is green, with total coverage at 99.72%.

    1. `_lease_duration_of` no longer repeats the lookup from stage to role. It first refuses a stage that is not in `self._definition.stages`. It then calls `self._definition.role_of(stage)`, refuses a `None` role and returns `role.lease_duration`. The `StageDefinition` variable named `definition` is gone, so nothing shadows the pipeline definition any more. The order of the preconditions and their `ValueError` messages are the same as before.
    2. `claim` now narrows the state once, with `state = _state_of(document)`, and gives that `WorkItemState` to both `_check_preconditions` (whose parameter changes from `document` to `state`) and `_with_claim(document, state, claim)`. The second `_state_of` call, which could never fail, is gone. "No state" is still the first precondition checked.

    What I rejected: the reviewer suggested making `_check_preconditions` return a `(state, lease)` tuple. Narrowing the state in `claim` does the same job with no tuple return value.

    Process note: my first commit for this round piped `make check` into `tail`, so its failed exit status was hidden and the commit went in with an unformatted line. I ran `ruff format`, ran `make check` again (green) and amended the local commit, which had not been pushed, so only 2c15695 remains.

    I noticed nothing else and touched nothing else.

    `make check`: check: green
