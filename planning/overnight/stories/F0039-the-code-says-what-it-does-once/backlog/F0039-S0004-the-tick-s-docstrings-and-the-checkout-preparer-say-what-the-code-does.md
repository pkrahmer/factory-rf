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
