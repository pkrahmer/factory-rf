"""The guard allows an edit beneath the run's own temporary folder, after the checkout's rules."""

import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from factory.adapters.claude_guard import GuardVerdict, judge, read_guard_settings
from factory.domain.agent_runs import GuardSettings
from factory.domain.errors import GuardSettingsInvalid
from factory.domain.write_paths import PROTECTED_PATHS, refusal
from guard_support import hook_payload, outside

# The installed console script, beside the interpreter that runs the tests.
GUARD = str(Path(sys.executable).parent / "factory-guard")
ALLOWED = GuardVerdict(allowed=True, message="")


@dataclass(frozen=True)
class Case:
    """The file a `Write` names, the settings it is judged against and the verdict expected."""

    file_path: str
    settings: GuardSettings
    expected: GuardVerdict


def _checkout(root: Path) -> Path:
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "src" / "a.py").write_text("", encoding="utf-8")
    return root


def _settings(
    root: Path, temporary: Path | None, write_paths: tuple[str, ...] = ("src/*",)
) -> GuardSettings:
    return GuardSettings(
        root=root,
        write_paths=list(write_paths),
        protected_paths=list(PROTECTED_PATHS),
        temporary_directory=temporary,
    )


def _folders(tmp_path: Path) -> tuple[Path, Path]:
    temporary = tmp_path / "t"
    temporary.mkdir()
    return _checkout(tmp_path / "checkout"), temporary


def _refused_in_checkout(settings: GuardSettings) -> GuardVerdict:
    message = refusal("src/a.py", settings)
    assert message is not None
    return GuardVerdict(allowed=False, message=message)


def _file_in_folder(tmp_path: Path) -> Case:
    root, temporary = _folders(tmp_path)
    return Case(str(temporary / "notes.txt"), _settings(root, temporary), ALLOWED)


def _missing_folders(tmp_path: Path) -> Case:
    root, temporary = _folders(tmp_path)
    file_path = str(temporary / "deep" / "new" / "x.txt")
    return Case(file_path, _settings(root, temporary), ALLOWED)


def _folder_itself(tmp_path: Path) -> Case:
    root, temporary = _folders(tmp_path)
    refused = GuardVerdict(allowed=False, message=outside(str(temporary)))
    return Case(str(temporary), _settings(root, temporary), refused)


def _prefixed_sibling(tmp_path: Path) -> Case:
    root, temporary = _folders(tmp_path)
    file_path = f"{temporary}-x/a.txt"
    refused = GuardVerdict(allowed=False, message=outside(file_path))
    return Case(file_path, _settings(root, temporary), refused)


def _link_into_checkout(tmp_path: Path) -> Case:
    root, temporary = _folders(tmp_path)
    (temporary / "link.py").symlink_to(root / "src" / "a.py")
    settings = _settings(root, temporary, ("docs/*",))
    return Case(str(temporary / "link.py"), settings, _refused_in_checkout(settings))


def _no_temporary_folder(tmp_path: Path) -> Case:
    root, temporary = _folders(tmp_path)
    file_path = str(temporary / "notes.txt")
    refused = GuardVerdict(allowed=False, message=outside(file_path))
    return Case(file_path, _settings(root, None), refused)


def _checkout_beneath_folder(tmp_path: Path) -> Case:
    temporary = tmp_path / "t"
    root = _checkout(temporary / "checkout")
    settings = _settings(root, temporary, ("docs/*",))
    return Case(str(root / "src" / "a.py"), settings, _refused_in_checkout(settings))


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(_file_in_folder, id="file-in-folder"),
        pytest.param(_missing_folders, id="missing-folders"),
        pytest.param(_folder_itself, id="folder-itself"),
        pytest.param(_prefixed_sibling, id="prefixed-sibling"),
        pytest.param(_link_into_checkout, id="link-into-checkout"),
        pytest.param(_no_temporary_folder, id="no-temporary-folder"),
        pytest.param(_checkout_beneath_folder, id="checkout-beneath-folder"),
    ],
)
def test_a_write_beneath_the_temporary_folder_is_allowed_after_the_checkout_rules(
    tmp_path: Path, case: Callable[[Path], Case]
) -> None:
    built = case(tmp_path)

    assert judge(hook_payload(built.file_path), built.settings) == built.expected


@pytest.mark.parametrize("temporary", ["absolute", "absent", "relative"])
def test_the_settings_file_reads_the_temporary_folder_back(tmp_path: Path, temporary: str) -> None:
    root = tmp_path / "checkout"
    folder = tmp_path / "t"
    content: dict[str, object] = {"root": str(root), "write_paths": [], "protected_paths": []}
    if temporary == "absolute":
        content["temporary_directory"] = str(folder)
    elif temporary == "relative":
        content["temporary_directory"] = "relative/t"
    path = tmp_path / "guard.json"
    path.write_text(json.dumps(content), encoding="utf-8")

    if temporary == "relative":
        with pytest.raises(GuardSettingsInvalid):
            read_guard_settings(path)
        return
    read = read_guard_settings(path)

    assert read.temporary_directory == (folder if temporary == "absolute" else None)


@pytest.mark.parametrize(
    ("with_folder", "status", "stderr"),
    [
        pytest.param(True, 0, "", id="with-folder"),
        pytest.param(False, 2, "outside", id="without-folder"),
    ],
)
def test_the_console_script_allows_a_write_in_the_temporary_folder_it_is_given(
    tmp_path: Path, *, with_folder: bool, status: int, stderr: str
) -> None:
    root, temporary = _folders(tmp_path)
    settings = _settings(root, temporary if with_folder else None)
    path = tmp_path / "guard.json"
    path.write_text(settings.model_dump_json(), encoding="utf-8")
    file_path = str(temporary / "notes.txt")

    result = subprocess.run(  # noqa: S603  (the installed console script, fixed arguments)
        [GUARD, "--settings", str(path)],
        input=hook_payload(file_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == status
    assert result.stderr == (f"{outside(file_path)}\n" if stderr == "outside" else "")
