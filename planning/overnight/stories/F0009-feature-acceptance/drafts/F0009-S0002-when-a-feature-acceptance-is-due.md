# When a feature acceptance is due

## Assignment (as of log entry 1)

Derive, from the remote's files alone, the status of every feature's acceptance, and turn a due acceptance into an event. A feature is complete when it has an archived story and no story file waits in its backlog or in progress; only story files count, so a `.gitkeep` or a note beside the stories never keeps a feature incomplete (ST6.2). A complete feature's acceptance is due when no report at `done` covers exactly its archived stories. The other states follow v1's derivation: in flight (a report is on its own branch), merged and not yet recorded (a report is on the main branch and is not at `done`), and the recorded result (accepted or refused). The watcher's evaluation takes a due acceptance as a candidate in work item order, where it comes after its feature's stories and before the next feature's (shown with ST6.3 in the previous story), and the board's acceptance column is filled from the same status. Covers ST6.2; keeps kept thing 19 (the due rule) and kept thing 3 (the remote is read, never the work tree); R18. The previous story supplies `AcceptanceState` and the ids.

## Interface

`src/factory/domain/acceptance.py` (grown)

```python
class FeatureFiles(BaseModel):
    feature: FeatureId
    backlog: list[str] = []
    in_progress: list[str] = []
    done: list[str] = []

class ReportFacts(BaseModel):
    id: WorkItemId
    folder: LifecycleFolder
    state: AcceptanceState
    on_branch: bool

class FeatureAcceptance(BaseModel):
    feature: FeatureId
    directory: str
    status: AcceptanceStatus
    archived: list[WorkItemId]
    next_acceptance: WorkItemId

def story_file_ids(names: Iterable[str]) -> list[WorkItemId]: ...
def acceptance_status(files: FeatureFiles, reports: Sequence[ReportFacts]) -> AcceptanceStatus: ...
```

`src/factory/application/acceptance_reading.py` (new)

```python
class AcceptanceReader:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def feature_files(self, feature: FeatureId, *, ref: str = "origin/main") -> FeatureFiles: ...
    def read(self) -> list[FeatureAcceptance]: ...
    def due_events(self) -> list[Event]: ...
    def fill_board(self, rows: Sequence[FeatureRow]) -> list[FeatureRow]: ...
```

`AcceptanceStatus` and `FeatureRow` are in `factory.domain.board`, `Event` in `factory.domain.events`, `Boundaries` in `factory.application.boundaries`.

Rules:

- `FeatureFiles` holds file names only (no directories), for the files directly in the feature's `backlog`, `in-progress` and `done` folders.
- A story file is a name that `parse_work_item_file_name` reads as a story id (not an acceptance id). `story_file_ids` returns the ids of the story files among the names, ascending, without repeats; every other name (`.gitkeep`, `README.md`, notes, an acceptance's report such as `F0001-A0001-acceptance.md`) is ignored.
- The archived stories of a feature are `story_file_ids(files.done)`.
- `reports` holds every report of the feature: those on the main branch (`on_branch=False`, folder `in-progress` or `done`) and those on a remote acceptance branch (`on_branch=True`, folder `in-progress`).
- `acceptance_status` returns the first of these that applies:
  1. `in_flight`: a report with `on_branch=True` whose id has no report with `on_branch=False`;
  2. `merged_unrecorded`: a report with `on_branch=False` whose state's stage is not `done`;
  3. `incomplete`: there is no archived story, or `story_file_ids(files.backlog)` or `story_file_ids(files.in_progress)` is not empty;
  4. `accepted` or `refused`: a report with `on_branch=False` and stage `done` whose `stories` equal the archived stories as sets; the status is that report's `outcome` (the highest id when several cover);
  5. `due`.
- `AcceptanceReader` reads only `origin/...` refs of the checkout's git (`Git.resolve`, `list_files`, `show_file`, `remote_branches`), never the work tree and never a local branch.
- `feature_files(feature, ref=...)` lists `factory/features/<directory>/{backlog,in-progress,done}` at `ref` for the directory whose name `parse_feature_directory_name` reads as `feature`; a feature with no directory at `ref` gives three empty lists.
- `read()` returns one `FeatureAcceptance` per directory under `factory/features` on `origin/main` whose name `parse_feature_directory_name` accepts, ordered by feature id. `directory` is `factory/features/<directory name>`; `next_acceptance` is `next_acceptance_id` over the ids of all the feature's reports, on the main branch and on remote branches `work-item/<id>` of acceptances.
- A report on the main branch is a file in `in-progress/` or `done/` whose name `parse_work_item_file_name` reads as an acceptance id; its state is read with the work item reader and must be an `AcceptanceState`, else `WorkItemFormatError` with `path` set to the report's path. A report on a branch is the file with the branch's id in `in-progress/` at `origin/<branch>`; a remote acceptance branch without such a file is ignored.
- `due_events()` returns, for every feature whose status is `due`, `Event(kind="acceptance_due", work_item=None, feature=<feature>, remote_state=<commit of origin/main>, detail=<next_acceptance>)`, ordered by `work_item_order(next_acceptance)`. It returns `[]` when `definition.acceptance_stage` is `None`.
- `fill_board(rows)` returns the rows in the same order with `acceptance` set to the status of the feature with that id; a row whose feature has no directory on `origin/main` is returned unchanged. When `definition.acceptance_stage` is `None` every row is returned unchanged.
- Evaluation. The watcher's evaluation (`factory.application.watcher`, F0006-S0002) takes `due_events()` as extra candidates of its fourth tier, ranked with the runnable work items by `work_item_order` of the acceptance id in `detail`; a work item waiting for the human still outranks them. This story changes that module only to read the events in. The board command (`factory.entry.watch`, F0006-S0006) passes its feature rows through `fill_board`.

Tests: `tests/domain/test_acceptance_status.py`, `tests/application/test_acceptance_reading.py`; the remote is the `remote` fixture, files are pushed with `human.push_file`.

## Acceptance criteria

1. `story_file_ids(["F0001-S0002-b.md", "F0001-S0001-a.md"])` is `["F0001-S0001", "F0001-S0002"]`, and a name that appears twice gives its id once.
2. `story_file_ids` ignores `.gitkeep`, `README.md`, `notes.md` and `F0001-A0001-acceptance.md`: the list `[".gitkeep", "README.md", "notes.md", "F0001-A0001-acceptance.md"]` gives `[]`.
3. ST6.2: a feature with archived stories `F0001-S0001-a.md` and `F0001-S0002-b.md` in `done` and `.gitkeep` in `backlog` has the status `due` when no report exists.
4. A feature with no archived story (only `.gitkeep` in every folder) has the status `incomplete`.
5. A feature with a story file in `backlog`, or one in `in_progress`, has the status `incomplete` even though it has archived stories.
6. A report at `done` on the main branch with outcome `accepted` or `refused` and `stories` equal to the archived stories gives the status `accepted` or `refused`, and the feature is not `due`.
7. When two reports at `done` both cover the archived stories, the one with the higher id decides the status.
8. A report at `done` whose `stories` differ from the archived stories, with fewer or with more, does not cover them: the status is `due`.
9. A report with `on_branch=True` gives `in_flight`, whatever the folders hold, backlog story files included.
10. A report with `on_branch=True` whose id also has a report with `on_branch=False` is not in flight: the status is `merged_unrecorded` while that main-branch report's stage is not `done`.
11. A report on the main branch whose stage is not `done` gives `merged_unrecorded`, also when the backlog holds the stories the merge brought.
12. A recorded `accepted` result does not stand while a story file waits: with a covering report at `done` and a story file in `backlog`, the status is `incomplete`.
13. `feature_files` and `read` ignore the work tree and local branches: a story file that exists only in the checkout's work tree, or only on a local branch, is not counted.
14. `read()` gives the status `due` for a feature whose `done` folder on `origin/main` holds two story files and whose `in-progress` folder holds only `.gitkeep`, and gives no entry for a directory `notes` under `factory/features`.
15. `read()` gives `accepted` for a feature whose `done` folder holds a report with the outcome `accepted` that covers its archived stories.
16. `read()` gives `in_flight` for a feature with a remote branch `work-item/F0001-A0001` that holds the report, and that feature's `next_acceptance` is `F0001-A0002`.
17. A remote branch `work-item/F0001-A0001` that holds no report file, and a remote branch of a story, do not make a feature `in_flight`.
18. `read()` raises `WorkItemFormatError` whose `path` is the report's path for a report on the main branch whose front matter is not valid YAML, and for one that has no `stories` key.
19. `feature_files` gives three empty lists for a feature that has no directory at the ref.
20. `due_events()` returns one event per due feature with the kind, `work_item=None`, `feature`, `remote_state` (the commit of `origin/main`) and `detail` (the next acceptance id) set as the Interface says, ordered by `work_item_order` of the `detail`.
21. `due_events()` returns `[]` when no feature is due, and `[]` when `definition.acceptance_stage` is `None` although a feature is complete.
22. `fill_board` sets `acceptance` on each row to its feature's status, keeps the order, leaves a row of an unknown feature unchanged, and changes no row when `definition.acceptance_stage` is `None`.
23. The watcher's evaluation, with `F0002` due and the story `F0003-S0001` in progress and runnable, returns the `acceptance_due` event for `F0002`; with the story `F0001-S0001` in progress and runnable it returns that story's `run` event.
24. `make check` stays green.
25. docs: `docs/operator-guide.md` explains when a feature acceptance becomes due (an archived story, no story file in the backlog or in progress, no recorded report covering exactly the archived stories; `.gitkeep` and notes do not count) and the six statuses the board shows.

## Demo

```bash
uv run python -c "
from factory.domain.acceptance import AcceptanceState, FeatureFiles, ReportFacts, acceptance_status
files = FeatureFiles(feature='F0001', backlog=['.gitkeep'], done=['F0001-S0001-a.md', 'F0001-S0002-b.md'])
print(acceptance_status(files, []))
report = ReportFacts(id='F0001-A0001', folder='done', on_branch=False, state=AcceptanceState(stage='done', outcome='refused', stories=['F0001-S0001', 'F0001-S0002']))
print(acceptance_status(files, [report]))
waiting = files.model_copy(update={'in_progress': ['F0001-S0003-c.md']})
print(acceptance_status(waiting, [report]))
print(acceptance_status(files.model_copy(update={'done': ['F0001-S0001-a.md']}), [report]))
"
```
Expect: four lines: `due` (the `.gitkeep` does not keep the feature incomplete), `refused` (the report covers exactly the two archived stories), `incomplete` (a story file is in progress), `due` (the report covers two stories but only one is archived).

```bash
uv run python -c "
from factory.domain.acceptance import story_file_ids
print(story_file_ids(['.gitkeep', 'F0001-S0002-b.md', 'notes.md', 'F0001-A0001-acceptance.md', 'F0001-S0001-a.md']))
"
```
Expect: one line: `['F0001-S0001', 'F0001-S0002']`.

## Log (append only)

1. 2026-10-12 human: created.
