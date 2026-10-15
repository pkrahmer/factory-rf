---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The acceptance stage and the acceptance reviewer's facts

## Assignment (as of log entry 1)

Open a due acceptance and give the acceptance reviewer what it needs. A due acceptance is opened by pushing a branch `work-item/F0001-A0001` that holds one new file, the report's head: the state (stage = the pipeline definition's `acceptance_stage`, `stories` = the archived stories, counters at their initial values), the title taken from the feature file (`# Acceptance of <feature title>`) and an empty `## Journal` section. That is all the opening does: the claim, the draft pull request and the agent run belong to the stage protocol, which meets the acceptance as an ordinary work item at its stage, read from its branch (S0008 makes the watcher see it, S0009 runs it). The reviewer's prompt gets three facts computed by code, not by the agent: the archived stories, the next free story number and the cost of the stories, read from the cost records of the archived stories; this story builds them and `acceptance_prompt`, and S0009 has the stage protocol append them. The reviewer may write only its report and new stories in the feature's backlog: that is the role's write paths in the pipeline definition, expanded by F0004's `WritePathService` as for any work item, and this story shows it for an acceptance. Each acceptance has its own report file and so its own cost line, which counts only its own records (GH4.4), shown with F0005's `BillService`. Covers GH4.4; keeps kept thing 19 (the acceptance judges the whole and proposes stories that only the human starts), kept thing 2 (proposed stories only as backlog files) and kept thing 20 (each acceptance costed). The factory opens the acceptance without a `created` entry of a human: its journal starts with the stage protocol's `started` entry. The units here are `acceptance_prompt` and the service that opens and reads. `AcceptanceDueHandler` is registered for `acceptance_due` in `factory.entry.wiring.build_handlers` by S0010, which also takes the kind out of `NOT_YET_HANDLED`. Criteria 16 to 18 pass at once against code that F0004 and F0005 built; they show that the reviewer's write paths and the own cost line work for an acceptance's file and fail the day either changes.

## Interface

`src/factory/domain/acceptance.py` (grown)

```python
class AcceptanceFacts(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    archived: list[WorkItemId]
    next_story: WorkItemId
    cost_line: str

    def lines(self) -> list[str]: ...

def acceptance_facts(files: FeatureFiles, cost_line: str) -> AcceptanceFacts: ...
def acceptance_prompt(base: str, facts: AcceptanceFacts) -> str: ...
def acceptance_head(feature_title: str, stage: str, stories: Sequence[WorkItemId]) -> WorkItemDocument: ...
```

`src/factory/application/acceptance.py` (new)

```python
class OpenedAcceptance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: WorkItemId
    branch: str
    path: str
    commit: CommitId

class AcceptanceService:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def open(self, feature: FeatureId) -> OpenedAcceptance: ...
    def facts(self, feature: FeatureId) -> AcceptanceFacts: ...

class AcceptanceDueHandler(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

`CommitId` is in `factory.domain.git`, `CannotHandle`, `WorkItemFormatError` and `PushFailed` in `factory.domain.errors`, `JOURNAL` in `factory.domain.sections`.

Rules:

- `acceptance_facts(files, cost_line)`: `archived` is `story_file_ids(files.done)`; `next_story` is `"<feature>-S<n>"` with `n` the highest story number among the story files of `backlog`, `in_progress` and `done`, plus one, written with four digits; with no story file it is number 1; when the highest number is 9999 it raises `ValueError`. `.gitkeep`, notes and an acceptance's report file do not count.
- `AcceptanceFacts.next_story` holds a story id only: a validator refuses an acceptance id with a `ValidationError`.
- `AcceptanceFacts.lines()` is exactly three lines: `Archived stories: ` followed by the ids joined by `, `; `Next free story number: ` and the id; `Cost of the stories: ` and `cost_line`.
- `acceptance_prompt(base, facts)` is `base`, an empty line, then the three lines, joined with `\n`.
- `acceptance_head(feature_title, stage, stories)` returns a `WorkItemDocument` whose state is an `AcceptanceState` with `initial_state(stage)`'s values (every counter 0, no claim, no pull request, empty journal), `stories` as given and `outcome` `None`, and whose body is exactly `# Acceptance of <feature_title>`, an empty line, `## Journal` and a final newline. The heading is built from `JOURNAL` (`f"## {JOURNAL}"`), never written as a literal: F0005-S0009's search test (`tests/test_no_journal_reading.py`) allows the literal `Journal` only in `factory.domain.sections` and `JOURNAL` only in a short list of modules. This story adds `"factory.domain.acceptance"` to the set `ALLOWED["JOURNAL"]` of F0005-S0009's `tests/test_no_journal_reading.py`, with the human's leave (the feature's decision 22), and changes nothing else of that file (S0004 adds it to `ALLOWED["entry_text"]`).
- `AcceptanceService.__init__` raises `ValueError` when `definition.acceptance_stage` is `None`; the handler below builds the service inside `handle`, after its own check.
- `open(feature)`: reads `AcceptanceReader.read()` (S0002); when the feature's status is not `due` it raises `CannotHandle(kind="acceptance_due", reason="feature <feature> is <status>, not due")` and changes nothing. The title is the first `# ` title of `f"{FEATURES_DIRECTORY}/{directory}/{FEATURE_FILE_NAME}"` at `origin/main`, with `directory` the directory's name that `read()` gives; a missing file or one without a title raises `WorkItemFormatError` with `path` set to that file, before anything is written. The id is the feature's `next_acceptance`; the path is `work_item_path(directory, "in-progress", acceptance_file_name(id))` (the directory's name, as F0002-S0001's function takes it). It runs `Git.checkout(branch, start_point="origin/main")`, creates the report's folder when missing, writes `acceptance_head(...)` with the work item writer, commits and pushes `branch`; a push whose outcome is not `pushed` raises `PushFailed`. It opens no pull request, writes no claim and runs no agent.
- `facts(feature)`: reads the feature at `origin/main` only. The feature's files and directory are those of `AcceptanceReader.feature_files` and `read()`; the cost line is `cost_line(bill(records))` over the cost records of the archived stories only, each read from `cost_records_path(work_item_path(directory, "done", <file name>))` at `origin/main` with `Git.show_file` and the cost record reader; a story without a sidecar file adds no record. A feature with no directory on `origin/main` raises `ValueError` naming the feature.
- The reviewer's write paths need no method of this story: `WritePathService(boundaries).at(stage_start, <report path>)` (F0004-S0003) gives the `write_paths` of the role of `definition.acceptance_stage`, with `{work_item}` the report and `{feature}` the feature directory two levels above it.
- An acceptance's own cost line is `BillService(boundaries.git, boundaries.cost_reader).for_work_item(<acceptance id>).line` (F0005-S0009): the report's sidecar is `cost_records_path(<report path>)`, so only its own records count.
- `AcceptanceDueHandler.__init__` stores its arguments and never raises. `handle(event)` raises, in this order, `CannotHandle(kind=<the event's kind>, reason="not an acceptance_due event")` for another kind; `CannotHandle(kind="acceptance_due", reason="no feature")` for an `acceptance_due` event without a feature; `CannotHandle(kind="acceptance_due", reason="no acceptance stage")` when `definition.acceptance_stage` is `None`. Otherwise it opens `event.feature` with `AcceptanceService(boundaries, definition).open`.

Tests: `tests/domain/test_acceptance_facts.py`, `tests/application/test_acceptance_service.py`, `tests/application/test_acceptance_due_handler.py`; the `remote`, `checkout`, `human`, `kill_points` and `boundaries` fixtures, with the pipeline definition of the fixture (`RuamelPipelineDefinitionReader().parse(PIPELINE_YAML)`). The fixture's feature `F0001` has a backlog story, so it is `incomplete`; a test that opens an acceptance pushes a feature `F0002-todo` of its own with `human.push_file("main", ...)`: its `feature.md` (`# Todo service`), story files under `done/`, and nothing under `backlog/` or `in-progress/`. Criteria 16 and 17 claim the opened acceptance with `ClaimService(boundaries, "factory-1", definition).claim(branch, path, document, "acceptance")`, which returns the `StageStart`. The closed-model test builds the models through a variable typed `type[BaseModel]` and assigns with `setattr`, the field's name in a variable. `Event.model_construct` builds the `acceptance_due` event without a feature in criterion 20, since `Event` itself refuses it.

## Acceptance criteria

1. `acceptance_facts` for `done = [F0002-S0001-a.md, F0002-S0002-b.md, F0002-S0004-d.md]`, `backlog = [F0002-S0006-x.md, .gitkeep]` gives `archived == ["F0002-S0001", "F0002-S0002", "F0002-S0004"]` and `next_story == "F0002-S0007"`.
2. `next_story` is written with four digits, also across a power of ten: the highest story number 9 gives `F0002-S0010`; a story file in `in_progress` counts; an acceptance's report file in `in_progress` does not.
3. `next_story` for the highest number 9998 is `F0002-S9999`, and for the highest number 9999 `acceptance_facts` raises `ValueError`.
4. `AcceptanceFacts.lines()` is exactly the three lines `Archived stories: F0002-S0001, F0002-S0002, F0002-S0004`, `Next free story number: F0002-S0007` and `Cost of the stories: <cost_line>` for the facts of criterion 1.
5. `acceptance_prompt("Judge the feature.", facts)` is `"Judge the feature."`, an empty line and the three lines, joined with newlines.
6. `acceptance_head("Todo service", "acceptance", ["F0001-S0001"])` has an `AcceptanceState` with stage `acceptance`, `stories == ["F0001-S0001"]`, `outcome is None`, every counter 0, no claim, no pull request and an empty journal, and the body `"# Acceptance of Todo service\n\n## Journal\n"`.
7. `AcceptanceService(boundaries, definition)` raises `ValueError` when `definition.acceptance_stage` is `None`.
8. `open("F0002")` for a due feature pushes the branch `work-item/F0002-A0001` and returns an `OpenedAcceptance` with that id and branch, the path `factory/features/F0002-todo/in-progress/F0002-A0001-acceptance.md` and the pushed commit; the report at that path on `origin/work-item/F0002-A0001` is `acceptance_head("Todo service", "acceptance", <the archived stories>)` as the writer renders it.
9. `open` adds exactly one commit on top of `origin/main` on the new branch, and that commit adds exactly the report path, also when the feature has no `in-progress/` folder on `origin/main` beforehand; no pull request exists afterwards (`hosting.pull_requests()` is empty).
10. `open` takes the title from the first `# ` line of `feature.md` at `origin/main`, and raises `WorkItemFormatError` with that file's path when the feature has no `feature.md` or no title in it, with no branch pushed.
11. `open("F0001")` for the fixture's feature, whose status is `incomplete`, raises `CannotHandle` with kind `acceptance_due` and the reason `feature F0001 is incomplete, not due`, and pushes nothing.
12. After `kill_points.arm(KillPoint.BEFORE_PUSH)` the first `open` raises `InjectedKill`; a second `open` for the same feature then ends with exactly one branch `work-item/F0002-A0001` on the remote, holding exactly one commit on top of `origin/main`.
13. `facts("F0002")` returns the archived stories and the next free story number of the feature as `origin/main` holds them, not of the work tree: a story file that exists only in the checkout's work tree is not counted.
14. `facts` takes its cost line from the cost records of the archived stories only: records of a story in `backlog`, of a story of another feature and of an acceptance are not counted, and a story without a sidecar file adds none; the line equals `cost_line(bill(<the archived stories' records>))`.
15. `facts` raises `ValueError` naming the feature for a feature that has no directory on `origin/main`.
16. At the stage-start commit of the claimed acceptance, `WritePathService(boundaries).at(stage_start, <report path>).write_paths` allows (`is_writable`) the report itself and `<feature directory>/backlog/F0002-S0005-new.md` with the fixture's pipeline definition.
17. The same write paths refuse `<feature directory>/done/F0002-S0001-a.md`, `<feature directory>/feature.md`, a file in another feature's `backlog`, `README.md` and `src/factory/x.py`.
18. GH4.4: with two acceptances `F0002-A0001` and `F0002-A0002` of one feature, each with its own cost records, and a story with its own, `BillService(...).for_work_item(<id>).line` of each acceptance counts only that report's records, and for a report without a cost records file it is `cost_line(bill([]))`.
19. `AcceptanceDueHandler.handle` opens the feature of an `acceptance_due` event: the branch for that feature exists on the remote afterwards.
20. `AcceptanceDueHandler.handle` raises `CannotHandle` with the reasons the Interface gives for an event of another kind and for an `acceptance_due` event without a feature, and pushes nothing.
21. `AcceptanceDueHandler(boundaries, definition)` with `definition.acceptance_stage` `None` is built without an error, and its `handle` of an `acceptance_due` event raises `CannotHandle` with kind `acceptance_due` and the reason `no acceptance stage`, and pushes nothing, and a `run` event with that definition raises with the reason `not an acceptance_due event`.
22. The models are closed and typed: `AcceptanceFacts` and `OpenedAcceptance` refuse an unknown key and an assignment to a field; `AcceptanceFacts.next_story` accepts `F0002-S0007` and refuses `F0002-A0007`; `AcceptanceFacts.archived` accepts `["F0002-S0001"]` and refuses `["F002-S0001"]`; `OpenedAcceptance.id` accepts `F0002-A0001` and refuses `F002-A0001`; `OpenedAcceptance.commit` accepts 40 lower-case hex characters and refuses 39; all with `ValidationError`.
23. F0005-S0009's search test passes on the real tree with `factory.domain.acceptance` in its allow-list of `JOURNAL`, and `acceptance_head` builds the heading from `JOURNAL`: the literal `## Journal` stands in no module of `src/factory` outside `factory.domain.sections`.
24. When the remote already holds a branch `work-item/F0002-A0001` that the checkout has not fetched (the human pushed it, without a report), `open("F0002")` raises `PushFailed` with the outcome `rejected`, and that remote branch is as the human left it.
25. make check stays green.
26. docs: `docs/project-guide.md` states what the opening of an acceptance writes (one report head on a branch `work-item/<acceptance id>`, no pull request, no claim), the three facts the reviewer gets, that the acceptance reviewer writes only its report and new backlog stories of its feature, and that `factory.domain.acceptance` is on the allow-list of `JOURNAL` in the journal search test.

## Demo

```bash
uv run python -c "
from factory.domain.acceptance import FeatureFiles, acceptance_facts, acceptance_prompt
files = FeatureFiles(feature='F0002', backlog=['F0002-S0006-x.md', '.gitkeep'], done=['F0002-S0001-a.md', 'F0002-S0002-b.md', 'F0002-S0004-d.md'])
facts = acceptance_facts(files, cost_line='19 runs, 7.1 min, 3.33 USD')
print(acceptance_prompt('Judge the feature.', facts))
"
```
Expect: five lines: `Judge the feature.`, an empty line, `Archived stories: F0002-S0001, F0002-S0002, F0002-S0004`, `Next free story number: F0002-S0007` and `Cost of the stories: 19 runs, 7.1 min, 3.33 USD`.

```bash
uv run python -c "
from factory.domain.acceptance import acceptance_head
head = acceptance_head('Todo service', 'acceptance', ['F0001-S0001', 'F0001-S0002'])
print(type(head.state).__name__, head.state.stage, head.state.stories, head.state.journal, head.state.claim)
print(repr(head.body))
"
```
Expect: two lines: `AcceptanceState acceptance ['F0001-S0001', 'F0001-S0002'] [] None`, then `'# Acceptance of Todo service\n\n## Journal\n'`.

## Log (append only)

1. 2026-10-12 human: created.
