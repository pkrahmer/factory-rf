"""The demo check: the parts of each demo, its pipeline definition, its stories, the index."""

import shutil
from pathlib import Path

import pytest

from factory.entry.check_demos import check_demos, main
from git_support import PIPELINE_YAML, STORY_FORM

GOOD_STORY = """\
# A story

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.

## Journal
"""
NO_SMOKE_TEST = GOOD_STORY.replace("## Smoke test\n\n```bash\ntrue\n```\nExpect: nothing.\n\n", "")
JOURNAL_ENTRY = "1. 2026-10-17 human: created."
WITH_ENTRY = GOOD_STORY + "\n" + JOURNAL_ENTRY + "\n"
BAD_FRONT_MATTER = "---\na: [\n---\n" + GOOD_STORY
FIRST = "features/F0001-x/backlog/F0001-S0001-first.md"
SECOND = "features/F0001-x/backlog/F0001-S0002-second.md"
FEATURE_FILE = "features/F0001-x/feature.md"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _index(root: Path, *names: str) -> None:
    lines = "".join(f"- `{name}/`: a demo.\n" for name in names)
    _write(root / "demo" / "README.md", "# Demos\n\n" + lines)


def _demo(root: Path, name: str = "todo") -> Path:
    demo = root / "demo" / name
    _write(demo / "README.md", f"# The {name} demo\n")
    _write(demo / "project" / "factory" / "pipeline.yml", PIPELINE_YAML)
    _write(demo / "project" / "factory" / "story-form.md", STORY_FORM)
    _write(demo / FEATURE_FILE, "# Feature\n")
    _write(demo / FIRST, GOOD_STORY)
    return demo


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """Return a root with the complete demo `todo` and an index that names it."""
    _demo(tmp_path)
    _index(tmp_path, "todo")
    return tmp_path


def _lines(capsys: pytest.CaptureFixture[str]) -> list[str]:
    return capsys.readouterr().out.splitlines()


def test_a_root_without_demos_gives_no_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert check_demos(tmp_path) == []

    status = main(["--root", str(tmp_path)])

    assert _lines(capsys) == ["demos ok"]
    assert status == 0


def test_a_complete_demo_named_in_the_index_gives_no_finding(root: Path) -> None:
    assert check_demos(root) == []


def test_a_missing_index_is_a_finding(root: Path) -> None:
    (root / "demo" / "README.md").unlink()

    assert check_demos(root) == ["demo/README.md: missing"]


def test_an_index_that_does_not_name_the_demo_is_a_finding(root: Path) -> None:
    _write(root / "demo" / "README.md", "# Demos\n\n- `other/`: a demo.\n- todo\n")

    assert check_demos(root) == ["demo/README.md: names no demo 'todo'"]


@pytest.mark.parametrize(
    ("part", "finding"),
    [
        pytest.param("README.md", "demo/todo: missing README.md", id="readme"),
        pytest.param("project", "demo/todo: missing project/", id="project"),
        pytest.param("features", "demo/todo: missing features/", id="features"),
    ],
)
def test_a_missing_part_of_a_demo_is_the_one_finding(root: Path, part: str, finding: str) -> None:
    target = root / "demo" / "todo" / part
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()

    assert check_demos(root) == [finding]


def test_a_pipeline_definition_with_a_repeated_key_is_a_finding(root: Path) -> None:
    _write(
        root / "demo" / "todo" / "project" / "factory" / "pipeline.yml",
        PIPELINE_YAML + "attempts_cap: 3\n",
    )

    findings = check_demos(root)

    assert len(findings) == 1
    assert findings[0].startswith("demo/todo/project/factory/pipeline.yml: not valid YAML")


def test_a_missing_pipeline_definition_is_a_finding(root: Path) -> None:
    (root / "demo" / "todo" / "project" / "factory" / "pipeline.yml").unlink()

    assert check_demos(root) == ["demo/todo: missing project/factory/pipeline.yml"]


def test_without_the_story_form_no_story_is_checked(root: Path) -> None:
    demo = root / "demo" / "todo"
    (demo / "project" / "factory" / "story-form.md").unlink()
    _write(demo / FIRST, NO_SMOKE_TEST)

    assert check_demos(root) == ["demo/todo: missing project/factory/story-form.md"]


def test_a_story_without_its_smoke_test_gives_the_story_check_finding(root: Path) -> None:
    _write(root / "demo" / "todo" / FIRST, NO_SMOKE_TEST)

    assert check_demos(root) == [f"demo/todo/{FIRST}: missing section: ## Smoke test"]


def test_a_story_in_the_folder_of_another_feature_gives_the_place_finding(root: Path) -> None:
    demo = root / "demo" / "todo"
    (demo / FIRST).unlink()
    other = "features/F0001-x/backlog/F0002-S0001-other.md"
    _write(demo / other, GOOD_STORY)

    assert check_demos(root) == [
        f"demo/todo/{other}: the story F0002-S0001 is in the directory of feature F0001"
    ]


def test_a_feature_folder_without_its_feature_file_gives_the_place_finding(root: Path) -> None:
    (root / "demo" / "todo" / FEATURE_FILE).unlink()

    assert check_demos(root) == [
        f"demo/todo/{FIRST}: the feature file feature.md is missing in factory/features/F0001-x"
    ]


@pytest.mark.parametrize(
    "stray",
    [
        pytest.param("features/F0001-x/in-progress/F0001-S0002-y.md", id="started-story"),
        pytest.param("features/notes.txt", id="loose-file"),
        pytest.param("features/F0001-x/backlog/notes.txt", id="backlog-file-not-md"),
        pytest.param("features/F0001-x/notes.md", id="feature-folder-file-not-feature-md"),
    ],
)
def test_a_file_that_is_no_feature_file_or_backlog_story_is_a_finding(
    root: Path, stray: str
) -> None:
    _write(root / "demo" / "todo" / stray, GOOD_STORY)

    assert check_demos(root) == [f"demo/todo/{stray}: not a feature file or a backlog story"]


def test_findings_of_two_demos_come_in_name_order_and_main_prints_them(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (_demo(tmp_path, "b") / "README.md").unlink()
    demo_a = _demo(tmp_path, "a")
    shutil.rmtree(demo_a / "features")
    _index(tmp_path, "a", "b")
    expected = ["demo/a: missing features/", "demo/b: missing README.md"]

    assert check_demos(tmp_path) == expected

    status = main(["--root", str(tmp_path)])

    assert _lines(capsys) == expected
    assert status == 1


def test_a_loose_file_and_a_hidden_folder_under_demo_are_no_demos(root: Path) -> None:
    _write(root / "demo" / "notes.txt", "Notes.\n")
    _write(root / "demo" / ".cache" / "entry", "cached\n")

    assert check_demos(root) == []


def test_story_findings_come_in_path_order_and_carry_their_line(root: Path) -> None:
    demo = root / "demo" / "todo"
    _write(demo / FIRST, WITH_ENTRY)
    _write(demo / SECOND, NO_SMOKE_TEST)
    line = WITH_ENTRY.splitlines().index(JOURNAL_ENTRY) + 1

    assert check_demos(root) == [
        f"demo/todo/{FIRST}:{line}: a backlog story carries no journal entries",
        f"demo/todo/{SECOND}: missing section: ## Smoke test",
    ]


def test_a_story_with_front_matter_that_is_not_yaml_is_one_finding(root: Path) -> None:
    _write(root / "demo" / "todo" / FIRST, BAD_FRONT_MATTER)

    assert check_demos(root) == [f"demo/todo/{FIRST}: front matter is not valid YAML"]


def test_the_root_defaults_to_the_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _demo(tmp_path)
    monkeypatch.chdir(tmp_path)

    status = main([])

    assert _lines(capsys) == ["demo/README.md: missing"]
    assert status == 1
