"""The probe, project agent and entrypoint test helpers are written in one shared place each."""

import re
from pathlib import Path

import pytest

TESTS = Path(__file__).parent
# The texts below are split so that a search of `tests` for them finds only their one module.
THIS = Path(__file__).name


def _writing(pattern: str) -> list[str]:
    found = re.compile(pattern, re.MULTILINE | re.DOTALL)
    return sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if path.name != THIS and found.search(path.read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize(
    ("pattern", "module"),
    [
        pytest.param(
            re.escape("ENVIRONMENT = " + '{"PATH": "/opt/factory/bin:/usr/bin"'),
            "probe_support.py",
            id="environment",
        ),
        pytest.param(
            r'^COMPLETED = AgentRunResult\([^)]*entry="probe"',
            "probe_support.py",
            id="completed",
        ),
        pytest.param(
            re.escape("PROJECT_CODER = " + "AGENT_FILE.replace("),
            "git_support.py",
            id="project-coder",
        ),
        pytest.param(re.escape("Layout" + "(tmp_path)"), "conftest.py", id="image-layout"),
    ],
)
def test_each_shared_helper_is_written_in_one_module(pattern: str, module: str) -> None:
    assert _writing(pattern) == [module]


def test_the_image_layout_fixture_returns_the_entrypoints_layout() -> None:
    conftest = (TESTS / "conftest.py").read_text(encoding="utf-8")

    assert "from entrypoint_support import Layout as ImageLayout\n" in conftest
    assert "    return ImageLayout" + "(tmp_path)\n" in conftest
