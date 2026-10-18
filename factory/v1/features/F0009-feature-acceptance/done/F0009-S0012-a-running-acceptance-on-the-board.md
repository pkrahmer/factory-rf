---
stage: done
pr: 115
blocked: null
comments_seen: 0
round: 1
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
4. coder: `BoardReader.read` in `src/factory/application/board.py` now builds its rows from `RemoteWorkItems.read(definition)` plus `AcceptanceReader(boundaries, definition).snapshots()`. It joins the two lists, sorts them by `work_item_order(snapshot.id)` and maps each snapshot through the unchanged `work_item_row`. Commit 6b578dd.

      - Design: the method builds one `AcceptanceReader` and uses it for both the feature column (`fill_board`) and the new rows. A definition without an acceptance stage gets no acceptance rows, because `snapshots()` already returns `[]` for it. A report that cannot be read raises `WorkItemFormatError` from `snapshots()`, which `read` passes on.
      - Rejected: merging the two already-sorted lists by hand. Both lists are small, and a single `sorted` with the shared key reads more clearly.
      - Refactor: I read my diff and found nothing to change (8 lines added, 6 removed, one file).
      - Noticed, not touched: the watch output still lists the feature rows before the work item rows, as the ticket asks.
      - `make check`: green (coverage 99.53 %).
      - Open: the docs criterion (10) is for the documenter.

   `make check`: check: green
5. reviewer: one finding (quality).

   Groups 1 to 3 pass. Each of criteria 1 to 8 has a test in `tests/application/test_board_reader_acceptance.py`, and each test checks what its criterion says. Criterion 4 is one parametrized test with three rows. The refused sides of the Interface are covered: no `acceptance_stage` (criterion 6) and the `WorkItemFormatError` with the report's path (criterion 8). The coder's `make check` was green. The layers are respected, since `application/board.py` imports only application and domain, and I found no security concern. The diff also lists `planning/` and `docs/runs/` changes, but they come from the human's commit ded79b2, which I did not review.

   1. `src/factory/application/board.py:43-47` copies the join-and-sort that `Watcher.evaluate` already does at `src/factory/application/watcher.py:36-40`. Both take `RemoteWorkItems.read(definition)` plus `AcceptanceReader(...).snapshots()` and sort them by `work_item_order`, but the copies have already drifted: the watcher also breaks ties by `snapshot.path` and the board does not. Fix: move the join into one application function that returns the ordered snapshots of every running work item (stories and acceptances), for example next to `AcceptanceReader` or in `work_items.py`. Have both `Watcher.evaluate` and `BoardReader.read` call it, so the board and the watcher cannot order rows differently. Changing `watcher.py` this way changes no behaviour.

   Rejected as a finding: calling `AcceptanceReader` twice in `read` (once in `fill_board`, once in `snapshots()`). They do different reads, and the Interface asks for this.
6. coder: coder (round 1): fixed the reviewer's one finding, the duplicated join-and-sort. Commit 1665867.
      - Built: `running_work_items(work_items, acceptances, definition)` in `src/factory/application/acceptance_reading.py`. It returns `RemoteWorkItems.read(definition)` plus `AcceptanceReader.snapshots()`, sorted by `(work_item_order(snapshot.id), snapshot.path)`. `Watcher.evaluate` (`src/factory/application/watcher.py`) and `BoardReader.read` (`src/factory/application/board.py`) now both call it, so the board and the watcher can no longer order rows differently. The board now also uses the watcher's path tie-break. Neither caller uses `work_item_order` directly any more, so I removed that import from both.
      - Design: the function takes the caller's `RemoteWorkItems` and `AcceptanceReader` instances rather than building its own. The watcher still needs its `work_items` for `_illegal_changes`, and the board still needs its reader for `fill_board`, so passing them in avoids a second set of objects. I put it in `acceptance_reading.py` because that module already imports `work_items.py`. Putting it in `work_items.py` would have made an import cycle.
      - Rejected: a method on `AcceptanceReader`. The function joins two readers, so it does not belong on either one.
      - Refactor: this round's change is itself the refactor. Reading the diff again, I found nothing more to change.
      - No tests changed. `make check`: green (coverage 99.53 %).
      - Open: criterion 10 (docs) is for the documenter.

   `make check`: check: green
7. reviewer: reviewer (round 1): no findings.

   - Last round's finding is fixed. `running_work_items(work_items, acceptances, definition)` at `src/factory/application/acceptance_reading.py:249` is now the only place that joins `RemoteWorkItems.read` with `AcceptanceReader.snapshots()` and sorts them by `(work_item_order(id), path)`. `Watcher.evaluate` (`src/factory/application/watcher.py:38`) and `BoardReader.read` (`src/factory/application/board.py:44`) both call it. The watcher's behaviour is unchanged, since it uses the same key it used before. The board gains the path tie-break. The unused `work_item_order` import is gone from `watcher.py`.
   - Criteria 1 to 8 each have a test in `tests/application/test_board_reader_acceptance.py`, and I read each test against its criterion:
     - Criterion 4 is one parametrized test with three rows, and the third pushes and starts `F0002-S0003` after the opening.
     - Criterion 5 asserts both the merged row and that no row remains once the item is booked into `done/`.
     - Criterion 6 covers the refused side, a definition without `acceptance_stage`.
     - Criterion 8 covers the error side: `WorkItemFormatError` with `path == REPORT`.
     - Criterion 7 pins the exact output line.
     - The coder's `make check` was green, with coverage at 99.53 %.
   - Architecture: the change touches only `factory.application`, which imports application and domain modules. Putting the function in `acceptance_reading.py` avoids an import cycle with `work_items.py`. No interface or DTO changed.
   - Security: no subprocess, no strings built into commands, and no suppression markers.
   - Quality: the names say what things are, the new public function has a docstring that names the error it raises, and there is no dead or duplicated code.
   - Ticket hygiene: the Assignment matches what was built, the log records the design and what was rejected, and criterion 10 still describes what the documenter has to write.
   - Not reviewed: the `planning/` and `docs/runs/` changes in the diff come from the human's commit ded79b2.
8. documenter: docs (round 1): documented the acceptance rows on the board; no findings.

   Changed:
   - `docs/operator-guide.md`, `factory-watch` section: a work item row exists for each story in `in-progress/` and for each running acceptance (opened, waiting with a question or at its approval, or merged and not yet booked). Rows are in id order, so an acceptance comes after its feature's stories and before a later feature's stories. It also gives the acceptance's title (`Acceptance of <feature title>`), its folder, and that its state is the one on its branch.
   - `docs/project-guide.md`, "The watcher's command line": the board's rows come from `running_work_items(...)` in `factory.application.acceptance_reading`. That is `RemoteWorkItems.read` plus `AcceptanceReader.snapshots()`, sorted by `(work_item_order(id), path)`. `Watcher.evaluate` calls the same function. A report that cannot be read raises `WorkItemFormatError` from `read`.

   Checks run:
   - The demo's `awk` command prints the new line from the `factory-watch` section.
   - `make check` is green.

   Cross-read and found current: the board paragraph of the project guide (apart from the sentence changed) and the watcher event text in the operator guide, against the diff in `board.py`, `watcher.py` and `acceptance_reading.py`.

   Stale but untouched: nothing seen. The diff also lists `planning/` and `docs/runs/` changes from the human's commit; they are not mine.

   `make check`: check: green
9. demo: demo (round 1): ran both demo commands from the repository root. Both met their `Expect:` lines, and I found no findings.

   1. `uv run pytest --no-header -p no:cacheprovider tests/application/test_board_reader_acceptance.py`
   ```
   ..........                                                               [100%]
   10 passed in 7.86s
   ```
   Met. The last line is `10 passed in <time>`, and the Expect asks for at least 10: criteria 1–8, with criterion 4 as three rows.

   2. `awk '/^## /{s=($0=="## Looking at the remote: `factory-watch`")} s && /running acceptance/' docs/operator-guide.md`
   ```
   - A work item row exists for each story in `in-progress/` and for each running acceptance (one that is opened, waiting with a question or at its approval, or merged and not yet booked), with its title (the first `# ` title of the body, else the id), its stage, what it waits for (`blocked`), the instance holding its claim, since when (`running_since`, the claim's start in UTC) and its pull request. An absent value is `-`. The rows are in id order, so an acceptance's row comes after its feature's stories and before the stories of a later feature. An acceptance's title is `Acceptance of <feature title>`, its folder `in-progress`, and its state is the one on its branch.
   ```
   Met. It printed one line, and the awk filter only prints from the `factory-watch` section.

   I then read the acceptance criteria again against these results. Nothing contradicts any of them:
   - Criteria 1–8 are covered by the passing module.
   - Criterion 10 is met in both guides. The operator guide line above says what it requires. `docs/project-guide.md:558` says that the board's rows are those of `RemoteWorkItems.read` and `AcceptanceReader.snapshots()`, sorted by `work_item_order` (through `running_work_items`).
   - Criterion 9 (`make check`) is the factory's gate, and I did not run it in this stage.

   Open: nothing.
10. done (pull request merged); cost: 8 runs, 24.5 min, 59 turns, 216k tokens in (966k more from cache), 21k out, $2.11
