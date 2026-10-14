---
stage: accept
pr: 58
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Agent definitions, the prompt and the allowed decisions

## Assignment (as of log entry 1)

Build what a stage needs before its agent runs. The stage's agent definition is read from the agent home through `AgentDefinitionReader`. The prompt is composed from fixed lines. The allowed decisions are computed once from the pipeline definition (the stage's `next`, then `question`), so that the prompt's line and `AgentRunRequest.allowed_decisions` come from the same list; the runtime builds its outcome schema from that list and the stage protocol validates the agent's decision against it later (S0005). The story form check that a stage runs before and after the agent is built here too (`StoryFormChecker`); it reads the project's form from `origin/main`, so nothing an agent writes in the work tree can change it. The first stage's prompt carries the form's findings (kept thing 9), and the tester's prompt names an approved test change recognised from the journal's data (the speaker of the last `result` record), never from its text. The agent run's environment is not decided here: the caller gives it to `TaskComposer`, which passes it into the request unchanged (F0001 decision 17; F0006's wiring supplies a `PATH` that holds `factory-guard` and a `HOME`, F0010 scrubs it). The names `TaskComposer`, `TaskContext` and the module `factory.application.task` are the interface sheet's; the glossary's word for the text they compose is the prompt. v1's decision `stuck` does not exist here: an agent that cannot finish ends with `question`. Covers no acceptance condition alone; it prepares GH1.1 (S0003) and GH2.5 (S0004). Keeps kept things 1 (code decides, the agent judges), 5 (the form is checked before and after), 9 and 10 (`question` is always allowed).

## Interface

`src/factory/domain/prompts.py`

```python
TESTER_ROLE = "tester"
CODER_ROLE = "coder"
END_LINE = (
    "End with your decision and your journal entry; "
    "the factory commits, pushes and moves the work item."
)

class PromptFacts(BaseModel):
    work_item: WorkItemId
    path: str
    stage: Name
    allowed_decisions: list[str]
    branch: str
    pull_request: PositiveInt
    round: NonNegativeInt
    test_change_entry: PositiveInt | None = None
    findings: list[FormFinding] | None = None

def allowed_decisions(next_stages: Sequence[str]) -> list[str]: ...
def compose_prompt(facts: PromptFacts) -> str: ...
```

`src/factory/application/task.py`

```python
class TaskContext(BaseModel):
    work_item: WorkItemId
    path: str
    stage: Name
    document: WorkItemDocument
    branch: str
    pull_request: PositiveInt
    findings: list[FormFinding]
    guard: GuardSettings

class StoryFormChecker:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def findings(self, document: WorkItemDocument) -> list[FormFinding]: ...

class TaskComposer:
    def __init__(
        self,
        boundaries: Boundaries,
        definition: PipelineDefinition,
        environment: Mapping[str, str],
    ) -> None: ...
    def agent(self, stage: str) -> AgentDefinition: ...
    def compose(self, context: TaskContext, agent: AgentDefinition) -> AgentRunRequest: ...
```

Types: `Mapping` from `collections.abc`, `FormFinding` from `factory.domain.story_form`, `GuardSettings`, `AgentDefinition`, `AgentRunRequest` and `QUESTION` from `factory.domain.agent_runs`, `WorkItemDocument` from `factory.domain.work_item`, `PipelineDefinition` from `factory.domain.pipeline_definition`, `Boundaries` from `factory.application.boundaries`. All models are frozen and forbid unknown keys, like every DTO of the interface sheet.

- `allowed_decisions(next_stages)` returns the names of `next_stages` in their order, then `QUESTION`; `QUESTION` is last and always present.
- `compose_prompt` returns these lines joined by one newline, without a trailing newline, in this order: `Work item: <path>`, `Id: <work_item>`, `Stage: <stage>`, `Allowed decisions: <the decisions joined by ", ">`, `Branch: <branch>`, `Pull request: <pull_request>`, `Round: <round>`, the `Mode:` line, the `Format check` line, `END_LINE`.
- The `Mode:` line is present exactly when `test_change_entry` is not `None`; it reads `Mode: a test change the human approved; the coder's journal entry <test_change_entry> names it.`
- The `Format check` line is present exactly when `findings` is not `None`: `Format check: passed` for an empty list, otherwise `Format check found: 1. <message> 2. <message>`, numbered from 1, one space between items, no final full stop.
- `StoryFormChecker.findings` reads the form with `Git.show_file("origin/main", STORY_FORM_FILE)`, never from the work tree, and returns `check_story_form(document, form, folder="in-progress")`. A form that is absent at `origin/main` raises `WorkItemFormatError` whose `path` is `STORY_FORM_FILE`.
- `TaskComposer.agent(stage)` returns `AgentDefinitionReader.read(role)` for the role of the stage in the pipeline definition. A stage without a role raises `ValueError` naming the stage. An agent file that does not exist lets `AgentDefinitionMissing` propagate.
- `TaskComposer.compose` returns an `AgentRunRequest` with `agent` as given, `prompt` from `compose_prompt`, `allowed_decisions` from `allowed_decisions(stage.next)`, `time_limit = timedelta(minutes=role.time_limit)`, `working_directory = boundaries.checkout`, `environment = dict(<the environment given to TaskComposer>)` (a copy, passed on unchanged: nothing is added, removed or scrubbed), `guard = context.guard` and `os_user = None`.
- The prompt's facts: `round` is `context.document.state.round`; `findings` is `context.findings` when `context.stage` is `definition.first_stage()` and `None` at every other stage; `test_change_entry` is the number of `last_record(context.document, kind="result")` when the stage's role is `TESTER_ROLE` and that record's speaker is `CODER_ROLE`, else `None`. The last `result` record is used, not the last record, so a later `stall`, `crash` or `comment` record (a tester that stalled, a copied human comment) does not hide the test change from the tester's next attempt. The journal's records are read through `last_record`; the text of an entry is never read.

Tests: `tests/domain/test_prompts.py`, `tests/application/test_task.py`. The latter builds the agent home under `tmp_path` with one agent file per role under test and the project's form on the remote's `main`, as the `boundaries` fixture does. `PromptFacts` and `TaskContext` refuse what their types refuse (`round` below 0, a `pull_request` or `test_change_entry` below 1, an unknown key); the limits are tested on both sides (criterion 22).

## Acceptance criteria

1. `allowed_decisions(["review", "doing"])` returns `["review", "doing", "question"]`: the stage's `next` in its order, then `question`.
2. `allowed_decisions([])` returns `["question"]`: `question` is allowed at every stage.
3. `compose_prompt` for work item `F0001-S0003`, path `factory/features/F0001-demo/in-progress/F0001-S0003-demo.md`, stage `doing`, allowed decisions `["review", "tests", "question"]`, branch `work-item/F0001-S0003`, pull request 7, round 1, no findings and no test change returns exactly these 8 lines in order: `Work item: <the path>`, `Id: F0001-S0003`, `Stage: doing`, `Allowed decisions: review, tests, question`, `Branch: work-item/F0001-S0003`, `Pull request: 7`, `Round: 1`, and `END_LINE`.
4. With `findings=[]` the prompt has the line `Format check: passed` directly after the `Round:` line and before `END_LINE`.
5. With two findings whose messages are `a` and `b` the prompt has the single line `Format check found: 1. a 2. b`.
6. With `findings=None` no line of the prompt starts with `Format check`.
7. With `test_change_entry=4` the prompt has the line `Mode: a test change the human approved; the coder's journal entry 4 names it.` after the `Round:` line and before the `Format check` line; with `None` no line starts with `Mode:`.
8. `compose` for the first stage of the pipeline definition puts the context's findings into the prompt as a `Format check` line; for a later stage, with the same non-empty findings in the context, the prompt has no `Format check` line.
9. `compose` for a stage whose role is `tester`, with a journal whose last `result` record has speaker `coder` and number 5, returns a prompt with the `Mode:` line naming entry 5.
10. `compose` returns no `Mode:` line for a tester stage whose last `result` record has speaker `tester` even when that entry's text starts with `coder:`, none for a tester stage whose journal has no `result` record, and none for a coder stage whose last `result` record has speaker `coder`.
11. After the coder's `result` record number 5 the journal holds a `factory` `stall` record (number 6, a stalled tester attempt) and a `human` `comment` record (number 7): `compose` for the tester stage still returns the `Mode:` line naming entry 5.
12. The request's `allowed_decisions` equals `allowed_decisions(stage.next)` for the stage, and its prompt equals `compose_prompt` of the facts taken from the context (`work_item`, `path`, `stage`, `branch`, the context's `pull_request`, and the document's `round`: a state with `round` 2 gives the line `Round: 2`), so its `Allowed decisions:` line equals those decisions joined by `", "`.
13. The request's `time_limit` is `timedelta(minutes=25)` for a role defined with `time_limit: 25` and `timedelta(minutes=40)` for a role that sets none.
14. The request's `agent` equals the definition passed in, `working_directory` equals `boundaries.checkout`, `guard` equals the context's guard and `os_user` is `None`.
15. The request's `environment` equals the mapping given to `TaskComposer` (for `{"PATH": "/opt/guard", "HOME": "/home/factory"}` the request holds those two entries and no other).
16. `agent("tests")` returns the agent definition whose `name` is the stage's role, read from the agent home.
17. `agent` for a stage that has no role (the approval stage) raises `ValueError` whose message names the stage.
18. `agent` for a role whose agent file does not exist raises `AgentDefinitionMissing` naming the role.
19. `StoryFormChecker.findings` returns `[]` for a complete story (a title line, every section of the form, criteria ending with `make check` … `green` and `docs:`, a smoke-test code block followed by `Expect:`, and a state whose journal records match the entries of its `## Journal` section), and a non-empty list for the same story without its `## Smoke test` section.
20. The form is read at `origin/main`: after the human pushes a form with one more required section to `main` and the checkout fetches, a story without that section gets a finding; a change to `factory/story-form.md` in the work tree alone changes nothing.
21. `findings` raises `WorkItemFormatError` with `path == "factory/story-form.md"` when the form is absent at `origin/main`.
22. The models' limits hold on both sides: `PromptFacts` accepts `round=0` and refuses `round=-1`, accepts `pull_request=1` and refuses `pull_request=0`, accepts `test_change_entry=1` and refuses `test_change_entry=0`; `TaskContext` accepts `pull_request=1` and refuses `pull_request=0`; both are frozen (assigning to `round` of `PromptFacts` and to `branch` of `TaskContext`, through `setattr` with the field's name in a variable, raises `ValidationError`) and each refuses an unknown key (built through a variable typed `type[BaseModel]`).
23. make check stays green.
24. docs: `docs/project-guide.md` states how a stage's prompt is composed (the lines and their order, that `question` is always allowed and `stuck` is not a decision, that the Format check line goes to the first stage, that the Mode line is decided from the last `result` record's speaker) and that the story form is read from `origin/main`, and that the request's environment is the caller's, passed unchanged; `docs/decisions.md` records why the prompt, the request and the validation share one list of decisions.

## Demo

```bash
uv run python -c "
from factory.domain.prompts import PromptFacts, allowed_decisions, compose_prompt
from factory.domain.story_form import FormFinding
print(allowed_decisions(['review', 'doing']))
facts = PromptFacts(work_item='F0001-S0003', path='factory/features/F0001-demo/in-progress/F0001-S0003-demo.md', stage='intake', allowed_decisions=allowed_decisions(['tests']), branch='work-item/F0001-S0003', pull_request=7, round=0, findings=[FormFinding(line=None, message='the criteria are not numbered'), FormFinding(line=None, message='the Journal section is missing')])
print(compose_prompt(facts))
"
```
Expect: 10 lines. Line 1 is `['review', 'doing', 'question']`. Lines 2 to 10 are `Work item: factory/features/F0001-demo/in-progress/F0001-S0003-demo.md`, `Id: F0001-S0003`, `Stage: intake`, `Allowed decisions: tests, question`, `Branch: work-item/F0001-S0003`, `Pull request: 7`, `Round: 0`, `Format check found: 1. the criteria are not numbered 2. the Journal section is missing`, and the closing line `End with your decision and your journal entry; the factory commits, pushes and moves the work item.`

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: concrete modules and signatures (`factory/domain/prompts.py`, `factory/application/task.py`), types and imports named. Each stated behaviour is pinned down: line order, the `Mode:` and `Format check` text, the `show_file("origin/main", STORY_FORM_FILE)` read, the `ValueError` for a stage without a role, the request fields, and the rule for which `result` record sets the test change.
   - Criteria: each is testable by one test function. Every Interface comment has a criterion: allowed decisions 1-2, prompt lines 3-7, findings only at the first stage 8, `Mode:` 9-11, request fields 12-15, `agent` 16-18, form checker 19-21. Failing sides are covered: a tester with a `tester`-speaker or missing `result` record (10), a stage without a role (17), a missing agent file (18), a missing form (21), a form change in the work tree only (20), and both sides of every model limit with unknown keys and frozen models (22).
   - Demo: a runnable `uv run python -c` command. The Expect line (10 lines: the list, then 9 prompt lines) matches what the Interface produces.
   - Architecture: the pure prompt rules are in the domain layer; `TaskComposer` and `StoryFormChecker` are in the application layer. Git is reached through the `Git` interface and the agent home through `AgentDefinitionReader`, so no layer rule is broken.
   - Scope: inside F0005's scope (agent definitions, prompt, allowed decisions, environment passed unchanged, form check). The environment's content, the claim and stalls are left to other stories, as the feature says.
3. tester: Wrote the red tests for every criterion from the Interface and the criteria. The tests do not interpret anything the criteria leave open.

   Which test covers each criterion:
   - criterion 1: tests/domain/test_prompts.py::test_allowed_decisions_are_the_next_stages_in_order_then_question
   - criterion 2: tests/domain/test_prompts.py::test_question_is_allowed_at_a_stage_without_next
   - criterion 3: tests/domain/test_prompts.py::test_the_prompt_holds_the_facts_line_by_line_and_ends_with_the_end_line. The wording of END_LINE is checked separately in test_the_end_line_says_what_the_factory_does_after_the_agent.
   - criterion 4: tests/domain/test_prompts.py::test_no_findings_give_a_passed_format_check_after_the_round
   - criterion 5: tests/domain/test_prompts.py::test_findings_are_numbered_on_one_format_check_line
   - criterion 6: tests/domain/test_prompts.py::test_without_findings_the_prompt_has_no_format_check_line
   - criterion 7: tests/domain/test_prompts.py::test_a_test_change_adds_the_mode_line_between_round_and_format_check and ::test_without_a_test_change_the_prompt_has_no_mode_line
   - criterion 8: tests/application/test_task.py::test_the_first_stage_gets_the_findings_and_a_later_stage_does_not
   - criterion 9: tests/application/test_task.py::test_the_tester_gets_the_mode_line_after_a_coder_result
   - criterion 10: tests/application/test_task.py::test_the_mode_line_comes_only_from_a_coder_result_at_a_tester_stage. It is parametrized over three cases: the tester spoke last with text starting "coder:", there is no result record, and a coder stage.
   - criterion 11: tests/application/test_task.py::test_a_later_stall_and_comment_do_not_hide_the_test_change
   - criterion 12: tests/application/test_task.py::test_the_request_shares_the_allowed_decisions_and_the_facts_of_the_context
   - criterion 13: tests/application/test_task.py::test_the_time_limit_is_the_roles_minutes. The tester's time_limit is set to 25 in a copy of PIPELINE_YAML; the coder sets none, so 40.
   - criterion 14: tests/application/test_task.py::test_the_request_carries_the_agent_checkout_and_guard_without_os_user
   - criterion 15: tests/application/test_task.py::test_the_request_holds_the_given_environment_unchanged
   - criterion 16: tests/application/test_task.py::test_agent_reads_the_definition_of_the_stages_role
   - criterion 17: tests/application/test_task.py::test_agent_for_a_stage_without_a_role_names_the_stage
   - criterion 18: tests/application/test_task.py::test_agent_for_a_role_without_an_agent_file_is_missing. Stage review, role reviewer, which is not installed.
   - criterion 19: tests/application/test_task.py::test_the_form_check_finds_nothing_only_in_a_complete_story
   - criterion 20: tests/application/test_task.py::test_the_form_is_read_at_main_on_the_remote_not_in_the_work_tree
   - criterion 21: tests/application/test_task.py::test_a_form_absent_at_main_is_a_format_error. The human's clone removes the form with real git, pushes main, and the checkout fetches.
   - criterion 22: tests/domain/test_prompts.py::test_prompt_facts_hold_their_limits_on_both_sides, ::test_prompt_facts_are_frozen, ::test_prompt_facts_refuse_an_unknown_key; tests/application/test_task.py::test_task_context_holds_the_pull_request_limit_on_both_sides, ::test_task_context_is_frozen, ::test_task_context_refuses_an_unknown_key
   - criteria 23 and 24: no test. They are make check and docs.

   Files created: tests/domain/test_prompts.py and tests/application/test_task.py.

   Run results:
   - `make test` (one run) stops with collection errors in both new files, which is the expected red. The runner could not import the modules factory.domain.prompts and factory.application.task.
   - `make lint` is green. ruff format reflowed test_task.py once.

   Notes for the coder:
   - The compose tests do not install agent files; only the `agent(...)` tests do.
   - The environment test passes {"PATH": "/opt/guard", "HOME": "/home/factory"} to TaskComposer.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built the prompt, the allowed decisions and the request for a stage's agent run. The tester's tests pass without any change, and `make check` is green (total coverage 99.58 %).

   What was built:
   - `src/factory/domain/prompts.py` holds `TESTER_ROLE`, `CODER_ROLE`, `END_LINE`, `PromptFacts` (frozen, forbids unknown keys), `allowed_decisions` and `compose_prompt`.
     - `allowed_decisions` returns the `next` stages followed by `QUESTION`.
     - `compose_prompt` puts the lines in a fixed order. The `Mode:` line is added only when `test_change_entry` is not None, and the `Format check` line only when `findings` is not None.
   - `src/factory/application/task.py` holds `TaskContext`, `StoryFormChecker` and `TaskComposer`.
     - `StoryFormChecker` reads the form with `git.show_file(FORM_REF, STORY_FORM_FILE)`, where `FORM_REF = origin/main`. If the form is absent it raises `WorkItemFormatError(path=STORY_FORM_FILE)`.
     - `TaskComposer.compose` computes the decisions once and gives the same list to both the prompt facts and `AgentRunRequest.allowed_decisions`. It passes `dict(environment)` on unchanged.
     - Findings go only to `definition.first_stage()`.
     - The test change entry comes from `last_record(document, kind="result")`: it is set when the stage's role is `tester` and that record's speaker is `coder`. The text of an entry is never read.

   Commits:
   - a3e3fcf: the feature.
   - 6bb8ef5: refactor. The error for a stage without a role is now raised in one helper, `_role_name`, which both `agent` and the time-limit lookup use. Before, the same `ValueError` was raised in two places.

   Design decision: the `Format check` and `Mode:` lines are built by small private helpers in the domain module. I did not put a conditional list comprehension inside `compose_prompt`, because the line order stays easier to read as plain appends.

   Added beyond the interface: `compose` raises `WorkItemFormatError("the document has no state", context.path)` when the document has no state. `WorkItemDocument.state` is optional and `mypy --strict` refuses `.state.round` without a check. The error follows the existing `_state_of` in `factory.domain.journal`. No test exercises this branch (`task.py:118`).

   Noticed but not touched:
   - `TaskComposer.compose` for a stage without a role raises `ValueError`, the same as `agent`. No criterion covers this.
   - An unknown stage name raises `KeyError` from the definition's `stages` dict.

   `make check`: check: green
5. reviewer: No findings.

   What I reviewed: `git diff main...HEAD -- . ':!factory'`, which covers `src/factory/domain/prompts.py`, `src/factory/application/task.py`, `tests/domain/test_prompts.py` and `tests/application/test_task.py`. I read the code against the Interface and all 24 criteria.

   - Criteria: each of criteria 1–22 has a test that checks what the criterion says.
     - Failing sides are tested: a stage without a role (17), a missing agent file (18), a form absent at `origin/main` (21), and a form changed only in the work tree (20).
     - Both sides of every model limit are tested (22): `round` 0/-1, `pull_request` 1/0, `test_change_entry` 1/0. The tests also cover frozen models and unknown keys.
     - The coder's entry says the factory's `make check` was green.
   - Architecture: `prompts.py` is in the domain layer and uses only pydantic and domain imports. `task.py` is in the application layer. It reaches git only through `Boundaries.git.show_file` and the agent home only through `AgentDefinitionReader`, and it uses no concrete tool.
   - Shared decisions: `compose` computes `allowed_decisions` once and passes the same list to `PromptFacts` and to `AgentRunRequest`.
   - Environment: copied with `dict(...)` and passed on unchanged.
   - Mode line: decided from `last_record(kind="result")` and its speaker. The entry text is never read.
   - Security and quality: no secrets, no shell, no suppression markers. Names, docstrings and why-comments (`FORM_REF`, the last-result rule) are as `CLAUDE.md` asks.

   Considered and not raised:
   - `_round` raises `WorkItemFormatError` when the document has no state (`task.py`). This is beyond the Interface and no test covers it. It is not a finding: `mypy --strict` needs the check, it copies `journal._state_of`, and the coder disclosed it. The Interface does not describe a stateless document at all; a later story that relies on this case should state it.
   - `compose` raises `KeyError` for an unknown stage and `ValueError` for a stage without a role. The Interface does not state either rule, so neither is a gap against this story.
6. documenter: wrote the documentation for criterion 24; `make check` is green.

   Files changed:
   - `docs/project-guide.md`: new section "The prompt and the request for a stage", placed after "The agent definition reader". It covers:
     - the shared decisions list, with `question` always allowed and `stuck` not a decision;
     - the prompt lines and their order in a table;
     - the Format check line going to the first stage only;
     - the Mode line decided from the speaker of the last `result` record;
     - the request fields, with the environment copied and passed on unchanged;
     - `agent()` errors;
     - the story form read from `origin/main`.
   - `docs/decisions.md`: new entry "The prompt, the request and the validation share one list of decisions". It gives the reasons and the alternatives rejected.

   Cross-read against the diff and found current: the "AgentRunRequest" and "agent definition reader" parts of `docs/project-guide.md`, and the story form check section.

   I did not run the examples, because I wrote none. The demo in the ticket is the coder's and the tester's to run.

   Not touched: `README.md` and `docs/operator-guide.md`, which this story does not change. The mention in the project guide that F0010 scrubs the environment comes from the Assignment.

   No findings for the coder.

   `make check`: check: green
7. demo: ran the one command under `## Demo` from the repository root, exactly as written. It exited with code 0. No findings.

   Command 1 (`uv run python -c "…allowed_decisions…compose_prompt…"`), output:

   ```
   ['review', 'doing', 'question']
   Work item: factory/features/F0001-demo/in-progress/F0001-S0003-demo.md
   Id: F0001-S0003
   Stage: intake
   Allowed decisions: tests, question
   Branch: work-item/F0001-S0003
   Pull request: 7
   Round: 0
   Format check found: 1. the criteria are not numbered 2. the Journal section is missing
   End with your decision and your journal entry; the factory commits, pushes and moves the work item.
   ```

   Met its `Expect:` line. The output has 10 lines and each one matches the expected text exactly:
   - line 1 is the list with `question` last;
   - lines 2–8 are the facts, in order;
   - line 9 is the numbered `Format check found:` line, with a single space between the items and no final full stop;
   - line 10 is `END_LINE`.

   Checked against the criteria:
   - The demo is consistent with criteria 1, 2 (`question` appended after the stage's `next`), 3 (line order), 5 (format of the findings line) and 7 (no `Mode:` line when `test_change_entry` is None).
   - No criterion is contradicted.
   - Criteria 8–22 are for `TaskComposer`, `StoryFormChecker` and the model limits. This demo does not exercise them; they are covered by the tests named in entry 3.
