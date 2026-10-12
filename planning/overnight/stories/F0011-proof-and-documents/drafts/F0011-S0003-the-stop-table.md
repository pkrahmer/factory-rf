# The stop table

## Assignment (as of log entry 1)

List every stop that v1 let reach only the factory's log or the container's output (the stops of v1's limits L11, L19, L26, L33, L55, L58, L64 and L65) with the destination v1.1 gives it, as data (`STOP_TABLE`), and give each row a test. A stop of the repository or the machine goes to the health status and to a time-stamped line of the factory log; a stop of one work item goes once on that work item's pull request, which the stop service opens as a draft first when there is none; one row, a backlog story whose own file names a later stage, is removed by the start rule and has no stop at all. The producers of the machine stops are tested in their own features (F0006, F0010); this story proves each destination through the stop service, that production code names every reason, and, for the stops of a work item, the whole path from the fault through the tick and the dispatcher to the single post. It covers ST3.5 and keeps kept thing 12 (loud over lucky). The operator guide's table of stops (WE6.2) is written from this table by F0011-S0004's check.

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
- `limits` is not empty and each entry matches `^[LR]\d+$` (the number of one of v1's limits or of a rule of the handover).

The fifteen rows, in this order. What each stop is, for the guide: a failed fetch, an expired token included; the checkout cannot be restored to the remote's state (the dirty main branch); the pipeline definition fails its validation, an agent that is not installed included; an agent file holds a key the runner does not apply; a work item of v1's format is found; the entrypoint waits for a repository that is empty or has no pipeline definition; lint fails on the main branch; a preflight item fails; two work items have one id; the one pull request lookup fails; a recorded question for a work item without a pull request; a handler fails on the same event and state; a hand-over fails every time; a push is rejected; a backlog story names a later stage in its own file (removed).

| id | limits | destination | reason | test |
|---|---|---|---|---|
| `fetch-failed` | L26, L58 | `health_status` | `fetch_failed` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `checkout-restore-failed` | L64 | `health_status` | `checkout_restore_failed` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `pipeline-definition-invalid` | L64 | `health_status` | `pipeline_definition_invalid` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `agent-definition-invalid` | L30 | `health_status` | `agent_definition_invalid` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
| `v1-work-item-found` | R26 | `health_status` | `v1_work_item_found` | `test_repository_stop_reaches_the_health_status_and_the_factory_log` |
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

Scenarios of the six stops of a work item (test inputs; all use the world and the helpers of F0011-S0001 and F0011-S0002; "a failing tick" is a tick in which the handler of the event raises; the manual clock is not advanced):

- `duplicate`: `start_story`, one tick (the first stage ends in a question, so the branch and the pull request exist); `human.push_file` a second story file with the same id and another slug under `in-progress/` of the same feature on `main`; failing ticks follow.
- `pull-request-lookup`: `start_story`, one tick; then `hosting.fail_next("get_pull_request", times=99)` and `hosting.fail_next("find_open_pull_request", times=99)`; failing ticks follow.
- `ask-without-pull-request`: a work item branch `work-item/<id>` pushed by hand from `origin/main`, its file rendered with `FrontmatterWorkItemWriter` from `initial_state("intake")` with `blocked="question"`, no `pull_request` and one journal entry of kind `question`; no pull request exists; failing ticks follow.
- `handler-error`: `start_story`, one tick (the question is recorded); `hosting.fail_next("post_comment", times=3)`; the `ask` handler fails in each of the next three ticks, and the report is the fourth call of `post_comment`, which succeeds.
- `hand-over-error`: `drive_to(world, work_item, "smoke-test")`; `hosting.fail_next("set_description", times=3)`; queue `completed("approval", "Accepted.")`; one tick moves the work item to `approval`, the hand-over fails in each of the next three ticks.
- `push-rejected`: `drive_to(world, work_item, "tests")`; an executable `hooks/update` in the bare remote that exits 1 for `refs/heads/work-item/*`; queue `completed("doing", "Done.")`; the claim's push of the next stage is refused in each failing tick.

Tests: `tests/domain/test_stop_table.py` (criteria 1 to 4); `tests/test_stop_table.py` (criteria 5 to 14), using the helpers of `tests/proof_support.py`.

## Acceptance criteria

1. `STOP_TABLE` holds exactly the fifteen rows of the table above, in that order, with those ids, limits, destinations, reasons and tests.
2. Every value of `RepositoryStopReason` is the `reason` of exactly one row of `STOP_TABLE`, and no row has a reason outside it.
3. Across `STOP_TABLE` the limits include each of `L11`, `L19`, `L26`, `L33`, `L55`, `L58`, `L64` and `L65`.
4. A `StopRow` is rejected with `pydantic.ValidationError` when it has `destination="health_status"` and no reason, when it has a reason and `destination="pull_request"`, when `limits` is empty, and when a limit is `"X7"`; the first row of the table is accepted.
5. Every `test` of `STOP_TABLE` is the name of a function in `tests/test_stop_table.py`.
6. For each row with `destination="health_status"`: `StopService.raise_stop` with a `RepositoryStop` of that reason (scope `machine` for `preflight_failed`, `repository` otherwise, detail `the fault`) leaves `JsonHealthStatusFile.read()` holding exactly that stop with `healthy` false, writes exactly one line to the factory log file that starts with the manual clock's reading as `TimestampedFactoryLog` writes it and contains the reason and `the fault`, and leaves `hosting.pull_requests()` empty and `hosting.factory_posts` empty.
7. For each reason of `RepositoryStopReason`, the quoted reason string occurs as a string constant in some module under `src/factory/application` or `src/factory/entry`: production code can raise every stop of the table.
8. `duplicate`: after the second failing tick no post of kind `error` exists; after the third exactly one exists, on the first work item's pull request, with the key `PostKey(work_item, "error", n)` where `n` is the first 12 characters of the commit `origin/<branch>` points at; three more ticks add no post.
9. `pull-request-lookup`: after the second failing tick no post of kind `error` exists; after the third exactly one exists on the work item's pull request, with that key; three more ticks add no post.
10. `ask-without-pull-request`: after the second failing tick no post and no pull request exist; after the third exactly one pull request exists, a draft for the branch (opened first), and exactly one post of kind `error` is on it; three more ticks add no post and no second pull request.
11. `handler-error`: after the second failing tick no post of kind `error` exists; after the third exactly one exists on the work item's pull request, and no post of kind `question` exists (the stop does not carry the question past the fault); three more ticks add no post.
12. `hand-over-error`: after the second failing tick no post of kind `error` exists; after the third exactly one exists on the work item's pull request; three more ticks add no post.
13. `push-rejected`: no failing tick sends the fake agent runtime a request (no claim, no agent run); after the second failing tick no post of kind `error` exists; after the third exactly one exists on the work item's pull request; three more ticks add no post.
14. `later-stage-in-backlog-file`: a backlog story whose own file carries `stage: doing`, `round: 2` and `attempts: 1` in front matter is started and ticked once; its branch exists with `stage == "intake"`, `round == 0`, `attempts == 0` and `crashes == 0`, `JsonHealthStatusFile.read().healthy` is true and no post of kind `error` exists.
15. make check stays green.
16. docs: `docs/operator-guide.md` gets the section *The stops*, a table with one row per row of `STOP_TABLE` (the id as `` `fetch-failed` ``-style text, the destination in words: `health status and factory log`, `pull request` or `no stop`, and what the operator does), and states that every line about a stop is time-stamped; `docs/decisions.md` records that the producers of the machine stops are proved by their own features and that a story file naming a later stage is removed by the start rule, not stopped. README and project guide are untouched.

## Demo

```bash
uv run python -c "
from factory.domain.stop_table import STOP_TABLE
for r in STOP_TABLE:
    print(r.id, r.destination, ','.join(r.limits), r.reason or '-')
"
```
Expect: fifteen lines, the first `fetch-failed health_status L26,L58 fetch_failed`, the eighth `preflight-failed health_status L55 preflight_failed`, the ninth `duplicate pull_request L19 -`, the last `later-stage-in-backlog-file none L11 -`.

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
uv run pytest tests/test_stop_table.py tests/domain/test_stop_table.py -q -p no:cacheprovider
```
Expect: the last line reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
