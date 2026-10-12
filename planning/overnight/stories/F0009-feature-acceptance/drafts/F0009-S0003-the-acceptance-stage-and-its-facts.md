# The acceptance stage and the acceptance reviewer's facts

## Assignment (as of log entry 1)

Open a due acceptance and give the acceptance reviewer what it needs. A due acceptance is opened by pushing a branch `work-item/F0001-A0001` that holds one new file, the report's head: the state (stage = the pipeline definition's `acceptance_stage`, `stories` = the archived stories, counters at their initial values), the title taken from the feature file (`# Acceptance of <feature title>`) and an empty `## Journal` section. That is all the opening does: the claim, the draft pull request and the agent run belong to the stage protocol, which meets the acceptance on the next tick as an ordinary work item at its first stage, read from its branch. The reviewer's prompt gets three facts computed by code, not by the agent: the archived stories, the next free story number and the cost of the stories, read from the cost records of the archived stories. The reviewer may write only its report and new stories in the feature's backlog; each acceptance has its own report file and so its own cost line, which counts only its own records (GH4.4). Covers GH4.4; keeps kept thing 19 (the acceptance judges the whole and proposes stories that only the human starts), kept thing 2 (proposed stories only as backlog files) and kept thing 20 (each acceptance costed). The factory opens the acceptance without a `created` entry of a human: its journal starts with the stage protocol's `started` entry. The units here are `acceptance_prompt`, which the stage protocol appends to the reviewer's prompt, and the service that opens and reads. Registering `AcceptanceDueHandler` with the dispatcher is wiring in `factory.entry.wiring`; it is built and tested through ticks in the last story of this feature.

## Interface

`src/factory/domain/acceptance.py` (grown)

```python
class AcceptanceFacts(BaseModel):
    archived: list[WorkItemId]
    next_story: WorkItemId
    cost_line: str

    def lines(self) -> list[str]: ...

def acceptance_facts(files: FeatureFiles, cost_line: str) -> AcceptanceFacts: ...
def acceptance_prompt(base: str, facts: AcceptanceFacts) -> str: ...
def acceptance_head(feature_title: str, stage: str, stories: Sequence[WorkItemId]) -> WorkItemDocument: ...
```

`src/factory/application/acceptance_reading.py` (grown)

```python
class AcceptanceReader:
    def in_flight(self) -> list[WorkItemSnapshot]: ...
```

`src/factory/application/acceptance.py` (new)

```python
class OpenedAcceptance(BaseModel):
    id: WorkItemId
    branch: str
    path: str
    commit: CommitId

class AcceptanceService:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def open(self, feature: FeatureId) -> OpenedAcceptance: ...
    def facts(self, feature: FeatureId, *, ref: str) -> AcceptanceFacts: ...
    def write_paths(self, work_item_path: str) -> list[str]: ...
    def own_cost_line(self, work_item_path: str, *, ref: str) -> str: ...

class AcceptanceDueHandler:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

`WorkItemSnapshot` is in `factory.domain.work_item`, `CommitId` in `factory.domain.git`, `CannotHandle`, `WorkItemFormatError` and `PushFailed` in `factory.domain.errors`.

Rules:

- `acceptance_facts(files, cost_line)`: `archived` is `story_file_ids(files.done)`; `next_story` is `"<feature>-S<n>"` with `n` the highest story number among the story files of `backlog`, `in_progress` and `done`, plus one, written with four digits; with no story file it is number 1; when the highest number is 9999 it raises `ValueError`. `.gitkeep`, notes and an acceptance's report file do not count.
- `AcceptanceFacts.lines()` is exactly three lines: `Archived stories: ` followed by the ids joined by `, `; `Next free story number: ` and the id; `Cost of the stories: ` and `cost_line`.
- `acceptance_prompt(base, facts)` is `base`, an empty line, then the three lines, joined with `\n`.
- `acceptance_head(feature_title, stage, stories)` returns a `WorkItemDocument` whose state is an `AcceptanceState` with `initial_state(stage)`'s values (every counter 0, no claim, no pull request, empty journal), `stories` as given and `outcome` `None`, and whose body is exactly `# Acceptance of <feature_title>`, an empty line, `## Journal` and a final newline.
- `in_flight()` returns, for every remote branch `work-item/<id>` of an acceptance whose report file is in `in-progress/` of the feature at `origin/<branch>` and whose id has no report on the main branch, a `WorkItemSnapshot` with the report's id, its path on the branch, folder `in-progress`, `branch_name(id)`, the commit of `origin/<branch>` and the document read from there; ordered by `work_item_order`. Story branches, branches without the report file and branches whose acceptance is already on the main branch are skipped. The watcher's reading of work items (`factory.application.work_items`, F0006-S0001) adds these snapshots to the stories it judges.
- `AcceptanceService.__init__` raises `ValueError` when `definition.acceptance_stage` is `None`.
- `open(feature)`: reads `AcceptanceReader.read()`; when the feature's status is not `due` it raises `CannotHandle(kind="acceptance_due", reason="feature <feature> is <status>, not due")` and changes nothing. The title is the first `# ` title of `<directory>/feature.md` (`FEATURE_FILE_NAME`) at `origin/main`; a missing file or one without a title raises `WorkItemFormatError` with `path` set to that file, before anything is written. The id is the feature's `next_acceptance`; the path is `work_item_path(directory, "in-progress", acceptance_file_name(id))`. It runs `Git.checkout(branch, start_point="origin/main")`, creates the report's folder when missing, writes `acceptance_head(...)` with the work item writer, commits and pushes `branch`; a push whose outcome is not `pushed` raises `PushFailed`. It opens no pull request, writes no claim and runs no agent.
- `facts(feature, ref=...)`: the feature's files at `ref` (`AcceptanceReader.feature_files`), the directory as `AcceptanceReader.read()` reports it, and the cost line `cost_line(bill(records))` over the cost records of the archived stories only, each read from `cost_records_path` of the story's path in `done/` at `ref`; a story without a sidecar file adds no record.
- `write_paths(work_item_path)` is `expand_write_paths(...)` of the write paths of the role of `definition.acceptance_stage`, with `work_item_path` and the feature directory (two levels above the work item's path).
- `own_cost_line(work_item_path, ref=...)` is `cost_line(bill(records))` over the cost records at `cost_records_path(work_item_path)` at `ref`, and over no record when that file is missing.
- `AcceptanceDueHandler.handle(event)` opens `event.feature`; for an event of another kind it raises `CannotHandle(kind=<the event's kind>, reason="not an acceptance_due event")`, and for an `acceptance_due` event without a feature `CannotHandle(kind="acceptance_due", reason="no feature")`.

Tests: `tests/domain/test_acceptance_facts.py`, `tests/application/test_acceptance_reading_in_flight.py`, `tests/application/test_acceptance_service.py`; the `remote`, `checkout`, `human`, `kill_points` and `boundaries` fixtures, with the pipeline definition of the fixture.

## Acceptance criteria

1. `acceptance_facts` for `done = [F0002-S0001-a.md, F0002-S0002-b.md, F0002-S0004-d.md]`, `backlog = [F0002-S0006-x.md, .gitkeep]` gives `archived == ["F0002-S0001", "F0002-S0002", "F0002-S0004"]` and `next_story == "F0002-S0007"`.
2. `next_story` is written with four digits, also across a power of ten: the highest story number 9 gives `F0002-S0010`; a story file in `in_progress` counts; an acceptance's report file in `in_progress` does not.
3. `next_story` for the highest number 9998 is `F0002-S9999`, and for the highest number 9999 `acceptance_facts` raises `ValueError`.
4. `AcceptanceFacts.lines()` is exactly the three lines `Archived stories: F0002-S0001, F0002-S0002, F0002-S0004`, `Next free story number: F0002-S0007` and `Cost of the stories: <cost_line>` for the facts of criterion 1.
5. `acceptance_prompt("Judge the feature.", facts)` is `"Judge the feature."`, an empty line and the three lines, joined with newlines.
6. `acceptance_head("Todo service", "acceptance", ["F0001-S0001"])` has an `AcceptanceState` with stage `acceptance`, `stories == ["F0001-S0001"]`, `outcome is None`, every counter 0, no claim, no pull request and an empty journal, and the body `"# Acceptance of Todo service\n\n## Journal\n"`.
7. `in_flight()` returns, for the branch `work-item/F0001-A0001` that holds `factory/features/F0001-todo/in-progress/F0001-A0001-acceptance.md`, one snapshot with that id, that path, folder `in-progress`, branch `work-item/F0001-A0001`, the commit of `origin/work-item/F0001-A0001` and the report read from the branch.
8. `in_flight()` skips a story branch, a `work-item/F0001-A0001` branch without the report file, and a branch whose acceptance is already on the main branch.
9. `in_flight()` returns the snapshots of two features in `work_item_order`.
10. The watcher's evaluation, with an in-flight acceptance at stage `acceptance` and no claim on its branch, returns a `run` event whose work item is that acceptance.
11. `AcceptanceService(boundaries, definition)` raises `ValueError` when `definition.acceptance_stage` is `None`.
12. `open("F0001")` for a due feature pushes the branch `work-item/F0001-A0001` and returns an `OpenedAcceptance` with that id and branch, the path `factory/features/<directory>/in-progress/F0001-A0001-acceptance.md` and the pushed commit; the report at that path on `origin/work-item/F0001-A0001` is `acceptance_head(<the title of feature.md>, "acceptance", <the archived stories>)` as the writer renders it.
13. `open` adds exactly one commit on top of `origin/main` on the new branch, and that commit adds exactly the report path, also when the feature has no `in-progress/` folder on `origin/main` beforehand; no pull request exists afterwards (`hosting.pull_requests()` is empty).
14. `open` takes the title from the first `# ` line of `feature.md` at `origin/main`, and raises `WorkItemFormatError` with that file's path when the feature has no `feature.md` or no title in it, with no branch pushed.
15. `open` for a feature whose status is not `due` raises `CannotHandle` with kind `acceptance_due` and the reason `feature F0001 is incomplete, not due` (for the status `incomplete`), and pushes nothing.
16. After `kill_points.arm(KillPoint.BEFORE_PUSH)` the first `open` raises `InjectedKill`; a second `open` for the same feature then ends with exactly one branch `work-item/F0001-A0001` on the remote, holding exactly one commit on top of `origin/main`.
17. `facts("F0001", ref="origin/main")` returns the archived stories and the next free story number of the feature at that ref, not of the work tree.
18. `facts` takes its cost line from the cost records of the archived stories only: records of a story in `backlog`, of a story of another feature and of an acceptance are not counted, and a story without a sidecar file adds none; the line equals `cost_line(bill(<the archived stories' records>))`.
19. `write_paths(<report path>)` allows (`is_writable`) the report itself and `<feature directory>/backlog/F0001-S0005-new.md` with the fixture's pipeline definition.
20. `write_paths(<report path>)` refuses `<feature directory>/done/F0001-S0001-a.md`, `<feature directory>/feature.md`, a file in another feature's `backlog`, `README.md` and `src/factory/x.py`.
21. GH4.4: with two acceptances `F0001-A0001` and `F0001-A0002` of one feature, each with its own cost records, and a story with its own, `own_cost_line` of each report's path counts only that report's records, and for a report without a cost records file it is `cost_line(bill([]))`.
22. `AcceptanceDueHandler.handle` opens the feature of an `acceptance_due` event: the branch for that feature exists on the remote afterwards.
23. `AcceptanceDueHandler.handle` raises `CannotHandle` with the reasons the Interface gives for an event of another kind and for an `acceptance_due` event without a feature, and pushes nothing.
24. `make check` stays green.
25. docs: `docs/project-guide.md` states what the opening of an acceptance writes (one report head on a branch `work-item/<acceptance id>`, no pull request, no claim), the three facts the reviewer gets, and that the acceptance reviewer writes only its report and new backlog stories of its feature.

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
