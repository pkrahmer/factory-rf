---
stage: demo
pr: 14
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The hosting-service fake

## Assignment (as of log entry 1)

Build the one fake of the hosting service that every test of the factory uses (SI2.3): `FakeHostingService` implements the `HostingService` protocol of S0002 in memory, and adds the test operations that act as the human on the pull request (comment, delete a comment, close, merge), make the next call fail, and inspect what the factory did. It behaves as the PyGithub client of S0003 does where the tests can see it: the post key makes a repeated post a no-op, `merge_commit` is set only for a merged pull request, labels are replaced only where they start with `stage:`, every failing call raises the one `HostingServiceError`. It reaches the `after-post` kill point after a post, so that a test can kill the tick between a post and its record. Covers SI2.3 and R10 (one fake implements the same interface; the fake is also how GH3.4 and ST1.1 will count posts); keeps kept thing 11 (posts carry the marker and, here, a key). It was split from the interface story (S0002) to keep each story within 26 criteria, and it comes after the PyGithub client (S0003).

## Interface

`src/factory/adapters/fake_hosting.py`

```python
class FakeHostingService:      # satisfies HostingService structurally, no inheritance
    """Implements the ten operations of HostingService, with the signatures of S0002, in memory."""

    def __init__(self, kill_points: KillPoints | None = None) -> None: ...
    def add_human_comment(self, number: int, body: str, *, author: str = "human") -> int: ...
    def delete_comment(self, number: int, comment_id: int) -> None: ...
    def close_by_human(self, number: int) -> None: ...
    def merge_by_human(self, number: int, merge_commit: CommitId) -> None: ...
    def fail_next(self, operation: str, *, times: int = 1) -> None: ...
    def factory_posts(self, number: int) -> list[PullRequestComment]: ...
    def labels(self, number: int) -> list[str]: ...
    def description(self, number: int) -> str: ...
    def pull_requests(self) -> list[PullRequestView]: ...
```

The rules, each with a criterion below:

- Pull request numbers start at 1 and rise by one with each created pull request. Comment ids start at 1 and rise by one across all pull requests, the human's and the factory's alike. The `url` of pull request `n` is `https://fake.invalid/pull/<n>`. The `created_at` of the comment with id `i` is the date 2026-10-12 in UTC plus `i` seconds.
- `create_pull_request` makes an open pull request with the given branch, title and draft flag, no merge commit and no labels; its description is `body`.
- `find_open_pull_request(branch)` returns the open pull request of that branch, and `None` when there is none, or when the pull requests of that branch are closed or merged.
- `close_by_human(n)` and `close(n)` set the state to `"closed"`; `reopen(n)` sets it to `"open"`; `merge_by_human(n, commit)` sets it to `"merged"` with `merge_commit` set to `commit`. `set_draft` sets the draft flag; `set_description` replaces the description, which `description(n)` returns.
- `set_labels(n, labels)` removes the labels that start with `LABEL_PREFIX`, keeps the others in their order and adds the given labels after them; `labels(n)` returns the result.
- `list_comments(n)` returns the comments of that pull request ordered by id ascending (oldest first), each built with `PullRequestComment.from_body`. `add_human_comment` adds a comment with the given author (default `"human"`) and body as written and returns its id. `delete_comment` removes it; an id that does not exist raises `HostingServiceError`.
- `post_comment(n, text, key)` adds a comment with the author `"factory"` and the body `render_post(text, key)` and returns `"posted"`, then reaches `KillPoint.AFTER_POST` (when the fake has kill points). When a comment of that pull request already has `key` as its key, it adds nothing, reaches no kill point and returns `"already_posted"`. `factory_posts(n)` returns the comments whose `by_factory` is true, in order.
- Every operation that takes a pull request number (the eight of the protocol and the seven test operations above that take one) raises `HostingServiceError` for a number that does not exist.
- `fail_next(operation, times=n)`, for one of the ten protocol operations by name, makes the next `n` calls of that operation raise `HostingServiceError(operation, "injected failure")` before they have any effect; calls of other operations, and later calls of that one, are not affected. An operation that is not one of the ten, or a `times` below 1, raises `ValueError`.
- `pull_requests()` returns every pull request, whatever its state, ordered by number.

Tests: `tests/adapters/test_fake_hosting.py`, `tests/test_hosting_fake_search.py` (uses `tests/source_search.py` from S0003); `tests/conftest.py` gains the fixture `hosting`, a `FakeHostingService(kill_points)` (an addition; no existing fixture is changed). A test that needs a commit id uses a low-entropy literal such as `"a" * 40`, so that `make secrets` stays green. A test module assigns `FakeHostingService` to a variable annotated `HostingService`, so that mypy checks the fit.

## Acceptance criteria

1. `create_pull_request("work-item/F0001-S0001", "title", "body", draft=True)` returns an open view with that branch, title and `draft` true, `merge_commit` `None`, number 1 and the url `https://fake.invalid/pull/1`; a second call returns number 2; `description(1)` is `body` and `labels(1)` is `[]`; with `draft=False` the flag is false.
2. `pull_requests()` returns every pull request, including a closed one and a merged one, ordered by number.
3. `find_open_pull_request` returns the open pull request of a branch, and `None` for a branch without one, for one whose pull request was closed, and for one whose pull request was merged.
4. After `close_by_human(n)`, `get_pull_request(n)` is `"closed"` with `merge_commit` `None`; after `merge_by_human(n, commit)` it is `"merged"` with `merge_commit == commit` and the draft flag as before.
5. `close(n)` makes the state `"closed"` and a following `reopen(n)` makes it `"open"` again.
6. `set_draft(n, False)` makes `get_pull_request(n).draft` false and `set_draft(n, True)` makes it true; `set_description(n, "new")` makes `description(n)` return `new`.
7. `set_labels(n, ["stage:doing"])` after `set_labels(n, ["bug"])` gives `["bug", "stage:doing"]`; a following `set_labels(n, ["stage:review"])` gives `["bug", "stage:review"]`.
8. `add_human_comment` returns ids 1, 2 and 3 across two pull requests; `list_comments` of each returns its comments ordered by id; the `created_at` of consecutive ids differs by one second, is in UTC and falls on 2026-10-12 for the first comment.
9. A comment added with `add_human_comment(n, "(a)")` has the author `human`, `by_factory` false and `key` `None`; with `author="someone"` the author is kept; a body that only quotes a key line without the marker has `by_factory` false and `key` `None`.
10. `post_comment` returns `"posted"` and the pull request then has a comment by `factory` whose body is `render_post(text, key)`, whose `by_factory` is true and whose `key` is the key; `factory_posts(n)` holds that comment and not a human comment.
11. A second `post_comment` with the same key returns `"already_posted"` and the number of comments is unchanged; with another `n` or another kind it returns `"posted"`.
12. With `KillPoint.AFTER_POST` armed, `post_comment` raises `InjectedKill` and the comment is already in `list_comments`; a repeated `post_comment` with the same key then returns `"already_posted"`; the point is reached once per `"posted"` and not at all for `"already_posted"`; a `FakeHostingService` built without kill points posts normally.
13. `delete_comment(n, id)` removes the comment, so `list_comments` no longer lists it; an id that does not exist raises `HostingServiceError`.
14. For a pull request number that does not exist, each of `get_pull_request`, `list_comments`, `post_comment`, `close`, `reopen`, `set_draft`, `set_description`, `set_labels`, `add_human_comment`, `delete_comment`, `close_by_human`, `merge_by_human`, `factory_posts`, `labels` and `description` raises `HostingServiceError`.
15. After `fail_next("post_comment", times=2)`, the next two `post_comment` calls raise `HostingServiceError` with `operation == "post_comment"` and `detail == "injected failure"` and post nothing, the third call posts; in between `list_comments` works.
16. `fail_next("nope")` and `fail_next("post_comment", times=0)` raise `ValueError`, and `fail_next("post_comment", times=1)` is accepted.
17. Among the concrete classes of `src/factory` (those that are not `Protocol` classes, so the `HostingService` protocol of S0002 is left out), exactly `FakeHostingService` and `PyGithubHostingService` define a method named `post_comment`, and no class under `tests/` does.
18. `FakeHostingService` is not a subclass of `HostingService`, and a test module assigns a `FakeHostingService` to a variable annotated `HostingService`, so that `make check` (mypy) proves the structural fit.
19. make check stays green.
20. docs: `docs/project-guide.md` says that tests use `FakeHostingService` (the `hosting` fixture) and nothing else in place of the hosting service, and lists its test operations (`add_human_comment`, `delete_comment`, `close_by_human`, `merge_by_human`, `fail_next`, `factory_posts`, `labels`, `description`, `pull_requests`).

## Demo

```bash
uv run python -c "
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.hosting import PostKey
hosting = FakeHostingService()
pull = hosting.create_pull_request('work-item/F0001-S0001', 'F0001-S0001: title', 'body', draft=True)
key = PostKey(work_item='F0001-S0001', kind='question', n='2')
print(pull.number, pull.state, pull.draft)
print(hosting.post_comment(pull.number, 'Which option?', key))
print(hosting.post_comment(pull.number, 'Which option?', key))
print(len(hosting.factory_posts(pull.number)))
hosting.add_human_comment(pull.number, '(a)')
print([comment.author for comment in hosting.list_comments(pull.number)])
"
```
Expect: five lines: `1 open True`, `posted`, `already_posted`, `1`, `['factory', 'human']`.

```bash
uv run python -c "
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.hosting import PostKey
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
kill_points = KillPoints()
hosting = FakeHostingService(kill_points)
pull = hosting.create_pull_request('work-item/F0001-S0001', 'title', 'body', draft=True)
key = PostKey(work_item='F0001-S0001', kind='stall', n='5')
kill_points.arm(KillPoint.AFTER_POST)
try:
    hosting.post_comment(pull.number, 'Stalled.', key)
except InjectedKill as kill:
    print(kill, len(hosting.factory_posts(pull.number)))
print(hosting.post_comment(pull.number, 'Stalled.', key), len(hosting.factory_posts(pull.number)))
"
```
Expect: two lines: `injected kill at after-post 1`, then `already_posted 1`: the tick died after the post, and the rerun posts nothing a second time.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted. Format check passed; nothing was changed in the story.
   - Interface: `src/factory/adapters/fake_hosting.py` names the class, its constructor and the nine test operations with full signatures. The ten protocol operations are the signatures of S0002. Every behaviour in its comments and rules (numbering, url, created_at, post key, label replacement, kill point, failure injection) has a criterion.
   - Criteria: each fits one test function. Every rule has its failing side: a missing pull request number (14, all 15 operations, which matches the eight protocol plus seven test operations that take a number), a missing comment id (13), a repeated key (11, 12), an invalid `fail_next` (16), injected failure (15), and no pull request found for closed or merged (3). The edge case of `delete_comment` with an id that belongs to another pull request is not stated; I take it as outside the rules, since the fake allows what GitHub would refuse unless a criterion says otherwise (decision 6).
   - Demo: both blocks are runnable with `uv run python -c`. Each Expect line is checkable output: five lines in the first block and two in the second. The second relies on the `InjectedKill` text `injected kill at after-post` from S0001.
   - Architecture: the fake sits in `factory.adapters`, satisfies the `HostingService` protocol structurally (criterion 18), and is the only fake of the hosting service (criterion 17). It imports only domain types, so the layering holds.
   - Scope: within FEATURE.md ("the one fake (SI2.3)"). It does not touch wiring, the posting rules of handlers or the kill-point tests, all of which are out of scope.
3. tester: wrote red tests for every acceptance criterion of the hosting-service fake.

   Criterion → test:
   - criterion 1: tests/adapters/test_fake_hosting.py::test_created_pull_requests_are_open_numbered_and_carry_url_description_and_no_labels
   - criterion 2: tests/adapters/test_fake_hosting.py::test_pull_requests_lists_every_state_ordered_by_number
   - criterion 3: tests/adapters/test_fake_hosting.py::test_find_open_pull_request_returns_only_an_open_one
   - criterion 4: tests/adapters/test_fake_hosting.py::test_human_close_and_merge_set_state_and_merge_commit
   - criterion 5: tests/adapters/test_fake_hosting.py::test_close_and_reopen_toggle_the_state
   - criterion 6: tests/adapters/test_fake_hosting.py::test_set_draft_and_set_description_change_the_pull_request
   - criterion 7: tests/adapters/test_fake_hosting.py::test_set_labels_replaces_only_stage_labels
   - criterion 8: tests/adapters/test_fake_hosting.py::test_comment_ids_rise_across_pull_requests_with_a_second_apart
   - criterion 9: tests/adapters/test_fake_hosting.py::test_human_comments_are_not_factory_posts
   - criterion 10: tests/adapters/test_fake_hosting.py::test_post_comment_adds_a_factory_post_with_marker_and_key
   - criterion 11: tests/adapters/test_fake_hosting.py::test_a_repeated_key_is_not_posted_again
   - criterion 12: tests/adapters/test_fake_hosting.py::test_after_post_kill_point_fires_after_the_post_and_not_for_a_repeat
   - criterion 13: tests/adapters/test_fake_hosting.py::test_delete_comment_removes_it_and_refuses_an_unknown_id
   - criterion 14: tests/adapters/test_fake_hosting.py::test_an_unknown_pull_request_number_is_refused (parametrized, one case per operation, 15 in all)
   - criterion 15: tests/adapters/test_fake_hosting.py::test_fail_next_fails_that_many_calls_of_that_operation
   - criterion 16: tests/adapters/test_fake_hosting.py::test_fail_next_refuses_an_unknown_operation_or_times_below_one (cases: unknown name, times=0) and ::test_fail_next_accepts_one_time (times=1)
   - criterion 17: tests/test_hosting_fake_search.py::test_only_the_fake_and_the_pygithub_client_define_post_comment and ::test_no_test_class_defines_post_comment. Protocol classes are found by a `Protocol` base in the AST.
   - criterion 18: tests/adapters/test_fake_hosting.py::test_the_fake_fits_the_protocol_without_inheriting_it. It assigns the fake to a variable annotated `HostingService`, so mypy checks the fit, and it asserts that `HostingService` is not in the MRO.
   - criterion 19 (make check) and criterion 20 (docs) are not test functions. Criterion 19 is the gate the coder runs; criterion 20 belongs to the documenter.

   Files: I created tests/adapters/test_fake_hosting.py and tests/test_hosting_fake_search.py. I added the `hosting` fixture to tests/conftest.py, which returns `FakeHostingService(kill_points)`. No existing fixture was changed.

   Red run: `make test` stops when it loads conftest with `ModuleNotFoundError: No module named 'factory.adapters.fake_hosting'`. That is the only module the runner could not import. Because conftest imports the fake, the whole suite is red until the module exists. `make lint` is green.

   Choices made inside the criteria: in criterion 14, operations that need a comment id or other arguments get valid ones, so only the pull request number is wrong. In criterion 12, "once per posted" is checked with a second post under a new key, which raises the reach count to 2. The test for criterion 8 also checks that the first comment's `tzinfo` is `UTC`. I left untested the case that the criteria leave open: `delete_comment` with an id that belongs to another pull request, as intake noted.

   `make lint`: lint: green
   `make test`: E   ModuleNotFoundError: No module named 'factory.adapters.fake_hosting'
4. coder: built `FakeHostingService` in `src/factory/adapters/fake_hosting.py`. All tests pass and `make check` is green (coverage 99 %, the new module is fully covered). The second demo block prints `injected kill at after-post 1` / `already_posted 1` as expected.

   What it does:
   - Each pull request is a private mutable `_PullRequest` dataclass that holds its description, labels and comments. Callers get a frozen `PullRequestView` built fresh on each read, so the domain DTOs stay frozen and the test operations can change state in place.
   - Comment ids come from one counter shared by all pull requests. `created_at` is 2026-10-12 UTC plus the id in seconds. Every comment, the human's and the factory's, goes through `PullRequestComment.from_body`, so `by_factory` and `key` are derived the same way as in the PyGithub client.
   - `post_comment` follows `PyGithubHostingService.post_comment`: first the key check, then the post, then `KillPoint.AFTER_POST`. A repeated key reaches no kill point.
   - Each of the ten protocol operations first checks for an injected failure and only then looks up the pull request number. So an injected failure has no effect at all, even for a number that does not exist. The test operations take no injected failures, as the interface says (`fail_next` names only the ten).
   - `set_labels` uses the same `LABEL_PREFIX` filter as the PyGithub client.

   Rejected: storing pull requests as `PullRequestView` and replacing them with `model_copy(update=...)`. The description, labels and comments would then need side dictionaries next to the view, and the state would be split across several places.

   Refactor pass: I read the diff (one new file). Nothing to rename or simplify, so there is no refactor commit.

   Noticed, not touched: `delete_comment` with an id that belongs to another pull request raises `HostingServiceError`, because it searches only the comments of the given pull request. No criterion covers this case, as intake noted. Criterion 20 (docs) is left for the documenter.

   `make check`: check: green
5. reviewer: no findings.

   - Acceptance criteria: I read every test against its criterion. Criteria 1–18 each have a test that checks what the criterion names. The failing sides of the Interface's rules are tested: an unknown pull request number for all 15 operations (criterion 14), an unknown comment id (13), a repeated key (11, 12), an injected failure that posts nothing (15), an unknown operation for `fail_next` (16), and `times` on both sides of its limit, 0 refused and 1 accepted (16). Criterion 17 checks every module under `src/factory` (`tests/source_search.py`) and every file under `tests/`, and leaves out `Protocol` classes. Criterion 18 relies on the variable annotated `HostingService` that mypy checks, and also checks the MRO. Per the coder's entry, the factory's `make check` after the coder was green.
   - Architecture: `src/factory/adapters/fake_hosting.py` imports only `factory.domain`. It fits the protocol structurally without inheriting from it. It calls no tool, and no `dict[str, Any]` crosses a function boundary.
   - Security: no suppression markers, no secrets (the commit id is `"a" * 40`), and no shell or file I/O.
   - Quality: `post_comment` follows `PyGithubHostingService.post_comment` (key check, then post, then `AFTER_POST`). `set_labels` uses the shared `LABEL_PREFIX`. Comments go through `PullRequestComment.from_body`, as in the real client. Public names have docstrings and private ones have none.
   - Ticket hygiene: the coder's entry explains the main decision (a private mutable `_PullRequest` with fresh frozen views) and what was rejected (`model_copy` with side dictionaries). `Assignment` matches what was built. Criterion 20 still says what the documenter must write.

   Open, not a finding: `delete_comment` raises `HostingServiceError` when the id belongs to another pull request. No criterion states this case, as intake, the tester and the coder all noted.
6. documenter: no findings.
   - `docs/project-guide.md`: new subsection "The fake" under the hosting service (the `hosting` fixture and `FakeHostingService` as the only stand-in, the behaviour shared with the PyGithub client, numbering, url and `created_at`, the kill point, a table of the nine test operations, a short example). The two "fake follows in a later story" sentences were stale and now point to it.
   - `README.md`: the status sentence lists the hosting fake.
   - Cross-read and found current: the rest of the project guide's hosting section and the kill-points table (`AFTER_POST` already names the fake), `docs/decisions.md`, `docs/operator-guide.md`. The diff matches the Interface; I did not re-run the demo blocks, the coder ran the second one. `make check` is green.
   - Not touched: nothing stale seen. Open, not a finding: `delete_comment` with an id from another pull request raises `HostingServiceError`; no criterion covers it, so the guide only says an unknown id raises.

   `make check`: check: green
