"""The image's entrypoint, run with `sh` against stub executables in a temporary layout."""

import re
import shutil
from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, ProcessResult, run_process

ROOT = Path(__file__).parent.parent
ENTRYPOINT = ROOT / "image" / "entrypoint.sh"
STAMP = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ "
STAMPED = re.compile(rf"{STAMP}(?P<text>.*)")
SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"
AGENT_TEXT = "---\nmodel: sonnet\n---\nDo the work.\n"
SETTINGS_TEXT = '{"permissions": {}}\n'


class Layout:
    """The directories of one entrypoint run under `tmp_path`, and stubs that record calls."""

    def __init__(self, root: Path) -> None:
        self.opt = root / "opt"
        self.home = root / "user-home"
        self.claude_home = root / "claude-home"
        self.state = root / "state"
        self.bin = root / "bin"
        self.records = root / "records"
        for directory in (self.opt / "claude" / "agents", self.home, self.bin, self.records):
            directory.mkdir(parents=True)
        (self.opt / "claude" / "agents" / "coder.md").write_text(AGENT_TEXT, encoding="utf-8")
        (self.opt / "claude" / "settings.json").write_text(SETTINGS_TEXT, encoding="utf-8")
        self._stub(
            "python",
            f"printf '%s\\n' \"$@\" > '{self.records}/python-args'\npwd > '{self.records}/cwd'",
        )
        self._stub("git", f"printf '%s\\n' \"$*\" >> '{self.records}/git-calls'")

    def _stub(self, name: str, body: str) -> None:
        path = self.bin / name
        path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        path.chmod(0o755)

    def environment(
        self, *, claude_home: bool = True, instance: str | None = None
    ) -> dict[str, str]:
        environment = {
            "PATH": f"{self.bin}:{SYSTEM_PATH}",
            "HOME": str(self.home),
            "FACTORY_OPT": str(self.opt),
            "FACTORY_STATE": str(self.state),
        }
        if claude_home:
            environment["FACTORY_CLAUDE_HOME"] = str(self.claude_home)
        if instance is not None:
            environment["FACTORY_INSTANCE"] = instance
        return environment

    def run(self, environment: dict[str, str] | None = None) -> ProcessResult:
        return run_process(
            ProcessRequest(
                argv=["sh", str(ENTRYPOINT)],
                cwd=self.home,
                env=self.environment() if environment is None else environment,
            )
        )

    def python_args(self) -> list[str] | None:
        path = self.records / "python-args"
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else None


@pytest.fixture
def layout(tmp_path: Path) -> Layout:
    """Return the image layout, homes, state and stubs of one run under `tmp_path`."""
    return Layout(tmp_path)


def _texts(output: str) -> list[str]:
    texts = []
    for line in output.splitlines():
        match = STAMPED.fullmatch(line)
        assert match is not None, f"line without a time stamp: {line!r}"
        texts.append(match["text"])
    return texts


@pytest.mark.parametrize(("instance", "named"), [(None, "unset"), ("factory-1", "factory-1")])
def test_every_line_of_a_full_run_is_time_stamped(
    layout: Layout, instance: str | None, named: str
) -> None:
    result = layout.run(layout.environment(instance=instance))

    assert result.exit_status == 0
    assert _texts(result.stderr) + _texts(result.stdout) == [
        f"installed agents and settings into {layout.claude_home}",
        f"prepared {layout.state}/runs",
        f"starting instance {named}",
    ]


def test_the_script_writes_output_only_through_its_log_function() -> None:
    lines = ENTRYPOINT.read_text(encoding="utf-8").splitlines()

    writing = [line for line in lines if re.search(r"\b(?:echo|printf)\b", line)]

    assert writing
    assert all(line.strip().startswith("log()") for line in writing)


def test_the_agents_are_replaced_by_the_images_and_the_settings_copied(layout: Layout) -> None:
    stale = layout.claude_home / "agents" / "retired.md"
    stale.parent.mkdir(parents=True)
    stale.write_text(AGENT_TEXT, encoding="utf-8")

    result = layout.run()

    assert result.exit_status == 0
    assert sorted(path.name for path in (layout.claude_home / "agents").iterdir()) == ["coder.md"]
    assert (layout.claude_home / "agents" / "coder.md").read_text(encoding="utf-8") == AGENT_TEXT
    assert (layout.claude_home / "settings.json").read_text(encoding="utf-8") == SETTINGS_TEXT


@pytest.mark.parametrize("missing", ["claude/agents", "claude/settings.json"])
def test_a_missing_image_file_ends_the_run_with_one_line_before_the_instance(
    layout: Layout, missing: str
) -> None:
    path = layout.opt / missing
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()

    result = layout.run()

    assert result.exit_status == 1
    assert result.stdout == ""
    texts = _texts(result.stderr)
    assert len(texts) == 1
    assert str(path) in texts[0]
    assert layout.python_args() is None


def test_without_a_claude_home_the_agents_go_into_the_users_home(layout: Layout) -> None:
    result = layout.run(layout.environment(claude_home=False))

    assert result.exit_status == 0
    claude = layout.home / ".claude"
    assert (claude / "agents" / "coder.md").read_text(encoding="utf-8") == AGENT_TEXT
    assert (claude / "settings.json").read_text(encoding="utf-8") == SETTINGS_TEXT


@pytest.mark.parametrize("existing_mode", [None, 0o755])
def test_the_runs_directory_gets_the_mode_2750(layout: Layout, existing_mode: int | None) -> None:
    runs = layout.state / "runs"
    if existing_mode is not None:
        runs.mkdir(parents=True)
        runs.chmod(existing_mode)

    result = layout.run()

    assert result.exit_status == 0
    stat = run_process(ProcessRequest(argv=["stat", "-c", "%a", str(runs)], cwd=layout.home))
    assert stat.stdout.strip() == "2750"


def test_the_instance_starts_in_the_opt_directory(layout: Layout) -> None:
    result = layout.run()

    assert result.exit_status == 0
    recorded = (layout.records / "cwd").read_text(encoding="utf-8").strip()
    assert Path(recorded).resolve() == layout.opt.resolve()


def test_the_entrypoint_hands_over_to_the_run_module(layout: Layout) -> None:
    result = layout.run()

    assert result.exit_status == 0
    assert layout.python_args() == ["-m", "factory.entry.run"]


def test_the_entrypoint_sets_no_git_configuration(layout: Layout) -> None:
    result = layout.run()

    assert result.exit_status == 0
    assert "git config" not in ENTRYPOINT.read_text(encoding="utf-8")
    assert not (layout.records / "git-calls").exists()
