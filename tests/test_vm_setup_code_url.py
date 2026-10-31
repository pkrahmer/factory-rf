"""The setup script's option `--code-url`: the factory's code cloned without a credential."""

import re
from pathlib import Path

import pytest

from vm_support import REQUIRED, STEPS, SYSTEM_PATH, indent, run_setup, step_texts

PROJECT_URL = REQUIRED[REQUIRED.index("--repository-url") + 1]
CODE_URL = "https://code.example.invalid/factory.git"
INSTANCE = "code-url-test"
WAITING = (
    "setup: checkout: waiting for /home/factory/.secrets/hosting-token;"
    " place the secrets and run this script again"
)
STEPS_TO_CHECKOUT = list(STEPS[: STEPS.index("checkout") + 1])
QUIET = "#!/bin/sh\nexit 0\n"
RECORDING_GIT = """#!/bin/sh
{{
  echo call
  for word in "$@"; do printf 'arg %s\\n' "$word"; done
}} >> {log}
"""
# runuser runs only git for real: every other command it is given would write as factory.
RUNUSER = """#!/bin/sh
for word in "$@"; do
  if [ "$word" = git ]; then
    shift 3
    exec "$@"
  fi
done
exit 0
"""


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def _stand_ins(tmp_path: Path, git: str) -> Path:
    """Write the stand-in tools that carry the script up to its checkout step."""
    folder = tmp_path / "bin"
    folder.mkdir()
    log = tmp_path / "git.log"
    _write(folder / "id", "#!/bin/sh\necho 0\n")
    _write(folder / "dpkg-query", "#!/bin/sh\nprintf 'install ok installed'\n")
    _write(folder / "mktemp", f"#!/bin/sh\necho {tmp_path / 'staged'}\n")
    _write(folder / "runuser", RUNUSER)
    _write(folder / "git", git.format(log=log))
    for name in (
        "grep",
        "zpool",
        "zfs",
        "loginctl",
        "stat",
        "install",
        "cp",
        "chmod",
        "rm",
        "visudo",
    ):
        _write(folder / name, QUIET)
    return folder


def _clones(tmp_path: Path) -> int:
    log = tmp_path / "git.log"
    if not log.exists():
        return 0
    return log.read_text(encoding="utf-8").splitlines().count("arg clone")


def _setup(tmp_path: Path, git: str, words: list[str]) -> tuple[int | None, str, str]:
    folder = _stand_ins(tmp_path, git)
    result = run_setup(
        tmp_path,
        [*REQUIRED, "--instance", INSTANCE, *words],
        path=f"{folder}:{SYSTEM_PATH}",
    )
    return result.exit_status, result.stdout, result.stderr


def _option_variables(code: str) -> list[str]:
    arm = re.search(r"(?s)--code-url\)(.*?);;", code)
    return [] if arm is None else re.findall(r"(?<![\w$])(\w+)=", arm.group(1))


def _names(text: str, variable: str) -> bool:
    return re.search(rf"\$\{{?{variable}(?!\w)", text) is not None


def _step_names(stdout: str) -> list[str]:
    names: list[str] = []
    for line in stdout.splitlines():
        found = re.match(r"setup: ([\w-]+): ", line)
        if found is not None and (names == [] or names[-1] != found.group(1)):
            names.append(found.group(1))
    return names


def _after_the_wait(code: str) -> list[str]:
    checkout = step_texts(code)["checkout"]
    waiting = checkout.find("waiting for /home/factory/.secrets/hosting-token")
    assert waiting >= 0
    return checkout[waiting:].splitlines()


def _code_clone(code: str) -> tuple[list[str], int]:
    """The checkout step's lines after the wait, and the index of the one clone of the code url."""
    lines = _after_the_wait(code)
    variables = _option_variables(code)
    assert variables != []
    clones = [
        index
        for index, line in enumerate(lines)
        if "git clone" in line and any(_names(line, variable) for variable in variables)
    ]
    assert len(clones) == 1
    return lines, clones[0]


def _guard(lines: list[str], index: int) -> str:
    """The `if` or `elif` line the line at `index` is indented under, or the empty text."""
    for line in reversed(lines[:index]):
        if line.strip() and indent(line) < indent(lines[index]):
            return line if line.lstrip().startswith(("if ", "elif ")) else ""
    return ""


def _compares_urls(line: str, variables: list[str], operator: str) -> bool:
    """Whether the line compares a code-url variable with `$repository_url` by `operator`."""
    code = "|".join(variables)
    left = rf"\"\$\{{?(?:{code})\}}?\""
    right = r"\"\$\{?repository_url\}?\""
    return (
        re.search(rf"{left}\s+{operator}\s+{right}", line) is not None
        or re.search(rf"{right}\s+{operator}\s+{left}", line) is not None
    )


def _rest_of_block(lines: list[str], index: int) -> list[str]:
    """The lines after the one at `index`, up to the end of the top-level block it stands in."""
    rest: list[str] = []
    for line in lines[index + 1 :]:
        if line.strip() and indent(line) == 0:
            break
        rest.append(line)
    return rest


def test_a_different_code_url_is_cloned_after_the_wait_without_the_askpass(code: str) -> None:
    lines, index = _code_clone(code)
    clone = lines[index]
    variables = _option_variables(code)

    assert "GIT_TERMINAL_PROMPT=0" in clone
    assert "GIT_ASKPASS=" not in clone
    assert "core.askpass" not in clone.lower()
    assert not _names(clone, "repository_url")
    assert _compares_urls(_guard(lines, index), variables, "!=")
    assert not _compares_urls(_guard(lines, index), variables, "=")


def test_the_clone_after_the_secrets_wait_carries_the_askpass_and_the_project_url(
    code: str,
) -> None:
    lines = _after_the_wait(code)
    variables = _option_variables(code)
    clones = [
        index
        for index, line in enumerate(lines)
        if "git clone" in line
        and 'GIT_ASKPASS="$askpass"' in line
        and 'core.askPass="$askpass"' in line
        and "GIT_TERMINAL_PROMPT=0" in line
    ]

    assert len(clones) == 1
    assert any(_names(lines[clones[0]], source) for source in ["repository_url", *variables])
    assert _compares_urls(_guard(lines, clones[0]), variables, "=")
    assert not _compares_urls(_guard(lines, clones[0]), variables, "!=")


def test_the_code_url_defaults_to_the_repository_url(code: str) -> None:
    lines = code.splitlines()
    variables = _option_variables(code)
    names = "|".join(variables)
    defaults = [
        index
        for index, line in enumerate(lines)
        if re.fullmatch(rf"\s*(?:{names})=\"?\$\{{?repository_url\}}?\"?", line)
    ]

    assert variables != []
    assert len(defaults) == 1
    guard = _guard(lines, defaults[0])
    assert re.search(rf"-z\s+\"\$\{{?(?:{names})\}}?\"", guard) is not None


def test_a_code_repository_that_asks_for_a_credential_fails_the_clone(code: str) -> None:
    lines, index = _code_clone(code)
    variable = "|".join(_option_variables(code))
    message = re.compile(
        rf"echo \"setup: checkout: cannot clone \$\{{?(?:{variable})\}}? without a credential;"
        r" the code repository must be readable without a token\" >&2"
    )
    after = lines[index:]
    failing = next((i for i, line in enumerate(after) if message.search(line)), None)

    assert failing is not None
    assert "||" in lines[index]
    assert any(line.strip() == "exit 1" for line in after[failing + 1 : failing + 3])


def test_the_code_clone_unsets_an_askpass_the_environment_hands_on(code: str) -> None:
    lines, index = _code_clone(code)
    clone = lines[index]

    assert re.search(r"(?<![\w-])env\s+(?:-\S+\s+)*-u\s+GIT_ASKPASS(?!\w)", clone) is not None


def test_the_code_clone_counts_as_a_fresh_clone(code: str) -> None:
    lines, index = _code_clone(code)
    later = [
        line
        for line in _rest_of_block(lines, index)
        if line.strip() == "cloned=yes" and indent(line) <= indent(lines[index])
    ]

    assert later != []


@pytest.mark.parametrize(
    "words",
    [
        pytest.param(["--code-url", CODE_URL], id="different"),
        pytest.param(["--code-url", PROJECT_URL], id="equal"),
        pytest.param([], id="absent"),
    ],
)
def test_the_first_pass_stops_at_the_secrets_wait_without_a_clone(
    tmp_path: Path, words: list[str]
) -> None:
    status, stdout, stderr = _setup(tmp_path, RECORDING_GIT, words)

    assert status == 0, stderr
    assert stdout.splitlines()[-1] == WAITING
    assert _step_names(stdout) == STEPS_TO_CHECKOUT
    assert _clones(tmp_path) == 0


def test_the_environment_file_never_holds_the_code_url(code: str) -> None:
    environment = step_texts(code)["environment"]
    variables = _option_variables(code)

    assert variables != []
    assert [variable for variable in variables if _names(environment, variable)] == []
    assert "FACTORY_REPOSITORY_URL=$repository_url" in environment


@pytest.mark.parametrize(
    "words",
    [
        pytest.param(["--help"], id="help"),
        pytest.param([*REQUIRED, "--bogus"], id="fault"),
    ],
)
def test_the_usage_text_names_the_code_url_option(tmp_path: Path, words: list[str]) -> None:
    result = run_setup(tmp_path, words)

    usage = result.stdout if words == ["--help"] else result.stderr
    lines = [line for line in usage.splitlines() if line.startswith("usage: setup.sh")]
    assert len(lines) == 1
    assert "--code-url" in lines[0]
