"""The podman images adapter: its build's arguments, output tail and time limit, and `path`."""

import json
import time
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict

from factory.adapters.podman_images import PodmanImages
from factory.domain.containers import JOB_PODMAN_OPTIONS
from factory.domain.errors import ContainerError
from factory.domain.settings import ContainerProfileName
from factory.domain.stage_layer import stage_layer
from run_layout_support import read_records, write_script
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

BASE = "factory-stage:vm"
TAG = "factory-stage:vm-project"
SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"
LIMIT = timedelta(minutes=5)

# Records its arguments and, for `build`, what the folder of its last argument holds; then
# prints the planned lines, waits as planned and exits with the planned status.
STAND_IN = r"""
import json
import os
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parent
arguments = sys.argv[1:]
context = Path(arguments[-1]) if arguments else None
listing = None
if arguments[:1] == ["build"] and context is not None and context.is_dir():
    listing = sorted(os.listdir(context))
with (here / "calls.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps({"arguments": arguments, "context": listing}) + "\n")
plan = json.loads((here / "plan.json").read_text(encoding="utf-8"))
sys.stdout.write(plan["stdout"])
sys.stdout.flush()
time.sleep(plan["wait_seconds"])
sys.exit(plan["exit_status"])
"""


class _Call(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    context: list[str] | None


def _podman(tmp_path: Path, stdout: str = "", wait_seconds: float = 0, status: int = 0) -> Path:
    folder = tmp_path / "podman-bin"
    path = write_script(folder / "podman", STAND_IN)
    plan = {"stdout": stdout, "wait_seconds": wait_seconds, "exit_status": status}
    (folder / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return path


def _calls(podman: Path) -> list[_Call]:
    return read_records(podman.parent / "calls.jsonl", _Call)


LAYER = stage_layer("ARG FACTORY_BASE\nFROM ${FACTORY_BASE}\nRUN true\n", "sha256-base")


def test_the_build_passes_the_base_the_network_the_tag_and_an_empty_context(
    tmp_path: Path,
) -> None:
    podman = _podman(tmp_path)

    build = PodmanImages(str(podman)).build(LAYER, BASE, TAG, LIMIT)

    calls = _calls(podman)
    [built] = [call for call in calls if call.arguments[:1] == ["build"]]
    words = built.arguments
    assert build.passed
    assert "--build-arg" in words
    assert words[words.index("--build-arg") + 1] == f"FACTORY_BASE={BASE}"
    assert "--network=host" in words
    assert words[words.index("-t") + 1] == TAG
    assert built.context == []
    assert calls[-1].arguments == ["image", "prune", "-f"]
    assert calls.index(built) < len(calls) - 1


@pytest.mark.parametrize("count", [25, 5])
def test_the_output_tail_is_the_last_twenty_lines_in_order(tmp_path: Path, count: int) -> None:
    lines = [f"step {number}" for number in range(1, count + 1)]
    podman = _podman(tmp_path, stdout="".join(f"{line}\n" for line in lines))

    build = PodmanImages(str(podman)).build(LAYER, BASE, TAG, LIMIT)

    assert build.output_tail == "\n".join(lines[-20:])


def test_a_build_that_fails_has_not_passed(tmp_path: Path) -> None:
    podman = _podman(tmp_path, stdout="error: no such package\n", status=1)

    build = PodmanImages(str(podman)).build(LAYER, BASE, TAG, LIMIT)

    assert not build.passed


def test_a_build_that_reaches_its_time_limit_has_not_passed(tmp_path: Path) -> None:
    podman = _podman(tmp_path, wait_seconds=ROOMY_BOUND_SECONDS * 4)

    started = time.monotonic()
    build = PodmanImages(str(podman)).build(LAYER, BASE, TAG, ROOMY_LIMIT)
    elapsed = time.monotonic() - started

    assert not build.passed
    assert elapsed < ROOMY_BOUND_SECONDS


@pytest.mark.parametrize(
    ("printed", "expected"),
    [
        pytest.param(
            '["PATH=/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin","LANG=C.UTF-8"]\n',
            "/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin",
            id="with-path",
        ),
        pytest.param('["LANG=C.UTF-8"]\n', SYSTEM_PATH, id="without-path"),
    ],
)
def test_path_is_the_images_configured_path_or_the_base_default(
    tmp_path: Path, printed: str, expected: str
) -> None:
    podman = _podman(tmp_path, stdout=printed)

    path = PodmanImages(str(podman)).path(TAG)

    assert path == expected
    [call] = _calls(podman)
    assert call.arguments == ["image", "inspect", "--format", "{{json .Config.Env}}", TAG]


@pytest.mark.parametrize(
    ("printed", "status"),
    [
        pytest.param("Error: no such image\n", 125, id="inspect-fails"),
        pytest.param("no environment here\n", 0, id="no-json"),
    ],
)
def test_path_raises_a_container_error_when_the_image_cannot_be_read(
    tmp_path: Path, printed: str, status: int
) -> None:
    podman = _podman(tmp_path, stdout=printed, status=status)

    with pytest.raises(ContainerError):
        PodmanImages(str(podman)).path(TAG)


@pytest.mark.parametrize(
    ("profile", "options"),
    [
        pytest.param("job", list(JOB_PODMAN_OPTIONS), id="job"),
        pytest.param("rootless", [], id="rootless"),
    ],
)
def test_the_job_profile_puts_its_global_options_before_every_podman_command(
    tmp_path: Path, profile: ContainerProfileName, options: list[str]
) -> None:
    podman = _podman(tmp_path, stdout='["LANG=C.UTF-8"]\n')
    images = PodmanImages(str(podman), profile=profile)

    images.build(LAYER, BASE, TAG, LIMIT)
    images.path(TAG)

    calls = _calls(podman)
    assert [call.arguments[: len(options)] for call in calls] == [options] * 3
    assert [call.arguments[len(options) :][:2] for call in calls] == [
        ["build", "--build-arg"],
        ["image", "prune"],
        ["image", "inspect"],
    ]
