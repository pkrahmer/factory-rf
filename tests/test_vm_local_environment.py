"""The operator's own environment file: the unit reads it, the setup script never writes it."""

import re
from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from vm_support import SERVICE, SYSTEM_PATH

LOCAL = "factory.local.env"
UNIT = """\
# The factory as a system service, one instance per name: factory@vm runs the instance vm.
# vm/setup.sh installs it as factory@.service and enables it; the operator starts it.
[Unit]
Description=The factory, instance %i
After=network-online.target zfs.target
Wants=network-online.target

[Service]
User=factory
Group=factory
WorkingDirectory=/srv/factory/%i
EnvironmentFile=/srv/factory/%i/factory.env
EnvironmentFile=-/srv/factory/%i/factory.local.env
ExecStart=/srv/factory/%i/factory/.venv/bin/factory-run
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
"""


def _closing_text(code: str) -> str:
    start = code.rfind("\n", 0, code.index("setup: done:")) + 1
    return code[start:]


def _run_closing_text(code: str, tmp_path: Path, instance: str, base: str) -> ProcessResult:
    runner = tmp_path / "runner.sh"
    runner.write_text(f"instance={instance}\nbase={base}\n{_closing_text(code)}", encoding="utf-8")
    return run_process(
        ProcessRequest(argv=["sh", str(runner)], cwd=tmp_path, env={"PATH": SYSTEM_PATH})
    )


def test_the_unit_reads_the_local_file_after_the_environment_file_and_nothing_else() -> None:
    text = SERVICE.read_text(encoding="utf-8")

    assert [line for line in text.splitlines() if line.startswith("EnvironmentFile=")] == [
        "EnvironmentFile=/srv/factory/%i/factory.env",
        "EnvironmentFile=-/srv/factory/%i/factory.local.env",
    ]
    assert text == UNIT


def test_the_script_names_the_local_file_only_in_its_closing_line(code: str) -> None:
    naming = [line for line in code.splitlines() if LOCAL in line]

    assert len(naming) == 1, naming
    assert "setup: local:" in naming[0]
    assert naming[0] in _closing_text(code)


@pytest.mark.parametrize(
    "command",
    [
        pytest.param(r"(?<![\w-])rm(?![\w-])", id="rm"),
        pytest.param(r"(?<![\w-])cp(?![\w-])", id="cp"),
        pytest.param(r"(?<![\w-])install(?![\w-])", id="install"),
        pytest.param(r"(?<![\w-])tee(?![\w-])", id="tee"),
        pytest.param(r"(?<![\w-])touch(?![\w-])", id="touch"),
        pytest.param(r">", id="redirection"),
        pytest.param(r"(?<![\w-])stage(?![\w-])", id="stage"),
    ],
)
def test_no_command_of_the_script_mentions_the_local_file(code: str, command: str) -> None:
    pattern = re.compile(command)

    assert [line for line in code.splitlines() if LOCAL in line and pattern.search(line)] == []


@pytest.mark.parametrize("instance", ["vm", "other"])
def test_the_closing_text_names_the_instance_s_local_file_after_done(
    code: str, tmp_path: Path, instance: str
) -> None:
    result = _run_closing_text(code, tmp_path, instance, f"/srv/factory/{instance}")

    assert result.exit_status == 0, result.stderr
    done, local = ["", "", *result.stdout.splitlines()][-2:]
    assert done.startswith("setup: done:"), result.stdout
    assert local == (
        f"setup: local: /srv/factory/{instance}/factory.local.env is yours: "
        "the script never writes it; the unit reads it after factory.env"
    )


@pytest.mark.parametrize(
    "content",
    [pytest.param(b"MODEL=proxy-model\n", id="present"), pytest.param(None, id="absent")],
)
def test_the_closing_text_leaves_the_local_file_as_it_found_it(
    code: str, tmp_path: Path, content: bytes | None
) -> None:
    local = tmp_path / LOCAL
    if content is not None:
        local.write_bytes(content)

    result = _run_closing_text(code, tmp_path, "vm", str(tmp_path))

    assert result.exit_status == 0, result.stderr
    if content is None:
        assert not local.exists()
    else:
        assert local.read_bytes() == content
