"""The machine's setup script, run for real up to its argument and root checks."""

from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, run_process
from vm_support import REQUIRED, SETUP, SYSTEM_PATH, entries, run_setup

OPTIONS = (
    "--device",
    "--repository-url",
    "--instance",
    "--pool",
    "--quota",
    "--ref",
    "--image",
    "--runtime",
    "--sudoers",
)


def test_the_script_parses_and_starts_with_its_shebang_and_set_eu(tmp_path: Path) -> None:
    result = run_process(ProcessRequest(argv=["sh", "-n", str(SETUP)], cwd=tmp_path))

    assert result.exit_status == 0, result.stderr
    lines = SETUP.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "#!/bin/sh"
    commands = [line for line in lines if line.strip() and not line.strip().startswith("#")]
    assert commands[0] == "set -eu"


@pytest.mark.parametrize(
    "words",
    [
        pytest.param([], id="no-words"),
        pytest.param(["--device", "/dev/null"], id="device-alone"),
        pytest.param(["--repository-url", "https://example.invalid/r.git"], id="url-alone"),
        pytest.param(["--device"], id="device-without-value"),
        pytest.param([*REQUIRED, "--bogus"], id="unknown-word"),
        pytest.param([*REQUIRED, "--runtime", "vim"], id="unknown-runtime"),
    ],
)
def test_an_argument_fault_prints_the_usage_and_exits_2(tmp_path: Path, words: list[str]) -> None:
    before = entries(tmp_path)

    result = run_setup(tmp_path, words)

    assert result.exit_status == 2
    assert result.stdout == ""
    lines = result.stderr.splitlines()
    assert lines[0].startswith("setup.sh: ")
    assert lines[1].startswith("usage: setup.sh")
    assert [option for option in OPTIONS if option not in lines[1]] == []
    assert entries(tmp_path) == before


def test_help_prints_the_usage_to_standard_output_and_exits_0(tmp_path: Path) -> None:
    result = run_setup(tmp_path, ["--help"])

    assert result.exit_status == 0
    assert result.stdout.startswith("usage: setup.sh")
    assert [option for option in OPTIONS if option not in result.stdout] == []


@pytest.mark.parametrize(
    "words",
    [
        pytest.param(REQUIRED, id="required-only"),
        pytest.param(
            [
                *REQUIRED,
                "--instance",
                "x",
                "--pool",
                "p",
                "--quota",
                "1G",
                "--ref",
                "v1",
                "--image",
                "i:1",
                "--runtime",
                "opencode",
                "--sudoers",
            ],
            id="every-option",
        ),
    ],
)
def test_a_user_other_than_root_is_refused_before_the_steps(
    tmp_path: Path, words: list[str]
) -> None:
    stand_in = tmp_path / "bin" / "id"
    stand_in.parent.mkdir()
    stand_in.write_text("#!/bin/sh\necho 1000\n", encoding="utf-8")
    stand_in.chmod(0o755)
    before = entries(tmp_path)

    result = run_setup(tmp_path, words, path=f"{stand_in.parent}:{SYSTEM_PATH}")

    assert result.exit_status == 2
    assert result.stderr == "setup.sh: run as root\n"
    assert result.stdout == ""
    assert entries(tmp_path) == before
