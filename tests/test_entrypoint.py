"""The image's entrypoint, run with `sh` against stub executables in a temporary layout."""

import re
import shutil
from pathlib import Path

import pytest

from entrypoint_support import AGENT_TEXT, ENTRYPOINT, SETTINGS_TEXT, Layout, texts
from factory.adapters.process import ProcessRequest, run_process


@pytest.mark.parametrize(("instance", "named"), [(None, "unset"), ("factory-1", "factory-1")])
def test_every_line_of_a_full_run_is_time_stamped(
    image_layout: Layout, instance: str | None, named: str
) -> None:
    result = image_layout.run(image_layout.environment(instance=instance))

    assert result.exit_status == 0
    assert texts(result.stderr) + texts(result.stdout) == [
        f"installed agents and settings into {image_layout.claude_home}",
        f"prepared {image_layout.state}/runs",
        f"starting instance {named}",
    ]


def test_the_script_writes_output_only_through_its_log_function() -> None:
    lines = ENTRYPOINT.read_text(encoding="utf-8").splitlines()

    writing = [line for line in lines if re.search(r"\b(?:echo|printf)\b", line)]

    assert writing
    assert all(line.strip().startswith("log()") for line in writing)


def test_the_agents_are_replaced_by_the_images_and_the_settings_copied(
    image_layout: Layout,
) -> None:
    stale = image_layout.claude_home / "agents" / "retired.md"
    stale.parent.mkdir(parents=True)
    stale.write_text(AGENT_TEXT, encoding="utf-8")

    result = image_layout.run()

    assert result.exit_status == 0
    assert sorted(path.name for path in (image_layout.claude_home / "agents").iterdir()) == [
        "coder.md"
    ]
    assert (image_layout.claude_home / "agents" / "coder.md").read_text(
        encoding="utf-8"
    ) == AGENT_TEXT
    assert (image_layout.claude_home / "settings.json").read_text(encoding="utf-8") == SETTINGS_TEXT


@pytest.mark.parametrize("missing", ["claude/agents", "claude/settings.json"])
def test_a_missing_image_file_ends_the_run_with_one_line_before_the_instance(
    image_layout: Layout, missing: str
) -> None:
    path = image_layout.opt / missing
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()

    result = image_layout.run()

    assert result.exit_status == 1
    assert result.stdout == ""
    lines = texts(result.stderr)
    assert len(lines) == 1
    assert str(path) in lines[0]
    assert image_layout.python_args() is None


def test_without_a_claude_home_the_agents_go_into_the_users_home(image_layout: Layout) -> None:
    result = image_layout.run(image_layout.environment(claude_home=False))

    assert result.exit_status == 0
    claude = image_layout.home / ".claude"
    assert (claude / "agents" / "coder.md").read_text(encoding="utf-8") == AGENT_TEXT
    assert (claude / "settings.json").read_text(encoding="utf-8") == SETTINGS_TEXT


@pytest.mark.parametrize("existing_mode", [None, 0o755])
def test_the_runs_directory_gets_the_mode_2750(
    image_layout: Layout, existing_mode: int | None
) -> None:
    runs = image_layout.state / "runs"
    if existing_mode is not None:
        runs.mkdir(parents=True)
        runs.chmod(existing_mode)

    result = image_layout.run()

    assert result.exit_status == 0
    stat = run_process(ProcessRequest(argv=["stat", "-c", "%a", str(runs)], cwd=image_layout.home))
    assert stat.stdout.strip() == "2750"


def test_the_instance_starts_in_the_opt_directory(image_layout: Layout) -> None:
    result = image_layout.run()

    assert result.exit_status == 0
    recorded = (image_layout.records / "cwd").read_text(encoding="utf-8").strip()
    assert Path(recorded).resolve() == image_layout.opt.resolve()


def test_the_entrypoint_hands_over_to_the_run_module(image_layout: Layout) -> None:
    result = image_layout.run()

    assert result.exit_status == 0
    assert image_layout.python_args() == ["-m", "factory.entry.run"]


def test_the_entrypoint_sets_no_git_configuration(image_layout: Layout) -> None:
    result = image_layout.run()

    assert result.exit_status == 0
    assert "git config" not in ENTRYPOINT.read_text(encoding="utf-8")
    assert not (image_layout.records / "git-calls").exists()
