"""The operator guide is a folder of topic files, and nothing names the single file it was."""

from pathlib import Path

from support.check_documents_support import TOPIC_FILES
from support.guide_files_support import searched_files

ROOT = Path(__file__).parents[2]
GUIDE = ROOT / "docs" / "operator-guide"
OLD_GUIDE = ROOT / "docs" / "operator-guide.md"
SEARCHED = (
    ROOT / "src",
    ROOT / "agents",
    ROOT / "operator",
    ROOT / "docs",
    ROOT / "README.md",
)
NOT_SEARCHED = (ROOT / "docs" / "runs", ROOT / "docs" / "decisions.md")


def test_the_single_guide_is_gone_and_the_folder_holds_the_index_and_ten_topics() -> None:
    assert not OLD_GUIDE.exists()
    names = sorted(path.name for path in GUIDE.iterdir())
    assert names == sorted(("README.md", *TOPIC_FILES))


def test_no_file_names_the_single_guide() -> None:
    found = [
        f"{path.relative_to(ROOT)}:{number}"
        for path in searched_files(SEARCHED, NOT_SEARCHED)
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
        )
        if "docs/operator-guide.md" in line
    ]
    assert found == []
