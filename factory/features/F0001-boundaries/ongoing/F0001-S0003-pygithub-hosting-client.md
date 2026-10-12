---
stage: docs
pr: 3
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The PyGithub hosting client and its one error type

## Assignment (as of log entry 1)

Build the first implementation of the hosting-service interface on PyGithub, so that every call to the hosting service goes through one client with one error handling. Every failing call, whether the API answers with an error or cannot be reached, raises the one `HostingServiceError` to every caller. A search test proves that no other module imports `github`, calls the hosting service's API by another route, or names the `gh` tool. The client is tested against stand-ins of PyGithub's objects with no network (a real call is a morning observation, and the baseline run is the first to see it). Covers SI2.1, SI2.2 and R9 (PyGithub behind the hosting-service interface; not GitPython, pygit2, dulwich, githubkit, the `gh` tool or plain httpx); builds on S0002 and keeps kept thing 11 (the post carries the marker and its key). The fake (S0014) is the other implementation; wiring that builds the PyGithub `Repository` from the token is F0002 onward (`factory.entry.wiring`), with F0010 for the token.

## Interface

`src/factory/adapters/pygithub_hosting.py`

```python
from github.Repository import Repository

class PyGithubHostingService:      # satisfies HostingService structurally, no inheritance
    """Implements the ten operations of HostingService, with the signatures of S0002."""

    def __init__(self, repository: Repository, kill_points: KillPoints | None = None) -> None: ...
```

The members of PyGithub that the client uses, which the stand-ins provide (PyGithub 2.10.0):

- `repository.create_pull(base, head, *, title, body, draft)`, `repository.get_pulls(state=..., head=...)`, `repository.get_pull(number)`, `repository.owner.login`. The constructor reads nothing from the repository; `owner.login` is read only inside `find_open_pull_request`.
- On a pull request: `number`, `head.ref`, `title`, `state` (`"open"` or `"closed"`), `merged` (bool), `draft` (bool), `merge_commit_sha`, `html_url`, `get_issue_comments()`, `create_issue_comment(body)`, `edit(state=...)` and `edit(body=...)`, `convert_to_draft()`, `mark_ready_for_review()`, `get_labels()`, `set_labels(*names)`.
- On a comment: `id`, `user.login`, `body`, `created_at`. On a label: `name`.

The rules, each with a criterion below:

- `create_pull_request` calls `create_pull(base=MAIN_BRANCH, head=branch, title=title, body=body, draft=draft)` once.
- `find_open_pull_request` calls `get_pulls(state="open", head="<repository.owner.login>:<branch>")` and returns the first result as a view, or `None` when there is none.
- A pull request becomes a `PullRequestView` as follows: `branch` is `head.ref`, `url` is `html_url`; `state` is `"merged"` when `merged` is true, else `"open"` when `state` is `"open"`, else `"closed"`; `merge_commit` is `merge_commit_sha` only when the pull request is merged, and `None` otherwise, even when GitHub reports a test-merge commit for an open pull request.
- `list_comments` returns the pull request's issue comments as `PullRequestComment.from_body(...)` (the author is `user.login`), sorted by `id` ascending whatever order PyGithub gives; a naive `created_at` is read as UTC.
- `post_comment` first lists the comments; when one of them has a `key` equal to the given key it returns `"already_posted"` and posts nothing. Otherwise it calls `create_issue_comment(render_post(text, key))` once, reaches `KillPoint.AFTER_POST` (when it has kill points), and returns `"posted"`. A comment that quotes a key line without the marker has no key and does not count.
- `close` calls `edit(state="closed")`, `reopen` calls `edit(state="open")`, `set_draft(number, True)` calls `convert_to_draft()`, `set_draft(number, False)` calls `mark_ready_for_review()`, `set_description` calls `edit(body=body)`.
- `set_labels` reads the pull request's label names and calls `set_labels` with the names that do not start with `LABEL_PREFIX`, in their order, followed by the given labels. The names it read are never returned.
- A `github.GithubException` or an `OSError` (a connection error is an `OSError`) raised inside any of the ten operations is raised again as `HostingServiceError(operation, detail)` with the operation's name and `str(error)` as detail, chained to the original (`raise ... from error`). Any other exception, and `InjectedKill`, passes through unchanged.
- `github` is imported by this module only; no module in `src/factory` imports `requests`, `httpx`, `aiohttp`, `urllib3`, `urllib.request`, `http.client`, `socket`, `git`, `pygit2`, `dulwich` or `githubkit`, and none contains the string literal `"gh"`. The search reads import statements and string literals; it does not see `importlib` or a command line built from pieces, which F0001's other searches and `make check` (ruff `S` rules) cover.

Tests: `tests/adapters/test_pygithub_hosting.py`, with stand-ins in `tests/adapters/pygithub_stand_ins.py` (plain classes with the members above that record every call, passed to the client with `typing.cast`; the module also assigns the client to a variable annotated `HostingService`, so that mypy checks the fit); `tests/source_search.py` (a helper that parses every module under `src/factory` with `ast`) and `tests/test_hosting_search.py`. A test that needs a commit id uses a low-entropy literal such as `"a" * 40`, so that `make secrets` stays green.

## Acceptance criteria

1. `create_pull_request("work-item/F0001-S0001", "title", "body", draft=True)` calls `create_pull` once with `base="main"`, `head="work-item/F0001-S0001"`, the title, the body and `draft=True`, and returns the view built from the result; with `draft=False` it passes `False`.
2. `find_open_pull_request(branch)` calls `get_pulls` with `state="open"` and `head="<owner login>:<branch>"` and returns the first result as a view.
3. `find_open_pull_request` returns `None` when `get_pulls` returns nothing.
4. `get_pull_request(5)` calls `get_pull(5)` and returns a view with the pull request's number, `head.ref` as `branch`, title, draft flag and `html_url` as `url`.
5. The state of the view is `"merged"` for a pull request whose `merged` is true (with `state` `"closed"` in PyGithub, and `merge_commit` equal to `merge_commit_sha`), `"closed"` for one that is closed and not merged, and `"open"` for an open one.
6. `merge_commit` is `None` for an open pull request and for a closed unmerged one even when `merge_commit_sha` is set.
7. `list_comments` returns each comment with its id, `user.login` as author, body and `created_at`, oldest first by id even when the stand-in returns them in another order, and reads a naive `created_at` as UTC.
8. A comment made by `render_post` is returned with `by_factory` true and its key; a comment with the marker and no key has `by_factory` true and `key` `None`; a comment with a key line and no marker has `by_factory` false and `key` `None`.
9. `post_comment` on a pull request without a comment of that key calls `create_issue_comment` once with `render_post(text, key)` and returns `"posted"`.
10. `post_comment` returns `"already_posted"` and does not call `create_issue_comment` when a comment with the same key exists; a comment that only quotes the key line without the marker does not count, and `"posted"` is returned.
11. With `KillPoint.AFTER_POST` armed, `post_comment` raises `InjectedKill` after `create_issue_comment` was called, and a second `post_comment` with the same key on the same stand-in returns `"already_posted"`; the point is not reached on `"already_posted"`, and without kill points the call returns normally.
12. `close` calls `edit(state="closed")` and `reopen` calls `edit(state="open")` on the pull request of that number.
13. `set_draft(n, True)` calls `convert_to_draft()` and `set_draft(n, False)` calls `mark_ready_for_review()`.
14. `set_description(n, "new text")` calls `edit(body="new text")`.
15. `set_labels(n, ["stage:doing"])` on a pull request that has the labels `bug` and `stage:tests` calls `set_labels("bug", "stage:doing")`; with no existing label it calls `set_labels("stage:doing")`.
16. For each of the ten operations, a `GithubException` (status 500) and an `OSError` raised by the stand-in surface as `HostingServiceError` whose `operation` is the operation's name and whose `detail` is `str(error)`, with the original as `__cause__`; for `post_comment` this holds whether the error comes while listing or while posting.
17. A `ValueError` raised by the stand-in passes through unchanged, and so does `InjectedKill` raised by the client's own kill point.
18. `PyGithubHostingService(repository)` calls nothing on `repository` and reads no attribute of it: a stand-in that raises on every access is accepted by the constructor.
19. Among the modules of `src/factory`, exactly `factory.adapters.pygithub_hosting` imports `github`, and none imports `requests`, `httpx`, `aiohttp`, `urllib3`, `urllib.request`, `http.client`, `socket`, `git`, `pygit2`, `dulwich` or `githubkit`.
20. No module under `src/factory` contains the string literal `"gh"`.
21. `PyGithubHostingService` is not a subclass of `HostingService`, and a test module assigns a `PyGithubHostingService` to a variable annotated `HostingService`, so that `make check` (mypy) proves the structural fit.
22. make check stays green.
23. docs: `docs/project-guide.md` states that the hosting service is reached only through the `HostingService` interface, that `PyGithubHostingService` is the one client and raises `HostingServiceError` for every failing call, and that tests do not call PyGithub: they use stand-ins of its objects here, and a fake follows in a later story; `docs/decisions.md` records why PyGithub and not `gh`, GitPython-style wrappers or plain httpx (R9) (WE6.3).

## Demo

```bash
uv run python -c "
from github import GithubException
from factory.adapters.pygithub_hosting import PyGithubHostingService
from factory.domain.errors import HostingServiceError
class Broken:
    def get_pull(self, number):
        raise GithubException(404, {'message': 'Not Found'}, None)
service = PyGithubHostingService(Broken())
try:
    service.get_pull_request(5)
except HostingServiceError as error:
    print(error.operation, '|', error.detail)
"
```
Expect: one line, `get_pull_request | 404 {"message": "Not Found"}`.

```bash
uv run python -c "
import ast, pathlib
found = []
for path in sorted(pathlib.Path('src/factory').rglob('*.py')):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        if any(name == 'github' or name.startswith('github.') for name in names):
            found.append(path.as_posix())
print(sorted(set(found)))
"
```
Expect: one line, `['src/factory/adapters/pygithub_hosting.py']`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `src/factory/adapters/pygithub_hosting.py` names the class, the constructor signature and the exact PyGithub members the stand-ins must provide. Every operation's call and mapping is stated concretely: the `create_pull` arguments, the `get_pulls` head string, the state and merge_commit mapping, the comment sorting and UTC rule, the post flow, and the label filtering.
   - Criteria: each of the 23 is testable by one test function. Every rule has its failing side. A key line without the marker does not count (8, 10). An open or closed-unmerged pull request has no merge_commit (6). Errors are covered for all ten operations, in both the list and post paths of `post_comment` (16). Other exceptions and `InjectedKill` pass through (17). The constructor touches nothing (18). The source searches are in 19 and 20, the structural fit in 21. Kill-point behaviour is in 11, including the case where it is not reached.
   - Demo: both commands are runnable. The expected lines can be checked: the `GithubException` text for 404 and the single module path that imports `github`.
   - Architecture: the client sits in `factory.adapters`, behind the S0002 interface. It imports `HostingService`, DTOs and `HostingServiceError` from the domain and application layers, which is the allowed direction. PyGithub is confined to one module, as R9 requires.
   - Scope: the story is within the feature's scope (SI2.1, SI2.2). The wiring of the `Repository` and the token are left to F0002 and F0010, and the fake to S0014.
3. tester: wrote red tests for criteria 1–21. Criterion 22 is the factory's `make check`, and criterion 23 belongs to the docs stage.
   - criterion 1: tests/adapters/test_pygithub_hosting.py::test_create_pull_request_opens_against_main_and_returns_the_view (parametrized over draft True/False)
   - criterion 2: tests/adapters/test_pygithub_hosting.py::test_find_open_pull_request_filters_by_owner_and_branch
   - criterion 3: tests/adapters/test_pygithub_hosting.py::test_find_open_pull_request_is_none_without_a_result
   - criterion 4: tests/adapters/test_pygithub_hosting.py::test_get_pull_request_maps_the_pull_request_to_a_view
   - criterion 5: tests/adapters/test_pygithub_hosting.py::test_view_state_follows_merged_then_state
   - criterion 6: tests/adapters/test_pygithub_hosting.py::test_unmerged_pull_request_has_no_merge_commit_even_with_a_sha
   - criterion 7: tests/adapters/test_pygithub_hosting.py::test_list_comments_sorts_by_id_and_reads_naive_times_as_utc
   - criterion 8: tests/adapters/test_pygithub_hosting.py::test_list_comments_tells_factory_posts_by_marker_and_key
   - criterion 9: tests/adapters/test_pygithub_hosting.py::test_post_comment_posts_the_rendered_body_once
   - criterion 10: tests/adapters/test_pygithub_hosting.py::test_post_comment_skips_an_existing_key_but_not_a_quoted_one
   - criterion 11: tests/adapters/test_pygithub_hosting.py::test_kill_after_post_leaves_the_post_recognisable
   - criterion 12: tests/adapters/test_pygithub_hosting.py::test_close_and_reopen_edit_the_state
   - criterion 13: tests/adapters/test_pygithub_hosting.py::test_set_draft_converts_or_marks_ready
   - criterion 14: tests/adapters/test_pygithub_hosting.py::test_set_description_edits_the_body
   - criterion 15: tests/adapters/test_pygithub_hosting.py::test_set_labels_keeps_foreign_labels_and_replaces_stage_labels
   - criterion 16: tests/adapters/test_pygithub_hosting.py::test_every_failing_call_raises_hosting_service_error (13 failing stand-in calls × GithubException(500)/OSError). The table covers both the listing and posting paths of post_comment, both set_draft paths, and both get_labels and set_labels for set_labels.
   - criterion 17: tests/adapters/test_pygithub_hosting.py::test_other_errors_and_injected_kills_pass_through
   - criterion 18: tests/adapters/test_pygithub_hosting.py::test_constructor_touches_nothing_on_the_repository
   - criterion 19: tests/test_hosting_search.py::test_only_the_pygithub_client_imports_github and ::test_no_module_imports_another_route_to_the_hosting_service (parametrized over the forbidden modules)
   - criterion 20: tests/test_hosting_search.py::test_no_module_names_the_gh_tool
   - criterion 21: tests/adapters/test_pygithub_hosting.py::test_client_fits_the_interface_without_inheriting_it, together with the module-level `STRUCTURAL_FIT: HostingService = ...` in the same test module, which mypy checks

   Files created:
   - tests/adapters/__init__.py
   - tests/adapters/pygithub_stand_ins.py: plain recording stand-ins. Each has a `failures` map from method name to exception, and `create_issue_comment` appends the comment so that a repeated post sees it. `Untouchable` raises on any attribute access.
   - tests/adapters/test_pygithub_hosting.py
   - tests/source_search.py: an ast helper with `modules()`, `imported_modules()`, `imports()` and `string_literals()`.
   - tests/test_hosting_search.py

   What I chose: the `HostingService` assignment sits in the test module, not in the stand-ins module. Criterion 21 says "a test module", and that is where mypy checks the fit either way. The tests import the stand-ins as `adapters.pygithub_stand_ins` and the search helper as `source_search`, because `tests/` has no `__init__.py`.

   `make test` run once: collection stops at `ModuleNotFoundError: No module named 'factory.adapters.pygithub_hosting'`, the only module the runner could not import. Before the coder's work, test_only_the_pygithub_client_imports_github fails on an empty set. `make lint` is green after `ruff format` on my files. I skipped the type check, as this stage says.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: built `src/factory/adapters/pygithub_hosting.py` (commit a9600d5). `PyGithubHostingService` implements the ten `HostingService` operations on PyGithub's `Repository` without inheriting the protocol. The constructor only stores the repository and the kill points.
      - Main decision: there is one error boundary, a private context manager `_failing_as(operation)`. Each operation wraps its whole body in it, and it re-raises `GithubException` and `OSError` as `HostingServiceError(operation, str(error)) from error`. Because each operation's `get_pull` call is inside its own wrapper, a failure while `post_comment` lists comments is reported as `post_comment`. The `AFTER_POST` kill point is reached outside the wrapper, after a successful post. `InjectedKill` is a `BaseException` and is never caught anyway.
      - Alternative rejected: a decorator on each method. It would hide the operation name in the decorator argument, and mypy would need a `ParamSpec` dance. The `with` block reads more plainly.
      - Mapping: four private module functions do the translation. `_state` checks merged first, then open, then closed. `_view` sets `merge_commit` only when the pull request is merged. `_as_utc` treats a naive `created_at` as UTC. `_comments` sorts by id. `set_labels` keeps label names without `LABEL_PREFIX`, in their order, then adds the given ones. `MAIN_BRANCH` and `LABEL_PREFIX` come from `factory.domain.paths`.
      - `make check` is green, with 100 % coverage. Demo 1 prints `get_pull_request | 404 {"message": "Not Found"}`.
      - Refactor pass: I read the diff (one new module) and found nothing to rename, simplify or remove, so there is no refactor commit.
      - Noticed, not touched: nothing outside the ticket. Criterion 23 (docs) is the documenter's.

   `make check`: check: green
5. reviewer: no findings.
      - Scope: I reviewed `git diff main...HEAD -- . ':!factory'`. It contains `src/factory/adapters/pygithub_hosting.py`, the stand-ins, the client tests, `tests/source_search.py` and `tests/test_hosting_search.py`. The two `docs/runs/` files in the diff come from the human's own commit 4e81e15 (night log and report), not from a stage, so they are not under review.
      - 1. Acceptance criteria: each of criteria 1–21 has a test, and each test checks what its criterion names. Specific checks:
        - Criteria 5–6: merged-with-closed state and an unmerged pull request carrying a sha.
        - Criterion 7: the order of ids is shuffled, and both a naive and a +02:00 `created_at` are covered.
        - Criteria 8 and 10: a quoted key line without the marker does not count.
        - Criterion 11: kill point reached once, the repeat returns `already_posted`, and the unarmed path is covered.
        - Criterion 12: the pull request of the other number is untouched.
        - Criterion 16: a table of 13 failing calls × `GithubException(500)`/`OSError`, asserting `operation`, `detail` and `__cause__`. It covers both the listing and posting paths of `post_comment`.
        - Criterion 17: `ValueError` and `InjectedKill`.
        - Criterion 18: `Untouchable` raises on any attribute access.
        - Criteria 19–20: an ast search of imports and string literals. `git` is matched exactly or as a dotted prefix, so `github` does not trigger it.
        - Criterion 21: the module-level `STRUCTURAL_FIT: HostingService` plus an MRO check.
        - Every stated rule has its failing side tested; the Interface states no numeric limit. The coder's entry records `make check` green. Criterion 22 is the factory's; criterion 23 is the documenter's.
      - 2. Architecture: the client is in `factory.adapters` and imports only `factory.domain` and PyGithub. It satisfies `HostingService` structurally without inheriting it. PyGithub is confined to this one module (R9), no command-line tool is called, and no `dict[str, Any]` crosses a boundary.
      - 3. Security: no secrets (the test sha is `"a" * 40`), no strings built into commands, and no suppression markers. A raised error carries only the operation name and `str(error)`, chained to the original error.
      - 4. Quality: there is one error boundary (`_failing_as`). The `AFTER_POST` kill point is reached outside it, after a successful post, as the rule asks. The private mapping functions each do one thing. The module, class and public-method docstrings are present and say what each one is for. Comments explain why (test-merge sha, `OSError` as connection error).
      - 5. Ticket hygiene: the coder's entry names the main decision (a context manager as the single error boundary) and what was rejected (a decorator with `ParamSpec`). The Assignment matches what was built. Criterion 23 still describes what the reader must learn: the interface-only route, the one client and its one error, stand-ins now and a fake later, and why PyGithub (R9).
