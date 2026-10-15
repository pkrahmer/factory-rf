---
stage: doing
pr: 110
blocked: null
comments_seen: 2
round: 1
attempts: 0
---
# The watcher reads acceptances

## Assignment (as of log entry 1)

Let the watcher's evaluation see acceptances: the features whose acceptance is due, and every acceptance report that is in `in-progress/` on the remote, whether it is still on its own branch or already merged and not yet recorded. F0006's `RemoteWorkItems` reads stories only and excludes acceptance ids, so without this story no `merged` event would ever be raised for an acceptance, its status would stay `merged_unrecorded` for ever, and the tiers could not rank a due acceptance against the runnable stories. A new reading, `AcceptanceReader.snapshots()`, gives one `WorkItemSnapshot` for every acceptance whose report is in `in-progress/` on `origin/main` or on its own branch, in the rules F0006-S0001 uses for stories. `Watcher.evaluate` joins them with the stories in `work_item_order` and hands the due features to the evaluation in a new field, `EvaluationInput.due`; the fourth tier ranks a due feature after the feature's own stories and before the next feature's (ST6.3 in the evaluation, for a slug that starts with a digit and for a missing slug), and tiers 2 and 3 still outrank it. The board reader fills the acceptance column. The evaluation builds the `acceptance_due` event itself, and no code reads an event's `detail` back. Covers ST6.2 and ST6.3 (the evaluation side), ST2.1 and ST2.2 (the `merged` event of a merged report, S0011 walks it over ticks) and R18; keeps kept thing 19, kept thing 3 (the remote is read, never the work tree) and kept thing 15 (id order). Changes code of F0006 (`evaluate`, `Watcher.evaluate`, `BoardReader.__init__`, which now keeps the boundaries, and `BoardReader.read`) with the additions below and nothing else, and one test of F0006-S0006 as the Rules name it. Uses `AcceptanceReader` (S0002), `AcceptanceService.open` (S0003) and the handlers of S0004 and S0005 only to set the tests up.

## Interface

`src/factory/domain/evaluation.py` (F0006-S0002's module; one field and one rule grow)

```python
class EvaluationInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    definition: PipelineDefinition
    snapshots: list[WorkItemSnapshot]
    main_commit: CommitId
    illegal_changes: list[IllegalChange] = []
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
- `Watcher.evaluate(definition)` resolves `origin/main` first, as F0006-S0002 says (a `None` is `GitError`), then reads the stories as before, builds `AcceptanceReader(boundaries, definition)`, and passes `snapshots=sorted([*stories, *reader.snapshots()], key=lambda s: (work_item_order(s.id), s.path))`, `illegal_changes` computed by F0006-S0005's move rule over that same joined list, so that a stage change on an acceptance's branch that the definition does not allow is rejected like a story's, and `due=reader.due_features()` to `evaluate`. For stories alone the order is the one `RemoteWorkItems.read` returns (plain id order is `work_item_order` within a feature's stories).
- `BoardReader.read(definition)` ends with `AcceptanceReader(boundaries, definition).fill_board(<its feature rows>)`; its other rows and the board command's output are as F0006-S0006 defines them. `fill_board` is the S0002 function; the rows come from `BoardReader`, not from the entry module.
- One test of F0006 changes, with the human's leave (the feature's decision 22), and nothing else of its file: in `tests/application/test_board_reader.py`, `test_only_story_files_count_on_main` (F0006-S0006) expects `[FeatureRow(feature="F0001", title="Example feature", backlog=1, in_progress=0, done=0, acceptance="incomplete")]`, because `BoardReader.read` now fills the acceptance column and the fixture's `F0001` has a backlog story. Every other test of F0006 stays as it is: the watcher, tick and `run_watch` tests run over the fixture, whose `F0001` stays `incomplete`, no feature is due and no acceptance report exists; `tests/entry/test_watch.py` compares `run_watch`'s output with `BoardReader.read` itself; and no test of F0006 to F0008 archives the fixture's only story and then evaluates or ticks.

Tests: `tests/domain/test_evaluation_due.py`, `tests/application/test_acceptance_snapshots.py`, `tests/application/test_watcher_acceptance.py`, `tests/entry/test_watch_acceptance.py` (new files; the one changed test of F0006 is named in the Rules); the fixtures `remote`, `checkout`, `human`, `hosting`, `clock` and `boundaries`, with `install_agents(agent_home, <the roles of the fixture's pipeline definition>)` for `run_watch`'s definition. The evaluation tests use hand-built snapshots and plain functions for the lookup and the claim status, as F0006-S0002's do. The remote tests push a feature `F0002-todo` of their own (`feature.md` and story files under `done/`, nothing under `backlog/` or `in-progress/`), and open acceptances with `AcceptanceService.open`; a pull request number and a stage are written into a report's state on its branch with `human.push_file`; the human merges with `human.merge(branch, method)` and `hosting.merge_by_human`. The closed-model test builds `EvaluationInput` through a variable typed `type[BaseModel]`. The changed test of F0006-S0006 named in the Rules stays in its file. Criterion 13 pushes its feature under the directory it names, opens the acceptance while the feature is due, and only then pushes and starts `F0002-S0003`.

## Acceptance criteria

1. `EvaluationInput.due` is `[]` by default, accepts `["F0002"]` and refuses `["F002"]` with `ValidationError`, and `EvaluationInput` still refuses an unknown key.
2. With `due == ["F0002"]` and a runnable `F0003-S0001`, `evaluate` returns an event of kind `acceptance_due` with `work_item` `None`, `feature == "F0002"` and `remote_state` equal to `main_commit`; with a runnable `F0001-S0001` instead it returns that story's `run` event.
3. With `due == ["F0002"]` and a runnable `F0002-S0003`, `evaluate` returns the `run` event of `F0002-S0003`: a feature's acceptance comes after its own stories (ST6.3).
4. A waiting work item (at an approval stage, `handed_over` equal to its stage, its pull request open with no unread human comment) and a held claim each give `idle` although `due` is `["F0002"]`: tiers 2 and 3 win over a due feature (two cases, one test).
5. `snapshots()` returns, for the branch `work-item/F0002-A0001` that holds `factory/features/F0002-todo/in-progress/F0002-A0001-acceptance.md` while `origin/main` holds the feature `F0002-todo` and no report of it, one snapshot with that id, that path, folder `in-progress`, branch `work-item/F0002-A0001`, the commit of `origin/work-item/F0002-A0001` and the report read from the branch.
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
17. `run_watch` on a remote with the due feature `F0002-todo` (two story files in `done/`) writes `event: acceptance_due:F0002  acceptance of F0002 is due` as its first line and, in the board, the row `F0002  Todo service  backlog=0  in-progress=0  done=2  acceptance=due` and for the fixture's feature `F0001` the cell `acceptance=incomplete`.
18. `BoardReader.read(definition)` leaves every row's `acceptance` `None` when `definition.acceptance_stage` is `None`, and `run_watch` then prints `acceptance=-` for every feature.
19. An in-flight acceptance whose branch's last commit, pushed by the human, changed its stage from `acceptance` to `intake` gives the `reject` event of that acceptance.
20. `snapshots()` gives no snapshot for an acceptance report on `origin/main` in another feature's `in-progress/` (`factory/features/F0001-example/in-progress/F0002-A0001-acceptance.md`), nor for a branch `work-item/F0004-A0001` whose report sits under a feature directory that `origin/main` lacks.
21. make check stays green.
22. docs: `docs/project-guide.md` states that `AcceptanceReader.snapshots()` reads the acceptances' reports in `in-progress/` from the main branch and from their branches (merged and not yet recorded included), that `Watcher.evaluate` joins them with the stories in `work_item_order` and passes the due features in `EvaluationInput.due`, and the fourth tier's ranking; `docs/operator-guide.md` explains the board's acceptance column and that a due acceptance runs after the feature's stories.

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
2. intake: accepted
   - Interface: concrete modules and signatures (EvaluationInput.due, AcceptanceReader.snapshots(), the unchanged Watcher.evaluate and BoardReader.read) and the tier-4 ranking key, the snapshot fields and the join are all stated. due_features() and fill_board come from S0002, as the story says.
   - Criteria: each is testable by one test function. Every Interface rule has both sides: due validation (1: accepts F0002, refuses F002, unknown key); acceptance_stage None (11, 16, 18); non-acceptance state raising WorkItemFormatError (11); skipped story and report-less branches (6); done/ with and without a leftover branch (9); merged with the branch present or deleted (7, 8); tiers 2 and 3 over a due feature (4); a due feature after its own stories, before the next feature's and after an earlier feature's (2, 3, 13); an illegal stage change rejected (19).
   - Demo: a runnable python -c script. Its Expect line names the three output keys, which can be checked.
   - Architecture: the changes fall in domain (evaluation) and application (reader, watcher, board). Only Git.resolve, list_files, show_file and remote_branches are used, with no work tree, so the layers hold.
   - Scope: inside FEATURE.md ("the watcher's evaluation takes the due features and the reports in in-progress/ into account", and the board column). The one F0006 test change is covered by feature decision 22.
3. tester: red tests written for every criterion; make lint green.
   - criterion 1: tests/domain/test_evaluation_due.py::test_due_is_empty_by_default_and_holds_feature_ids, ::test_evaluation_input_refuses_a_malformed_due_and_an_unknown_key (F002, unknown key; through a variable typed type[BaseModel])
   - criterion 2: tests/domain/test_evaluation_due.py::test_a_due_feature_ranks_after_earlier_and_before_later_features_stories (F0003-S0001 gives acceptance_due, F0001-S0001 gives run)
   - criterion 3: tests/domain/test_evaluation_due.py::test_a_features_own_story_runs_before_its_due_acceptance
   - criterion 4: tests/domain/test_evaluation_due.py::test_a_waiting_work_item_and_a_held_claim_win_over_a_due_feature (two cases)
   - criterion 5: tests/application/test_acceptance_snapshots.py::test_a_report_on_its_branch_alone_gives_its_snapshot
   - criterion 6: tests/application/test_acceptance_snapshots.py::test_a_story_branch_and_an_acceptance_branch_without_a_report_are_skipped
   - criterion 7: tests/application/test_acceptance_snapshots.py::test_a_merged_report_not_yet_recorded_has_mains_path_and_the_branchs_document (after the merge the human pushes a changed state to the branch, so branch and main differ)
   - criterion 8: tests/application/test_acceptance_snapshots.py::test_a_merged_report_whose_branch_is_deleted_is_read_from_main (the branch is deleted on the bare remote, then fetched with prune)
   - criterion 9: tests/application/test_acceptance_snapshots.py::test_a_recorded_report_gives_a_snapshot_only_from_a_leftover_branch (recorded / leftover-branch)
   - criterion 10: tests/application/test_acceptance_snapshots.py::test_snapshots_of_two_features_come_in_work_item_order (F0002 from its branch, F0003 from main, so a "main first" order fails)
   - criterion 11: tests/application/test_acceptance_snapshots.py::test_a_report_with_a_plain_work_item_state_is_a_format_error_with_its_path, ::test_no_acceptance_stage_gives_no_snapshots
   - criterion 12: tests/application/test_watcher_acceptance.py::test_an_in_flight_acceptance_without_a_claim_runs
   - criterion 13: tests/application/test_watcher_acceptance.py::test_a_started_story_of_the_feature_runs_before_its_in_flight_acceptance (F0002-2fa, F0002)
   - criterion 14: tests/application/test_watcher_acceptance.py::test_a_merged_acceptance_at_its_approval_is_a_merged_event (parametrised on merge, squash and rebase; the event's work_item must equal AcceptanceReader.snapshots()[0] and pull_request must equal the merged view)
   - criterion 15: tests/application/test_watcher_acceptance.py::test_a_due_feature_is_an_acceptance_due_event_at_mains_head
   - criterion 16: tests/application/test_watcher_acceptance.py::test_without_an_acceptance_stage_acceptances_and_due_features_are_not_seen
   - criterion 17: tests/entry/test_watch_acceptance.py::test_run_watch_shows_a_due_acceptance_as_its_event_and_in_the_board
   - criterion 18: tests/entry/test_watch_acceptance.py::test_without_an_acceptance_stage_the_board_has_no_acceptance_status (pushes factory/pipeline.yml without the acceptance_stage line, so run_watch loads that definition)
   - criterion 19: tests/application/test_watcher_acceptance.py::test_a_stage_change_the_definition_forbids_on_an_acceptance_branch_is_rejected
   - F0006 test changed, as the Rules allow: tests/application/test_board_reader.py::test_only_story_files_count_on_main now expects acceptance="incomplete" for F0001.
   Files created: tests/domain/test_evaluation_due.py, tests/application/test_acceptance_snapshots.py, tests/application/test_watcher_acceptance.py, tests/entry/test_watch_acceptance.py. Changed: tests/application/test_board_reader.py.
   Import errors: none. Every module under test already exists; the tests fail because EvaluationInput has no `due` field yet (it is refused as an unknown key), AcceptanceReader has no `snapshots()`, and the watcher and BoardReader do not read acceptances yet. make test ran once and was red. Its output was cut off to the last lines, so I saw only some of the failure reasons: the shown failures are the evaluation_due tests and the run_watch board test. The type check was not run in this stage.
   Open: none.

   `make lint`: lint: green
   `make test`: FAILED tests/entry/test_watch_acceptance.py::test_run_watch_shows_a_due_acceptance_as_its_event_and_in_the_board
4. coder: the watcher now reads acceptances, and the evaluation ranks due features in tier 4. `make check` is green: lint, types, layers, sast, secrets, licenses, and tests at 99.5 % coverage.
      - `src/factory/domain/evaluation.py`: added `EvaluationInput.due: list[FeatureId] = []`. `_new_work` now collects two kinds of candidate: the runnable pairs, keyed by `work_item_order(id)`, and the due features, keyed by `(feature, 1, "")` through `_due_order`. The smallest key decides, and ties go to the first in list order. A due feature gives `acceptance_due` with `feature` set, no work item, `remote_state=main_commit` and detail `acceptance of <F> is due`. A snapshot gives `run`, or `ask` at the attempts cap, as before. Tiers 1 to 3 are unchanged.
      - `src/factory/application/acceptance_reading.py`: added `AcceptanceReader.snapshots()`. It returns `[]` without an acceptance stage. Report paths come first from the acceptance branches (in-progress file of the id under the feature's directory on main) and are then overwritten by main's in-progress reports, so main's path wins. The document is read from `origin/<branch>` when that ref exists and holds the file at the path, otherwise from main. Snapshots are sorted by `work_item_order`. The existing state check moved into a shared `_document(ref, path)`, which `_report` also uses, so a non-acceptance state raises `WorkItemFormatError` with the path in both readings.
      - `src/factory/application/watcher.py`: `Watcher.evaluate` joins the stories and `snapshots()`, sorted by `(work_item_order(id), path)`. It runs the move rule over the joined list and passes `due=reader.due_features()`.
      - `src/factory/application/board.py`: `BoardReader.__init__` keeps the boundaries, and `read` passes its feature rows through `AcceptanceReader(...).fill_board`.
      - Commits: 66d1d99 (feat), b0efa13 (refactor: the duplicated loop that looked up a report's paths on its branch, used by `_branch_reports` and `snapshots()`, is now one helper `_branch_report_paths_at`).
      - Design decision: one sort key over a mixed candidate list, instead of finding the first runnable snapshot and comparing it with the first due feature. This matches the Interface rule "ranked by one key". For a list already in id order and `due` empty, the result is the same as F0006's, and the F0006 tests stay green.
      - Noticed, not touched:
        - `snapshots()` only finds feature directories as they are on `origin/main`, so a report on a branch whose feature directory is missing on main is ignored. That uncovered `continue` is `acceptance_reading.py:121`.
        - With the `(F, 1, "")` key, a due feature would rank before an acceptance snapshot of the same feature. In practice they cannot exist together, because a feature with an open acceptance is not due.

   `make check`: check: green
5. reviewer: findings in group 1 (acceptance criteria). I stopped there, as the checklist says. Criteria 1 to 19 each have a test that checks what the criterion says. The coder's entry reports `make check` green. The code matches the Interface: the tier-4 key `(feature, 1, "")`, the joined sort in `Watcher.evaluate`, main's path winning in `snapshots()`, the document read from the branch when the branch holds it, and `BoardReader` keeping the boundaries. Both gaps below are gaps in the story, not the tester's: the Interface states the rule, but no criterion names its failing side.
   1. `src/factory/application/acceptance_reading.py:112` (`_main_report_paths`, the `_is_report_of` filter). The Interface rule says the report is in `in-progress/` "of the feature (a directory … whose name `parse_feature_directory_name` reads as the id's feature)". Its failing side is untested: an acceptance report on `origin/main` in another feature's directory, for example `factory/features/F0001-example/in-progress/F0002-A0001-acceptance.md`, must give no snapshot. Fix: the human adds a criterion for this case, and the tester adds it as a row of the parametrized skip test in `tests/application/test_acceptance_snapshots.py` (criterion 6's).
   2. `src/factory/application/acceptance_reading.py:120-121` (`_branch_report_paths`, `if directory is None: continue`). The same rule's failing side on the branch side is untested: a branch `work-item/F0004-A0001` holds a report under a feature directory that `origin/main` lacks, and it must give no snapshot. The coder's entry names this as the uncovered line. Fix: the same criterion, or a second one, as another row of that parametrized test.
   Not reviewed past group 1: groups 2 to 5 (architecture, security, quality, ticket hygiene). The coder cannot write tests, so the next step is a `question` to the human asking whether to add these criteria.
6. coder: coder (round 1): question for the human about the reviewer's two findings in entry 5. Both findings are missing tests. Neither needs a code change. I can't add tests or criteria myself (R9, R13), so I'm asking before anything moves.

   What the code does now (unchanged since 66d1d99/b0efa13):
   - Main side: `src/factory/application/acceptance_reading.py`, `_main_report_paths`. It reads only the `in-progress/` folder of each feature directory on `origin/main`. It keeps a file only if `_is_report_of(id, feature)` holds. So `factory/features/F0001-example/in-progress/F0002-A0001-acceptance.md` gives no snapshot.
   - Branch side: `_branch_report_paths`. It looks for the branch's report only under the directory of the id's own feature as `origin/main` has it. If main has no such directory, it skips the branch (`continue`). So `work-item/F0004-A0001` with a report under a feature directory that main lacks gives no snapshot.

   Both behaviours follow the Interface rule ("in-progress/ of the feature (a directory … whose name parse_feature_directory_name reads as the id's feature)"). No criterion covers the refused side, and CLAUDE.md asks for both sides of every limit.

   Options:
   (a) Add one criterion before the two closing ones. Suggested wording: "`snapshots()` gives no snapshot for an acceptance report on `origin/main` in another feature's `in-progress/` (`factory/features/F0001-example/in-progress/F0002-A0001-acceptance.md`), nor for a branch `work-item/F0004-A0001` whose report sits under a feature directory that `origin/main` lacks." The tester adds both as rows of criterion 6's parametrized test, `tests/application/test_acceptance_snapshots.py::test_a_story_branch_and_an_acceptance_branch_without_a_report_are_skipped`. The ticket then goes back through tests and to review with no code change.
   (b) Leave the criteria as they are and accept the gap. The reviewer would then need to stop counting it as a finding.

   I'd choose (a): the behaviour already exists, and the tests would only pin it down.

   Nothing else changed this round. `make check` was green at b0efa13 (entry 4); I didn't re-run it because I changed no code.
7. human (pull request comment, 2026-10-15): (a): add the criterion before the two closing ones, as you worded it, and the tester adds both cases as rows of criterion 6's parametrized test `test_a_story_branch_and_an_acceptance_branch_without_a_report_are_skipped`. No code change. The Interface stays as it is.
8. coder: coder (round 1): the human chose (a) in entry 7, so this round needs a test change. I made no code change.
   - Ticket: added criterion 20 before the two closing ones, in the wording the human approved. It says `snapshots()` gives no snapshot for an acceptance report on `origin/main` in another feature's `in-progress/` (`factory/features/F0001-example/in-progress/F0002-A0001-acceptance.md`), nor for a branch `work-item/F0004-A0001` whose report sits under a feature directory that `origin/main` lacks. The closing criteria are renumbered: `make check` is now 21 and `docs:` is 22. `## Assignment` is unchanged.
   - Test change for the tester: in `tests/application/test_acceptance_snapshots.py::test_a_story_branch_and_an_acceptance_branch_without_a_report_are_skipped`, add two parametrized rows for criterion 20, each expecting `snapshots() == []`:
     1. the report `F0002-A0001` pushed to `origin/main` under `factory/features/F0001-example/in-progress/`;
     2. a branch `work-item/F0004-A0001` holding a report under a feature directory that `origin/main` lacks.
   - The code at b0efa13 should already pass both rows: `_main_report_paths` filters with `_is_report_of`, and `_branch_report_paths` skips a branch whose feature directory is missing (`acceptance_reading.py:120-121`). If either row fails, it comes back to doing.
   Open: none.
9. tester: tester (round 1, approved test change): I added the two rows that the human approved in entry 7 and the coder named in entry 8. They go into `tests/application/test_acceptance_snapshots.py::test_a_story_branch_and_an_acceptance_branch_without_a_report_are_skipped`. Each new row expects `snapshots() == []`.
      - Row `report-in-another-features-directory-on-main`: the report `F0002-A0001` is pushed to `main` under `factory/features/F0001-example/in-progress/F0002-A0001-acceptance.md`.
      - Row `branch-report-under-a-feature-directory-main-lacks`: the branch `work-item/F0004-A0001` holds `factory/features/F0004-missing/in-progress/F0004-A0001-acceptance.md`, and `origin/main` has no F0004 directory.
      - The test gained a third parameter, `report: bool`. The new rows push a real acceptance document (`_render(boundaries, _approval())`) and not placeholder text, so each row is skipped because of where the file sits, not because its content is unreadable. The two existing rows are unchanged; they use `report=False` and still push "# Not a report".
      - This is criterion 20, in the same parametrized test as criterion 6.
      `make test` is green (coverage 99.53 %), so the code at b0efa13 already passes both rows, as the coder expected. `make lint` is green. No other file was changed.
      Open: none.

   `make lint`: lint: green
   `make test`: test: green
