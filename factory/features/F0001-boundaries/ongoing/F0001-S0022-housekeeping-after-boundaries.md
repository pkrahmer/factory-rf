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
