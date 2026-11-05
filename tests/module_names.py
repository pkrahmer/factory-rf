"""Asks whether a module of the factory still defines a name."""

import importlib
import importlib.util


def has_name(module: str, name: str) -> bool:
    """Whether the module `module`, imported, has an attribute `name`."""
    return hasattr(importlib.import_module(module), name)


def module_exists(module: str) -> bool:
    """Whether the module `module` can be found; a parent package that is gone means it is not."""
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False
