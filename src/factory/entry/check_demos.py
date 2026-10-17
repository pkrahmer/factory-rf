"""The demo check command: the parts, pipeline definition, stories and index of every demo."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from factory.application.files import PipelineDefinitionReader, WorkItemReader
from factory.domain.errors import PipelineDefinitionInvalid
from factory.domain.paths import (
    FEATURE_FILE_NAME,
    FEATURES_DIRECTORY,
    PIPELINE_DEFINITION_FILE,
    STORY_FORM_FILE,
)
from factory.entry.check_story import backlog_story_findings, finding_line
from factory.entry.wiring import build_pipeline_definition_reader, build_work_item_reader

_PROGRAM = "check-demos"
_DEMOS = "demo"
_README = "README.md"
_PROJECT = "project"
_FEATURES = "features"
_BACKLOG = "backlog"
_CLEAN = 0
_FINDINGS = 1


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _demo_folders(demos: Path) -> list[Path]:
    return sorted(
        entry for entry in demos.iterdir() if entry.is_dir() and not entry.name.startswith(".")
    )


def _index_findings(index: str | None, name: str) -> list[str]:
    if index is None or any(f"`{name}/`" in line for line in index.splitlines()):
        return []
    return [f"{_DEMOS}/{_README}: names no demo '{name}'"]


def _part_findings(demo: Path, label: str) -> list[str]:
    findings: list[str] = []
    if not (demo / _README).is_file():
        findings.append(f"{label}: missing {_README}")
    for folder in (_PROJECT, _FEATURES):
        if not (demo / folder).is_dir():
            findings.append(f"{label}: missing {folder}/")
    return findings


def _pipeline_findings(reader: PipelineDefinitionReader, project: Path, label: str) -> list[str]:
    path = project / PIPELINE_DEFINITION_FILE
    if not path.is_file():
        return [f"{label}: missing {_PROJECT}/{PIPELINE_DEFINITION_FILE}"]
    try:
        reader.parse(_read(path))
    except PipelineDefinitionInvalid as error:
        return [f"{label}/{_PROJECT}/{PIPELINE_DEFINITION_FILE}: {error.fault}"]
    return []


def _story_findings(
    reader: WorkItemReader, features: Path, relative: str, form: str, label: str
) -> list[str]:
    feature, _, story = relative.split("/")
    # The story is checked at the path it will have once the demo is a project.
    path = f"{FEATURES_DIRECTORY}/{feature}/{_BACKLOG}/{story}"
    findings = backlog_story_findings(
        reader,
        path,
        _read(features / relative),
        form,
        feature_file_exists=(features / feature / FEATURE_FILE_NAME).is_file(),
    )
    return [finding_line(f"{label}/{_FEATURES}/{relative}", finding) for finding in findings]


def _is_feature_file(parts: Sequence[str]) -> bool:
    return len(parts) == 2 and parts[1] == FEATURE_FILE_NAME


def _is_backlog_story(parts: Sequence[str]) -> bool:
    return len(parts) == 3 and parts[1] == _BACKLOG and parts[2].endswith(".md")


def _features_findings(reader: WorkItemReader, features: Path, form: str, label: str) -> list[str]:
    findings: list[str] = []
    files = sorted(path.relative_to(features) for path in features.rglob("*") if path.is_file())
    for relative in files:
        if _is_feature_file(relative.parts):
            continue
        if _is_backlog_story(relative.parts):
            findings += _story_findings(reader, features, relative.as_posix(), form, label)
        else:
            findings.append(
                f"{label}/{_FEATURES}/{relative.as_posix()}: not a feature file or a backlog story"
            )
    return findings


def _demo_findings(
    pipeline_reader: PipelineDefinitionReader,
    story_reader: WorkItemReader,
    demo: Path,
    index: str | None,
) -> list[str]:
    label = f"{_DEMOS}/{demo.name}"
    findings = [*_index_findings(index, demo.name), *_part_findings(demo, label)]
    project = demo / _PROJECT
    if not project.is_dir():
        return findings
    findings += _pipeline_findings(pipeline_reader, project, label)
    form_path = project / STORY_FORM_FILE
    if not form_path.is_file():
        return [*findings, f"{label}: missing {_PROJECT}/{STORY_FORM_FILE}"]
    features = demo / _FEATURES
    if features.is_dir():
        findings += _features_findings(story_reader, features, _read(form_path), label)
    return findings


def check_demos(root: Path) -> list[str]:
    """The findings of every demo under `root / "demo"`, one line each, in path order."""
    demos = root / _DEMOS
    if not demos.is_dir():
        return []
    index_path = demos / _README
    index = _read(index_path) if index_path.is_file() else None
    findings = [] if index is not None else [f"{_DEMOS}/{_README}: missing"]
    pipeline_reader = build_pipeline_definition_reader()
    story_reader = build_work_item_reader()
    for demo in _demo_folders(demos):
        findings += _demo_findings(pipeline_reader, story_reader, demo, index)
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    """Print `demos ok` and return 0, or print one line per finding and return 1."""
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    root: Path = arguments.root
    findings = check_demos(root)
    if not findings:
        print("demos ok")
        return _CLEAN
    for finding in findings:
        print(finding)
    return _FINDINGS


if __name__ == "__main__":
    raise SystemExit(main())
