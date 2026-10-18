"""The confinement of one run: the targets as the existing files allow them, and the extras."""

from pathlib import Path

import pytest

from factory.domain.confinement import Confinement, WriteTarget, confinement_of

ROOT = Path("/w")
TEMPORARY = Path("/r/run")


def _folder(path: str) -> WriteTarget:
    return WriteTarget(path=Path(path), kind="folder")


def _file(path: str) -> WriteTarget:
    return WriteTarget(path=Path(path), kind="file")


@pytest.mark.parametrize(
    ("target", "existing", "folders", "files"),
    [
        pytest.param(_folder("/w/src"), [], ["/w/src"], [], id="folder"),
        pytest.param(
            _file("/w/README.md"), ["/w/README.md"], [], ["/w/README.md"], id="existing-file"
        ),
        pytest.param(_file("/w/docs/openapi.json"), [], ["/w/docs"], [], id="missing-file"),
        pytest.param(_file("/w/NEW.md"), [], [], [], id="missing-file-at-root"),
        pytest.param(_file("/w/a/b/c.md"), [], ["/w/a/b"], [], id="missing-nested-file"),
    ],
)
def test_a_target_is_a_folder_a_file_or_the_folder_of_a_missing_file(
    target: WriteTarget, existing: list[str], folders: list[str], files: list[str]
) -> None:
    confinement = confinement_of(
        [target],
        root=ROOT,
        existing_files={Path(path) for path in existing},
        extras=[],
        temporary_directory=TEMPORARY,
    )

    assert confinement == Confinement(
        folders=[Path(path) for path in folders],
        files=[Path(path) for path in files],
        temporary_directory=TEMPORARY,
    )


def test_the_extras_follow_the_targets_as_given_and_a_repeated_path_is_left_out() -> None:
    targets = [
        _folder("/w/src"),
        _file("/w/README.md"),
        _file("/w/docs/new.md"),
        _folder("/w/docs"),
    ]
    extras = [
        _folder("/w/src"),
        _folder("/x/extra"),
        _file("/x/missing.json"),
        _file("/w/README.md"),
    ]

    confinement = confinement_of(
        targets,
        root=ROOT,
        existing_files={Path("/w/README.md")},
        extras=extras,
        temporary_directory=TEMPORARY,
    )

    assert confinement == Confinement(
        folders=[Path("/w/src"), Path("/w/docs"), Path("/x/extra")],
        files=[Path("/w/README.md"), Path("/x/missing.json")],
        temporary_directory=TEMPORARY,
    )
