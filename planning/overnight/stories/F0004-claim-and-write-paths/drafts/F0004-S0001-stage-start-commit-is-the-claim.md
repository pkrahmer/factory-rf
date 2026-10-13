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

Tests: `tests/application/test_claims.py`, with the shared fixtures `remote`, `checkout`, `human`, `clock` and `boundaries`. The test reads what the remote holds through a second `GitCli` clone of `remote`; a rejected push is made by `human.push_file(branch, path, text)` on the work item's branch; an unreachable remote by moving the bare repository away. Each test sets the work item up on the branch before `claim`: push the definition to `main` where it needs another one, `checkout.fetch()`, `checkout.checkout(branch_name(id), start_point="origin/main")`, then write a work item with `initial_state(stage)`, journal entry 1 and a `## Journal` section at `factory/features/F0001-example/in-progress/F0001-S0001-first.md` (the fixture's backlog story has no state and no journal section, so `append_entry` would raise `WorkItemFormatError` on it). A helper in the test module does this.

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
17. make check stays green.
18. docs: `docs/project-guide.md` describes the claim (the stage-start commit with its "started" entry and the `claim` in the state, that the push is the claim, that the stage-start commit is the last commit before the agent run, and that whatever the caller left uncommitted, for a new branch its opening, is part of it); `docs/decisions.md` records why the push is the claim (R19, R20) and that a rejected push leaves the local commit to the next tick's restore.

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
