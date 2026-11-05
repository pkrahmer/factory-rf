"""The old layer packages are gone: `src/factory` holds only the areas, `entry` and `contract`."""

import importlib.util
from pathlib import Path

import pytest

from support.source_search import SRC

TESTS = Path(__file__).parents[1]
OLD_LAYERS = ("domain", "application", "adapters")
AREAS = ("shared", "hosting", "work", "agents", "watching", "machine", "pipeline")


@pytest.mark.parametrize("layer", OLD_LAYERS)
def test_no_test_folder_of_an_old_layer_is_left(layer: str) -> None:
    assert not (TESTS / layer).exists()


def test_the_package_holds_only_its_init_the_areas_entry_and_contract() -> None:
    entries = {path.name for path in SRC.iterdir() if path.name != "__pycache__"}

    assert entries == {"__init__.py", *AREAS, "entry", "contract"}


@pytest.mark.parametrize("layer", OLD_LAYERS)
def test_an_old_layer_package_cannot_be_imported(layer: str) -> None:
    assert importlib.util.find_spec(f"factory.{layer}") is None
