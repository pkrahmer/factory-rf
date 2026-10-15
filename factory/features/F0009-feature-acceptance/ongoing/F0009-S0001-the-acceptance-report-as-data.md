---
stage: accept
pr: 103
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
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
14. The reader returns an `AcceptanceState` with those values for the text of a document whose front matter is a plain work item's front matter plus `stories: [F0001-S0001, F0001-S0002]` and `outcome: refused` with `stage: done`, and an `AcceptanceState` with `outcome` `None` for one that adds only `stories: [F0001-S0001]` with `stage: acceptance`: either key is enough (two cases, one test).
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
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory/domain/acceptance.py`; `parse` and `render` in `adapters/work_item_markdown.py`). Every rule stated there has a criterion: id form and range (1, 2), `next_acceptance_id` (3-5), file name (6, 7), `stories` order and ids (11, 12), `outcome` tied to `done` (13), reader and writer behaviour (14-20), journal functions (21, 22).
   - Criteria: each can be tested by one test function. Each rule has its failing side: 0 and 10000 (2), 9999 (5), a story id for the file name (7), unsorted and repeated stories (11), an acceptance id in `stories` (12), `outcome` set while not done and `done` without an outcome (13), an unknown key and invalid values (16, 17, 23).
   - Demo: three runnable `uv run python -c` blocks. Each `Expect:` line gives exact output that can be checked.
   - Architecture: the new module is in the domain layer and does no I/O. The adapter change stays in the existing reader and writer. No git, hosting service or agent runtime is touched.
   - Scope: within F0009 "Scope" (first bullet), and nothing in "Out of scope" is touched.
3. tester: red tests written for every criterion; `make lint` green; `make test` stops at collection because `factory.domain.acceptance` does not exist yet (ModuleNotFoundError in all three new files).
   - criterion 1: tests/domain/test_acceptance.py::test_acceptance_id_is_the_feature_and_a_four_digit_number
   - criterion 2: tests/domain/test_acceptance.py::test_acceptance_id_takes_numbers_from_1_to_9999 (0, 1, 9999, 10000)
   - criterion 3: tests/domain/test_acceptance.py::test_first_acceptance_of_a_feature_is_number_one
   - criterion 4: tests/domain/test_acceptance.py::test_next_acceptance_follows_the_highest_of_the_feature
   - criterion 5: tests/domain/test_acceptance.py::test_next_acceptance_ends_at_9999 (A9998 → A9999, A9999 → ValueError)
   - criterion 6: tests/domain/test_acceptance.py::test_acceptance_file_name_reads_back_to_its_id_and_slug
   - criterion 7: tests/domain/test_acceptance.py::test_acceptance_file_name_refuses_a_story_id
   - criteria 8, 9: tests/domain/test_acceptance.py::test_acceptance_sorts_after_the_stories_of_its_feature (rows `F0002-2fa` and `F0002`; the first acceptance id is `acceptance_id(feature, 1)`)
   - criterion 10: tests/domain/test_acceptance.py::test_acceptance_state_defaults_to_no_stories_and_no_outcome
   - criterion 11: tests/domain/test_acceptance.py::test_acceptance_stories_ascend_strictly
   - criterion 12: tests/domain/test_acceptance.py::test_acceptance_stories_refuse_an_acceptance_id
   - criterion 13: tests/domain/test_acceptance.py::test_acceptance_outcome_is_set_exactly_when_done
   - criterion 14: tests/adapters/test_work_item_markdown_acceptance.py::test_reader_returns_an_acceptance_state_for_either_extra_key
   - criterion 15: tests/adapters/test_work_item_markdown_acceptance.py::test_reader_returns_a_plain_state_without_the_extra_keys
   - criterion 16: tests/adapters/test_work_item_markdown_acceptance.py::test_reader_refuses_any_other_unknown_key (`verdict` beside a plain front matter, and beside `stories`, following the Interface rule "any other unknown key is still a WorkItemFormatError")
   - criterion 17: tests/adapters/test_work_item_markdown_acceptance.py::test_reader_names_the_extra_key_of_an_invalid_value
   - criterion 18: tests/adapters/test_work_item_markdown_acceptance.py::test_writer_puts_stories_and_outcome_last (checks the full key order: WorkItemState's fields, then `stories`, then `outcome`, and `outcome: null`)
   - criterion 19: tests/adapters/test_work_item_markdown_acceptance.py::test_writer_gives_a_plain_state_neither_extra_key
   - criterion 20: tests/adapters/test_work_item_markdown_acceptance.py::test_acceptance_document_survives_a_round_trip
   - criterion 21: tests/domain/test_journal_acceptance.py::test_append_entry_keeps_the_acceptance_state
   - criterion 22: tests/domain/test_journal_acceptance.py::test_restore_puts_back_the_baseline_stories_and_outcome
   - criterion 23: tests/domain/test_acceptance.py::test_acceptance_state_is_closed_and_typed (built through `type[BaseModel]`) and ::test_acceptance_state_refuses_an_assignment (uses `setattr` with the field name held in a variable)
   - criteria 24, 25: not tests (make check; documenter).
   Files created: tests/domain/test_acceptance.py, tests/adapters/test_work_item_markdown_acceptance.py, tests/domain/test_journal_acceptance.py.
   Could not be imported: factory.domain.acceptance (all three files import it). I skipped the type check, as this stage's instructions say.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: all the tester's tests pass and `make check` is green.
      - New module `src/factory/domain/acceptance.py` (`ACCEPTANCE_SLUG`, `AcceptanceOutcome`, `AcceptanceState`, `acceptance_id`, `next_acceptance_id`, `acceptance_file_name`). `AcceptanceState` subclasses `WorkItemState` and keeps its frozen, `extra="forbid"` config. A field validator refuses acceptance ids in `stories` and any list that is not strictly ascending (`sorted(set(...))`, the same rule `comments_read` uses). A model validator ties `outcome` to `stage == DONE_STAGE`. `next_acceptance_id` takes the highest number among the feature's acceptances and goes through `acceptance_id`, so the 1-9999 range is checked in one place.
      - Changed `src/factory/adapters/work_item_markdown.py`: the reader validates with `AcceptanceState` when the front matter has `stories` or `outcome`, and with `WorkItemState` otherwise. The extra keys are worked out from the difference between the two models' fields, not listed by hand. Faults still come from `first_fault`, so an unknown key comes first and a bad value is named by its key. The writer needed no change: it already dumps `state.model_dump()`, so the subclass's fields come after `journal` in field order.
      - Main design decision: picking the model in the reader by its keys. I rejected a single model with optional extra fields, because a story would then accept `stories` and `outcome`, which the Interface rules out.
      - Refactor pass: I read the diff (two files, about 80 lines) and found nothing to rename, simplify or remove, so there is no refactor commit.
      - Noticed and left alone: `append_entry` and `restore_state_and_journal` already keep the subclass through `model_copy`, so criteria 21 and 22 pass without a change to `factory.domain.journal`.
      - Commit: `ticket F0009-S0001: feat(domain): the acceptance id, report file name and state`.

   `make check`: check: green
5. reviewer: no findings.
      - Acceptance criteria: criteria 1-23 each have a test that checks what the criterion says (the tester's map in entry 3 is correct), and the coder's entry reports `make check` green. Every limit in the Interface is tested on both sides: numbers 0/1/9999/10000, A9998→A9999 and A9999 raising, a story id refused by `acceptance_file_name`, unsorted, repeated and ascending `stories`, an acceptance id in `stories`, `outcome` both without `done` and with it, an unknown key on a plain front matter and on an acceptance's, an invalid `stories` and an invalid `outcome` value named by their key. Criterion 23 builds the model through `type[BaseModel]` and assigns through `setattr` with the field name in a variable, as `CLAUDE.md` asks.
      - Architecture: `src/factory/domain/acceptance.py` has no I/O and imports only the domain (`identifiers`, `pipeline_definition`, `work_item`). The adapter imports the domain, which the layer order allows. No `dict[str, Any]` crosses a function boundary.
      - Security: no new markers, no secrets, no new commands or string-built queries. Input is still checked at the reader by Pydantic, and faults still go through `first_fault`.
      - Quality: `src/factory/adapters/work_item_markdown.py` works out `_ACCEPTANCE_KEYS` from the two models' fields instead of listing them, which avoids a second list to keep in sync. The writer was left unchanged and already dumps `state.model_dump()`, as the Interface requires; criteria 18 and 20 prove it. `next_acceptance_id` goes through `acceptance_id`, so the 1-9999 range is checked in one place. The one-line `sorted(set(...))` check repeats the one on `comments_read` in `work_item.py`, but it is too small to count as a duplicated helper. Docstrings are present and accurate.
      - Ticket hygiene: entry 4 states the main decision (picking the model by the front matter's keys) and the rejected alternative (one model with optional extra fields). The Assignment matches what was built. Criterion 25 still says what the project guide must state.
6. documenter: criterion 25 is written, `make check` is green (run in the foreground after the last edit), and I found no findings.
   - `docs/project-guide.md`: new section "The feature acceptance". It covers the id form `F0001-A0001` (numbered per feature, 1 to 9999, how `next_acceptance_id` picks the next number), the report file name `F0001-A0004-acceptance.md`, the sort order after the stories, `AcceptanceState` with its `stories` and `outcome` rules, and how the reader and writer treat the two keys. It states that `stories` and `outcome` belong to the factory and that `restore_state_and_journal` restores them after every agent run.
   - `docs/project-guide.md`, "The layout": the sentence about the ten keys of `WorkItemState` now says an acceptance adds `stories` and `outcome` after `journal`.
   - I checked the section against the diff by reading the code. I did not run the demo commands.
   - Cross-read and found current: README, `docs/operator-guide.md`, and the project guide's sections on ids, order, the state, the journal and restore.
   - Stale but unrelated, so not touched: the project guide's board paragraph says `FeatureRow.acceptance` is always `None` until F0009-S0001. This story does not change the board, so the line is still true. A later F0009 story that builds the board support should update it.

   `make check`: check: green
7. demo: I ran all three demo commands from the repository root, exactly as written. Each output matches its `Expect:` line, and nothing the demo showed goes against an acceptance criterion. No findings.

   1. Ids and order. This met its Expect line: four lines, `F0002-A0001`, `F0002-A0004`, then the same sorted list twice. The second and third lines cover criteria 8 and 9 (a slug that starts with a digit, and a missing slug).
   ```
   F0002-A0001
   F0002-A0004
   ['F0002-S0001', 'F0002-S0009', 'F0002-A0001', 'F0003-S0001']
   ['F0002-S0001', 'F0002-S0009', 'F0002-A0001', 'F0003-S0001']
   ```

   2. `AcceptanceState` validation. This met its Expect line: `rejected` on three lines, then `refused ['F0001-S0001']`.
   ```
   rejected
   rejected
   rejected
   refused ['F0001-S0001']
   ```

   3. Writer key order and a round trip through the reader. This met its Expect line: `['stories', 'outcome']`, then `AcceptanceState True`.
   ```
   ['stories', 'outcome']
   AcceptanceState True
   ```

   Extra check for criterion 18, beyond the demo commands: I rendered the same kind of document and printed the whole front matter. It shows the ten `WorkItemState` keys in order, ending with `journal: []`, then `stories: [F0001-S0001]` and `outcome: null`. This agrees with the criterion.

   Not run here: `make check`. The factory runs it after this stage. The coder's and documenter's entries both report it green.
