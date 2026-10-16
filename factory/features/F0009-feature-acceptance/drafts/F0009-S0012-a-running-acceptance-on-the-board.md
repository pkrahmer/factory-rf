# A running acceptance on the board

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

`factory-watch` prints a work item row for every story in `in-progress/`, with its stage, what it waits for, its claim and its pull request. A running acceptance gets no row. While `F0002-A0001` runs, waits with a question or waits at its approval for the human, the board shows only `acceptance=in_flight` in the feature's row, and its `work items` list can be empty. The feature acceptance's demo showed this: with `F0003-A0002` opened and the next event `run:F0003-A0002`, the board listed no work item. The operator cannot see on the board that an acceptance waits for them, or which pull request to open. This story gives every acceptance that `AcceptanceReader.snapshots()` returns a work item row of its own, built the same way as a story's row and placed by `work_item_order`, so an acceptance comes after its feature's stories. The feature rows and the event line stay as they are.

## Interface

`src/factory/application/board.py`: `BoardReader.read(definition)` keeps its signature. Its `rows` are `work_item_row(snapshot)` for every snapshot of `RemoteWorkItems.read(definition)` and of `AcceptanceReader(boundaries, definition).snapshots()`, joined and sorted by `work_item_order(snapshot.id)`. A definition without an `acceptance_stage` gives no acceptance rows, because `snapshots()` returns `[]` for it. `work_item_row` (`src/factory/domain/board.py`) is unchanged. An acceptance's row is titled by its report's first `# ` title (`Acceptance of <feature title>`). Its folder is `in-progress`, and its stage, `blocked`, claim, `running_since` and pull request come from the report's state as the snapshot holds it (the branch's document while the branch holds the report).

Errors: a report that `snapshots()` cannot read raises `WorkItemFormatError` from `read`, as `snapshots()` already does for the watcher's evaluation.

Tests: one new module, `tests/application/test_board_reader_acceptance.py`, with the fixtures of `tests/conftest.py`. It opens an acceptance as `tests/application/test_stage_run_acceptance.py` does (`AcceptanceService(boundaries, definition).open("F0002")` after pushing `F0002-todo` with archived stories). No existing test module changes.

## Acceptance criteria

1. With the acceptance `F0002-A0001` opened on its branch and no story in progress, `BoardReader(boundaries).read(definition).rows` is one row: `work_item == "F0002-A0001"`, `title == "Acceptance of Todo service"`, `folder == "in-progress"`, `stage == "acceptance"`, `blocked is None`, `claim is None`, `pull_request is None`.
2. After the report's state on its branch is set to stage `approval`, `pull_request` 3 and `blocked` `question`, the acceptance's row shows `stage == "approval"`, `pull_request == 3` and `blocked == "question"`.
3. With the story `F0001-S0001` in `in-progress/` and the acceptance `F0002-A0001` opened, the rows are in the order `F0001-S0001`, `F0002-A0001`. With a story of `F0003` also in `in-progress/`, the acceptance's row comes before the `F0003` story's row.
4. A merged acceptance not yet recorded (its report in `in-progress/` on `origin/main`, the branch deleted) still has its row. Once it is booked into `done/`, it has none.
5. With a pipeline definition without an `acceptance_stage`, an acceptance branch on the remote adds no row, and the story rows are still there.
6. `run_watch` prints the acceptance's row under `work items` in the same column format as a story's row: `F0002-A0001  Acceptance of Todo service  in-progress  stage=acceptance  blocked=-  claim=-  running_since=-  pull_request=-`.
7. `make check` stays green.
8. docs: the operator guide's `factory-watch` section says that a work item row exists for each story in `in-progress/` and for each running acceptance, and that an acceptance's row comes after its feature's stories.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_board_reader_acceptance.py
```
Expect: the last line is `<n> passed in <time>`, with n at least 6.

```bash
grep -n "running acceptance" docs/operator-guide.md
```
Expect: at least one line in the `factory-watch` section.

## Log (append only)

1. 2026-10-16 human: created.
