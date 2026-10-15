---
stage: docs
pr: 111
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
# An acceptance runs through the stage protocol

## Assignment (as of log entry 1)

Let an acceptance run its stage through F0005's stage protocol, the same code that runs a story's stages, with the smallest change that makes it work. Two things stop an acceptance today. First, the protocol checks the story form before and after every agent run (`StoryFormChecker`, called by `StageLauncher` and `AfterAgent`); the report `# Acceptance of <title>` with a `## Journal` section has none of the form's `## Description`, `## Interface`, `## Acceptance criteria` and `## Smoke test`, so decision rule 1 (F0005-S0006) would turn the reviewer's forward decision into a question every time and an acceptance would never reach its approval. Second, nothing appends the acceptance reviewer's facts (S0003) to its prompt. This story makes `StoryFormChecker.findings` return no findings for a document whose state is an `AcceptanceState` (the opening always writes one, and the checker receives the document only), and makes `TaskComposer.compose` append `acceptance_prompt(...)` with the facts when the stage is the definition's `acceptance_stage` and the work item is an acceptance. The claim, the draft pull request, the run, the undo, the restore, the entry, the checks and the result commit are the protocol's, unchanged. Covers no handover condition alone; it makes ST2.1's and ST2.2's acceptances runnable, carries the reviewer half of kept thing 19 (the acceptance judges the whole) and keeps kept thing 11 (the prompt's facts are computed by code, not by the agent). Changes F0005's `factory.application.task` by these two additions and nothing else. Uses `AcceptanceService` and `acceptance_prompt` (S0003), `AcceptanceState` (S0001), and the protocol's `StageRunner` (F0005-S0007) for the end-to-end check.

## Interface

`src/factory/application/task.py` (F0005-S0001's module; two methods grow, no signature changes)

```python
class StoryFormChecker:
    def findings(self, document: WorkItemDocument) -> list[FormFinding]: ...

class TaskComposer:
    def compose(self, context: TaskContext, agent: AgentDefinition) -> AgentRunRequest: ...
```

Rules:

- `StoryFormChecker.findings(document)` returns `[]` when `document.state` is an `AcceptanceState`, before it reads the form: a missing form file is then no `WorkItemFormatError`. For every other document it is the F0005 behaviour exactly.
- `TaskComposer.compose(context, agent)`: when `context.stage == definition.acceptance_stage` and `is_acceptance(context.work_item)`, the request's `prompt` is `acceptance_prompt(compose_prompt(facts), AcceptanceService(boundaries, definition).facts(feature_of(context.work_item)))`, the composer's own `boundaries` and `definition`. For any other stage or work item, and for a definition whose `acceptance_stage` is `None`, the prompt is `compose_prompt(facts)` as before. Everything else of the request is unchanged.
- The module `factory.application.task` imports `factory.application.acceptance`: both are in the application layer, and `acceptance` does not import `task`.
- No test of F0005 changes: its tests (`tests/application/test_task.py`, `test_stage_launch.py`, `test_after_agent.py`) build documents with a plain `WorkItemState` and contexts of stories, which take the unchanged paths.

Tests: `tests/application/test_task_acceptance.py` and `tests/application/test_stage_run_acceptance.py` (new files: the tests of F0005 stay as they are); the fixtures `remote`, `checkout`, `human`, `hosting`, `agent_runtime`, `boundaries`, `agent_home` and `clock`, with `install_agents(agent_home, <the roles of the fixture's pipeline definition>)` from `tests/git_support.py`. The fixture's feature `F0001` has a backlog story and is never due; the tests push a feature `F0002-todo` of their own with `human.push_file("main", ...)` (`feature.md` with the title `Todo service`, story files under `done/`, nothing under `backlog/` or `in-progress/`) and open the acceptance with `AcceptanceService.open`. The checker tests use the fixture's `factory/story-form.md`. The run is scripted on `FakeAgentRuntime` as F0005-S0007's tests do: the decision `approval` and a non-blank entry.

## Acceptance criteria

1. `StoryFormChecker(boundaries).findings(document)` is `[]` for a document whose state is an `AcceptanceState` and whose body is only `# Acceptance of Todo service` and an empty `## Journal` section.
2. The same call is `[]` for that document when `factory/story-form.md` is missing at `origin/main`, where it raises `WorkItemFormatError` for a document with a plain `WorkItemState`.
3. The same body with a plain `WorkItemState` still gives findings (the missing sections): the check of a story is unchanged.
4. `TaskComposer.compose` for an acceptance at the stage `acceptance` returns a request whose `prompt` equals `acceptance_prompt(compose_prompt(<the facts of the context>), AcceptanceService(boundaries, definition).facts("F0002"))`: the usual lines of the prompt, an empty line, and the three lines `Archived stories: ...`, `Next free story number: ...` and `Cost of the stories: ...`.
5. `compose` for a story, and for an acceptance at a stage other than `acceptance`, returns a prompt with no line that starts with `Archived stories:`.
6. `compose` with a definition whose `acceptance_stage` is `None` returns the unchanged prompt for any work item, without an error.
7. `StageRunner(...).run(<the opened acceptance's id>, <its path>)` with the agent scripted to end with the decision `approval` ends with `next_stage == "approval"` and `rule == 6`, with the work item not blocked and no `question` record in its journal, although the report has none of the story form's sections.
8. In that run the prompt the agent received (`agent_runtime.requests()[0].prompt`) ends with the three fact lines of the feature at `origin/main`.
9. In that run the stage protocol opened the acceptance's draft pull request titled `F0002-A0001: Acceptance of Todo service`, and the report on `origin/work-item/F0002-A0001` has the stage `approval` and that pull request's number in its state.
10. make check stays green.
11. docs: `docs/project-guide.md` states that an acceptance runs through the stage protocol, that the story form check returns no findings for a document whose state is an `AcceptanceState`, and that `TaskComposer.compose` appends the three facts at the definition's `acceptance_stage`.

## Demo

```bash
uv run python -c "
from types import SimpleNamespace
from factory.application.task import StoryFormChecker
from factory.domain.acceptance import AcceptanceState
from factory.domain.work_item import WorkItemDocument, WorkItemState
form = '# Story title\n\n## Description\n\n## Interface\n\n## Acceptance criteria\n\n## Smoke test\n\n## Journal\n'
boundaries = SimpleNamespace(git=SimpleNamespace(show_file=lambda ref, path: form))
checker = StoryFormChecker(boundaries)
body = '# Acceptance of Todo service\n\n## Journal\n'
print(checker.findings(WorkItemDocument(state=AcceptanceState(stage='acceptance'), body=body)))
print(len(checker.findings(WorkItemDocument(state=WorkItemState(stage='tests'), body=body))) > 0)
"
```
Expect: two lines: `[]` (an acceptance has no story form to meet), then `True` (the same text as a story has findings).

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names `factory.application.task` with `StoryFormChecker.findings` and `TaskComposer.compose`. It states no signature change, the import of `factory.application.acceptance` with its direction, and exact prompt composition and early-return rules. Nothing is left open.
   - Criteria: 1–9 are each testable by one test function. The rules have both sides: `findings` returns `[]` for an acceptance, and a plain state still gets findings (3) or `WorkItemFormatError` (2). `compose` appends the facts at the acceptance stage (4), but not for a story or another stage (5), and not when `acceptance_stage` is `None` (6). The run criteria 7–9 cover decision, rule, no question record, prompt tail, pull request title and state. 10 and 11 are the closing criteria.
   - Demo: the command is runnable with the stub boundaries. Its `Expect:` line states two checkable output lines (`[]`, then `True`).
   - Architecture: both modules are in the application layer, and `acceptance` does not import `task`. The change is two additions and nothing else, and F0005's tests stay as they are.
   - Scope: within F0009's scope ("the story form check skipped for it and the facts appended to the reviewer's prompt"). Nothing is in "Out of scope". FEATURE.md decision 17 matches the story.
3. tester: Wrote the red tests for the acceptance's path through the stage protocol. They are the coder's specification.

   Criterion → test:
   - criteria 1 and 3: tests/application/test_task_acceptance.py::test_only_an_acceptance_report_meets_the_story_form_without_its_sections (parametrized: `acceptance-state` gives `[]`, `plain-state` gives findings)
   - criterion 2: tests/application/test_task_acceptance.py::test_a_missing_story_form_is_an_error_only_for_a_story (parametrized: with the form removed at `origin/main`, an acceptance gives `[]` and a plain state raises `WorkItemFormatError`)
   - criterion 4: tests/application/test_task_acceptance.py::test_an_acceptance_at_the_acceptance_stage_gets_the_feature_facts_appended (prompt == `acceptance_prompt(compose_prompt(PromptFacts of the context), AcceptanceService(...).facts("F0002"))`; the last four lines are an empty line plus the three fact lines)
   - criterion 5: tests/application/test_task_acceptance.py::test_no_facts_are_appended_off_the_acceptance_stage_or_for_a_story (parametrized: a story at `acceptance`, a story at `intake`, an acceptance at `review`)
   - criterion 6: tests/application/test_task_acceptance.py::test_without_an_acceptance_stage_the_prompt_is_unchanged (parametrized: acceptance and story, `acceptance_stage=None`)
   - criterion 7: tests/application/test_stage_run_acceptance.py::test_an_acceptance_reaches_approval_although_its_report_has_no_story_sections
   - criterion 8: tests/application/test_stage_run_acceptance.py::test_the_reviewer_prompt_ends_with_the_feature_facts_at_main
   - criterion 9: tests/application/test_stage_run_acceptance.py::test_the_protocol_opens_the_acceptance_pull_request_and_records_it (title, branch, number equal to the report's, and the pushed state has stage `approval` and that pull request number). The test does not assert `draft`: the pull request's draft flag after the run is not something the criterion fixes.

   Files created:
   - tests/application/test_task_acceptance.py
   - tests/application/test_stage_run_acceptance.py

   Both push the feature `F0002-todo` themselves (`feature.md` "# Todo service", two stories under `done/`). The run tests open the acceptance with `AcceptanceService.open` and install agents for every role of `PIPELINE_YAML`.

   Test results: every module imports, because nothing new is imported. `make test` gives 6 failures, all for the right reason:
   - The run reaches no `approval`: decision rule 1 turns the decision into a question.
   - The prompt lacks the fact lines.
   - The checker gives findings or raises for an `AcceptanceState`.

   The story-side and unchanged-prompt rows pass already, as they should. `make lint` is green.

   `make lint`: lint: green
   `make test`: FAILED tests/application/test_task_acceptance.py::test_an_acceptance_at_the_acceptance_stage_gets_the_feature_facts_appended
4. coder: An acceptance now runs its stage through the stage protocol. The only file changed is `src/factory/application/task.py`.
   - `StoryFormChecker.findings` returns `[]` when `document.state` is an `AcceptanceState`. It does this before reading the form, so a missing form raises no `WorkItemFormatError` for an acceptance. Every other document gets the F0005 behaviour unchanged.
   - `TaskComposer.compose` gets its prompt from a new private method, `_prompt`. When the stage is `definition.acceptance_stage` and `is_acceptance(work_item)`, `_prompt` wraps `compose_prompt(facts)` in `acceptance_prompt(..., AcceptanceService(boundaries, definition).facts(feature_of(work_item)))`. Any other case, including `acceptance_stage is None`, gets the unchanged prompt.
   - `task` now imports `factory.application.acceptance`. `acceptance` does not import `task`, and import-linter is green.

   Design: the checker tells an acceptance apart by the type of the document's state, as the Interface says. I did not test the work item id with `is_acceptance` because the checker receives only the document. The choice of prompt sits in two small private methods, `_prompt` and `_is_acceptance_run`. I did not add a branch inside `compose`, which now differs from before by one line.

   Commits:
   - ba5413d (feat)
   - 6141647 (refactor): drops a redundant `acceptance_stage is not None` guard, because a stage name never equals `None`.

   `make check` is green with coverage at 99.53 %. Line 128 of `task.py` is not covered: it is the `ValueError` that `_role_name` raises for an unknown stage. It was uncovered before this ticket, and I did not touch it.

   Process note: my first `make check` ran longer than the tool's 2-minute timeout and was moved to the background, which `CLAUDE.md` forbids. It finished green. The final `make check`, chained with the refactor commit, ran in the foreground and was green.

   `make check`: check: green
5. reviewer: Review, round 0. I read the ticket and `git diff main...HEAD -- . ':!factory'`: `src/factory/application/task.py` plus the two new test modules. The code changes match the Interface: an early `[]` for an `AcceptanceState` in `StoryFormChecker.findings`, and `TaskComposer._prompt` / `_is_acceptance_run` gate `acceptance_prompt(...)` on `acceptance_stage` and `is_acceptance`. `acceptance` does not import `task`. The coder's entry reports `make check` green. Criteria 1–8 each have a test that checks what the criterion says. Criterion 9 does not, so I stopped at checklist group 1.

   1. `tests/application/test_stage_run_acceptance.py::test_the_protocol_opens_the_acceptance_pull_request_and_records_it`: criterion 9 says the protocol opened the acceptance's *draft* pull request, but the test never checks the draft flag.
      - The tester's log entry says the flag after the run is not fixed. The code says otherwise: `opening.py:114` creates the pull request with `draft=True`. The only code that sets it ready is the approval hand-over (`handlers/hand_over.py:69`, `acceptance.py:231`), and `StageRunner` does not reach either. So `FakeHostingService.pull_requests()[0].draft` is `True` after the run.
      - Fix: add `assert pull_request.draft` to that test. The coder may not edit tests (R9), so the coder should end with `tests` and name this one-line addition for the tester.

   Open: nothing beyond finding 1. I did not judge the later checklist groups (architecture, security, quality, hygiene), since the review stops at the first failing group.
6. coder: Round 1. The review has one finding, and it is a change to a test, which the coder may not make (R9). So I am handing it back to the tester. I made no code changes this round: the code was not part of the finding.

   Test change for the tester: in `tests/application/test_stage_run_acceptance.py::test_the_protocol_opens_the_acceptance_pull_request_and_records_it`, add `assert pull_request.draft` after the title and branch checks. This makes the test check that the pull request is a draft, which criterion 9 requires.

   The reviewer says this holds after the run, and I did not re-check it. Their reasons: `opening.py:114` creates the pull request with `draft=True`. Only the approval hand-over (`handlers/hand_over.py:69`, `acceptance.py:231`) sets it ready, and `StageRunner` never reaches that code.

   Open: nothing else.
7. tester: Test change, round 1, as the coder's entry 6 names it after review finding 1.

   - Changed: `tests/application/test_stage_run_acceptance.py::test_the_protocol_opens_the_acceptance_pull_request_and_records_it` now has `assert pull_request.draft` right after the title and branch checks. It was only that one line.
   - Why: criterion 9 says the protocol opened the acceptance's *draft* pull request, and the test did not check the draft flag. In entry 3 I wrote that the flag after the run was not fixed by the criterion. That was wrong: the criterion names the draft.

   `make test` is green with coverage at 99.53 %, so the code already meets the stronger test. Nothing else is open.

   `make lint`: lint: green
   `make test`: test: green
8. coder: Round 1, after the tester's change. The only review finding asked for a test change. The tester has now made it in entry 7: `assert pull_request.draft` in `tests/application/test_stage_run_acceptance.py::test_the_protocol_opens_the_acceptance_pull_request_and_records_it`. That leaves nothing for the code to do, so this round has no code change and no commit. The implementation is the one from entry 4: `src/factory/application/task.py`, commits ba5413d (feat) and 6141647 (refactor).

   I ran `make check` in the foreground on the committed state and it is green, with coverage at 99.53 %. The stronger test passes against the existing code. Refactor: nothing to change, since the diff is the same one the reviewer already read.

   Open: nothing.

   `make check`: check: green
9. reviewer: Review, round 1. No findings.

   I read the ticket and `git diff main...HEAD -- . ':!factory'`. The diff covers `src/factory/application/task.py` and the two new modules, `tests/application/test_task_acceptance.py` and `tests/application/test_stage_run_acceptance.py`.

   - Acceptance criteria: round 0's only finding is fixed. `test_the_protocol_opens_the_acceptance_pull_request_and_records_it` now asserts `pull_request.draft` (tester, entry 7). Each of criteria 1–9 has a test that checks what the criterion says:
     - Both sides of the form-check rule are rows of one parametrized test: an acceptance gives `[]` and a plain state gives findings (1/3). With the form missing, an acceptance gives `[]` and a plain state raises `WorkItemFormatError` (2).
     - The prompt tests check:
       - exact equality with `acceptance_prompt(compose_prompt(...), facts("F0002"))` plus the four-line tail (4);
       - no `Archived stories:` line for a story at `acceptance`, a story at `intake`, or an acceptance at `review` (5);
       - the unchanged prompt when `acceptance_stage=None` (6).
     - The run tests cover approval with rule 6, not blocked and no question record (7); the prompt ending with the fact lines (8); and the draft pull request's title, branch and number, with stage `approval` and the pull request number in the pushed state (9).
     - The Interface states no numeric limits. The coder's entry 8 reports `make check` green.
   - Architecture: `task` imports `factory.application.acceptance` and domain modules only. Both are in the application layer. `acceptance` does not import `task`, directly or through `stage.py`, and import-linter is green.
   - Security: no strings built into shell or SQL commands, no suppression markers, no secrets. Test hex values are not used.
   - Quality: `findings` returns early for an `AcceptanceState`, as the Interface says. Its docstring explains why. `compose` changes by one line. The choice of prompt sits in the private methods `_prompt` and `_is_acceptance_run`. It reuses `is_acceptance`, `feature_of`, `acceptance_prompt` and `AcceptanceService.facts` rather than copying them. There is no dead code.
   - Ticket hygiene: the log names the main decisions and what was rejected:
     - the checker tells an acceptance apart by the type of the document's state, not by the work item id;
     - the coder chose private methods over a branch inside `compose`;
     - the coder dropped the redundant `None` guard in 6141647.

     The Assignment matches what was built. Criterion 11 still describes what `docs/project-guide.md` must say.

   Open: nothing.
