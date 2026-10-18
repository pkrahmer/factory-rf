"""The kernel refuses a restricted process's writes outside the folders and files it names."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from factory.adapters.landlock import abi_version

# Every child gets the tree's root as its first argument and these names for its parts.
PRELUDE = """
import json, os, subprocess, sys
from pathlib import Path
from factory.adapters.landlock import abi_version, restrict_writes
from factory.domain.errors import ConfinementError
base = Path(sys.argv[1])
A, B, O, P = base / "A", base / "B", base / "O", base / "P"
F = P / "f.txt"
def attempt(action):
    try:
        result = action()
    except PermissionError as error:
        print(f"errno {error.errno}")
    else:
        print("ok" if result is None else result)
"""


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """Folders A (with a subfolder d), B, O and P, F in P, existing files in A and O, two links."""
    for name in ("A", "A/d", "B", "O", "P"):
        (tmp_path / name).mkdir()
    (tmp_path / "A" / "existing.txt").write_text("a\n", encoding="utf-8")
    (tmp_path / "O" / "existing.txt").write_text("o\n", encoding="utf-8")
    (tmp_path / "P" / "f.txt").write_text("f\n", encoding="utf-8")
    (tmp_path / "link_to_folder").symlink_to(tmp_path / "A")
    (tmp_path / "link_to_file").symlink_to(tmp_path / "P" / "f.txt")
    return tmp_path


def _child(base: Path, code: str, *arguments: str) -> list[str]:
    result = subprocess.run(  # noqa: S603  (fixed interpreter, code written by the test)
        [sys.executable, "-c", PRELUDE + code, str(base), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.splitlines()


def _write(path: str) -> str:
    return f'attempt(lambda: ({path}).write_text("x\\n", encoding="utf-8") and None)\n'


def test_abi_version_reports_at_least_3_and_restricts_nothing(tmp_path: Path) -> None:
    abi = abi_version()

    lines = _child(tmp_path, "abi_version()\n" + _write('base / "new.txt"'))

    assert isinstance(abi, int)
    assert abi >= 3
    assert lines == ["ok"]
    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "x\n"


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        pytest.param(_write('A / "new.txt"'), "ok", id="new-file-in-folder"),
        pytest.param('attempt(lambda: (A / "new").mkdir())\n', "ok", id="new-folder-in-folder"),
        pytest.param(
            '(A / "made").mkdir()\n' + _write('A / "made" / "new.txt"'),
            "ok",
            id="new-file-in-made-folder",
        ),
        pytest.param(
            'attempt(lambda: (A / "existing.txt").unlink())\n', "ok", id="delete-in-folder"
        ),
        pytest.param(
            'attempt(lambda: (A / "link").symlink_to(O / "existing.txt"))\n',
            "ok",
            id="symbolic-link-in-folder",
        ),
        pytest.param(
            'attempt(lambda: (A / "existing.txt").rename(A / "d" / "moved.txt") and None)\n',
            "ok",
            id="rename-between-folders-in-folder",
        ),
        pytest.param(
            'def append():\n    with F.open("a", encoding="utf-8") as h:\n        h.write("y")\n'
            "attempt(append)\n",
            "ok",
            id="append-to-file",
        ),
        pytest.param(
            'def truncate():\n    with F.open("r+", encoding="utf-8") as h:\n'
            "        h.truncate(0)\n"
            "attempt(truncate)\n",
            "ok",
            id="truncate-file",
        ),
        pytest.param(_write('O / "new.txt"'), "errno 13", id="new-file-in-other-folder"),
        pytest.param(_write('base / "new.txt"'), "errno 13", id="new-file-in-root"),
        pytest.param(
            'attempt(lambda: F.rename(P / "moved") and None)\n', "errno 13", id="rename-file"
        ),
        pytest.param("attempt(lambda: F.unlink())\n", "errno 13", id="delete-file"),
        pytest.param(
            'attempt(lambda: (O / "link").symlink_to(O / "existing.txt"))\n',
            "errno 13",
            id="symbolic-link-in-other-folder",
        ),
        pytest.param(
            'attempt(lambda: (O / "existing.txt").read_text(encoding="utf-8").strip())\n',
            "o",
            id="read-in-other-folder",
        ),
        pytest.param(
            'shell = subprocess.run(["sh", "-c", f"echo x > {O}/c"], capture_output=True)\n'
            'print(shell.returncode != 0, (O / "c").exists())\n',
            "True False",
            id="shell-started-by-child",
        ),
    ],
)
def test_a_restricted_process_writes_only_beneath_its_folders_and_on_its_files(
    tree: Path, action: str, expected: str
) -> None:
    lines = _child(tree, "restrict_writes([A], [F])\n" + action)

    assert lines == [expected]


REFUSING = """
folders = [base / name for name in json.loads(sys.argv[2])]
files = [base / name for name in json.loads(sys.argv[3])]
try:
    restrict_writes(folders, files)
except ConfinementError as error:
    print(str(error).replace(str(base), "<base>"))
""" + _write('O / "after.txt"')


@pytest.mark.parametrize(
    ("folders", "files", "message"),
    [
        pytest.param(
            ["missing"],
            [],
            "cannot open <base>/missing: No such file or directory",
            id="missing-folder",
        ),
        pytest.param(
            [],
            ["missing.txt"],
            "cannot open <base>/missing.txt: No such file or directory",
            id="missing-file",
        ),
        pytest.param(["P/f.txt"], [], "<base>/P/f.txt is not a folder", id="file-as-folder"),
        pytest.param([], ["A"], "<base>/A is a folder", id="folder-as-file"),
        pytest.param(
            ["link_to_folder"],
            [],
            "<base>/link_to_folder is a symbolic link",
            id="link-to-folder",
        ),
        pytest.param(
            [], ["link_to_file"], "<base>/link_to_file is a symbolic link", id="link-to-file"
        ),
    ],
)
def test_a_refused_path_raises_and_restricts_nothing(
    tree: Path, folders: list[str], files: list[str], message: str
) -> None:
    lines = _child(tree, REFUSING, json.dumps(folders), json.dumps(files))

    assert lines == [message, "ok"]


@pytest.mark.parametrize(
    ("folders", "files", "message"),
    [
        pytest.param(
            ["missing"],
            ["missing.txt"],
            "cannot open <base>/missing: No such file or directory",
            id="folder-before-file",
        ),
        pytest.param(
            ["missing", "absent"],
            [],
            "cannot open <base>/missing: No such file or directory",
            id="first-of-two-folders",
        ),
        pytest.param(
            [],
            ["missing.txt", "absent.txt"],
            "cannot open <base>/missing.txt: No such file or directory",
            id="first-of-two-files",
        ),
    ],
)
def test_the_first_failing_path_names_the_error(
    tree: Path, folders: list[str], files: list[str], message: str
) -> None:
    lines = _child(tree, REFUSING, json.dumps(folders), json.dumps(files))

    assert lines[0] == message


def test_empty_rules_refuse_every_write_and_leave_reading_open(tree: Path) -> None:
    lines = _child(
        tree,
        "restrict_writes([], [])\n"
        + _write('A / "new.txt"')
        + 'attempt(lambda: (A / "existing.txt").read_text(encoding="utf-8").strip())\n',
    )

    assert lines == ["errno 13", "a"]


@pytest.mark.parametrize(
    ("folder", "expected"),
    [pytest.param("A", "ok", id="in-both"), pytest.param("B", "errno 13", id="in-first-only")],
)
def test_a_second_restriction_stacks_on_the_first(tree: Path, folder: str, expected: str) -> None:
    lines = _child(
        tree,
        "restrict_writes([A, B], [])\nrestrict_writes([A], [])\n" + _write(f'{folder} / "new.txt"'),
    )

    assert lines == [expected]


def test_restricting_leaves_no_descriptor_open(tree: Path) -> None:
    lines = _child(
        tree,
        'before = len(os.listdir("/proc/self/fd"))\n'
        "restrict_writes([A], [F])\n"
        'after = len(os.listdir("/proc/self/fd"))\n'
        "print(before, after)\n",
    )

    count_before, count_after = lines[0].split()
    assert count_after == count_before
