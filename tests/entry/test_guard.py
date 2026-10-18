"""The guard command: settings option, payload on stdin, exit status and stderr."""

import io
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.write_paths import WritePathService
from factory.domain.agent_runs import GuardSettings
from factory.domain.work_item import Claim
from factory.domain.write_paths import PROTECTED_PATHS
from factory.entry.guard import main
from git_support import PIPELINE_YAML
from guard_support import hook_payload

USAGE = "usage: factory-guard --settings <file>"
REFUSAL = "docs/a.md is outside the write paths of this stage."
WORK_ITEM = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"


def _settings_file(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "checkout"
    (root / "src").mkdir(parents=True)
    settings = GuardSettings(
        root=root, write_paths=["src/*"], protected_paths=list(PROTECTED_PATHS)
    )
    path = tmp_path / "guard.json"
    path.write_text(settings.model_dump_json(), encoding="utf-8")
    return root, path


def _run(argv: list[str], payload: str) -> tuple[int, str]:
    stderr = io.StringIO()
    status = main(argv, stdin=io.StringIO(payload), stderr=stderr)
    return status, stderr.getvalue()


def test_an_allowed_payload_returns_0_and_writes_nothing(tmp_path: Path) -> None:
    root, settings = _settings_file(tmp_path)

    status, stderr = _run(["--settings", str(settings)], hook_payload(str(root / "src" / "a.py")))

    assert (status, stderr) == (0, "")


def test_a_refused_payload_returns_2_and_writes_the_refusal(tmp_path: Path) -> None:
    root, settings = _settings_file(tmp_path)

    status, stderr = _run(["--settings", str(settings)], hook_payload(str(root / "docs" / "a.md")))

    assert (status, stderr) == (2, REFUSAL + "\n")


@pytest.mark.parametrize("argv", [[], ["--settings"]])
def test_a_missing_settings_option_returns_2_with_the_usage(
    tmp_path: Path, argv: list[str]
) -> None:
    root, _ = _settings_file(tmp_path)

    status, stderr = _run(argv, hook_payload(str(root / "src" / "a.py")))

    assert status == 2
    assert stderr.strip() == USAGE


@pytest.mark.parametrize("content", [None, "not json"])
def test_a_missing_or_invalid_settings_file_returns_2_naming_the_file(
    tmp_path: Path, content: str | None
) -> None:
    root, _ = _settings_file(tmp_path)
    settings = tmp_path / "other.json"
    if content is not None:
        settings.write_text(content, encoding="utf-8")

    status, stderr = _run(["--settings", str(settings)], hook_payload(str(root / "src" / "a.py")))

    assert status == 2
    assert str(settings) in stderr


def test_a_rewritten_definition_in_the_work_tree_changes_no_verdict(
    tmp_path: Path, boundaries: Boundaries, checkout: GitCli
) -> None:
    commit = checkout.resolve("origin/main")
    assert commit is not None
    claim = Claim(
        instance="factory-1",
        stage="tests",
        started_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
        lease_duration=30,
    )
    settings = WritePathService(boundaries).at(StageStart(commit=commit, claim=claim), WORK_ITEM)
    settings_file = tmp_path / "guard.json"
    settings_file.write_text(settings.model_dump_json(), encoding="utf-8")
    payload = hook_payload(str(boundaries.checkout / "docs" / "a.md"))
    argv = ["--settings", str(settings_file)]

    before = _run(argv, payload)
    (boundaries.checkout / "factory" / "pipeline.yml").write_text(
        PIPELINE_YAML.replace('tester: {write_paths: ["tests/*"]}', 'tester: {write_paths: ["*"]}'),
        encoding="utf-8",
    )
    after = _run(argv, payload)

    assert before == (2, REFUSAL + "\n")
    assert after == before


@pytest.mark.parametrize(
    ("relative", "status", "stderr"),
    [("src/a.py", 0, ""), ("docs/a.md", 2, REFUSAL)],
)
def test_the_module_runs_as_the_guard_command(
    tmp_path: Path, relative: str, status: int, stderr: str
) -> None:
    root, settings = _settings_file(tmp_path)

    result = subprocess.run(  # noqa: S603  (fixed interpreter and module)
        [sys.executable, "-m", "factory.entry.guard", "--settings", str(settings)],
        input=hook_payload(str(root / relative)),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == status
    assert result.stderr.strip() == stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    ("relative", "status", "stderr"),
    [("src/a.py", 0, ""), ("docs/a.md", 2, REFUSAL + "\n")],
)
def test_main_without_arguments_reads_the_process_streams(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: str, status: int, stderr: str
) -> None:
    root, settings = _settings_file(tmp_path)
    patched_stderr = io.StringIO()
    monkeypatch.setattr(sys, "argv", ["factory-guard", "--settings", str(settings)])
    monkeypatch.setattr(sys, "stdin", io.StringIO(hook_payload(str(root / relative))))
    monkeypatch.setattr(sys, "stderr", patched_stderr)

    returned = main()

    assert returned == status
    assert patched_stderr.getvalue() == stderr


def test_a_path_with_a_nul_character_returns_2(tmp_path: Path) -> None:
    root, settings = _settings_file(tmp_path)
    file_path = f"{root}/src/a\x00.py"

    status, stderr = _run(["--settings", str(settings)], hook_payload(file_path))

    assert (status, stderr) == (2, f"{file_path} is outside the checkout.\n")
