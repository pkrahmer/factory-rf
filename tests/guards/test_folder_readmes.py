"""Every listed folder README that exists agrees with its folder and keeps the README's form."""

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


@pytest.mark.parametrize("path", FOLDER_READMES)
def test_a_folder_readme_agrees_with_its_folder(path: str) -> None:
    readme = ROOT / path
    if not readme.is_file():
        pytest.skip(f"{path} is not written yet")
    folder = path.removesuffix(SUFFIX)

    problems = readme_problems(
        folder, readme.read_text(encoding="utf-8"), _subfolders(readme.parent)
    )

    assert problems == []


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
