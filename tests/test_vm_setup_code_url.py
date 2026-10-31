"""The setup script's option `--code-url`: the factory's code cloned without a credential."""

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

from vm_support import REQUIRED, STEPS, SYSTEM_PATH, run_setup, step_texts

PROJECT_URL = REQUIRED[REQUIRED.index("--repository-url") + 1]
CODE_URL = "https://code.example.invalid/factory.git"
INSTANCE = "code-url-test"
WAITING = (
    "setup: checkout: waiting for /home/factory/.secrets/hosting-token;"
    " place the secrets and run this script again"
)
NO_CREDENTIAL = (
    f"setup: checkout: cannot clone {CODE_URL} without a credential;"
    " the code repository must be readable without a token"
)
STEPS_TO_CHECKOUT = list(STEPS[: STEPS.index("checkout") + 1])
QUIET = "#!/bin/sh\nexit 0\n"
RECORDING_GIT = """#!/bin/sh
{{
  echo call
  for word in "$@"; do printf 'arg %s\\n' "$word"; done
  env | while IFS= read -r line; do printf 'env %s\\n' "$line"; done
}} >> {log}
"""
REFUSING_GIT = (
    RECORDING_GIT
    + """offered=no
case "$*" in
  *core.askPass*|*core.askpass*) offered=yes ;;
esac
if [ -n "${{GIT_ASKPASS-}}" ]; then
  offered=yes
fi
if [ "$offered" = no ]; then
  echo "fatal: could not read Username: terminal prompts disabled" >&2
  exit 128
fi
"""
)
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


@dataclass(frozen=True)
class GitCall:
    """One call of the stand-in git: its words and its environment."""

    words: list[str]
    environment: dict[str, str]


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


def _git_calls(tmp_path: Path) -> list[GitCall]:
    log = tmp_path / "git.log"
    if not log.exists():
        return []
    calls: list[GitCall] = []
    for line in log.read_text(encoding="utf-8").splitlines():
        if line == "call":
            calls.append(GitCall([], {}))
        elif line.startswith("arg "):
            calls[-1].words.append(line.removeprefix("arg "))
        elif line.startswith("env ") and "=" in line:
            name, _, value = line.removeprefix("env ").partition("=")
            calls[-1].environment[name] = value
    return calls


def _clones(tmp_path: Path) -> list[GitCall]:
    return [call for call in _git_calls(tmp_path) if "clone" in call.words]


def _setup(tmp_path: Path, git: str, words: list[str]) -> tuple[int | None, str, str]:
    folder = _stand_ins(tmp_path, git)
    result = run_setup(
        tmp_path,
        [*REQUIRED, "--instance", INSTANCE, *words],
        path=f"{folder}:{SYSTEM_PATH}",
    )
    return result.exit_status, result.stdout, result.stderr


def _offers_askpass(call: GitCall) -> bool:
    texts = [*call.words, *call.environment.values()]
    return "GIT_ASKPASS" in call.environment or any("core.askpass" in t.lower() for t in texts)


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


@pytest.mark.parametrize(
    ("words", "different"),
    [
        pytest.param(["--code-url", CODE_URL], True, id="different"),
        pytest.param(["--code-url", PROJECT_URL], False, id="equal"),
        pytest.param([], False, id="absent"),
    ],
)
def test_only_a_different_code_url_is_cloned_without_the_askpass(
    tmp_path: Path, words: list[str], *, different: bool
) -> None:
    status, _, stderr = _setup(tmp_path, RECORDING_GIT, words)

    assert status == 0, stderr
    clones = _clones(tmp_path)
    if different:
        assert len(clones) == 1
        clone = clones[0]
        after = clone.words[clone.words.index("clone") + 1 :]
        assert CODE_URL in after
        assert PROJECT_URL not in after
        assert clone.environment.get("GIT_TERMINAL_PROMPT") == "0"
        assert not _offers_askpass(clone)
    else:
        assert clones == []


def test_the_clone_after_the_secrets_wait_carries_the_askpass_and_the_project_url(
    code: str,
) -> None:
    checkout = step_texts(code)["checkout"]
    waiting = checkout.find("waiting for /home/factory/.secrets/hosting-token")
    sources = ["repository_url", *_option_variables(code)]
    clones = [
        line
        for line in checkout[waiting:].splitlines()
        if "git clone" in line
        and 'GIT_ASKPASS="$askpass"' in line
        and 'core.askPass="$askpass"' in line
        and "GIT_TERMINAL_PROMPT=0" in line
    ]

    assert waiting >= 0
    assert len(clones) == 1
    assert any(_names(clones[0], source) for source in sources)


def test_a_code_repository_that_asks_for_a_credential_fails_the_clone(tmp_path: Path) -> None:
    status, stdout, stderr = _setup(tmp_path, REFUSING_GIT, ["--code-url", CODE_URL])

    assert status == 1
    assert NO_CREDENTIAL in stderr.splitlines()
    assert WAITING not in stdout
    assert len(_clones(tmp_path)) == 1


@pytest.mark.parametrize(
    ("words", "clones"),
    [
        pytest.param(["--code-url", CODE_URL], 1, id="different"),
        pytest.param([], 0, id="absent"),
    ],
)
def test_the_first_pass_stops_at_the_secrets_wait_after_the_code_clone(
    tmp_path: Path, words: list[str], clones: int
) -> None:
    status, stdout, stderr = _setup(tmp_path, RECORDING_GIT, words)

    assert status == 0, stderr
    assert stdout.splitlines()[-1] == WAITING
    assert _step_names(stdout) == STEPS_TO_CHECKOUT
    assert len(_clones(tmp_path)) == clones


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
