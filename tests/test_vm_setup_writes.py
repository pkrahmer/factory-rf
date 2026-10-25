"""The setup script's writes as factory: the text comes from the helper's own standard input."""

import re
import stat
from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, run_process
from vm_support import SYSTEM_PATH, function_text, setup_code, step_texts, write_helpers

AS_ITSELF = 'as_factory() {\n  "$@"\n}\n'


@pytest.fixture
def code() -> str:
    """Return the setup script's text without its comment lines."""
    return setup_code()


@pytest.fixture
def helper(code: str) -> str:
    """Return the name of the script's one write helper."""
    helpers = write_helpers(code)
    assert len(helpers) == 1, helpers
    return helpers[0]


def test_no_write_reads_dev_stdin_by_name(code: str) -> None:
    assert "/dev/stdin" not in code
    assert [line for line in code.splitlines() if "install" in line and "stdin" in line] == []


@pytest.mark.parametrize(
    ("step", "mode", "target"),
    [
        pytest.param("image-id", "0644", r"\$\{?base\}?/image-id", id="image-id"),
        pytest.param("checkout", "0755", r"\$\{?askpass\}?", id="askpass"),
        pytest.param("environment", "0644", r"\$\{?env_file\}?", id="factory-env"),
    ],
)
def test_each_file_is_written_through_the_helper_with_its_mode(
    code: str, helper: str, step: str, mode: str, target: str
) -> None:
    call = re.compile(rf"(?<![\w-]){helper}\s+{mode}\s+\"?{target}\"?(?![\w/.-])")
    body = function_text(code, helper).splitlines()[1:-1]

    assert [line for line in step_texts(code)[step].splitlines() if call.search(line)] != []
    assert [line for line in body if re.match(r"\s*as_factory\s.*cat >", line)] != []


@pytest.mark.parametrize(
    "texts",
    [pytest.param(["one"], id="first"), pytest.param(["one", "two"], id="again")],
)
def test_the_helper_writes_its_standard_input_with_the_mode(
    code: str, helper: str, tmp_path: Path, texts: list[str]
) -> None:
    runner = tmp_path / "runner.sh"
    call = f'printf \'%s\\n\' "$3" | {helper} "$1" "$2"\n'
    runner.write_text(f"{AS_ITSELF}{function_text(code, helper)}\n{call}", encoding="utf-8")
    target = tmp_path / "target"

    for text in texts:
        result = run_process(
            ProcessRequest(
                argv=["sh", str(runner), "0640", str(target), text],
                cwd=tmp_path,
                env={"PATH": SYSTEM_PATH},
            )
        )
        assert result.exit_status == 0, result.stderr

    assert target.read_text(encoding="utf-8") == f"{texts[-1]}\n"
    assert stat.S_IMODE(target.stat().st_mode) == 0o640
