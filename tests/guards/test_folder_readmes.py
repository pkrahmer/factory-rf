"""Every listed folder README exists, agrees with its folder and keeps the README's form."""

from pathlib import Path

import pytest

from factory.shared.domain.folder_readmes import FOLDER_READMES, readme_problems

ROOT = Path(__file__).parents[2]
README_NAME = "README.md"
SUFFIX = f"/{README_NAME}"
LEFT_OUT = "__pycache__"


def _subfolders(folder: Path) -> list[str]:
    return sorted(
        entry.name
        for entry in folder.iterdir()
        if entry.is_dir() and not entry.name.startswith(".") and entry.name != LEFT_OUT
    )


def _listed_readme_problems(root: Path, path: str) -> list[str]:
    readme = root / path
    folder = path.removesuffix(SUFFIX)
    text = readme.read_text(encoding="utf-8") if readme.is_file() else None
    return readme_problems(folder, text, _subfolders(root / folder))


@pytest.mark.parametrize(
    ("folders", "expected"),
    [
        pytest.param(["bin", "lib"], ["bin", "lib"], id="plain-folders"),
        pytest.param(["bin", ".hidden"], ["bin"], id="hidden-folder"),
        pytest.param(["bin", LEFT_OUT], ["bin"], id="pycache"),
        pytest.param([".hidden", LEFT_OUT], [], id="nothing-left"),
    ],
)
def test_the_subfolders_leave_out_hidden_folders_and_pycache(
    tmp_path: Path, folders: list[str], expected: list[str]
) -> None:
    for name in folders:
        (tmp_path / name).mkdir()
    (tmp_path / "a-file.md").write_text("# A file\n", encoding="utf-8")

    assert _subfolders(tmp_path) == expected


TITLE = "# A folder"
OPENING = "What the folder holds."
LINK = "The guide says more: [the guide](../docs/README.md)."
NAMING_README = f"{TITLE}\n\n{OPENING}\n\n{LINK}\n\n- `y/` holds the files of the folder.\n"
SILENT_README = f"{TITLE}\n\n{OPENING}\n\n{LINK}\n"


@pytest.mark.parametrize(
    ("readme", "expected"),
    [
        pytest.param(NAMING_README, [], id="names-its-subfolder"),
        pytest.param(None, ["x: no README.md"], id="no-readme"),
        pytest.param(SILENT_README, ["x: y/ is not named"], id="subfolder-not-named"),
    ],
)
def test_a_listed_readme_gives_its_problems_and_a_missing_one_fails(
    tmp_path: Path, readme: str | None, expected: list[str]
) -> None:
    (tmp_path / "x" / "y").mkdir(parents=True)
    if readme is not None:
        (tmp_path / "x" / README_NAME).write_text(readme, encoding="utf-8")

    assert _listed_readme_problems(tmp_path, f"x{SUFFIX}") == expected


@pytest.mark.parametrize("path", FOLDER_READMES)
def test_a_folder_readme_agrees_with_its_folder(path: str) -> None:
    assert _listed_readme_problems(ROOT, path) == []


def test_every_listed_readme_is_a_readme_of_a_folder_that_exists() -> None:
    wrong = [
        path
        for path in FOLDER_READMES
        if not path.endswith(SUFFIX) or not (ROOT / path.removesuffix(SUFFIX)).is_dir()
    ]

    assert wrong == []


def test_every_package_under_the_factory_package_has_its_readme_listed() -> None:
    package = ROOT / "src" / "factory"
    missing = [
        f"src/factory/{entry.name}{SUFFIX}"
        for entry in sorted(package.iterdir())
        if (entry / "__init__.py").is_file()
        and f"src/factory/{entry.name}{SUFFIX}" not in FOLDER_READMES
    ]

    assert missing == []
