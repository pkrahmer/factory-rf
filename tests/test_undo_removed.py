"""The undo's module is gone; the take holds the functions they shared."""

import importlib.util
from collections.abc import Callable

import pytest

from module_names import has_name
from source_search import SRC, imported_modules, modules

UNDO_NAMES = ("UndoService", "UndoReport")


def _modules_holding_undid() -> list[str]:
    return sorted(
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if "undid" in path.read_text(encoding="utf-8")
    )


def _modules_importing_an_undo_name() -> list[str]:
    return sorted(
        name
        for name, tree in modules().items()
        if any(imported.rsplit(".", 1)[-1] in UNDO_NAMES for imported in imported_modules(tree))
    )


@pytest.mark.parametrize(
    ("check", "expected"),
    [
        pytest.param(
            lambda: importlib.util.find_spec("factory.application.undo"), None, id="undo-module"
        ),
        pytest.param(
            lambda: has_name("factory.application.take", "is_refused"), True, id="is-refused"
        ),
        pytest.param(
            lambda: has_name("factory.application.take", "read_baseline"),
            True,
            id="read-baseline",
        ),
        pytest.param(
            lambda: has_name("factory.application.take", "restore_work_item"),
            True,
            id="restore-work-item",
        ),
        pytest.param(_modules_holding_undid, [], id="no-undid"),
        pytest.param(_modules_importing_an_undo_name, [], id="no-undo-name-imported"),
    ],
)
def test_the_undo_module_is_gone_and_the_take_holds_the_shared_functions(
    check: Callable[[], object], expected: object
) -> None:
    assert check() == expected
