"""Tests for the words of the tick's docstrings and the checkout preparer's return type."""

import inspect
import typing

import pytest

from factory.application.scheduler import CheckoutPreparer, RepositoryWaiter
from factory.application.tick import Tick

TICK = (
    "One pass over the remote, the only truth of the work items; the checkout is disposable."
    " The tick status is kept from one run to the next. Beyond the remote, it reads only the"
    " agent files in the agent's home and the instance's state directory (the health file and"
    " the records), never what an earlier tick left in the checkout."
)
TICK_RUN = (
    "Check the disk, fetch, load, restore, publish the stop records, preflight, dispatch."
    " Before the dispatch, the stale branches are deleted and the remote is evaluated. A stop"
    " ends the tick. Raises `WorkItemFormatError`, `ValueError` from the evaluation, and"
    " `GitError` outside the fetch and the restore: no stop exists for them."
)
PREPARE = "Clone when the checkout holds no `.git`; keep any checkout that does."


@pytest.mark.parametrize(
    ("documented", "words"),
    [
        pytest.param(Tick, TICK, id="tick"),
        pytest.param(Tick.run, TICK_RUN, id="tick-run"),
        pytest.param(CheckoutPreparer.prepare, PREPARE, id="checkout-preparer-prepare"),
    ],
)
def test_the_docstrings_say_what_the_code_does(documented: object, words: str) -> None:
    docstring = inspect.getdoc(documented)

    assert docstring is not None
    assert " ".join(docstring.split()) == words


@pytest.mark.parametrize(
    ("method", "returned"),
    [
        pytest.param(CheckoutPreparer.prepare, type(None), id="checkout-preparer"),
        pytest.param(RepositoryWaiter.prepare, bool, id="repository-waiter"),
    ],
)
def test_the_preparers_return_types(method: object, returned: type) -> None:
    assert typing.get_type_hints(method)["return"] is returned
