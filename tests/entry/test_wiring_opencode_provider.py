"""The wiring hands the provider file to the opencode runtime and to no other."""

import json
import sys
from pathlib import Path

import pytest

from adapters.opencode_stand_in import REPLY_EVENTS, opencode_request, write_agent_settings
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from opencode_provider_support import CONFIGURATION, write_provider
from podman_support import IMAGE, PodmanPlan
from wiring_support import CREDENTIAL, dataset_podman


def _capturing_opencode(folder: Path, runs: Path, capture: Path) -> Path:
    """An `opencode` that copies each run's configuration into `capture` and replies."""
    folder.mkdir(parents=True)
    capture.mkdir()
    path = folder / "opencode"
    path.write_text(
        f"#!{sys.executable} -B\n"
        "import shutil\nimport sys\nfrom pathlib import Path\n"
        f"for found in Path({str(runs)!r}).glob('opencode-*.json'):\n"
        f"    shutil.copy(found, Path({str(capture)!r}) / found.name)\n"
        f"sys.stdout.write({REPLY_EVENTS!r})\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def test_the_built_opencode_runtime_merges_the_provider_file(
    tmp_path: Path, local_settings: InstanceSettings
) -> None:
    runs = local_settings.state_directory / "runs"
    runs.mkdir(parents=True)
    capture = tmp_path / "capture"
    executable = _capturing_opencode(tmp_path / "opencode-bin", runs, capture)
    settings = local_settings.model_copy(
        update={
            "agent_runtime": "opencode",
            "opencode_executable": str(executable),
            "opencode_provider_file": write_provider(tmp_path / "provider"),
        }
    )
    write_agent_settings(settings.agent_home, json.dumps({"permissions": {"deny": []}}))
    dataset_podman(tmp_path, PodmanPlan(image=IMAGE))
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    boundaries.agent_runtime.run(opencode_request(tmp_path / "work"))

    [config] = capture.iterdir()
    held = json.loads(config.read_text(encoding="utf-8"))
    assert {key: held[key] for key in CONFIGURATION} == CONFIGURATION


@pytest.mark.parametrize(
    "with_file",
    [pytest.param(True, id="with-file"), pytest.param(False, id="without-file")],
)
def test_the_provider_file_changes_nothing_on_a_claude_code_instance(
    tmp_path: Path, local_settings: InstanceSettings, *, with_file: bool
) -> None:
    provider_file = write_provider(tmp_path / "provider") if with_file else None
    settings = local_settings.model_copy(
        update={"agent_runtime": "claude", "opencode_provider_file": provider_file}
    )

    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    assert type(boundaries.agent_runtime) is ClaudeCodeRuntime
