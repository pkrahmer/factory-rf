"""The boundaries hand the interfaces to services: built by keyword, never changed."""

import dataclasses
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries


def test_boundaries_refuse_positional_arguments(boundaries: Boundaries) -> None:
    values = [getattr(boundaries, field.name) for field in dataclasses.fields(boundaries)]
    build: Callable[..., Boundaries] = Boundaries

    with pytest.raises(TypeError):
        build(*values)


def test_boundaries_refuse_assignment_to_a_field(boundaries: Boundaries, tmp_path: Path) -> None:
    field = "checkout"

    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(boundaries, field, tmp_path / "elsewhere")
