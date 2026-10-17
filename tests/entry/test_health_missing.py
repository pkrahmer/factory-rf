"""The health check reads a missing health file as not healthy, a damaged one as healthy."""

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.process import ProcessRequest, run_process
from factory.domain.stops import HealthStatus
from factory.entry.health import main
from factory.entry.wiring import health_file


def _nothing(_state_directory: Path) -> None:
    pass


def _empty(state_directory: Path) -> None:
    JsonHealthStatusFile(state_directory / "health.json").write(HealthStatus())


def _damaged(state_directory: Path) -> None:
    (state_directory / "health.json").write_text("not json", encoding="utf-8")


@pytest.mark.parametrize(
    ("prepare", "expected_line", "expected_status"),
    [
        pytest.param(
            _nothing, "no health status: {folder}/health.json is missing", 1, id="missing"
        ),
        pytest.param(_empty, "healthy", 0, id="no-stop"),
        pytest.param(_damaged, "healthy", 0, id="damaged"),
    ],
)
def test_only_a_missing_health_file_is_not_healthy(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    prepare: Callable[[Path], None],
    expected_line: str,
    expected_status: int,
) -> None:
    prepare(tmp_path)

    status = main(["--state-directory", str(tmp_path)])

    assert capsys.readouterr().out == expected_line.format(folder=tmp_path) + "\n"
    assert status == expected_status


def test_a_given_store_is_read_when_the_state_directory_has_no_health_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    store = JsonHealthStatusFile(tmp_path / "elsewhere" / "status.json")
    store.write(HealthStatus())

    status = main(["--state-directory", str(tmp_path)], store=store)

    assert capsys.readouterr().out == "healthy\n"
    assert status == 0


def test_the_module_run_as_a_process_exits_one_without_a_health_file(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()

    result = run_process(
        ProcessRequest(
            argv=[sys.executable, "-m", "factory.entry.health", "--state-directory", str(state)],
            cwd=tmp_path,
        )
    )

    assert result.exit_status == 1


def test_the_health_file_lies_in_the_state_directory(tmp_path: Path) -> None:
    assert health_file(tmp_path) == tmp_path / "health.json"
