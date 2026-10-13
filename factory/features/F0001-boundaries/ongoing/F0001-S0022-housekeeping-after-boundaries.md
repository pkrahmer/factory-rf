---
stage: docs
pr: 26
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Housekeeping after Boundaries: one frozen model, one check, honest test names and documents

## Assignment (as of log entry 1)

F0001's fourth acceptance carried small items that no later story fixed, and the human chose to fix them in one story (questionnaire 1, Q27, 2026-10-13). None of them changes what the boundaries do:

1. `RemoteBranch` is the only result model in `factory.domain.git` that is neither frozen nor closed to unknown fields.
2. `tests/application/test_git_protocol.py` and `tests/application/test_hosting_protocol.py` still say "protocol", although the interfaces are abstract base classes since S0019.
3. `GitCli` checks some arguments more than once within one call. `merge` checks its `ref` directly, again through `_resolve_or_raise` (which calls the public `resolve`) and again through its own `is_ancestor` calls, which also check `"HEAD"`; a merge that conflicts also checks `MERGE_HEAD` through `resolve`. `reset_to` checks its `ref` twice the same way. `revert_paths` checks its commit twice the same way and the resolved commit once more for each path through `show_file`. `delete_branch` checks its branch and then `refs/heads/<branch>` through `resolve`.
4. No test gives `check_branch_name` a control character between 0x10 and 0x1f, so narrowing its bound from 0x20 to 0x10 survives the tests (the acceptance's one surviving mutant).
5. Four places in the documents are stale or dense:
   - the operator guide cites the planning tag "(WE6.3)";
   - the project guide's intro still says "until then `CLAUDE.md` holds the rules";
   - the README calls the project guide "(partly written)";
   - one entry of `docs/decisions.md` holds decisions 22 and 23 in one paragraph.

The human allows this story to change tests other stories wrote: the renames of item 2 and the two import lines of `tests/application/test_interfaces.py` that name the renamed modules, and the new rows of item 4 in `tests/domain/test_git.py` (questionnaire 1, Q27). FEATURE.md decision 16's "fourteen" stays as a historic statement.

Covers R4 (the checks stay green), R7 (frozen DTOs) and R9; keeps the documents true (WE6.3).

## Interface

`src/factory/domain/git.py`:

```python
class RemoteBranch(BaseModel):
    """A branch as the remote holds it: its name without the remote's prefix, and its commit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    commit: CommitId
```

`src/factory/adapters/git_cli.py`:

- Every public `GitCli` operation calls `check_git_argument` (or `check_branch_name`) once for each argument it checks, as its first statements, and never again within the call. Resolution, ancestry and file reads inside an operation go through private helpers that run `git rev-parse`, `git merge-base --is-ancestor` and `git ls-tree` without checking: `_resolve_or_raise`, `delete_branch` and `merge`'s conflict check of `MERGE_HEAD` stop calling the public `resolve`, `merge` stops calling the public `is_ancestor`, and `revert_paths` stops calling the public `show_file`. The public `resolve`, `is_ancestor` and `show_file` still check their arguments first. No operation's outcome changes.

Tests:

- The tester renames the two test modules, their content unchanged: `tests/application/test_git_protocol.py` becomes `tests/application/test_git_interface.py`, and `tests/application/test_hosting_protocol.py` becomes `tests/application/test_hosting_interface.py`. `tests/application/test_interfaces.py` then imports `OPERATIONS` from `application.test_git_interface` and `application.test_hosting_interface`; nothing else in it changes.
- `tests/domain/test_git.py` gets the new refused values for `check_branch_name`.
- `tests/domain/test_git.py` also gets the tests of `RemoteBranch`.
- `tests/adapters/test_git_cli_arguments.py` gets the test of the single checks.
- `tests/test_test_names.py` (new, at the `tests/` root) gets the name search.

## Acceptance criteria

1. Assigning to `name` of a `RemoteBranch` raises `ValidationError`.
2. Constructing a `RemoteBranch` with an unknown field raises `ValidationError` (through a variable typed `type[BaseModel]`, as `CLAUDE.md` says).
3. `RemoteBranch(name="main", commit="a" * 40)` still constructs, and two equal instances compare equal.
4. With `factory.adapters.git_cli.check_git_argument` wrapped by pytest's `monkeypatch` to count its calls, each of these calls on the `checkout` fixture (a fresh clone) calls it exactly once (a parametrized test): `merge("origin/main")`, which returns `"up_to_date"`; `reset_to("origin/main")`; `revert_paths("HEAD", ["a.txt", "b.txt"])`; `delete_branch("gone")`.
5. With `check_git_argument` wrapped the same way, `merge("origin/main")` after the checkout and the remote changed the same file differently calls it exactly once and returns `"conflict"`.
6. `checkout.resolve("-x")`, `checkout.show_file("-x", "README.md")`, `checkout.is_ancestor("-x", "HEAD")` and `checkout.is_ancestor("HEAD", "-x")` still raise `ValueError` (a parametrized test).
7. `check_branch_name` raises `ValueError` for `"a\x10b"` and `"a\x1fb"`; `"a b"` (0x20) is still refused as a space, and `"a!b"` (0x21) is accepted.
8. No module under `tests/` has `protocol` in its file name, and `tests/application/test_git_interface.py` and `tests/application/test_hosting_interface.py` exist (a search test in `tests/test_test_names.py`).
9. `make check` stays green.
10. docs:
   - `docs/operator-guide.md` drops "(WE6.3)" and keeps the sentence's meaning.
   - The intro of `docs/project-guide.md` no longer says "until then `CLAUDE.md` holds the rules"; it says the guide grows with each story and that `CLAUDE.md` holds the rules every change follows.
   - `README.md`'s link to the project guide drops "(partly written)".
   - The project guide's sentence on the frozen result models of `factory.domain.git` names `RemoteBranch` too.
   - `docs/decisions.md` splits the entry "A pushed branch is never read as a refspec" into two entries: decision 22's refusal of `+`, `:` and `*`, and decision 23's branch-name rules with `refs/heads/<branch>`. Each keeps its date, its reasons and its rejected alternatives.
   - The project guide's sentences that name `test_git_protocol.py` or `test_hosting_protocol.py` use the new names.

## Demo

```bash
uv run python -c "
from pydantic import ValidationError
from factory.domain.git import RemoteBranch, check_branch_name
b = RemoteBranch(name='main', commit='a' * 40)
try:
    b.name = 'x'
except ValidationError:
    print('frozen')
for v in ('a\x10b', 'a\x1fb'):
    try:
        check_branch_name(v)
    except ValueError:
        print('refused', hex(ord(v[1])))
"
ls tests/application
```
Expect: three lines `frozen`, `refused 0x10`, `refused 0x1f`, then a listing that holds `test_git_interface.py` and `test_hosting_interface.py` and no file name with `protocol`.

## Log (append only)

1. 2026-10-13 human: created.
2. intake: accepted
   - Interface: `RemoteBranch` is given with `frozen=True, extra="forbid"` and its fields. The `GitCli` paragraph names the operations, the helpers to introduce (`_resolve_or_raise`, `delete_branch`, `merge`'s MERGE_HEAD check, `revert_paths`) and the public methods that keep their checks. The test file moves and the import lines are named.
   - Criteria: each one fits a single test function. Criteria 1 to 3 cover `RemoteBranch`: frozen, closed to unknown fields, and still constructible and comparable. Criteria 4 and 5 count the checks, parametrized and with the conflict case apart. Criterion 6 keeps the public checks. Criterion 7 covers both sides of the 0x10 boundary: 0x10 and 0x1f are refused, 0x20 is refused as a space, and 0x21 is accepted. Criterion 8 is a file-name search. Criteria 9 and 10 close the list in the required order. Every rule has its failing side tested (criteria 6 and 7).
   - Demo: the commands run. The `\x10` and `\x1f` escapes reach Python intact through bash double quotes, and Python reads them as control characters. The Expect line names three exact output lines and the listing, so the output can be checked against it.
   - Architecture: the changes sit in `domain.git`, `adapters.git_cli` and the tests, so the layering is kept. The count tests wrap `check_git_argument` through `monkeypatch`, with no mock of the code under test. The `RemoteBranch` test follows the `type[BaseModel]` rule.
   - Scope: this is the fourth acceptance's housekeeping, which the human chose in Q27 and recorded as decision 24 in FEATURE.md. The test changes beyond this story's own are limited to those the human allowed. No new dependency, no marker, and no change to `factory/`.
3. tester: Wrote the tests for criteria 1–8, renamed the two test modules and changed the import lines in `test_interfaces.py`.

   Mapping:
   - criterion 1: tests/domain/test_git.py::test_remote_branch_refuses_assignment (assigns through `setattr`, like the existing frozen-model tests, so mypy stays clean)
   - criterion 2: tests/domain/test_git.py::test_remote_branch_refuses_an_unknown_field (constructs through a variable typed `type[BaseModel]`)
   - criterion 3: tests/domain/test_git.py::test_remote_branch_constructs_and_equal_instances_compare_equal
   - criterion 4: tests/adapters/test_git_cli_arguments.py::test_operation_checks_its_argument_once (parametrized: merge returns "up_to_date"; reset_to, revert_paths and delete_branch return None). The helper `_count_checks` wraps `factory.adapters.git_cli.check_git_argument` through monkeypatch and still calls the real check.
   - criterion 5: tests/adapters/test_git_cli_arguments.py::test_conflicting_merge_checks_its_argument_once. The human pushes `shared.txt` to main, the checkout commits a different `shared.txt` and fetches. Counting starts only after that, so the setup's own checks are not counted.
   - criterion 6: tests/adapters/test_git_cli_arguments.py::test_public_reading_operations_still_refuse_an_option_like_ref (parametrized, on the `checkout` fixture)
   - criterion 7: new rows in tests/domain/test_git.py. `"a\x10b"`, `"a\x1fb"` and `"a b"` were added to test_branch_name_that_git_would_not_take_as_a_branch_is_refused, and `"a!b"` to test_branch_name_that_git_takes_as_a_branch_is_accepted. The ticket asked for these as rows, so there is no new function.
   - criterion 8: tests/test_test_names.py::test_no_test_module_is_named_after_a_protocol

   Files:
   - created: tests/test_test_names.py
   - renamed (content unchanged): tests/application/test_git_protocol.py → test_git_interface.py, tests/application/test_hosting_protocol.py → test_hosting_interface.py
   - changed: tests/application/test_interfaces.py (the two import lines only), tests/domain/test_git.py, tests/adapters/test_git_cli_arguments.py

   `make test` is red, with no import or collection errors. Each module under test imports; the tests fail on wrong results. The RemoteBranch tests fail because the model is not frozen and accepts unknown fields. The check-count tests fail because GitCli checks its arguments more than once. The new criterion 7 rows and the criterion 6 and 8 tests already pass: they guard behaviour that exists. `make lint` is green. I skipped the type check, as the stage says.

   `make lint`: lint: green
   `make test`: FAILED tests/domain/test_git.py::test_remote_branch_refuses_an_unknown_field
4. coder: Implemented the code side of the housekeeping. `make check` is green (commit "fix(git): freeze RemoteBranch and check each GitCli argument once").

   - `src/factory/domain/git.py`: `RemoteBranch` now has `model_config = ConfigDict(frozen=True, extra="forbid")` (criteria 1–3).
   - `src/factory/adapters/git_cli.py`: added three private helpers that run git without checking the arguments, because their public callers have already checked them:
     - `_resolve_unchecked` runs `rev-parse --verify`.
     - `_is_ancestor_unchecked` runs `merge-base --is-ancestor`.
     - `_blob` runs `ls-tree` and finds the blob.
   - The public `resolve`, `is_ancestor` and `show_file` keep their checks and now delegate to these helpers (criterion 6).
   - These callers now use the helpers instead of the public methods: `_resolve_or_raise`, `delete_branch`, the `MERGE_HEAD` check in `_merge_diverged`, `merge`'s two ancestry tests and `revert_paths`'s per-path read. Each operation now checks each argument once, as its first statements (criteria 4 and 5). No outcome changes.
   - Criterion 7's rows and criterion 8 already passed against the existing code.

   Decision: the counting test reads `git_cli.check_git_argument`, and mypy's no-implicit-reexport refused that attribute. I added `__all__ = ["GitCli", "check_git_argument"]` to `git_cli.py`, with a one-line comment saying why.
   - Rejected: `check_git_argument as check_git_argument`, because ruff PLC0414 refuses it.
   - Rejected: a `noqa`, because no marker is allowed outside `process.py`.
   - Rejected: changing the test (R9).

   The reviewer may want to judge whether exporting the check through `__all__` is acceptable. It is the first `__all__` in `src/factory`.

   Refactor: I read the diff and found nothing to change, so there is no refactor commit.

   Not done here: criterion 10's documents (the operator guide's "(WE6.3)", the project guide's intro and the RemoteBranch and test-file names in it, the README's "(partly written)", and the split of decisions 22 and 23 in `docs/decisions.md`). `CLAUDE.md` gives these to the documenter stage. I did not write them.

   `make check`: check: green
5. reviewer: no findings.

   What I checked:
   - Acceptance criteria:
     - Criteria 1–3 are covered by `tests/domain/test_git.py`. The unknown-field test goes through `type[BaseModel]`.
     - Criteria 4 and 5 are covered by `tests/adapters/test_git_cli_arguments.py`. The wrapper still calls the real check, and counting starts only after the setup.
     - Criterion 6 is covered in the same file: both arguments of `is_ancestor` are refused.
     - Criterion 7: the rows 0x10, 0x1f and 0x20 are refused and the row 0x21 is accepted, so both sides of the boundary are tested.
     - Criterion 8: `tests/test_test_names.py` covers it.
     - The coder's entry reports `make check` green.
   - Code: in `src/factory/adapters/git_cli.py` no public `GitCli` method calls another public method any more.
     - `merge`, `reset_to`, `revert_paths` and `delete_branch` each check their argument once, as their first statement, then use `_resolve_unchecked`, `_is_ancestor_unchecked` and `_blob`.
     - `_merge_diverged` checks `MERGE_HEAD` through `_resolve_unchecked`.
     - The public `resolve`, `show_file` and `is_ancestor` keep their checks.
     - Each operation returns the same results as before.
   - Architecture: the layers are unchanged and no new tool call or marker was added. `RemoteBranch` is frozen and closed to unknown fields, like the other result models.
   - The coder's `__all__ = ["GitCli", "check_git_argument"]`: I accept it. Criterion 4 wraps the check by the name `factory.adapters.git_cli.check_git_argument`, and mypy's no-implicit-reexport refuses that name otherwise. The other two options would have needed a `noqa` marker, which is not allowed, or a test change, which R9 forbids. No other test imports anything except `GitCli` from the module, and the comment beside it gives the reason.
   - Ticket: the Assignment matches what was built, and the log explains the `__all__` decision and the options rejected. Criterion 10 (the docs criterion) still lists everything the documenter has to write: "(WE6.3)", the project guide's intro, the `RemoteBranch` mention, the README, the split of decisions 22 and 23, and the renamed test modules.
