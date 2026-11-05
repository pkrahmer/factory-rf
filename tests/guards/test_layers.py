"""The layer packages exist and the domain stays at the bottom of the layers."""

import importlib
import subprocess
import sys

LAYERS = ("pipeline.domain", "pipeline.application", "pipeline.adapters", "entry")


def test_each_layer_package_imports_with_a_docstring() -> None:
    for layer in LAYERS:
        module = importlib.import_module(f"factory.{layer}")
        assert module.__doc__


def test_domain_imports_nothing_from_the_other_layers() -> None:
    code = (
        "import sys; import factory.pipeline.domain; "
        "print(sorted(m for m in sys.modules if m.startswith('factory.') "
        "and m != 'factory.pipeline' and 'domain' not in m.split('.')[1:3]))"
    )
    result = subprocess.run(  # noqa: S603  (fixed interpreter and code, no input)
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]"
