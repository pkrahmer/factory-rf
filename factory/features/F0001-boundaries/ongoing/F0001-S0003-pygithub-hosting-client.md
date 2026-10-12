---
stage: tests
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
