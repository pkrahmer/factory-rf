"""The story check command: places, forms, readers by folder, output and exit status."""

import subprocess
import sys
from pathlib import Path

import pytest

from factory.entry.check_story import main

FORM = "# Story form\n\n## Description\n\n## Acceptance criteria\n\n## Journal\n"
FEATURE = "F0002-work-item-data"
GOOD = (
    "# A story\n\n## Description\n\nText.\n\n## Acceptance criteria\n\n"
    "1. It works.\n2. make check stays green.\n3. docs: none, nothing changes.\n\n## Journal\n"
)
# The last criterion is on line 11 of the body.
BAD_LAST_CRITERION = GOOD.replace("3. docs: none, nothing changes.", "3. done.")
WITH_ONE_ENTRY = GOOD + "\n1. 2026-10-12 human: created.\n"
UNKNOWN_KEY = "---\nstage: review\ncolour: 2\n---\n"
TWO_RECORDS = (
    "---\nstage: review\njournal:\n"
    "- number: 1\n  speaker: human\n  kind: created\n"
    "- number: 2\n  speaker: factory\n  kind: started\n---\n"
)
USAGE = "usage: factory-check-story <path>..."
NOT_A_LOCATION = (
    "not a work item location: "
    "expected factory/features/<feature>/<backlog|in-progress|done>/<file>.md"
)


def _root(tmp_path: Path, *, form: bool = True, feature_file: bool = True) -> Path:
    root = tmp_path / "repository"
    (root / "factory" / "features" / FEATURE).mkdir(parents=True)
    if form:
        (root / "factory" / "story-form.md").write_text(FORM, encoding="utf-8")
    if feature_file:
        (root / "factory" / "features" / FEATURE / "feature.md").write_text(
            "# Feature\n", encoding="utf-8"
        )
    return root


def _story(root: Path, folder: str, text: str | bytes, name: str = "F0002-S0001-x.md") -> str:
    path = f"factory/features/{FEATURE}/{folder}/{name}"
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        target.write_bytes(text)
    else:
        target.write_text(text, encoding="utf-8")
    return path


def _lines(text: str) -> list[str]:
    return text.splitlines()


def test_a_clean_backlog_story_prints_ok_and_returns_0(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    path = _story(root, "backlog", GOOD)

    status = main([path], root=root)

    assert _lines(capsys.readouterr().out) == [f"{path}: ok"]
    assert status == 0


def test_findings_print_with_and_without_a_line_place_before_form(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path, feature_file=False)
    path = _story(root, "backlog", BAD_LAST_CRITERION)

    status = main([path], root=root)

    assert _lines(capsys.readouterr().out) == [
        f"{path}: the feature file feature.md is missing in factory/features/{FEATURE}",
        f'{path}:11: the last criterion must start with "docs:"',
    ]
    assert status == 1


@pytest.mark.parametrize(
    ("second", "status"), [(GOOD, 0), (BAD_LAST_CRITERION, 1)], ids=["all-ok", "one-finding"]
)
def test_several_paths_are_checked_in_the_order_given(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], second: str, status: int
) -> None:
    root = _root(tmp_path)
    first = _story(root, "backlog", GOOD, "F0002-S0002-b.md")
    other = _story(root, "backlog", second, "F0002-S0001-a.md")
    third = _story(root, "backlog", GOOD, "F0002-S0003-c.md")

    result = main([first, other, third], root=root)

    second_lines = (
        [f"{other}: ok"]
        if second == GOOD
        else [f'{other}:11: the last criterion must start with "docs:"']
    )
    assert _lines(capsys.readouterr().out) == [f"{first}: ok", *second_lines, f"{third}: ok"]
    assert result == status


def test_no_path_prints_the_usage_and_returns_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = main([], root=_root(tmp_path))

    captured = capsys.readouterr()
    assert _lines(captured.err) == [USAGE]
    assert captured.out == ""
    assert status == 2


def test_an_unreadable_story_form_prints_the_reason_and_returns_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path, form=False)
    path = _story(root, "backlog", GOOD)

    status = main([path], root=root)

    captured = capsys.readouterr()
    prefix = "cannot read factory/story-form.md: "
    assert len(_lines(captured.err)) == 1
    assert captured.err.startswith(prefix)
    assert captured.err.strip() != prefix.strip()
    assert captured.out == ""
    assert status == 2


@pytest.mark.parametrize("content", [None, b"\xff\xfe"], ids=["no-file", "not-utf-8"])
def test_an_unreadable_story_prints_the_reason_and_returns_2_at_once(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], content: bytes | None
) -> None:
    root = _root(tmp_path)
    first = _story(root, "backlog", GOOD)
    broken = f"factory/features/{FEATURE}/backlog/F0002-S0002-y.md"
    if content is not None:
        _story(root, "backlog", content, "F0002-S0002-y.md")
    after = _story(root, "backlog", GOOD, "F0002-S0003-z.md")

    status = main([first, broken, after], root=root)

    captured = capsys.readouterr()
    prefix = f"cannot read {broken}: "
    assert _lines(captured.out) == [f"{first}: ok"]
    assert len(_lines(captured.err)) == 1
    assert captured.err.startswith(prefix)
    assert captured.err.strip() != prefix.strip()
    assert status == 2


def test_a_path_outside_the_work_item_locations_is_reported_and_not_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    path = f"factory/features/{FEATURE}/ongoing/F0002-S0001-x.md"

    status = main([path], root=root)

    captured = capsys.readouterr()
    assert _lines(captured.out) == [f"{path}: {NOT_A_LOCATION}"]
    assert captured.err == ""
    assert status == 1


def test_a_started_story_with_a_bad_front_matter_prints_the_fault_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    path = _story(root, "in-progress", UNKNOWN_KEY + BAD_LAST_CRITERION)

    status = main([path], root=root)

    assert _lines(capsys.readouterr().out) == [f"{path}: unknown key: colour"]
    assert status == 1


@pytest.mark.parametrize("folder", ["in-progress", "done"])
def test_a_started_story_with_front_matter_is_checked_with_its_folder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], folder: str
) -> None:
    root = _root(tmp_path)
    path = _story(root, folder, TWO_RECORDS + WITH_ONE_ENTRY)

    status = main([path], root=root)

    assert _lines(capsys.readouterr().out) == [
        f"{path}: the journal data lists 2 entries but the text shows 1"
    ]
    assert status == 1


def test_a_started_story_as_the_human_moved_it_is_ok(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    started = _story(root, "in-progress", GOOD)
    done = _story(root, "done", GOOD, "F0002-S0002-y.md")

    status = main([started, done], root=root)

    assert _lines(capsys.readouterr().out) == [f"{started}: ok", f"{done}: ok"]
    assert status == 0


def test_a_backlog_story_with_front_matter_is_read_as_a_specification(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    path = _story(root, "backlog", "---\nstage: tests\n---\n" + GOOD)

    status = main([path], root=root)

    assert _lines(capsys.readouterr().out) == [
        f"{path}: a backlog story carries no front matter: stage"
    ]
    assert status == 1


def test_a_place_finding_comes_before_the_fault_of_the_reader(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    path = _story(root, "in-progress", UNKNOWN_KEY + GOOD, "F0003-S0001-x.md")

    status = main([path], root=root)

    assert _lines(capsys.readouterr().out) == [
        f"{path}: the story F0003-S0001 is in the directory of feature F0002",
        f"{path}: unknown key: colour",
    ]
    assert status == 1


def test_the_module_runs_as_a_script_and_prints_the_usage_without_a_path(
    tmp_path: Path,
) -> None:
    result = subprocess.run(  # noqa: S603  (fixed interpreter and module, no input)
        [sys.executable, "-m", "factory.entry.check_story"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )

    assert result.returncode == 2
    assert _lines(result.stderr) == [USAGE]


def test_main_without_arguments_reads_argv_and_the_current_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _root(tmp_path)
    path = _story(root, "backlog", GOOD)
    monkeypatch.setattr(sys, "argv", ["factory-check-story", path])
    monkeypatch.chdir(root)

    status = main()

    assert _lines(capsys.readouterr().out) == [f"{path}: ok"]
    assert status == 0


def test_the_feature_file_is_looked_for_beside_the_story(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path, feature_file=False)
    path = _story(root, "backlog", GOOD)

    missing = main([path], root=root)
    missing_lines = _lines(capsys.readouterr().out)
    (root / "factory" / "features" / FEATURE / "feature.md").write_text(
        "# Feature\n", encoding="utf-8"
    )
    present = main([path], root=root)

    assert missing_lines == [
        f"{path}: the feature file feature.md is missing in factory/features/{FEATURE}"
    ]
    assert missing == 1
    assert _lines(capsys.readouterr().out) == [f"{path}: ok"]
    assert present == 0
