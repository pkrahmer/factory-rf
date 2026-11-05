"""The job start script's step `image`, read as text: the build without layers and the prune."""

from collections.abc import Callable

import pytest

from support.dockerfile_support import _uncommented
from support.vm_support import JOB_START, lines_with

BUILD = "podman $JOB_PODMAN_OPTIONS build"
NO_LAYERS = "--layers=false"
PRUNE = "podman $JOB_PODMAN_OPTIONS image prune -f"


def _image_step(code: str) -> str:
    """The text from the line `step image` to the line of the next step."""
    start = code.index("\nstep image\n")
    end = code.index("\nstep ", start + 1)
    return code[start:end]


@pytest.fixture
def image_step() -> str:
    return _image_step(_uncommented(JOB_START.read_text(encoding="utf-8")))


def _builds_without_layers_then_prunes(step: str) -> bool:
    lines = step.splitlines()
    builds = [index for index, line in enumerate(lines) if BUILD in line and NO_LAYERS in line]
    prunes = [index for index, line in enumerate(lines) if PRUNE in line]
    return bool(builds) and bool(prunes) and max(builds) < min(prunes)


def _reversed(step: str) -> str:
    lines = step.splitlines()
    build = next(line for line in lines if BUILD in line)
    prune = next((line for line in lines if PRUNE in line), PRUNE)
    return "\n".join(line for line in lines if line not in (build, prune)) + f"\n{prune}\n{build}"


@pytest.mark.parametrize(
    ("change", "holds"),
    [
        pytest.param(lambda step: step, True, id="the-script"),
        pytest.param(lambda step: step.replace(f" {NO_LAYERS}", ""), False, id="without-no-layers"),
        pytest.param(
            lambda step: "\n".join(line for line in step.splitlines() if PRUNE not in line),
            False,
            id="without-prune",
        ),
        pytest.param(_reversed, False, id="prune-before-build"),
    ],
)
def test_the_image_step_builds_without_layers_and_then_prunes(
    image_step: str, change: Callable[[str], str], holds: bool
) -> None:
    assert _builds_without_layers_then_prunes(change(image_step)) is holds


def test_a_failed_prune_fails_the_image_step(image_step: str) -> None:
    prunes = lines_with(image_step, PRUNE)
    assert prunes
    assert all(line.rstrip().endswith("|| failed image") for line in prunes)


@pytest.mark.parametrize("flag", ["-a", "--all"])
def test_the_prune_never_removes_a_tagged_image(image_step: str, flag: str) -> None:
    prunes = lines_with(image_step, PRUNE)
    assert prunes
    assert all(flag not in line.split() for line in prunes)
