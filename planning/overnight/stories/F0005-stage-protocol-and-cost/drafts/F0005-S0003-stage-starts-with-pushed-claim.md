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
