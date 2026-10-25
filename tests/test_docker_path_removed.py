"""The Docker path is gone: its files, its names and the tests that read it."""

import importlib.util
import os
from collections.abc import Callable
from pathlib import Path

import pytest

import factory.adapters.process
from factory.adapters.process import ProcessRequest, run_process
from search_support import modules_matching
from vm_support import SETUP, SYSTEM_PATH, setup_code, step_texts

ROOT = Path(__file__).parent.parent
SOURCE = ROOT / "src" / "factory"
THIS = Path(__file__).name
HELPER = "vm/git-credential-factory"
INSTALLED_HELPER = "/usr/local/bin/git-credential-factory"
# A string literal that begins `image/`, or a path built with the part `image`.
IMAGE_PATH = r"[\"']image/|/\s*[\"']image[\"']"


@pytest.mark.parametrize(
    ("path", "present"),
    [
        ("image/Dockerfile", False),
        ("image/compose.yml", False),
        ("image/entrypoint.sh", False),
        ("image/sudoers-factory-agent", False),
        ("image/gitconfig", False),
        ("image/git-credential-factory", False),
        (HELPER, True),
    ],
)
def test_the_docker_files_are_gone_and_the_helper_is_moved(path: str, *, present: bool) -> None:
    file = ROOT / path

    assert file.is_file() is present
    assert not present or os.access(file, os.X_OK)


def test_the_setup_script_installs_the_moved_helper(tmp_path: Path) -> None:
    code = setup_code()
    tools = step_texts(code)["tools"]

    result = run_process(
        ProcessRequest(argv=["sh", "-n", str(SETUP)], cwd=tmp_path, env={"PATH": SYSTEM_PATH})
    )

    assert HELPER in tools
    assert INSTALLED_HELPER in tools
    assert "image/" not in code
    assert result.exit_status == 0


def _sessions_module_is_gone() -> bool:
    return importlib.util.find_spec("factory.domain.sessions") is None


def _process_table_reader_is_gone() -> bool:
    return not hasattr(factory.adapters.process, "read_process_table")


def _no_module_reads_proc() -> bool:
    return [path for path in SOURCE.rglob("*.py") if "/proc" in path.read_text("utf-8")] == []


@pytest.mark.parametrize(
    "is_gone",
    [
        pytest.param(_sessions_module_is_gone, id="sessions-module"),
        pytest.param(_process_table_reader_is_gone, id="read_process_table"),
        pytest.param(_no_module_reads_proc, id="proc"),
    ],
)
def test_the_process_table_names_are_removed(is_gone: Callable[[], bool]) -> None:
    assert is_gone()


def test_no_test_reads_a_file_under_image() -> None:
    assert modules_matching(IMAGE_PATH, THIS) == []
