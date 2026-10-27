"""The documents command reads the files of the project guide beside its index."""

from pathlib import Path

import pytest

from check_documents_support import MISSING_LINES
from document_texts import clean_texts, project_guide, write_documents
from factory.domain.documents import DECISION_LOG, OPERATOR_GUIDE, README
from factory.entry.check_documents import main

STAGES = "docs/project-guide/stages.md"


@pytest.mark.parametrize(
    ("files", "folders", "output", "exit_status"),
    [
        pytest.param(
            {STAGES: "# Stages\n\nEach ticket waits.\n"},
            [],
            "docs/project-guide/stages.md: uses the v1 word 'ticket'\n",
            1,
            id="guide-file-read",
        ),
        pytest.param(
            {
                STAGES: "# Stages\n\nThe stages run.\n",
                "docs/project-guide/notes.txt": "A ticket.\n",
                "docs/project-guide/old/x.md": "A ticket.\n",
            },
            ["docs/project-guide/empty.md"],
            "documents ok\n",
            0,
            id="others-ignored",
        ),
        pytest.param(
            {STAGES: "# Stages\n\nThe café opens — every day.\n"},
            [],
            "documents ok\n",
            0,
            id="utf-8",
        ),
    ],
)
def test_the_files_beside_the_index_are_read(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    files: dict[str, str | None],
    folders: list[str],
    output: str,
    exit_status: int,
) -> None:
    write_documents(tmp_path, clean_texts())
    write_documents(tmp_path, files)
    for folder in folders:
        (tmp_path / folder).mkdir(parents=True)

    status = main(["--root", str(tmp_path)])

    assert capsys.readouterr().out == output
    assert status == exit_status


def _old_path_texts() -> dict[str, str | None]:
    clean = clean_texts()
    return {
        README: clean[README],
        OPERATOR_GUIDE: clean[OPERATOR_GUIDE],
        DECISION_LOG: clean[DECISION_LOG],
        "docs/project-guide.md": project_guide(),
    }


@pytest.mark.parametrize(
    ("texts", "output"),
    [
        pytest.param(_old_path_texts(), "docs/project-guide/README.md: missing\n", id="old-path"),
        pytest.param({}, MISSING_LINES, id="empty-root"),
    ],
)
def test_the_old_guide_path_is_not_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], texts: dict[str, str | None], output: str
) -> None:
    write_documents(tmp_path, texts)

    status = main(["--root", str(tmp_path)])

    assert capsys.readouterr().out == output
    assert status == 1
