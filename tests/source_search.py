"""Reads the modules under `src/factory` with `ast`: their imports and string literals."""

import ast
from pathlib import Path

import factory

SRC = Path(factory.__file__).parent


def modules() -> dict[str, ast.Module]:
    """Every module under `src/factory`, parsed, by its dotted name."""
    found: dict[str, ast.Module] = {}
    for path in sorted(SRC.rglob("*.py")):
        parts = path.relative_to(SRC.parent).with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        found[".".join(parts)] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return found


def imported_modules(tree: ast.Module) -> set[str]:
    """The absolute module names that `tree` imports."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def imports(tree: ast.Module, module: str) -> bool:
    """Whether `tree` imports `module` or one of its submodules."""
    return any(name == module or name.startswith(f"{module}.") for name in imported_modules(tree))


def string_literals(tree: ast.Module) -> list[str]:
    """Every string literal in `tree`."""
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
