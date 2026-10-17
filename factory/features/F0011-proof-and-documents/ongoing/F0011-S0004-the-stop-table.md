---
stage: review
pr: 148
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The stop table

## Assignment (as of log entry 1)

List every stop that v1 let reach only the factory's log or the container's output (the stops of v1's limits L11, L19, L26, L30, L33, L55, L58, L64 and L65) with the destination v1.1 gives it, as data (`STOP_TABLE`), and give each row a test. A stop of the repository or the machine goes to the health status and to a time-stamped line of the factory log (when the state directory itself cannot be written, `factory-run` reports an invalid environment on standard error instead and writes no stop, F0010-S0019); a stop of one work item goes once on that work item's pull request, which the stop service opens as a draft first when there is none; one row, a backlog story whose own file names a later stage, is removed by the start rule and has no stop at all. v1.1 starts fresh (decision 008), so no stop recognizes a work item of v1's format. The producers of the machine stops are tested in their own features (F0006, F0010); this story proves each destination through the stop service, that production code names every reason, and, for the stops of a work item, the whole path from the fault through the tick and the dispatcher to the single post. A scenario that fails is a defect to fix under `src/`, never a test to bend. It covers ST3.5 and keeps kept thing 12 (loud over lucky). The operator guide's table of stops (WE6.2) is written from this table by F0011-S0005's check.

## Interface

`src/factory/domain/stop_table.py`

```python
from typing import Literal

from pydantic import BaseModel, ConfigDict

from factory.domain.stops import RepositoryStopReason

Destination = Literal["health_status", "pull_request", "none"]


class StopRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    limits: tuple[str, ...]
    destination: Destination
    reason: RepositoryStopReason | None = None
    test: str


STOP_TABLE: tuple[StopRow, ...]
```

Rules of `StopRow` (each a `ValueError` from a model validator, so a `pydantic.ValidationError` for the caller):

- `reason` is set exactly when `destination` is `"health_status"`.
- `limits` is not empty and each entry matches `^L\d+$` (the number of one of v1's limits).

The model is closed: `frozen=True` refuses the assignment of a field and `extra="forbid"` refuses an unknown key, each with a `pydantic.ValidationError`; a `destination` outside `Destination` and a `reason` outside `RepositoryStopReason` are refused with it too.

The fourteen rows, in this order. What each stop is, for the guide: a failed fetch, an expired token included; the checkout cannot be restored to the remote's state (the dirty main branch); the pipeline definition fails its validation, an agent that is not installed included; an agent file holds a key the runner does not apply; the entrypoint waits for a repository that is empty or has no pipeline definition; lint fails on the main branch; a preflight item fails; two work items have one id; the one pull request lookup fails; a recorded question for a work item without a pull request; a handler fails on the same event and state; a hand-over fails every time; a push is rejected; a backlog story names a later stage in its own file (removed).

| id | limits | destination | reason | test |
|---|---|---|---|---|
| `fetch-failed` | L26, L58 | `health_status` | `fetch_failed` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `checkout-restore-failed` | L64 | `health_status` | `checkout_restore_failed` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `pipeline-definition-invalid` | L64 | `health_status` | `pipeline_definition_invalid` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `agent-definition-invalid` | L30 | `health_status` | `agent_definition_invalid` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `repository-unavailable` | L64 | `health_status` | `repository_unavailable` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `main-branch-failing` | L65 | `health_status` | `main_branch_failing` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `preflight-failed` | L55 | `health_status` | `preflight_failed` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `duplicate` | L19 | `pull_request` | none | `test_duplicate_is_a_counted_error_reported_once_on_the_pull_request` |
| `pull-request-lookup` | L19 | `pull_request` | none | `test_failed_pull_request_lookup_is_a_counted_error_reported_once` |
| `ask-without-pull-request` | L19, L26 | `pull_request` | none | `test_ask_without_pull_request_is_reported_once_on_a_draft_pull_request_opened_first` |
| `handler-error` | L26 | `pull_request` | none | `test_handler_that_fails_every_time_is_reported_once_after_the_error_cap` |
| `hand-over-error` | L33 | `pull_request` | none | `test_hand_over_that_fails_every_time_is_reported_once_after_the_error_cap` |
| `push-rejected` | L58 | `pull_request` | none | `test_rejected_push_is_a_counted_error_reported_once` |
| `later-stage-in-backlog-file` | L11 | `none` | none | `test_story_file_naming_a_later_stage_starts_at_intake_with_no_stop` |

Scenarios of the six stops of a work item (test inputs; all use the world and the helpers of F0011-S0001, F0011-S0002 and F0011-S0003; "question run" is `completed("question", "Which format does the title take?")`; "a failing tick" is a tick in which the handler of the event raises; the manual clock is not advanced):

- `duplicate`: `start_story`, queue a question run, one tick (the first stage ends in a question, so the branch and the pull request exist); `human.push_file` a second story file with the same id and another slug under `in-progress/` of the same feature on `main`; failing ticks follow.
- `pull-request-lookup`: `start_story`, queue a question run, one tick; then `hosting.fail_next("get_pull_request", times=99)` and `hosting.fail_next("find_open_pull_request", times=99)`; failing ticks follow.
- `ask-without-pull-request`: `start_story` (the story is under `in-progress/` on `main`, the factory has not ticked); then the branch `work-item/<id>` is pushed by hand from `origin/main` with `human.push_file`, holding the story's file at its `in-progress/` path, rendered with `FrontmatterWorkItemWriter` from `initial_state("intake")` with `blocked="question"` and no `pull_request`, over the story's body with a `## Journal` section that holds one entry, of kind `question` (added with `append_entry`); no pull request exists; failing ticks follow.
- `handler-error`: `start_story`, queue a question run, one tick (the question is recorded); `hosting.fail_next("post_comment", times=3)`; the `ask` handler fails in each of the next three ticks, and the report is the fourth call of `post_comment`, which succeeds.
- `hand-over-error`: `drive_to(world, work_item, "smoke-test")`; `hosting.fail_next("set_description", times=3)`; queue `completed("approval", "Accepted.")`; one tick moves the work item to `approval`, the hand-over fails in each of the next three ticks.
- `push-rejected`: `drive_to(world, work_item, "tests")`; an executable `hooks/update` in the bare remote that exits 1 for `refs/heads/work-item/*`; queue `completed("doing", "Done.")`; the claim's push of the next stage is refused in each failing tick.

This story changes `RemoteWorkItems.read` (`src/factory/application/work_items.py`, F0006): a story file in `in-progress/` whose id an earlier file of the list already has is read from `origin/main` as a started story (as `_started_document` reads it), never from the work item's branch, which holds only the first file. Today `_branch_document` raises `WorkItemFormatError` (`missing on branch`) for it, the tick raises before the dispatcher, and the duplicate reaches only the factory log.

Tests: `tests/domain/test_stop_table.py` (criteria 1 to 5); `tests/test_stop_table.py` (criteria 6 to 15), using the helpers of `tests/proof_support.py`; `tests/application/test_work_items_duplicate.py` (criterion 16).

## Acceptance criteria

1. `STOP_TABLE` holds exactly the fourteen rows of the table above, in that order, with those ids, limits, destinations, reasons and tests.
2. Every value of `RepositoryStopReason` is the `reason` of exactly one row of `STOP_TABLE`, and no row has a reason outside it.
3. Across `STOP_TABLE` the limits include each of `L11`, `L19`, `L26`, `L30`, `L33`, `L55`, `L58`, `L64` and `L65`.
4. A `StopRow` is rejected with `pydantic.ValidationError` when it has `destination="health_status"` and no reason, when it has a reason and `destination="pull_request"`, when it has a reason and `destination="none"`, when `limits` is empty, and when a limit is `"X7"`; the first row of the table is accepted.
5. A `StopRow` is a closed model: assigning a field of a built one (`setattr` with the field name in a variable), an unknown key, `destination="log"` and `reason="v1_work_item_found"` are each rejected with `pydantic.ValidationError`, the last three constructed through a variable typed `type[BaseModel]`.
6. Every `test` of `STOP_TABLE` is the name of a function in `tests/test_stop_table.py`.
7. For each row with `destination="health_status"`: `StopService.raise_stop` with a `RepositoryStop` of that reason (scope `machine` for `preflight_failed`, `repository` otherwise, detail `the fault`) leaves `JsonHealthStatusFile.read()` holding exactly that stop with `healthy` false, writes exactly one line to the factory log file that starts with the manual clock's reading as `TimestampedFactoryLog` writes it and contains the reason and `the fault`, and leaves no pull request in `hosting.pull_requests()` (so there is nothing to post on).
8. For each reason of `RepositoryStopReason`, the quoted reason string occurs as a string constant in some module under `src/factory/application` or `src/factory/entry` (read with `modules()` and `string_literals()` of `tests/source_search.py`): production code can raise every stop of the table.
9. `duplicate`: after the second failing tick no post of kind `error` exists; after the third exactly one exists, on the first work item's pull request, with the key `PostKey(work_item=<the work item>, kind="error", n=<the first 12 characters of the commit origin/<branch> points at>)`; three more ticks add no post.
10. `pull-request-lookup`: after the second failing tick no post of kind `error` exists; after the third exactly one exists on the work item's pull request, with that key; three more ticks add no post.
11. `ask-without-pull-request`: after the second failing tick no post and no pull request exist; after the third exactly one pull request exists, a draft for the branch (opened first), and exactly one post of kind `error` is on it; three more ticks add no post and no second pull request.
12. `handler-error`: after the second failing tick no post of kind `error` exists; after the third exactly one exists on the work item's pull request, and no post of kind `question` exists (the stop does not carry the question past the fault); three more ticks add no post.
13. `hand-over-error`: after the second failing tick no post of kind `error` exists; after the third exactly one exists on the work item's pull request; three more ticks add no post.
14. `push-rejected`: no failing tick sends the fake agent runtime a request (no claim, no agent run); after the second failing tick no post of kind `error` exists; after the third exactly one exists on the work item's pull request; three more ticks add no post.
15. `later-stage-in-backlog-file`: a backlog story whose own file carries `stage: doing`, `round: 2` and `attempts: 1` in front matter is started and ticked once with a question run queued; its branch exists with `stage == "intake"`, `round == 0`, `attempts == 0` and `crashes == 0`, `JsonHealthStatusFile.read().healthy` is true and no post of kind `error` exists.
16. `RemoteWorkItems.read` on a remote whose `main` holds two in-progress files of one id and whose branch of that id holds only the first returns two snapshots, the second with the state `initial_state(<the first stage>)` and its body from `origin/main`; when the only in-progress file of an id is missing on that id's branch, it still raises `WorkItemFormatError`.
17. make check stays green.
18. docs: `docs/operator-guide.md` gets the section *The stops*, which takes the content of the two existing stop sections (*Stops of the repository or the machine* and *Stops of one work item*, which are removed; the other sections about one stop link to the table instead of repeating its destination) into one table with one row per row of `STOP_TABLE` (the id as `` `fetch-failed` ``-style text, the destination in words: `health status and factory log`, `pull request` or `no stop`, and what the operator does), and states that every line about a stop in the factory log is time-stamped, and, in the row of `preflight-failed`, that when the state directory cannot be written `factory-run` still ends with status 2 but writes no stop: the settings fault reaches standard error as two lines without a stamp (F0010-S0019); `docs/decisions.md` records that the producers of the machine stops are proved by their own features and that a story file naming a later stage is removed by the start rule, not stopped. README and project guide are untouched.

## Demo

```bash
uv run python -c "
from factory.domain.stop_table import STOP_TABLE
for r in STOP_TABLE:
    print(r.id, r.destination, ','.join(r.limits), r.reason or '-')
"
```
Expect: fourteen lines, the first `fetch-failed health_status L26,L58 fetch_failed`, the seventh `preflight-failed health_status L55 preflight_failed`, the eighth `duplicate pull_request L19 -`, the last `later-stage-in-backlog-file none L11 -`.

```bash
uv run python -c "
from typing import get_args
from factory.domain.stop_table import STOP_TABLE
from factory.domain.stops import RepositoryStopReason
print(sorted(r.reason for r in STOP_TABLE if r.reason) == sorted(get_args(RepositoryStopReason)))
"
```
Expect: `True`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_stop_table.py tests/domain/test_stop_table.py
```
Expect: the last line reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `src/factory/domain/stop_table.py` names `StopRow`, `Destination`, `STOP_TABLE` with concrete fields and validator rules; the fourteen rows are spelled out, and the 7 reason values match `RepositoryStopReason` in `domain/stops.py`. The one code change (`RemoteWorkItems.read`) names its module and the behaviour.
   - Criteria: 1 to 18 are each testable by one function. Every Interface rule has both sides: reason set exactly when `health_status` (criterion 4 covers missing and surplus reasons), non-empty limits and `^L\d+$` (empty and `"X7"` rejected, first row accepted), closed model (criterion 5). The read change has both sides in criterion 16 (duplicate read from main; missing file still raises). Error caps are checked at the second and third ticks, plus three more ticks with no repeat.
   - Demo: the three commands are runnable. Each `Expect:` line is checkable (fourteen lines with named first, seventh, eighth and last; `True`; the `passed` line).
   - Architecture: the table is data in `factory.domain`, with no I/O. It imports only `factory.domain.stops`. The tests use the existing helpers (`tests/proof_support.py`, `tests/source_search.py`, `FakeHosting.fail_next` and `pull_requests`).
   - Scope: stays within F0011's stop-table scope (L11, L19, L26, L30, L33, L55, L58, L64, L65). The producers of the machine stops stay out of scope. The F0006 code change is recorded as decision 19 in `FEATURE.md`.
3. tester: Wrote red tests for criteria 1 to 16, using the Interface and the scenario list as written.

   Criterion → test:
   - criterion 1: tests/domain/test_stop_table.py::test_the_table_holds_the_fourteen_stops_in_order
   - criterion 2: tests/domain/test_stop_table.py::test_every_repository_stop_reason_is_the_reason_of_exactly_one_row
   - criterion 3: tests/domain/test_stop_table.py::test_the_table_covers_every_limit_of_v1_whose_stop_reached_only_a_log
   - criterion 4: tests/domain/test_stop_table.py::test_a_row_breaking_a_rule_of_the_table_is_rejected (parametrized: health without reason, reason with pull_request, reason with none, empty limits, "X7") and ::test_the_first_row_of_the_table_is_accepted
   - criterion 5: tests/domain/test_stop_table.py::test_a_built_row_refuses_the_assignment_of_a_field and ::test_a_row_with_an_unknown_key_or_value_is_rejected (parametrized: unknown key, destination "log", reason "v1_work_item_found", all built through `type[BaseModel]`)
   - criterion 6: tests/test_stop_table.py::test_every_test_of_the_table_is_a_function_of_this_module (reads the module's top-level functions with `ast`)
   - criterion 7: tests/test_stop_table.py::test_repository_stop_reaches_the_health_status_and_the_factory_log (parametrized over the seven health_status rows; uses the conftest `boundaries`, `clock` and `hosting` fixtures, and the log at tmp_path/state/factory.log)
   - criterion 8: tests/test_stop_table.py::test_production_code_names_every_reason_of_a_repository_stop (parametrized over `RepositoryStopReason`)
   - criterion 9: tests/test_stop_table.py::test_duplicate_is_a_counted_error_reported_once_on_the_pull_request
   - criterion 10: tests/test_stop_table.py::test_failed_pull_request_lookup_is_a_counted_error_reported_once
   - criterion 11: tests/test_stop_table.py::test_ask_without_pull_request_is_reported_once_on_a_draft_pull_request_opened_first
   - criterion 12: tests/test_stop_table.py::test_handler_that_fails_every_time_is_reported_once_after_the_error_cap
   - criterion 13: tests/test_stop_table.py::test_hand_over_that_fails_every_time_is_reported_once_after_the_error_cap
   - criterion 14: tests/test_stop_table.py::test_rejected_push_is_a_counted_error_reported_once (installs an executable `hooks/update` in the bare remote that exits 1 for refs/heads/work-item/*)
   - criterion 15: tests/test_stop_table.py::test_story_file_naming_a_later_stage_starts_at_intake_with_no_stop
   - criterion 16: tests/application/test_work_items_duplicate.py::test_a_second_file_of_one_id_is_read_from_main_as_a_started_story and ::test_the_only_file_of_an_id_missing_on_its_branch_is_still_a_format_error

   How the scenario tests are written:
   - Error posts are counted over every pull request with a local helper `_error_posts`.
   - For "three more ticks add no post", the test compares every factory post before and after those ticks.
   - Duplicate and pull-request-lookup also compare the post's key with `PostKey(work_item, "error", n=<first 12 characters of origin/<branch>>)`, read after the third failing tick.
   - The duplicate's second file is `<id>-other.md`, so its path sorts after `F0001-S0001-first.md`.
   - Ask-without-pull-request builds the branch file from `initial_state("intake")` with `blocked="question"`, over `STORY` (which already has `## Journal`), with one `question` entry from speaker `intake` added by `append_entry`. It renders the file with the world's `FrontmatterWorkItemWriter` and pushes it with `human.push_file` to the story's in-progress path.

   Files created: tests/domain/test_stop_table.py, tests/test_stop_table.py, tests/application/test_work_items_duplicate.py.

   One `make test` run: collection stopped with 2 errors, in tests/domain/test_stop_table.py and tests/test_stop_table.py. Both import `factory.domain.stop_table`, which does not exist yet. Because collection was interrupted, tests/application/test_work_items_duplicate.py did not run. Its first test should fail against the current `_branch_document`, which raises "missing on branch". Its second test pins behaviour that already exists.

   `make lint` is green after `ruff format`. I skipped the type check, as the stage says to.

   Nothing is open: no criterion needed interpreting beyond what the scenario list states.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built the stop table and the duplicate read; `make check` green (coverage 99.55 %). Commit 49a4329.

   - `src/factory/domain/stop_table.py`: `Destination`, `StopRow` (frozen, extra="forbid") and `STOP_TABLE`, the fourteen rows in the Interface's order. There are two model validators, each raising a `ValueError`: the reason is set exactly when the destination is `health_status`, and the limits are non-empty and each matches `^L\d+$`. Two private builders (`_health`, `_pull_request`) keep the rows short: every health_status row shares the one repository test name, and every pull_request row has no reason.
   - `src/factory/application/work_items.py`: `read` tracks the ids it has already seen. `_snapshot` takes `duplicate=` and reads a later in-progress file of a seen id from origin/main through `_started_document`, as for a story without a branch. Before this, `_branch_document` raised `missing on branch`. `branch_commit` stays the resolved branch tip, so the dispatcher's error key (`n` = first 12 characters of origin/<branch>) and the duplicate post land on the first work item's pull request. The only file of an id that is missing on its branch still raises `WorkItemFormatError`.
   - Rejected: dropping the duplicate's `branch_commit` (setting it to None). That would make the second snapshot look like a story that was never started, and the scenario's key and pull request depend on the branch tip.
   - Every scenario in tests/test_stop_table.py (criteria 6 to 15) passed with no change under `src/` beyond the read change, so the other stops already reach their destinations.
   - Refactor: I read the diff back and found nothing to rename, simplify or remove, so there is no refactor commit.
   - Not touched: the docs criterion (18) belongs to the documenter.

   `make check`: check: green
