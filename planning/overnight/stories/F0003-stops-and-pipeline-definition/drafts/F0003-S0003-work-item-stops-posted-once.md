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

Tests: `tests/domain/test_work_item_stop.py`, `tests/domain/test_post_texts.py`, `tests/application/test_stop_posting.py`. They use the fixtures `hosting` (the fake, with `kill_points`), `kill_points`, `checkout`, `human` and `boundaries` that earlier stories put in `tests/conftest.py`, and the fake's `fail_next`, `pull_requests`, `factory_posts` and `close_by_human`. A test that opens a pull request first pushes the stop's branch with `human.push_file(branch, "note.txt", "x")` and then calls `checkout.fetch()`. The refusal of an unknown field is tested through a variable typed `type[BaseModel]`.

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
22. `make check` stays green.
23. docs: `docs/operator-guide.md` explains that a stop of one work item appears as one comment on its pull request (a draft pull request is opened first when there is none, and only when the work item's branch is on the remote with a commit beyond `main`), that a restart never repeats it, and that the comment ends with the factory's marker and its key; `docs/decisions.md` records that stops are keyed posts, so that the order of the post and the state write does not matter, and that the branch is checked before the pull request is opened.

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
