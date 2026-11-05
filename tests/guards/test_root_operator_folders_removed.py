"""The VM's files and the template sit under `operator/`, and nothing names their old place."""

import re
from pathlib import Path

import pytest

from support.guide_files_support import searched_files

ROOT = Path(__file__).parents[2]
SEARCHED = (
    ROOT / "src",
    ROOT / "tests",
    ROOT / "operator",
    ROOT / "agents",
    ROOT / "docs",
    ROOT / "README.md",
)
NOT_SEARCHED = (ROOT / "docs" / "decisions.md", ROOT / "docs" / "runs")
VM_FILES = ("setup.sh", "job-start.sh", "Dockerfile", "factory.service", "git-credential-factory")
TEMPLATE_FILES = ("CLAUDE.md", "Makefile", "factory/pipeline.yml")
# Built from their parts, so that this file does not name the old places itself.
OLD_VM = "vm" + "/"
OLD_TEMPLATE = "template" + "/"
# A name at the root: not the tail of a longer path such as `operator/vm/`.
AT_ROOT = r"(?<!operator/)(?<![\w.-])"


@pytest.mark.parametrize("folder", ["vm", "template"])
def test_the_old_root_folder_is_gone(folder: str) -> None:
    assert [path for path in (ROOT / folder).rglob("*") if path.is_file()] == []


@pytest.mark.parametrize(
    "path",
    [*(f"operator/vm/{name}" for name in VM_FILES)]
    + [*(f"operator/template/{name}" for name in TEMPLATE_FILES)],
)
def test_the_moved_file_lies_under_operator(path: str) -> None:
    assert (ROOT / path).is_file()


@pytest.mark.parametrize(
    "old_name",
    [*(OLD_VM + name for name in VM_FILES), OLD_TEMPLATE],
)
def test_no_file_names_the_old_root_path(old_name: str) -> None:
    pattern = re.compile(AT_ROOT + re.escape(old_name))
    naming = [
        str(path.relative_to(ROOT))
        for path in searched_files(SEARCHED, NOT_SEARCHED)
        if pattern.search(path.read_text(encoding="utf-8", errors="ignore"))
    ]

    assert naming == []


@pytest.mark.parametrize(
    ("text", "named"),
    [
        pytest.param("run `" + OLD_VM + "setup.sh`", True, id="at-root"),
        pytest.param('"$code/' + OLD_VM + 'Dockerfile"', True, id="under-a-checkout"),
        pytest.param("$REF:" + OLD_VM + "job-start.sh", True, id="in-a-git-show"),
        pytest.param("run `operator/" + OLD_VM + "setup.sh`", False, id="moved"),
        pytest.param("`tests/" + OLD_VM + "`", False, id="tests-folder"),
        pytest.param("/proc/sys/" + OLD_VM + "drop_caches", False, id="other-file"),
    ],
)
def test_the_search_finds_only_a_name_at_the_root(text: str, *, named: bool) -> None:
    found = any(re.search(AT_ROOT + re.escape(OLD_VM + name), text) for name in VM_FILES)

    assert found is named
