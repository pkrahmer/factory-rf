"""The documents command checks the operator guide's index and topic files in the repository."""

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.entry.check_documents import main

ROOT = Path(__file__).parents[2]
GUIDE = "docs/operator-guide"


def _without_heading(name: str, heading: str) -> Callable[[Path], None]:
    def change(root: Path) -> None:
        path = root / GUIDE / name
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        kept = [line for line in lines if line.rstrip("\n") != f"## {heading}"]
        assert len(kept) == len(lines) - 1
        path.write_text("".join(kept), encoding="utf-8")

    return change


def _without_file(name: str) -> Callable[[Path], None]:
    def change(root: Path) -> None:
        (root / GUIDE / name).unlink()

    return change


def _unchanged(root: Path) -> None:
    del root


@pytest.fixture
def documents(tmp_path: Path) -> Path:
    """A copy of the repository's documents under `tmp_path`."""
    root = tmp_path / "root"
    (root / "docs").mkdir(parents=True)
    shutil.copy(ROOT / "README.md", root / "README.md")
    shutil.copy(ROOT / "docs" / "decisions.md", root / "docs" / "decisions.md")
    shutil.copytree(ROOT / "docs" / "project-guide", root / "docs" / "project-guide")
    shutil.copytree(ROOT / GUIDE, root / GUIDE)
    return root


@pytest.mark.parametrize(
    ("change", "output", "exit_status"),
    [
        pytest.param(_unchanged, "documents ok\n", 0, id="as-it-is"),
        pytest.param(
            _without_heading("stops.md", "The stops"),
            "docs/operator-guide/stops.md: section 'The stops' is missing\n",
            1,
            id="no-stops-section",
        ),
        pytest.param(
            _without_heading("install.md", "Install"),
            "docs/operator-guide/install.md: section 'Install' is missing\n",
            1,
            id="no-install-section",
        ),
        pytest.param(
            _without_heading("install.md", "Configuration"),
            "docs/operator-guide/install.md: section 'Configuration' is missing\n",
            1,
            id="no-configuration-section",
        ),
        pytest.param(
            _without_file("install.md"),
            "docs/operator-guide/install.md: missing\n",
            1,
            id="no-install-file",
        ),
        pytest.param(
            _without_file("README.md"),
            "docs/operator-guide/README.md: missing\n",
            1,
            id="no-index",
        ),
    ],
)
def test_the_operator_guide_folder_is_checked_per_file(
    documents: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    change: Callable[[Path], None],
    output: str,
    exit_status: int,
) -> None:
    change(documents)

    status = main(["--root", str(documents)])

    assert capsys.readouterr().out == output
    assert status == exit_status
