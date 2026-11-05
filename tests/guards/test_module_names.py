"""A module named at an old layer path is found, and named, in any area."""

import pytest

from support.module_names import module_exists_anywhere, names_the_module_anywhere


@pytest.mark.parametrize(
    ("module", "found"),
    [
        pytest.param("factory.domain.errors", True, id="old-path-in-an-area"),
        pytest.param("factory.adapters.process", True, id="old-adapter-path-in-an-area"),
        pytest.param("factory.domain.no_such_module", False, id="old-path-nowhere"),
        pytest.param("factory.shared.domain.errors", True, id="own-path"),
        pytest.param("factory.shared.domain.no_such_module", False, id="own-path-missing"),
        pytest.param("factory.entry.run", True, id="entry-module"),
        pytest.param("factory.entry.confine", False, id="entry-module-missing"),
        pytest.param("factory.contract.errors", False, id="contract-is-no-layer"),
    ],
)
def test_a_module_is_found_at_its_path_or_from_an_old_layer_path_in_any_area(
    module: str, found: bool
) -> None:
    assert module_exists_anywhere(module) is found


@pytest.mark.parametrize(
    ("names", "module", "named"),
    [
        pytest.param(
            {"factory.agents.adapters.landlock"}, "factory.adapters.landlock", True, id="in-an-area"
        ),
        pytest.param({"factory.adapters.landlock"}, "factory.adapters.landlock", True, id="as-is"),
        pytest.param(
            {"factory.agents.adapters.landlock_extra"},
            "factory.adapters.landlock",
            False,
            id="same-beginning",
        ),
        pytest.param(
            {"factory.agents.domain.landlock"}, "factory.adapters.landlock", False, id="other-layer"
        ),
        pytest.param({"factory.entry.confine"}, "factory.entry.confine", True, id="entry-as-is"),
        pytest.param(
            {"factory.pipeline.entry.confine"},
            "factory.entry.confine",
            False,
            id="entry-in-an-area",
        ),
        pytest.param(set(), "factory.application.undo", False, id="no-names"),
    ],
)
def test_a_set_of_names_holds_a_module_at_its_path_or_from_an_old_layer_path_in_any_area(
    names: set[str], module: str, named: bool
) -> None:
    assert names_the_module_anywhere(names, module) is named
