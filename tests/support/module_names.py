"""Asks whether a module of the factory still defines a name, or exists in any area."""

import importlib
import importlib.util
from collections.abc import Collection

from support.source_search import SRC

LAYERS = ("domain", "application", "adapters")
# Package folders under `src/factory/` that are not areas.
NOT_AREAS = frozenset({"entry", "contract"})


def has_name(module: str, name: str) -> bool:
    """Whether the module `module`, imported, has an attribute `name`."""
    return hasattr(importlib.import_module(module), name)


def module_exists(module: str) -> bool:
    """Whether the module `module` can be found; a parent package that is gone means it is not."""
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


def areas() -> list[str]:
    """The areas, read from the tree: the package folders but `entry` and `contract`."""
    return sorted(
        path.name
        for path in SRC.iterdir()
        if path.is_dir() and (path / "__init__.py").is_file() and path.name not in NOT_AREAS
    )


def is_old_layer_path(name: str) -> bool:
    """Whether `name` is `factory.<layer>.<rest>`, a layer of `LAYERS` and `<rest>` dotted names."""
    parts = name.split(".")
    return (
        len(parts) >= 3
        and parts[0] == "factory"
        and parts[1] in LAYERS
        and all(part.isidentifier() for part in parts[2:])
    )


def _in_every_area(module: str) -> list[str]:
    if not is_old_layer_path(module):
        return []
    parts = module.split(".")
    return [".".join(["factory", area, *parts[1:]]) for area in areas()]


def module_exists_anywhere(module: str) -> bool:
    """Whether `module` can be found at its path or, named at an old layer path, in any area."""
    return module_exists(module) or any(module_exists(name) for name in _in_every_area(module))


def names_the_module_anywhere(names: Collection[str], module: str) -> bool:
    """Whether `names` holds `module` or, for an old layer path, the same module in any area."""
    return module in names or any(name in names for name in _in_every_area(module))
