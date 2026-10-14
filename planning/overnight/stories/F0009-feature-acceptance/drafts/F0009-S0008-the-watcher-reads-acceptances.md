# The watcher reads acceptances

## Assignment (as of log entry 1)

Let the watcher's evaluation see acceptances: the features whose acceptance is due, and every acceptance report that is in `in-progress/` on the remote, whether it is still on its own branch or already merged and not yet recorded. F0006's `RemoteWorkItems` reads stories only and excludes acceptance ids, so without this story no `merged` event would ever be raised for an acceptance, its status would stay `merged_unrecorded` for ever, and the tiers could not rank a due acceptance against the runnable stories. A new reading, `AcceptanceReader.snapshots()`, gives one `WorkItemSnapshot` for every acceptance whose report is in `in-progress/` on `origin/main` or on its own branch, in the rules F0006-S0001 uses for stories. `Watcher.evaluate` joins them with the stories in `work_item_order` and hands the due features to the evaluation in a new field, `EvaluationInput.due`; the fourth tier ranks a due feature after the feature's own stories and before the next feature's (ST6.3 in the evaluation, for a slug that starts with a digit and for a missing slug), and tiers 2 and 3 still outrank it. The board reader fills the acceptance column. The evaluation builds the `acceptance_due` event itself, and no code reads an event's `detail` back. Covers ST6.2 and ST6.3 (the evaluation side), ST2.1 and ST2.2 (the `merged` event of a merged report, S0011 walks it over ticks) and R18; keeps kept thing 19, kept thing 3 (the remote is read, never the work tree) and kept thing 15 (id order). Changes code of F0006 (`evaluate`, `Watcher.evaluate`, `BoardReader.read`) with the additions below and nothing else. Uses `AcceptanceReader` (S0002), `AcceptanceService.open` (S0003) and the handlers of S0004 and S0005 only to set the tests up.

## Interface

`src/factory/domain/evaluation.py` (F0006-S0002's module; one field and one rule grow)

```python
class EvaluationInput(BaseModel):
    definition: PipelineDefinition
    snapshots: list[WorkItemSnapshot]
    main_commit: CommitId
    due: list[FeatureId] = []         # the features whose acceptance is due (F0009-S0008)
```

`src/factory/application/acceptance_reading.py` (grown)

```python
class AcceptanceReader:
    def snapshots(self) -> list[WorkItemSnapshot]: ...
```

`src/factory/application/watcher.py` (F0006-S0002's `Watcher.evaluate` grows) and `src/factory/application/board.py` (F0006-S0006's `BoardReader.read` grows): no signature changes.

Rules:

- Tier 4 of `evaluate` has two kinds of candidates: the runnable snapshots, as F0006-S0002 defines them, and the features in `due`. They are ranked by one key: a snapshot by `work_item_order(<its id>)`, a due feature by `(<the feature id>, 1, "")`. The first candidate decides. A snapshot decides as before (`ask` at the attempts cap, else `run`). A due feature gives `Event(kind="acceptance_due", work_item=None, feature=<the feature>, remote_state=main_commit, detail="acceptance of <feature> is due")`; `detail` is display only. Tiers 1 to 3 are unchanged and win over a due feature. `due` empty is F0006's behaviour exactly.
- `snapshots()` returns `[]` when `definition.acceptance_stage` is `None`. Otherwise it returns one snapshot for every acceptance id whose report file is in `in-progress/` of the feature (a directory under `factory/features` whose name `parse_feature_directory_name` reads as the id's feature) on `origin/main`, or at `origin/work-item/<id>`; never two snapshots for one id. `path` is the report's path on `origin/main` when it is there, else its path on the branch; `folder` is `in-progress`; `branch` is `branch_name(id)`; `branch_commit` is the commit of `origin/<branch>`, or `None` without that ref; `document` is the work item reader's parse of the file at `origin/<branch>` when the branch holds a file at that path, else of the file on `origin/main`, and its state must be an `AcceptanceState`, else `WorkItemFormatError` with `path` set. A report that is in `done/` on `origin/main` and in no `in-progress/` gives no snapshot, unless a remote branch still holds it in `in-progress/` (the leftover of a kill between the booking and the deletion of the branch): then the branch's snapshot is given, so that the `merged` event lets the handler finish. Story branches and remote acceptance branches without a report file are ignored. The result is ordered by `work_item_order(id)`. Only `Git.resolve`, `list_files`, `show_file` and `remote_branches` are used: no work tree, no local branch, no hosting call.
- `Watcher.evaluate(definition)` resolves `origin/main` first, as F0006-S0002 says (a `None` is `GitError`), then reads the stories as before, builds `AcceptanceReader(boundaries, definition)`, and passes `snapshots=sorted([*stories, *reader.snapshots()], key=lambda s: (work_item_order(s.id), s.path))` and `due=reader.due_features()` to `evaluate`. For stories alone the order is the one `RemoteWorkItems.read` returns (plain id order is `work_item_order` within a feature's stories).
- `BoardReader.read(definition)` ends with `AcceptanceReader(boundaries, definition).fill_board(<its feature rows>)`; its other rows and the board command's output are as F0006-S0006 defines them. `fill_board` is the S0002 function; the rows come from `BoardReader`, not from the entry module.
- No test of F0006 changes. The drafted tests of F0006-S0002 (c19 to c22) and F0006-S0006 (c12 to c15, c22) run the watcher and `run_watch` over the fixture, whose feature `F0001` has a backlog story: it stays `incomplete`, no feature is due, no acceptance report exists, nothing new is read from the hosting service, and none of those tests reads the acceptance cell of the board. A test that archives the fixture's only story and then evaluates or ticks sees `acceptance_due` where it saw `idle`; as far as the drafts of F0006 to F0008 show, none does (F0007-S0003 and F0007-S0010 read `origin/main` after the archive without a tick, F0008-S0004 criterion 2 calls a function), and a future one pushes a second backlog story.

Tests: `tests/domain/test_evaluation_due.py`, `tests/application/test_acceptance_snapshots.py`, `tests/application/test_watcher_acceptance.py`, `tests/entry/test_watch_acceptance.py` (new files: the tests of F0006 stay as they are); the fixtures `remote`, `checkout`, `human`, `hosting`, `clock` and `boundaries`, with `install_agents(agent_home, <the roles of the fixture's pipeline definition>)` for `run_watch`'s definition. The evaluation tests use hand-built snapshots and plain functions for the lookup and the claim status, as F0006-S0002's do. The remote tests push a feature `F0002-todo` of their own (`feature.md` and story files under `done/`, nothing under `backlog/` or `in-progress/`), and open acceptances with `AcceptanceService.open`; a pull request number and a stage are written into a report's state on its branch with `human.push_file`; the human merges with `human.merge(branch, method)` and `hosting.merge_by_human`. The closed-model test builds `EvaluationInput` through a variable typed `type[BaseModel]`.

## Acceptance criteria

1. `EvaluationInput.due` is `[]` by default, accepts `["F0002"]` and refuses `["F002"]` with `ValidationError`, and `EvaluationInput` still refuses an unknown key.
2. With `due == ["F0002"]` and a runnable `F0003-S0001`, `evaluate` returns an event of kind `acceptance_due` with `work_item` `None`, `feature == "F0002"` and `remote_state` equal to `main_commit`; with a runnable `F0001-S0001` instead it returns that story's `run` event.
3. With `due == ["F0002"]` and a runnable `F0002-S0003`, `evaluate` returns the `run` event of `F0002-S0003`: a feature's acceptance comes after its own stories (ST6.3).
4. A waiting work item (blocked, with an open pull request and nothing new) and a held claim each give `idle` although `due` is `["F0002"]`: tiers 2 and 3 win over a due feature (two cases, one test).
5. `snapshots()` returns, for the branch `work-item/F0001-A0001` that holds `factory/features/F0001-todo/in-progress/F0001-A0001-acceptance.md` and has no report on the main branch, one snapshot with that id, that path, folder `in-progress`, branch `work-item/F0001-A0001`, the commit of `origin/work-item/F0001-A0001` and the report read from the branch.
6. `snapshots()` skips a story branch and a `work-item/F0001-A0001` branch without the report file.
7. A merged report that is not yet recorded (the report is in `in-progress/` on `origin/main`, and the branch still exists) gives one snapshot: its path is the one on the main branch, the branch fields are the branch's, and the document is read from the branch.
8. A merged report whose branch the hosting service deleted gives one snapshot with `branch_commit` `None` and the document read from `origin/main`.
9. A report in `done/` on `origin/main` gives no snapshot; the same report with a remote branch that still holds it in `in-progress/` (the leftover of a kill) gives one snapshot, read from the branch.
10. `snapshots()` returns the snapshots of two features, one from a branch and one from the main branch, in `work_item_order`.
11. `snapshots()` raises `WorkItemFormatError` with the report's path for a report on a branch whose state is a plain work item state (no `stories` key), and returns `[]` when `definition.acceptance_stage` is `None`.
12. The watcher's evaluation, with an in-flight acceptance at stage `acceptance` and no claim on its branch, returns a `run` event whose work item is that acceptance.
13. ST6.3 in the evaluation, parametrised on the feature directory `F0002-2fa` and `F0002`: an in-flight `F0002-A0001` at stage `acceptance` and a started, runnable story `F0002-S0003` in `in-progress/` give the `run` event of `F0002-S0003`.
14. A merged pull request of an acceptance at the stage `approval`, whose report is in `in-progress/` on the main branch, gives the `merged` event for that acceptance, carrying its snapshot and the merged view, and not a `reject` event.
15. A due feature `F0002` gives the `acceptance_due` event with `feature == "F0002"`, no work item and `remote_state` equal to the head of `origin/main`.
16. With `definition.acceptance_stage` `None`, the evaluation gives `idle` although a feature is complete and an acceptance report is on the remote, as F0006 does.
17. `run_watch` on a remote with the due feature `F0002-todo` (two story files in `done/`) writes `event: acceptance_due:F0002` as its first line and, in the board, the row `F0002  Todo service  backlog=0  in-progress=0  done=2  acceptance=due` and for the fixture's feature `F0001` the cell `acceptance=incomplete`.
18. `BoardReader.read(definition)` leaves every row's `acceptance` `None` when `definition.acceptance_stage` is `None`, and `run_watch` then prints `acceptance=-` for every feature.
19. make check stays green.
20. docs: `docs/project-guide.md` states that `AcceptanceReader.snapshots()` reads the acceptances' reports in `in-progress/` from the main branch and from their branches (merged and not yet recorded included), that `Watcher.evaluate` joins them with the stories in `work_item_order` and passes the due features in `EvaluationInput.due`, and the fourth tier's ranking; `docs/operator-guide.md` explains the board's acceptance column and that a due acceptance runs after the feature's stories.

## Demo

```bash
uv run python -c "
from factory.domain.evaluation import EvaluationInput, evaluate
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, initial_state
definition = PipelineDefinition(contract='1.0', stages={'intake': StageDefinition(role='intake', next=['approval']), 'approval': StageDefinition(approval=True, next=['done']), 'done': StageDefinition()}, roles={'intake': RoleDefinition(write_paths=['{work_item}'])})
def story(work_item):
    return WorkItemSnapshot(id=work_item, path='factory/features/F0002-x/in-progress/' + work_item + '-y.md', folder='in-progress', branch='work-item/' + work_item, branch_commit=None, document=WorkItemDocument(state=initial_state('intake'), body='# T\n'))
def lookup(number):
    raise AssertionError('no pull request is looked up')
for snapshots in ([story('F0003-S0001')], [story('F0002-S0003')], [story('F0001-S0001')]):
    facts = EvaluationInput(definition=definition, snapshots=snapshots, main_commit='a' * 40, due=['F0002'])
    print(evaluate(facts, lookup, lambda state: 'none').key)
"
```
Expect: three lines: `acceptance_due:F0002` (the next feature's story comes after the due acceptance), `run:F0002-S0003` (the feature's own story comes first), `run:F0001-S0001` (an earlier feature's story comes first).

## Log (append only)

1. 2026-10-12 human: created.
