"""The claim service is the only module that builds claims and judges their lease."""

import ast

from source_search import imported_modules, modules

CLAIMS = "factory.application.claims"
LEASE = "factory.domain.lease"
LEASE_FUNCTIONS = ("claim_status", "lease_expired", "lease_age", "observed_claim_status")


def _dotted(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        owner = _dotted(node.value)
        return None if owner is None else f"{owner}.{node.attr}"
    return None


def _reaches_a_lease_function_as_attribute(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.Attribute)
        and node.attr in LEASE_FUNCTIONS
        and _dotted(node.value) in {"lease", LEASE}
        for node in ast.walk(tree)
    )


def _calls_claim(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == "Claim")
            or (isinstance(node.func, ast.Attribute) and node.func.attr == "Claim")
        )
        for node in ast.walk(tree)
    )


def test_only_the_claim_service_uses_the_lease_functions() -> None:
    found = modules()
    wanted = {f"{LEASE}.{name}" for name in LEASE_FUNCTIONS}
    importers = {name for name, tree in found.items() if imported_modules(tree) & wanted}
    reaching = {
        name
        for name, tree in found.items()
        if name != CLAIMS and _reaches_a_lease_function_as_attribute(tree)
    }

    assert importers == {CLAIMS}
    assert reaching == set()


def test_only_the_claim_service_constructs_a_claim() -> None:
    constructing = {name for name, tree in modules().items() if _calls_claim(tree)}

    assert constructing == {CLAIMS}
