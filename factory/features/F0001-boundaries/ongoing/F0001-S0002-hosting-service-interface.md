---
stage: review
pr: 2
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
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
- `parse_post_key(body)` reads only the last non-blank line of `body`; that line must be exactly a key comment (trailing whitespace, a trailing `\r` included, ignored) whose work item, kind and `n` are valid, and blank lines after it do not matter; in every other case it returns `None`.
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
9. `parse_post_key` returns the key for a body whose key line is followed by two blank lines, for one whose key line ends in spaces, for one whose key line ends in `\r`, and for one with `\r\n` line ends throughout.
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
2. intake: accepted
   - Interface: names concrete modules and signatures (errors, identifiers, git, paths, domain.hosting, application.hosting); the partial modules and the names later stories add are stated, and the ten operations are listed.
   - Criteria: each is testable by a test function without further decisions. Every stated rule has its failing side: PostKey rejections (5), parse_post_key None cases (8), the naive datetime, id 0 and UTC conversion (11), merge_commit missing, present on a non-merged state, wrong length or case, and number 0 (12), unknown keywords and assignment (13). The behaviours in the Interface comments (render_post format, last-non-blank-line parsing, by_factory from the marker only, the error message) are each covered by criteria 1, 3, 6 to 10.
   - Demo: both commands are runnable; the Expect lines give exact output (the three lines, and `rejected 1`).
   - Architecture: the domain DTOs and the protocol in application sit in the right layers, application imports only the domain, and criterion 16 enforces the imports. The hosting service stays behind an interface (R6, R10).
   - Scope: within F0001's scope (the interface, DTOs, marker and post key). Idempotent posting and the fake are left to S0014 and F0003/F0007, as the feature says.
3. tester: Wrote red tests for criteria 1–16. Criteria 17 and 18 are the factory's check and the documenter's work, so they get no test.

   - criterion 1: tests/domain/test_errors.py::test_hosting_service_error_carries_operation_detail_and_message
   - criterion 2: tests/domain/test_hosting.py::test_constants_have_their_values
   - criterion 3: tests/domain/test_hosting.py::test_post_key_comment_names_work_item_kind_and_n
   - criterion 4: tests/domain/test_hosting.py::test_post_key_accepts_valid_values (parametrized: the ten kinds, F0001-A0001, n "0a1f"), plus test_post_kind_lists_exactly_the_ten_kinds
   - criterion 5: tests/domain/test_hosting.py::test_post_key_rejects_invalid_values
   - criterion 6: tests/domain/test_hosting.py::test_render_post_strips_trailing_whitespace_and_ends_with_the_key
   - criterion 7: tests/domain/test_hosting.py::test_parse_post_key_reads_back_a_rendered_post (one case per kind)
   - criterion 8: tests/domain/test_hosting.py::test_parse_post_key_returns_none_without_a_valid_last_key_line (eight cases)
   - criterion 9: tests/domain/test_hosting.py::test_parse_post_key_tolerates_trailing_whitespace_and_crlf (four cases)
   - criterion 10: tests/domain/test_hosting.py::test_comment_is_by_factory_exactly_when_it_carries_the_marker
   - criterion 11: tests/domain/test_hosting.py::test_comment_rejects_a_naive_created_at, ::test_comment_id_must_be_positive (0 rejected, 1 accepted), ::test_comment_converts_created_at_to_utc
   - criterion 12: tests/domain/test_hosting.py::test_pull_request_view_accepts_consistent_states, ::test_pull_request_view_rejects_inconsistent_values
   - criterion 13: tests/domain/test_hosting.py::test_models_forbid_unknown_keys_and_are_frozen (one case per model)
   - criterion 14: tests/application/test_hosting_protocol.py::test_hosting_service_has_exactly_the_ten_operations, ::test_no_operation_returns_or_reads_labels. The second test compares each operation's return hint with the one in the Interface. It also checks that `set_labels` is the only operation with "label" in its name and that `PullRequestView` has no label field.
   - criterion 15: tests/test_no_untyped_dicts.py::test_the_search_finds_a_mutable_mapping_to_any (the `MutableMapping[str, Any]` snippet), ::test_the_search_finds_nested_and_qualified_mappings_to_any, ::test_no_function_in_the_package_has_a_mapping_to_any. The search uses `ast` and also reads string annotations. It follows no type alias, as the Interface says.
   - criterion 16: tests/domain/test_hosting.py::test_domain_modules_import_only_stdlib_pydantic_and_domain (the four modules), ::test_application_hosting_imports_only_stdlib_and_domain. Both parse the source with `ast` and resolve relative imports. "Standard library" means `sys.stdlib_module_names`.

   Files created: tests/domain/test_hosting.py, tests/application/__init__.py, tests/application/test_hosting_protocol.py, tests/test_no_untyped_dicts.py. Extended: tests/domain/test_errors.py gains one new test. Its import line now also names `BoundaryError` and `HostingServiceError`, and the existing test is unchanged; until those names exist, the whole module fails at collection.

   `make test` (one run) fails at collection as intended: `ModuleNotFoundError: No module named 'factory.domain.hosting'` for tests/domain/test_hosting.py and tests/application/test_hosting_protocol.py. The coder must also create `factory.domain.identifiers`, `factory.domain.git`, `factory.domain.paths` and `factory.application.hosting`, and add `BoundaryError` and `HostingServiceError` to `factory.domain.errors`.

   Outside the stage's procedure, I ran tests/test_no_untyped_dicts.py once on its own to check that the search logic works. It passes on the current tree because there are no offenders yet. `make lint` is green.

   I made no interpretation that needs the human. Commit ids in tests use `"a" * 40`.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: implemented the hosting-service interface and its DTOs. All tests from the tester pass, `make check` is green (coverage 100 %) and both demos print exactly what the ticket expects. Commit: `ticket F0001-S0002: feat(domain): hosting-service DTOs, post key and HostingService protocol`.

   Built:
   - src/factory/domain/errors.py: adds `BoundaryError(FactoryError)` and `HostingServiceError(BoundaryError)`. The second carries `operation` and `detail`, and its message is `hosting service <operation> failed: <detail>`.
   - src/factory/domain/identifiers.py (only `WorkItemId`), src/factory/domain/git.py (only `CommitId`), src/factory/domain/paths.py (only `MAIN_BRANCH` and `LABEL_PREFIX`). Each is the first part of a module that later stories extend.
   - src/factory/domain/hosting.py: `FACTORY_MARKER`, `PullRequestState`, `PostKind`, `PostOutcome`, and the models `PullRequestView`, `PostKey` and `PullRequestComment`.
     - The three models share a private `_Frozen` base: frozen, with `extra="forbid"`.
     - A model validator on `PullRequestView` requires `merge_commit` exactly when the state is `"merged"`.
     - A field validator converts `created_at` to UTC after `AwareDatetime` has rejected naive values.
     - `render_post` and `parse_post_key` are module functions. `PullRequestComment.from_body` takes `by_factory` from the marker alone and never looks at the author.
   - src/factory/application/hosting.py: the `HostingService` Protocol with its ten operations. Each has a one-line docstring and `...` as its body. No operation reads labels.

   Main design decision: `parse_post_key` matches the last non-blank line, with trailing whitespace stripped, against a loose regex for the comment's shape, `<!-- factory key=A:B:C -->`. It then hands the three parts to `PostKey.model_validate` and returns `None` on a `ValidationError`. That way the rules for a valid work item, kind and `n` live only in `PostKey`. The alternative I rejected was one strict regex that repeats the work-item pattern, the kind alternation and the hex rule, which would duplicate the model's rules.

   Refactor: I read the diff as a reviewer would and found nothing to change, so there is no refactor commit.

   Not touched: the docs for criterion 18 belong to the documenter. The PyGithub client (S0003) and the fake (S0014) implement this protocol later.

   `make check`: check: green
