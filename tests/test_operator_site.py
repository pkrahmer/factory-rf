"""The operator's site file: its place, its loader and the `site` command, run as children."""

import re
import shutil
import stat
from collections.abc import Callable
from pathlib import Path

import pytest

from operator_support import (
    SITE_EXAMPLE,
    example_keys,
    exported,
    load_site,
    make_work_tree,
    operator_environment,
    run_library,
    run_site,
)

INTERFACE_KEYS = [
    "SITE_REPOSITORY",
    "SITE_CHECKOUT",
    "SITE_API_URL",
    "SITE_TOKEN_CMD",
    "SITE_PROXY",
    "SITE_NO_PROXY",
    "SITE_PROJECT",
    "SITE_REGION",
    "SITE_IMPERSONATE",
    "SITE_RUN_AS",
    "SITE_CONNECTOR",
    "SITE_JOB",
    "SITE_INSTANCE",
    "SITE_REPOSITORY_URL",
    "SITE_CODE_URL",
    "SITE_CODE_REF",
    "SITE_HOSTING_SECRET",
    "SITE_MODEL_SECRET",
    "SITE_MODEL_BASE_URL",
    "SITE_MODEL",
    "SITE_MODEL_INPUT_COST",
    "SITE_MODEL_OUTPUT_COST",
    "SITE_LOGIN_URL",
    "SITE_LOGIN_SCOPE",
    "SITE_LOGIN_CLIENT_ID",
    "SITE_CPU",
    "SITE_MEMORY",
    "SITE_TIMEOUT",
    "SITE_IDLE_MINUTES",
    "SITE_RESET_REPOSITORY",
    "SITE_SANITISE_RULES",
]
USAGE = "usage: site path | init | show | get SITE_X"
URL_HOST = re.compile(r"://(?:[^/@\s]*@)?([^/:\s'\"]*)")


def in_repository(path: Path) -> str:
    return f"site: {path} lies in a git repository; keep the site file outside every repository"


@pytest.fixture
def site_file(tmp_path: Path) -> Path:
    """The site file's path, in a folder of `tmp_path` that is not a git work tree."""
    folder = tmp_path / "site"
    folder.mkdir()
    return folder / "site.env"


@pytest.fixture
def site_env(tmp_path: Path, site_file: Path) -> dict[str, str]:
    """An environment whose `FACTORY_SITE` names `site_file`."""
    return operator_environment(tmp_path, FACTORY_SITE=str(site_file))


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        pytest.param(
            {"FACTORY_SITE": "chosen/site.env", "XDG_CONFIG_HOME": "xdg"},
            "chosen/site.env",
            id="factory-site",
        ),
        pytest.param({"XDG_CONFIG_HOME": "xdg"}, "xdg/kumpel/site.env", id="xdg-config-home"),
        pytest.param({}, "home/.config/kumpel/site.env", id="home"),
        pytest.param(
            {"FACTORY_SITE": "", "XDG_CONFIG_HOME": "xdg"},
            "xdg/kumpel/site.env",
            id="empty-factory-site",
        ),
    ],
)
def test_the_site_path_follows_factory_site_then_xdg_then_home(
    tmp_path: Path, values: dict[str, str], expected: str
) -> None:
    absolute = {name: str(tmp_path / value) if value else "" for name, value in values.items()}
    env = operator_environment(tmp_path, **absolute)

    result = run_library("site_path\n", tmp_path, env)

    assert result.exit_status == 0, result.stderr
    assert result.stdout == f"{tmp_path / expected}\n"


def test_the_loader_exports_key_lines_and_skips_blank_and_comment_lines(
    tmp_path: Path, site_file: Path, site_env: dict[str, str]
) -> None:
    site_file.write_text("# a comment\n\nSITE_A=x\n   \n   # indented\n", encoding="utf-8")

    result = load_site(tmp_path, site_env)

    assert result.exit_status == 0, result.stderr
    assert exported(result.stdout) == {"SITE_A": "x"}


@pytest.mark.parametrize(
    ("line", "value"),
    [
        pytest.param("SITE_A=a b", "a b", id="inner-space"),
        pytest.param('SITE_A="a b "', "a b ", id="double-quotes"),
        pytest.param("SITE_A='x'", "x", id="single-quotes"),
        pytest.param("SITE_A=a  ", "a", id="trailing-spaces"),
        pytest.param('SITE_A="x', '"x', id="unmatched-quote"),
        pytest.param("SITE_A=", "", id="empty"),
        pytest.param("SITE_A=a=b", "a=b", id="second-equals"),
    ],
)
def test_the_value_is_the_text_after_the_first_equals_sign(
    tmp_path: Path, site_file: Path, site_env: dict[str, str], line: str, value: str
) -> None:
    site_file.write_text(f"{line}\n", encoding="utf-8")

    result = load_site(tmp_path, site_env)

    assert result.exit_status == 0, result.stderr
    assert exported(result.stdout) == {"SITE_A": value}


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("$(touch MARK)", id="command-substitution"),
        pytest.param("`touch MARK`", id="backticks"),
        pytest.param("$HOME;touch MARK", id="variable-and-semicolon"),
    ],
)
def test_a_value_is_never_interpreted(
    tmp_path: Path, site_file: Path, site_env: dict[str, str], value: str
) -> None:
    site_file.write_text(f"SITE_A={value}\n", encoding="utf-8")

    result = load_site(tmp_path, site_env)

    assert result.exit_status == 0, result.stderr
    assert exported(result.stdout) == {"SITE_A": value}
    assert not (tmp_path / "MARK").exists()
    assert not (site_file.parent / "MARK").exists()


def test_a_backslash_in_a_value_has_no_meaning(
    tmp_path: Path, site_file: Path, site_env: dict[str, str]
) -> None:
    site_file.write_text("SITE_A=a\\nb\\\\c\n", encoding="utf-8")

    result = load_site(tmp_path, site_env)

    assert result.exit_status == 0, result.stderr
    assert exported(result.stdout) == {"SITE_A": r"a\nb\\c"}


def test_a_key_name_may_hold_digits_and_underscores(
    tmp_path: Path, site_file: Path, site_env: dict[str, str]
) -> None:
    site_file.write_text("SITE_A_1=x\n", encoding="utf-8")

    result = load_site(tmp_path, site_env)

    assert result.exit_status == 0, result.stderr
    assert exported(result.stdout) == {"SITE_A_1": "x"}


def test_a_key_that_appears_twice_keeps_its_first_value(
    tmp_path: Path, site_file: Path, site_env: dict[str, str]
) -> None:
    site_file.write_text("SITE_A=first\nSITE_A=second\n", encoding="utf-8")

    result = load_site(tmp_path, site_env)

    assert result.exit_status == 0, result.stderr
    assert exported(result.stdout) == {"SITE_A": "first"}


@pytest.mark.parametrize(
    ("line", "value"),
    [
        pytest.param("SITE_A =1", None, id="space-before-equals"),
        pytest.param("SITE_A= 1", " 1", id="space-after-equals"),
    ],
)
def test_a_space_before_the_equals_sign_is_a_fault_and_one_after_it_is_the_value(
    tmp_path: Path, site_file: Path, site_env: dict[str, str], line: str, value: str | None
) -> None:
    site_file.write_text(f"{line}\n", encoding="utf-8")

    result = load_site(tmp_path, site_env)

    if value is None:
        assert result.exit_status == 2
        assert exported(result.stdout) == {}
        assert result.stderr.splitlines() == [f"site: {site_file}:1: not a KEY=value line"]
    else:
        assert result.exit_status == 0, result.stderr
        assert exported(result.stdout) == {"SITE_A": value}


@pytest.mark.parametrize(
    ("line", "message"),
    [
        pytest.param("plain text", "not a KEY=value line", id="plain-text"),
        pytest.param("OTHER=1", "OTHER is not a SITE_ key", id="other-key"),
        pytest.param("site_a=1", None, id="lower-case"),
        pytest.param("SITE_A = 1", None, id="spaces-around-equals"),
        pytest.param("SITE_=1", None, id="no-name"),
    ],
)
def test_a_faulty_line_exports_nothing_and_returns_2(
    tmp_path: Path, site_file: Path, site_env: dict[str, str], line: str, message: str | None
) -> None:
    site_file.write_text(f"SITE_B=good\n{line}\n", encoding="utf-8")

    result = load_site(tmp_path, site_env)

    assert result.exit_status == 2
    assert exported(result.stdout) == {}
    lines = result.stderr.splitlines()
    assert len(lines) == 1, result.stderr
    if message is None:
        assert lines[0].startswith(f"site: {site_file}:2: ")
    else:
        assert lines[0] == f"site: {site_file}:2: {message}"


def test_a_variable_already_in_the_environment_keeps_its_value(
    tmp_path: Path, site_file: Path, site_env: dict[str, str]
) -> None:
    site_file.write_text("SITE_A=file\nSITE_B=other\n", encoding="utf-8")

    result = load_site(tmp_path, {**site_env, "SITE_A": "env"})

    assert result.exit_status == 0, result.stderr
    assert exported(result.stdout) == {"SITE_A": "env", "SITE_B": "other"}


def test_a_missing_site_file_returns_1(
    tmp_path: Path, site_file: Path, site_env: dict[str, str]
) -> None:
    result = load_site(tmp_path, site_env)

    assert result.exit_status == 1
    assert result.stderr.splitlines() == [f"site: no site file at {site_file}; run: site init"]


@pytest.mark.parametrize(
    ("work_tree", "status"),
    [pytest.param(True, 3, id="in-work-tree"), pytest.param(False, 0, id="outside")],
)
def test_a_site_file_in_a_git_work_tree_is_refused(
    tmp_path: Path, work_tree: bool, status: int
) -> None:
    folder = tmp_path / "folder"
    if work_tree:
        make_work_tree(folder)
    else:
        folder.mkdir()
    path = folder / "site.env"
    path.write_text("SITE_A=x\n", encoding="utf-8")

    result = load_site(tmp_path, operator_environment(tmp_path, FACTORY_SITE=str(path)))

    assert result.exit_status == status
    if work_tree:
        assert result.stderr.splitlines() == [in_repository(path)]
        assert exported(result.stdout) == {}
    else:
        assert exported(result.stdout) == {"SITE_A": "x"}


@pytest.mark.parametrize(
    ("names", "missing"),
    [
        pytest.param("SITE_A SITE_D", None, id="all-set"),
        pytest.param("SITE_A SITE_B SITE_C", "SITE_B, SITE_C", id="unset-and-empty"),
        pytest.param("SITE_C SITE_A SITE_B", "SITE_C, SITE_B", id="order-given"),
    ],
)
def test_require_names_every_unset_or_empty_name_in_the_order_given(
    tmp_path: Path,
    site_file: Path,
    site_env: dict[str, str],
    names: str,
    missing: str | None,
) -> None:
    env = {**site_env, "SITE_A": "a", "SITE_C": "", "SITE_D": "d"}

    result = run_library(f"site_require {names}\n", tmp_path, env)

    assert result.exit_status == (0 if missing is None else 2)
    assert result.stdout == ""
    if missing is None:
        assert result.stderr == ""
    else:
        assert result.stderr.splitlines() == [f"site: missing {missing} in {site_file}"]


def test_require_adds_the_site_prefix_to_a_bare_name(
    tmp_path: Path, site_file: Path, site_env: dict[str, str]
) -> None:
    result = run_library("site_require A B\n", tmp_path, site_env)

    assert result.exit_status == 2
    assert result.stdout == ""
    assert result.stderr.splitlines() == [f"site: missing SITE_A, SITE_B in {site_file}"]


def test_the_path_command_prints_the_site_path(
    tmp_path: Path, site_file: Path, site_env: dict[str, str]
) -> None:
    result = run_site(["path"], tmp_path, site_env)

    assert result.exit_status == 0, result.stderr
    assert result.stdout == f"{site_file}\n"
    assert result.stdout == run_library("site_path\n", tmp_path, site_env).stdout


def test_show_says_set_or_unset_for_every_key_of_the_example_and_no_value(
    tmp_path: Path, site_file: Path, site_env: dict[str, str]
) -> None:
    keys = example_keys()
    site_file.write_text(
        f"SITE_REPOSITORY=owner/SECRETMARK\nSITE_PROJECT=\n{keys[-1]}=SECRETMARK\n",
        encoding="utf-8",
    )
    present = {"SITE_REPOSITORY", keys[-1]}

    result = run_site(["show"], tmp_path, site_env)

    assert result.exit_status == 0, result.stderr
    assert result.stdout.splitlines() == [
        f"{key}={'set' if key in present else 'unset'}" for key in keys
    ]
    assert "SECRETMARK" not in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("text", "value"),
    [
        pytest.param("SITE_A=the value\n", "the value", id="set"),
        pytest.param("SITE_B=other\n", None, id="unset"),
        pytest.param("SITE_A=\n", None, id="empty"),
    ],
)
def test_get_prints_a_set_value_and_refuses_an_unset_or_empty_one(
    tmp_path: Path, site_file: Path, site_env: dict[str, str], text: str, value: str | None
) -> None:
    site_file.write_text(text, encoding="utf-8")

    result = run_site(["get", "SITE_A"], tmp_path, site_env)

    if value is None:
        assert result.exit_status == 1
        assert result.stdout == ""
        assert result.stderr.splitlines() == ["site: SITE_A is not set"]
    else:
        assert result.exit_status == 0, result.stderr
        assert result.stdout == f"{value}\n"


def test_init_writes_the_example_once_with_mode_0600(tmp_path: Path) -> None:
    path = tmp_path / "new" / "folder" / "site.env"
    env = operator_environment(tmp_path, FACTORY_SITE=str(path))

    first = run_site(["init"], tmp_path, env)

    assert first.exit_status == 0, first.stderr
    assert first.stdout.splitlines() == [f"site: wrote {path}; edit it, then run: site check"]
    assert path.read_bytes() == SITE_EXAMPLE.read_bytes()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    path.write_bytes(b"SITE_A=mine\n")

    second = run_site(["init"], tmp_path, env)

    assert second.exit_status == 1
    assert second.stderr.splitlines() == [f"site: {path} exists; not overwritten"]
    assert path.read_bytes() == b"SITE_A=mine\n"


@pytest.mark.parametrize(
    "words",
    [
        pytest.param([], id="no-argument"),
        pytest.param(["frobnicate"], id="unknown-command"),
        pytest.param(["get"], id="get-without-name"),
        pytest.param(["get", "HOME"], id="get-not-a-site-key"),
    ],
)
def test_a_malformed_command_prints_the_usage_and_exits_2(
    tmp_path: Path, site_file: Path, site_env: dict[str, str], words: list[str]
) -> None:
    site_file.write_text("SITE_A=x\n", encoding="utf-8")

    result = run_site(words, tmp_path, site_env)

    assert result.exit_status == 2
    assert result.stdout == ""
    assert result.stderr.splitlines() == [USAGE]


def test_the_example_loads_comments_every_key_and_holds_only_made_up_values(
    tmp_path: Path, site_file: Path, site_env: dict[str, str]
) -> None:
    shutil.copyfile(SITE_EXAMPLE, site_file)
    text = SITE_EXAMPLE.read_text(encoding="utf-8")
    lines = text.splitlines()

    result = load_site(tmp_path, site_env)

    assert result.exit_status == 0, result.stderr
    assert result.stderr == ""
    uncommented = [
        line
        for number, line in enumerate(lines)
        if line.startswith("SITE_") and (number == 0 or not lines[number - 1].startswith("#"))
    ]
    assert uncommented == []
    assert example_keys()[: len(INTERFACE_KEYS)] == INTERFACE_KEYS
    hosts = URL_HOST.findall(text)
    assert [
        host
        for host in hosts
        if not (
            host.endswith("example.invalid") or host == "localhost" or host.startswith("192.0.2.")
        )
    ] == []


def _missing(path: Path) -> tuple[str, int]:
    return f"site: no site file at {path}; run: site init", 1


def _faulty(path: Path) -> tuple[str, int]:
    path.write_text("plain text\n", encoding="utf-8")
    return f"site: {path}:1: not a KEY=value line", 2


def _in_work_tree(path: Path) -> tuple[str, int]:
    make_work_tree(path.parent)
    path.write_text("SITE_A=x\n", encoding="utf-8")
    return in_repository(path), 3


@pytest.mark.parametrize(
    "words", [pytest.param(["show"], id="show"), pytest.param(["get", "SITE_A"], id="get")]
)
@pytest.mark.parametrize(
    "failing_load",
    [
        pytest.param(_missing, id="missing"),
        pytest.param(_faulty, id="faulty"),
        pytest.param(_in_work_tree, id="in-work-tree"),
    ],
)
def test_show_and_get_pass_on_a_failing_load(
    tmp_path: Path,
    site_file: Path,
    site_env: dict[str, str],
    words: list[str],
    failing_load: Callable[[Path], tuple[str, int]],
) -> None:
    message, status = failing_load(site_file)

    result = run_site(words, tmp_path, site_env)

    assert result.exit_status == status
    assert result.stdout == ""
    assert result.stderr.splitlines() == [message]


@pytest.mark.parametrize(
    "work_tree", [pytest.param(True, id="in-work-tree"), pytest.param(False, id="outside")]
)
def test_init_refuses_a_path_in_a_git_work_tree(tmp_path: Path, work_tree: bool) -> None:
    root = tmp_path / "root"
    if work_tree:
        make_work_tree(root)
    else:
        root.mkdir()
    path = root / "conf" / "site.env"
    env = operator_environment(tmp_path, FACTORY_SITE=str(path))

    result = run_site(["init"], tmp_path, env)

    if work_tree:
        assert result.exit_status == 3
        assert result.stderr.splitlines() == [in_repository(path)]
        assert not path.parent.exists()
    else:
        assert result.exit_status == 0, result.stderr
        assert path.read_bytes() == SITE_EXAMPLE.read_bytes()
