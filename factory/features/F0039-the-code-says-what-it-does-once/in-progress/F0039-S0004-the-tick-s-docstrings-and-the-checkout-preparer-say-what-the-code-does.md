---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 383
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-21T01:43:24.055355Z'
  lease_duration: 60
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
