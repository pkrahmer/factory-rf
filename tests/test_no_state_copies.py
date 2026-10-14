"""Only `require_state` checks that a work item has a state; the journal keeps its own copy."""

import ast

import pytest

from source_search import modules

COPY = "_state_of"
COPY_MODULE = "factory.domain.journal"
ALLOWED_CHECKS = {
    ("factory.domain.work_item", "require_state"),
    (COPY_MODULE, COPY),
}
OUTSIDE = "factory.application.example"

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


def copies(trees: dict[str, ast.Module]) -> list[str]:
    """Every module outside the journal that defines a `_state_of` function."""
    return [
        module
        for module, tree in sorted(trees.items())
        if module != COPY_MODULE
        and any(isinstance(node, FunctionNode) and node.name == COPY for node in ast.walk(tree))
    ]


def _is_state(node: ast.expr) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "state"


def _names_assigned_a_state(function: FunctionNode) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and _is_state(node.value):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif (
            isinstance(node, ast.AnnAssign)
            and node.value is not None
            and _is_state(node.value)
            and isinstance(node.target, ast.Name)
        ):
            names.add(node.target.id)
    return names


def _is_state_check(node: ast.If, state_names: set[str]) -> bool:
    if len(node.body) != 1 or not isinstance(node.body[0], ast.Raise):
        return False
    test = node.test
    if not (
        isinstance(test, ast.Compare)
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Is)
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value is None
    ):
        return False
    subject = test.left
    return _is_state(subject) or (isinstance(subject, ast.Name) and subject.id in state_names)


def state_checks(trees: dict[str, ast.Module]) -> list[str]:
    """Every function outside the allowed two that raises when a state is None."""
    found: list[str] = []
    for module, tree in sorted(trees.items()):
        for function in ast.walk(tree):
            if not isinstance(function, FunctionNode):
                continue
            if (module, function.name) in ALLOWED_CHECKS:
                continue
            state_names = _names_assigned_a_state(function)
            if any(
                isinstance(node, ast.If) and _is_state_check(node, state_names)
                for node in ast.walk(function)
            ):
                found.append(f"{module}.{function.name}")
    return found


def test_no_module_but_the_journal_defines_its_own_state_copy() -> None:
    assert copies(modules()) == []


@pytest.mark.parametrize(
    ("module", "found"),
    [(OUTSIDE, [OUTSIDE]), (COPY_MODULE, [])],
    ids=["outside", "journal"],
)
def test_a_state_copy_is_found_outside_the_journal_only(module: str, found: list[str]) -> None:
    source = (
        "def _state_of(document):\n"
        "    if document.state is None:\n"
        "        raise ValueError('no state')\n"
        "    return document.state\n"
    )

    assert copies({module: ast.parse(source)}) == found


def test_no_function_but_the_allowed_two_checks_a_state_itself() -> None:
    assert state_checks(modules()) == []


ATTRIBUTE_CHECK = (
    "def release(document):\n"
    "    if document.state is None:\n"
    "        raise ValueError('no state')\n"
    "    return document.state.stage\n"
)
NAME_CHECK = (
    "def begin(snapshot):\n"
    "    state = snapshot.document.state\n"
    "    if state is None:\n"
    "        raise ValueError('no state')\n"
    "    return state.stage\n"
)


@pytest.mark.parametrize(
    "source",
    [ATTRIBUTE_CHECK, NAME_CHECK],
    ids=["attribute", "assigned-name"],
)
def test_an_inline_state_check_is_found(source: str) -> None:
    assert state_checks({OUTSIDE: ast.parse(source)}) != []


@pytest.mark.parametrize(
    ("module", "source"),
    [
        (
            "factory.domain.work_item",
            ATTRIBUTE_CHECK.replace("def release", "def require_state"),
        ),
        (COPY_MODULE, ATTRIBUTE_CHECK.replace("def release", "def _state_of")),
    ],
    ids=["require-state", "journal-copy"],
)
def test_the_allowed_state_checks_are_not_found(module: str, source: str) -> None:
    assert state_checks({module: ast.parse(source)}) == []
