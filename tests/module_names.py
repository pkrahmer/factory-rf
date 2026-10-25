"""Asks whether a module of the factory still defines a name."""

import importlib


def has_name(module: str, name: str) -> bool:
    """Whether the module `module`, imported, has an attribute `name`."""
    return hasattr(importlib.import_module(module), name)
