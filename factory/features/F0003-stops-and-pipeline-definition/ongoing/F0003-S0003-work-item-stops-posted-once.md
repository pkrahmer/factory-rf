---
stage: demo
pr: 42
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
# Work item stops on the pull request, posted once

## Assignment (as of log entry 1)

Build the destination of every stop of one work item (R27): a comment on that work item's pull request, with the draft pull request opened first when the work item has none (ST3.2), and posted once however often the stop is attempted (GH3.4). `StopService.post` takes a `WorkItemStop` whose `key` is the `PostKey` derived from state on the remote; the hosting service's keyed `post_comment` turns a repeat into a no-op, so a kill between the post and the write of its state, or a failing post after the pull request was opened, leaves exactly one pull request and one post after the restart. The service writes no state itself: the caller records the pull request's number in the work item when `opened` is true (R22). Before it opens a pull request it checks that the stop's branch is on the remote with a commit beyond `main`, because the hosting service refuses a pull request without one, and the fake must not be kinder than production. Covers ST3.2 and GH3.4; keeps kept thing 11 (every stop is one post on the pull request, saying what each possible answer will do) and, with S0002, R27. The texts of the individual stops (questions, caps, notes) and the handlers that call this service are F0005 to F0009.

## Interface

`src/factory/domain/stops.py` (adds to S0001's module)

```python
class WorkItemStop(BaseModel):                # goes on the work item's pull request, once
    model_config = ConfigDict(frozen=True, extra="forbid")
    key: PostKey                              # key.work_item is the stop's work item
    branch: str                               # where a draft pull request is opened if there is none
    title: str                                # that pull request's title
    pull_request: PositiveInt | None          # from the work item's state
    text: str                                 # what each possible answer will do (kept 11)

class StopPosted(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    pull_request: PositiveInt                 # the caller records it in the state when opened is True
    opened: bool
    outcome: PostOutcome                      # "posted" or "already_posted"
```

`src/factory/domain/post_texts.py`

```python
def opened_for_stop_description(work_item: WorkItemId) -> str: ...
    # "The factory opened this draft pull request to report a stop on <work item>. The stop is the comment below."
```

`src/factory/application/stops.py` (adds to S0002's `StopService`)

```python
class StopService:
    def post(self, stop: WorkItemStop) -> StopPosted: ...    # HostingServiceError; GitError
```

Rules:

- `WorkItemStop.branch`, `title` and `text` must not be blank (empty or whitespace only), else `ValidationError`. A blank `text` would break kept thing 11. `branch` must equal `branch_name(stop.key.work_item)` (`factory.domain.identifiers`), else `ValidationError`: a stop belongs to the one branch of its work item. Both models are frozen and refuse unknown fields; `pull_request` is a positive integer or `None`.
- `post` finds the pull request number: `stop.pull_request` when it is set, and then it looks nothing up and creates nothing, whatever the state of that pull request (a number that the human has since closed or merged is still posted on). When it is `None`, it takes the open pull request of `stop.branch` (`hosting.find_open_pull_request`); when there is none, it first checks the remote branch and then creates a draft pull request with `hosting.create_pull_request(stop.branch, stop.title, opened_for_stop_description(stop.key.work_item), draft=True)`. Only an open pull request is reused; a closed or merged one on the branch is not.
- The check before a pull request is created uses the remote-tracking refs that the last fetch left in the checkout: `boundaries.git.resolve("origin/" + stop.branch)` must give a commit, and that commit must not be an ancestor of `origin/main` (`boundaries.git.is_ancestor`), else `post` raises `HostingServiceError("create_pull_request", "branch <branch> is not on the remote with a commit beyond main")` and creates and posts nothing. The factory's opening pushes the branch before any stop of that work item can be posted; this check makes the fake and the production service refuse the same case.
- `post` then calls `hosting.post_comment(number, stop.text, stop.key)` and returns `StopPosted(pull_request=number, opened=<see below>, outcome=<the call's outcome>)`. `opened` is true exactly when `stop.pull_request` was `None`: the number is then new to the state, whether this call created the pull request or found it open, and the caller records it.
- What makes a repeat a no-op is the key alone (the hosting service's keyed post): the same key posts nothing a second time whatever the text, and a different key (another kind, or another `n`) posts again.
- `post` writes no file and makes no git write; its only git calls are the two reads above. A `HostingServiceError` and a `GitError` are not caught, and neither is `InjectedKill`.

Tests: `tests/domain/test_work_item_stop.py`, `tests/domain/test_post_texts.py`, `tests/application/test_stop_posting.py`. They use the fixtures `hosting` (the fake, with `kill_points`), `kill_points`, `checkout`, `human` and `boundaries` that earlier stories put in `tests/conftest.py`, and the fake's `fail_next`, `pull_requests`, `factory_posts` and `close_by_human`. A test that opens a pull request first pushes the stop's branch with `human.push_file(branch, "note.txt", "x")` and then calls `checkout.fetch()`. The refusal of an unknown field is tested through a variable typed `type[BaseModel]`. For the remote branch at `main`'s tip (criterion 12), the test runs `run_git(tmp_path / "human", "push", "-q", "origin", "origin/main:refs/heads/<branch>")` and then `checkout.fetch()`. The refusal of an assignment to a frozen model's field assigns with `setattr(instance, field, value)`, the field's name in a variable, because a direct assignment is a `mypy --strict` error under the pydantic plugin (`misc`, the property is read-only) and `setattr` with a constant name is ruff's `B010`.

## Acceptance criteria

1. A `WorkItemStop` whose `branch`, `title` or `text` is empty, or only whitespace, is rejected with `ValidationError` (one test per field); a stop with all three filled is accepted.
2. A `WorkItemStop` whose `branch` is not `branch_name(key.work_item)` (for example `work-item/F0001-S0002` with a key of `F0001-S0001`) is rejected with `ValidationError`.
3. A `WorkItemStop` and a `StopPosted` each reject an unknown field with `ValidationError`, and neither accepts an assignment to a field (one test, both models).
4. `pull_request` is a positive integer: for `WorkItemStop` and for `StopPosted`, the values 0 and -1 are rejected with `ValidationError` and 1 is accepted; a `WorkItemStop` also accepts `None`.
5. `opened_for_stop_description("F0001-S0001")` returns exactly `The factory opened this draft pull request to report a stop on F0001-S0001. The stop is the comment below.`
6. A stop with `pull_request` set posts its text on that pull request and returns `StopPosted(pull_request=<that number>, opened=False, outcome="posted")`; no pull request is created (`hosting.pull_requests()` is unchanged) and no git call is made.
7. A stop with `pull_request` set to a pull request that the human has closed (`close_by_human`) still posts there and returns `outcome="posted"`.
8. A stop with `pull_request=None`, for a branch with no pull request, creates a draft pull request: afterwards `hosting.pull_requests()` holds one pull request, a draft, with `branch` equal to `stop.branch`, `title` equal to `stop.title` and the description of criterion 5 (`hosting.description(number)`).
9. In that case the comment is posted on the new pull request, and the result is `StopPosted(pull_request=<the new number>, opened=True, outcome="posted")`: the pull request is opened first and the stop posted there.
10. A stop with `pull_request=None`, for a branch that already has an open pull request, posts on that pull request, creates no second one, and returns `opened=True` with that pull request's number.
11. A stop with `pull_request=None`, for a branch whose only pull request was closed by the human, creates a new draft pull request and posts there; the closed one gets no comment.
12. A stop with `pull_request=None` and no open pull request raises `HostingServiceError` with `operation == "create_pull_request"` when the branch is not on the remote, and when the remote branch is at the tip of `main` (no commit beyond it; one test, two cases); in both cases no pull request exists afterwards and nothing was posted.
13. The posted comment is the factory's: `hosting.factory_posts(number)` holds one comment with `by_factory` true and `key` equal to `stop.key`.
14. Posting the same stop a second time returns `outcome="already_posted"` with the same pull request number, and `factory_posts` still holds one comment.
15. A second stop with the same key and another `text` also returns `outcome="already_posted"`, and the first comment's text is unchanged.
16. A second stop with another key (the same `kind` and another `n`, or another `kind`) posts again: `factory_posts` holds two comments, each with its own key.
17. After a kill at `KillPoint.AFTER_POST` during the first `post` (`InjectedKill`, with `pull_request=None` in the stop, as after a restart that has not recorded the number), a second `post` of the same stop returns `outcome="already_posted"` and `factory_posts` holds exactly one comment (GH3.4).
18. In that same case `hosting.pull_requests()` still holds exactly one pull request, and the second call returns its number.
19. When `post_comment` fails once after the pull request was created (`hosting.fail_next("post_comment")`), `post` raises `HostingServiceError` and the pull request stays; posting the stop again opens no second pull request and posts the comment once.
20. When `create_pull_request` fails (`hosting.fail_next("create_pull_request")`), `post` raises `HostingServiceError`, no pull request exists and no comment was posted.
21. `post` leaves the checkout as it was: `checkout.status().changes` is empty and `checkout.resolve("HEAD")` is the same commit before and after.
22. When reading the remote branch fails with `GitError` (the `boundaries` fixture's `git` replaced with `dataclasses.replace` by a `GitCli` on a directory that does not exist), `post` of a stop with `pull_request=None` whose branch has no open pull request raises that `GitError`, and no pull request exists afterwards.
23. `make check` stays green.
24. docs: `docs/operator-guide.md` explains that a stop of one work item appears as one comment on its pull request (a draft pull request is opened first when there is none, and only when the work item's branch is on the remote with a commit beyond `main`), that a restart never repeats it, and that the comment ends with the factory's marker and its key; `docs/decisions.md` records that stops are keyed posts, so that the order of the post and the state write does not matter, and that the branch is checked before the pull request is opened.

## Demo

```bash
uv run python -c "
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from factory.adapters.clock import ManualClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.health_file import JsonHealthStatusFile
from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.domain.hosting import PostKey
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.stops import WorkItemStop
class StubGit:
    def resolve(self, ref):
        return 'a' * 40
    def is_ancestor(self, ancestor, descendant):
        return False
def service_for(hosting):
    state = Path(tempfile.mkdtemp())
    clock = ManualClock(datetime(2026, 10, 12, 12, 0, tzinfo=UTC))
    parts = dict.fromkeys(['agent_runtime', 'project_commands', 'work_item_reader', 'work_item_writer', 'cost_reader', 'cost_writer'])
    return StopService(Boundaries(**parts, git=StubGit(), hosting=hosting, clock=clock, log=TimestampedFactoryLog(state / 'factory.log', clock), health=JsonHealthStatusFile(state / 'health.json'), checkout=state))
stop = WorkItemStop(key=PostKey(work_item='F0001-S0001', kind='stall', n='3'), branch='work-item/F0001-S0001', title='F0001-S0001: stage tests stalled', pull_request=None, text='Stage tests stalled twice. Comment anything to retry; close the pull request to stop.')
hosting = FakeHostingService()
service = service_for(hosting)
first = service.post(stop)
again = service.post(stop)
print(first.opened, first.outcome, again.outcome)
pull_requests = hosting.pull_requests()
print(len(pull_requests), pull_requests[0].draft, pull_requests[0].branch)
posts = hosting.factory_posts(first.pull_request)
print(len(posts), posts[0].key == stop.key)
kill_points = KillPoints()
hosting = FakeHostingService(kill_points)
service = service_for(hosting)
kill_points.arm(KillPoint.AFTER_POST)
try:
    service.post(stop)
except InjectedKill as kill:
    print('killed at', kill.point.value)
restarted = service.post(stop)
print(restarted.outcome, len(hosting.pull_requests()), len(hosting.factory_posts(restarted.pull_request)))
"
```
Expect: five lines of output: `True posted already_posted`, then `1 True work-item/F0001-S0001`, then `1 True`, then `killed at after-post`, then `already_posted 1 1`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory/domain/stops.py` models, `factory/domain/post_texts.py`, `StopService.post` with its errors). Each behaviour in its comments (the description text, `opened` semantics, the key deciding repeats) has a criterion: 5, 9/10, 14 to 16.
   - Criteria: each is testable by one test function. Each rule has both sides. Blank fields are rejected (1) and filled ones accepted (1). The branch must match (2). Positive integers are tested at 0, -1 and 1 (4). A set pull request number is not looked up (6, 7). An open pull request is reused (10) and a closed one is not (11). The branch check refuses when the branch is missing or at main's tip (12) and passes when it is beyond main (8, 9). A GitError is raised (22), as is a HostingServiceError (19, 20). The kill and restart cases are covered (17, 18).
   - Demo: runnable as written, with a StubGit and None placeholders for the unused boundaries. The Expect line gives five concrete lines that can be compared with the output.
   - Architecture: the DTOs and text are in the domain, the service is in the application and uses only the hosting and git interfaces from Boundaries. The service writes no state, which matches R22 and R27.
   - Scope: within F0003's scope item 3 and decisions 5 to 8. The texts of individual stops and the handlers are left to F0005 to F0009.
   No questions.
3. tester: Wrote red tests for criteria 1 to 22. `make lint` is green. `make test` stops at collection on purpose: `factory.domain.post_texts` does not exist yet, and `StopPosted` / `WorkItemStop` cannot be imported from `factory.domain.stops`.

   Mapping:
   - criterion 1: tests/domain/test_work_item_stop.py::test_a_stop_with_branch_title_and_text_filled_is_accepted, ::test_a_blank_branch_is_rejected, ::test_a_blank_title_is_rejected, ::test_a_blank_text_is_rejected (each runs with empty, space and other whitespace)
   - criterion 2: tests/domain/test_work_item_stop.py::test_a_branch_of_another_work_item_is_rejected
   - criterion 3: tests/domain/test_work_item_stop.py::test_both_models_reject_an_unknown_field_and_an_assignment
   - criterion 4: tests/domain/test_work_item_stop.py::test_the_pull_request_of_a_stop_is_a_positive_integer (-1, 0, 1), ::test_a_stop_accepts_no_pull_request, ::test_the_pull_request_of_a_posted_stop_is_a_positive_integer (-1, 0, 1)
   - criterion 5: tests/domain/test_post_texts.py::test_the_description_of_a_pull_request_opened_for_a_stop_names_the_work_item
   - criterion 6: tests/application/test_stop_posting.py::test_a_stop_with_a_pull_request_is_posted_there_without_opening_one_or_calling_git. "No git call" is checked by putting a `GitCli` on a directory that does not exist into the boundaries, so any git call would raise `GitError`.
   - criterion 7: tests/application/test_stop_posting.py::test_a_stop_is_posted_on_its_pull_request_after_the_human_closed_it
   - criterion 8: tests/application/test_stop_posting.py::test_a_stop_without_a_pull_request_opens_a_draft_on_its_branch
   - criterion 9: tests/application/test_stop_posting.py::test_a_stop_without_a_pull_request_is_posted_on_the_draft_it_opened
   - criterion 10: tests/application/test_stop_posting.py::test_a_stop_without_a_pull_request_reuses_the_open_one_of_its_branch
   - criterion 11: tests/application/test_stop_posting.py::test_a_stop_without_a_pull_request_does_not_reuse_one_the_human_closed
   - criterion 12: tests/application/test_stop_posting.py::test_no_pull_request_is_opened_for_a_branch_without_a_commit_beyond_main (two cases: missing, at-main)
   - criterion 13: tests/application/test_stop_posting.py::test_the_posted_comment_is_the_factorys_with_the_stops_key
   - criterion 14: tests/application/test_stop_posting.py::test_posting_the_same_stop_again_posts_nothing
   - criterion 15: tests/application/test_stop_posting.py::test_a_stop_with_the_same_key_and_another_text_posts_nothing
   - criterion 16: tests/application/test_stop_posting.py::test_a_stop_with_another_key_posts_again (two cases: another-n, another-kind)
   - criterion 17: tests/application/test_stop_posting.py::test_a_stop_killed_after_its_post_is_not_posted_again_after_the_restart
   - criterion 18: tests/application/test_stop_posting.py::test_a_stop_killed_after_its_post_opens_no_second_pull_request_after_the_restart
   - criterion 19: tests/application/test_stop_posting.py::test_a_failed_post_keeps_the_opened_pull_request_and_the_retry_posts_once
   - criterion 20: tests/application/test_stop_posting.py::test_a_failed_pull_request_creation_posts_nothing
   - criterion 21: tests/application/test_stop_posting.py::test_posting_a_stop_leaves_the_checkout_as_it_was
   - criterion 22: tests/application/test_stop_posting.py::test_a_git_error_reading_the_remote_branch_is_raised_and_opens_nothing

   Files created:
   - tests/domain/test_work_item_stop.py
   - tests/domain/test_post_texts.py
   - tests/application/test_stop_posting.py

   Modules the test runner could not import:
   - `factory.domain.post_texts` (missing)
   - `StopPosted` and `WorkItemStop` from `factory.domain.stops`
   - `StopService.post` does not exist yet either; the tests fail on it once the imports resolve.

   In criteria 12 and 20, "nothing was posted" is asserted through `hosting.pull_requests() == []`: without a pull request there can be no comment.

   No questions.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built posting a work item's stop once on its pull request. `make check` is green and the Demo prints the five expected lines.

   - `src/factory/domain/stops.py`: added `WorkItemStop` and `StopPosted`. Both are frozen with `extra="forbid"`. One shared field validator refuses a blank `branch`, `title` or `text`. A model validator requires `branch == branch_name(key.work_item)`. `pull_request` is `PositiveInt | None` on the stop and `PositiveInt` on the result, and `outcome` is `PostOutcome`.
   - `src/factory/domain/post_texts.py`: new module with `opened_for_stop_description`.
   - `src/factory/application/stops.py`: added `StopService.post`.
     - When `stop.pull_request` is set, it posts there and calls neither git nor any lookup.
     - Otherwise it reuses `find_open_pull_request(branch)`. When there is none, it first checks `resolve("origin/<branch>")`, then that the result is not an ancestor of `origin/main`, and only then calls `create_pull_request(..., draft=True)`. A failed check raises `HostingServiceError("create_pull_request", "branch <branch> is not on the remote with a commit beyond main")`.
     - It then calls the keyed `post_comment`. `opened` is `stop.pull_request is None`.
     - Nothing is caught and no state is written.
   - Commits: c90ee70 (feat), 2914411 (refactor).

   Main decision: `post` relies entirely on the hosting service's keyed `post_comment` to make a repeat a no-op. It keeps no record of its own before or after the post, so a kill between the post and the caller's state write needs no recovery path in this service. Rejected: listing the comments first to detect an earlier post. That would duplicate what the keyed post already guarantees and add a call that can fail.

   Refactor: the first version had a private `_REMOTE = "origin/"` constant. The refactor replaced it with the existing `REMOTE` from `factory.domain.paths`, next to `MAIN_BRANCH`. Nothing else needed changing.

   Noticed, not touched: the `StopService` docstring said "never to a pull request". I rewrote it because the class now posts to one. The class now covers two kinds of stop; splitting it would be a separate ticket.

   `make check`: check: green
5. reviewer: Groups 1 to 3 pass. Criteria 1 to 22 each have a test that checks what the criterion says. Each rule in the Interface has its failing side tested: blank fields, a foreign branch, unknown fields, assignment, `pull_request` at -1, 0 and 1, a missing branch and a branch at main's tip, GitError, and both HostingServiceError paths. Criterion 6 checks for "no git call" by using a GitCli on a missing directory. Criterion 14 posts the second time with the recorded number instead of `None`. The repeat with `None` is covered by 17, 18 and 19, so I accept that. The coder's entry says `make check` is green. The layers hold: the application imports only from the domain and uses the `Git` and hosting interfaces through `Boundaries`. Nothing is silenced and there are no secrets. Group 4 has one finding:

   1. `src/factory/application/stops.py:24` (`StopService.__init__`): the docstring still says "Report through the log and the health status store of `boundaries`". `post` now also posts through `boundaries.hosting` and reads `boundaries.git`, so the docstring is wrong. The coder updated the class docstring for this reason but missed this one. Fix: reword it to cover the hosting service and git as well, e.g. "Report through the log, health status, hosting service and git of `boundaries`."
6. coder: Round 1. Fixed the reviewer's one finding and nothing else.

   - `src/factory/application/stops.py:24`: the docstring of `StopService.__init__` now reads "Report through the log, health status, hosting service and git of `boundaries`." It names every boundary the service uses, including the two that `post` uses. Commit 7fc337f.

   Refactor: none needed. The change is a single docstring line.

   `make check`: check: green

   `make check`: check: green
7. reviewer: No findings. Round 1 fixed the finding from entry 5: `src/factory/application/stops.py:24` now names every boundary the service uses.

   - Group 1 passes. Criteria 1 to 22 each have a test that checks what the criterion says. The failing side of each Interface rule is tested: a blank branch, title or text (empty, a space, other whitespace); a branch that belongs to another work item; unknown fields; assignment to a frozen field; `pull_request` at -1, 0 and 1, plus `None`; a remote branch that is missing or sits at main's tip; a `GitError` from reading the branch; and both `HostingServiceError` paths. "No git call" in criterion 6 is checked with a `GitCli` on a directory that does not exist. Criterion 14 re-posts with the recorded number. The repeat with `pull_request=None` is covered by criteria 17, 18 and 19. The coder's entry 6 reports `make check` green.
   - Group 2 passes. `post` uses only the `Git` and `HostingService` interfaces through `Boundaries`, and their signatures match the calls: `resolve` returns `CommitId | None` and `is_ancestor` returns `bool`. The domain imports only from the domain. Nothing is wired outside `factory.entry`.
   - Group 3 passes. No secrets, no markers that silence a check, no shell commands built from strings. The new models validate their input when they are built.
   - Group 4 passes. The docstrings of the module, `WorkItemStop`, `StopPosted`, `post` and `opened_for_stop_description` describe what the code does. The comments explain why: the keyed post makes a repeat a no-op, and the branch check makes the fake fail the way production does. The code reuses `REMOTE` and `MAIN_BRANCH` from `factory.domain.paths`. There is no dead code.
   - Group 5 passes. Entry 4 states the main decision: rely on the keyed `post_comment` alone. It also says what was rejected: listing comments first. The Assignment matches what was built. Criterion 24 still describes what the operator guide and the decision log need.
8. documenter: wrote the documentation for criterion 24 and fixed one stale sentence. `make check` is green.

   Files changed:
   - `docs/operator-guide.md`: new section "Stops of one work item". It covers the single comment on the pull request and its marker and key. It says a draft pull request is opened first when there is none, and only when the branch is on the remote with a commit beyond `main`. It says a restart never repeats a stop. It also says which pull request is reused or posted on, and that the caller records the number.
   - `docs/decisions.md`: new entry. Stops are keyed posts, so the order of the post and the state write does not matter. The branch is checked before the pull request is opened, so the fake and production refuse the same case. Alternatives rejected are listed.
   - `docs/project-guide.md`: the `StopService` paragraph said it "never reaches a pull request". It now says this holds for repository and machine stops, and describes `post`, `WorkItemStop` and `StopPosted`.

   Cross-read and found current: `README.md`, the operator guide's other sections, and the post-key and marker section of the project guide. The marker and key format shown in the new section matches `render_post`. The stop description text matches `opened_for_stop_description`.

   I did not run the examples. The new section has no runnable commands.

   No findings for the coder. The docstrings and the Interface match the code. I saw nothing stale that is unrelated to this story.

   `make check`: check: green
