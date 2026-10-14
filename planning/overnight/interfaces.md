# Interface sheet: modules, DTOs and interfaces shared by the features of v1.1

Status: proposed, written unattended on 2026-10-12/13 under decision 007, question 1. The stories copy names and signatures from here into their `## Interface` sections. A name used by one feature only is that feature's to choose; everything that crosses a feature boundary is fixed below.

## Summary

- 86 modules under `src/factory/` in the four layers (31 domain, 32 application, 16 adapters, 7 entry), each with the story that creates it; tests mirror them under `tests/<layer>/`.
- The shared DTOs are frozen Pydantic models that forbid unknown keys, with their rules written as comments. They include the work item's state in the front matter (`stage`, `blocked`, `round`, `attempts`, `crashes`, `pull_request`, `comments_read`, `handed_over`, `claim`, `journal`), the cost record, the check result, the pipeline definition and the agent run request and result.
- Interfaces live in `factory.application` as `typing.Protocol`s. They cover git, the hosting service (exactly R10's operations), the project commands, the agent runtime and the agent definitions, and one reader and one writer per file format. Three more cover the machine: clock, factory log and health status. Each has its first implementation in `factory.adapters`, plus `FakeHostingService` and `FakeAgentRuntime`.
- One error hierarchy is rooted in `FactoryError` in `factory.domain.errors`. For each error type the sheet says which layer raises it and what it becomes: a counted error, a repository or machine stop, or nothing (a stall is a result and is never raised). The kill points raise `InjectedKill`, which is a `BaseException` so that no handler can survive it.
- Four named kill points cover every row of section 7.2: `agent-run`, `before-push`, `after-post` and `after-push`. The stall rows need no kill point, because the fake agent runtime returns `died` or `time_limit` for them.
- Posts are keyed (answer 4). `HostingService.post_comment` takes a `PostKey` and posts nothing when a comment with that key already exists.
- The journal shows `<number>. <date> <speaker>: <text>`, with a date on the human's entries only. Its speaker and kind are kept as data in the front matter list `journal`. The lease clock is three pure functions in `factory.domain.lease`.
- Spellings fixed here (answer 5): folders `backlog/`, `in-progress/`, `done/`; the file `factory/pipeline.yml`; branches `work-item/<id>`; the headings `## Description`, `## Interface`, `## Acceptance criteria`, `## Smoke test`, `## Journal`; acceptance ids `F0001-A0001`.
- 14 open questions, most of them choices made here where v1's spelling or default was not in the inputs.

Notation. An operation's tag `[F0001-S0004 | F0006]` means: built by that story, and first needed by a story of that feature. "Built by F0001" means the boundary stories; "needed" means the first feature whose criteria call it.

## Package layout

Every module needs a module docstring, and so does every package `__init__.py` (`D104` is on). Paths of files inside a project are repository-relative POSIX strings everywhere; only the checkout root, the agent home and the state directory are `Path`s.

### `factory.domain` (pure data and rules, no I/O, no clock)

| Module | Purpose | Created by |
|---|---|---|
| `factory.domain.errors` | The one exception hierarchy (section Errors); later stories add their types here | F0001-S0001 |
| `factory.domain.kill_points` | `KillPoint`, `InjectedKill`, `KillPoints`: the injection seam (R36) | F0001-S0001 |
| `factory.domain.hosting` | Pull request DTOs, `PostKey`, the marker and the rendering and parsing of a post's key | F0001-S0002 |
| `factory.domain.git` | Git DTOs: commit ids, changed paths, status, push and merge outcomes | F0001-S0004 |
| `factory.domain.checks` | `CheckResult`, the generic result of a project command (R8) | F0001-S0006 |
| `factory.domain.agent_runs` | `AgentDefinition`, `AgentRunRequest`, `AgentRunResult`, `GuardSettings`, `TokenCounts` | F0001-S0007 |
| `factory.domain.identifiers` | Id patterns, file-name parsing, branch names, `work_item_order` | F0002-S0001 |
| `factory.domain.paths` | Folder and file names of the project's `factory/` tree, the main branch and the remote | F0002-S0001 |
| `factory.domain.work_item` | `WorkItemState`, `Claim`, `WorkItemDocument`, `initial_state`; later `WorkItemSnapshot` (F0006-S0001) | F0002-S0002 |
| `factory.domain.journal` | `JournalRecord`, `NewEntry`, append, render, restore (SI1.1) | F0002-S0003 |
| `factory.domain.sections` | Title and `## ` sections outside code fences, insert under a heading (SI1.3) | F0002-S0004 |
| `factory.domain.story_form` | `FormFinding` and the story form check (kept 9) | F0002-S0005 |
| `factory.domain.cost_records` | `CostRecord` (R24) | F0002-S0006 |
| `factory.domain.stops` | `WorkItemStop`, `RepositoryStop`, `HealthStatus`, `StopPosted` (R27) | F0003-S0001 |
| `factory.domain.post_texts` | The texts of the factory's posts and notes; later stories add theirs | F0003-S0002 |
| `factory.domain.pipeline_definition` | The pipeline definition's schema, defaults and load-time rules (R30, ST8) | F0003-S0003 |
| `factory.domain.lease` | The lease clock: age, expiry and `claim_status` (decision 007, question 4) | F0004-S0002 |
| `factory.domain.write_paths` | Write-path matching, placeholders and `PROTECTED_PATHS` (R32) | F0004-S0003 |
| `factory.domain.prompts` | The prompt's lines and the allowed decisions of a stage | F0005-S0001 |
| `factory.domain.decisions` | Decision rules 1 to 7 over a stage's result | F0005-S0006 |
| `factory.domain.labels` | `labels_for(state)`: the labels as a projection of the stage | F0005-S0007 |
| `factory.domain.bills` | `Bill`, `StageBill`, sums of cost records, the cost line and the cost table | F0005-S0009 |
| `factory.domain.run_record` | `RunRecord`, the local cache for the board (answer 2) | F0005-S0003 |
| `factory.domain.events` | `EventKind`, `Event` | F0006-S0002 |
| `factory.domain.evaluation` | The four tiers over snapshots, giving one event (R26) | F0006-S0002 |
| `factory.domain.tick_status` | `ErrorCount`, `TickStatus`, `ERROR_CAP` (R28) | F0006-S0003 |
| `factory.domain.move_rule` | Legal stage changes under the pipeline definition (ST2.3, ST2.4) | F0006-S0005 |
| `factory.domain.board` | `BoardRow`, `FeatureRow`, `AcceptanceStatus` | F0006-S0006 |
| `factory.domain.acceptance` | When an acceptance is due, its derived states and its facts (ST6.2) | F0009-S0001 |
| `factory.domain.settings` | `InstanceSettings` read from the environment (R25) | F0010-S0001 |
| `factory.domain.preflight` | `PreflightItem`, the preflight's items and the image stamp | F0010-S0004 |

### `factory.application` (use cases and the interfaces they need)

| Module | Purpose | Created by |
|---|---|---|
| `factory.application.hosting` | `HostingService` protocol (R10) | F0001-S0002 |
| `factory.application.git` | `Git` protocol (R9) | F0001-S0004 |
| `factory.application.project_commands` | `ProjectCommands` protocol (R11) | F0001-S0006 |
| `factory.application.agent_runtime` | `AgentRuntime` protocol (R12); `AgentDefinitionReader` protocol (F0003-S0004) | F0001-S0007 |
| `factory.application.files` | Reader and writer protocols per format (R13) | F0002-S0002 |
| `factory.application.machine` | `Clock`, `FactoryLog`, `HealthStatusStore`; `RunRecordStore` (F0005-S0003) | F0003-S0001 |
| `factory.application.boundaries` | `Boundaries`, the holder of every interface that wiring passes to services | F0003-S0001 |
| `factory.application.stops` | `StopService`: every stop to its one destination | F0003-S0001 |
| `factory.application.pipeline_loading` | `PipelineLoader`: read, validate, check installed agents | F0003-S0004 |
| `factory.application.claims` | `ClaimService`: claim, recognition, expiry, release (GH1.2) | F0004-S0001 |
| `factory.application.write_paths` | `WritePathService`: the guard settings at the stage-start commit | F0004-S0003 |
| `factory.application.undo` | `UndoService`: undo and restore after an agent run (WE2) | F0004-S0005 |
| `factory.application.task` | Agent definitions to a request: the prompt, decisions, guard, `time_limit` | F0005-S0001 |
| `factory.application.opening` | Opening and preparing the work item's branch and its draft pull request | F0005-S0002 |
| `factory.application.stage` | The stage protocol: claim, agent run, undo, entry, decision, checks, result commit | F0005-S0003 |
| `factory.application.stalls` | A stall: attempt, entry, partial work, note | F0005-S0004 |
| `factory.application.costs` | Cost records at agent run start and end; bills from the records | F0005-S0008 |
| `factory.application.work_items` | Work items read from the remote-tracking refs as snapshots (R18) | F0006-S0001 |
| `factory.application.watcher` | The evaluation with its one pull request lookup | F0006-S0002 |
| `factory.application.dispatcher` | `Handler` protocol, `Dispatcher`, counted errors (R28) | F0006-S0003 |
| `factory.application.tick` | One tick: fetch, restore checkout, load, evaluate, dispatch | F0006-S0004 |
| `factory.application.handlers.comments` | `comment` events: copy by id, answers (GH3.1, ST1.1) | F0007-S0001 |
| `factory.application.handlers.questions` | `ask` events: recorded questions posted | F0007-S0002 |
| `factory.application.handlers.merged` | `merged` events: archive with the bill | F0007-S0003 |
| `factory.application.handlers.closed` | `closed` events: discard, send-back | F0007-S0004 |
| `factory.application.handlers.reject` | `reject` events: an illegal stage change moved back | F0007-S0006 |
| `factory.application.handlers.lookups` | `duplicate` and `pull_request_lookup` events (ST3.1) | F0007-S0008 |
| `factory.application.handlers.hand_over` | `hand_over` events (ST1.2, ST1.3) | F0007-S0009 |
| `factory.application.recovery` | `crash` and `expired` handlers (GH2, ST1.4) | F0008-S0001 |
| `factory.application.acceptance` | The acceptance stage and its approval; `acceptance_due` handler | F0009-S0002 |
| `factory.application.preflight` | The preflight's items, the probe and its stamp | F0010-S0004 |
| `factory.application.scheduler` | The loop with its pauses (15 s, doubling to 120 s) | F0010-S0001 |

### `factory.adapters` (wrappers, readers, writers, fakes)

| Module | Purpose | Created by |
|---|---|---|
| `factory.adapters.fake_hosting` | `FakeHostingService`, the one fake of the hosting service (SI2.3) | F0001-S0002 |
| `factory.adapters.pygithub_hosting` | `PyGithubHostingService`, the only module that imports `github` (SI2.1) | F0001-S0003 |
| `factory.adapters.process` | `run_process`, the one place that starts a subprocess for the wrappers | F0001-S0004 |
| `factory.adapters.git_cli` | `GitCli`, the git command-line wrapper | F0001-S0004 |
| `factory.adapters.make_commands` | `MakeProjectCommands`, project commands as make targets | F0001-S0006 |
| `factory.adapters.fake_agent_runtime` | `FakeAgentRuntime` and `ScriptedRun` | F0001-S0007 |
| `factory.adapters.claude_runtime` | `ClaudeCodeRuntime`, the `claude -p` wrapper | F0001-S0008 |
| `factory.adapters.work_item_markdown` | `FrontmatterWorkItemReader`, `FrontmatterWorkItemWriter` | F0002-S0002 |
| `factory.adapters.cost_records_jsonl` | `JsonLinesCostRecordReader`, `JsonLinesCostRecordWriter` | F0002-S0006 |
| `factory.adapters.clock` | `SystemClock`, `ManualClock` (tests) | F0003-S0001 |
| `factory.adapters.factory_log` | `TimestampedFactoryLog`: standard output and the factory log file | F0003-S0001 |
| `factory.adapters.health_file` | `JsonHealthStatusFile` | F0003-S0001 |
| `factory.adapters.pipeline_yaml` | `RuamelPipelineDefinitionReader` | F0003-S0003 |
| `factory.adapters.agent_files` | `FrontmatterAgentDefinitionReader` (agent files in the agent home) | F0003-S0004 |
| `factory.adapters.claude_guard` | The guard hook's payload from Claude Code, to a path and a verdict | F0004-S0004 |
| `factory.adapters.run_record_file` | `JsonRunRecordFile` | F0005-S0003 |

### `factory.entry` (command line and wiring; nothing else wires)

| Module | Purpose | Created by |
|---|---|---|
| `factory.entry.wiring` | `build_boundaries(settings) -> Boundaries`: picks the concrete adapters | F0002-S0005 (grown by each command) |
| `factory.entry.check_story` | `factory-check-story <path>`: the form check for the human | F0002-S0005 |
| `factory.entry.guard` | `factory-guard --settings <file>`: the write-path guard hook command | F0004-S0004 |
| `factory.entry.bill` | `factory-bill [<work item id>]`: prints the cost table and cost line | F0005-S0009 |
| `factory.entry.watch` | `factory-watch`: evaluate once and print the board; no `--follow` (SI3.1) | F0006-S0006 |
| `factory.entry.run` | `factory-run`: the entrypoint loop of one instance | F0010-S0001 |
| `factory.entry.health` | `factory-health`: exit status 1 while the health status holds a stop | F0010-S0003 |

Console scripts in `pyproject.toml` use these names. Test modules mirror the package (`tests/domain/test_journal.py` and so on), and each test folder has an `__init__.py`.

### Shared test fixtures (`tests/conftest.py`)

These are shared by every feature's tests, so their names are fixed here. `kill_points` is `KillPoints()`. `clock` is `ManualClock(datetime(2026, 10, 12, 12, 0, tzinfo=UTC))`. `remote` is a bare repository in `tmp_path` whose `main` holds `factory/pipeline.yml` (the YAML below), `factory/story-form.md` and one feature folder. `checkout` is a `GitCli` on a clone of `remote`, with `kill_points`. `human` is a `HumanClone`, a second clone driven through `GitCli`, with `start(path)` (move a backlog story to `in-progress/` and push), `push_file(branch, path, text)` and `merge(branch, method)` (`"merge"`, `"squash"` or `"rebase"`, pushed to `main`). `hosting` is `FakeHostingService(kill_points)`. `agent_runtime` is `FakeAgentRuntime(kill_points)`. `boundaries` is a `Boundaries` built from these.

```yaml
# factory/pipeline.yml of the fixture (and the shape of the template F0010 ships)
contract: "1.0"
attempts_cap: 2
crash_cap: 2
acceptance_stage: acceptance
project_commands:
  check: {time_limit: 10}
  lint: {time_limit: 5}
  test: {time_limit: 10}
roles:
  intake: {write_paths: ["{work_item}"]}
  tester: {write_paths: ["tests/*"]}
  coder: {write_paths: ["src/*"]}
  reviewer: {write_paths: ["{work_item}"]}
  documenter: {write_paths: ["README.md", "docs/*"]}
  smoke-tester: {write_paths: ["{work_item}"]}
  acceptance-reviewer: {write_paths: ["{work_item}", "{feature}/backlog/*"]}
stages:
  intake: {role: intake, next: [tests]}
  tests: {role: tester, next: [doing], checks: [lint], reports: [test]}
  doing: {role: coder, next: [review, tests], checks: [check]}
  review: {role: reviewer, next: [docs, doing], round_cap: 3}
  docs: {role: documenter, next: [smoke-test, doing], checks: [check], round_cap: 3}
  smoke-test: {role: smoke-tester, next: [approval, doing], round_cap: 3}
  acceptance: {role: acceptance-reviewer, next: [approval]}
  approval: {approval: true, next: [done, doing]}
  done: {}
```

## DTOs

Common rules for every model below: `model_config = ConfigDict(frozen=True, extra="forbid")`, so a change is a `model_copy(update=...)`. Datetimes are `AwareDatetime` and are converted to UTC by a validator. A field marked "unknown" is `None` and is never `0`. `WorkItemId`, `CommitId` and the name types are `Annotated[str, StringConstraints(pattern=...)]`.

### Identifiers and paths (F0002-S0001; used by every later feature)

```python
# factory/domain/identifiers.py
FEATURE_ID = r"F\d{4}"
STORY_ID = r"F\d{4}-S\d{4}"
ACCEPTANCE_ID = r"F\d{4}-A\d{4}"
WorkItemId = Annotated[str, StringConstraints(pattern=r"^F\d{4}-[SA]\d{4}$")]
FeatureId = Annotated[str, StringConstraints(pattern=r"^F\d{4}$")]
Name = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$")]  # stage, role, instance names

class WorkItemFileName(BaseModel):
    id: WorkItemId
    slug: str | None                      # "[a-z0-9][a-z0-9-]*"; may start with a digit (ST6.3)

class FeatureDirectoryName(BaseModel):
    id: FeatureId
    slug: str | None

def parse_work_item_file_name(name: str) -> WorkItemFileName | None: ...   # "F0001-S0001-slug.md"; None if no match
def parse_feature_directory_name(name: str) -> FeatureDirectoryName | None: ...  # "F0001-slug" or "F0001"
def is_acceptance(work_item: WorkItemId) -> bool: ...
def feature_of(work_item: WorkItemId) -> FeatureId: ...
def work_item_order(work_item: WorkItemId) -> tuple[str, int, str]: ...
    # (feature id, 0 for a story or 1 for an acceptance, id). Within a kind the order is plain
    # string order (kept 15). An acceptance sorts after every story of its feature, whatever
    # the slug or no slug (ST6.3), because the slug is not part of the id.
def branch_name(work_item: WorkItemId) -> str: ...            # "work-item/F0001-S0001"
def work_item_of_branch(branch: str) -> WorkItemId | None: ...
```

```python
# factory/domain/paths.py
REMOTE = "origin"
MAIN_BRANCH = "main"
FACTORY_DIRECTORY = "factory"
PIPELINE_DEFINITION_FILE = "factory/pipeline.yml"
STORY_FORM_FILE = "factory/story-form.md"
FEATURE_FORM_FILE = "factory/feature-form.md"
FEATURES_DIRECTORY = "factory/features"
FEATURE_FILE_NAME = "feature.md"                       # factory/features/F0001-slug/feature.md
LifecycleFolder = Literal["backlog", "in-progress", "done"]
LIFECYCLE_FOLDERS: tuple[LifecycleFolder, ...] = ("backlog", "in-progress", "done")
V1_LIFECYCLE_FOLDERS = ("drafts", "ongoing")           # R26: a work item found in "ongoing" is refused
COST_RECORDS_SUFFIX = ".costs.jsonl"                   # F0001-S0001-slug.md -> F0001-S0001-slug.costs.jsonl
BRANCH_PREFIX = "work-item/"
LABEL_PREFIX = "stage:"
def work_item_path(feature_directory: str, folder: LifecycleFolder, file_name: str) -> str: ...
def cost_records_path(work_item_path: str) -> str: ...
def folder_of(path: str) -> LifecycleFolder | None: ...
```

Story headings, used by the form check, the prompt, the hand-over and the restore: `# <title>` on the first line of the body, then `## Description`, `## Interface`, `## Acceptance criteria`, `## Smoke test`, `## Journal`. The project's story form names its required sections. The factory's code knows only `## Acceptance criteria`, `## Smoke test` (every fenced block followed by a line starting `Expect:`) and `## Journal`, as constants in `factory.domain.sections`: `ACCEPTANCE_CRITERIA`, `SMOKE_TEST`, `JOURNAL`.

### The work item's state and document (F0002-S0002; used by F0004 to F0009)

```python
# factory/domain/work_item.py
Blocked = Literal["question", "attempts_cap", "round_cap", "crash_cap", "send_back"]
    # What the work item waits for. The human's next comment answers it:
    # question -> unblocks; attempts_cap -> unblocks and sets attempts to 0 (ST1.1);
    # crash_cap -> unblocks and sets crashes to 0 (GH2.4); round_cap and send_back -> as F0007 decides.

class Claim(BaseModel):                       # written in the stage-start commit (R20)
    instance: Name                            # the claiming instance's configured name
    stage: Name                               # the stage claimed
    started_at: AwareDatetime                 # UTC, the claiming instance's clock (decision 007, q. 4)
    lease_duration: PositiveInt               # minutes, copied from the role at claim time (R21)

class WorkItemState(BaseModel):               # the YAML front matter; keys written in this order
    stage: Name
    blocked: Blocked | None = None
    round: NonNegativeInt = 0
    attempts: NonNegativeInt = 0
    crashes: NonNegativeInt = 0
    pull_request: PositiveInt | None = None
    comments_read: list[PositiveInt] = []     # ids of the pull request's comments already copied (GH3.1, GH3.2)
    handed_over: Name | None = None           # the stage whose hand-over completed (answer 15)
    claim: Claim | None = None                # set by the stage-start commit, cleared by the stage's result commit
    journal: list[JournalRecord] = []         # speaker and kind of each entry (decision 007, q. 2)
    # Rules: comments_read is sorted ascending with no repeats. claim.stage == stage when claim is set.
    # journal numbers are 1..n in order (see The journal).
    # F0009-S0001 adds AcceptanceState(WorkItemState) with `stories: list[WorkItemId]` and
    # `outcome: Literal["accepted", "refused"] | None = None`.

class WorkItemDocument(BaseModel):
    state: WorkItemState | None               # None only from WorkItemReader.parse_specification
    body: str                                 # Markdown after the front matter, from the "# <title>" line
    ignored_keys: list[str] = []              # front matter keys parse_specification dropped (R26 reads them)

def initial_state(first_stage: str) -> WorkItemState: ...   # stage=first_stage, every counter 0 (ST6.1)

# added by F0006-S0001
class WorkItemSnapshot(BaseModel):            # one work item as the remote shows it (R18)
    id: WorkItemId
    path: str                                 # its path on origin/main
    folder: LifecycleFolder
    branch: str                               # branch_name(id)
    branch_commit: CommitId | None            # head of origin/<branch>; None when the branch does not exist
    document: WorkItemDocument                # from origin/<branch> when it exists; else main's text
                                              # read with parse_specification and state=initial_state(...)
```

### The journal (F0002-S0003; used by F0004, F0005, F0007, F0008, F0009)

```python
# factory/domain/journal.py
HUMAN = "human"
FACTORY = "factory"
Speaker = Name                                # "human", "factory" or a role name of the pipeline definition
JournalKind = Literal[
    "created",     # human: the story entered the pipeline (entry 1, written by the opening)
    "started",     # factory: the stage-start commit's entry (R20)
    "result",      # a role: the agent's entry with its decision applied, the checks' lines below it
    "question",    # a role (its decision) or factory (a cap question): a recorded question
    "comment",     # human: a pull request comment copied by id
    "close",       # human: the pull request closed, recorded before any effect (GH3.3)
    "stall",       # factory
    "crash",       # factory: an own crash, naming the rerun's stage-start commit (answer 1)
    "expiry",      # factory: another instance's lease expired (answer 1)
    "move_back",   # factory: an illegal stage change moved back (reject)
    "send_back",   # factory: a close at the approval sent back
    "done",        # factory: archived, with the bill; also "merged before approval" (R31)
]

class JournalRecord(BaseModel):               # one element of the front matter's `journal` list
    number: PositiveInt
    speaker: Speaker
    kind: JournalKind

class NewEntry(BaseModel):
    speaker: Speaker
    kind: JournalKind
    text: str                                 # non-empty; may span lines
    on: date | None = None                    # required when speaker == "human", forbidden otherwise
```

### Hosting service DTOs (F0001-S0002; used by F0003, F0005 to F0009)

```python
# factory/domain/hosting.py
FACTORY_MARKER = "<!-- factory -->"
PullRequestState = Literal["open", "closed", "merged"]
PostKind = Literal[
    "question", "attempts_cap", "round_cap", "crash_cap", "send_back",
    "stall", "expiry", "correction", "error", "cost_table",
]
PostOutcome = Literal["posted", "already_posted"]

class PullRequestView(BaseModel):
    number: PositiveInt
    branch: str                               # head branch
    title: str
    state: PullRequestState                   # "merged" whatever the merge method (ST2.3)
    draft: bool
    merge_commit: CommitId | None = None      # set exactly when state == "merged"
    url: str

class PostKey(BaseModel):                     # answer 4
    work_item: WorkItemId
    kind: PostKind
    n: str                                    # pattern [0-9a-f]+: the journal entry number the post reports,
                                              # or for kind "error" the first 12 digits of the remote state commit;
                                              # always derived from state on the remote, so a rerun derives the same key
    def comment(self) -> str: ...             # "<!-- factory key=F0001-S0001:question:7 -->"

class PullRequestComment(BaseModel):
    id: PositiveInt
    author: str                               # the login, kept but not used to decide (R34)
    body: str
    created_at: AwareDatetime
    by_factory: bool                          # the body contains FACTORY_MARKER
    key: PostKey | None                       # parsed from the body; None for the human's comments

def render_post(text: str, key: PostKey) -> str: ...   # text, a blank line, FACTORY_MARKER, newline, key.comment()
def parse_post_key(body: str) -> PostKey | None: ...
```

### Git DTOs (F0001-S0004; used by F0004 to F0011)

```python
# factory/domain/git.py
CommitId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
PushOutcome = Literal["pushed", "rejected", "unreachable"]
MergeOutcome = Literal["merged", "fast_forwarded", "up_to_date", "conflict", "not_fast_forward"]
ChangeKind = Literal["added", "modified", "deleted"]     # a rename is a deletion plus an addition

class ChangedPath(BaseModel):
    path: str
    change: ChangeKind

class RemoteBranch(BaseModel):
    name: str                                 # without "origin/"
    commit: CommitId

class CommitInfo(BaseModel):
    commit: CommitId
    parents: list[CommitId]
    subject: str
    author: str
    committed_at: AwareDatetime

class WorkTreeStatus(BaseModel):
    branch: str | None                        # None when HEAD is detached
    head: CommitId | None                     # None in a repository without commits
    changes: list[ChangedPath]                # staged, unstaged and untracked; ignored paths excluded
```

### The check result (F0001-S0006; used by F0005, F0010) (R8)

```python
# factory/domain/checks.py
OUTPUT_TAIL_LINES = 30
CheckStatus = Literal["passed", "failed", "time_limit"]

class CheckResult(BaseModel):                 # no layer names: a project's layers are its own command
    command: str                              # pattern ^[a-z][a-z0-9-]*$, e.g. "check", "lint", "test"
    status: CheckStatus                       # judged by exit status only (kept 8)
    exit_status: int | None                   # None exactly when status == "time_limit"
    duration: timedelta
    last_line: str                            # last non-blank line of the output, "" if none
    output_tail: str                          # last OUTPUT_TAIL_LINES lines of stdout and stderr, interleaved
    # Rule: status == "passed" exactly when exit_status == 0.
    @property
    def passed(self) -> bool: ...
```

### Agent runs (F0001-S0007; used by F0004, F0005, F0008, F0009, F0010)

```python
# factory/domain/agent_runs.py
QUESTION = "question"                         # always an allowed decision (kept 10)
EndReason = Literal["completed", "no_result", "time_limit", "budget", "died"]
    # completed: the runtime returned a valid decision and entry
    # no_result: it ended normally but without a valid structured result
    # time_limit: the request's time_limit was reached and the run was ended
    # budget: the budget was exhausted, after the one resume (v1's rule)
    # died: the process ended abnormally (signal, non-zero exit, unreadable output)

class AgentDefinition(BaseModel):             # an agent file in <agent home>/agents/<name>.md
    name: Name                                # the file name without ".md"; equals the role's name
    model: str
    tools: list[str]
    effort: str | None = None
    budget_usd: Decimal                       # > 0
    instructions: str                         # the file's body
    # F0010-S0006 fixes APPLIED_AGENT_KEYS = frozenset({"model", "tools", "effort", "budget_usd"}),
    # the keys the pinned runtime applies; any other key in the file is refused (SI4.1).

class GuardSettings(BaseModel):               # what the guard hook allows; always from the stage-start commit (R32)
    root: Path                                # the checkout, absolute
    write_paths: list[str]                    # placeholders already expanded
    protected_paths: list[str]

class AgentRunRequest(BaseModel):
    agent: AgentDefinition                    # its budget_usd is the run's budget
    prompt: str
    allowed_decisions: list[str]              # unique, non-empty, contains QUESTION; a stage's `next` plus QUESTION
    time_limit: timedelta                     # > 0
    working_directory: Path                   # absolute; the checkout
    environment: dict[str, str] = {}          # the run's whole environment; nothing is inherited (WE3.2)
    guard: GuardSettings | None = None        # None only in tests of the runtime itself
    os_user: str | None = None                # F0010-S0007: the unprivileged user the run executes as

class TokenCounts(BaseModel):
    input: NonNegativeInt
    output: NonNegativeInt
    cache_read: NonNegativeInt = 0
    cache_creation: NonNegativeInt = 0

class PermissionDenial(BaseModel):
    tool: str
    detail: str

class AgentRunResult(BaseModel):
    end_reason: EndReason
    decision: str | None = None               # set exactly when end_reason == "completed"
    entry: str | None = None                  # set exactly when end_reason == "completed"
    duration: timedelta
    turns: NonNegativeInt | None = None       # unknown when not reported
    tokens: TokenCounts | None = None         # unknown when not reported (R24)
    cost_usd: Decimal | None = None           # unknown when not reported (R24)
    permission_denials: list[PermissionDenial] = []
    @property
    def ok(self) -> bool: ...                 # end_reason == "completed"
```

### The cost record and the bill (records F0002-S0006, bills F0005-S0009; used by F0005, F0007, F0008, F0009, F0010)

```python
# factory/domain/cost_records.py
class CostRecord(BaseModel):                  # one JSON line in the sidecar file (R15, R24)
    run: str                                  # uuid4 hex, unique within the file
    work_item: WorkItemId
    stage: Name
    role: Name
    attempt: NonNegativeInt                   # the attempts counter when the run started
    status: Literal["started", "completed"]
    started_at: AwareDatetime
    duration_seconds: NonNegativeFloat | None = None
    end_reason: EndReason | None = None
    turns: NonNegativeInt | None = None       # unknown
    tokens: TokenCounts | None = None         # unknown
    cost_usd: Decimal | None = None           # unknown; written as a JSON string ("0.4123") or null
    image: str | None = None                  # F0010-S0002: the image identity (ST5.4); None before F0010
    # Rules: status "started" -> duration_seconds, end_reason, turns, tokens, cost_usd all None.
    # status "completed" -> duration_seconds and end_reason set.
    @property
    def ok(self) -> bool: ...                 # status == "completed" and end_reason == "completed"
```

```python
# factory/domain/bills.py
class Bill(BaseModel):
    runs: NonNegativeInt                      # every record, ok or not (GH4.2)
    runs_cost_unknown: NonNegativeInt         # records whose cost_usd is unknown, so not in cost_usd
    duration: timedelta
    turns: NonNegativeInt                     # sum of known turns
    tokens: TokenCounts                       # sum of known tokens
    cost_usd: Decimal                         # sum of known costs

class StageBill(BaseModel):
    stage: Name
    bill: Bill

def bill(records: Sequence[CostRecord]) -> Bill: ...
def bills_by_stage(records: Sequence[CostRecord]) -> list[StageBill]: ...   # in order of first appearance
def cost_line(bill: Bill) -> str: ...          # display only, never read back (SI1.2)
def cost_table(stage_bills: Sequence[StageBill]) -> str: ...   # Markdown table, total row last
```

### The pipeline definition (F0003-S0003; used by F0004 to F0010) (R30)

```python
# factory/domain/pipeline_definition.py
CONTRACT_MAJOR = 1
DONE_STAGE = "done"
RESERVED_NAMES = ("human", "factory", "question")
WORK_ITEM_PLACEHOLDER = "{work_item}"         # in write_paths: the work item's own file
FEATURE_PLACEHOLDER = "{feature}"             # in write_paths: the work item's feature directory

class RoleDefinition(BaseModel):
    write_paths: list[str]                    # required, no default
    lease_duration: PositiveInt = 60          # minutes (R21, GH1.4)
    time_limit: PositiveInt = 40              # minutes: the agent run's time_limit

class StageDefinition(BaseModel):
    role: Name | None = None                  # None: no agent runs here (an approval, done)
    next: list[Name] = []                     # where the stage may move; next[0] is the forward move
    approval: bool = False                    # the human decides here; the hand-over happens on entry
    checks: list[str] = []                    # project commands, in order, after the agent (rule 5)
    reports: list[str] = []                   # project commands after green, recorded only (rule 6)
    round_cap: PositiveInt | None = None      # rework rounds before the human is asked; None: no cap

class ProjectCommandDefinition(BaseModel):
    time_limit: PositiveInt = 10              # minutes

class PipelineDefinition(BaseModel):
    contract: str                             # required, "<major>.<minor>"
    stages: dict[Name, StageDefinition]       # required; YAML order is the pipeline's order
    roles: dict[Name, RoleDefinition]         # required; a role's name is its agent definition's name
    project_commands: dict[str, ProjectCommandDefinition] = {
        "check": ProjectCommandDefinition(), "lint": ProjectCommandDefinition(),
        "test": ProjectCommandDefinition()}
    attempts_cap: PositiveInt = 2
    crash_cap: PositiveInt = 2                # (R23)
    acceptance_stage: Name | None = None      # F0009: an acceptance's first stage
    # Rules (each a ValueError whose message names the fault; the reader wraps it in
    # PipelineDefinitionInvalid):
    # 1. contract matches ^\d+\.\d+$ and its major is CONTRACT_MAJOR (ST8.4).
    # 2. stages is not empty and holds DONE_STAGE, which has no role and an empty next.
    # 3. every name in a next is a stage: "stage <s>: next names unknown stage <t>" (ST8.2).
    # 4. every stage's role is in roles, and every role has at least one write path (ST8.3).
    # 5. an approval stage has no role; no stage or role name is in RESERVED_NAMES.
    # 6. every check and report names a key of project_commands.
    # 7. for each stage with a role: role.time_limit plus the time_limits of its checks and reports
    #    is at most role.lease_duration: "role <r> at stage <s>: <n> min exceed lease_duration <m> min"
    #    (ST8.5, GH1.4).
    # 8. acceptance_stage, when set, names a stage with a role.
    # Whether each role's agent is installed is checked by PipelineLoader (I/O), not here.
    def first_stage(self) -> str: ...                    # the first key of stages
    def role_of(self, stage: str) -> RoleDefinition | None: ...   # KeyError for an unknown stage
    def position(self, stage: str) -> int: ...          # its index; a move to a lower index is a rework
```

### Stops (F0003-S0001, S0002; used by F0005 to F0010) (R27)

```python
# factory/domain/stops.py
RepositoryStopReason = Literal[
    "fetch_failed",                 # GH5.3 (an expired token included)
    "checkout_restore_failed",      # answer 3: the "dirty main branch" stop
    "pipeline_definition_invalid",  # ST8, an agent that is not installed included
    "agent_definition_invalid",     # SI4.3
    "v1_work_item_found",           # R26
    "repository_unavailable",       # the entrypoint waits for the repository (ST3.3)
    "main_branch_failing",          # ST4.5
    "preflight_failed",             # ST3.3, ST5.3
]

class RepositoryStop(BaseModel):              # goes to the health status and a time-stamped line
    scope: Literal["repository", "machine"]   # "machine" for preflight_failed, else "repository"
    reason: RepositoryStopReason
    detail: str                               # names the fault: the key, stage, file or both versions
    at: AwareDatetime

class HealthStatus(BaseModel):                # the file the health check reads
    stops: list[RepositoryStop] = []          # at most one per reason
    @property
    def healthy(self) -> bool: ...            # no stops

class WorkItemStop(BaseModel):                # goes on the work item's pull request, once
    key: PostKey                              # key.work_item is the stop's work item
    branch: str                               # where a draft pull request is opened if there is none
    title: str                                # that pull request's title
    pull_request: PositiveInt | None          # from the work item's state
    text: str                                 # what each possible answer will do (kept 11)

class StopPosted(BaseModel):
    pull_request: PositiveInt                 # the caller records it in the state when opened is True
    opened: bool
    outcome: PostOutcome
```

### Events, tick status, run record and board (F0005-S0003, F0006; used by F0007 to F0010)

```python
# factory/domain/events.py
EventKind = Literal[
    "run",                  # a stage is due: F0005 (registered by F0006-S0003)
    "comment",              # new comments on the pull request: F0007-S0001, S0007
    "ask",                  # a recorded question not yet posted, the attempts-cap question: F0007-S0002
    "merged",               # F0007-S0003; an acceptance's: F0009-S0003, S0004
    "closed",               # F0007-S0004, S0005; an acceptance's: F0009-S0003
    "reject",               # an illegal stage change: F0007-S0006
    "hand_over",            # stage is an approval and handed_over != stage: F0007-S0009
    "crash",                # an own claim found at the first look: F0008-S0001, S0002
    "expired",              # another instance's claim past its lease: F0008-S0003
    "duplicate",            # two work items with one id: F0007-S0008
    "pull_request_lookup",  # the one lookup failed: F0007-S0008
    "acceptance_due",       # F0009-S0001, S0002
    "v1_work_item",         # R26, a repository stop: F0006-S0002
    "idle",                 # nothing to do, or waiting for the human or a held claim
]

class Event(BaseModel):
    kind: EventKind
    work_item: WorkItemSnapshot | None        # None for "idle" and "acceptance_due"
    pull_request: PullRequestView | None = None   # the tick's one lookup, when made
    feature: FeatureId | None = None          # set for "acceptance_due"
    remote_state: CommitId                    # head of the work item's remote branch, else of origin/main
    detail: str = ""
    @property
    def key(self) -> str: ...                 # "<kind>:<work item id, feature id or '-'>"
```

```python
# factory/domain/tick_status.py              (a local cache, may reset on restart: answer 14)
ERROR_CAP = 3

class ErrorCount(BaseModel):
    event_key: str
    remote_state: CommitId
    count: PositiveInt
    reported: bool = False

class TickStatus(BaseModel):
    errors: list[ErrorCount] = []
```

```python
# factory/domain/run_record.py               (a cache for the board only: answer 2, GH1.5)
class RunRecord(BaseModel):
    work_item: WorkItemId
    stage: Name
    instance: Name
    started_at: AwareDatetime
```

```python
# factory/domain/board.py
AcceptanceStatus = Literal["incomplete", "due", "in_flight", "merged_unrecorded", "accepted", "refused"]

class BoardRow(BaseModel):
    work_item: WorkItemId
    title: str
    folder: LifecycleFolder
    stage: Name | None
    blocked: Blocked | None
    claim: Claim | None
    running_since: AwareDatetime | None       # from the run record, display only
    pull_request: PositiveInt | None

class FeatureRow(BaseModel):
    feature: FeatureId
    title: str
    backlog: NonNegativeInt
    in_progress: NonNegativeInt
    done: NonNegativeInt                      # story files only (ST6.2)
    acceptance: AcceptanceStatus | None = None    # filled from F0009-S0001
```

### Shared pure functions (domain)

| Signature | Module | Built by | Needed by |
|---|---|---|---|
| `append_entry(document: WorkItemDocument, entry: NewEntry) -> WorkItemDocument` | journal | F0002-S0003 | F0004 to F0009 |
| `render_entry(number: int, entry: NewEntry) -> str` | journal | F0002-S0003 | F0002 |
| `entry_text(document: WorkItemDocument, number: int) -> str` | journal | F0002-S0003 | F0007 (hand-over; display only) |
| `last_record(document: WorkItemDocument, *, speaker: str \| None = None, kind: JournalKind \| None = None) -> JournalRecord \| None` | journal | F0002-S0003 | F0007, F0009 |
| `restore_state_and_journal(current: WorkItemDocument, baseline: WorkItemDocument) -> WorkItemDocument` | journal | F0002-S0003 | F0004-S0005 |
| `title(body: str) -> str \| None` | sections | F0002-S0004 | F0005, F0007, F0009 |
| `sections(body: str) -> list[Section]` (`Section(heading: str, start: int, end: int)`, line indexes, end exclusive) | sections | F0002-S0004 | F0005, F0007 |
| `section_text(body: str, heading: str) -> str \| None` | sections | F0002-S0004 | F0005, F0007, F0009 |
| `insert_paragraph(body: str, heading: str, paragraph: str) -> str` (raises `WorkItemFormatError` when the heading is missing) | sections | F0002-S0004 | F0007, F0009 |
| `check_story_form(document: WorkItemDocument, form: str, *, folder: LifecycleFolder) -> list[FormFinding]` (`FormFinding(line: PositiveInt \| None, message: str)`) | story_form | F0002-S0005 | F0005 |
| `claim_status`, `lease_age`, `lease_expired` | lease | F0004-S0002 | F0006, F0008 (section The lease clock) |
| `is_writable(path: str, write_paths: Sequence[str]) -> bool` (fnmatch, `*` crosses `/`, as v1) | write_paths | F0004-S0003 | F0004, F0005 |
| `expand_write_paths(patterns: Sequence[str], *, work_item_path: str, feature_directory: str) -> list[str]` | write_paths | F0004-S0003 | F0005, F0009 |
| `PROTECTED_PATHS: tuple[str, ...]` (v1's Chapter 12 list in v1.1's file names; outside every write path) | write_paths | F0004-S0003 | F0004, F0010 |
| `labels_for(state: WorkItemState) -> list[str]` (`["stage:<stage>"]`) | labels | F0005-S0007 | F0005, F0007 |
| `stall_note(reason: StallReason, attempts: int, attempts_cap: int) -> str` ("retrying" exactly when attempts < attempts_cap) | post_texts | F0005-S0004 | F0008-S0003 |
| `expiry_note(crashes: int, crash_cap: int) -> str` ("retrying" exactly when crashes < crash_cap) | post_texts | F0008-S0003 | F0011 |

`StallReason = Literal["died", "time_limit", "budget", "no_result", "decision_not_allowed", "left_branch", "form_invalid"]` lives in `factory.domain.decisions` (F0005-S0004). A stall is a value, never an exception.

## Interfaces

Every protocol is in `factory.application` and is wired in `factory.entry.wiring` only. A wrapper's constructor takes the bound directory and an optional `KillPoints`. When it is `None`, every point is inert.

### The injection seam (F0001-S0001; used by F0008, F0011) (R36)

```python
# factory/domain/kill_points.py
class KillPoint(StrEnum):
    AGENT_RUN = "agent-run"      # AgentRuntime.run, after the agent's writes, before it returns: the tick dies (crash)
    BEFORE_PUSH = "before-push"  # Git.push, before `git push`: between a commit and its push
    AFTER_POST = "after-post"    # HostingService.post_comment, after the post, before it returns:
                                 # between a post and its record
    AFTER_PUSH = "after-push"    # Git.push, after a successful push: "the tick, at any other point"
                                 # (fault paths 5, 10 and 11 all fall after a push)

class InjectedKill(BaseException):      # BaseException: no `except Exception` in a handler survives it,
    point: KillPoint                    # just as no handler survives a real death
    def __init__(self, point: KillPoint) -> None: ...

class KillPoints:
    def __init__(self) -> None: ...
    def arm(self, point: KillPoint, *, after: int = 0) -> None: ...   # fire on the (after+1)-th reach; ValueError if after < 0
    def reach(self, point: KillPoint) -> None: ...    # raises InjectedKill(point) when armed and due, then disarms
    def reached(self, point: KillPoint) -> int: ...   # how often the point was reached
```

Section 7.2's rows map to these points as follows. During an agent run, where the tick dies, is `AGENT_RUN`. During an agent run, where the run dies and the tick lives, is a `ScriptedRun` whose result is `died` or `time_limit`, with no kill point. Between a commit and its push is `BEFORE_PUSH`. Between a post and its record is `AFTER_POST`. The tick at any other point is `AFTER_PUSH` with `after=`. The container is any point, after which the test deletes the checkout and the state directory and restarts with the same instance name.

### Git (F0001-S0004, S0005) (R9)

```python
# factory/application/git.py
class Git(Protocol):
    """The git command-line tool, bound to one checkout; the remote is always "origin"."""
    # reading
    def fetch(self) -> None: ...                                        # [F0001-S0004 | F0004] with prune; FetchFailed
    def remote_branches(self) -> list[RemoteBranch]: ...                # [F0001-S0004 | F0006] GitError
    def resolve(self, ref: str) -> CommitId | None: ...                 # [F0001-S0004 | F0004] None: no such ref; GitError
    def show_file(self, ref: str, path: str) -> str | None: ...         # [F0001-S0004 | F0004] None: absent at ref; GitError
    def list_files(self, ref: str, directory: str) -> list[str]: ...    # [F0001-S0004 | F0006] recursive, sorted; GitError
    def is_ancestor(self, ancestor: str, descendant: str) -> bool: ...  # [F0001-S0004 | F0006] GitError
    def log(self, ref: str, *, since: str | None = None, path: str | None = None) -> list[CommitInfo]: ...
                                                                        # [F0001-S0004 | F0006] newest first; GitError
    def changed_paths(self, since: str) -> list[ChangedPath]: ...       # [F0001-S0004 | F0004] commits since `since`
                                                                        # plus the work tree, untracked included; GitError
    def status(self) -> WorkTreeStatus: ...                             # [F0001-S0004 | F0005] GitError
    # writing
    def clone(self, url: str) -> None: ...                              # [F0001-S0005 | F0006] into the bound directory,
                                                                        # which must be missing or empty; GitError
    def checkout(self, branch: str, *, start_point: str | None = None) -> None: ...
                                                                        # [F0001-S0005 | F0004] with start_point: create or
                                                                        # reset the branch there (-B); GitError
    def commit(self, message: str) -> CommitId: ...                     # [F0001-S0005 | F0004] stages every change (add -A);
                                                                        # NothingToCommit; GitError
    def push(self, branch: str) -> PushOutcome: ...                     # [F0001-S0005 | F0004] never forced; reaches
                                                                        # BEFORE_PUSH and, when pushed, AFTER_PUSH;
                                                                        # GitError for any other failure
    def delete_remote_branch(self, branch: str) -> PushOutcome: ...     # [F0001-S0005 | F0007] GitError
    def delete_branch(self, branch: str) -> None: ...                   # [F0001-S0005 | F0007] local, forced; GitError
    def merge(self, ref: str, *, fast_forward_only: bool = False) -> MergeOutcome: ...
                                                                        # [F0001-S0005 | F0005] a conflict is aborted
                                                                        # before returning "conflict"; GitError
    def reset_to(self, ref: str) -> None: ...                           # [F0001-S0005 | F0006] reset --hard and clean -fd
                                                                        # (ignored paths stay: handover section 8); GitError
    def revert_paths(self, commit: str, paths: Sequence[str]) -> None: ...
                                                                        # [F0001-S0005 | F0004] each path to its content at
                                                                        # commit, deleted when absent there; GitError
    def move(self, source: str, destination: str) -> None: ...          # [F0001-S0005 | F0007] git mv; GitError
```

First implementation: `factory.adapters.git_cli.GitCli(directory: Path, kill_points: KillPoints | None = None)`. Commit messages are free text and never parsed. Tests use the real `GitCli` against a bare remote and do not fake git.

### Hosting service (F0001-S0002, S0003) (R10, SI2)

```python
# factory/application/hosting.py
class HostingService(Protocol):
    """Pull requests only. Every failing call raises HostingServiceError (SI2.2). Labels are never read back."""
    def create_pull_request(self, branch: str, title: str, body: str, *, draft: bool) -> PullRequestView: ...
                                                        # [F0001-S0002 | F0003] base is MAIN_BRANCH
    def find_open_pull_request(self, branch: str) -> PullRequestView | None: ...
                                                        # [F0001-S0002 | F0003] only an open one (F0005-S0002)
    def get_pull_request(self, number: int) -> PullRequestView: ...           # [F0001-S0002 | F0006] state and merge state
    def list_comments(self, number: int) -> list[PullRequestComment]: ...     # [F0001-S0002 | F0007] oldest first
    def post_comment(self, number: int, text: str, key: PostKey) -> PostOutcome: ...
                                                        # [F0001-S0002 | F0003] posts render_post(text, key) unless a
                                                        # comment with that key exists ("already_posted"); reaches
                                                        # AFTER_POST after a post
    def close(self, number: int) -> None: ...           # [F0001-S0002 | none in the skeleton; R10 names it]
    def reopen(self, number: int) -> None: ...          # [F0001-S0002 | F0007]
    def set_draft(self, number: int, draft: bool) -> None: ...                # [F0001-S0002 | F0007] draft or ready
    def set_description(self, number: int, body: str) -> None: ...            # [F0001-S0002 | F0007] replaces it
    def set_labels(self, number: int, labels: Sequence[str]) -> None: ...     # [F0001-S0002 | F0005] replaces the labels
                                                        # starting with LABEL_PREFIX and keeps all others
```

First implementation: `factory.adapters.pygithub_hosting.PyGithubHostingService(repository: github.Repository.Repository, kill_points: KillPoints | None = None)`. Wiring builds the `Repository` from the token, which only the factory process holds (R33). Tests use stand-ins of PyGithub's objects (answer 10). Every `github.GithubException` and every connection error becomes `HostingServiceError`.

The one fake: `factory.adapters.fake_hosting.FakeHostingService(kill_points: KillPoints | None = None)`. It implements the protocol and adds these test operations:

```python
    def add_human_comment(self, number: int, body: str, *, author: str = "human") -> int: ...  # returns the comment id
    def delete_comment(self, number: int, comment_id: int) -> None: ...                       # GH3.2
    def close_by_human(self, number: int) -> None: ...
    def merge_by_human(self, number: int, merge_commit: CommitId) -> None: ...  # the git merge is the test's (human.merge)
    def fail_next(self, operation: str, *, times: int = 1) -> None: ...  # the next calls of that method raise
    def factory_posts(self, number: int) -> list[PullRequestComment]: ...  # GH3.4 counts these
    def labels(self, number: int) -> list[str]: ...
    def description(self, number: int) -> str: ...
    def pull_requests(self) -> list[PullRequestView]: ...
```

### Project commands (F0001-S0006) (R11, R8)

```python
# factory/application/project_commands.py
class ProjectCommands(Protocol):
    """The project's commands, judged by exit status only (kept 8, 17)."""
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult: ...
        # [F0001-S0006 | F0005] a red or timed-out command is a CheckResult, not an error;
        # ProjectCommandError when it cannot be started (tool missing) or the name is not ^[a-z][a-z0-9-]*$
```

This is the only operation, because no story in the skeleton needs another. The preflight's probe (F0010-S0005) runs `lint` through it on the checkout. At that point the tick has already reset the checkout to `origin/main`, so no worktree operation is needed. First implementation: `factory.adapters.make_commands.MakeProjectCommands(directory: Path, kill_points: KillPoints | None = None)`, which runs `make <command>`.

### Agent runtime and agent definitions (F0001-S0007, S0008; F0003-S0004) (R12)

```python
# factory/application/agent_runtime.py
class AgentRuntime(Protocol):
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...
        # [F0001-S0007 | F0005] a run that dies, reaches its time_limit or its budget is a result
        # (a stall for the caller), not an error; AgentRuntimeError when the run cannot be started;
        # reaches AGENT_RUN after the run's writes
    def version(self) -> str: ...      # [F0001-S0008 | F0010] AgentRuntimeError when not reported

class AgentDefinitionReader(Protocol):
    def names(self) -> list[str]: ...  # [F0003-S0004 | F0003] installed agents, sorted; AgentDefinitionError
                                       # when the agent home is missing
    def read(self, name: str) -> AgentDefinition: ...
                                       # [F0003-S0004 | F0005] AgentDefinitionMissing; AgentDefinitionInvalid
                                       # naming the key (SI4.1, from F0010-S0006)
```

First implementations: `factory.adapters.claude_runtime.ClaudeCodeRuntime(executable: str, state_directory: Path, kill_points: KillPoints | None = None)` and `factory.adapters.agent_files.FrontmatterAgentDefinitionReader(agent_home: Path)`. `ClaudeCodeRuntime` writes the guard settings file under `state_directory`, outside the checkout, and passes a `PreToolUse` hook that calls `factory-guard --settings <file>`. Its outcome schema has the fields `decision` (an enum of `allowed_decisions`) and `entry`.

The fake is `factory.adapters.fake_agent_runtime.FakeAgentRuntime(kill_points: KillPoints | None = None, version: str = "fake")`:

```python
class ScriptedRun(BaseModel):
    writes: dict[str, str] = {}      # path -> content, written under request.working_directory
    deletes: list[str] = []
    result: AgentRunResult
    kill: bool = False               # after the writes, reach AGENT_RUN (armed or not, the test decides)

class FakeAgentRuntime:              # implements AgentRuntime
    def queue(self, run: ScriptedRun) -> None: ...
    def requests(self) -> list[AgentRunRequest]: ...   # every request received, in order
    # run() with nothing queued raises AgentRuntimeError
```

### Readers and writers (R13)

```python
# factory/application/files.py
class PipelineDefinitionReader(Protocol):                       # F0003-S0003
    def parse(self, text: str) -> PipelineDefinition: ...      # [F0003-S0003 | F0003] PipelineDefinitionInvalid
                                                                # naming the missing key, stage or rule

class WorkItemReader(Protocol):                                 # F0002-S0002
    def parse(self, text: str) -> WorkItemDocument: ...        # [F0002-S0002 | F0004] state required;
                                                                # WorkItemFormatError (v1's `comments_seen` included)
    def parse_specification(self, text: str) -> WorkItemDocument: ...
                                                                # [F0002-S0002 | F0005] front matter dropped into
                                                                # ignored_keys, state None; WorkItemFormatError only
                                                                # for unreadable YAML
    def read(self, path: Path) -> WorkItemDocument: ...        # [F0002-S0002 | F0004] parse() of the file; also
                                                                # OSError -> WorkItemFormatError

class WorkItemWriter(Protocol):                                 # F0002-S0002
    def render(self, document: WorkItemDocument) -> str: ...   # [F0002-S0002 | F0004] keys in WorkItemState's field
                                                                # order; WorkItemFormatError when state is None
    def write(self, path: Path, document: WorkItemDocument) -> None: ...   # [F0002-S0002 | F0004]

class CostRecordReader(Protocol):                               # F0002-S0006
    def parse(self, text: str) -> list[CostRecord]: ...        # [F0002-S0006 | F0005] CostRecordFormatError(line)
    def read(self, path: Path) -> list[CostRecord]: ...        # [F0002-S0006 | F0005] a missing file is []

class CostRecordWriter(Protocol):                               # F0002-S0006
    def render(self, records: Sequence[CostRecord]) -> str: ...            # [F0002-S0006 | F0005] one line each
    def write(self, path: Path, records: Sequence[CostRecord]) -> None: ...  # [F0002-S0006 | F0005] replaces the file
```

First implementations: `factory.adapters.pipeline_yaml.RuamelPipelineDefinitionReader()`, `factory.adapters.work_item_markdown.FrontmatterWorkItemReader()` and `FrontmatterWorkItemWriter()`, and `factory.adapters.cost_records_jsonl.JsonLinesCostRecordReader()` and `JsonLinesCostRecordWriter()`. No story writes the pipeline definition, so it has no writer (open question 8). A file at a commit is read with `Git.show_file` followed by `parse`.

### The machine's stores (F0003-S0001; F0005-S0003)

```python
# factory/application/machine.py
class Clock(Protocol):
    def now(self) -> datetime: ...                    # aware, UTC
class FactoryLog(Protocol):
    def line(self, text: str) -> None: ...            # "<YYYY-MM-DDTHH:MM:SSZ> <text>" to stdout and the factory log (ST3.4)
class HealthStatusStore(Protocol):
    def read(self) -> HealthStatus: ...               # a missing file is HealthStatus()
    def write(self, status: HealthStatus) -> None: ...
class RunRecordStore(Protocol):                       # F0005-S0003
    def read(self) -> RunRecord | None: ...           # missing or unreadable is None: a cache
    def write(self, record: RunRecord) -> None: ...
    def clear(self) -> None: ...
```

Implementations: `SystemClock()` and `ManualClock(start: datetime)` with `advance(by: timedelta)`, `TimestampedFactoryLog(path: Path, clock: Clock)`, `JsonHealthStatusFile(path: Path)` at `<state directory>/health.json`, and `JsonRunRecordFile(path: Path)` at `<state directory>/run-record.json`. Every one raises `OSError` only, and only on write.

### Services used across features

```python
# factory/application/boundaries.py   (F0003-S0001; a story that creates an interface adds its field)
@dataclass(frozen=True)
class Boundaries:                     # not a DTO: the interfaces wiring hands to services (keeps args <= 5)
    git: Git
    hosting: HostingService
    agent_runtime: AgentRuntime
    project_commands: ProjectCommands
    work_item_reader: WorkItemReader
    work_item_writer: WorkItemWriter
    cost_reader: CostRecordReader
    cost_writer: CostRecordWriter
    clock: Clock
    log: FactoryLog
    health: HealthStatusStore
    pipeline_reader: PipelineDefinitionReader      # F0003-S0003
    agent_definitions: AgentDefinitionReader       # F0003-S0004
    run_record: RunRecordStore                     # F0005-S0003
    checkout: Path                                 # the checkout root

# factory/application/stops.py        (F0003-S0001, S0002)
class StopService:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def post(self, stop: WorkItemStop) -> StopPosted: ...
        # [F0003-S0002 | F0005] opens a draft pull request on stop.branch when stop.pull_request is None
        # (finding an open one first); HostingServiceError
    def raise_stop(self, stop: RepositoryStop) -> None: ...       # [F0003-S0001 | F0003] health + line; OSError
    def clear_stop(self, reason: RepositoryStopReason) -> None: ...   # [F0003-S0001 | F0006]

# factory/application/pipeline_loading.py   (F0003-S0004)
class PipelineLoader:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def load(self, ref: str = "origin/main") -> PipelineDefinition: ...
        # [F0003-S0004 | F0006] PipelineDefinitionInvalid (an agent not installed included);
        # AgentDefinitionInvalid (from F0010-S0006); GitError

# factory/application/claims.py      (F0004-S0001, S0002; the only module that knows claims: GH1.2)
class StageStart(BaseModel):          # a DTO, defined here because only the claim service makes it
    commit: CommitId                  # the pushed stage-start commit: the undo's and the guard's baseline
    claim: Claim

class ClaimService:
    def __init__(self, boundaries: Boundaries, instance: str, definition: PipelineDefinition) -> None: ...
    def claim(self, branch: str, path: str, document: WorkItemDocument, stage: str) -> StageStart: ...
        # [F0004-S0001 | F0005] writes the claim and the "started" entry into document, writes it at path,
        # commits, pushes; PushFailed when rejected or unreachable (then there is no claim: GH1.1); GitError
    def status(self, state: WorkItemState) -> ClaimStatus: ...    # [F0004-S0002 | F0006] uses Clock.now()
    def release(self, document: WorkItemDocument) -> WorkItemDocument: ...   # [F0004-S0002 | F0005] claim -> None

# factory/application/write_paths.py  (F0004-S0003)
class WritePathService:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def at(self, stage_start: StageStart, work_item_path: str) -> GuardSettings: ...
        # [F0004-S0003 | F0004] reads the pipeline definition at stage_start.commit, never the work tree
        # (R32, WE2.3); GitError; PipelineDefinitionInvalid

# factory/application/undo.py         (F0004-S0005)
class UndoReport(BaseModel):
    reverted: list[str]
    deleted: list[str]
    restored_work_item: bool          # state and journal put back from the stage-start commit

class UndoService:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def undo(self, stage_start: StageStart, work_item_path: str) -> UndoReport: ...
        # [F0004-S0005 | F0005] never raises for an invalid pipeline definition in the work tree (WE2.2);
        # GitError; WorkItemFormatError when the stage-start commit's own work item is unreadable

# factory/application/dispatcher.py   (F0006-S0003)
class Handler(Protocol):
    def handle(self, event: Event) -> None: ...   # any Exception is a counted error (R28)

DispatchOutcome = Literal["handled", "error", "reported", "capped"]
class Dispatcher:
    def __init__(self, handlers: Mapping[EventKind, Handler], status: TickStatus, stops: StopService) -> None: ...
    def dispatch(self, event: Event) -> DispatchOutcome: ...
        # a kind without a handler raises UnhandledEvent inside, counted like any error (SI2.4);
        # at ERROR_CAP the report is posted once with PostKey(kind="error", n=remote_state[:12]);
        # "capped": the same event on the same remote state is not tried again
```

## Errors

One hierarchy, in `factory.domain.errors` (created by F0001-S0001; each story adds the types it raises first). Every type carries its fields as attributes, and its message names the fault.

```python
class FactoryError(Exception): ...                       # every error the factory raises on purpose
class WorkItemFormatError(FactoryError): fault: str; path: str | None
class CostRecordFormatError(FactoryError): line: int; fault: str
class PipelineDefinitionInvalid(FactoryError): fault: str
class AgentDefinitionError(FactoryError): name: str; fault: str
class AgentDefinitionMissing(AgentDefinitionError): ...
class AgentDefinitionInvalid(AgentDefinitionError): key: str
class BoundaryError(FactoryError): ...                   # an outside party failed
class GitError(BoundaryError): command: str; exit_status: int | None; output_tail: str
class FetchFailed(GitError): ...
class NothingToCommit(GitError): ...
class HostingServiceError(BoundaryError): operation: str; detail: str
class ProjectCommandError(BoundaryError): command: str; detail: str
class AgentRuntimeError(BoundaryError): detail: str
class PushFailed(FactoryError): branch: str; outcome: PushOutcome
class UnhandledEvent(FactoryError): kind: str
class CannotHandle(FactoryError): kind: str; reason: str
# and, outside the hierarchy, factory.domain.kill_points.InjectedKill(BaseException)
```

| Type | Raised by (layer) | Built by | Becomes |
|---|---|---|---|
| `WorkItemFormatError` | reader (adapters); `sections`, `journal` (domain) | F0002-S0002 | counted error in a handler; a form finding when the form check reports it |
| `CostRecordFormatError` | cost record reader (adapters) | F0002-S0006 | counted error |
| `PipelineDefinitionInvalid` | reader (adapters), `PipelineLoader` (application) | F0003-S0003 | repository stop `pipeline_definition_invalid`; the tick does nothing else (ST8.1) |
| `AgentDefinitionMissing` | agent definition reader (adapters) | F0003-S0004 | at load: `PipelineDefinitionInvalid` (ST8.3); in a stage: counted error |
| `AgentDefinitionInvalid` | agent definition reader (adapters) | F0010-S0006 | repository stop `agent_definition_invalid` (SI4.3) |
| `GitError` | `GitCli` (adapters) | F0001-S0004 | counted error in a handler; at the tick's checkout restore: repository stop `checkout_restore_failed` (answer 3) |
| `FetchFailed` | `GitCli.fetch` (adapters) | F0001-S0004 | repository stop `fetch_failed`; the tick ends (GH5.3) |
| `NothingToCommit` | `GitCli.commit` (adapters) | F0001-S0005 | counted error unless the caller expects it |
| `HostingServiceError` | both hosting implementations (adapters) | F0001-S0002 | counted error; in the preflight: machine stop `preflight_failed` |
| `ProjectCommandError` | `MakeProjectCommands` (adapters) | F0001-S0006 | counted error in a stage; in the preflight: machine stop |
| `AgentRuntimeError` | both runtimes (adapters) | F0001-S0007 | counted error (no attempt: no run started); in the preflight: machine stop (ST5.3) |
| `PushFailed` | `ClaimService`, stage and handlers (application) | F0004-S0001 | counted error, at most one report per remote state (GH5.2); at the claim, no agent run (GH1.1) |
| `UnhandledEvent` | `Dispatcher` (application) | F0006-S0003 | counted error (SI2.4) |
| `CannotHandle` | handlers (application) | F0007-S0008 | counted error (ST3.1, R28) |
| `InjectedKill` | `KillPoints.reach` in the wrappers and fakes | F0001-S0001 | a crash: the test restarts with the same instance name |

The three ways a stage does not move forward, besides a rework and a question:

- **Counted error** (handover section 2: the factory's own fault). Any `Exception` that leaves a handler is counted by the dispatcher per event key and remote state, retried on later ticks, and reported once at `ERROR_CAP`.
- **Stall.** Never an exception. The stage protocol sees an `AgentRunResult` that is not `ok`, a decision that is not allowed, or a broken branch or form (`StallReason`). It charges an attempt and applies the undo.
- **Crash.** Never caught. In production the process is gone; in tests it is `InjectedKill`. It is recognised at the next first look as an own claim (`ClaimStatus` `"own"`) or as an expired one (`"expired"`).

## The journal

The visible part is in the body under `## Journal`. It is written by code only and never parsed for speaker, kind or cost (SI1.4):

```
## Journal

1. 2026-10-12 human: created.
2. factory: started intake as factory-1.
3. intake: accepted
   The criteria are each testable by one test.
4. 2026-10-13 human: (a), the tester fixes the test.
```

- The prefix is `<number>. ` followed by `<YYYY-MM-DD> ` and then `<speaker>: `. The date is written exactly when the speaker is `human`, as in v1. `on` is the date of the comment, or of the act for `created` and `close`.
- Continuation lines are indented by `len("<number>. ")` spaces. Blank lines inside a text stay empty. Entries follow one another with no blank line between them. The speaker is shown as the speaker's name. No display text is configured, so changing a display text can change nothing that readers return (SI1.1).
- The data is in the front matter key `journal`, as a list with one element per visible entry:

```yaml
journal:
- number: 1
  speaker: human
  kind: created
- number: 2
  speaker: factory
  kind: started
```

- Rules: the numbers are 1..n in order. `append_entry` writes both halves in one call, so n always equals the count of visible entries. The claim's data (instance, start time) is in `claim`, not in the entry's text. `restore_state_and_journal` puts back the whole front matter and the `## Journal` section of the baseline, and keeps the rest of the current body. `entry_text(document, number)` finds the visible text of an entry by its number, for display such as the hand-over's description, and returns no speaker, kind or cost.
- Entry 1 (`human`, `created`) is written by the opening (F0005-S0002). A backlog story carries no journal. Whatever it carries is dropped with its state fields (ST6.1).

## The lease clock

Decision 007, question 4, as functions in `factory.domain.lease` (F0004-S0002), called through `ClaimService.status` with `Clock.now()`:

```python
ClaimStatus = Literal["none", "own", "held", "expired"]

def lease_age(claim: Claim, now: datetime) -> timedelta: ...
    # now - claim.started_at; both aware UTC; negative under clock skew
def lease_expired(claim: Claim, now: datetime) -> bool: ...
    # lease_age >= timedelta(minutes=claim.lease_duration); an age below zero counts as not expired
def claim_status(claim: Claim | None, *, instance: str, now: datetime) -> ClaimStatus: ...
    # None -> "none"; claim.instance == instance -> "own" without consulting now (GH1.3: a same-name
    # restart reruns at once); otherwise "expired" when lease_expired, else "held"
```

- The start time is written by the claiming instance in UTC from `Clock.now()` into `claim.started_at` in the stage-start commit. The lease is the claiming role's `lease_duration` at that time, copied into `claim.lease_duration`. A change of the pipeline definition later therefore never shortens a running claim.
- `"own"` leads to the `crash` event (F0008). `"expired"` leads to `expired`, which is handled as a crash (answer 1). `"held"` is waiting (`idle`). The operator guide states that instances need a synchronised clock.

## Names

Every name in this sheet that renames a v1 word, so that drafters can check them. The table follows the glossary (handover appendix) and the decisions. Convention: names that are a project's data (folders, stage and role names) use hyphens. Keys and the values of `Literal`s use snake_case.

| v1 word or name | v1.1 name in this sheet |
|---|---|
| ticket, `Ticket` | work item: `WorkItemDocument`, `WorkItemState`, `WorkItemSnapshot`, `work_item` |
| log, `## Log (append only)`, `ENTRY` | journal: `journal`, `JournalRecord`, `## Journal` |
| `drafts/` | `backlog/` |
| `ongoing/` (in production) | `in-progress/` |
| promote | start (the human's move to `in-progress/`; `HumanClone.start`) |
| stage table, `stages.yml`, `Config` | pipeline definition: `factory/pipeline.yml`, `PipelineDefinition` |
| `version` (of the stage table) | `contract` (contract version) |
| `lease_minutes` | `lease_duration` (per role, minutes) |
| time limit, timeout (`claude` and `make` calls) | `time_limit` |
| `max_attempts` | `attempts_cap` |
| `max_rounds` | `round_cap` |
| crash cap (new) | `crash_cap`, `crashes` |
| lane, `lanes:` | write paths: `write_paths`, `GuardSettings` |
| `agent:` (stage key) | `role:`; `roles:` holds each role's write paths and limits |
| `records:` (stage key) | `reports:` |
| gate, stage `accept` | approval: `approval: true`, stage `approval` |
| demonstration, `## Demo`, stage `demo`, agent `demo` | smoke test: `## Smoke test`, stage `smoke-test`, role `smoke-tester` |
| acceptor | acceptance reviewer: role `acceptance-reviewer`, `acceptance_stage` |
| assignment, `## Assignment (as of log entry 1)` | description: `## Description` |
| task (the agent's) | prompt: `AgentRunRequest.prompt` |
| outcome (the agent's `outcome` field) | `decision` (`AgentRunResult.decision`); a stage's result is its result commit |
| verdict | recommendation (F0009) |
| control surface | project commands: `ProjectCommands`, `project_commands` |
| failure, `GitHubError` | error: `HostingServiceError`, counted error, `ERROR_CAP` |
| `AgentMissingError` | `AgentDefinitionMissing` |
| `AgentSpec` | `AgentDefinition` |
| `AgentRun` | `AgentRunResult` |
| memo, `Memo`, `failures` | tick status: `TickStatus`, `ErrorCount` |
| `Running`, `.git/factory-run.json` | run record: `RunRecord`, `<state directory>/run-record.json` (a cache) |
| `Bucket` | `Bill` |
| `pr` (state key), `pr` event | `pull_request`; event `comment` |
| `comments_seen` (a count) | `comments_read` (ids) |
| `error pr-lookup` event | `pull_request_lookup` |
| evidence | recovery state (not used; the claim replaces it) |
| the factory's log file, tick log | factory log: `FactoryLog` |
| hardening path | fault-injection path |
| failing sides | edge cases |

## Open questions

1. **The acceptance's id and order.** The sheet uses `F0001-A0001`. Under plain string order `A` sorts before `S`, so `work_item_order` puts an acceptance after its feature's stories. The alternative is a letter after `S` with no key function. Recommendation: keep `A` and the key, because the order is then a stated rule rather than a property of the alphabet.
2. **Spellings that v1 did not give in the inputs.** The branch prefix `work-item/`, the feature file `feature.md`, the forms `factory/story-form.md` and `factory/feature-form.md`, the file name `factory/pipeline.yml`, the marker `<!-- factory -->` and the label prefix `stage:` are all chosen here. If v1's own spellings are wanted where the glossary does not rename a word, F0002-S0001 should take them from v1's template.
3. **Default `time_limit`s.** v1 gave every call the full lease. The defaults here are 40 minutes for an agent run and 10 minutes for a project command. With them, the fixture's heaviest stage (`tests`: 40 + 5 + 10) fits a 60-minute lease, but a stage with two checks and a report at the defaults does not. Should a project be made to set them?
4. **Values of `blocked`.** v1's values are not in the inputs. The sheet uses five values, so that an answer can reset the right counter (ST1.1, GH2.4). Do `round_cap` and `send_back` need to be told apart, or is one value enough?
5. **The journal's date.** Decision 007 writes `<number>. <date> <speaker>: <text>`, and F0002 says only the human's entries are dated, as in v1. The sheet dates the human's entries only. Should the factory's entries be dated too?
6. **The lease recorded in the claim.** `Claim.lease_duration` goes beyond R20, which names only the instance and the start time. It saves a lookup of the pipeline definition at the stage-start commit. Is the extra key acceptable?
7. **Write-path placeholders.** `{work_item}` and `{feature}` let a role write only its own work item and its feature's backlog, as v1's "only their story file" did. Every role must then have at least one write path (ST8.3). Is the placeholder form acceptable, or should the work item's own file be writable by every role implicitly?
8. **No writer for the pipeline definition.** The brief asks for one reader and one writer per format, but no story writes `factory/pipeline.yml`. The sheet names the reader only. Should a writer be added anyway, for a round-trip test?
9. **Agent file keys.** `AgentDefinition` holds `model`, `tools`, `effort` and `budget_usd`, v1's `AgentSpec` minus `name`. Which keys the pinned `claude -p` really applies is F0010-S0006's finding. If it differs, the DTO changes in F0010.
10. **`ERROR_CAP` as a constant (3)** and not a pipeline definition key. R30 does not list it. Should a project be able to set it?
11. **Kill points.** Four points, with "the tick at any other point" taken as `AFTER_PUSH` plus a count, which covers fault paths 5, 10 and 11. Fault-paths' open question 3 (does a crash between two stages raise `crashes`, and on which stage?) is unchanged by the sheet. F0008-S0001 has to answer it.
12. **`HostingService.close`** is in R10 but no story of the skeleton calls it, because the human closes. Keep it (R10 is exact), or drop it until a story needs it?
13. **`Boundaries`** is a frozen dataclass, not a Pydantic model. It holds interfaces, not data, and keeps services within five arguments. Is that within R7's "DTOs are Pydantic"?
14. **Event kinds.** The fourteen kinds rename v1's dispatcher lines (`pr` → `comment`, `error pr-lookup` → `pull_request_lookup`) and add `hand_over`, `crash`, `expired`, `acceptance_due` and `v1_work_item`. F0006's drafter should check them against v1's `dispatch.py` lines in `v1-04-08.md`, Chapter 7, which the sheet did not read.

## Sources

- Features, scope and stories: `factory-rf/planning/overnight/skeleton.md` (every section).
- Binding answers: `factory-rf/planning/overnight/skeleton-answers.md`. 1: expiry as a crash, the notes. 2: run record as a cache, no lock. 3: checkout restore and its stop. 4: keyed posts and the key's format. 5: spellings. 8: stage-start commit last, the opening commit. 10: PyGithub stand-ins. 11: R26 detection. 14: tick status as a cache. 15: `handed_over`.
- Kill points and test names: `factory-rf/planning/overnight/fault-paths.md`, the table of thirteen paths and *Kill points without a path*.
- Rules R1 to R38, the names of section 2, the conditions of section 5, sections 7.2 and 8, and the appendix: `factory-v2/planning/v1.1/handover.md`.
- Decisions: `factory-v2/planning/decisions/005-v1-1-architecture-choices.md` (tools, Pydantic, file formats, names in formats); `006-v1-1-open-points.md` (claim, lease, crash cap, data of a work item, hosting client, kill tests, validation, layers); `007-overnight-defaults.md` (questions 1, 2 and 4).
- v1's data model (`AgentSpec`, `AgentRun`, `Memo`, `Running`, `Bucket`, `GitHubError`, `AgentMissingError`, the state fields, `lanes`, `checks`, `records`): `factory-v2/planning/v1.1/v1-style-facts.md`.
- Layers, wrappers, test rules, argument limit and dependencies: `factory-rf/CLAUDE.md`, `factory-rf/pyproject.toml`.
- The form of an exact `## Interface` section and v1's journal and front matter: `factory-demo-todo/factory/features/F0001-todo-service/done/F0001-S0001-domain-model-and-in-memory-repository.md`.

## Amendments during the night

- 2026-10-13 morning, the human's decision: every interface in this sheet written as `typing.Protocol` is an abstract base class (`abc.ABC`, each operation an `@abstractmethod` with a docstring-only body), and every implementation the factory writes, fakes included, inherits it. `Protocol` stays only for shapes of code the factory does not own. F0001's four interfaces are converted by F0001-S0019; the drafts of F0002 to F0011 were converted the same morning. See `CLAUDE.md`, Architecture.

Changes the main session made after the sheet was written. They win over the sections above.

- 2026-10-13 01:00, from F0001 round 1: `GitCli(..., *, identity: GitIdentity | None = None, environment: Mapping[str, str] | None = None)`. `GitIdentity(name: str, email: str)` is a frozen Pydantic model in `factory.domain.git`. The identity comes from the instance's settings (`GIT_USER_NAME`, `GIT_USER_EMAIL`), and the extra environment carries the factory process's credential settings. Git still ignores the system and global configuration.
- 2026-10-13 01:00: F0001's stories were renumbered (14 stories). The "created by" tags for F0001 in the tables above are stale; `stories/F0001-boundaries/FEATURE.md` is authoritative.
- 2026-10-13 01:00: `factory.entry.wiring` grows with each feature (`build_boundaries`, `build_dispatcher`); see `skeleton-answers.md`, the answers to cross-check round 1's blockers.
- 2026-10-13 01:00: every entry module's function is `main() -> int`, reading its arguments from `sys.argv` (`pyproject.toml`'s console scripts).

Changes after the human's questionnaire 1 and F0002's rounds, 2026-10-13. They win over the sections above.

- Q3, no run record: `factory.domain.run_record` (`RunRecord`), `RunRecordStore` in `factory.application.machine`, `factory.adapters.run_record_file` (`JsonRunRecordFile`), `Boundaries.run_record` and the run-record row of the names table are dropped. The board's "running since" is the claim's `started_at`. GH1.5 tests that the tick reads and writes no run record and no lock.
- Q15 and decision 008 (factory-v2), v1.1 starts fresh: `V1_LIFECYCLE_FOLDERS` and every recognition of v1 work items (R26's refusal) are dropped. `ignored_keys` stays, as the keys `parse_specification` dropped, with no R26 reader. `WorkItemReader` refuses every unknown key as a `WorkItemFormatError`, with no special case for v1's `comments_seen`.
- F0002, slug: a slug follows v1's rule, lower-case segments of letters and digits joined by single hyphens; both models refuse a slug that breaks it (F0002 decision 1).
- F0002, cost record: `cost_usd` is unknown (`None`) or a finite value of at least 0.
- F0002, R13: the work item adapter `factory.adapters.work_item_markdown` splits the file with python-frontmatter and reads and writes its YAML with ruamel.yaml through `RuamelYamlHandler(frontmatter.YAMLHandler)`, an adapter-internal class (F0002 decision 4). F0002's `FEATURE.md` and stories are authoritative for the exact rules.
- F0003, 2026-10-14: the stories were renumbered: S0001 stop data, clock, log and health file; S0002 repository and machine stops (`StopService`, `Boundaries`); S0003 work item stops posted once; S0004 pipeline definition schema; S0005 agent definition reader (creates `AgentDefinitionInvalid`); S0006 pipeline loader; S0007 load-time rules. Other features that cite "F0003-S0004" for the loader mean S0006. `Boundaries` is `kw_only=True`. New names: `all_faults`, `split_front_matter`, `PIPELINE_REF`. The stop reason `v1_work_item_found` is dropped (Q15). Only a load of `origin/main` raises or clears the loader's stop, so F0006-S0004 and S0006 adapt to that. F0003's `FEATURE.md` and stories are authoritative.
- F0006, 2026-10-14 (round 1): the production wiring (Q20 A) is F0006-S0007, with `build_handlers` in place of the sheet's `build_dispatcher`, `HandlerFactory`, `handler_factory`, `agent_environment`, `production_environment` and `NOT_YET_HANDLED`; the tick keeps its status as `Tick.status`; the `run` handler is `RunHandler` in `factory.application.handlers.run`; F0005's `StageMove` seen from the tick is `FactoryMove`. Later features register their handlers in `build_handlers` and take their kinds out of `NOT_YET_HANDLED`. Open: a `Git` operation that lists local branches (until then the restore deletes only branches of work items the remote knows). F0006's `FEATURE.md` and stories are authoritative.
- F0007, 2026-10-14 (round 1): `unblock` (`factory.domain.answers`, F0007-S0007) and `destination_path` (`factory.domain.archive`, F0007-S0003) are new; F0007's handlers inherit F0006's `Handler` and register in `build_handlers`, leaving `NOT_YET_HANDLED = ("crash", "expired", "acceptance_due")`. F0006-S0002's `question_posted` compares with the latest `question` record (applied 2026-10-14).
