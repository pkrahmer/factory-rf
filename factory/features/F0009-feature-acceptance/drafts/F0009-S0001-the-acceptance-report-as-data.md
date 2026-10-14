# The acceptance report as data, and its place in the order

## Assignment (as of log entry 1)

Give a feature acceptance the data it needs before anything can open, run or decide one: its id (`F0001-A0001`, one per acceptance, numbered per feature), its report file name, and its state in the front matter (`AcceptanceState`: the work item state plus `stories`, the archived stories the report covers, and `outcome`, the human's result). The reader and the writer of work items learn the two extra keys, so that every service that reads a work item (the undo, the claim, the comment handler) can read a report. Each acceptance is a work item of its own with its own report file and its own cost records; there is no single report that later acceptances overwrite. An acceptance sorts after every story of its feature whatever the feature folder's slug, which is shown here for a slug that starts with a digit and for a missing slug. Covers ST6.3; keeps kept thing 4 (state and journal are data, restored by code) and kept thing 19 (the feature acceptance is a work item beside the stories). No git, no hosting service and no agent runtime are touched by this story. Criteria 8, 9, 21 and 22 pass at once against code that F0002 built (`work_item_order`, `append_entry`, `restore_state_and_journal`); they are the proof of ST6.3 and of kept thing 4 for an acceptance, and they fail the day someone changes those functions.

## Interface

`src/factory/domain/acceptance.py` (new)

```python
ACCEPTANCE_SLUG = "acceptance"
AcceptanceOutcome = Literal["accepted", "refused"]

class AcceptanceState(WorkItemState):
    stories: list[WorkItemId] = []
    outcome: AcceptanceOutcome | None = None

def acceptance_id(feature: FeatureId, number: int) -> WorkItemId: ...
def next_acceptance_id(feature: FeatureId, existing: Iterable[WorkItemId]) -> WorkItemId: ...
def acceptance_file_name(work_item: WorkItemId) -> str: ...
```

`src/factory/adapters/work_item_markdown.py` (F0002-S0002's module, two methods grow)

```python
class FrontmatterWorkItemReader:
    def parse(self, text: str) -> WorkItemDocument: ...

class FrontmatterWorkItemWriter:
    def render(self, document: WorkItemDocument) -> str: ...
```

`AcceptanceState` is a subclass of `WorkItemState` and keeps its `ConfigDict(frozen=True, extra="forbid")`. `WorkItemId`, `FeatureId` and `is_acceptance` come from `factory.domain.identifiers`, `DONE_STAGE` from `factory.domain.pipeline_definition`.

Rules:

- `acceptance_id(feature, number)` is `"<feature>-A<number as four digits>"`, for `number` from 1 to 9999; any other number raises `ValueError`.
- `next_acceptance_id(feature, existing)` looks only at the ids in `existing` that are acceptances of `feature` (story ids and other features' acceptances are ignored), takes the highest number and adds one; with none it is number 1. When the highest number is 9999 it raises `ValueError`. A gap in the numbers is not filled.
- `acceptance_file_name(work_item)` is `"<work item>-acceptance.md"`; a story id raises `ValueError`. The name is read back by `parse_work_item_file_name` to the same id and the slug `acceptance`.
- `AcceptanceState.stories` is strictly ascending (sorted, no repeats) and holds story ids only, never an acceptance id.
- `AcceptanceState.outcome` is set exactly when `stage == DONE_STAGE`.
- The reader returns an `AcceptanceState` exactly when the front matter has a `stories` or an `outcome` key, and a plain `WorkItemState` otherwise. Any other unknown key is still a `WorkItemFormatError` naming the key; an invalid value of `stories` or `outcome` is a `WorkItemFormatError` whose `fault` names that key.
- The writer writes an `AcceptanceState` with all the keys of `WorkItemState` in their order, then `stories`, then `outcome` (`null` while unset), both always; a plain `WorkItemState` gets neither key. It dumps the state with `document.state.model_dump()`, never through `document.model_dump()`, which serialises the field by its declared type `WorkItemState` and drops `stories` and `outcome`.
- `append_entry` and `restore_state_and_journal` (`factory.domain.journal`) keep the state's type and its `stories` and `outcome`.

Tests: `tests/domain/test_acceptance.py`, `tests/adapters/test_work_item_markdown_acceptance.py`, `tests/domain/test_journal_acceptance.py`. The closed-model test of criterion 23 builds the model through a variable typed `type[BaseModel]` and assigns with `setattr`, the field's name in a variable (`CLAUDE.md`, Tests).

## Acceptance criteria

1. `acceptance_id("F0001", 1)` is `"F0001-A0001"` and `acceptance_id("F0012", 345)` is `"F0012-A0345"`.
2. `acceptance_id` accepts the numbers 1 and 9999 and raises `ValueError` for 0 and for 10000.
3. `next_acceptance_id("F0001", [])` is `"F0001-A0001"`.
4. `next_acceptance_id("F0001", ["F0001-A0001", "F0001-A0003", "F0001-S0009", "F0002-A0007"])` is `"F0001-A0004"`: the highest acceptance number of the feature plus one, a gap not filled, story ids and other features' acceptances ignored.
5. `next_acceptance_id("F0001", ["F0001-A9998"])` is `"F0001-A9999"`, and `next_acceptance_id("F0001", ["F0001-A9999"])` raises `ValueError`.
6. `acceptance_file_name("F0001-A0004")` is `"F0001-A0004-acceptance.md"`, and `parse_work_item_file_name` reads that name back to the id `"F0001-A0004"` and the slug `"acceptance"`.
7. `acceptance_file_name("F0001-S0004")` raises `ValueError`.
8. ST6.3, a slug that starts with a digit: for the feature directory name `"F0002-2fa"`, the ids `["F0003-S0001", <the first acceptance id of the feature that parse_feature_directory_name reads from the name>, "F0002-S0009", "F0002-S0001"]`, sorted with `work_item_order`, are `["F0002-S0001", "F0002-S0009", "F0002-A0001", "F0003-S0001"]`.
9. ST6.3, a missing slug: the same list for the feature directory name `"F0002"` sorts to the same result.
10. `AcceptanceState(stage="acceptance")` has `stories == []`, `outcome is None`, and the other fields as `WorkItemState(stage="acceptance")` has them.
11. `AcceptanceState` rejects a `stories` list that is not strictly ascending, with a `ValidationError`, for `["F0001-S0002", "F0001-S0001"]` and for `["F0001-S0001", "F0001-S0001"]`, and accepts `["F0001-S0001", "F0001-S0002"]`.
12. `AcceptanceState` rejects an acceptance id in `stories` (`["F0001-A0001"]`) with a `ValidationError`.
13. `AcceptanceState` rejects an `outcome` while the stage is not `done` (`stage="acceptance", outcome="accepted"`) and rejects `stage="done"` without an `outcome`, each with a `ValidationError`; `stage="done", outcome="refused"` is accepted.
14. The reader, given the text of a document whose front matter is a plain work item's front matter plus `stories: [F0001-S0001, F0001-S0002]` and `outcome: refused` with `stage: done`, returns an `AcceptanceState` with those values.
15. The reader, given a front matter with neither `stories` nor `outcome`, returns a state that is a `WorkItemState` and not an `AcceptanceState`.
16. The reader raises `WorkItemFormatError` for a front matter with the extra key `verdict`, and the error's `fault` names `verdict`.
17. The reader raises `WorkItemFormatError` whose `fault` names `stories` for an unsorted `stories` list, and one that names `outcome` for `outcome: maybe`.
18. The writer renders an `AcceptanceState` document with `stories` and then `outcome` as the last two front matter keys, after `journal`, and writes `outcome: null` while the outcome is unset.
19. The writer renders a plain `WorkItemState` document with neither a `stories` nor an `outcome` key.
20. `parse(render(document))` equals `document` for an `AcceptanceState` document that holds two stories, an outcome and two journal records.
21. `append_entry` on a document whose state is an `AcceptanceState` returns a document whose state is an `AcceptanceState` with the same `stories` and `outcome`.
22. `restore_state_and_journal(current, baseline)`, where `current` carries different `stories` and `outcome` than the `AcceptanceState` of `baseline`, returns a document with the baseline's `stories` and `outcome`.
23. `AcceptanceState` is closed and typed: built through a variable typed `type[BaseModel]`, it refuses an unknown key (`verdict`), and an assignment to `stories` made with `setattr` and the field's name in a variable; `stories` accepts `["F0001-S0001"]` and refuses `["F001-S0001"]`; `outcome` accepts `"refused"` and refuses `"maybe"`, each refusal a `ValidationError`.
24. make check stays green.
25. docs: `docs/project-guide.md` states the acceptance's id form (`F0001-A0001`, numbered per feature), its report file name, and that `stories` and `outcome` belong to the factory and are restored after every agent run.

## Demo

```bash
uv run python -c "
from factory.domain.acceptance import next_acceptance_id
from factory.domain.identifiers import parse_feature_directory_name, work_item_order
print(next_acceptance_id('F0002', []))
print(next_acceptance_id('F0002', ['F0002-A0001', 'F0002-A0003', 'F0001-A0009', 'F0002-S0007']))
for name in ('F0002-2fa', 'F0002'):
    feature = parse_feature_directory_name(name).id
    ids = ['F0003-S0001', next_acceptance_id(feature, []), 'F0002-S0009', 'F0002-S0001']
    print(sorted(ids, key=work_item_order))
"
```
Expect: four lines: `F0002-A0001`, `F0002-A0004`, then twice `['F0002-S0001', 'F0002-S0009', 'F0002-A0001', 'F0003-S0001']`.

```bash
uv run python -c "
from pydantic import ValidationError
from factory.domain.acceptance import AcceptanceState
for bad in (dict(stage='acceptance', outcome='accepted'), dict(stage='done'), dict(stage='acceptance', stories=['F0001-S0002', 'F0001-S0001'])):
    try:
        AcceptanceState(**bad)
    except ValidationError:
        print('rejected')
ok = AcceptanceState(stage='done', outcome='refused', stories=['F0001-S0001'])
print(ok.outcome, ok.stories)
"
```
Expect: the word `rejected` on three lines, then `refused ['F0001-S0001']`.

```bash
uv run python -c "
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.domain.acceptance import AcceptanceState
from factory.domain.work_item import WorkItemDocument
document = WorkItemDocument(state=AcceptanceState(stage='acceptance', stories=['F0001-S0001']), body='# Acceptance of Todo service\n')
text = FrontmatterWorkItemWriter().render(document)
keys = [line.split(':')[0] for line in text.splitlines() if line and line[0].isalpha() and ':' in line]
print(keys[-2:])
parsed = FrontmatterWorkItemReader().parse(text)
print(type(parsed.state).__name__, parsed == document)
"
```
Expect: two lines: `['stories', 'outcome']`, then `AcceptanceState True`.

## Log (append only)

1. 2026-10-12 human: created.
