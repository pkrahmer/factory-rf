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
12. The request's `allowed_decisions` equals `allowed_decisions(stage.next)` for the stage, and its prompt's `Allowed decisions:` line equals those decisions joined by `", "`.
13. The request's `time_limit` is `timedelta(minutes=25)` for a role defined with `time_limit: 25` and `timedelta(minutes=40)` for a role that sets none.
14. The request's `agent` equals the definition passed in, `working_directory` equals `boundaries.checkout`, `guard` equals the context's guard and `os_user` is `None`.
15. The request's `environment` equals the mapping given to `TaskComposer` (for `{"PATH": "/opt/guard", "HOME": "/home/factory"}` the request holds those two entries and no other).
16. `agent("tests")` returns the agent definition whose `name` is the stage's role, read from the agent home.
17. `agent` for a stage that has no role (the approval stage) raises `ValueError` whose message names the stage.
18. `agent` for a role whose agent file does not exist raises `AgentDefinitionMissing` naming the role.
19. `StoryFormChecker.findings` returns `[]` for a story that has every section of the form, and a non-empty list for a story without its `## Smoke test` section.
20. The form is read at `origin/main`: after the human pushes a form with one more required section to `main` and the checkout fetches, a story without that section gets a finding; a change to `factory/story-form.md` in the work tree alone changes nothing.
21. `findings` raises `WorkItemFormatError` with `path == "factory/story-form.md"` when the form is absent at `origin/main`.
22. The models' limits hold on both sides: `PromptFacts` accepts `round=0` and refuses `round=-1`, accepts `pull_request=1` and refuses `pull_request=0`, accepts `test_change_entry=1` and refuses `test_change_entry=0`; `PromptFacts` and `TaskContext` each refuse an unknown key (built through a variable typed `type[BaseModel]`).
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
