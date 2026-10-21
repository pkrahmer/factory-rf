# The pipeline definition and the stages

This file covers the pipeline definition and a stage from the claim to the result commit; read the index, `README.md`, first.

## The claim service

`factory.application.claims.ClaimService(boundaries, instance, definition)` makes the first half of a claim: the stage-start commit. `instance` is the factory instance's name and must match `[a-z][a-z0-9-]*`, otherwise the constructor raises `ValueError`. `definition` is the `PipelineDefinition` the caller loaded (normally from `origin/main`); the lease is copied from it.

`claim(branch, path, document, stage)` returns a `StageStart(commit, claim)`. It does this, in order:

1. Checks the preconditions and writes nothing if one fails (`ValueError`): the document has a state; `stage` is the state's stage; `stage` is in the definition and has a role; `branch` is `branch_name` of the id in the file name of `path`, so a claim is made only on the work item's own branch; the checkout is on `branch`.
2. Builds the `Claim`: the instance's name, the stage, the start time from `boundaries.clock` (UTC) and the `lease_duration` of the stage's role, copied now. A claim already in the document is replaced.
3. Sets `state.claim` and appends one journal entry (speaker `factory`, kind `started`, text `started <stage> as <instance>.`, see `started_text`). Nothing else in the document changes.
4. Writes the work item at `boundaries.checkout / path` and commits with the subject `work item <id>: <stage> starts as <instance>`.
5. Pushes `branch`. Any outcome other than `"pushed"` raises `PushFailed`.

**The push is the claim.** Whoever pushes first owns the stage. A rejected or unreachable push is no claim: the remote is unchanged, and the caller starts no agent run. The local commit stays on the local branch; the next tick's restore brings the branch back to the remote. `InjectedKill` at `BEFORE_PUSH` is not caught.

**The stage-start commit is the last commit before the agent run.** The commit stages every change in the work tree, so whatever the caller left uncommitted is part of it; for a new branch that is the work item's opening. The commit is therefore the baseline for what the agent may write and for undoing it.

**Status.** `status(state)` returns a `ClaimStatus` (`factory.domain.lease`): `"none"` (no claim), `"own"` (the claim's `instance` is the service's, whatever its age, so a restarted instance with the same name reruns its stage at once, R20), `"held"` (another instance's claim, lease still running) or `"expired"` (another instance's, lease run out). It uses `boundaries.clock.now()` and the claim's own `lease_duration`, never the definition's, so a later change of the definition does not shorten a running claim (R21).

**Observed status.** `observed_status(state)` is `status` as a look from outside the instance's tick sees it (`observed_claim_status` in `factory.domain.lease`, with the same clock): an own claim within its lease is `"held"`, since the tick may be running its stage, and at and past its lease `"own"`; every other claim, and no claim, gets what `status` gives. Only `Watcher(..., observer=True)` (`factory-watch`) uses it; the tick uses `status`.

**The lease clock.** `lease_age(claim, now)` is `now - claim.started_at` (negative under clock skew); `lease_expired(claim, now)` is true when the age is at least `claim.lease_duration` minutes, and a negative age is never expired. Both are pure: `now` is passed in.

**Release.** `release(document)` returns the document with `state.claim` set to `None`, for the stage's result commit. Journal, other state fields and body are unchanged and no entry is appended. A document without a claim comes back equal; one without a state raises `ValueError`.

**`ClaimService` is the only module that builds or judges claims.** Only `factory.application.claims` imports `claim_status`, `lease_expired`, `lease_age` or `observed_claim_status`, and only it calls `Claim(...)`; `tests/test_claim_ownership.py` searches the source with `ast` and fails otherwise. Code that needs to know a claim's standing asks the service.

In tests, set the work item up on its branch before `claim` (a state, a journal entry and a `## Journal` section, or `append_entry` raises `WorkItemFormatError`); `put_work_item` and `created_state` in `tests/work_item_support.py` do it, and `tests/application/test_claims.py` uses them.

## The pipeline definition

The project's `factory/pipeline.yml` is read by `RuamelPipelineDefinitionReader.parse(text)` (`factory.adapters.pipeline_yaml`, the `PipelineDefinitionReader` interface in `factory.application.files`, `Boundaries.pipeline_reader`) into a `PipelineDefinition` (`factory.domain.pipeline_definition`). The reader is the only one of this format and nothing writes it. The text is loaded in ruamel.yaml's safe mode, so only plain data is built and a key repeated in one mapping is refused. `PIPELINE_YAML` in `tests/git_support.py` is the example definition.

| Key | Meaning | Default |
|---|---|---|
| `contract` | the contract version, a quoted text such as `'1.0'`; an unquoted `1.0` is a number and is refused | required |
| `stages` | name to `StageDefinition`; the order in the file is the pipeline's order | required |
| `roles` | name to `RoleDefinition`; a role's name is its agent definition's name | required |
| `project_commands` | name to `ProjectCommandDefinition` | `check`, `lint` and `test`, each with `time_limit` 10 |
| `attempts_cap` | attempts before the human is asked | 2 |
| `crash_cap` | crashes before the human is asked | 2 |
| `acceptance_stage` | the stage of the feature acceptance | none |
| `tool_paths` | folders every role's agent run writes besides its write paths (the project's tool state); each is `<folder>/*` in the checkout or `~/<folder>/*` in the agent's home | `[]` |

A stage has `role` (none: no agent runs there), `next` (`next[0]` is the forward move), `approval` (the human decides), `checks` (project commands run after the agent), `reports` (project commands run after green, recorded only) and `round_cap` (none: no cap). A role has `write_paths` (required; `{work_item}` is the work item's own file and `{feature}` its feature directory, the constants `WORK_ITEM_PLACEHOLDER` and `FEATURE_PLACEHOLDER`), `lease_duration` (60 minutes) and `time_limit` (40 minutes, the agent run's). A project command has `time_limit` (10 minutes). Every limit is a positive integer; stage, role and command names match `^[a-z][a-z0-9-]*$`.

- Values are taken only in their YAML type (strict mode): a limit is a YAML integer, so `true`, `'30'` and `30.0` are refused; `approval` is `true` or `false`, so `'yes'`, `'off'`, `1` and `0` are refused; names, `contract`, `checks`, `reports` and write paths are strings. A write path must hold at least one character that is not whitespace (`''` and `'  '` are refused at `roles.<role>.write_paths[<n>]`, with pydantic's message `String should match pattern '\S'`).
- A key with a default may be left out and takes it. A stage with nothing to say is written `done: {}`; `done:` alone is null and is refused (`invalid stages.done: ...`).
- Unknown keys are refused at every level, so a misspelt key is never ignored.
- A given `project_commands` replaces the default set as a whole; it does not merge. `lint: {}` takes `time_limit` 10.
- `ProjectCommandDefinition` has `time_limit` and `not_read`: a list of write-path patterns (`matches_any`) for the paths the command does not read, default `[]` (nothing left out). A pattern must be relative, non-empty, hold no `..` segment, not start with `~` and hold no `{` or `}` (a placeholder is expanded in write paths only). Otherwise the load fails, with the last rule of the definition, one fault per pattern: `project command <name>: not_read <pattern> must be a path pattern inside the checkout`. `is_inside_checkout` lives in `factory.domain.pipeline_definition`; `write_paths` and `confinement` import it. `KnownResults` passes it to `Git.work_tree_id` as `left_out`, and the tree that returns is part of the result's key.
- A name that breaks the pattern is reported at the path of its key: `invalid stages.<name>.[key]: ...`, likewise `roles.<name>.[key]` and `project_commands.<name>.[key]`.
- The methods: `first_stage()`, `role_of(stage)` (`None` for a stage without a role, `KeyError` for an unknown stage) and `position(stage)` (index in `stages`; `ValueError` for an unknown one, not specified).
- The rules that look across keys run at load, see "The rules of the definition" below. `first_stage()` is safe on a loaded definition, because rule 3 requires the stage `done`.

### Faults

`parse` raises only `PipelineDefinitionInvalid(fault)` (a `FactoryError`; the message is the fault). The faults are `not valid YAML: <problem> (line <l>, column <c>)` (`yaml_fault` in the same module builds it from ruamel's `problem` and `problem_mark`, 1-based, on one line: the repeated key is named in the problem, a line break inside the problem is written as the two characters `\n` or `\r`, and ruamel's context lines and its `To suppress this check` hint are left out; without a mark the position is omitted, and an error with no problem gives the first non-blank line of its text), `the pipeline definition must be a mapping` (a list, a string or an empty text) and the spellings of `all_faults` in `factory.adapters.validation_faults`, the same module the work item reader uses: `unknown key: <path>`, `missing key: <path>` and `invalid <path>: <message>`. A `<path>` has dots between keys and `[n]` for a list position (`roles.coder.write_paths`). A text with several faults is refused once, with all of them joined by `; ` in the order unknown key, missing key, invalid value (`unknown key: x; missing key: contract`). The rules below run only when every field is valid, so the field faults come first and alone.

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
| 12 | `tool path <path>: must be <folder>/* or ~/<folder>/*`, once for each such path |

Rule 12: `<folder>` is one or more `/`-separated segments, each non-empty, none `.` or `..`, none holding `*`, `?` or `[`, and it does not start with `/`. `*.log`, `.venv`, `/var/cache/*`, `a/*/b/*`, `~/*` and `a/./b/*` are refused; `.venv/*`, `a/b/*` and `~/.cache/*` pass. The helper `tool_path_folder` (`factory.domain.pipeline_definition`) returns the folder of a valid tool path, `~/` kept, and `None` for any other form. A `tool_paths` that is not a list is refused by the model (`invalid tool_paths: Input should be a valid list`).

Rules 10 and 11 apply to every stage except `done`, and only when the stage `done` exists. Without it the end of the pipeline is unknown, and rule 3's fault is the one that matters. A stage with an empty `next` has nowhere to send a forward outcome or an approval; a stage with neither a role nor `approval: true` runs no agent and waits for no human. Rule 10's faults come before rule 11's, each in the order of the stages. A stage no `next` names (such as `acceptance`) is accepted: there is no rule on reachability.

Tests: `tests/adapters/test_pipeline_rules.py` (through the reader, comparing `fault`) and `tests/application/test_pipeline_loading_rules.py` (each refusal is one reported stop).

```bash
uv run python -c "
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
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

`PipelineLoader(boundaries).load(ref=PIPELINE_REF)` (`factory.application.pipeline_loading`; `PIPELINE_REF` is `origin/main`) is the one place that loads the definition. It reads `PIPELINE_DEFINITION_FILE` at `ref` with `git.show_file` (never the work tree), parses it with `pipeline_reader`, and only when the text is valid checks with `agent_definitions.names()` that every role has an agent. Every refusal of the definition is `PipelineDefinitionInvalid(fault)`; the faults are listed in the operator guide, "The stop `pipeline_definition_invalid`", and the rules in "The rules of the definition" above. When those checks pass, `load` clears `pipeline_definition_invalid` (at `PIPELINE_REF`) and then calls `agent_definitions.read(role)` for every role in the order of `roles`; an `AgentDefinitionInvalid` is raised to the caller as it is, not wrapped.

- Only the loader raises and clears the stops `pipeline_definition_invalid` and `agent_definition_invalid`; no caller does. At `PIPELINE_REF` a refusal calls `StopService.raise_stop` before it raises, and a success calls `clear_stop` before it returns. A refused agent file raises `RepositoryStop(reason="agent_definition_invalid", detail="<agent name>: <fault>")`; since a definition that passes its own checks has already cleared `pipeline_definition_invalid`, only the agent stop remains. Any `AgentDefinitionInvalid` raises it, not only an unapplied key.
- A load at any other ref raises the same refusal but raises and clears no stop, so a read of a branch never changes the health status. `WritePathService` ("The write paths" below) reads the definition at another commit and parses it directly with `pipeline_reader`, not through the loader.
- A `GitError` propagates and raises no stop. An `OSError` of the stop's writes propagates in place of `PipelineDefinitionInvalid`.
- Tests: `tests/application/test_pipeline_loading.py`, with `human.push_file` and `checkout.fetch()` for other versions of the file and `install_agents(agent_home, roles)` in `tests/git_support.py` for the agent files.

## The prompt and the request for a stage

Before a stage's agent runs, `TaskComposer` (`factory.application.task`) builds its `AgentRunRequest`; the caller gives it `Boundaries`, the `PipelineDefinition` and the `environment`, and each call a `TaskContext` (work item, path, stage, document, branch, pull request, the form findings, the `GuardSettings`). The pure rules are in `factory.domain.prompts`.

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

`compose` fills `AgentRunRequest` with the agent as given, the prompt, the decisions, `time_limit` (the role's minutes), `working_directory` (`boundaries.checkout`), `guard` (from the context) and `os_user`, which is `boundaries.settings.agent_user`. `environment` is a copy of the mapping given to `TaskComposer`, passed on unchanged: nothing is added, removed or scrubbed here (the wiring supplies it, already scrubbed at its source, `production_environment()`). `agent(stage)` reads the definition of the stage's role through `AgentDefinitionReader`; a stage without a role raises `ValueError` naming it, a missing file lets `AgentDefinitionMissing` through. A document without a state makes `compose` raise `WorkItemFormatError`.

The prompt is `compose_prompt(facts)`, except for an acceptance at the definition's `acceptance_stage` (`context.stage == definition.acceptance_stage` and `is_acceptance(context.work_item)`): there it is `acceptance_prompt(compose_prompt(facts), AcceptanceService(boundaries, definition).facts(feature_of(context.work_item)))`, so the fact lines (`Archived stories`, `Next free story number`, `Cost of the stories`, `Human interventions of the stories`) follow the usual prompt after an empty line. A story, an acceptance at another stage and a definition whose `acceptance_stage` is `None` get the unchanged prompt. The facts are computed by code at `origin/main`, not by the agent.

### The story form check

`StoryFormChecker(boundaries).findings(document)` returns `check_story_form(document, form, folder="in-progress")`. The form is read with `Git.show_file("origin/main", STORY_FORM_FILE)`, never from the work tree, so nothing an agent writes there changes it; the checkout must have fetched to see a form the human pushed. A form absent at `origin/main` raises `WorkItemFormatError` with `path == "factory/story-form.md"`. A stage runs the check before and after the agent.

An acceptance runs through this same stage protocol (`StageLauncher`, `AfterAgent`, `StageRunner`) unchanged. Its report (`# Acceptance of <title>` and `## Journal`) has none of the story form's sections, so `findings` returns `[]` for a document whose state is an `AcceptanceState` (the opening always writes one), before it reads the form: a missing form file is then no `WorkItemFormatError` either. The checker receives only the document, which is why it looks at the type of the state and not at the work item id. Without this, decision rule 1 would turn the reviewer's forward decision into a question every time.

Tests: `tests/domain/test_prompts.py`, `tests/application/test_task.py`, `tests/application/test_task_acceptance.py`, `tests/application/test_stage_run_acceptance.py`.

## Opening a work item

`WorkItemOpening` (`factory.application.opening`) runs before a stage is claimed. It is built with `Boundaries` and the `PipelineDefinition`. Neither method commits, pushes or fetches; the tick fetched before, so a commit pushed since is not seen. The claim makes the first commit, which for a new branch is also the opening commit.

### `prepare(work_item, path)`

`path` is the work item's file under its feature's `in-progress/` folder, the same on `main` and on its branch. The branch is `branch_name(work_item)`. When `prepare` returns, the checkout is on that branch with a clean work tree, and it returns a frozen `PreparedWorkItem` (work item, branch, path, document, `branch_existed`, `merge_conflict`).

- **No `origin/<branch>`: the work item is new.** The local branch is created at `origin/main` and the file is read from `origin/main`. An absent file raises `WorkItemFormatError` with `path` set. Only the body of the backlog file is used: whatever its own front matter says (`stage`, `attempts`, `blocked`, a `journal` list) is ignored. The state is `initial_state` of the definition's first stage. A body without a `## Journal` section gets an empty one at its end; entries already in that section are left as they are, and the form check reports the mismatch between the text and the one record of the state. Entry 1 (`human`, `created`, dated by the clock) is then appended by code.
- **`origin/<branch>` exists.** The local branch is reset to `origin/<branch>`, whatever a local branch of that name held, then `origin/main` is merged in. On a conflict the wrapper has already aborted the merge: `merge_conflict` is `True`, the head is the remote branch's and the document is the branch's. The document is read from the work tree after the merge.

Doing the merge here means the baseline of the undo, taken at the stage-start commit, comes after every preparation step.

### `ensure_pull_request(work_item, document)`

Returns, in this order: the pull request numbered in `document.state.pull_request` if it is open; the open pull request of the branch; a new draft titled `<id>: <title>` with the body as description. Only an open pull request is reused; a closed or merged one never is. The title is looked up only when a draft is created, and a body without a title line then raises `WorkItemFormatError`. A `HostingServiceError` propagates. No file changes.

Tests: `tests/application/test_opening.py`.

## Starting a stage

`StageLauncher(boundaries, instance, definition, environment)` (`factory.application.stage`) takes a `PreparedWorkItem` from `WorkItemOpening.prepare` and runs the stage's agent. `instance` and `definition` go to `ClaimService`; `environment` is the environment of the agent run and reaches `TaskComposer` unchanged, so the run holds exactly those entries.

`launch(prepared)` does these steps in this order. The claim in step 4 is the only write to the git remote.

1. Refuse a work item with `merge_conflict` set or without a state: `ValueError`, before anything is read or pushed.
2. Read the agent definition with `TaskComposer.agent`. A stage without a role (the approval stage) raises `ValueError` naming the stage; a missing agent file raises `AgentDefinitionMissing`. Both come before any push.
3. Take the story form findings from `prepared.document` (`StoryFormChecker`).
4. Push the claim: `ClaimService.claim(branch, path, document, stage)` makes the stage-start commit. A rejected push or an unreachable remote raises `PushFailed`.
5. Read the work item file back from the work tree. `StartedStage.document` is what the stage-start commit holds, not the document given to the claim.
6. `WorkItemOpening.ensure_pull_request`: find or create the pull request.
7. `WritePathService.at(stage_start, path)` gives the guard, from the definition at the stage-start commit.
8. `TaskComposer.compose` builds the request (prompt, guard, environment, allowed decisions).
9. `run_sealed(boundaries, request, run=PatientRuns(boundaries).run)`: the agent runs, sealed (see `watching.md`, *Boundaries*), through `PatientRuns`. The cost record is begun before step 9 and completed after it.

**`PatientRuns`** (`factory.application.provider_limits`; `PatientRuns(boundaries).run(request)`) wraps `boundaries.agent_runtime.run` for the stage launch. A result that does not end `provider_limit` comes back as it is. After a `provider_limit` it loops: (1) the budget left is the agent's `budget_usd` less the run's cost so far, and at or below zero the run ends `budget`; (2) the time left is the request's `time_limit` less the calls' durations (the waits do not count), and at or below zero it ends `time_limit`; (3) when the waits reach the ceiling it logs `provider limit: <agent> waited <s> s, the ceiling of <c> s; the run ends provider_limit` and returns the result; (4) otherwise it logs `provider limit: <agent> waits <w> s before it resumes <session>` (`a new run` without a session), waits the result's `limit_wait` or the cool-down, at most what is left of the ceiling, and (5) calls the runtime again with `request.model_copy(...)`: `CONTINUE_PROMPT` and `resume_session` with a session, the request's own prompt without one, and in both the budget and the time left; (6) `resumed_result` joins the calls. The cool-down and the ceiling are `boundaries.settings.provider_limit` (`ProviderLimit`, `factory.domain.provider_limits`, defaults 10 and 120 minutes, from `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` and `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES`). It builds no `AgentRunRequest` of its own. The preflight's probe uses `run_sealed` without `run` and never waits.

**`Waiter`** (`factory.application.machine`) is the interface of waiting: `wait(duration)` returns after it and raises `ValueError` for a negative one. `SleepingWaiter` (`factory.adapters.clock`) calls `time.sleep`; `ManualWaiter(clock)` advances a `ManualClock` by the duration, records it in `waits` and returns at once. `build_boundaries` gives `SleepingWaiter()`. Tests: `tests/application/test_patient_runs.py`, `tests/application/test_stage_provider_limit.py`, `tests/adapters/test_waiters.py`.

**No agent run precedes the pushed claim.** When `run` is called, `origin/<branch>` already holds the stage-start commit with the claim and the journal record (`factory`, `started`); when step 4 fails, no run starts. The stage-start commit is the last commit before the run: for a branch that existed it is one commit above the old head (the merge of `main` in `prepare` comes before it), for a new work item it is also the opening commit.

The stage-start commit does not change `pull_request`: it is `None` for a new work item and otherwise the number already recorded. The number of the pull request found or created in step 6 is in `StartedStage.pull_request` and in the prompt; the stage's next commit records it. No local record of the run is written; the claim's `started_at` says when the stage began.

`launch` returns a frozen `LaunchedStage`: `started` (a `StartedStage` with the work item, stage, branch, path, `stage_start`, `document`, `pull_request` and the form `findings` taken before the run), `request` and `result`. A run that dies, reaches its `time_limit` or its budget is a result. `PushFailed`, `AgentDefinitionMissing` and `AgentRuntimeError` propagate unchanged; after an `AgentRuntimeError` the claim stays pushed.

Tests: `tests/application/test_stage_launch.py`. `ObservingRuntime` (`tests/observing_runtime.py`) is an `AgentRuntime` that records the remote branch's head, the checkout's `HEAD` and the pull requests in the hosting fake at the moment `run` is called, then delegates to `FakeAgentRuntime`.

## Stalls

A stall is the one way a stage ends without a result the factory can keep. It costs one attempt and is a value, never an exception. `StallService.stall` (`factory.application.stalls`) does it; the later stories (the branch, the decision, the form, a red check, a merge conflict) call it with their reason.

### The reasons

`factory.domain.decisions.StallReason` (defined in `factory.domain.journal`, which the stall record names) is one of `died`, `time_limit`, `budget`, `provider_limit`, `no_result`, `decision_not_allowed`, `left_branch`, `form_invalid`, `check_red`, `merge_conflict`, `nested_repository`. `stall_reason_of(result)` maps the end reason of an `AgentRunResult` to the reason of the same name and `completed` to `None`.

`factory.domain.post_texts.stall_cause(reason, detail="")` gives the reason's sentence, and `<sentence>: <detail>` with a detail. `stall_note(reason, attempts, attempts_cap, *, detail="")` gives `Stalled (attempt <n> of <cap>): <cause>. ` and then `Retrying on the next tick.` when `attempts < attempts_cap`, otherwise `The attempts cap is reached; the factory asks you next.` The word "retry" appears only in the first case.

The detail's trailing line breaks are removed. A detail of one line is part of the sentence, as above. A detail of several lines puts its first line through `stall_cause` into the sentence, so the follow-up stays on that first line, and the remaining lines follow after an empty line in a fenced block: the fence `` ```text ``, the lines unchanged, the closing fence. GitHub renders a comment as Markdown, and unfenced output loses `<module>` and turns `__init__` bold. The fence is three backticks, or one more than the longest run of backticks in the remaining lines when that run is three or longer. The journal's stall entry is unchanged and keeps the detail as continuation lines.

### `StallService.stall(context, reason, detail="")`

`StallService(boundaries, instance, definition)`. `StallContext` (frozen, no unknown keys) holds `work_item`, `stage`, `branch`, `path`, `stage_start` (a `StageStart`, or `None` when the stage never started, for example a merge conflict at the preparation) and optionally the `document`, the `pull_request` and the `cost` (a `CostRun`) the caller already holds. The steps, in this order:

1. With a `stage_start`: when the checkout is not on `context.branch`, what the agent left on the other branch is discarded with `reset_to("HEAD")` (that branch keeps its head) and the branch is checked out at the stage-start commit. Then `UndoService.undo` runs, whatever the reason; its report is `StallResult.undo`. With a `context.cost`, the sidecar is written again right after the undo. Without a `stage_start` nothing is undone and `undo` is `None`.
2. The document is `context.document`, else the work item file read from the work tree.
3. The pull request is `context.pull_request`, else `WorkItemOpening.ensure_pull_request` (an open pull request of the branch, or a new draft).
4. The new state has `attempts` + 1, the claim released (`ClaimService.release`) and `pull_request` set; `stage`, `blocked`, `round`, `crashes`, `comments_read` and `handed_over` stay. One entry is appended: speaker `factory`, kind `stall`, text `Stage <stage> stalled (attempt <n> of <cap>): <cause>`.
5. The file is written, everything in the work tree is committed in one commit and pushed. Any push outcome but `pushed` raises `PushFailed`.
6. After the push, the note is posted with `PostKey(work_item, "stall", <the stall entry's number>)`.
7. Whether the note was `posted` or `already_posted`, `HostingService.set_labels(pull_request, labels_for(<the stalled state>))` writes the stage label, so a first-stage stall has its label before any result commit. Written, never read back.

So a stall keeps the writes inside the write paths (the undo reverts the rest) and releases the claim, which keeps a later tick from taking the stalled stage for a crash. The stall adds one commit, directly above the stage-start commit: the agent cannot commit, because the checkout's `.git` is the factory's alone (see the decision log's "The factory alone writes the checkout's `.git`").

A `HostingServiceError` is not a stall and propagates unchanged: from step 3 before anything is written, committed or pushed, so the remote is unchanged; from step 6 after the push, so the stall commit stays on the remote, no note is posted and no label is written; from step 7, so the stall commit stays and the note stays posted. `StallResult` (frozen, no unknown keys) holds `reason`, `attempts`, `attempts_cap`, `commit` (the pushed head), `pull_request` (the last three at least 1), `note` (the `PostOutcome`) and `undo`.

Tests: `tests/domain/test_decisions.py`, `tests/domain/test_stall_texts.py`, `tests/domain/test_stall_note_block.py`, `tests/application/test_stalls.py`, `tests/application/test_stall_labels.py`. The last starts stages with `StageLauncher` and the fake agent runtime; its `SwitchingRuntime` (a subclass of `ObservingRuntime`) switches the checkout to another branch while it runs.

## After the agent run

The factory believes what it observes, not what the agent reports. `AfterAgent(boundaries, instance, definition).process(launched)` (`factory.application.stage`) takes the `LaunchedStage` that `StageLauncher` returns and goes through these steps in order. The first step that fails is a stall (see "Stalls"), which counts one attempt, and the later steps do not run.

1. **Nested repository.** When `launched.nested_repositories` is not empty (the run already removed them), the stall `nested_repository` with the paths joined by `, ` as detail, whatever else the agent did. Its sentence is `the agent left a git repository in the work tree, which the factory removed`.
2. **Branch.** The checkout must still be on the work item's branch, otherwise the stall `left_branch`.
3. **Result.** `stall_reason_of(result)` turns a run that died, ran out of budget or time, or gave no result into the stall of that reason; the detail is the first permission denial (`denied: <tool>: <detail>`), if any. A decision that is not one of the request's `allowed_decisions` is `decision_not_allowed`, with the decision and the allowed ones as detail.
4. **Undo and restore.** `UndoService.undo` reverts the changes outside the write paths. Then the stage-start state (the claim included) and the stage-start journal are put back, whatever the agent wrote there: **the agent's edits to state and journal are always discarded.** The rest of the body keeps the agent's changes when the role may write the work item; when it may not, the undo has put the whole file back and lists it in `reverted`.
5. **The entry.** `factory.domain.decisions.agent_entry(role=, stage=, decision=, text=, undone=)` builds it, and code decides everything but the words. The speaker is the role. The kind is `question` for the decision `question`, otherwise `result`. The text is the agent's text, stripped, with one leading `<role>:` or `<stage>:` removed (the colon directly after the name; the role is tried first). A blank text gives `None`, which `AfterAgent` stalls as `no_result`. When paths were undone, the text ends with a blank line and `The factory undid changes outside the write paths: <paths sorted, joined by ", ">.`. The work item's own cost-record file, which the factory rewrites after the undo, is never named there.
6. **The form again.** The story form is checked on the undone work item and compared with the findings from before the run (`StartedStage.findings`). Only a finding that was not there before stalls, as `form_invalid`, with the new messages joined by `; ` as detail. Findings are compared by message with every run of digits replaced by one mark, so a finding whose line number moved because the agent edited above it is the same finding. A kind that now occurs more often than before counts as new: of equal messages the earlier ones count as the old ones. Only in this stall is the entry appended (above the stall entry); otherwise it is built but not appended.

What comes back is an `AgentAftermath` (frozen, no unknown keys): `started`, `request`, `result`, `decision`, `document` (the work item after step 3, without the entry), `entry`, `undo` (the `UndoReport`) and `form_findings` (all findings after the run). The stage's result commit ("The stage protocol", below) appends the entry.

Tests: `tests/domain/test_agent_entry.py`, `tests/application/test_after_agent.py`. The latter starts stages with `StageLauncher` and the fake agent runtime, whose `ScriptedRun.writes` tampers with the work item, writes outside the write paths and breaks the form.

## The decision rules

`factory.domain.decisions.decide(definition, state, decision, findings=())` turns the agent's decision into a `StageMove` (frozen, no unknown keys): `rule`, `stage`, `blocked`, `round` and `question`. It is pure; `StageFinisher` ("The stage protocol", below) applies the move. It never touches `attempts` or `crashes`: a rework counts rounds, a stall counts attempts, and the two are kept apart.

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

The factory's own question texts are in `factory.domain.post_texts`: `round_cap_question(rounds, cap)`, `findings_question(findings)` (the messages numbered from 1, joined by one space) and `attempts_cap_question(stage, attempts, last_stall)`. That module imports `StallReason` and `FormFinding` only under `TYPE_CHECKING`, because `decisions` imports it.

Tests: `tests/domain/test_decision_rules.py`, `tests/domain/test_question_texts.py`.

## The stage protocol

`StageRunner(boundaries, instance, definition, environment).run(work_item, path)` (`factory.application.stage`) is the one entry point that runs a stage from the claim to the result commit. It returns a frozen `StageReport`: `work_item`, `stage` (the stage that ran, from the state `prepare` read), `next_stage`, `rule` (the decision rule applied, 1 to 7, or `None` when the stage stalled before a decision), `commit` (the pushed head), `pull_request` and `stall`. `stall` is set exactly when the stage stalled; `next_stage` equals `stage` for a stall and for the rules that keep the stage (1, 2 and 4). A red check is rule 5.

`run` does these steps in this order; a `StallResult` from any step ends the run with a report whose `rule` is `None`:

1. `WorkItemOpening.prepare`. With `merge_conflict` set in the result, `StallService.stall` with reason `merge_conflict` and no stage start: no claim is pushed and no agent runs.
2. `StageLauncher.launch`: claim, pull request, agent run. `environment` is passed unchanged.
3. `AfterAgent.process`: branch, result, undo, entry, form.
4. `StageFinisher.finish`: decision, checks and reports, result commit.

### `StageFinisher.finish(aftermath)`

1. `decide` on the state of `aftermath.document`, with the form findings after the run. A first stage whose agent fixed the last finding therefore moves forward instead of asking.
2. Rule 6 only: each check of the stage's `checks`, in order, through `KnownResults.run` (`processes-and-checks.md`, *Known results*), which runs `ProjectCommands.run` with the `time_limit` of the pipeline definition's project command unless a passed result is known for the same key. The first one that is not green ends the stage as a stall `check_red` (rule 5): the later checks and all reports do not run. The stall detail is the command's name and the last `STALL_TAIL_LINES` (15) lines of its output (all, when fewer). The journal then holds the agent's entry, ending with the lines of the checks that were green, directly above the `factory` stall record. The stall costs one attempt and changes neither the stage nor `crashes`. The checks see the work tree after the undo.
3. Rule 6 only, once every check is green: each report of the stage's `reports`, in order. A report that fails holds nothing; a report is recorded, never enforced.
4. The agent's entry gains, after a blank line, one line `` `<command>`: <last line of its output> `` (`command_line`) for each green check and each report, in the order they ran (for example `` `check`: 12 passed ``). A result taken instead of a run adds `` (not run again: passed on tree <12 characters> at <time>) ``, and a result stopped at its time limit adds `` (stopped at its time limit after <s> s) ``. A stage with neither gets no such lines.
5. The entry is appended; when the move has a question (rules 1 and 4), a `factory` entry of kind `question` follows it.
6. The new state takes `stage`, `blocked` and `round` from the move and `pull_request` from the started stage, and the claim is released. `crashes` is reset to 0 on rule 6, a forward move, and unchanged otherwise; `attempts`, `comments_read` and `handed_over` never change.
7. The file is written, everything in the work tree is committed in one commit and pushed. Any push outcome but `pushed` raises `PushFailed`, and no label has been written.
   Between the commit and the push, when the move's stage is an approval stage (`approval` in the pipeline definition): `HostingService.set_description(number, text)`, with `hand_over_description(moved, Git.log("HEAD", since="origin/main"))` for a story, or `acceptance_description(moved, role)` for an acceptance, `role` being the role of the stage that ran. After the push those commits are the ones the hand-over reads from `origin/<branch>`. A `HostingServiceError` there is caught and logged as `pull request #<number>: description not written before the push: <error>`, and the push goes on; the hand-over writes the description on the next tick. A forward move, a rework and a question write no description. It is the private `_describe` of `_commit_and_push`; the order commit, description, push is fixed. `handed_over` stays unset.
8. Last, `HostingService.set_labels(pull_request, labels_for(new_state))`. `labels_for` (`factory.domain.labels`) gives `[LABEL_PREFIX + state.stage]`, for example `["stage:review"]`. Labels are a projection of the stage: they are written after the push and never read back. A `HostingServiceError` from this step propagates; the result commit stays pushed.

Rules 1, 2, 3, 4 and 7 run no check and no report.

A run adds exactly one commit of the factory's own on `origin/<branch>`: the result commit or the stall commit, directly above the stage-start commit, since the agent cannot commit. It holds the whole work tree, so a file a check creates is committed unless `.gitignore` covers it.

Tests: `tests/domain/test_labels.py`, `tests/application/test_stage_finish.py`, `tests/application/test_stage_run.py`. The checks and reports are real `make` targets from a `Makefile` the tests push to `main`; the agent is `FakeAgentRuntime`, the hosting service its fake.
