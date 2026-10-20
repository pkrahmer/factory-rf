"""The make class, against real Makefiles written into a temporary directory."""

import time
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters import make_commands
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.process import ProcessResult
from factory.application.project_commands import ProjectCommands
from factory.domain.checks import TargetTime
from factory.domain.errors import ProjectCommandError
from factory.domain.kill_points import KillPoint, KillPoints
from process_support import is_gone
from run_process_recorder import Recorder
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

LIMIT = timedelta(seconds=30)


def _commands(directory: Path, *targets: tuple[str, str]) -> MakeProjectCommands:
    makefile = "".join(f"{name}:\n\t{recipe}\n\n" for name, recipe in targets)
    (directory / "Makefile").write_text(makefile, encoding="utf-8")
    return MakeProjectCommands(directory)


def test_succeeding_target_passes(tmp_path: Path) -> None:
    commands = _commands(tmp_path, ("check", '@echo "check: green"'))

    result = commands.run("check", time_limit=LIMIT)

    assert result.status == "passed"
    assert result.exit_status == 0
    assert result.command == "check"
    assert result.passed is True


@pytest.mark.parametrize("recipe_status", [2, 3])
def test_failing_recipe_fails_with_the_status_make_sets(tmp_path: Path, recipe_status: int) -> None:
    commands = _commands(tmp_path, ("lint", f"@exit {recipe_status}"))

    result = commands.run("lint", time_limit=LIMIT)

    assert result.status == "failed"
    assert result.exit_status == 2


def test_missing_target_is_a_failed_command(tmp_path: Path) -> None:
    commands = _commands(tmp_path, ("check", "@true"))

    result = commands.run("nope", time_limit=LIMIT)

    assert result.status == "failed"
    assert result.exit_status == 2


def test_command_reaching_its_time_limit_is_killed(tmp_path: Path) -> None:
    pid_file = tmp_path / "sleep.pid"
    commands = _commands(tmp_path, ("slow", f"@sleep 60 & echo $$! > {pid_file}; wait"))
    start = time.monotonic()

    # ROOMY_LIMIT: the shell must start its grandchild and write the pid file before the kill.
    result = commands.run("slow", time_limit=ROOMY_LIMIT)

    assert time.monotonic() - start < ROOMY_BOUND_SECONDS
    assert result.status == "time_limit"
    assert result.exit_status is None
    assert is_gone(int(pid_file.read_text(encoding="utf-8")))


@pytest.mark.parametrize("time_limit", [timedelta(0), timedelta(seconds=-1)])
def test_time_limit_of_zero_or_less_is_rejected(tmp_path: Path, time_limit: timedelta) -> None:
    commands = _commands(tmp_path, ("check", "@true"))

    with pytest.raises(ValueError, match="time_limit"):
        commands.run("check", time_limit=time_limit)


def test_time_limit_of_one_second_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = Recorder()
    recorder.results.append(
        ProcessResult(exit_status=0, stdout="", stderr="", timed_out=False, duration=timedelta(0))
    )
    monkeypatch.setattr(make_commands, "run_process", recorder)
    commands = _commands(tmp_path, ("check", "@true"))

    assert commands.run("check", time_limit=timedelta(seconds=1)).passed is True
    [request] = recorder.requests
    assert request.time_limit == timedelta(seconds=1)


@pytest.mark.parametrize(
    ("printed", "first_kept"),
    [(29, 1), (30, 1), (31, 2), (40, 11)],
)
def test_output_tail_keeps_the_last_thirty_lines(
    tmp_path: Path, printed: int, first_kept: int
) -> None:
    commands = _commands(tmp_path, ("count", f"@seq 1 {printed}"))

    result = commands.run("count", time_limit=LIMIT)

    assert result.output_tail.splitlines() == [str(n) for n in range(first_kept, printed + 1)]


def test_output_tail_merges_stderr_in_the_order_written(tmp_path: Path) -> None:
    commands = _commands(tmp_path, ("mixed", "@echo a; echo b >&2; echo c"))

    result = commands.run("mixed", time_limit=LIMIT)

    assert result.output_tail.splitlines() == ["a", "b", "c"]


def test_last_line_skips_trailing_blank_lines(tmp_path: Path) -> None:
    commands = _commands(tmp_path, ("check", "@echo done; echo; echo '   '; echo"))

    assert commands.run("check", time_limit=LIMIT).last_line == "done"


def test_last_line_is_empty_without_output(tmp_path: Path) -> None:
    commands = _commands(tmp_path, ("check", "@true"))

    assert commands.run("check", time_limit=LIMIT).last_line == ""


def test_last_line_skips_the_lines_make_writes(tmp_path: Path) -> None:
    commands = _commands(
        tmp_path,
        ("lint", '@echo "lint: red"; exit 3'),
        ("nested", "@echo \"lint: red\"; echo 'make[1]: Leaving directory'"),
    )

    failed = commands.run("lint", time_limit=LIMIT)
    nested = commands.run("nested", time_limit=LIMIT)

    assert "make: *** [Makefile:2: lint] Error 3" in failed.output_tail.splitlines()
    assert failed.last_line == "lint: red"
    assert nested.last_line == "lint: red"


def test_duration_is_the_time_the_command_ran(tmp_path: Path) -> None:
    commands = _commands(tmp_path, ("pause", "@sleep 0.3"))

    result = commands.run("pause", time_limit=LIMIT)

    assert timedelta(seconds=0.3) <= result.duration < LIMIT


def test_command_runs_with_the_current_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PROBE", "probe-value")
    commands = _commands(tmp_path, ("probe", "@echo $$PROBE"))

    assert commands.run("probe", time_limit=LIMIT).last_line == "probe-value"


def test_run_reaches_no_kill_point(tmp_path: Path, kill_points: KillPoints) -> None:
    (tmp_path / "Makefile").write_text("check:\n\t@true\n", encoding="utf-8")
    commands = MakeProjectCommands(tmp_path, kill_points)
    for point in KillPoint:
        kill_points.arm(point)

    result = commands.run("check", time_limit=LIMIT)

    assert result.passed is True
    assert {point: kill_points.reached(point) for point in KillPoint} == dict.fromkeys(KillPoint, 0)


@pytest.mark.parametrize("command", ["check; rm -rf x", "Check", "-f"])
def test_invalid_command_name_is_refused_before_starting(tmp_path: Path, command: str) -> None:
    marker = tmp_path / "started"
    commands = _commands(tmp_path, ("check", f"@touch {marker}"), ("Check", f"@touch {marker}"))

    with pytest.raises(ProjectCommandError) as caught:
        commands.run(command, time_limit=LIMIT)

    assert caught.value.command == command
    assert not marker.exists()


def test_executable_that_cannot_start_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text("check:\n\t@true\n", encoding="utf-8")
    commands = MakeProjectCommands(tmp_path, executable="/no/such/make")

    with pytest.raises(ProjectCommandError) as caught:
        commands.run("check", time_limit=LIMIT)

    assert caught.value.command == "check"
    assert caught.value.detail != ""


def test_make_class_inherits_the_project_commands_interface() -> None:
    assert issubclass(MakeProjectCommands, ProjectCommands)


def test_outer_make_variables_do_not_reach_the_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAKELEVEL", "1")
    monkeypatch.setenv("MAKEFLAGS", "w")
    monkeypatch.setenv("MFLAGS", "-w")
    commands = _commands(tmp_path, ("level", "@echo ok; echo $(MAKELEVEL)"))

    result = commands.run("level", time_limit=LIMIT)

    assert result.output_tail.splitlines() == ["ok", "0"]


def test_command_name_with_a_trailing_newline_is_refused_before_starting(tmp_path: Path) -> None:
    marker = tmp_path / "started"
    commands = _commands(tmp_path, ("check", f"@touch {marker}"))

    with pytest.raises(ProjectCommandError):
        commands.run("check\n", time_limit=LIMIT)

    assert not marker.exists()


def test_targets_are_read_from_the_whole_output(tmp_path: Path) -> None:
    commands = _commands(
        tmp_path,
        (
            "check",
            '@echo "lint: green (0.5 s)"; seq 1 40; '
            'echo "test: green (2.0 s)"; echo "check: green"',
        ),
    )

    result = commands.run("check", time_limit=LIMIT)

    assert "lint: green (0.5 s)" not in result.output_tail.splitlines()
    assert result.targets == [
        TargetTime(target="lint", seconds=0.5),
        TargetTime(target="test", seconds=2.0),
    ]


def test_target_printing_no_green_line_has_no_targets(tmp_path: Path) -> None:
    commands = _commands(tmp_path, ("check", '@echo "check: green"'))

    assert commands.run("check", time_limit=LIMIT).targets == []
