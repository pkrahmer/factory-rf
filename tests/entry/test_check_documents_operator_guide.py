"""The documents command checks the operator guide's index and topic files in the repository."""

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from support.check_documents_support import TIME_LINE

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


@pytest.mark.parametrize(
    ("change", "output", "exit_status"),
    [
        pytest.param(_unchanged, None, 0, id="as-it-is"),
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
    output: str | None,
    exit_status: int,
) -> None:
    change(documents)

    status = main(["--root", str(documents)])

    printed = capsys.readouterr().out.splitlines(keepends=True)
    if output is None:
        assert re.fullmatch(TIME_LINE, printed[-1].rstrip("\n"))
    else:
        assert (
            "".join(
                line
                for line in printed
                if not line.endswith(" does not exist\n") and line != "Report (not checked yet):\n"
            )
            == output
        )
    assert status == exit_status
