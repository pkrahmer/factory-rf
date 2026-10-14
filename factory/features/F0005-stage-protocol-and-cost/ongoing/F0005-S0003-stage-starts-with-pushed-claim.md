---
stage: doing
pr: 60
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
# The stage starts with the pushed claim, then the agent run

## Assignment (as of log entry 1)

Build the start of a stage: with a prepared work item (S0002), read the stage's agent definition, check the story form, push the claim through the claim service, ensure the pull request, take the guard settings from the stage-start commit, compose the request and only then run the agent. No agent run starts before the stage-start commit with its "started" entry is pushed, and none starts when that push is rejected or the remote is unreachable (GH1.1, R19). No local run record is written; the board reads the claim's `started_at` (questionnaire 1, Q3). The environment of the agent run is the caller's: `StageLauncher` takes it and gives it to `TaskComposer` (S0001) unchanged. Covers GH1.1; implements the start of R19 (the stage's result commit is S0007's). Keeps kept things 4 (each stage starts from the committed work item) and 5 (the same steps in the same order). The pull request number is recorded by the stage's next commit (S0004, S0007), not by the stage-start commit; a boundary error after the claim leaves the claim pushed, which F0008 handles as a crash (FEATURE decision 8).

## Interface

`src/factory/application/stage.py`

```python
class StartedStage(BaseModel):
    work_item: WorkItemId
    stage: Name
    branch: str
    path: str
    stage_start: StageStart
    document: WorkItemDocument
    pull_request: PullRequestView
    findings: list[FormFinding]

class LaunchedStage(BaseModel):
    started: StartedStage
    request: AgentRunRequest
    result: AgentRunResult

class StageLauncher:
    def __init__(
        self,
        boundaries: Boundaries,
        instance: str,
        definition: PipelineDefinition,
        environment: Mapping[str, str],
    ) -> None: ...
    def launch(self, prepared: PreparedWorkItem) -> LaunchedStage: ...
```

Types: `Mapping` from `collections.abc`, `StageStart` from `factory.application.claims`, `PreparedWorkItem` from `factory.application.opening`, `FormFinding` from `factory.domain.story_form`, `AgentRunRequest` and `AgentRunResult` from `factory.domain.agent_runs`, `PullRequestView` from `factory.domain.hosting`. Both models are frozen and forbid unknown keys. `StartedStage.document` is the work item as committed in the stage-start commit, read back from the work tree; `findings` are the story form's findings before the run.

- `launch` performs these steps in this order, and the git remote is written only by the claim in step 4: (1) refuse a conflicted work item or a stage without a role; (2) read the agent definition with `TaskComposer.agent`; (3) take the form findings with `StoryFormChecker` from `prepared.document`; (4) push the claim with `ClaimService.claim(branch, path, prepared.document, stage)`; (5) read the work item file back; (6) `WorkItemOpening.ensure_pull_request`; (7) `WritePathService.at(stage_start, path)` for the guard; (8) `TaskComposer.compose`, built with the environment given to `StageLauncher`; (9) `AgentRuntime.run`.
- The stage-start commit is the commit `ClaimService.claim` makes. The branch's opening and the merge of the main branch come before it, so it is the last commit before the run; for a new branch it is also the opening commit.
- The stage-start commit does not change `pull_request`: the state there carries `None` for a new work item and the number already recorded otherwise. The pull request found or created in step 6 is in `StartedStage.pull_request`.
- A conflicted `prepared` (`merge_conflict`) and a stage whose role is `None` raise `ValueError`, before anything is read or pushed.
- `PushFailed`, `AgentDefinitionMissing` and `AgentRuntimeError` propagate unchanged. A run that dies, reaches its `time_limit` or its budget is a result, not an error.

Tests: `tests/application/test_stage_launch.py`. It uses `ObservingRuntime(AgentRuntime)` in `tests/observing_runtime.py` (a helper module at the `tests/` root, as `git_support.py` is), an `AgentRuntime` that records what the remote branch and the hosting fake hold at the moment `run` is called and then delegates to `FakeAgentRuntime`; S0004, S0005 and S0008 import it. The agent files of the roles under test are written into the agent home that the `boundaries` fixture reads.

## Acceptance criteria

1. When the runtime's `run` is called, `origin/<branch>` already holds the stage-start commit: the work item file there has a state whose `claim` names the launching instance and the stage, with `started_at` equal to the fixture clock, and the journal's last record is (`factory`, `started`); `StartedStage.document` equals that file as the work item reader parses it.
2. For a work item that already had a branch, when `origin/main` holds no commit the branch lacks, the stage-start commit is exactly one commit above the previous head of `origin/<branch>`, and `StartedStage.stage_start.commit` equals both `origin/<branch>` and the checkout's `HEAD` at the moment of the run.
3. For a new work item the stage-start commit is the opening commit: `log("origin/<branch>", since="origin/main")` holds exactly one commit, and the file there has the initial state with the claim, with journal records (1, `human`, `created`) and (2, `factory`, `started`).
4. When another clone pushes to the work item's branch between `prepare` and `launch`, the claim push is rejected: `launch` raises `PushFailed` with outcome `rejected` and `FakeAgentRuntime.requests()` stays empty.
5. When the remote is unreachable (its directory is deleted after `prepare`), `launch` raises `PushFailed` with outcome `unreachable` and no agent run starts.
6. A stage whose agent file is missing raises `AgentDefinitionMissing` before anything is pushed: the remote branch is unchanged (absent for a new work item) and no agent run starts.
7. `launch` of a `PreparedWorkItem` with `merge_conflict` set raises `ValueError`; nothing is pushed and no agent run starts.
8. `launch` of a work item whose stage has no role (the approval stage) raises `ValueError` naming the stage; nothing is pushed and no agent run starts.
9. For a new work item, when the runtime's `run` is called, exactly one open draft pull request of the branch exists in the hosting fake, `StartedStage.pull_request` is that pull request, and the `pull_request` of the state in the stage-start commit is `None`.
10. For a work item at a later stage whose state already records pull request number 7 (an open one), the `pull_request` of the state in the stage-start commit is still 7, no second pull request is created, and `StartedStage.pull_request` is number 7.
11. The request the runtime received equals `LaunchedStage.request`; its `guard` equals `WritePathService.at(stage_start, path)`; its prompt's `Pull request:` line carries the number of the draft.
12. The request's `environment` equals the mapping given to `StageLauncher` (a `PATH` and a `HOME` in the test), and it holds no other entry.
13. For a work item at the first stage whose story lacks a required section, the prompt has a `Format check found:` line and `StartedStage.findings` is the same non-empty list; for a complete story the prompt has `Format check: passed` and the list is empty.
14. `LaunchedStage.result` is the runtime's result unchanged: a scripted result with end reason `died`, `time_limit` or `budget` (parametrised) is returned without an exception.
15. An `AgentRuntimeError` raised by the runtime propagates unchanged, and the stage-start commit stays on `origin/<branch>`.
16. `StartedStage` and `LaunchedStage` are frozen and forbid unknown keys: assigning to `branch` of `StartedStage` and to `result` of `LaunchedStage` (through `setattr`, the field's name in a variable) and building each with an unknown field raise `ValidationError`.
17. make check stays green.
18. docs: `docs/project-guide.md` states the order of a stage's start (agent definition, form check, claim pushed, pull request, guard, prompt, run) and that no agent run precedes the pushed claim; `docs/decisions.md` records that the pull request number travels with the stage's next commit and that no local run record is kept (the board reads the claim).

## Demo

```bash
uv run pytest tests/application/test_stage_launch.py
```
Expect: the last line reports `passed` and the output contains neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `src/factory/application/stage.py` names `StartedStage`, `LaunchedStage` and `StageLauncher` with signatures, the nine ordered steps, the source module of every type used, and the errors that propagate. Nothing needs a further decision.
   - Criteria: each is testable by one test function. Every rule has its failing side. A conflicted work item is criterion 7 and a stage without a role is criterion 8. A rejected push is 4, an unreachable remote is 5, a missing agent file is 6, and a runtime error is 15. A run that dies or hits its limit being returned as a result is 14. The frozen models and the unknown-key refusal are 16. Interface comments on the stage-start commit (one commit above the old head, the opening commit for a new item, `pull_request` unchanged, `document` read back) are covered by 1, 2, 3, 9 and 10. The environment passed on unchanged is 12.
   - Demo: `uv run pytest tests/application/test_stage_launch.py` is runnable, and its `Expect:` line (last line says `passed`, no `failed` or `error`) can be checked against the output.
   - Architecture: the module sits in `factory.application` and reaches git, hosting and the runtime only through the interfaces. The test helper `tests/observing_runtime.py` sits at the `tests/` root, like `git_support.py`.
   - Scope: the story is within the feature's scope (the stage start, the claim pushed first, the guard, the environment). It leaves out the pull request state reading, F0008's crash handling and the cost records, which are the feature's out-of-scope items or later stories.
3. tester: red tests written for the stage start. `make test` stops at collection with `ModuleNotFoundError: No module named 'factory.application.stage'`, which is the expected reason. `make lint` is green. I skipped the type check as the stage says.

   Criteria → tests (all in `tests/application/test_stage_launch.py`):
   - criterion 1: `test_the_stage_start_commit_is_on_the_remote_when_the_run_starts`
   - criterion 2: `test_the_stage_start_commit_is_one_commit_above_the_existing_branch`
   - criterion 3: `test_the_stage_start_commit_of_a_new_work_item_is_its_opening_commit`
   - criterion 4: `test_a_push_by_another_clone_rejects_the_claim_and_no_run_starts`
   - criterion 5: `test_an_unreachable_remote_fails_the_claim_and_no_run_starts` (the remote directory is removed with `shutil.rmtree` after `prepare`)
   - criterion 6: `test_a_missing_agent_file_is_raised_before_anything_is_pushed`, parametrised for a new branch (stays absent) and an existing one (head unchanged)
   - criterion 7: `test_a_conflicted_work_item_is_refused_before_anything_is_read_or_pushed`
   - criterion 8: `test_a_stage_without_a_role_is_refused_naming_the_stage` (`match="approval"`)
   - criterion 9: `test_a_new_work_item_has_one_open_draft_when_the_run_starts`
   - criterion 10: `test_a_recorded_open_pull_request_is_kept_and_reused` (six pull requests of other branches are created first, so the work item's is number 7)
   - criterion 11: `test_the_runtime_receives_the_request_with_the_guard_and_the_draft_number`
   - criterion 12: `test_the_request_carries_exactly_the_given_environment`
   - criterion 13: `test_the_first_stage_prompt_carries_the_form_findings`, parametrised complete / without-smoke-test
   - criterion 14: `test_a_run_that_did_not_complete_is_returned_as_its_result`, parametrised died / time_limit / budget
   - criterion 15: `test_a_runtime_error_propagates_and_leaves_the_claim_pushed` (nothing is queued, so `FakeAgentRuntime` raises `AgentRuntimeError("no scripted run is queued")`)
   - criterion 16: `test_started_and_launched_stages_are_frozen_and_forbid_unknown_keys`
   - criteria 17 and 18 (make check, docs) are not test cases.

   Files created:
   - `tests/application/test_stage_launch.py`
   - `tests/observing_runtime.py`: `ObservingRuntime(AgentRuntime)` takes the delegate `FakeAgentRuntime` and the keywords `remote`, `branch`, `hosting` and `checkout: Git`. On each `run` it records an `Observation` (`remote_head`, `checkout_head`, `pull_requests`), then delegates. `observations()` lists them. The tests put it into `Boundaries` with `dataclasses.replace(boundaries, agent_runtime=...)`.

   Notes for the coder:
   - Criteria 7 and 8 install no agent file. If `launch` read the agent definition before step 1's refusal, it would raise `AgentDefinitionMissing` instead of `ValueError`, so these tests also check the order.
   - Criterion 7 checks only for `ValueError`, not its message.
   - Criterion 16 rebuilds each model with `model(**dict(instance), unknown=1)`.

   Modules the runner could not import: `factory.application.stage`.

   Nothing in the criteria needed interpreting; no questions are open.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: built the start of a stage in `src/factory/application/stage.py` (commit 61fd765). It holds `StartedStage`, `LaunchedStage` and `StageLauncher`. All 20 cases in `tests/application/test_stage_launch.py` pass, and `make check` is green (total coverage 99.55 %, `stage.py` 94 %).

   What `launch` does, in the interface's order:
   1. `_launchable_stage` refuses a work item with `merge_conflict` set, a document without a state, a stage missing from the pipeline definition, or a stage without a role. Each raises `ValueError` naming the branch or the stage, before anything is read.
   2. It reads the agent definition with `TaskComposer.agent`.
   3. It takes the form findings with `StoryFormChecker` from `prepared.document`.
   4. `ClaimService.claim` writes the stage-start commit and pushes it. This is the only remote write.
   5. It reads the work item file back from the checkout.
   6. `WorkItemOpening.ensure_pull_request` finds or creates the pull request.
   7. `WritePathService.at` gives the guard.
   8. `TaskComposer.compose` builds the request, using the environment the launcher was given.
   9. `AgentRuntime.run` runs the agent.

   `PushFailed`, `AgentDefinitionMissing` and `AgentRuntimeError` are not caught, so they reach the caller unchanged. The `ClaimService`, `WorkItemOpening` and `TaskComposer` objects are built once in `__init__`.

   Main decision: the launcher checks the role itself in step 1 instead of relying on `TaskComposer.agent`'s `ValueError`. That keeps the refusal ahead of every read. It also keeps the error for a stage missing from the pipeline definition a `ValueError` rather than a `KeyError` from the stages table. Rejected: building the guard and composing the request before the claim. The claim's commit is the guard's input (`WritePathService.at(stage_start, …)`), and the request's pull request number only exists after step 6.

   Refactor pass: I read the diff as a reviewer would and found nothing to rename, simplify or remove, so there is no refactor commit.

   Noticed, not touched: two defensive refusals in `_launchable_stage` have no test, which leaves `stage.py` lines 93 and 96 uncovered. One is a document without a state, which `prepare` never produces; the other is a stage that is not in the pipeline definition. Neither is a limit the Interface states. The `docs:` criterion is the documenter's.

   `make check`: check: green
5. reviewer: one quality finding (group 4). Groups 1–3 pass:
   - Group 1: criteria 1–16 each have a test that checks what the criterion says. The coder's entry records `make check` green.
   - Group 2: `stage.py` imports only from `factory.application` and `factory.domain`, and it reaches git, the hosting service and the runtime only through `Boundaries`.
   - Group 3: no strings are built into commands and no check is silenced.

   Findings:
   1. `src/factory/application/stage.py:97-98`: the role check repeats `TaskComposer._role_name` (`src/factory/application/task.py:106-110`), with the same message word for word. The log's reason for it ("keeps the refusal ahead of every read") does not hold. `TaskComposer.agent` is step 2, and it raises this `ValueError` in `_role_name` before it calls `agent_definitions.read`, so no read comes first. Criterion 8's test would pass without the copy. Fix: drop the role check from `_launchable_stage` and let step 2 (`self._composer.agent(stage)`) raise it. If the stage-membership check at line 96 is kept so that an unknown stage gives `ValueError` rather than `KeyError`, put it in front of `TaskComposer._role_name` or `agent`, not beside a copy of the role rule.

   Not findings:
   - The `state is None` refusal at line 93 is needed to narrow the type for mypy.
   - The criteria and the Interface match what was built.
   - The docs criterion still describes what the documenter must write.
