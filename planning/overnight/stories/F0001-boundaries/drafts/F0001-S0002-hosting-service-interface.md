# The hosting-service interface and its DTOs

## Assignment (as of log entry 1)

Define everything the factory knows about the hosting service, with no implementation behind it: the pull request DTOs, the factory's marker, the post key that makes a repeated post a no-op, the one error type of every failing call, and the `HostingService` protocol with the operations R10 lists (create as draft or ready, read state and merge state, list comments with id and author, post with the marker, close, reopen) plus those that R22 (the description as the one projection of the work item) and kept thing 11 (draft or ready) need: find the open pull request of a branch, mark draft or ready, replace the description, write labels. The PyGithub client (S0003) and the one fake (S0014) implement it. Covers R10 (the interface), R6 (an interface in front of the tool), R7 (DTOs shaped by the factory, with a search that no `dict[str, Any]` crosses a function boundary) and R34 (the marker, not the author, tells the factory's posts apart); keeps kept thing 11 (posts carry the factory's marker). Because the hosting DTOs need a work item id, a commit id and two names that the interface sheet gives to later stories, this story creates the first part of three modules and the later stories add the rest: `factory.domain.identifiers` (only `WorkItemId`), `factory.domain.git` (only `CommitId`) and `factory.domain.paths` (only `MAIN_BRANCH` and `LABEL_PREFIX`).

## Interface

`src/factory/domain/errors.py` (adds to the module from S0001)

```python
class BoundaryError(FactoryError):
    """An outside party failed."""

class HostingServiceError(BoundaryError):
    operation: str
    detail: str
    def __init__(self, operation: str, detail: str) -> None: ...
```

`src/factory/domain/identifiers.py` (only this name; F0002 adds the rest)

```python
WorkItemId = Annotated[str, StringConstraints(pattern=r"^F\d{4}-[SA]\d{4}$")]
```

`src/factory/domain/git.py` (only this name; S0005 and later stories add the rest)

```python
CommitId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
```

`src/factory/domain/paths.py` (only these names; F0002 adds the rest)

```python
MAIN_BRANCH = "main"
LABEL_PREFIX = "stage:"
```

`src/factory/domain/hosting.py`

```python
FACTORY_MARKER = "<!-- factory -->"
PullRequestState = Literal["open", "closed", "merged"]
PostKind = Literal[
    "question", "attempts_cap", "round_cap", "crash_cap", "send_back",
    "stall", "expiry", "correction", "error", "cost_table",
]
PostOutcome = Literal["posted", "already_posted"]

class PullRequestView(BaseModel):
    number: PositiveInt
    branch: str
    title: str
    state: PullRequestState
    draft: bool
    merge_commit: CommitId | None = None
    url: str

class PostKey(BaseModel):
    work_item: WorkItemId
    kind: PostKind
    n: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]+$")]
    def comment(self) -> str: ...

class PullRequestComment(BaseModel):
    id: PositiveInt
    author: str
    body: str
    created_at: AwareDatetime
    by_factory: bool
    key: PostKey | None
    @classmethod
    def from_body(cls, *, id: int, author: str, body: str, created_at: datetime) -> "PullRequestComment": ...

def render_post(text: str, key: PostKey) -> str: ...
def parse_post_key(body: str) -> PostKey | None: ...
```

`src/factory/application/hosting.py`

```python
class HostingService(Protocol):
    def create_pull_request(self, branch: str, title: str, body: str, *, draft: bool) -> PullRequestView: ...
    def find_open_pull_request(self, branch: str) -> PullRequestView | None: ...
    def get_pull_request(self, number: int) -> PullRequestView: ...
    def list_comments(self, number: int) -> list[PullRequestComment]: ...
    def post_comment(self, number: int, text: str, key: PostKey) -> PostOutcome: ...
    def close(self, number: int) -> None: ...
    def reopen(self, number: int) -> None: ...
    def set_draft(self, number: int, draft: bool) -> None: ...
    def set_description(self, number: int, body: str) -> None: ...
    def set_labels(self, number: int, labels: Sequence[str]) -> None: ...
```

There are ten operations, and none of them returns labels: labels are written as a projection of the stage and never read back.

The rules, each with a criterion below:

- Every model in `factory.domain.hosting` is frozen and forbids unknown keys; datetimes are aware and converted to UTC.
- `merge_commit` is set exactly when `PullRequestView.state` is `"merged"`, and is a 40-character lowercase hexadecimal commit id.
- `PostKey.comment()` is `<!-- factory key=<work_item>:<kind>:<n> -->`, for example `<!-- factory key=F0001-S0001:question:7 -->`. `n` is lowercase hexadecimal and not empty.
- `render_post(text, key)` is `text` with its trailing whitespace removed, then a blank line, then `FACTORY_MARKER`, a newline and `key.comment()`; nothing follows the key.
- `parse_post_key(body)` reads only the last non-blank line of `body`; that line must be exactly a key comment (trailing whitespace, a trailing `
` included, ignored) whose work item, kind and `n` are valid, and blank lines after it do not matter; in every other case it returns `None`.
- `PullRequestComment.from_body` sets `by_factory` exactly when `body` contains `FACTORY_MARKER` (the author is never consulted: R34) and `key` to `parse_post_key(body)` when `by_factory`, else `None`.
- `HostingServiceError` is raised by every implementation for every failing call (SI2.2); its message is `hosting service <operation> failed: <detail>`.
- Both domain modules import only the standard library, Pydantic and `factory.domain`; `factory.application.hosting` imports only the domain.
- No function or method in `src/factory` has a parameter or return annotation that is a subscript of `dict`, `Mapping` or `MutableMapping` (also as `typing.Mapping` or `collections.abc.Mapping`) whose second argument is `Any`, however deeply nested (R7). The search does not follow a type alias; the factory writes none for these types.

Tests: `tests/domain/test_hosting.py`, `tests/domain/test_errors.py` (extended: it gains new tests only, no existing test is changed), `tests/application/test_hosting_protocol.py`, `tests/test_no_untyped_dicts.py`. A test that needs a commit id uses a low-entropy literal such as `"a" * 40`, so that `make secrets` stays green.

## Acceptance criteria

1. `HostingServiceError("post_comment", "403 forbidden")` carries `operation == "post_comment"` and `detail == "403 forbidden"`, its message is `hosting service post_comment failed: 403 forbidden`, and it is a subclass of `BoundaryError` and of `FactoryError`.
2. `MAIN_BRANCH` is `"main"`, `LABEL_PREFIX` is `"stage:"` and `FACTORY_MARKER` is `<!-- factory -->`.
3. `PostKey(work_item="F0001-S0001", kind="question", n="7").comment()` is `<!-- factory key=F0001-S0001:question:7 -->`.
4. `PostKey` accepts every one of the ten kinds, the work item ids `F0001-S0001` and `F0001-A0001`, and `n` values `"7"` and `"0a1f"`.
5. `PostKey` rejects the work item ids `F001-S0001` and `F0001-X0001`, the kind `"other"`, and the `n` values `""`, `"G1"` and `"ABC"`.
6. `render_post("Stage tests stalled.\n\n", key)` returns `Stage tests stalled.`, a blank line, `<!-- factory -->`, a newline and the key comment, with no newline at the end.
7. `parse_post_key(render_post(text, key)) == key` for every one of the ten kinds.
8. `parse_post_key` returns `None` for: an empty string; a body without a key line; a key line followed by another line of text; a key comment quoted inside a sentence; a key with the kind `other`; a key with the work item `F001-S0001`; a key with `n` `G` and a key with an empty `n`.
9. `parse_post_key` returns the key for a body whose key line is followed by two blank lines, for one whose key line ends in spaces, for one whose key line ends in `
` and for one with `

` line ends throughout.
10. `PullRequestComment.from_body` gives `by_factory` true and the parsed key for a body made by `render_post`; true and `None` for a body with the marker and no key; false and `None` for a body with a key line and no marker; false and `None` for a plain body; and an author of `"factory"` without the marker is not by the factory, while an author of `"someone"` with the marker is.
11. `PullRequestComment` rejects a naive `created_at` and an `id` of 0, accepts an id of 1, and converts a `created_at` with another offset to UTC.
12. `PullRequestView` accepts `state="merged"` with a 40-character lowercase hexadecimal `merge_commit`, and accepts `"open"` and `"closed"` without one; it rejects `"merged"` without a `merge_commit`, `"open"` with one, a `merge_commit` of 39 characters or with an uppercase letter, and a `number` of 0.
13. Every model of `factory.domain.hosting` (`PullRequestView`, `PostKey`, `PullRequestComment`) rejects an unknown keyword argument and rejects assignment to a field.
14. `HostingService` has exactly these ten public operations: `create_pull_request`, `find_open_pull_request`, `get_pull_request`, `list_comments`, `post_comment`, `close`, `reopen`, `set_draft`, `set_description` and `set_labels`; none of them returns labels, and there is no operation that reads them.
15. No function or method under `src/factory` has an annotation that is a subscript of `dict`, `Mapping` or `MutableMapping` (also as `typing.Mapping` or `collections.abc.Mapping`) with `Any` as its second argument, at any depth (a test parses every module with `ast`; the test itself is checked against a source snippet that has `MutableMapping[str, Any]` in a parameter and is found).
16. `factory.domain.hosting`, `factory.domain.identifiers`, `factory.domain.git` and `factory.domain.paths` import only the standard library, `pydantic` and `factory.domain` modules, and `factory.application.hosting` imports only `factory.domain` modules and the standard library.
17. make check stays green.
18. docs: `docs/project-guide.md` describes the hosting-service interface (the ten operations, the marker and the post key, the one error type) and says that the hosting service is reached only through it; `docs/decisions.md` records why a post carries a key and why the marker, not the author, tells the factory's posts apart (WE6.3).

## Demo

```bash
uv run python -c "
from datetime import UTC, datetime
from factory.domain.hosting import PostKey, PullRequestComment, parse_post_key, render_post
key = PostKey(work_item='F0001-S0003', kind='stall', n='12')
body = render_post('Stage tests stalled.', key)
print(repr(body))
print(parse_post_key(body) == key)
comment = PullRequestComment.from_body(id=7, author='someone', body=body, created_at=datetime(2026, 10, 12, tzinfo=UTC))
print(comment.by_factory, comment.key.kind)
"
```
Expect: three lines: `'Stage tests stalled.\n\n<!-- factory -->\n<!-- factory key=F0001-S0003:stall:12 -->'`, then `True`, then `True stall`.

```bash
uv run python -c "
from pydantic import ValidationError
from factory.domain.hosting import PullRequestView
try:
    PullRequestView(number=3, branch='work-item/F0001-S0001', title='t', state='merged', draft=False, url='https://example.invalid/pull/3')
except ValidationError as error:
    print('rejected', error.error_count())
"
```
Expect: one line, `rejected 1`: a merged pull request without a merge commit is refused.

## Log (append only)

1. 2026-10-12 human: created.
