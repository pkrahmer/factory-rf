"""The guard's verdict on a hook payload, and the settings file it reads."""

import json
from pathlib import Path

import pytest

from factory.adapters.claude_guard import GuardVerdict, judge, read_guard_settings
from factory.domain.agent_runs import GuardSettings
from factory.domain.errors import GuardSettingsInvalid
from factory.domain.write_paths import PROTECTED_PATHS
from guard_support import hook_payload, outside

PROTECTED_MESSAGE = "pyproject.toml is owned by the human; a change there is a question."
OUTSIDE_WRITE_PATHS_MESSAGE = "docs/a.md is outside the write paths of this stage."


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    return root


def _settings(root: Path, write_paths: list[str]) -> GuardSettings:
    return GuardSettings(root=root, write_paths=write_paths, protected_paths=list(PROTECTED_PATHS))


@pytest.mark.parametrize("tool", ["Edit", "Write"])
def test_a_path_inside_the_write_paths_is_allowed(tmp_path: Path, tool: str) -> None:
    root = _root(tmp_path)

    verdict = judge(hook_payload(str(root / "src" / "a.py"), tool), _settings(root, ["src/*"]))

    assert verdict == GuardVerdict(allowed=True, message="")


def test_a_path_outside_the_write_paths_is_refused(tmp_path: Path) -> None:
    root = _root(tmp_path)

    verdict = judge(hook_payload(str(root / "docs" / "a.md")), _settings(root, ["src/*"]))

    assert verdict == GuardVerdict(allowed=False, message=OUTSIDE_WRITE_PATHS_MESSAGE)


def test_a_protected_path_is_refused_although_a_write_path_matches(tmp_path: Path) -> None:
    root = _root(tmp_path)

    verdict = judge(hook_payload(str(root / "pyproject.toml")), _settings(root, ["*"]))

    assert verdict == GuardVerdict(allowed=False, message=PROTECTED_MESSAGE)


@pytest.mark.parametrize("where", ["sibling", "prefixed sibling", "system"])
def test_a_path_outside_the_checkout_is_refused(tmp_path: Path, where: str) -> None:
    root = _root(tmp_path)
    file_path = {
        "sibling": str(tmp_path / "other" / "a.py"),
        "prefixed sibling": f"{root}-x/a.py",
        "system": "/etc/passwd",
    }[where]

    verdict = judge(hook_payload(file_path), _settings(root, ["*"]))

    assert verdict == GuardVerdict(allowed=False, message=outside(file_path))


@pytest.mark.parametrize(
    ("relative", "expected"),
    [
        ("src/../pyproject.toml", GuardVerdict(allowed=False, message=PROTECTED_MESSAGE)),
        ("src/../src/a.py", GuardVerdict(allowed=True, message="")),
    ],
)
def test_parent_segments_are_resolved_before_the_verdict(
    tmp_path: Path, relative: str, expected: GuardVerdict
) -> None:
    root = _root(tmp_path)
    write_paths = ["*"] if relative.endswith("pyproject.toml") else ["src/*"]

    verdict = judge(hook_payload(f"{root}/{relative}"), _settings(root, write_paths))

    assert verdict == expected


@pytest.mark.parametrize(
    ("file_path", "expected"),
    [
        ("src/a.py", GuardVerdict(allowed=True, message="")),
        ("docs/a.md", GuardVerdict(allowed=False, message=OUTSIDE_WRITE_PATHS_MESSAGE)),
    ],
)
def test_a_relative_path_is_taken_relative_to_the_root(
    tmp_path: Path, file_path: str, expected: GuardVerdict
) -> None:
    root = _root(tmp_path)

    assert judge(hook_payload(file_path), _settings(root, ["src/*"])) == expected


def test_a_link_to_outside_the_checkout_is_refused(tmp_path: Path) -> None:
    root = _root(tmp_path)
    target = tmp_path / "outside.py"
    target.write_text("", encoding="utf-8")
    (root / "src" / "out").symlink_to(target)
    file_path = str(root / "src" / "out")

    verdict = judge(hook_payload(file_path), _settings(root, ["src/*"]))

    assert verdict == GuardVerdict(allowed=False, message=outside(file_path))


def test_a_link_to_a_protected_path_is_refused(tmp_path: Path) -> None:
    root = _root(tmp_path)
    (root / "src" / "p").symlink_to(root / "pyproject.toml")

    verdict = judge(hook_payload(str(root / "src" / "p")), _settings(root, ["*"]))

    assert verdict == GuardVerdict(allowed=False, message=PROTECTED_MESSAGE)


def test_a_link_to_a_writable_path_is_allowed(tmp_path: Path) -> None:
    root = _root(tmp_path)
    (root / "src" / "real.py").write_text("", encoding="utf-8")
    (root / "src" / "ok").symlink_to(root / "src" / "real.py")

    verdict = judge(hook_payload(str(root / "src" / "ok")), _settings(root, ["src/*"]))

    assert verdict == GuardVerdict(allowed=True, message="")


@pytest.mark.parametrize(
    "payload",
    [
        "not json {",
        json.dumps(["Write", {"file_path": "docs/a.md"}]),
        json.dumps({"tool_name": "Write"}),
        json.dumps({"tool_name": "Write", "tool_input": "docs/a.md"}),
        json.dumps({"tool_name": "Write", "tool_input": {"content": "x"}}),
        json.dumps({"tool_name": "Write", "tool_input": {"file_path": 7}}),
        json.dumps({"tool_name": "Write", "tool_input": {"file_path": ""}}),
    ],
)
def test_a_payload_the_guard_cannot_read_is_allowed(tmp_path: Path, payload: str) -> None:
    root = _root(tmp_path)

    assert judge(payload, _settings(root, ["src/*"])) == GuardVerdict(allowed=True, message="")


def test_a_path_with_a_nul_character_is_refused_as_outside_the_checkout(tmp_path: Path) -> None:
    root = _root(tmp_path)
    file_path = f"{root}/src/a\x00.py"

    verdict = judge(hook_payload(file_path), _settings(root, ["src/*"]))

    assert verdict == GuardVerdict(allowed=False, message=outside(file_path))


def test_the_settings_file_reads_back_what_model_dump_json_wrote(tmp_path: Path) -> None:
    settings = _settings(_root(tmp_path), ["src/*", "tests/*"])
    path = tmp_path / "guard.json"
    path.write_text(settings.model_dump_json(), encoding="utf-8")

    read = read_guard_settings(path)

    assert read == settings
    assert isinstance(read.root, Path)
    assert read.root.is_absolute()


@pytest.mark.parametrize(
    "content", ["missing", "directory", "not utf-8", "not json", "not settings"]
)
def test_an_unreadable_settings_file_is_refused_naming_the_file_and_the_fault(
    tmp_path: Path, content: str
) -> None:
    path = tmp_path / "guard.json"
    if content == "directory":
        path.mkdir()
    elif content == "not utf-8":
        path.write_bytes(b"\xff\xfe")
    elif content == "not json":
        path.write_text("root: /x\n", encoding="utf-8")
    elif content == "not settings":
        path.write_text(json.dumps({"root": "relative", "write_paths": []}), encoding="utf-8")

    with pytest.raises(GuardSettingsInvalid) as caught:
        read_guard_settings(path)

    assert caught.value.path == str(path)
    assert caught.value.fault
    assert str(path) in str(caught.value)
    assert caught.value.fault in str(caught.value)
