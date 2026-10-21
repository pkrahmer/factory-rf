---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 383
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T01:42:45.376072Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T01:42:45.381233Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T01:43:03.415905Z'
  stage: intake
  run: b0f2cf94fc2a4dab8905066f5ceed1cc
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T01:43:24.055355Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T01:46:08.827610Z'
  stage: tests
  run: e58a73fe6dc74e358a35072d238c3542
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T01:46:30.158942Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T01:49:25.362209Z'
  stage: doing
  run: 0eb458b5532141f8ab52d2f9410366d3
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T01:49:46.157604Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T01:50:12.509440Z'
  stage: review
  run: 563681a6b08043ae86276bdc6cf43c9e
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T01:50:32.988613Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-21T01:50:49.239900Z'
  stage: docs
  run: 9b795c0508e24060b30d28ea1bcae1af
---

# The tick's docstrings and the checkout preparer say what the code does

## Description

The class docstring of `Tick` says "nothing local is read", though every tick reads the agent files in the agent's home, the instance's health file through the stop service and its stop records through `StopPublisher`, and the rule it stands for (the decision log's *The checkout is disposable*) is about the checkout, not the state directory. `Tick.run`'s docstring lists its steps without the publication of the stop records, which the module docstring names. Agents read docstrings as the design: the first invites local state into the tick, the second the removal of the publication. `CheckoutPreparer.prepare` is typed `-> bool` and documented "always `True`", and its one caller, `RepositoryWaiter.prepare`, ignores the value. This story rewrites the two docstrings of `Tick` and makes `CheckoutPreparer.prepare` return `None`. The tester first turns the seven earlier tests that assert its `True` into calls as statements, under the human's leave (the feature's decision 6). Unchanged: what the tick does and in which order, what the preparer clones, seals and logs, and `RepositoryWaiter.prepare`, which stays `-> bool`.

## Interface

`src/factory/application/tick.py` (`application`): docstrings only.

- The class docstring of `Tick` becomes, its words wrapped as ruff allows: "One pass over the remote, the only truth of the work items; the checkout is disposable." then a blank line and "The tick status is kept from one run to the next. Beyond the remote, it reads only the agent files in the agent's home and the instance's state directory (the health file and the records), never what an earlier tick left in the checkout."
- The docstring of `Tick.run` becomes: "Check the disk, fetch, load, restore, publish the stop records, preflight, dispatch." then a blank line and "Before the dispatch, the stale branches are deleted and the remote is evaluated. A stop ends the tick." then a blank line and today's "Raises `WorkItemFormatError`, `ValueError` from the evaluation, and `GitError` outside the fetch and the restore: no stop exists for them."

`src/factory/application/scheduler.py` (`application`):

```python
class CheckoutPreparer:
    def prepare(self) -> None:
        """Clone unless the checkout holds a sealed clone, then seal the clone."""
```

- `prepare` returns nothing; what it clones, seals, removes and logs, and the `GitError` it raises, stay as they are.
- `RepositoryWaiter.prepare(self) -> bool` is unchanged and calls `self._preparer.prepare()` as a statement, as today.

Tests (the tester writes them):

- `tests/application/test_tick_docstrings.py` (new): criteria 1 and 2.
- Earlier tests changed under the feature's decision 6, each keeping its name and every other line, `assert <call>.prepare() is True` (or `prepared = <call>.prepare()` with `assert prepared is True`) becoming the call as a statement: `tests/application/test_nested_repositories.py::test_the_preparer_removes_the_nested_repositories_of_a_kept_checkout` and `::test_a_missing_checkout_is_cloned_without_a_search`; `tests/application/test_checkout_preparer_seal.py::test_a_missing_checkout_is_cloned_and_sealed`, `::test_a_sealed_checkout_is_kept_and_sealed_again_without_a_log_line` and `::test_a_checkout_whose_git_folder_fails_the_check_is_removed_and_cloned_again`; `tests/application/test_scheduler.py::test_a_missing_checkout_is_cloned_and_cloned_again_after_removal` and `::test_an_existing_clone_is_kept_without_calling_git`.

## Acceptance criteria

1. The docstrings, their whitespace joined to single spaces (`" ".join(inspect.getdoc(x).split())`), are exactly these (rows of one parametrized test): for `Tick`, `One pass over the remote, the only truth of the work items; the checkout is disposable. The tick status is kept from one run to the next. Beyond the remote, it reads only the agent files in the agent's home and the instance's state directory (the health file and the records), never what an earlier tick left in the checkout.`; for `Tick.run`, `Check the disk, fetch, load, restore, publish the stop records, preflight, dispatch. Before the dispatch, the stale branches are deleted and the remote is evaluated. A stop ends the tick. Raises `WorkItemFormatError`, `ValueError` from the evaluation, and `GitError` outside the fetch and the restore: no stop exists for them.`; for `CheckoutPreparer.prepare`, `Clone unless the checkout holds a sealed clone, then seal the clone.`
2. The return types (rows of one parametrized test, read with `typing.get_type_hints`): `CheckoutPreparer.prepare` returns `type(None)`; `RepositoryWaiter.prepare` returns `bool`.
3. The preparer does what it did: the seven tests the Interface names pass, changed only as it says, and `tests/application/test_repository_waiter.py` and the rest of `tests/application/test_checkout_preparer_seal.py`, `tests/application/test_nested_repositories.py` and `tests/application/test_scheduler.py` pass unchanged.
4. `make check` stays green.
5. docs: `docs/project-guide/watching.md`, *Boundaries* or wherever it describes `CheckoutPreparer(git, settings, log=None).prepare()`: "returns `True` and raises `GitError` as before" becomes "returns nothing and raises `GitError` as before". *The tick*, the sentence "the remote is the only truth, so nothing is read before the fetch": nothing of the remote is read before the fetch, and beyond the remote the tick reads only the agent files in the agent's home and the instance's state directory (the health file and the records), never what an earlier tick left in the checkout. `docs/decisions.md`, `README.md` and `docs/operator-guide.md`: none, no decision and nothing an operator does changes.

## Smoke test

```bash
uv run python -c 'import inspect, typing; from factory.application.scheduler import CheckoutPreparer, RepositoryWaiter; from factory.application.tick import Tick; print("nothing local" in inspect.getdoc(Tick), "publish the stop records" in inspect.getdoc(Tick.run), typing.get_type_hints(CheckoutPreparer.prepare)["return"], typing.get_type_hints(RepositoryWaiter.prepare)["return"])'
```
Expect: one line, `False True <class 'NoneType'> <class 'bool'>` (before the story, `True False <class 'bool'> <class 'bool'>`)

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: concrete. It names `src/factory/application/tick.py` (docstrings of `Tick` and `Tick.run`) and `src/factory/application/scheduler.py` (`CheckoutPreparer.prepare(self) -> None`, with its docstring). The words match the code I read: `Tick` says "nothing local is read", `prepare` is `-> bool` with "always `True`", and `RepositoryWaiter.prepare` stays `-> bool`. The seven earlier tests are named by module and function, with the human's leave in the feature's decision 6.
   Criteria: each can be tested by one function. Criterion 1 is the three docstrings, compared exactly after joining whitespace, as rows of one parametrized test. Criterion 2 is the two return types, read with `get_type_hints`. Criterion 3 is that the unchanged tests still pass. Criterion 4 is `make check`; criterion 5 is `docs:`. The story has no rule with a failing side. Every behaviour in the Interface has a criterion, including the unchanged `RepositoryWaiter.prepare -> bool`.
   Smoke test: the one-line `python -c` command is runnable and uses no pytest. Its `Expect:` line gives the exact output, `False True <class 'NoneType'> <class 'bool'>`, with the pre-story output as a contrast.
   Architecture: the change is inside `factory.application`, with no new import, layer or dependency. It changes docstrings and one return type. Nothing is added to `Boundaries`.
   Scope: it stays within the feature's S0004 line. The `Tick` and `Tick.run` docstrings, `CheckoutPreparer.prepare -> None` and the seven tests all appear in the feature's Scope and decision 6. None of the feature's Out of scope items is touched.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 and 2. Changed the seven earlier tests the Interface names, under the human's leave in the feature's decision 6.

   Mapping:
   - criterion 1: tests/application/test_tick_docstrings.py::test_the_docstrings_say_what_the_code_does (rows `tick`, `tick-run`, `checkout-preparer-prepare`)
   - criterion 2: tests/application/test_tick_docstrings.py::test_the_preparers_return_types (rows `checkout-preparer`, `repository-waiter`)
   - criterion 3: the seven changed tests, plus the unchanged rest of tests/application/test_repository_waiter.py, test_checkout_preparer_seal.py, test_nested_repositories.py and test_scheduler.py
   - criterion 4: `make check` (the coder's)
   - criterion 5: docs, not tested

   Created: tests/application/test_tick_docstrings.py.

   Earlier test files changed (feature decision 6). Each test keeps its name. In each, `assert <call>.prepare() is True`, or `prepared = <call>.prepare()` with `assert prepared is True`, became the call as a statement:
   - tests/application/test_nested_repositories.py: test_the_preparer_removes_the_nested_repositories_of_a_kept_checkout, test_a_missing_checkout_is_cloned_without_a_search
   - tests/application/test_checkout_preparer_seal.py: test_a_missing_checkout_is_cloned_and_sealed, test_a_sealed_checkout_is_kept_and_sealed_again_without_a_log_line, test_a_checkout_whose_git_folder_fails_the_check_is_removed_and_cloned_again
   - tests/application/test_scheduler.py: test_a_missing_checkout_is_cloned_and_cloned_again_after_removal (two calls), test_an_existing_clone_is_kept_without_calling_git

   test_a_waiter_that_hits_a_git_error… in the seal module still asserts `prepared is False` on `RepositoryWaiter.prepare`, which stays `-> bool`. I left it unchanged.

   `make test`: 4 failures, all for the right reason. The three docstrings still hold today's words ("nothing local is read", no stop records, "always `True`"), and `CheckoutPreparer.prepare` returns `bool`. The `repository-waiter` row passes because that method does not change. Every module imported, so nothing was unimportable. `make lint`: green. Type check skipped, as the stage says.

   `lint`: lint: green (0.5 s)
   `test`: FAILED tests/application/test_tick_docstrings.py::test_the_preparers_return_types[checkout-preparer] - AssertionError: assert <class 'bool'> is <class 'NoneType'>
6. factory: started doing as self.
7. coder: Rewrote the two `Tick` docstrings and made `CheckoutPreparer.prepare` return `None`. `make check` is green and the smoke test prints `False True <class 'NoneType'> <class 'bool'>`.

   Built:
   - `src/factory/application/tick.py`: the class docstring of `Tick` and the docstring of `Tick.run` now use the Interface's words, wrapped to the line length. The `Raises` paragraph of `run` is unchanged. No code changed.
   - `src/factory/application/scheduler.py`: `CheckoutPreparer.prepare(self) -> None` has the new docstring, and its closing `return True` is removed. What it clones, seals, removes and logs is unchanged. `RepositoryWaiter.prepare` is untouched: it stays `-> bool` and still calls the preparer as a statement.

   Main choice: I removed the `return True` and left the method to end after `self._git.seal()`. I rejected adding an explicit `return None`, because it adds nothing in a `-> None` method and the module never does it elsewhere.

   Refactor pass: I read the diff (two docstrings, one signature, one line removed) and found nothing to change.

   The journal did not change the task's meaning, so `## Description` is unchanged.

   Noticed, not touched:
   - `docs/project-guide/watching.md:274` still says `prepare()` "returns `True`". The tick section there still has the old "nothing is read before the fetch" wording. Both belong to the documenter, as criterion 5 says.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   Reviewed `git diff main...HEAD -- . ':!factory'` against the work item.
   - Criterion 1: the Interface's words are now the docstrings of `Tick` and `Tick.run` (`src/factory/application/tick.py`) and of `CheckoutPreparer.prepare` (`src/factory/application/scheduler.py`). `tests/application/test_tick_docstrings.py::test_the_docstrings_say_what_the_code_does` compares all three exactly after joining whitespace, as rows of one parametrized test. I checked the new `Tick.run` docstring against the body: check disk, fetch, load, restore, `_publish_stop_records`, preflight, then `delete_stale_branches`, `evaluate`, dispatch. It says what the code does.
   - Criterion 2: `CheckoutPreparer.prepare` is `-> None` and its `return True` is gone. `RepositoryWaiter.prepare` is untouched and still calls `self._preparer.prepare()` as a statement (`scheduler.py:130`, the only caller under `src/`). `test_the_preparers_return_types` reads both return types with `get_type_hints`, as two rows.
   - Criterion 3: each of the seven earlier tests changed only from `assert ...prepare() is True` (or `prepared = ...` with `assert prepared is True`) to the call as a statement. Every other line stays. `RepositoryWaiter`'s `prepared is False` assertion in the seal module stays as it was.
   - Criterion 4: the coder's journal entry 7 records `check: green` and `duplicates: 0 new`.
   - Architecture, security, quality: the change stays inside `factory.application`, with no new import and no silencing marker. No dead code is left behind.
   - Hygiene: the journal names the main choice (drop `return True` rather than write `return None`) and what was rejected. The Description matches what was built. Criterion 5 still names what the documenter must change in `docs/project-guide/watching.md`.

   Earlier tests:
   - tests/application/test_checkout_preparer_seal.py: the human's leave, feature decision 6 (named in the story's Interface)
   - tests/application/test_nested_repositories.py: the human's leave, feature decision 6 (named in the story's Interface)
   - tests/application/test_scheduler.py: the human's leave, feature decision 6 (named in the story's Interface)
10. factory: started docs as self.
11. documenter: Docs: two sentences corrected in one file, as criterion 5 asks. No findings. Only documents changed, so I did not run `make check`; the factory's checks follow.

    Changed:
    - `docs/project-guide/watching.md`, *The tick* (line 74): "nothing is read before the fetch" now says nothing of the remote is read before the fetch. Beyond the remote the tick reads only the agent files in the agent's home and the instance's state directory (the health file and the records), never what an earlier tick left in the checkout. This matches the new `Tick` docstring.
    - `docs/project-guide/watching.md` (line 274): `CheckoutPreparer.prepare()` "returns `True` and raises `GitError` as before" now reads "returns nothing and raises `GitError` as before".

    Cross-read against the diff and found current: the rest of `watching.md` (the tick order, which lists publishing the stop records, and the preparer's clone, seal and log behaviour), `README.md`, `docs/operator-guide.md` and `docs/decisions.md`. A grep of `docs/` and `README.md` for other mentions of `prepare()`'s return value, "nothing local" and "always True" found none. The code matches the Interface: `prepare` is `-> None` and `RepositoryWaiter.prepare` stays `-> bool`.

    Stale text noticed, not touched: none.

    `check`: check: green (not run again: passed on tree 85bb13c714fd at 2026-10-21T01:48:14Z)
    `secrets`: secrets: green (0.8 s)
    `documents`: documents ok
