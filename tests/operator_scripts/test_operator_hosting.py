"""The operator's hosting library: its token source, its API calls through `curl` and its git."""

import base64
import shlex
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.shared.adapters.process import ProcessResult
from support.git_support import commit_all, write_executable, write_files
from support.operator_support import (
    CURL_STAND_IN,
    hosting_env,
    make_work_tree,
    run_hosting,
)
from support.recording_stand_in_support import read_records

ACCESS = "tok123"
# The command builds the token, so its text is in no file the test writes.
ACCESS_COMMAND = "printf 'tok%s\\n' 123"
ACCESS_BASE64 = base64.b64encode(f"x-access-token:{ACCESS}".encode()).decode()
NO_ACCESS = "hosting: the token command failed; see SITE_TOKEN_CMD in the site file\n"
CURL_ARGUMENTS = ["--silent", "--show-error", "--max-time", "40", "--config", "-"]

# A stand-in for gh: it records its arguments and prints `ghtok` for `gh auth token`.
GH_STAND_IN = r"""
import json, os, sys

with open(os.environ["STAND_IN_GH_RECORD"], "a", encoding="utf-8") as record:
    record.write(json.dumps({"argv": sys.argv[1:]}) + "\n")
if sys.argv[1:] == ["auth", "token"]:
    print("ghtok")
"""


@pytest.fixture
def site_file(tmp_path: Path) -> Path:
    """A site file that holds no value, in a folder of `tmp_path` outside every repository."""
    folder = tmp_path / "site"
    folder.mkdir()
    path = folder / "site.env"
    path.write_text("# the site of a test\n", encoding="utf-8")
    return path


@pytest.fixture
def records(tmp_path: Path) -> Path:
    """The folder of the stand-ins' records, which hold what the hosting library gave them."""
    folder = tmp_path / "records"
    folder.mkdir()
    return folder


@pytest.fixture
def temporary(tmp_path: Path) -> Path:
    """The temporary folder (`TMPDIR`) of the hosting library's runs."""
    folder = tmp_path / "tmp"
    folder.mkdir()
    return folder


@pytest.fixture
def stand_ins(tmp_path: Path) -> Path:
    """A folder with the stand-ins for `curl` and `gh`."""
    folder = tmp_path / "bin"
    folder.mkdir()
    write_executable(folder, CURL_STAND_IN, name="curl")
    write_executable(folder, GH_STAND_IN, name="gh")
    return folder


@pytest.fixture
def without_gh(tmp_path: Path) -> Path:
    """A folder with the stand-in for `curl` alone."""
    folder = tmp_path / "bin-without-gh"
    folder.mkdir()
    write_executable(folder, CURL_STAND_IN, name="curl")
    return folder


@pytest.fixture
def make_env(
    tmp_path: Path, site_file: Path, records: Path, temporary: Path, stand_ins: Path
) -> Callable[..., dict[str, str]]:
    """Build a run's environment: both stand-ins, the token command `source`, the variables."""

    def build(source: str | None = None, **values: str) -> dict[str, str]:
        if source is not None:
            values["SITE_TOKEN_CMD"] = source
        return hosting_env(tmp_path, site_file, records, temporary, stand_ins, **values)

    return build


def calls(records: Path, name: str) -> list[dict[str, object]]:
    """The calls a stand-in recorded, in order."""
    return read_records(records / f"{name}.jsonl")


def curl_input(records: Path) -> list[str]:
    """The lines of the standard input of the one call of the `curl` stand-in."""
    recorded = calls(records, "curl")
    assert len(recorded) == 1, recorded
    return str(recorded[0]["stdin"]).splitlines()


def test_the_token_is_the_first_line_of_the_command_trimmed(
    tmp_path: Path, make_env: Callable[..., dict[str, str]]
) -> None:
    env = make_env(source='printf "  tok123  \\r\\nsecond\\n"')
    result = run_hosting("hosting_token", tmp_path, env)
    assert (result.exit_status, result.stdout) == (0, "tok123\n")


@pytest.mark.parametrize(
    ("values", "expected", "gh_called"),
    [
        pytest.param({}, "ghtok\n", True, id="unset"),
        pytest.param({"SITE_TOKEN_CMD": ""}, "ghtok\n", True, id="empty"),
        pytest.param({"SITE_TOKEN_CMD": ACCESS_COMMAND}, f"{ACCESS}\n", False, id="set"),
    ],
)
def test_without_a_token_command_the_token_comes_from_gh(
    *,
    tmp_path: Path,
    make_env: Callable[..., dict[str, str]],
    records: Path,
    values: dict[str, str],
    expected: str,
    gh_called: bool,
) -> None:
    result = run_hosting("hosting_token", tmp_path, make_env(**values))
    assert (result.exit_status, result.stdout) == (0, expected)
    assert bool(calls(records, "gh")) is gh_called


@pytest.mark.parametrize(
    ("command", "with_gh"),
    [
        pytest.param("echo LEAKMARK; exit 1", True, id="fails-printing-on-stdout"),
        pytest.param("echo LEAKMARK >&2; exit 1", True, id="fails-printing-on-stderr"),
        pytest.param("true", True, id="prints-nothing"),
        pytest.param('printf "\\n  \\n\\n"', True, id="prints-blank-lines"),
        pytest.param(None, False, id="no-command-and-no-gh"),
    ],
)
def test_a_failing_token_source_stops_without_repeating_its_output(
    *,
    tmp_path: Path,
    site_file: Path,
    records: Path,
    temporary: Path,
    stand_ins: Path,
    without_gh: Path,
    command: str | None,
    with_gh: bool,
) -> None:
    values = {} if command is None else {"SITE_TOKEN_CMD": command}
    folder = stand_ins if with_gh else without_gh
    env = hosting_env(tmp_path, site_file, records, temporary, folder, **values)
    result = run_hosting("hosting_token", tmp_path, env)
    assert (result.exit_status, result.stdout, result.stderr) == (4, "", NO_ACCESS)
    assert "LEAKMARK" not in result.stderr


def test_the_api_call_gives_curl_the_token_on_standard_input_only(
    tmp_path: Path, make_env: Callable[..., dict[str, str]], records: Path
) -> None:
    result = run_hosting("hosting_api GET /user", tmp_path, make_env(source=ACCESS_COMMAND))
    assert result.exit_status == 0, result.stderr
    recorded = calls(records, "curl")
    assert len(recorded) == 1
    arguments = recorded[0]["argv"]
    assert arguments == CURL_ARGUMENTS
    assert not any(ACCESS in str(argument) for argument in arguments)
    lines = curl_input(records)
    for line in [
        f'header = "Authorization: Bearer {ACCESS}"',
        'url = "https://api.github.com/user"',
        'request = "GET"',
        'header = "Accept: application/vnd.github+json"',
        'header = "X-GitHub-Api-Version: 2022-11-28"',
    ]:
        assert line in lines


@pytest.mark.parametrize(
    "api_url",
    [
        pytest.param("https://api.example.invalid", id="without-slash"),
        pytest.param("https://api.example.invalid/", id="with-trailing-slash"),
    ],
)
def test_the_site_api_url_replaces_the_default(
    tmp_path: Path, make_env: Callable[..., dict[str, str]], records: Path, api_url: str
) -> None:
    env = make_env(source=ACCESS_COMMAND, SITE_API_URL=api_url)
    result = run_hosting("hosting_api GET /user", tmp_path, env)
    assert result.exit_status == 0, result.stderr
    assert 'url = "https://api.example.invalid/user"' in curl_input(records)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        pytest.param('{"a":"b\\"c"}', ['data = "{\\"a\\":\\"b\\\\\\"c\\"}"'], id="quote"),
        pytest.param(None, [], id="no-body"),
        pytest.param("a\nb", ['data = "a\\nb"'], id="newline"),
    ],
)
def test_a_body_is_passed_quoted_in_the_configuration(
    *,
    tmp_path: Path,
    make_env: Callable[..., dict[str, str]],
    records: Path,
    body: str | None,
    expected: list[str],
) -> None:
    code = "hosting_api POST /x" + ("" if body is None else f" {shlex.quote(body)}")
    result = run_hosting(code, tmp_path, make_env(source=ACCESS_COMMAND))
    assert result.exit_status == 0, result.stderr
    assert [line for line in curl_input(records) if line.lstrip().startswith("data")] == expected


LONG_BODY = "x" * 60 + "\n" + "y" * 39 + "Z" * 20


def first_hundred_on_one_line(stderr: str) -> bool:
    """The message holds the body's first 100 characters on one line and nothing after them."""
    return (
        stderr.count("\n") == 1
        and stderr.endswith("\n")
        and stderr.startswith("hosting: GET /user: 500 " + "x" * 60)
        and "y" * 39 in stderr
        and "Z" not in stderr
    )


@pytest.mark.parametrize(
    ("status", "body", "curl_exit", "curl_error", "exit_status", "stdout", "stderr_check"),
    [
        pytest.param(
            "200", '{"login":"someone"}\n', "0", "", 0, '{"login":"someone"}\n', "", id="200"
        ),
        pytest.param("201", '{"id":1}\n', "0", "", 0, '{"id":1}\n', "", id="201"),
        pytest.param("204", "", "0", "", 0, "", "", id="204"),
        pytest.param("299", '{"id":2}\n', "0", "", 0, '{"id":2}\n', "", id="299"),
        pytest.param(
            "199", '{"message":"Edge"}', "0", "", 22, "", "hosting: GET /user: 199 Edge\n", id="199"
        ),
        pytest.param(
            "300", '{"message":"Edge"}', "0", "", 22, "", "hosting: GET /user: 300 Edge\n", id="300"
        ),
        pytest.param(
            "301",
            "Moved Permanently",
            "0",
            "",
            22,
            "",
            "hosting: GET /user: 301 Moved Permanently\n",
            id="301",
        ),
        pytest.param(
            "404",
            '{"message":"Not Found"}',
            "0",
            "",
            22,
            "",
            "hosting: GET /user: 404 Not Found\n",
            id="404",
        ),
        pytest.param("500", LONG_BODY, "0", "", 22, "", first_hundred_on_one_line, id="500"),
        pytest.param(
            "200", "", "7", "", 22, "", "hosting: GET /user: no answer\n", id="curl-fails"
        ),
        pytest.param(
            "422",
            '{"message":"Validation Failed",'
            '"errors":[{"message":"A pull request already exists"}]}',
            "0",
            "",
            22,
            "",
            "hosting: GET /user: 422 Validation Failed\n",
            id="422-own-message-first",
        ),
        pytest.param(
            "200",
            "",
            "7",
            "curl: (7) Failed to connect to api.github.com port 443\n",
            22,
            "",
            "hosting: GET /user: no answer\n",
            id="curl-fails-with-its-error-text",
        ),
    ],
)
def test_the_status_decides_the_result_of_the_api_call(
    *,
    tmp_path: Path,
    make_env: Callable[..., dict[str, str]],
    status: str,
    body: str,
    curl_exit: str,
    curl_error: str,
    exit_status: int,
    stdout: str,
    stderr_check: str | Callable[[str], bool],
) -> None:
    env = make_env(
        source=ACCESS_COMMAND,
        STAND_IN_CURL_STATUS=status,
        STAND_IN_CURL_BODY=body,
        STAND_IN_CURL_EXIT=curl_exit,
        STAND_IN_CURL_ERROR=curl_error,
    )
    result = run_hosting("hosting_api GET /user", tmp_path, env)
    assert (result.exit_status, result.stdout) == (exit_status, stdout), result.stderr
    if isinstance(stderr_check, str):
        assert result.stderr == stderr_check
    else:
        assert stderr_check(result.stderr), result.stderr


@pytest.mark.parametrize(
    ("values", "exit_status", "url_line", "missing"),
    [
        pytest.param(
            {"SITE_REPOSITORY": "owner/repo"},
            0,
            'url = "https://api.github.com/repos/owner/repo/pulls"',
            False,
            id="set",
        ),
        pytest.param({}, 2, None, True, id="unset"),
    ],
)
def test_the_repository_call_puts_the_site_repository_in_the_path(
    *,
    tmp_path: Path,
    make_env: Callable[..., dict[str, str]],
    records: Path,
    site_file: Path,
    values: dict[str, str],
    exit_status: int,
    url_line: str | None,
    missing: bool,
) -> None:
    result = run_hosting(
        "hosting_repo_api GET /pulls", tmp_path, make_env(source=ACCESS_COMMAND, **values)
    )
    assert result.exit_status == exit_status, result.stderr
    if url_line is not None:
        assert url_line in curl_input(records)
    if missing:
        assert result.stderr == f"site: missing SITE_REPOSITORY in {site_file}\n"
        assert calls(records, "curl") == []


def test_the_repository_call_passes_its_body_on(
    tmp_path: Path, make_env: Callable[..., dict[str, str]], records: Path
) -> None:
    env = make_env(source=ACCESS_COMMAND, SITE_REPOSITORY="owner/repo")
    result = run_hosting('hosting_repo_api POST /pulls \'{"a":"b"}\'', tmp_path, env)
    assert result.exit_status == 0, result.stderr
    lines = curl_input(records)
    for line in [
        'url = "https://api.github.com/repos/owner/repo/pulls"',
        'request = "POST"',
        'data = "{\\"a\\":\\"b\\"}"',
    ]:
        assert line in lines


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """A git work tree in `tmp_path` with one commit, `the subject`."""
    directory = make_work_tree(tmp_path / "repo")
    write_files(directory, {"file.txt": "text\n"})
    commit_all(directory, "the subject")
    return directory


def test_git_gets_the_token_through_its_environment(
    tmp_path: Path, make_env: Callable[..., dict[str, str]], repository: Path
) -> None:
    env = make_env(source=ACCESS_COMMAND)
    header = run_hosting("hosting_git config --get http.extraHeader", tmp_path, env)
    assert (header.exit_status, header.stdout) == (0, f"Authorization: Basic {ACCESS_BASE64}\n")
    helper = run_hosting("hosting_git config --get-all credential.helper", tmp_path, env)
    assert (helper.exit_status, helper.stdout) == (0, "\n")
    dump = run_hosting("hosting_git -c 'alias.envdump=!env' envdump", tmp_path, env)
    assert dump.exit_status == 0, dump.stderr
    assert {"GIT_TERMINAL_PROMPT=0", "GIT_CONFIG_COUNT=2"} <= set(dump.stdout.splitlines())
    log_code = f"hosting_git -C {shlex.quote(str(repository))} log -1 --format=%s"
    log = run_hosting(log_code, tmp_path, env)
    assert (log.exit_status, log.stdout) == (0, "the subject\n")
    traced = run_hosting(log_code, tmp_path, {**env, "GIT_TRACE": "1"})
    built_in = [line for line in traced.stderr.splitlines() if "trace: built-in: git" in line]
    assert built_in
    assert not any(ACCESS in line or ACCESS_BASE64 in line for line in built_in)


def test_git_returns_the_exit_status_of_git(
    tmp_path: Path, make_env: Callable[..., dict[str, str]]
) -> None:
    result = run_hosting(
        "hosting_git config --get no.such.key", tmp_path, make_env(source=ACCESS_COMMAND)
    )
    assert result.exit_status == 1, result.stderr


def test_git_does_not_run_without_a_token(
    tmp_path: Path, make_env: Callable[..., dict[str, str]]
) -> None:
    folder = tmp_path / "never"
    code = f"hosting_git init {shlex.quote(str(folder))}"
    result = run_hosting(code, tmp_path, make_env(source="exit 1"))
    assert result.exit_status == 4
    assert not folder.exists()


def test_the_token_is_neither_left_in_a_file_nor_printed(
    tmp_path: Path, make_env: Callable[..., dict[str, str]], records: Path
) -> None:
    env = make_env(source=ACCESS_COMMAND, SITE_REPOSITORY="owner/repo")
    token = run_hosting("hosting_token", tmp_path, env)
    assert token.stdout == f"{ACCESS}\n"
    folder = shlex.quote(str(tmp_path / "cloned"))
    runs: list[ProcessResult] = [
        run_hosting("hosting_api GET /user", tmp_path, env),
        run_hosting("hosting_repo_api GET /pulls", tmp_path, env),
        run_hosting("hosting_api GET /user", tmp_path, {**env, "STAND_IN_CURL_STATUS": "404"}),
        run_hosting(f"hosting_git init -q {folder}\nhosting_git -C {folder} status", tmp_path, env),
    ]
    printed = "".join(run.stdout + run.stderr for run in runs) + token.stderr
    assert ACCESS not in printed
    assert ACCESS_BASE64 not in printed
    # The stand-ins' records hold what the library gave them, the token on curl's standard input.
    left = [
        path
        for path in tmp_path.rglob("*")
        if path.is_file()
        and records not in path.parents
        and (ACCESS.encode() in path.read_bytes() or ACCESS_BASE64.encode() in path.read_bytes())
    ]
    assert left == []


@pytest.mark.parametrize(("status", "exit_status"), [("200", 0), ("404", 22)])
def test_the_api_call_leaves_no_temporary_file(
    *,
    tmp_path: Path,
    make_env: Callable[..., dict[str, str]],
    temporary: Path,
    records: Path,
    status: str,
    exit_status: int,
) -> None:
    (temporary / "before").write_text("there before\n", encoding="utf-8")
    before = sorted(temporary.rglob("*"))
    env = make_env(source=ACCESS_COMMAND, STAND_IN_CURL_STATUS=status)
    result = run_hosting("hosting_api GET /user", tmp_path, env)
    assert result.exit_status == exit_status, result.stderr
    assert len(calls(records, "curl")) == 1
    assert sorted(temporary.rglob("*")) == before


@pytest.mark.parametrize(
    "code",
    [
        pytest.param("hosting_api GET /user", id="api"),
        pytest.param("hosting_repo_api GET /pulls", id="repository-api"),
    ],
)
def test_the_api_call_does_not_run_curl_without_a_token(
    tmp_path: Path, make_env: Callable[..., dict[str, str]], records: Path, code: str
) -> None:
    env = make_env(source="exit 1", SITE_REPOSITORY="owner/repo")
    result = run_hosting(code, tmp_path, env)
    assert (result.exit_status, result.stdout, result.stderr) == (4, "", NO_ACCESS)
    assert calls(records, "curl") == []


@pytest.mark.parametrize(
    "loaded",
    [
        pytest.param(False, id="from-the-site-file"),
        pytest.param(True, id="already-in-the-environment"),
    ],
)
def test_the_library_loads_the_site_itself(
    tmp_path: Path, make_env: Callable[..., dict[str, str]], site_file: Path, loaded: bool
) -> None:
    if loaded:
        # A `SITE_` value in the environment, and no site file a load could read.
        env = make_env(source=ACCESS_COMMAND, FACTORY_SITE=str(tmp_path / "absent.env"))
    else:
        site_file.write_text(f"SITE_TOKEN_CMD={ACCESS_COMMAND}\n", encoding="utf-8")
        env = make_env()
    result = run_hosting("hosting_token", tmp_path, env, load=False)
    assert (result.exit_status, result.stdout) == (0, f"{ACCESS}\n")
    if loaded:
        assert result.stderr == ""
