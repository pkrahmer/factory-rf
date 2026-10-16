---
stage: doing
pr: 115
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A running acceptance on the board

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

`factory-watch` prints a work item row for every story in `in-progress/`, with its stage, what it waits for, its claim and its pull request. A running acceptance gets no row. While `F0002-A0001` runs, waits with a question or waits at its approval for the human, the board shows only `acceptance=in_flight` in the feature's row, and its `work items` list can be empty. The feature acceptance's demo showed this: with `F0003-A0002` opened and the next event `run:F0003-A0002`, the board listed no work item. The operator cannot see on the board that an acceptance waits for them, or which pull request to open. This story gives every acceptance that `AcceptanceReader.snapshots()` returns a work item row of its own, built the same way as a story's row and placed by `work_item_order`, so an acceptance comes after its feature's stories. The feature rows and the event line stay as they are.

## Interface

`src/factory/application/board.py`: `BoardReader.read(definition)` keeps its signature. Its `rows` are `work_item_row(snapshot)` for every snapshot of `RemoteWorkItems.read(definition)` and of `AcceptanceReader(boundaries, definition).snapshots()`, joined and sorted by `work_item_order(snapshot.id)`. A definition without an `acceptance_stage` gives no acceptance rows, because `snapshots()` returns `[]` for it. `work_item_row` (`src/factory/domain/board.py`) is unchanged. An acceptance's row is titled by its report's first `# ` title (`Acceptance of <feature title>`). Its folder is `in-progress`, and its stage, `blocked`, claim, `running_since` and pull request come from the report's state as the snapshot holds it (the branch's document while the branch holds the report).

Errors: a report that `snapshots()` cannot read raises `WorkItemFormatError` from `read`, as `snapshots()` already does for the watcher's evaluation.

Tests: one new module, `tests/application/test_board_reader_acceptance.py`, with the fixtures of `tests/conftest.py`. The `walk` fixture pushes `F0002-todo` (title `Todo service`, two archived stories) and installs the agents; the module does not push that feature itself. An acceptance is opened with `AcceptanceService(boundaries, walk.definition).open("F0002")` after a fetch; its state on its branch is set with `walk.record(...)`; a claim is set by pushing the rendered report with that state to `work-item/F0002-A0001` with `human.push_file`. The merged case: `walk.open("F0002-A0001")` (one tick and the draft pull request), `walk.record("F0002-A0001", <number>, [], stage="approval", handed_over="approval")`, `walk.merge("F0002-A0001", <number>)`, and the branch deleted on the bare remote with `run_git(remote, "branch", "-D", "work-item/F0002-A0001")`, as `tests/application/test_acceptance_snapshots.py` does; it is booked into `done/` by one `walk.tick()`. A definition without an acceptance stage is `walk.definition.model_copy(update={"acceptance_stage": None})`. No existing test module changes.

## Acceptance criteria

1. With the acceptance `F0002-A0001` opened on its branch and no story in progress, `BoardReader(boundaries).read(definition).rows` is one row: `work_item == "F0002-A0001"`, `title == "Acceptance of Todo service"`, `folder == "in-progress"`, `stage == "acceptance"`, `blocked is None`, `claim is None`, `pull_request is None`.
2. After the report's state on its branch is set to stage `approval`, `pull_request` 3 and `blocked` `question`, the acceptance's row shows `stage == "approval"`, `pull_request == 3` and `blocked == "question"`.
3. With the report's state on its branch holding a claim of `factory-1` at stage `acceptance`, the acceptance's row has `claim` equal to that claim and `running_since` equal to its `started_at`.
4. The rows are in `work_item_order`, in one parametrized test with the acceptance `F0002-A0001` opened in each row: with the story `F0001-S0001` started, the order is `F0001-S0001`, `F0002-A0001`; with `F0001-S0001` started and a story `F0003-S0001` in `in-progress/` of `F0003-later`, it is `F0001-S0001`, `F0002-A0001`, `F0003-S0001`; and with the story `F0002-S0003` pushed to `F0002-todo`'s backlog and started after the opening, it is `F0002-S0003`, `F0002-A0001`.
5. A merged acceptance not yet recorded (its report in `in-progress/` on `origin/main`, the branch deleted) still has its row. Once it is booked into `done/`, it has none.
6. With a pipeline definition without an `acceptance_stage`, an acceptance branch on the remote adds no row, and the story rows are still there.
7. `run_watch` prints the acceptance's row under `work items` in the same column format as a story's row: `F0002-A0001  Acceptance of Todo service  in-progress  stage=acceptance  blocked=-  claim=-  running_since=-  pull_request=-`.
8. A report on the acceptance's branch whose front matter is a plain work item state (no `stories` or `outcome` key) makes `BoardReader(boundaries).read(definition)` raise `WorkItemFormatError` whose `path` is the report's path.
9. `make check` stays green.
10. docs: the operator guide's `factory-watch` section says that a work item row exists for each story in `in-progress/` and for each running acceptance, and that an acceptance's row comes after its feature's stories; the project guide's "The watcher's command line" says that the board's rows are those of `RemoteWorkItems.read` and `AcceptanceReader.snapshots()`, sorted by `work_item_order`.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_board_reader_acceptance.py
```
Expect: the last line is `<n> passed in <time>`, with n at least 10 (criteria 1 to 8, criterion 4 with three rows).

```bash
awk '/^## /{s=($0=="## Looking at the remote: `factory-watch`")} s && /running acceptance/' docs/operator-guide.md
```
Expect: at least one line, each from the `factory-watch` section (the command prints nothing from any other section).

## Log (append only)

1. 2026-10-16 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`BoardReader.read(definition)` unchanged, `AcceptanceReader(boundaries, definition).snapshots()`, `work_item_row`, `work_item_order`). It states the title, the folder, the source of the state, and the error. It also names the test module and the fixture setup.
   - Criteria: each is testable by one test function. The title, folder and state rules are covered by 1 to 3. The ordering rule is covered by 4, with the three rows parametrized. The merged-then-booked behaviour is covered by 5. The no-`acceptance_stage` rule is covered by 6. The error rule has its failing side in 8. Criterion 6 covers the side where the stage is missing, and 1 covers the side where it exists.
   - Demo: both commands are runnable. Each `Expect:` line is checkable (a passed count of at least 10, and `awk` lines from the `factory-watch` section only).
   - Architecture: the change is in `application/board.py` and reuses the domain `work_item_row`, so it follows the layer rules. It adds no new helper.
   - Scope: it matches FEATURE.md decision 23 and the S0012 mention in "Out of scope". It leaves the feature rows and the event line unchanged, and changes no existing test.
3. tester: wrote one new module, `tests/application/test_board_reader_acceptance.py`, using the fixtures in `tests/conftest.py` (`walk`, `boundaries`, `human`, `clock`, `remote`). A local `opened` fixture fetches and runs `AcceptanceService(boundaries, walk.definition).open("F0002")`. No existing test module changed.

   Criterion → test:
   - criterion 1: tests/application/test_board_reader_acceptance.py::test_an_opened_acceptance_is_a_row_titled_by_its_report
   - criterion 2: tests/application/test_board_reader_acceptance.py::test_an_acceptance_row_shows_stage_pull_request_and_blocked_from_its_branch (state set with `walk.record(..., 3, [], stage="approval", blocked="question")`)
   - criterion 3: tests/application/test_board_reader_acceptance.py::test_an_acceptance_row_shows_its_claim_and_running_since (the branch's report is re-rendered with a `factory-1` claim at stage `acceptance` and pushed with `human.push_file`)
   - criterion 4: tests/application/test_board_reader_acceptance.py::test_rows_come_in_work_item_order, three rows: story-of-an-earlier-feature, stories-around-it, story-of-its-own-feature (the last uses `PROPOSED`/`PROPOSED_TEXT` from `tests/acceptance_walk.py` for `F0002-S0003`)
   - criterion 5: tests/application/test_board_reader_acceptance.py::test_a_merged_acceptance_has_its_row_until_it_is_booked_into_done
   - criterion 6: tests/application/test_board_reader_acceptance.py::test_without_an_acceptance_stage_an_acceptance_branch_adds_no_row
   - criterion 7: tests/application/test_board_reader_acceptance.py::test_run_watch_prints_the_acceptance_row_under_work_items (checks that every line after `work items` is the one expected line)
   - criterion 8: tests/application/test_board_reader_acceptance.py::test_a_report_with_a_plain_work_item_state_is_a_format_error_with_its_path
   - criteria 9 and 10: not tests (the check gate and docs).

   Red state from one `make test` run: the tests for criteria 1–5 and 7 fail on their assertions (8 cases), because `BoardReader.read` does not yet give acceptance rows. Every module imported, so nothing failed to import. The tests for criteria 6 and 8 already pass: today's code adds no acceptance row, and it already raises through `fill_board`'s snapshot reading. They guard the refused side and the error path once the rows are added. `make lint` is green. The type check was skipped, as this stage allows.

   Open: nothing.

   `make lint`: lint: green
   `make test`: FAILED tests/application/test_board_reader_acceptance.py::test_run_watch_prints_the_acceptance_row_under_work_items
