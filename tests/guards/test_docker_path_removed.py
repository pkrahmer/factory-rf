"""The Docker path is gone: its files, its names and the tests that read it."""

import os
import re
from collections.abc import Callable
from pathlib import Path

import pytest

import factory.shared.adapters.process
from factory.shared.adapters.process import ProcessRequest, run_process
from support.module_names import module_exists_anywhere
from support.search_support import modules_matching
from support.vm_support import SETUP, SYSTEM_PATH, setup_code, step_texts

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "src" / "factory"
THIS = Path(__file__).name
HELPER = "operator/vm/git-credential-factory"
INSTALLED_HELPER = "/usr/local/bin/git-credential-factory"
# A string literal that begins `image/`, or a path built with the part `image`.
IMAGE_PATH = r"[\"']image/|/\s*[\"']image[\"']"
# The process table: a process's folder, `self`, or the bare `/proc` folder.
PROCESS_TABLE = re.compile(r"/proc(?:/(?:\d+|self)\b|/?(?![\w/]))")


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
    return not module_exists_anywhere("factory.domain.sessions")


def _process_table_reader_is_gone() -> bool:
    return not hasattr(factory.shared.adapters.process, "read_process_table")


def _names_the_process_table(text: str) -> bool:
    return PROCESS_TABLE.search(text) is not None


def _no_module_reads_proc() -> bool:
    return [
        path for path in SOURCE.rglob("*.py") if _names_the_process_table(path.read_text("utf-8"))
    ] == []


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


@pytest.mark.parametrize(
    ("text", "refused"),
    [
        pytest.param('Path("/proc/meminfo")', False, id="meminfo"),
        pytest.param('Path("/proc/1")', True, id="pid"),
        pytest.param('Path("/proc/self")', True, id="self"),
        pytest.param('Path("/proc")', True, id="bare"),
    ],
)
def test_the_process_table_check_refuses_only_the_process_table(
    text: str, *, refused: bool
) -> None:
    assert _names_the_process_table(text) is refused


def test_no_test_reads_a_file_under_image() -> None:
    assert modules_matching(IMAGE_PATH, THIS) == []
