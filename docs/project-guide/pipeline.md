# The pipeline definition, the stages and the tick

This file covers the pipeline definition and a stage from the claim to the result commit, the take's rule, the tick, its handlers, the stops and the boundaries; read the index, `README.md`, first.

## The claim service

`factory.pipeline.application.claims.ClaimService(boundaries, instance, definition)` makes the first half of a claim: the stage-start commit. `instance` is the factory instance's name and must match `[a-z][a-z0-9-]*`, otherwise the constructor raises `ValueError`. `definition` is the `PipelineDefinition` the caller loaded (normally from `origin/main`); the lease is copied from it.

`claim(branch, path, document, stage)` returns a `StageStart(commit, claim)`. It does this, in order:

1. Checks the preconditions and writes nothing if one fails (`ValueError`): the document has a state; `stage` is the state's stage; `stage` is in the definition and has a role; `branch` is `branch_name` of the id in the file name of `path`, so a claim is made only on the work item's own branch; the checkout is on `branch`.
2. Builds the `Claim`: the instance's name, the stage, the start time from `boundaries.clock` (UTC) and the `lease_duration` of the stage's role, copied now. A claim already in the document is replaced.
3. Sets `state.claim` and appends one journal entry (speaker `factory`, kind `started`, text `started <stage> as <instance>.`, see `started_text`). Nothing else in the document changes.
4. Writes the work item at `boundaries.checkout / path` and commits with the subject `work item <id>: <stage> starts as <instance>`.
5. Pushes `branch`. Any outcome other than `"pushed"` raises `PushFailed`.

**The push is the claim.** Whoever pushes first owns the stage. A rejected or unreachable push is no claim: the remote is unchanged, and the caller starts no agent run. The local commit stays on the local branch; the next tick's restore brings the branch back to the remote. `InjectedKill` at `BEFORE_PUSH` is not caught.

**The stage-start commit is the last commit before the agent run.** The commit stages every change in the work tree, so whatever the caller left uncommitted is part of it; for a new branch that is the work item's opening. The commit is therefore the baseline for what the agent may write and for the take's refusal rule.

**Status.** `status(state)` returns a `ClaimStatus` (`factory.pipeline.domain.lease`): `"none"` (no claim), `"own"` (the claim's `instance` is the service's, whatever its age, so a restarted instance with the same name reruns its stage at once), `"held"` (another instance's claim, lease still running) or `"expired"` (another instance's, lease run out). It uses `boundaries.clock.now()` and the claim's own `lease_duration`, never the definition's, so a later change of the definition does not shorten a running claim.

**Observed status.** `observed_status(state)` is `status` as a look from outside the instance's tick sees it (`observed_claim_status` in `factory.pipeline.domain.lease`, with the same clock): an own claim within its lease is `"held"`, since the tick may be running its stage, and at and past its lease `"own"`; every other claim, and no claim, gets what `status` gives. Only `Watcher(..., observer=True)` (`factory-watch`) uses it; the tick uses `status`.

**The lease clock.** `lease_age(claim, now)` is `now - claim.started_at` (negative under clock skew); `lease_expired(claim, now)` is true when the age is at least `claim.lease_duration` minutes, and a negative age is never expired. Both are pure: `now` is passed in.

**Release.** `release(document)` returns the document with `state.claim` set to `None`, for the stage's result commit. Journal, other state fields and body are unchanged and no entry is appended. A document without a claim comes back equal; one without a state raises `ValueError`.

**`ClaimService` is the only module that builds or judges claims.** Only `factory.pipeline.application.claims` imports `claim_status`, `lease_expired`, `lease_age` or `observed_claim_status`, and only it calls `Claim(...)`; `tests/guards/test_claim_ownership.py` searches the source with `ast` and fails otherwise. Code that needs to know a claim's standing asks the service.

In tests, set the work item up on its branch before `claim` (a state, a journal entry and a `## Journal` section, or `append_entry` raises `WorkItemFormatError`); `put_work_item` and `created_state` in `tests/support/work_item_support.py` do it, and `tests/pipeline/application/test_claims.py` uses them.

## The pipeline definition

The project's `factory/pipeline.yml` is read by `RuamelPipelineDefinitionReader.parse(text)` (`factory.pipeline.adapters.pipeline_yaml`, the `PipelineDefinitionReader` interface in `factory.shared.application.files`, `Boundaries.pipeline_reader`) into a `PipelineDefinition` (`factory.pipeline.domain.pipeline_definition`). The reader is the only one of this format and nothing writes it. The text is loaded in ruamel.yaml's safe mode, so only plain data is built and a key repeated in one mapping is refused. `PIPELINE_YAML` in `tests/support/git_support.py` is the example definition.

| Key | Meaning | Default |
|---|---|---|
| `contract` | the contract version, a quoted text such as `'1.0'`; an unquoted `1.0` is a number and is refused | required |
| `stages` | name to `StageDefinition`; the order in the file is the pipeline's order | required |
| `roles` | name to `RoleDefinition`; a role's name is its agent definition's name | required |
| `project_commands` | name to `ProjectCommandDefinition` | `check`, `lint` and `test`, each with `time_limit` 10 |
| `attempts_cap` | attempts before the human is asked | 2 |
| `crash_cap` | crashes before the human is asked | 2 |
| `acceptance_stage` | the stage of the feature acceptance | none |

An unknown key, `tool_paths` of earlier versions included, is refused like any other.

A stage has `role` (none: no agent runs there), `next` (`next[0]` is the forward move), `approval` (the human decides), `checks` (project commands run after the agent), `reports` (project commands run after green, recorded only) and `round_cap` (none: no cap). A role has `write_paths` (required; `{work_item}` is the work item's own file and `{feature}` its feature directory, the constants `WORK_ITEM_PLACEHOLDER` and `FEATURE_PLACEHOLDER`), `lease_duration` (60 minutes) and `time_limit` (40 minutes, the agent run's). A project command has `time_limit` (10 minutes). Every limit is a positive integer; stage, role and command names match `^[a-z][a-z0-9-]*$`.

- Values are taken only in their YAML type (strict mode): a limit is a YAML integer, so `true`, `'30'` and `30.0` are refused; `approval` is `true` or `false`, so `'yes'`, `'off'`, `1` and `0` are refused; names, `contract`, `checks`, `reports` and write paths are strings. A write path must hold at least one character that is not whitespace (`''` and `'  '` are refused at `roles.<role>.write_paths[<n>]`, with pydantic's message `String should match pattern '\S'`).
- A key with a default may be left out and takes it. A stage with nothing to say is written `done: {}`; `done:` alone is null and is refused (`invalid stages.done: ...`).
- Unknown keys are refused at every level, so a misspelt key is never ignored.
- A given `project_commands` replaces the default set as a whole; it does not merge. `lint: {}` takes `time_limit` 10.
- `ProjectCommandDefinition` has `time_limit` and `not_read`: a list of write-path patterns (`matches_any`) for the paths the command does not read, default `[]` (nothing left out). A pattern must be relative, non-empty, hold no `..` segment, not start with `~` and hold no `{` or `}` (a placeholder is expanded in write paths only). Otherwise the load fails, with the last rule of the definition, one fault per pattern: `project command <name>: not_read <pattern> must be a path pattern inside the checkout`. `is_inside_checkout` lives in `factory.pipeline.domain.pipeline_definition`; `write_paths` imports it. `KnownResults` passes it to `Git.work_tree_id` as `left_out`, and the tree that returns is part of the result's key.
- A name that breaks the pattern is reported at the path of its key: `invalid stages.<name>.[key]: ...`, likewise `roles.<name>.[key]` and `project_commands.<name>.[key]`.
- The methods: `first_stage()`, `role_of(stage)` (`None` for a stage without a role, `KeyError` for an unknown stage) and `position(stage)` (index in `stages`; `ValueError` for an unknown one, not specified).
- The rules that look across keys run at load, see "The rules of the definition" below. `first_stage()` is safe on a loaded definition, because rule 3 requires the stage `done`.

### Faults

`parse` raises only `PipelineDefinitionInvalid(fault)` (a `FactoryError`; the message is the fault). The faults are `not valid YAML: <problem> (line <l>, column <c>)` (`yaml_fault` in the same module builds it from ruamel's `problem` and `problem_mark`, 1-based, on one line: the repeated key is named in the problem, a line break inside the problem is written as the two characters `\n` or `\r`, and ruamel's context lines and its `To suppress this check` hint are left out; without a mark the position is omitted, and an error with no problem gives the first non-blank line of its text), `the pipeline definition must be a mapping` (a list, a string or an empty text) and the spellings of `all_faults` in `factory.shared.adapters.validation_faults`, the same module the work item reader uses: `unknown key: <path>`, `missing key: <path>` and `invalid <path>: <message>`. A `<path>` has dots between keys and `[n]` for a list position (`roles.coder.write_paths`). A text with several faults is refused once, with all of them joined by `; ` in the order unknown key, missing key, invalid value (`unknown key: x; missing key: contract`). The rules below run only when every field is valid, so the field faults come first and alone.

### The rules of the definition

`PipelineDefinition` has one validator that applies twelve rules, so every reader and every ref gets them. It collects the faults of all rules and refuses once, with the faults joined by `; ` in the order of the rules and, inside a rule, in the order of the stages or roles in the text. The reader reports the validator's message as the `fault`, without pydantic's `Value error, ` prefix.

**The contract.** `contract` is `<digits>.<digits>`. The major, compared as an integer, must be `CONTRACT_MAJOR` (1): `01.0` is read, `2.0`, `0.9` and `10.0` are not. Any minor is read (`1.0`, `1.7`, `1.10`).

**The lease.** For each stage with a role, the role's `time_limit` plus the `time_limit` of each command in the stage's `checks` and each in its `reports` must be at most the role's `lease_duration`. A command listed twice counts twice; a name that is no project command counts nothing; a stage without a role (an approval, `done`) is not measured. A role used by two stages is measured at each. With the defaults, 40 + 10 (one check) + 10 (one report) = 60 fits the lease of 60; a stage with two checks and a report adds up to 70 and does not.

The faults, in the order of the rules (`<s>` a stage, `<t>` a stage name, `<r>` a role, `<c>` a project command):

| Rule | Fault |
|---|---|
| 1 | `contract must look like <major>.<minor>, got '<contract>'` |
| 2 | `contract major <major> is not supported (this factory reads major 1)`, `<major>` as written |
| 3 | `stages must hold a stage named done`; `stage done must have no role and no next` |
| 4 | `stage <s>: next names unknown stage <t>`, once for each unknown name |
| 5 | in this order: `stage <s>: role <r> is not defined in roles`; `role <r>: write_paths is empty`; `stage <s>: an approval stage has no role` |
| 6 | `stage name <n> is reserved`; `role name <n> is reserved` (`human`, `factory`, `question`) |
| 7 | `stage <s>: check <c> is not a project command`; `stage <s>: report <c> is not a project command` |
| 8 | `role <r> at stage <s>: <total> min exceed lease_duration <lease> min` |
| 9 | `acceptance_stage <t> is not a stage with a role` |
| 10 | `stage <s>: next is empty` |
| 11 | `stage <s>: has neither a role nor approval` |

Rules 10 and 11 apply to every stage except `done`, and only when the stage `done` exists. Without it the end of the pipeline is unknown, and rule 3's fault is the one that matters. A stage with an empty `next` has nowhere to send a forward outcome or an approval; a stage with neither a role nor `approval: true` runs no agent and waits for no human. Rule 10's faults come before rule 11's, each in the order of the stages. A stage no `next` names (such as `acceptance`) is accepted: there is no rule on reachability.

Tests: `tests/pipeline/adapters/test_pipeline_rules.py` (through the reader, comparing `fault`) and `tests/pipeline/application/test_pipeline_loading_rules.py` (each refusal is one reported stop).

```bash
uv run python -c "
from factory.pipeline.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.shared.domain.errors import PipelineDefinitionInvalid
TEXT = '''contract: '1.0'
roles:
  coder: {write_paths: ['src/*']}
stages:
  doing: {role: coder, next: [done]}
  done: {}
'''
definition = RuamelPipelineDefinitionReader().parse(TEXT)
print(definition.first_stage(), definition.roles['coder'].lease_duration, sorted(definition.project_commands))
try:
    RuamelPipelineDefinitionReader().parse(TEXT.replace('contract', 'contrakt'))
except PipelineDefinitionInvalid as error:
    print(error.fault)
"
```

prints `doing 60 ['check', 'lint', 'test']` and then `unknown key: contrakt; missing key: contract`.

### The pipeline loader

`PipelineLoader(boundaries).load(ref=PIPELINE_REF)` (`factory.pipeline.application.pipeline_loading`; `PIPELINE_REF` is `origin/main`) is the one place that loads the definition. It reads `PIPELINE_DEFINITION_FILE` at `ref` with `git.show_file` (never the work tree), parses it with `pipeline_reader`, and only when the text is valid checks with `agent_definitions.names()` that every role has an agent. Every refusal of the definition is `PipelineDefinitionInvalid(fault)`; the faults are listed in `docs/operator-guide/stops.md`, "The stop `pipeline_definition_invalid`", and the rules in "The rules of the definition" above. When those checks pass, `load` clears `pipeline_definition_invalid` (at `PIPELINE_REF`) and then calls `agent_definitions.read(role)` for every role in the order of `roles`; an `AgentDefinitionInvalid` is raised to the caller as it is, not wrapped.

- Only the loader raises and clears the stops `pipeline_definition_invalid` and `agent_definition_invalid`; no caller does. At `PIPELINE_REF` a refusal calls `StopService.raise_stop` before it raises, and a success calls `clear_stop` before it returns. A refused agent file raises `RepositoryStop(reason="agent_definition_invalid", detail="<agent name>: <fault>")`; since a definition that passes its own checks has already cleared `pipeline_definition_invalid`, only the agent stop remains. Any `AgentDefinitionInvalid` raises it, not only an unapplied key.
- A load at any other ref raises the same refusal but raises and clears no stop, so a read of a branch never changes the health status. `WritePathService` ("The write paths" below) reads the definition at another commit and parses it directly with `pipeline_reader`, not through the loader.
- A `GitError` propagates and raises no stop. An `OSError` of the stop's writes propagates in place of `PipelineDefinitionInvalid`.
- Tests: `tests/pipeline/application/test_pipeline_loading.py`, with `human.push_file` and `checkout.fetch()` for other versions of the file and `install_agents(agent_home, roles)` in `tests/support/git_support.py` for the agent files.

## The prompt and the request for a stage

Before a stage's agent runs, `TaskComposer` (`factory.pipeline.application.task`) builds its `AgentRunRequest`; the caller gives it `Boundaries`, the `PipelineDefinition` and the `environment`, and each call a `TaskContext` (work item, path, stage, document, branch, pull request, the form findings). The pure rules are in `factory.agents.domain.prompts`.

### The decisions

`allowed_decisions(next_stages)` returns the stage's `next` in their order, then `question`. It is computed once in `compose`, and the same list goes into the prompt's line and into `AgentRunRequest.allowed_decisions`; the runtime builds its outcome schema from it and the stage protocol validates the agent's decision against it. `question` is always allowed. `stuck` is not a decision here: an agent that cannot finish ends with `question`.

### The prompt

`compose_prompt(PromptFacts)` joins these lines with one newline, no trailing newline:

| Line | When |
|---|---|
| `Work item: <path>`, `Id: <work item>`, `Stage: <stage>` | always |
| `Allowed decisions: <decisions joined by ", ">` | always |
| `Branch: <branch>`, `Pull request: <number>`, `Round: <round>` | always; the round is the document state's |
| `Mode: a test change the human approved; the coder's journal entry <n> names it.` | only when `test_change_entry` is set |
| `Format check: passed`, or `Format check found: 1. <message> 2. <message>` | only when `findings` is set (an empty list is `passed`) |
| `END_LINE` | always |

The Format check line goes to the first stage of the pipeline definition only; every later stage has `findings=None` and no such line.

The Mode line is decided from the journal's data, never from an entry's text: at a stage whose role is `tester`, `last_record(document, kind="result")` is read, and when its speaker is `coder` the line names its number. The last `result` record is used, not the last record, so a later `stall`, `crash` or `comment` record does not hide the test change. A `result` record by the tester, no `result` record, or any other role gives no Mode line.

### The request

`compose` fills `AgentRunRequest` with the agent as given, the prompt, the decisions, `time_limit` (the role's minutes), `working_directory` (`boundaries.checkout`) and no operating-system user. `environment` is a copy of the mapping given to `TaskComposer`, passed on unchanged: nothing is added, removed or scrubbed here (the wiring supplies it, already scrubbed at its source, `production_environment()`). `agent(stage)` reads the definition of the stage's role through `AgentDefinitionReader`; a stage without a role raises `ValueError` naming it, a missing file lets `AgentDefinitionMissing` through. A document without a state makes `compose` raise `WorkItemFormatError`.

The prompt is `compose_prompt(facts)`, except for an acceptance at the definition's `acceptance_stage` (`context.stage == definition.acceptance_stage` and `is_acceptance(context.work_item)`): there it is `acceptance_prompt(compose_prompt(facts), AcceptanceService(boundaries, definition).facts(feature_of(context.work_item)))`, so the fact lines (`Archived stories`, `Next free story number`, `Cost of the stories`, `Human interventions of the stories`) follow the usual prompt after an empty line. A story, an acceptance at another stage and a definition whose `acceptance_stage` is `None` get the unchanged prompt. The facts are computed by code at `origin/main`, not by the agent.

### The story form check

`StoryFormChecker(boundaries).findings(document)` returns `check_story_form(document, form, folder="in-progress")`. The form is read with `Git.show_file("origin/main", STORY_FORM_FILE)`, never from the work tree, so nothing an agent writes there changes it; the checkout must have fetched to see a form the human pushed. A form absent at `origin/main` raises `WorkItemFormatError` with `path == "factory/story-form.md"`. A stage runs the check before and after the agent.

An acceptance runs through this same stage protocol (`StageLauncher`, `AfterAgent`, `StageRunner`) unchanged. Its report (`# Acceptance of <title>` and `## Journal`) has none of the story form's sections, so `findings` returns `[]` for a document whose state is an `AcceptanceState` (the opening always writes one), before it reads the form: a missing form file is then no `WorkItemFormatError` either. The checker receives only the document, which is why it looks at the type of the state and not at the work item id. Without this, decision rule 1 would turn the reviewer's forward decision into a question every time.

Tests: `tests/agents/domain/test_prompts.py`, `tests/pipeline/application/test_task.py`, `tests/pipeline/application/test_task_acceptance.py`, `tests/pipeline/application/test_stage_run_acceptance.py`.

## Opening a work item

`WorkItemOpening` (`factory.hosting.application.opening`) runs before a stage is claimed. It is built with `Boundaries` and the `PipelineDefinition`. Neither method commits, pushes or fetches; the tick fetched before, so a commit pushed since is not seen. The claim makes the first commit, which for a new branch is also the opening commit.

### `prepare(work_item, path)`

`path` is the work item's file under its feature's `in-progress/` folder, the same on `main` and on its branch. The branch is `branch_name(work_item)`. When `prepare` returns, the checkout is on that branch with a clean work tree, and it returns a frozen `PreparedWorkItem` (work item, branch, path, document, `branch_existed`, `merge_conflict`).

- **No `origin/<branch>`: the work item is new.** The local branch is created at `origin/main` and the file is read from `origin/main`. An absent file raises `WorkItemFormatError` with `path` set. Only the body of the backlog file is used: whatever its own front matter says (`stage`, `attempts`, `blocked`, a `journal` list) is ignored. The state is `initial_state` of the definition's first stage. A body without a `## Journal` section gets an empty one at its end; entries already in that section are left as they are, and the form check reports the mismatch between the text and the one record of the state. Entry 1 (`human`, `created`, dated by the clock) is then appended by code.
- **`origin/<branch>` exists.** The local branch is reset to `origin/<branch>`, whatever a local branch of that name held, then `origin/main` is merged in. On a conflict the wrapper has already aborted the merge: `merge_conflict` is `True`, the head is the remote branch's and the document is the branch's. The document is read from the work tree after the merge.

Doing the merge here means the baseline of the take, taken at the stage-start commit, comes after every preparation step.

### `ensure_pull_request(work_item, document)`

Returns, in this order: the pull request numbered in `document.state.pull_request` if it is open; the open pull request of the branch; a new draft titled `<id>: <title>` with the body as description. Only an open pull request is reused; a closed or merged one never is. The title is looked up only when a draft is created, and a body without a title line then raises `WorkItemFormatError`. A `HostingServiceError` propagates. No file changes.

Tests: `tests/hosting/application/test_opening.py`.

## Starting a stage

`StageLauncher(boundaries, instance, definition, environment, *, stage_environment=None)` (`factory.pipeline.application.stage`) takes a `PreparedWorkItem` from `WorkItemOpening.prepare` and runs the stage's agent. `instance` and `definition` go to `ClaimService`; `environment` is the environment of the agent run and reaches `TaskComposer` unchanged, so the run holds exactly those entries.

`launch(prepared)` does these steps in this order. The claim in step 4 is the only write to the git remote.

1. Refuse a work item with `merge_conflict` set or without a state: `ValueError`, before anything is read or pushed.
2. Read the agent definition with `TaskComposer.agent`. A stage without a role (the approval stage) raises `ValueError` naming the stage; a missing agent file raises `AgentDefinitionMissing`. Both come before any push.
3. Take the story form findings from `prepared.document` (`StoryFormChecker`).
4. Push the claim: `ClaimService.claim(branch, path, document, stage)` makes the stage-start commit. A rejected push or an unreachable remote raises `PushFailed`.
5. Read the work item file back from the work tree. `StartedStage.document` is what the stage-start commit holds, not the document given to the claim.
6. `WorkItemOpening.ensure_pull_request`: find or create the pull request.
7. `WritePathService.at(stage_start, path)` gives the `WritePathSettings`, from the definition at the stage-start commit.
8. `TaskComposer.compose` builds the request (prompt, environment, allowed decisions).
9. `stage_environment.prepare(stage_start.commit, branch, sync_time_limit=...)` after step 8, then `stage_environment.run_agent(request, run=PatientRuns(boundaries).run)`: the agent runs through `PatientRuns`, in the stage environment (see `machine.md`, *The stage environment*). The cost record is begun between the two and completed after the run. The sync limit is the `time_limit` of the definition's `sync` project command, or the default of a project command (10 minutes) without one. A `SnapshotError` or `ContainerError` from `prepare` ends the launch, after the claim and before any run.

**`PatientRuns`** (`factory.agents.application.provider_limits`; `PatientRuns(boundaries).run(request)`) wraps `boundaries.agent_runtime.run` for the stage launch. A result that does not end `provider_limit` comes back as it is. After a `provider_limit` it loops: (1) the budget left is the agent's `budget_usd` less the run's cost so far, and at or below zero the run ends `budget`; (2) the time left is the request's `time_limit` less the calls' durations (the waits do not count), and at or below zero it ends `time_limit`; (3) when the waits reach the ceiling it logs `provider limit: <agent> waited <s> s, the ceiling of <c> s; the run ends provider_limit` and returns the result; (4) otherwise it logs `provider limit: <agent> waits <w> s before it resumes <session>` (`a new run` without a session), waits the result's `limit_wait` or the cool-down, at most what is left of the ceiling, and (5) calls the runtime again with `request.model_copy(...)`: `CONTINUE_PROMPT` and `resume_session` with a session, the request's own prompt without one, and in both the budget and the time left; (6) `resumed_result` joins the calls. The cool-down and the ceiling are `boundaries.settings.provider_limit` (`ProviderLimit`, `factory.agents.domain.provider_limits`, defaults 10 and 120 minutes, from `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` and `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES`). It builds no `AgentRunRequest` of its own. The preflight's probe uses `run_sealed` without `run` and never waits.

**`Waiter`** (`factory.watching.application.machine`) is the interface of waiting: `wait(duration)` returns after it and raises `ValueError` for a negative one. `SleepingWaiter` (`factory.shared.adapters.clock`) calls `time.sleep`; `ManualWaiter(clock)` advances a `ManualClock` by the duration, records it in `waits` and returns at once. `build_boundaries` gives `SleepingWaiter()`. Tests: `tests/agents/application/test_patient_runs.py`, `tests/pipeline/application/test_stage_provider_limit.py`, `tests/watching/adapters/test_waiters.py`.

**No agent run precedes the pushed claim.** When `run` is called, `origin/<branch>` already holds the stage-start commit with the claim and the journal record (`factory`, `started`); when step 4 fails, no run starts. The stage-start commit is the last commit before the run: for a branch that existed it is one commit above the old head (the merge of `main` in `prepare` comes before it), for a new work item it is also the opening commit.

The stage-start commit does not change `pull_request`: it is `None` for a new work item and otherwise the number already recorded. The number of the pull request found or created in step 6 is in `StartedStage.pull_request` and in the prompt; the stage's next commit records it. No local record of the run is written; the claim's `started_at` says when the stage began.

`launch` returns a frozen `LaunchedStage`: `started` (a `StartedStage` with the work item, stage, branch, path, `stage_start`, `document`, `pull_request` and the form `findings` taken before the run), `request` and `result`. A run that dies, reaches its `time_limit` or its budget is a result. `PushFailed`, `AgentDefinitionMissing` and `AgentRuntimeError` propagate unchanged; after an `AgentRuntimeError` the claim stays pushed.

Tests: `tests/pipeline/application/test_stage_launch.py`. `ObservingRuntime` (`tests/support/observing_runtime.py`) is an `AgentRuntime` that records the remote branch's head, the checkout's `HEAD` and the pull requests in the hosting fake at the moment `run` is called, then delegates to `FakeAgentRuntime`.

## Stalls

A stall is the one way a stage ends without a result the factory can keep. It costs one attempt and is a value, never an exception. `StallService.stall` (`factory.pipeline.application.stalls`) does it; the later stories (the branch, the decision, the form, a red check, a merge conflict) call it with their reason.

### The reasons

`factory.work.domain.decisions.StallReason` (defined in `factory.work.domain.journal`, which the stall record names) is one of `died`, `time_limit`, `budget`, `provider_limit`, `no_result`, `decision_not_allowed`, `form_invalid`, `check_red`, `merge_conflict`. `stall_reason_of(result)` maps the end reason of an `AgentRunResult` to the reason of the same name and `completed` to `None`.

`factory.hosting.domain.post_texts.stall_cause(reason, detail="")` gives the reason's sentence, and `<sentence>: <detail>` with a detail. `stall_note(reason, attempts, attempts_cap, *, detail="")` gives `Stalled (attempt <n> of <cap>): <cause>. ` and then `Retrying on the next tick.` when `attempts < attempts_cap`, otherwise `The attempts cap is reached; the factory asks you next.` The word "retry" appears only in the first case.

The detail's trailing line breaks are removed. A detail of one line is part of the sentence, as above. A detail of several lines puts its first line through `stall_cause` into the sentence, so the follow-up stays on that first line, and the remaining lines follow after an empty line in a fenced block: the fence `` ```text ``, the lines unchanged, the closing fence. GitHub renders a comment as Markdown, and unfenced output loses `<module>` and turns `__init__` bold. The fence is three backticks, or one more than the longest run of backticks in the remaining lines when that run is three or longer. The journal's stall entry is unchanged and keeps the detail as continuation lines.

### `StallService.stall(context, reason, detail="")`

`StallService(boundaries, instance, definition, stage_environment=None)`; `None` means `stage_environment_of(boundaries)`. `AfterAgent`, `StageFinisher` and `StageRunner` each give their stall service the environment they hold, and `StageRunner` builds one for all of them, so one object per stage sees every `prepare` and every `take`. `StallContext` (frozen, no unknown keys) holds `work_item`, `stage`, `branch`, `path`, `stage_start` (a `StageStart`, or `None` when the stage never started, for example a merge conflict at the preparation) and optionally the `document`, the `pull_request` and the `cost` (a `CostRun`) the caller already holds. The steps, in this order:

1. With a `stage_start`: when the checkout is not on `context.branch`, what the agent left on the other branch is discarded with `reset_to("HEAD")` (that branch keeps its head) and the branch is checked out at the stage-start commit. Then `stage_environment.take(context.stage_start, context.path)` runs, whatever the reason, `check_red` included; its report, a `TakeReport`, is `StallResult.take`. With a `context.cost`, the sidecar is written again right after the take. Without a `stage_start` nothing is taken and `take` is `None`. A `WorkItemFormatError`, `SnapshotError` or `ContainerError` from the take propagates before anything is written, committed, pushed or posted.
2. The document is `context.document`, else the work item file read from the work tree.
3. The pull request is `context.pull_request`, else `WorkItemOpening.ensure_pull_request` (an open pull request of the branch, or a new draft).
4. The new state has `attempts` + 1, the claim released (`ClaimService.release`) and `pull_request` set; `stage`, `blocked`, `round`, `crashes`, `comments_read` and `handed_over` stay. One entry is appended: speaker `factory`, kind `stall`, text `Stage <stage> stalled (attempt <n> of <cap>): <cause>`.
5. The file is written, everything in the work tree is committed in one commit and pushed. Any push outcome but `pushed` raises `PushFailed` with git's reason. The stall push is not retried.
6. After the push, the note is posted with `PostKey(work_item, "stall", <the stall entry's number>)`.
7. Whether the note was `posted` or `already_posted`, `HostingService.set_labels(pull_request, labels_for(<the stalled state>))` writes the stage label, so a first-stage stall has its label before any result commit. Written, never read back.

So a stall keeps the writes inside the write paths (the environment's take brings those writes from the dataset into the work tree and leaves the rest there) and releases the claim, which keeps a later tick from taking the stalled stage for a crash. The stall adds one commit, directly above the stage-start commit: the agent cannot commit, because the checkout's `.git` is the factory's alone (see the decision log's "The factory alone writes the checkout's `.git`").

A `HostingServiceError` is not a stall and propagates unchanged: from step 3 before anything is written, committed or pushed, so the remote is unchanged; from step 6 after the push, so the stall commit stays on the remote, no note is posted and no label is written; from step 7, so the stall commit stays and the note stays posted. `StallResult` (frozen, no unknown keys) holds `reason`, `attempts`, `attempts_cap`, `commit` (the pushed head), `pull_request` (the last three at least 1), `note` (the `PostOutcome`) and `take` (a `TakeReport`, or `None`).

Tests: `tests/agents/domain/test_decisions.py`, `tests/work/domain/test_stall_texts.py`, `tests/hosting/domain/test_stall_note_block.py`, `tests/pipeline/application/test_stalls.py`, `tests/pipeline/application/test_stall_labels.py`. The last starts stages with `StageLauncher` and the fake agent runtime; its `SwitchingRuntime` (a subclass of `ObservingRuntime`) switches the checkout to another branch while it runs.

## After the agent run

The factory believes what it observes, not what the agent reports. `AfterAgent(boundaries, instance, definition, *, stage_environment=None).process(launched)` (`factory.pipeline.application.stage`) takes the `LaunchedStage` that `StageLauncher` returns and goes through these steps in order. The first step that fails is a stall (see "Stalls"), which counts one attempt, and the later steps do not run.

1. **Result.** `stall_reason_of(result)` turns a run that died, ran out of budget or time, or gave no result into the stall of that reason; the detail is the first permission denial (`denied: <tool>: <detail>`), if any. A decision that is not one of the request's `allowed_decisions` is `decision_not_allowed`, with the decision and the allowed ones as detail.
2. **Take and restore.** `stage_environment.take(stage_start, path)` puts the changes outside the write paths back; the container environment copies the changed paths the role may write, and `left` of its `TakeReport` is the paths it left in the dataset. Then the stage-start state (the claim included) and the stage-start journal are put back, whatever the agent wrote there: **the agent's edits to state and journal are always discarded.** The rest of the body keeps the agent's changes when the role may write the work item; when it may not, the take has put the whole file back and lists it in `left`.
3. **The entry.** `factory.work.domain.decisions.agent_entry(role=, stage=, decision=, text=, left_out=)` builds it, and code decides everything but the words. The speaker is the role. The kind is `question` for the decision `question`, otherwise `result`. The text is the agent's text, stripped, with one leading `<role>:` or `<stage>:` removed (the colon directly after the name; the role is tried first). A blank text gives `None`, which `AfterAgent` stalls as `no_result`. When the take left paths out, the text ends with a blank line and `The factory left out changes outside the write paths: <paths sorted, joined by ", ">.`. The work item's own cost-record file, which the factory rewrites after the take, is never named there.
4. **The form again.** The story form is checked on the taken work item and compared with the findings from before the run (`StartedStage.findings`). Only a finding that was not there before stalls, as `form_invalid`, with the new messages joined by `; ` as detail. Findings are compared by message with every run of digits replaced by one mark, so a finding whose line number moved because the agent edited above it is the same finding. A kind that now occurs more often than before counts as new: of equal messages the earlier ones count as the old ones. Only in this stall is the entry appended (above the stall entry); otherwise it is built but not appended.

What comes back is an `AgentAftermath` (frozen, no unknown keys): `started`, `request`, `result`, `decision`, `document` (the work item after step 2, without the entry), `entry`, `take` (the `TakeReport`) and `form_findings` (all findings after the run). The stage's result commit ("The stage protocol", below) appends the entry.

Tests: `tests/agents/domain/test_agent_entry.py`, `tests/pipeline/application/test_after_agent.py`. The latter starts stages with `StageLauncher` and the fake agent runtime, whose `ScriptedRun.writes` tampers with the work item, writes outside the write paths and breaks the form.

## The decision rules

`factory.work.domain.decisions.decide(definition, state, decision, findings=())` turns the agent's decision into a `StageMove` (frozen, no unknown keys): `rule`, `stage`, `blocked`, `round` and `question`. It is pure; `StageFinisher` ("The stage protocol", below) applies the move. It never touches `attempts` or `crashes`: a rework counts rounds, a stall counts attempts, and the two are kept apart.

"Forward" is a decision equal to `next[0]` of the state's stage; a "rework" is any other entry of `next`. This is the only rule for counting rounds, wherever in the pipeline definition the named stage sits. A stage missing from the definition, or a decision that is neither in `next` nor `question`, raises `ValueError` naming it.

The rules are tried in v1's order; rule 5 (a red check) is not decided here but by the checks after the move:

| Rule | When | Stage | `blocked` | `round` | `question` |
|---|---|---|---|---|---|
| 1 | forward, and `findings` is not empty | unchanged | `question` | unchanged | `findings_question(findings)` |
| 2 | decision `question` (findings do not matter) | unchanged | `question` | unchanged | `None`: the agent's own entry is the question |
| 3 | rework, stage has `round_cap`, `round + 1 <= round_cap` | the decision | `None` | `round + 1` | `None` |
| 4 | rework, stage has `round_cap`, `round + 1 > round_cap` | unchanged | `round_cap` | `round + 1` | `round_cap_question(round + 1, round_cap)` |
| 5 | forward, but a check is red | unchanged (a stall, see "The stage protocol") | | | |
| 6 | forward, no findings | `next[0]` | `None` | unchanged | `None` |
| 7 | rework, stage has no `round_cap` | the decision | `None` | unchanged | `None` |

Rules 3, 6 and 7 move, so they clear a `blocked` of `question`. `findings` matter only to a forward decision. Rule 6 only says the move; its checks run afterwards.

The factory's own question texts are in `factory.hosting.domain.post_texts`: `round_cap_question(rounds, cap)`, `findings_question(findings)` (the messages numbered from 1, joined by one space) and `attempts_cap_question(stage, attempts, last_stall)`. That module imports `StallReason` and `FormFinding` only under `TYPE_CHECKING`, because `decisions` imports it.

Tests: `tests/work/domain/test_decision_rules.py`, `tests/work/domain/test_question_texts.py`.

## The stage protocol

`StageRunner(boundaries, instance, definition, environment).run(work_item, path)` (`factory.pipeline.application.stage`) is the one entry point that runs a stage from the claim to the result commit. It returns a frozen `StageReport`: `work_item`, `stage` (the stage that ran, from the state `prepare` read), `next_stage`, `rule` (the decision rule applied, 1 to 7, or `None` when the stage stalled before a decision), `commit` (the pushed head), `pull_request` and `stall`. `stall` is set exactly when the stage stalled; `next_stage` equals `stage` for a stall and for the rules that keep the stage (1, 2 and 4). A red check is rule 5.

`run` does these steps in this order; a `StallResult` from any step ends the run with a report whose `rule` is `None`:

1. `WorkItemOpening.prepare`. With `merge_conflict` set in the result, `StallService.stall` with reason `merge_conflict` and no stage start: no claim is pushed and no agent runs.
2. `StageLauncher.launch`: claim, pull request, prepare, agent run. `environment` is passed unchanged. `StageRunner` builds one stage environment and gives it to its launcher, its after-agent, its finisher and its own stall service.
3. `AfterAgent.process`: branch, result, take, entry, form.
4. `StageFinisher.finish`: decision, checks and reports, result commit.

### `StageFinisher.finish(aftermath)`

1. `decide` on the state of `aftermath.document`, with the form findings after the run. A first stage whose agent fixed the last finding therefore moves forward instead of asking.
2. Rule 6 only: each check of the stage's `checks`, in order, through `KnownResults.run` (`machine.md`, *Known results*), which runs `ProjectCommands.run` with the `time_limit` of the pipeline definition's project command unless a passed result is known for the same key. The first one that is not green ends the stage as a stall `check_red` (rule 5): the later checks and all reports do not run. The stall detail is the command's name and the last `STALL_TAIL_LINES` (15) lines of its output (all, when fewer). The journal then holds the agent's entry, ending with the lines of the checks that were green, directly above the `factory` stall record. The stall costs one attempt and changes neither the stage nor `crashes`. The stall takes through the stage environment like any stall with a stage start; what the check wrote outside the write paths stays in its check container. The checks see the work tree after the take.
3. Rule 6 only, once every check is green: each report of the stage's `reports`, in order. A report that fails holds nothing; a report is recorded, never enforced.
4. The agent's entry gains, after a blank line, one line `` `<command>`: <last line of its output> `` (`command_line`) for each green check and each report, in the order they ran (for example `` `check`: 12 passed ``). A result taken instead of a run adds `` (not run again: passed on tree <12 characters> at <time>) ``, and a result stopped at its time limit adds `` (stopped at its time limit after <s> s) ``. A stage with neither gets no such lines.
5. The entry is appended; when the move has a question (rules 1 and 4), a `factory` entry of kind `question` follows it.
6. The new state takes `stage`, `blocked` and `round` from the move and `pull_request` from the started stage, and the claim is released. `crashes` is reset to 0 on rule 6, a forward move, and unchanged otherwise; `attempts`, `comments_read` and `handed_over` never change.
7. The file is written, everything in the work tree is committed in one commit and pushed through `push_with_retries` (`factory.hosting.application.pushes`): a server refusal (`[remote rejected]`) or an unreachable remote is pushed again after 5, 15 and 45 s (`RETRY_WAITS`, waited through `boundaries.waiter`), each wait after the log line `push: retry <n> of 3 in <s> s: <reason>`; the same commit, the same command, no force. Any other refusal, and the last failure, raises `PushFailed` with git's reason, and no label has been written.
   Between the commit and the push, when the move's stage is an approval stage (`approval` in the pipeline definition): `HostingService.set_description(number, text)`, with `hand_over_description(moved, Git.log("HEAD", since="origin/main"))` for a story, or `acceptance_description(moved, role)` for an acceptance, `role` being the role of the stage that ran. After the push those commits are the ones the hand-over reads from `origin/<branch>`. A `HostingServiceError` there is caught and logged as `pull request #<number>: description not written before the push: <error>`, and the push goes on; the hand-over writes the description on the next tick. A forward move, a rework and a question write no description. It is the private `_describe` of `_commit_and_push`; the order commit, description, push is fixed. `handed_over` stays unset.
8. Last, `HostingService.set_labels(pull_request, labels_for(new_state))`. `labels_for` (`factory.work.domain.labels`) gives `[LABEL_PREFIX + state.stage]`, for example `["stage:review"]`. Labels are a projection of the stage: they are written after the push and never read back. A `HostingServiceError` from this step propagates; the result commit stays pushed.

Rules 1, 2, 3, 4 and 7 run no check and no report.

A run adds exactly one commit of the factory's own on `origin/<branch>`: the result commit or the stall commit, directly above the stage-start commit, since the agent cannot commit. It holds the whole work tree, so a file a check creates is committed unless `.gitignore` covers it.

Tests: `tests/work/domain/test_labels.py`, `tests/pipeline/application/test_stage_finish.py`, `tests/pipeline/application/test_stage_run.py`. The checks and reports are real `make` targets from a `Makefile` the tests push to `main`; the agent is `FakeAgentRuntime`, the hosting service its fake.

## The take's rule

`TakeService(boundaries, mount_point).take(stage_start, work_item_path, changed_paths)` (`factory.pipeline.application.take`) copies from the dataset into the work tree what the role may write and leaves the rest. Its steps are in `machine.md`, *The take*; this section is the rule they apply. Three functions of the module hold it: `is_refused(path, settings, work_item_path)`, `read_baseline` and `restore_work_item`.

### What is left out

The rule is read at the stage-start commit, and applied to the paths the dataset changed. A candidate is refused, and so left out and named in `TakeReport.left`, in two cases:

- `refusal(path, settings)` is not `None`: the path is outside the write paths of the stage or is protected (see "The write paths"). The settings come from `WritePathService.at`, that is from the pipeline definition at the stage-start commit. An agent that rewrites `factory/pipeline.yml` to widen its role widens nothing, and an invalid rewrite does not make the take raise; the work tree keeps its pipeline definition.
- The path lies directly in an `in-progress` folder of a feature (`factory/features/<feature>/in-progress/<file>`) and is not the stage's own work item. This leaves out every other work item in progress, every cost-record file (`.costs.jsonl`), the stage's own included, and any other file there, whatever the write paths say. Nested files (`in-progress/sub/x`), other lifecycle folders and an `in-progress` folder outside `factory/features/` follow the write paths.

A left-out path is never written to the work tree, so there is nothing to revert. The entry names the paths (`The factory left out changes outside the write paths: <paths>.`, see *After the agent run*).

### The work item

The stage's own work item is handled separately. Its state and journal are restored from the stage-start commit with `restore_state_and_journal`; the agent's edits to its sections stay. `TakeReport.restored_work_item` is true when that changed the file. If the agent deleted the file or left front matter that cannot be read, the file is checked out whole from the stage-start commit (`Git.revert_paths`) and `restored_work_item` is true; it is not in `left`. A work item the role may not write at all is refused like any path: it is in `left`, the work tree keeps its copy, and `restored_work_item` is false.

The baseline is read first. When the stage-start commit does not hold the work item, or holds it unreadable, `take` raises `WorkItemFormatError` naming the path before it changes anything.

### The sidecar

The work item's `.costs.jsonl` is refused by the in-progress rule, so the take never brings the agent's copy; the factory rewrites it from memory after the take (`watching.md`).

### Limits

- The take makes no commit and no push. A commit the agent made on the dataset does not reach the work tree; only the changed paths are copied.
- Ignored paths are not judged: the take drops them, and the factory removes none (see *The take*, `machine.md`). Anything outside the checkout is not seen.
- Git's paths are taken as they are; renames show as a deletion and an addition (see "The git wrapper").

Tests: `tests/pipeline/application/test_take_rule.py` (the rule through `TakeService.take` on `FakeSnapshots`), `tests/pipeline/application/test_take.py` and `tests/pipeline/application/test_take_edges.py`.

## The tick

`Tick(boundaries, instance, handlers, status=None, preflight=None).run(*, fetched=False)` (`factory.pipeline.application.tick`) is one pass, in this order (disk check, fetch, load, restore, publish the stop records, preflight, clean up, evaluate, dispatch). The order matters: the remote is the only truth, so nothing of the remote is read before the fetch, and beyond the remote the tick reads only the agent files in the agent's home and the instance's state directory (the health file and the records), never what an earlier tick left in the checkout.

0. **Disk check** (`Tick._check_disk`), before the fetch. It reads `disk.free_bytes` of `settings.checkout.parent`, then of `settings.state_directory`; an `OSError` raises the machine stop `disk_low` at once with the detail `cannot read the free space of <path>: <error>` (no later path is read) and ends the tick with `TickOutcome(stopped="disk_low")`. Otherwise `disk_low_detail(free, settings.min_free_gb)` (`factory.machine.domain.disk`) gives the detail of a stop, raised the same way, or `None`, and the step calls `clear_stop("disk_low")`. `Tick._stop` takes a `scope`, `machine` here.
1. **Fetch** (`Git.fetch`). `FetchFailed` raises the repository stop `fetch_failed` (detail: the error's text) and ends the tick; success clears it. With `run(fetched=True)` the tick skips this step, its raise and its clear of `fetch_failed`, because the caller fetched just before and owns the stop: `factory-run` fetches once in an iteration (`_ProjectImageStart._follow_main`) and builds its tick with `fetched=True`. Every other caller (`fetched=False`, the default) fetches here as above.
2. **Load** the pipeline definition with `PipelineLoader` from `origin/main`. `PipelineDefinitionInvalid` ends the tick with `TickOutcome(stopped="pipeline_definition_invalid")`, and `AgentDefinitionInvalid` with `stopped="agent_definition_invalid"`; the loader raised the stop and clears it on a later success, the tick does neither.
3. **Restore** the checkout: one line `discarded uncommitted changes: <path>, <path>` (the paths in the order of `Git.status()`) when there are changes, then `reset_to("HEAD")`, `checkout("main", start_point="origin/main")`, and `delete_branch` for every `work-item/<id>` of an id that has `origin/work-item/<id>` or a story in `in-progress/` on `origin/main`. Other local branches stay. The restore removes no ignored path; whatever the line of the uncommitted changes names comes from `status()`, which lists no ignored path. A `GitError` here raises the stop `checkout_restore_failed` and ends the tick; success clears it.
3a. **Publish the stop records** (`Tick._publish_stop_records`): `StopPublisher(boundaries).publish()` (see "Stops, the clock and the factory log"). A `GitError`, `PushFailed` or `OSError` writes `cannot publish the stop records: <error>` to the log and the tick goes on. It stands after the restore because the restore logs what a killed stage left behind (`discarded uncommitted changes: ...`) before the publisher's checkout could discard it, and before the preflight so that a stop raised by an earlier tick reaches `main` even when this tick's preflight stops. A tick that ends earlier (`disk_low`, `fetch_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `checkout_restore_failed`) publishes nothing.
4. **Preflight**, when a `Preflight` is given (`preflight=None` skips the step): `preflight.run()` raises and clears its own stops. A reason it returns ends the tick with `TickOutcome(stopped=<reason>)`, before the cleanup. `build_tick` always gives one, made by `build_preflight(boundaries, settings, which, extra=())` in `factory.entry.wiring`; `build_tick` passes `machine_extras(boundaries, settings, environment)` (`token-file`, `podman`, `zfs`, `dataset`, `stage-image`, `opencode` only when `agent_runtime` is `opencode`, `agent-run-probe`, in that order; see `machine.md`, *The preflight*), computed from the same `agent_run_environment(...)` the handlers get. `opencode_item(settings, agent_models)` (`agent_models` from `installed_models(boundaries)`, the `model` of each installed agent in the order of the agents' names, each once, `[]` when the definitions cannot be read) fails for each alias without a mapping in `opencode_models`; it looks for no executable (the opencode the agent runs is the stage image's) and reads no login file. `MachineChecks.run` checks `REQUIRED_TOOLS` (`git`, `uv`) and no runtime executable, and the version item compares against the pin of the runtime in force.  One more item is `agent_run_probe_item(boundaries, settings, environment)` in `factory.machine.application.preflight`; under opencode its hint names `run <executable> run by hand`, gives no token hint, and for the login `none` adds the single sign-on hint; the probe runs the agent `coder` at `PROBE_BUDGET_USD` through the stage environment's `run_agent` and fails on any end but `completed`, on `AgentRuntimeError` and on `AgentDefinitionError`.
5. **Clean up** with `delete_stale_branches(boundaries)` (`factory.pipeline.application.recovery`, see "The stale branch" below). A stop of an earlier step, the preflight's included, ends the tick before it.
6. **Evaluate** with `Watcher(boundaries, instance).evaluate(definition)`.
7. **Dispatch**: `handlers(definition)` is built now, because the handlers take the loaded definition, and a `Dispatcher` with the tick's status handles the event. The tick keeps the dispatcher's status for the next run.

**The stale branch.** `delete_stale_branches(boundaries) -> list[str]` deletes the remote branches that a kill or a refused deletion left behind for a story that is already in `backlog/` or `done/`. It lists the stories of `origin/main` with `RemoteWorkItems.list_stories` for `backlog`, `done` and `in-progress`; the stale ids are those of the first two that no `in-progress` story file shares (a shared id is the `duplicate` case, which the evaluation reports). For each branch of `Git.remote_branches()` whose `work_item_of_branch` is a stale id, in the order of the names, it calls `Git.delete_remote_branch`. Outcome `"pushed"` writes `deleted stale branch <name>: its story is back in the backlog` (`its story is done` for `done/`, also for an id with story files in both `backlog/` and `done/`) and adds the name to the result; any other outcome writes `could not delete stale branch <name>: <outcome>` and goes on, to be tried on the next tick. It reads only `origin/main` and the remote-tracking branches, makes no hosting call, and does not catch `GitError`. Because of it, a story started again after a discard that was killed starts with an empty bill.

`run` returns `TickOutcome(stopped=..., event=..., dispatch=...)`: `stopped` is set and the others are `None` when the tick ended at a stop. `WorkItemFormatError`, `ValueError` from the evaluation and a `GitError` outside the fetch and the restore are not caught; no stop exists for them. The tick keeps no local record of a run and no lock. `IdleHandler` does nothing and is the handler of `idle`.

Because the checkout is rebuilt every tick and no local state is read, a rejected push leaves no trace: the next tick judges the remote. The dispatcher's count of errors per event and remote state is the only memory, and it is in the `TickStatus`. A push to the work item's branch changes the remote state and so retries a capped event. Every handler error, a `GitError` included, is counted as above, and each counted error writes one log line, `handler_error_line` of `factory.pipeline.domain.tick_status` (see `docs/operator-guide/stops.md`, *An event that keeps failing*). `HandlerFactory` is `Callable[[PipelineDefinition], Mapping[EventKind, Handler]]`; the production factory is `handler_factory` (see "The handlers of the events").

## The handlers of the events

`factory.entry.wiring.build_handlers(boundaries, definition, instance, environment)` is the one place that registers a handler (R5, nothing else wires); production code never builds a `Dispatcher` from a hand-written mapping. It returns the handlers of all thirteen kinds: `idle` (`IdleHandler()`), `run` (a `RunGate` around `RunHandler(boundaries, instance, definition, environment)`), `crash` (`RecoveryHandler(boundaries, definition, ClaimService(boundaries, instance, definition), <the RunGate registered for run>)`, the very same gate, so a rerun after a crash reads the pull request first), `expired` (the very same `RecoveryHandler` instance as `crash`), `comment` (`CommentHandler`), `ask` (`AskHandler`), `merged` (`SplitByWorkItemKind(MergedHandler, AcceptanceMerged)`), `closed` (`SplitByWorkItemKind(ClosedHandler, AcceptanceClosed)`), `reject` (`RejectHandler`), `hand_over` (`SplitByWorkItemKind(HandOverHandler, AcceptanceHandOver)`), `acceptance_due` (`AcceptanceDueHandler`), `duplicate` (`DuplicateHandler`) and `pull_request_lookup` (`PullRequestLookupHandler`). The `closed` and `merged` splits are built once and shared: the instances registered for `closed` and `merged` are the very ones the `RunGate` holds, so an acceptance whose pull request was closed or merged while its stage was due never reaches the story's handlers. With no `acceptance_stage` in the pipeline definition every handler still constructs; the acceptance handlers refuse the events they are given with `CannotHandle(kind, "no acceptance stage")`. `handler_factory(boundaries, instance, environment)` returns the `HandlerFactory` the tick takes: a function of the loaded definition that calls `build_handlers`, so the handlers always hold the definition the tick has just loaded. `factory-run` builds the `Tick` with it.

Every `EventKind` has a handler in `build_handlers`. A new kind adds its handler there; `test_every_kind_has_a_handler_and_acceptance_due_opens_the_acceptance` fails until it does. The dispatcher counts an event of a kind without a handler as an error (`UnhandledEvent: no handler for event kind <kind>`), never silence.

**A crash is discarded and the stage is rerun.** `RecoveryHandler(boundaries, definition, claims, run)` (`factory.pipeline.application.recovery`) handles `crash`, the event the watcher raises when the work item's claim is this instance's own (`ClaimService.status` is `own`), and `expired`, raised when the claim is another instance's and its lease has run out (`status` is `expired`). Its `run` property is the handler it reruns with. `handle` does five things in order (a sixth, 4b, only for `expired`):

1. Guards, before anything is touched: `CannotHandle` for an event of another kind, for an event without a work item or a snapshot without state (`target_of`), for a claim whose status is not the one the kind needs (`required_claim_status(kind)` in `factory.pipeline.domain.evaluation`, the inverse of `CLAIM_EVENTS`: `own` for `crash`, `expired` for `expired`; the rest raise `CannotHandle` with the event's kind) and for a snapshot with no `branch_commit`. A crash is charged only to a claim this instance holds; another instance's claim is its lease's business.
2. Discard: `WorkItemRecorder.check_out(branch)` resets the checkout to `HEAD`, then puts the local branch at `origin/<branch>`. Uncommitted and untracked files, local commits that were never pushed and the dead stage's cost records (they live in the work tree until the stage's result is pushed) are gone. The head it went back to is normally the stage-start commit; a commit the human pushed to the branch meanwhile is on the remote and stays.
3. Record: `crashed(state)` (`factory.pipeline.domain.recovery`) raises `crashes` by one and nothing else; `ClaimService.release` clears the claim; one journal entry of speaker `factory` and kind `crash` is appended, with the text of `crash_entry_text(stage, crashes, head)`. `attempts` is not touched: a crash is not a stall. For `expired` the entry has kind `expiry` and the text of `expiry_entry_text(stage, crashes, head)` (`factory.pipeline.domain.recovery`); the state change is the same.
4. Push: `WorkItemRecorder.record` writes the work item, makes one commit on top of the remote's head and pushes it. The subject is `work item <id>: crash of stage <stage> recorded` for a `crash` and `work item <id>: expiry of stage <stage> recorded` for an `expired`, where `<stage>` is the stage the work item was in. Any outcome but `pushed` raises `PushFailed`.
4b. Note (`expired` only): after the push, `StopService.post` puts `expiry_note(crashes, definition.crash_cap)` on the pull request with the key `<id>:expiry:<the expiry entry's number>` (a draft is opened when there is none; its number is then committed and pushed as `ask_crash_cap` does). A `HostingServiceError` propagates and the note is not posted again. A `crash` posts nothing.
5. Rerun: `run.handle` is called once, in the same call, with a `run` event whose snapshot carries the new document and the crash commit (`branch_commit` and `remote_state`). Nothing waits for the lease or an idle pause.

Below the cap a `crash` posts nothing on the pull request; an `expired` always posts its note (4b), also at the cap, where the question follows it. `GitError`, `PushFailed`, an exception from the rerun and `InjectedKill` leave `handle` uncaught; a kill before the push leaves the remote as it was, so the retry counts the crash once. 

**The crash cap asks the human.** `crash_cap` is a key of the pipeline definition (default 2; see its table). The cap counts the crashes since the last forward move: a forward move resets `crashes` in its result commit, the human's answer resets it through `unblock` and `CommentHandler`, a rework move and a stall keep it. Steps 3 and 5 of `handle` change when `at_crash_cap(<the crashed state>, definition.crash_cap)` (`factory.pipeline.domain.recovery`, true when `crashes >= crash_cap`) holds:

- Record: the new state is `asking_crash_cap(<the crashed state>)` (`blocked` = `"crash_cap"`, the rest as it was) and the `crash` entry is followed by a `question` entry by `factory` with `crash_cap_question(stage, crashes, crash_cap)` (`factory.hosting.domain.post_texts`), in the same commit.
- Rerun is skipped. After the push `handle` calls `ask_crash_cap(<the snapshot with the new document and the pushed commit>)` and returns without calling `run`.
- `ask_crash_cap(work_item)` raises `CannotHandle` when `blocked` is not `"crash_cap"` or when there is no `question` record by `factory` (`last_record`). Otherwise it posts through `StopService.post` a `WorkItemStop` keyed `PostKey(kind="crash_cap", n=<the record's number>)`, titled `<id>: <story title>` (`<id>` alone without a title), with the text `factory: <entry_text>`. That is the body and key `AskHandler` posts for a recorded question, so a repeat, or a repost after a kill, is a no-op (`StopPosted.outcome` is `"already_posted"`). When the post opened a pull request, `ask_crash_cap` checks the work item's branch out, sets `state.pull_request` and pushes one more commit (`pull request opened`); a push that is not `pushed` raises `PushFailed`.
- `HostingServiceError` from the post propagates; the question stays recorded and pushed (recording comes before posting).
- A boundary error after a pushed claim leaves the claim; the next tick raises `crash` and this handler records it like any crash. An error that repeats reaches the cap as the second crash, so the error cap of the dispatcher does not apply.

**The pull request is read before every agent run.** `RunGate(boundaries, run, closed, merged)` (`factory.pipeline.application.handlers.run_gate`) is the registered `run` handler. A stage can be due for a work item whose pull request the human has meanwhile closed or merged, and the human's act comes first, so the gate looks before the agent is started. With no pull request in the work item's state (`target_of(event).pull_request` is `None`) it calls `run.handle(event)` unchanged and reads nothing. Otherwise it calls `HostingService.get_pull_request` once, before any handler, and passes on the event copied with `pull_request` set to the view read: a `closed` view goes to `closed.handle` with the kind `closed`, a `merged` view to `merged.handle` with the kind `merged`, an `open` view to `run.handle` with the kind unchanged. A failing read raises (`HostingServiceError`) and no handler is called; it is a counted error of the dispatcher. The gate calls its handlers directly and does not re-dispatch, so it knows no registry. The `run`, `closed` and `merged` properties return the three handlers. Every path to an agent run goes through the gate, the rerun after a crash included: a story whose head branch the hosting service deleted reads as fresh, and the gate is the only place that notices its closed pull request. Tests: `tests/pipeline/application/handlers/test_run_gate.py`, `tests/entry/test_wiring_human_handlers.py`.

`RunHandler(boundaries, instance, definition, environment)` (`factory.pipeline.application.handlers.run`) turns a `run` event into one stage: it builds `StageRunner(boundaries, instance, definition, environment)` and calls `run(work_item.id, work_item.path)`. Any other kind is a `ValueError`. The `StageReport` is dropped, because a stall is already recorded by the stage; whatever `StageRunner.run` raises (a `HostingServiceError`, for example) propagates and is a counted error of the dispatcher. The handler adds nothing to the environment and takes nothing from it.

### Asking the human

`AskHandler(boundaries, definition)` (`factory.pipeline.application.handlers.questions`) handles `ask`. A question is recorded before it is posted, and every post carries `PostKey(work_item, <the blocked value>, str(<the question record's number>))`. The handler never checks whether it already posted: `HostingService.post_comment` treats a key the pull request holds as a no-op, so a repeat or a restart posts nothing twice.

- `handle` takes `target_of(event)` and `require_pull_request(target, "ask")` (no pull request: `CannotHandle`).
- `blocked` set: the question is the latest `question` record (`last_record`), whatever records follow it (the human's comments are recorded after a question that waits to be posted). The text is `<speaker>: <entry_text>`. No commit is made. A `blocked` value with no `question` record is `CannotHandle`. This covers the agent's question, `round_cap`, `send_back` and `crash_cap`, which other code records.
- `blocked` unset and `attempts >= definition.attempts_cap`: the handler records, then posts. It checks out the branch with `WorkItemRecorder`, takes the text of the latest `stall` entry (none: `CannotHandle`, nothing recorded), appends a `factory` `question` entry with `attempts_cap_question(stage, attempts, last_stall)` (`factory.hosting.domain.post_texts`), sets `blocked="attempts_cap"` and records with the subject `work item <id>: attempts cap question recorded`. Then it posts the new entry with kind `attempts_cap`.
- `blocked` unset below the cap: `CannotHandle`.
- Failures (`HostingServiceError`, `GitError`, `PushFailed`) propagate; a recorded entry stays recorded, and the next attempt posts it without a second entry.

`question_posted` compares the post's `n` with the number of the latest `question` record, so a comment recorded after the question does not raise `ask` again. Tests: `tests/pipeline/application/handlers/test_questions.py`, `tests/hosting/domain/test_question_post_texts.py`.

### Recording the human's act

A handler that answers an act of the human on a pull request first records the act in the work item's branch and pushes it, and only then posts, reopens or checks out anything else. If the factory dies after the push, the act is already in the journal and the next tick does not repeat it. `factory.pipeline.application.handlers.recording` holds what the handlers share:

- `target_of(event)` returns `Target(snapshot, state, pull_request)` for the event's work item. It raises `CannotHandle` (kind: the event's) for an event with no work item (`the event names no work item`) and for a work item whose document has no state (`work item <id> has no state`). `require_pull_request(target, kind)` returns the pull request number, or raises `CannotHandle` of `kind` (`work item <id> has no pull request`).
- `commit_subject(work_item, text)` gives `work item <id>: <text>`. Every commit the factory makes on a work item's branch begins `work item <id>: `: a stage's start, its end, a stall, an acceptance's opening and the handlers' records. The one exception is the merge of `origin/main` into a reopened branch, which keeps git's own subject. A project's `make mutants` reads the prefix to find the modules a feature changed.
- `WorkItemRecorder(boundaries)` does the git work. `check_out(branch)` resets to `HEAD`, switches to the branch at `origin/<branch>` and resets to it, so whatever a killed handler left (uncommitted changes, untracked files, an unpushed commit) is gone. It does not fetch: the caller must have fetched, as the tick does. `read` and `write` use the work item reader and writer on a path in the checkout. `publish(branch, subject)` commits and pushes through `push_with_retries` (a server refusal or an unreachable remote is pushed again after 5, 15 and 45 s, see *The pipeline definition and the stages*), and raises `PushFailed` with git's reason for any outcome but `pushed`. `delete_branch(branch)` calls `Git.delete_remote_branch` (a branch already gone counts as `"pushed"`; any other outcome raises `PushFailed(branch, outcome)`) and then `Git.delete_branch`; the merged and closed handlers share it. `record(branch, path, document, subject)` is `write` then `publish`.

### The merge archives the story

`MergedHandler(boundaries)` (`factory.pipeline.application.handlers.merged`) handles `merged`; it is registered for `merged` and is also the merged handler of the run gate. It does what `docs/operator-guide/work-items.md` says under "A merge archives the story", in this order:

1. `target_of(event)`, then `WorkItemRecorder.check_out(MAIN_BRANCH)`: it works on the remote's main, not on the work item's branch.
2. It reads the story at `snapshot.path` and appends `NewEntry(FACTORY, "done", done_entry_text(bill(records)))`. The records are `cost_reader.read(cost_records_path(path))`; a missing file gives none. `done_entry_text(bill)` is in `factory.hosting.domain.post_texts`: `done (pull request merged); cost: ` and `cost_line(bill)`.
3. It sets `stage` to `DONE_STAGE`, `blocked` and `claim` to `None`. The claim is dropped in the state and not through `ClaimService.release`, which needs an instance name and a pipeline definition the handler does not hold.
4. `Git.move` of the story to `destination_path(path, "done")`, and of its cost record file when `show_file("HEAD", ...)` finds one. The sidecar's destination is `cost_records_path(<the story's destination>)`, because `folder_of` knows only `.md` work item files.
5. It writes the document at the new path and publishes on main with `commit_subject(id, "merged, archived")`; a push that is not `pushed` raises `PushFailed`.
6. Only then `Git.delete_remote_branch(branch)`, which counts a branch already gone as `"pushed"`; any other outcome raises `PushFailed(branch, outcome)` and the archive stays pushed. Then `Git.delete_branch(branch)`.

It posts nothing and does not touch the pull request. `destination_path(path, folder)` (`factory.work.domain.archive`) returns the same file name in `folder` of the same feature directory, and raises `ValueError` for a path that `folder_of` places in no lifecycle folder; the discard below reuses it. Tests: `tests/pipeline/application/handlers/test_merged.py`, `tests/work/domain/test_archive.py`, `tests/watching/domain/test_archive_texts.py`.

### A close before the approval discards the story

`ClosedHandler(boundaries, definition)` (`factory.pipeline.application.handlers.closed`) handles `closed`; it is registered for `closed` and is also the closed handler of the run gate. It does what `docs/operator-guide/work-items.md` says under "A close before the approval discards the story":

1. `target_of(event)`. When `definition.stages[stage].approval` is true the handler sends the story back instead (see "A close at the approval sends the story back") and does not discard it.
2. `WorkItemRecorder.check_out(MAIN_BRANCH)`, then `Git.move` of the story to `destination_path(path, "backlog")`. The file is moved and not rewritten, so its text is main's, the human's.
3. `publish(MAIN_BRANCH, commit_subject(id, "closed before the approval, back in the backlog"))`; a push that is not `pushed` raises `PushFailed` and the branch is kept.
4. Only then `WorkItemRecorder.delete_branch(branch)`. The branch's cost records go with it, so a later start has an empty bill.

It makes no hosting-service call. Tests: `tests/pipeline/application/handlers/test_closed.py`.

### A close at the approval sends the story back

`ClosedHandler._send_back(target)` handles a `closed` event at a stage whose `approval` is true; `docs/operator-guide/work-items.md` says what the operator sees under "A close at the approval sends the story back". The rules are pure functions in `factory.work.domain.send_back`:

- `send_back_target(definition, approval)` is `next[1]` of the approval, or `None` when `next` has fewer than two stages. `None` is `CannotHandle("closed", ...)` before anything is written.
- `send_back_cap(definition, approval)` is the `round_cap` of the first stage whose `next[0]` is the approval and that has a cap, or `None`.
- `recorded_since_latest_result(document, kind)` is true when a record of `kind` is numbered after the latest `result` record (any record of the kind, when there is no result). `reason_given(document)` is that test for `comment`.

The reason is judged from records, never from text (see "No code reads data from the journal's text"): the human gave a reason when a `comment` record follows the latest `result`.

The order is fixed, and each step that changes the work item is pushed on its own, so a kill leaves a state the next attempt finishes:

1. Record the close, on the branch: `CommentCopier.unread` and `append` copy the unread comments, a `human` entry of kind `close` is added unless `recorded_since_latest_result(document, "close")` already holds, and `handed_over` is cleared. Commit subject `close recorded`; nothing is committed when the document is unchanged.
2. `HostingService.reopen`, then `set_draft(number, True)`.
3. Record the decision: a `send_back` entry (`send_back_entry_text(stage, round)`), and, when `send_back_question(round, cap, reason_given(closed))` returns a text, a `question` entry and `blocked = "send_back"`. The state gets `stage` = the target, `round` + 1 and `claim = None` (not through `ClaimService.release`, which needs an instance name). Subject `sent back`.
4. `set_labels(number, labels_for(state))` last; a failing call raises and the decision stays recorded.

The handler posts nothing; `AskHandler` posts the question. Tests: `tests/pipeline/application/handlers/test_closed_send_back.py`, `tests/work/domain/test_send_back.py`, `tests/hosting/domain/test_send_back_texts.py`.

### A comment can end a wait

`CommentHandler(boundaries)` (`factory.pipeline.application.handlers.comments`) handles `comment`. It takes `target_of(event)` and `require_pull_request(target, "comment")`, then copies with `CommentCopier.copy`:

- `blocked` unset: the comments are only copied.
- `blocked` set: `copy` gets an `adjust` function, so the answer lands in the same commit as the copied comments. `adjust` finds the factory's post of the wait, the comment listed with `by_factory` and the key `PostKey(work_item, <the blocked value>, str(<number of the latest question record>))`. It applies `unblock` when a comment of this copy has a non-blank body and an id greater than the post's. With no such post (not posted yet, or only an earlier question's) or no such comment, the document is unchanged and the wait stays.
- `unblock(state)` (`factory.work.domain.answers`) sets `blocked` to `None`, resets `attempts` to 0 when the wait was `attempts_cap` `crashes` to 0 when it was `crash_cap` and `round` to 0 when it was `round_cap`, so an answer at the round cap starts the count of rounds over (the count also holds the approval's send-backs). For any other wait, `send_back` included, it keeps `round`, so a later send-back past the cap asks again. A state that does not wait is returned as it is.

The answer is read from ids and keys, never from the comment's text. Tests: `tests/pipeline/application/handlers/test_comment_handler.py`, `tests/work/domain/test_answers.py`.

### The hand-over at the approval

`HandOverHandler(boundaries, definition)` (`factory.pipeline.application.handlers.hand_over`) handles `hand_over`. It takes `target_of(event)` and `require_pull_request`, checks out the branch and reads the work item. A stage that is not an approval is `CannotHandle("hand_over", ...)`. A work item whose `handed_over` already equals its stage returns at once. Otherwise, in this order:

1. `HostingService.set_description` with `hand_over_description(document, commits)` (`factory.hosting.domain.hand_over`): the sections Description and Acceptance criteria (`section_text` of the body), the reports Tests, Review, Documentation and Smoke test (`REPORT_SECTIONS`: the latest `result` record of `tester`, `reviewer`, `documenter` and `smoke-tester`), Commits (a fenced block of the first seven characters of each id and the subject, from `Git.log` of `origin/<branch>` since `origin/main`) and `HAND_OVER_CLOSING`. A missing or empty section, and a report with no `result` record, read `none`. The reports are found by `last_record(speaker=..., kind="result")`, so the speaker comes from the record and not from the visible line; `entry_text` is read only here, which is why the module is on the list in "No code reads data from the journal's text".
2. `set_draft(number, False)`.
3. `post_comment` of `cost_table_post(cost_table(bills_by_stage(records)))`, read from the cost records file on the branch, with the key `PostKey(work_item, "cost_table", str(<number of the latest result record>))`, or `"0"` with no result.
4. Record `handed_over = <stage>` with the subject `handed over at <stage>`.

The description is already in place when the hand-over runs: the stage that reached the approval wrote it between its result commit and its push (see `StageFinisher.finish`). Step 1 writes it again with the same text, since it reads the same document and commits; the hand-over stays the place that marks the pull request ready, posts the cost table and records `handed_over`. If the stage's own write failed, step 1 is the first write.

The first three effects are safe to repeat, so a failure or a kill anywhere before the record is retried whole; the record comes last. Tests: `tests/pipeline/application/handlers/test_hand_over.py`, `tests/work/domain/test_hand_over.py`.

### An illegal stage change is put back

`RejectHandler(boundaries)` (`factory.pipeline.application.handlers.reject`) handles `reject`; it is registered for `reject`. It puts the stage back with a commit whose subject contains `moved back` (`MOVED_BACK_MARKER`, `factory.hosting.domain.post_texts`), and the journal gains a `move_back` entry. That entry is what exempts the correction from the move rule: the next evaluation sees a `StageChange` with `correction` true and does not reject it. `docs/operator-guide/work-items.md` says what the operator sees.

1. `target_of(event)`, then `WorkItemRecorder.check_out(snapshot.branch)`.
2. The change is taken from the same source as the watcher's: `RemoteWorkItems(git, work_item_reader).last_stage_change(snapshot)`, the newest commit beyond `origin/main` that touched the work item's file, whatever later commits touched other files. `None` (no change, a merge commit, a parent without the file or with an unreadable one) and a change that is itself a correction raise `CannotHandle("reject", ...)` before anything is posted or written.
3. With a pull request, `correction_note(from, to)` is posted first, keyed `PostKey(kind="correction", n=len(journal) + 1)`, the number the new entry will get. A kill after the post, or before the push, leaves one note, and the next run adds one entry.
4. The recorded state has `stage` set to `from_stage`, `claim` set to `None` directly in the state (not through `ClaimService.release`, which needs an instance and a definition the handler does not hold) and one `factory` entry of kind `move_back` with `move_back_entry_text(from, to)`.
5. With a pull request, after the push `set_labels(number, labels_for(<recorded state>))`. A failing call raises; the correction stays on the branch.

Only the work item's branch is written: `main` is never checked out, written or pushed, so a killed correction cannot leave it dirty. Tests: `tests/pipeline/application/handlers/test_reject.py`, `tests/hosting/domain/test_correction_texts.py`.

### A stop with no work to do is an error

A handler that cannot do its work raises `CannotHandle` and never reports success: returning quietly would hide the stop from the human. The dispatcher counts the error, retries up to `ERROR_CAP` (3) times on the same remote state and then reports once, keyed `PostKey(kind="error", n=<first 12 digits of the remote state>)`.

`DuplicateHandler()` and `PullRequestLookupHandler()` (`factory.pipeline.application.handlers.lookups`) take no boundary and always raise: `CannotHandle("duplicate", "two work items share the id <id>")` and `CannotHandle("pull_request_lookup", "the pull request lookup for <branch> failed")`, each followed by `: <event.detail>` when the detail is not empty. Both are registered. `AskHandler` without a pull request is the third such stop (`require_pull_request`).

No module under `factory.pipeline.application.handlers` catches `Exception` or `BaseException` or has a bare `except`; `tests/pipeline/application/handlers/test_handlers_raise.py` walks the package and checks it. Tests of the dispatch sequence (`error, error, reported, capped`): `tests/pipeline/application/handlers/test_lookups.py`.

### Comments are copied by id

`CommentCopier(boundaries)` (`factory.pipeline.application.handlers.comments`) copies the human's comments on a pull request into the journal.

- Only the marker tells the factory's comments from the human's: `unread(state, pull_request)` lists the comments, drops those with `by_factory` and those whose id is in `state.comments_read`, and keeps the listed order. The author is never looked at, and a body starting with `factory:` counts as the human's.
- Comments are tracked by id, never by count, so a factory post in between, or a deleted comment, neither hides nor repeats another one.
- `append(document, comments)` adds, for each comment with a non-blank body, a `human` entry of kind `comment`, dated with `created_at` in UTC; `\r\n` in the body becomes `\n`, and the edges are stripped as for any entry. A blank comment gets no entry. Every given id joins `comments_read`, which stays sorted without repeats.
- `copy(snapshot, pull_request, adjust=None)` checks out the branch, reads the work item, appends the unread comments and records them with the subject `work item <id>: comments from the pull request`. It returns `CopyResult(recorded, commit)`: the new ids and the pushed commit, or `([], None)` with nothing written when nothing was unread. `adjust(document, comments)`, when given, changes the appended document and lands in the same commit; it is not called when nothing is unread. A push that fails raises `PushFailed`, and the next `copy` records the same comments once. A work item without a state raises `ValueError`; callers pass `target_of` first, which refuses it with `CannotHandle`.

The comment handler and the send-back use `CommentCopier`.

The agent run's environment is made by `agent_environment(scripts, home, path)`: exactly `PATH` = `<scripts>:<path>` and `HOME` = `str(home)`, where `path` is the `PATH` of the image in use (`SYSTEM_PATH`, `/usr/local/bin:/usr/bin:/bin`, by default). `production_environment(path)` calls it with the directory of `sys.executable` (where the console scripts are installed) and `Path.home()`. The result goes through `scrub_environment(source)` (`factory.agents.domain.agent_runs`), which keeps only the names in `ALLOWED_ENVIRONMENT_NAMES` (`PATH`, `HOME`, `LANG`, `LC_ALL`, `TERM`, `TZ`, compared as written): `production_environment()` is `scrub_environment({**os.environ, **agent_environment(...)})`, so `LANG`, `LC_ALL`, `TERM` and `TZ` pass when the process has them and no token or other variable does. The scrub happens once, at this source. `TaskComposer` hands the mapping it is given unchanged to `AgentRunRequest.environment`, `ClaudeCodeRuntime` runs the agent with `request.environment` minus any `CLAUDE_CODE_OAUTH_TOKEN` entry, plus its `SWITCHES`, plus the token its login shell reads from `login_file` (so `ALLOWED_ENVIRONMENT_NAMES` keeps its six names), and nothing of the process's own environment, and `AgentRunRequest(` is built in `factory.pipeline.application.task` (and the preflight's probe); `tests/guards/test_agent_run_request_search.py` searches for both and for `os.environ` in the inner layers and the runtime.

`token_file_item(path, *, uid, stat)` (`factory.machine.application.preflight`) is the preflight item `token-file`: it passes when the file exists and its folder belongs to `uid` with `mode & 0o077 == 0`; the file's own owner and mode do not count. It reads only through `stat`: `path.parent` first, then `path` only when the folder passes. `machine_extras` in `factory.entry.wiring` gives it to `build_tick`'s preflight. The credential helper is `vm/git-credential-factory` (POSIX `sh`), installed at `/usr/local/bin/git-credential-factory`; `docs/operator-guide/health.md`, "The hosting-service token", describes it, the mounted file and the rules `tests/vm/test_git_credential_helper.py` enforces.

The preflight probes the `PATH` for the tools in `REQUIRED_TOOLS`, and `build_boundaries` builds every adapter from the instance settings.

`Preflight._clear_stale_failing_stop` clears a `main_branch_failing` stop when the stamp's `main_failed` is no longer `origin/main`, unless `changes_only_stop_records(paths)` (`factory.machine.domain.preflight`) holds for `git.changed_paths(stamp.main_failed)`: true when the list is not empty and every `ChangedPath` is `STOP_RECORDS_FILE`, whatever its change. Then the stop stays and no `cleared` record or log line is written. A `GitError` from `changed_paths` (the commit is not in the clone) counts as a change and clears the stop. `changed_paths` compares with the work tree, which the tick's restore leaves at `origin/main`.

## Stops, the clock and the factory log

`factory.pipeline.domain.stops` holds `RepositoryStop` (scope, reason, detail, `at`) and `HealthStatus` (`stops`, `healthy`); both are frozen and refuse unknown fields. The rules (blank detail, scope against reason, naive `at`, one stop per reason) are in the formats of `docs/operator-guide/health.md` (*The factory log and the health status file*) and are `ValidationError`s. `at` is typed `UtcDatetime` and so is converted to UTC.

`factory.watching.application.machine` holds the abstract `Clock` (`now()`, aware and UTC), `FactoryLog` (`line(text)`) and `HealthStatusStore` (`read()`, `write(status)`) and `DiskSpace` (`free_bytes(path)`, `used_bytes(path)`). Their first implementations are `SystemClock` and `ManualClock(start)` (tests; `advance(by)`; a naive start is a `ValueError`) in `factory.shared.adapters.clock`, `TimestampedFactoryLog(path, clock)` in `factory.watching.adapters.factory_log` `JsonHealthStatusFile(path)` in `factory.watching.adapters.health_file` and `ShutilDiskSpace()` in `factory.machine.adapters.disk_space` (`free_bytes` is `shutil.disk_usage(path).free`; `used_bytes` sums the regular files under a path without following links, 0 for a missing path; `Boundaries.disk` is `ShutilDiskSpace()` from `build_boundaries`). Both JSON stores (and `JsonPreflightStampFile`) replace their file through `replace_text(path, text)` in `factory.shared.adapters.atomic_file`; `tests/guards/test_atomic_replace_search.py` checks that `os.replace` is called once in the package. In tests use the `clock` fixture (a `ManualClock` at 2026-10-12 12:00 UTC).

`factory-health` (`factory.entry.health`, `main(argv=None, *, store=None) -> int`) is the container's health check. It reads the health status from the health file of the state directory (`--state-directory <path>`, default the image's `/state`; on the VM the path is the `FACTORY_STATE` of the instance), or from the `HealthStatusStore` it is given. It prints `healthy` and returns 0, or prints one line per stop in force, `<reason> (<scope>): <detail> (since <at>)`, and returns 1. A missing health file prints `no health status: <path> is missing` and returns 1.

`factory-run` (`factory.entry.run.main(environ=None, *, runner=None, state_directory=STATE_DIRECTORY, clock=None)`) writes the stop of invalid settings (the log line `settings invalid: <variable>: <fault>` and the `preflight_failed` stop in `health.json`) to the directory `FACTORY_STATE` names (`named_state_directory` of `factory.shared.domain.settings`: stripped, non-blank, absolute), else to `state_directory`. A relative `FACTORY_STATE` is itself the fault, and its stop goes to `state_directory`. The same holds for a `SettingsInvalid` the runner raises after the settings were read, such as the unreadable token file.

`StopService(boundaries)` (`factory.pipeline.application.stops`) raises and clears the stops of the repository or the machine; those never reach a pull request. `post(stop)` is the other kind: it puts a `WorkItemStop` (`key`, `branch` equal to `branch_name(key.work_item)`, `title`, `pull_request` or `None`, `text`; `branch`, `title` and `text` not blank) on the work item's pull request and returns `StopPosted(pull_request, opened, outcome)`. See `docs/operator-guide/stops.md`, "The stops of one work item", and the decision log for the rules. `raise_stop(stop)` writes the line `stop <scope> <reason>: <detail>` through `boundaries.log`, then writes the health status with the stop in it (a known reason is replaced where it stood, a new one appended). Each write is tried even if the other fails, and the first `OSError` is raised afterwards, the log's when both fail. `clear_stop(reason)` does nothing when the status holds no stop of that reason; otherwise it writes the status without it first and then the line `stop cleared <reason>`, so a failed health write leaves the stop in force and says nothing. The replace-or-append rule is private to `stops.py`. `docs/operator-guide/health.md` describes the lines.

**Stop records.** `StopRecord` (`factory.pipeline.domain.stops`: `event` `raised` or `cleared`, `scope`, `reason`, `at`, `instance`; frozen, no unknown keys) is one event of a stop. It holds no detail. Its scope must match its reason by the same private function `RepositoryStop` uses. `stop_records_text(records)` gives one `model_dump_json()` line per record, and `parse_stop_records(text)` reads back the lines that validate and skips the others. `Boundaries.stop_records` (`RecordLog[StopRecord]`; `build_boundaries` sets a `JsonLinesRecordLog` at `<state directory>/records/stops.jsonl`) is where `StopService` appends: `raise_stop` appends a `raised` record when the health status it read held no stop of that reason (and none when the status cannot be read, so the records stay paired with the status), `clear_stop` appends a `cleared` record with the standing stop's scope. Each append is tried after the log line and the status like the other two, and its `OSError` is raised last.

`StopPublisher(boundaries).publish()` pushes the local records that `origin/main`'s `STOP_RECORDS_FILE` (`factory/stops.jsonl`) does not hold, compared as whole records, and returns them. It reads the file with `git.show_file` (missing is empty) and returns `[]` without a git operation when there is nothing to add. Otherwise it stands on `main` through `WorkItemRecorder.check_out`, appends the missing records once each in local order (adding a newline when the file does not end in one; lines that do not validate stay), and commits and pushes through `WorkItemRecorder.publish(MAIN_BRANCH, "stops recorded")`. It raises `GitError`, `PushFailed` or `OSError`; the local records stay, so the next call pushes them. Tests: `tests/pipeline/domain/test_stop_records.py`, `tests/pipeline/application/test_stop_records_service.py`, `test_stop_publisher.py`, `test_tick_stop_records.py`, `tests/entry/test_wiring_stop_records.py`.

`STOP_TABLE` in `factory.pipeline.domain.stop_table` is a tuple of `StopRow`s, one per stop, each with its v1 limits (`limits`), its `destination` (`health_status`, `pull_request` or `none`), its `reason` and the `test` that proves it. A row has a `reason` exactly when its destination is the health status. Each limit is the whole text `L` followed by ASCII digits, with nothing after it: `L7` is accepted; `L7x`, `L7 ` and `L7` followed by a newline are not, and neither is a digit outside ASCII. A refused row is a `pydantic.ValidationError`.

### Boundaries

`Boundaries` (`factory.pipeline.application.boundaries`) is the frozen dataclass of the interfaces that wiring hands to services: `git`, `hosting`, `agent_runtime`, `project_commands`, `work_item_reader`, `work_item_writer`, `cost_reader`, `cost_writer`, `pipeline_reader`, `agent_definitions`, `clock`, `log`, `health`, `checkout` (the checkout root, a `Path`), `settings` (below), `disk` (the `DiskSpace` of the disk check, see the tick's step 0), `disk_records` (the log of the disk records, see the paragraph on `DiskRecord` after `RecordLog`), `stop_records` (the log of the stop records, see "Stop records" under "Stops, the clock and the factory log"), `waiter` (a `Waiter`; `build_boundaries` gives `SleepingWaiter()`; see *Starting a stage*) and `result_records` (the log of the known results, see `machine.md`, *Known results*). `snapshots` (a `Snapshots`) and `containers` (a `ContainerRuns`) follow them. These eight, `settings` to `containers`, are required: none has a default or admits `None`, and a `Boundaries(...)` without one is a `TypeError`, so a construction that drops one does not type-check or run. `build_boundaries` sets all eight. It is not a DTO. It takes keyword arguments only, so a positional call is a `TypeError`, and assigning to a field raises `FrozenInstanceError`. `snapshots` and `containers` hold the dataset's and the containers' interfaces, and `stage_environment_of` gives the one `ContainerEnvironment` on them (see `machine.md`, *The container environment*). `build_boundaries` fills them with `ZfsSnapshots` and `PodmanRuns` (see `machine.md`, *The settings and the wiring*), and refuses an instance without a dataset, a workspace or a stage image before it builds anything; the `boundaries` fixture holds the fakes of the container environment. A later story that needs another interface adds a field. `factory.entry.wiring.build_boundaries` builds the concrete adapters. Its `project_commands` is `RecordingProjectCommands` around `ContainerMakeCommands` (see `machine.md`, *Container project commands*).

`Boundaries.settings` (`InstanceSettings`) is the one place the services read the instance's settings from (the image identity, the instance's name, the provider limit); `build_boundaries` fills it.

`build_boundaries(settings, token, *, hosting=None)` (`factory.entry.wiring`) is the one place that picks the concrete adapters. It resolves the hosting service first, so a URL with no `owner/name` fails (`SettingsInvalid`, `FACTORY_REPOSITORY_URL`) before any adapter exists: `hosting` when given (tests pass `FakeHostingService`), otherwise `pygithub_service(repository_name(settings.repository_url), token)` from `factory.hosting.adapters.pygithub_hosting`, which builds the PyGithub client lazily (no network call). It builds `GitCli(settings.checkout, git_options(settings))`; `ClaudeCodeRuntime(settings.claude_executable, <state directory>/runs, login_file=settings.claude_login_file, ...)`; `MakeProjectCommands(settings.checkout)`; the work item reader and writer, the cost record reader and writer and the pipeline reader; `FrontmatterAgentDefinitionReader(settings.agent_home)`, built once; one `SystemClock` shared by the clock and `TimestampedFactoryLog(<state directory>/factory.log)`; `JsonHealthStatusFile(<state directory>/health.json)`; and `checkout` and `settings`. It writes nothing. The token comes from `read_hosting_token(settings.token_file)`, which calls `read_setting_file(variable, path, read_file)` (`factory.shared.domain.settings`, the one reader of a setting's file, also used for the image identity; the reader is passed in so the domain does no I/O).

`git_options(settings)` gives `GitOptions(identity=settings.git_identity, environment=git_environment())`. `git_environment()` returns exactly seven entries, `GIT_CONFIG_COUNT=3`, `credential.helper` = `CREDENTIAL_HELPER`, `core.hooksPath` = the null device (the factory's git runs no hooks) and `core.fsmonitor` = `false` (a child git started for a nested repository inherits the pairs, so that repository's `core.fsmonitor` never runs), as `GIT_CONFIG_KEY_n`/`GIT_CONFIG_VALUE_n`. There is no `core.sharedRepository`: the shared group went with the second user.

**Agent runs.** `agent_runtime.run` is called in `factory.machine.application` by the stage environment's `run_agent` (`machine.md`), which returns the run's result as the runtime gave it, and by `PatientRuns`, which `StageLauncher.launch` passes as `run` and which waits out the provider's spend limit around the call. The factory seals nothing before a run and checks nothing after it: it does not look at the checkout's git folder, a repository nested in the work tree or the ignored paths. Tests: `tests/pipeline/application/test_stage_nested_repository.py`, `tests/pipeline/application/test_dispatcher_counts_every_error.py`.

`CheckoutPreparer(git, settings).prepare()` (`factory.pipeline.application.scheduler`) returns nothing and raises `GitError` as before. When `checkout/.git` does not exist in any form (`os.path.lexists`) it clones; otherwise it does nothing: no check, no clone again, whatever the `.git` holds. A folder with files and no `.git` is still refused by the clone. It takes no log. Tests: `tests/hosting/application/test_checkout_preparer.py`.

`repository_name(url)` uses one full-match regular expression for the three URL forms and drops a trailing `.git` and `/`. `InstanceSettings` has the fields `agent_home`, `claude_executable`, `token_file` and `claude_login_file` (`FACTORY_CLAUDE_LOGIN_FILE`, `None` when blank) and `api_login_file` (`API_LOGIN_FILE_VARIABLE`, `FACTORY_API_LOGIN_FILE`, `None` when blank), with the variables and defaults of the settings table in `docs/operator-guide/install.md`. Two of the settings have no default: `FACTORY_CLAUDE_HOME` (`agent_home`) and, when `read_settings` is given a reader, `FACTORY_IMAGE_ID_FILE` (`image`) are required and absolute, and `read_settings` refuses a missing, blank or relative value with `SettingsInvalid` naming the variable. The model refuses the same faults itself: `agent_home` has no default and, like `checkout` and `state_directory`, must be absolute (`is not an absolute path`). `container_env` (`FACTORY_CONTAINER_ENV`) is checked name by name, in order, by `container_env_fault(names)` (`factory.shared.domain.settings`), which both the model and `read_settings` call: `holds <name>, which is not a variable name`, `holds <name>, which the factory sets itself` (a name in `RESERVED_CONTAINER_NAMES` or beginning with `RESERVED_CONTAINER_PREFIX`) and `names <name> twice`. The reading raises them as `SettingsInvalid` naming `FACTORY_CONTAINER_ENV`; a model built in code raises `ValidationError`.

In tests use the `boundaries` fixture in `tests/conftest.py`: the real git wrapper, project commands, readers, writers, `TimestampedFactoryLog` at `<tmp_path>/state/factory.log` and `JsonHealthStatusFile` at `<tmp_path>/state/health.json`, with the fakes for the hosting service and the agent runtime and the `clock` fixture. It also sets the six required fields: `settings` (an `InstanceSettings` for `instance` `factory-1`, with the state directory `<tmp_path>/state`), `disk` (a `FakeDiskSpace` with ample room: `10**12` bytes free and 1 used in `<tmp_path>` and in the state directory), `disk_records`, `stop_records` and `result_records` (`JsonLinesRecordLog`s at `<tmp_path>/state/records/disk.jsonl`, `stops.jsonl` and `known-results.jsonl`) and `waiter` (a `ManualWaiter` on the `clock` fixture). A test that needs one of those features off replaces its collaborator with one of its own, never with `None`. A test that needs other parts uses `dataclasses.replace(boundaries, health=...)` and never calls `Boundaries(...)`, so a story that adds a required field changes only the fixture. Only the test of the keyword-only rule calls it directly, through a variable typed `Callable[..., Boundaries]` (a positional call is a `mypy --strict` error); the test of the frozen rule assigns with `setattr` and the field's name in a variable. An unwritable destination is a `JsonHealthStatusFile` or `TimestampedFactoryLog` whose path lies below a regular file; read standard output with `capsys`.

### The idle shutdown

`IdleShutdown(limit, clock, power, log)` (`factory.pipeline.application.idle_shutdown`) powers the machine off after an idle stretch; the setting `FACTORY_IDLE_SHUTDOWN_MINUTES` (`InstanceSettings.idle_shutdown_minutes`, a `NonNegativeInt`, `0` off) turns it on. `PowerOff` (`factory.watching.application.machine`, abstract) has one operation, `power_off()`, which raises `PowerOffError` when the machine cannot be asked or refuses. `SystemctlPowerOff` (`factory.machine.adapters.power_off`, a wrapper of R5) is its implementation: it runs `sudo -n /usr/bin/systemctl poweroff` without a shell through `factory.shared.adapters.process`, under a time limit of one minute (`POWER_OFF_TIME_LIMIT`), and builds its `PowerOffError` detail with `failure_detail` and `no_end_detail` of `factory.shared.adapters.printed_output`, or `cannot start <sudo>: <error>`.

`ProcessExit(request_stop)` (`factory.machine.adapters.power_off`) is the second implementation of `PowerOff`: `power_off()` calls `request_stop` once and raises nothing. The setting `FACTORY_IDLE_SHUTDOWN_ACTION` (`InstanceSettings.idle_shutdown_action`, `"poweroff"` by default or `"exit"`; anything else is `SettingsInvalid` with `is neither poweroff nor exit`) picks between the two.

`factory.entry.wiring.idle_shutdown_of(settings, boundaries, request_stop=None)` gives `None` for `0`, else the `IdleShutdown` with `SystemctlPowerOff()` for `poweroff` or `ProcessExit(request_stop)` for `exit` (without a `request_stop`, `ValueError`), `boundaries.clock` and `boundaries.log`. `run_instance(..., request_stop=None)` hands its `request_stop` on, and `run_until_stopped` passes its event's `set`, so the idle shutdown and the signal handlers stop the same loop and `main` returns 0 as after a `SIGTERM`. `run_instance` builds it once and hands it to `activity_tick(tick, idle)`, which runs the tick, gives the outcome to `idle.observe` and returns `activity(outcome)` as before, so the loop's pauses do not change.

`MachineStopExit(health, clock, log, request_stop)` (`factory.machine.application.machine_stop_exit`) ends the loop in a job when a machine stop stands: `observe()` reads the stops of scope `machine` from the health status, keeps for each reason the earliest `at` of an unbroken stretch (the preflight raises a stop again every tick with a new `at`), and when one has stood `MACHINE_STOP_LIMIT` (ten minutes, exactly is enough) logs `machine stop: standing for 10 minutes in a job, ending the factory's process: <reason>: <detail>` once and calls `request_stop`. `machine_stop_exit_of(settings, boundaries, request_stop)` gives `None` unless the idle shutdown is on (minutes above 0) with `exit`. `run_instance` wraps the prepare and tick callbacks with `_observed_iteration`, so it observes after each tick and after a `prepare` that left no tick, and raises `MachineStopStood` (`factory.shared.domain.errors`) after the scheduler ended on it; `main` returns 1 for it.

The rules of the stretch, in `observe(outcome)`:

- An outcome is idle when `stopped is None`, its event is of kind `idle` and `dispatch == "handled"`. Any other outcome starts a new stretch at `clock.now()` and does nothing else. An iteration that ran no tick calls `observe` not at all.
- The first stretch starts when the object is made. An idle outcome with `clock.now()` minus the start of at least `limit` (exactly the limit is enough) logs `idle shutdown: idle for <n> minutes, <action>`, calls `power.power_off()` once, and starts a new stretch.
- `<action>` is the constructor's `action` (default `powering the machine off`); `idle_shutdown_of` passes `ending the factory's process` with `exit` and nothing with `poweroff`.
- A `PowerOffError` is not raised: the log gets `idle shutdown: <error text>; the factory runs on`, and the new stretch starts as after a success.
- A `limit` of zero or less raises `ValueError`.
