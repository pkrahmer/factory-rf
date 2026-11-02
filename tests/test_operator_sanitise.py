"""The operator's sanitiser, its filter and its leak check, run as children in `tmp_path`."""

from pathlib import Path

import pytest

from factory.adapters.process import ProcessResult
from operator_support import ROOT, operator_environment, run_script

SANITISE_COMMAND = ROOT / "operator" / "bin" / "sanitise"
HOST_RULE = r"corp\.example\.invalid => <company-host>"
GROUP_RULE = r"(\d+)-secret => \1-x"
UNRELATED_RULE = r"nevermatches => x"
ESCAPED = "\x1b[31mred\x1b[0m"
JWT = "eyJabcdefghij.abcdefghij1.abcdefghij2"
CLASSIC_TOKEN = "ghp_" + "a" * 30
FINE_GRAINED_TOKEN = "github_pat_" + "a" * 30
SHORT_PART_JWT = "eyJabcdefghij.abcdefghi.abcdefghij2"
TEN_PART_JWT = "eyJabcdefghij.abcdefghij.abcdefghij2"
SHORT_THIRD_PART_JWT = "eyJabcdefghij.abcdefghij1.abcdefghi"
TEN_THIRD_PART_JWT = "eyJabcdefghij.abcdefghij1.abcdefghij"
USAGE = "usage: sanitise < raw > clean | sanitise check FILE..."


@pytest.fixture
def site_folder(tmp_path: Path) -> Path:
    """A folder outside every repository that holds the site file `site.env`."""
    folder = tmp_path / "site"
    folder.mkdir()
    (folder / "site.env").write_text("SITE_PROJECT=p\n", encoding="utf-8")
    return folder


@pytest.fixture
def site_env(tmp_path: Path, site_folder: Path) -> dict[str, str]:
    """An environment whose `FACTORY_SITE` names the site file."""
    return operator_environment(tmp_path, FACTORY_SITE=str(site_folder / "site.env"))


def write_rules(site_folder: Path, *lines: str) -> Path:
    """Write the default rules file beside the site file."""
    path = site_folder / "sanitise.rules"
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    return path


def write_file(folder: Path, name: str, text: str) -> Path:
    """Write `text` to `name` in `folder`, exactly as given."""
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def run_filter(tmp_path: Path, env: dict[str, str], text: str) -> ProcessResult:
    """Run the filter with `text` on its standard input."""
    source = write_file(tmp_path, "filter-input.txt", text)
    return run_script(
        ["-c", 'sh "$1" < "$2"', "sanitise", str(SANITISE_COMMAND), str(source)], tmp_path, env
    )


def run_check(tmp_path: Path, env: dict[str, str], *files: Path) -> ProcessResult:
    """Run `sanitise check` on `files`."""
    return run_script(
        [str(SANITISE_COMMAND), "check", *(str(file) for file in files)], tmp_path, env
    )


def reports(result: ProcessResult) -> list[str]:
    """The report lines of a check (`<file>:<line>: <n>`), sorted."""
    return sorted(line for line in result.stdout.splitlines() if not line.startswith("sanitise:"))


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        pytest.param(ESCAPED, "red", id="escape-sequence"),
        pytest.param(f"auth {JWT} end", "auth ***JWT*** end", id="jwt"),
        pytest.param(f"key {CLASSIC_TOKEN} end", "key ***TOKEN*** end", id="ghp-token"),
        pytest.param(f"key {FINE_GRAINED_TOKEN} end", "key ***TOKEN*** end", id="github-pat-token"),
        pytest.param("ghp_short", "ghp_short", id="short-ghp"),
        pytest.param("eyJabc.def", "eyJabc.def", id="short-jwt"),
        pytest.param(SHORT_PART_JWT, SHORT_PART_JWT, id="jwt-second-part-of-9"),
        pytest.param(TEN_PART_JWT, "***JWT***", id="jwt-second-part-of-10"),
        pytest.param(SHORT_THIRD_PART_JWT, SHORT_THIRD_PART_JWT, id="jwt-third-part-of-9"),
        pytest.param(TEN_THIRD_PART_JWT, "***JWT***", id="jwt-third-part-of-10"),
        pytest.param("ghp_" + "a" * 19, "ghp_" + "a" * 19, id="ghp-of-19"),
        pytest.param("ghp_" + "a" * 20, "***TOKEN***", id="ghp-of-20"),
        pytest.param("github_pat_" + "a" * 19, "github_pat_" + "a" * 19, id="github-pat-of-19"),
        pytest.param("github_pat_" + "a" * 20, "***TOKEN***", id="github-pat-of-20"),
    ],
)
def test_built_in_rules_replace_escapes_jwts_and_tokens(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str], line: str, expected: str
) -> None:
    write_rules(site_folder, UNRELATED_RULE)

    result = run_filter(tmp_path, site_env, f"{line}\n")

    assert result.exit_status == 0
    assert result.stdout == f"{expected}\n"


@pytest.mark.parametrize(
    ("rule", "line", "expected"),
    [
        pytest.param(
            HOST_RULE,
            "a corp.example.invalid b corp.example.invalid",
            "a <company-host> b <company-host>",
            id="every-occurrence",
        ),
        pytest.param(
            HOST_RULE, "CORP.EXAMPLE.INVALID", "CORP.EXAMPLE.INVALID", id="case-sensitive"
        ),
        pytest.param(GROUP_RULE, "id 42-secret", "id 42-x", id="group"),
        pytest.param("  spaced   =>   S  ", "spaced", "S", id="both-parts-trimmed"),
        pytest.param("first => one => two", "first", "one => two", id="first-arrow-splits"),
        pytest.param(r"tab => x\ty", "a tab", r"a x\ty", id="other-backslash-literal"),
        pytest.param(r"zero => x\0y", "zero", r"x\0y", id="group-zero-literal"),
        pytest.param(
            r"(a)(b)(c)(d)(e)(f)(g)(h)(i)(j) => \100", "abcdefghij", "j0", id="two-digit-group"
        ),
        pytest.param(r"(a)|(b) => [\1\2]", "b", "[b]", id="unmatched-group-empty"),
    ],
)
def test_site_rule_replaces_every_occurrence_and_keeps_groups(
    tmp_path: Path,
    site_folder: Path,
    site_env: dict[str, str],
    *,
    rule: str,
    line: str,
    expected: str,
) -> None:
    write_rules(site_folder, rule)

    result = run_filter(tmp_path, site_env, f"{line}\n")

    assert result.exit_status == 0
    assert result.stdout == f"{expected}\n"


def test_drop_removes_lines_and_leak_leaves_the_output_alone(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str]
) -> None:
    write_rules(site_folder, "drop: noise", "leak: beta")

    result = run_filter(tmp_path, site_env, "one\nnoise a\ntwo beta\nnoise b\nthree\n")

    assert result.exit_status == 0
    assert result.stdout == "one\ntwo beta\nthree\n"


def test_site_rules_see_the_text_the_built_ins_left_in_file_order(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str]
) -> None:
    write_rules(site_folder, r"\*\*\*TOKEN\*\*\* => first", "first => second")

    result = run_filter(tmp_path, site_env, f"key {CLASSIC_TOKEN}\n")

    assert result.exit_status == 0
    assert result.stdout == "key second\n"


FAULTS = [
    pytest.param("no arrow here", "", id="no-kind"),
    pytest.param("[unclosed => x", "", id="invalid-pattern"),
    pytest.param("=> x", "", id="empty-replace-pattern"),
    pytest.param("drop:", "", id="empty-drop-pattern"),
    pytest.param("leak:", "", id="empty-leak-pattern"),
    pytest.param(
        r"(\d+)-x => \2", "replacement names group 2, the pattern has 1", id="missing-group"
    ),
    pytest.param(
        r"(\d+)-x => \10",
        "replacement names group 10, the pattern has 1",
        id="missing-two-digit-group",
    ),
]


def names_the_fault(output: str, rules: Path, reason: str) -> bool:
    """Whether `output` holds the fault's line, whole when its reason is fixed."""
    prefix = f"sanitise: {rules}:3: "
    if reason:
        return f"{prefix}{reason}" in output.splitlines()
    return any(line.startswith(prefix) for line in output.splitlines())


@pytest.mark.parametrize(("fault", "reason"), FAULTS)
def test_rules_file_fault_stops_the_filter(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str], fault: str, reason: str
) -> None:
    rules = write_rules(site_folder, HOST_RULE, "# a comment", fault)

    result = run_filter(tmp_path, site_env, "a corp.example.invalid b\n")

    assert result.exit_status == 2
    assert result.stdout == ""
    assert names_the_fault(result.stderr, rules, reason)


def test_missing_rules_file_warns_once_in_the_filter_and_stops_the_check(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str]
) -> None:
    rules = site_folder / "sanitise.rules"
    leaking = write_file(tmp_path, "leaking.txt", f"key {CLASSIC_TOKEN}\n")

    filtered = run_filter(tmp_path, site_env, f"{ESCAPED}\nkey {CLASSIC_TOKEN}\n")
    checked = run_check(tmp_path, site_env, leaking)

    warning = f"sanitise: no rules file at {rules}; only the built-in rules apply"
    assert filtered.exit_status == 0
    assert filtered.stdout == "red\nkey ***TOKEN***\n"
    assert filtered.stderr.splitlines().count(warning) == 1
    assert checked.exit_status == 3
    assert (
        f"sanitise: no rules file at {rules}; nothing to check against"
        in (checked.stdout + checked.stderr).splitlines()
    )
    assert str(leaking) not in checked.stdout


@pytest.mark.parametrize(
    ("setting", "from_environment"),
    [
        pytest.param("absolute", False, id="site-file-absolute"),
        pytest.param("rules/other.rules", False, id="site-file-relative"),
        pytest.param("absolute", True, id="environment-absolute"),
    ],
)
def test_named_rules_file_wins_over_the_default(
    tmp_path: Path,
    site_folder: Path,
    site_env: dict[str, str],
    setting: str,
    from_environment: bool,
) -> None:
    write_rules(site_folder, "word => default")
    other = site_folder / "rules" / "other.rules"
    other.parent.mkdir()
    other.write_text("word => other\n", encoding="utf-8")
    value = str(other) if setting == "absolute" else setting
    env = dict(site_env)
    if from_environment:
        env["SITE_SANITISE_RULES"] = value
    else:
        (site_folder / "site.env").write_text(
            f"SITE_PROJECT=p\nSITE_SANITISE_RULES={value}\n", encoding="utf-8"
        )

    result = run_filter(tmp_path, env, "word\n")

    assert result.exit_status == 0
    assert result.stdout == "other\n"


@pytest.mark.parametrize(
    ("text", "report", "secret"),
    [
        pytest.param(
            "one\ntwo\nhost corp.example.invalid\n", "3: 1", "corp.example.invalid", id="site-rule"
        ),
        pytest.param(f"one\nkey {CLASSIC_TOKEN}\n", "2: builtin-3", CLASSIC_TOKEN, id="token"),
    ],
)
def test_check_names_file_line_and_rule_but_never_the_text(
    tmp_path: Path,
    site_folder: Path,
    site_env: dict[str, str],
    *,
    text: str,
    report: str,
    secret: str,
) -> None:
    write_rules(site_folder, HOST_RULE)
    leaking = write_file(tmp_path, "leaking.txt", text)

    result = run_check(tmp_path, site_env, leaking)

    assert result.exit_status == 1
    assert f"{leaking}:{report}" in result.stdout.splitlines()
    assert secret not in result.stdout + result.stderr


def test_check_reports_clean_files_leaking_files_and_missing_files(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str]
) -> None:
    write_rules(site_folder, HOST_RULE)
    clean = write_file(tmp_path, "clean.txt", "nothing here\n")
    leaking = write_file(tmp_path, "leaking.txt", "at corp.example.invalid\n")
    missing = tmp_path / "missing.txt"

    only_clean = run_check(tmp_path, site_env, clean)
    one_of_two = run_check(tmp_path, site_env, clean, leaking)
    with_missing = run_check(tmp_path, site_env, leaking, missing)

    assert only_clean.exit_status == 0
    assert "sanitise: clean" in only_clean.stdout.splitlines()
    assert one_of_two.exit_status == 1
    assert reports(one_of_two) == [f"{leaking}:1: 1"]
    assert with_missing.exit_status == 2
    assert (with_missing.stdout + with_missing.stderr).splitlines() == [
        f"sanitise: {missing}: no such file"
    ]


def test_check_reports_once_per_line_and_rule(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str]
) -> None:
    write_rules(site_folder, "alpha => A", "leak: beta")
    leaking = write_file(
        tmp_path,
        "leaking.txt",
        f"alpha beta\nx\nalpha\nalpha alpha\nkeys {CLASSIC_TOKEN} {FINE_GRAINED_TOKEN}\n",
    )

    result = run_check(tmp_path, site_env, leaking)

    assert result.exit_status == 1
    assert reports(result) == sorted(
        [
            f"{leaking}:1: 1",
            f"{leaking}:1: 2",
            f"{leaking}:3: 1",
            f"{leaking}:4: 1",
            f"{leaking}:5: builtin-3",
        ]
    )


def test_sanitised_output_passes_the_check(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str]
) -> None:
    write_rules(site_folder, HOST_RULE, GROUP_RULE, "drop: noise")
    raw = "\n".join(
        [
            f"{ESCAPED} at corp.example.invalid",
            f"auth {JWT}",
            f"keys {CLASSIC_TOKEN} {FINE_GRAINED_TOKEN}",
            "noise here",
            "id 42-secret",
            "plain",
        ]
    )

    filtered = run_filter(tmp_path, site_env, f"{raw}\n")
    clean = write_file(tmp_path, "clean.txt", filtered.stdout)
    checked = run_check(tmp_path, site_env, clean)

    assert filtered.exit_status == 0
    assert checked.exit_status == 0
    assert "sanitise: clean" in checked.stdout.splitlines()


@pytest.mark.parametrize(
    ("line", "rule"),
    [
        pytest.param(ESCAPED, "builtin-1", id="escape-sequence"),
        pytest.param(f"auth {JWT}", "builtin-2", id="jwt"),
        pytest.param(f"key {CLASSIC_TOKEN}", "builtin-3", id="ghp-token"),
        pytest.param(f"key {FINE_GRAINED_TOKEN}", "builtin-3", id="github-pat-token"),
        pytest.param(f"auth {SHORT_PART_JWT}", "", id="jwt-second-part-of-9"),
        pytest.param(f"auth {SHORT_THIRD_PART_JWT}", "", id="jwt-third-part-of-9"),
        pytest.param("key ghp_" + "a" * 19, "", id="ghp-of-19"),
        pytest.param("key github_pat_" + "a" * 19, "", id="github-pat-of-19"),
    ],
)
def test_check_reports_every_built_in(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str], line: str, rule: str
) -> None:
    write_rules(site_folder, UNRELATED_RULE)
    checked = write_file(tmp_path, "checked.txt", f"{line}\n")

    result = run_check(tmp_path, site_env, checked)

    if rule:
        assert result.exit_status == 1
        assert reports(result) == [f"{checked}:1: {rule}"]
    else:
        assert result.exit_status == 0
        assert result.stdout.splitlines() == ["sanitise: clean"]


def test_check_numbers_only_rule_lines(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str]
) -> None:
    write_rules(
        site_folder, "# a comment", "", "alpha => A", "# another", "", "drop: noise", "leak: beta"
    )
    leaking = write_file(tmp_path, "leaking.txt", "x\nnoise here\nbeta\n")

    result = run_check(tmp_path, site_env, leaking)

    assert result.exit_status == 1
    assert reports(result) == [f"{leaking}:2: 2", f"{leaking}:3: 3"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("a\nb", "a\nb\n", id="last-line-without-newline"),
        pytest.param("", "", id="empty-input"),
    ],
)
def test_filter_ends_every_line_with_a_newline(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str], text: str, expected: str
) -> None:
    write_rules(site_folder, UNRELATED_RULE)

    result = run_filter(tmp_path, site_env, text)

    assert result.exit_status == 0
    assert result.stdout == expected


@pytest.mark.parametrize(("fault", "reason"), FAULTS)
def test_rules_file_fault_stops_the_check_before_any_file(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str], fault: str, reason: str
) -> None:
    rules = write_rules(site_folder, HOST_RULE, "# a comment", fault)
    leaking = write_file(tmp_path, "leaking.txt", f"at corp.example.invalid {CLASSIC_TOKEN}\n")

    result = run_check(tmp_path, site_env, leaking)

    assert result.exit_status == 2
    assert str(leaking) not in result.stdout
    assert names_the_fault(result.stdout + result.stderr, rules, reason)


@pytest.mark.parametrize(
    "setting",
    [
        pytest.param("absolute", id="absolute"),
        pytest.param("rules/environment.rules", id="relative-to-site-folder"),
    ],
)
def test_environment_rules_file_wins_over_the_site_file(
    tmp_path: Path, site_folder: Path, site_env: dict[str, str], setting: str
) -> None:
    (site_folder / "rules").mkdir()
    from_site = site_folder / "rules" / "site.rules"
    from_site.write_text("word => site\n", encoding="utf-8")
    from_environment = site_folder / "rules" / "environment.rules"
    from_environment.write_text("word => environment\n", encoding="utf-8")
    (site_folder / "site.env").write_text(
        f"SITE_PROJECT=p\nSITE_SANITISE_RULES={from_site}\n", encoding="utf-8"
    )
    value = str(from_environment) if setting == "absolute" else setting

    result = run_filter(tmp_path, {**site_env, "SITE_SANITISE_RULES": value}, "word\n")

    assert result.exit_status == 0
    assert result.stdout == "environment\n"


@pytest.mark.parametrize(
    ("arguments", "site_exists", "expected"),
    [
        pytest.param(["frobnicate"], True, "usage", id="other-argument"),
        pytest.param(["check"], True, "usage", id="check-without-file"),
        pytest.param([], False, "site", id="missing-site-file"),
    ],
)
def test_wrong_call_or_missing_site_file_stops_the_command(
    tmp_path: Path,
    site_folder: Path,
    site_env: dict[str, str],
    *,
    arguments: list[str],
    site_exists: bool,
    expected: str,
) -> None:
    write_rules(site_folder, UNRELATED_RULE)
    absent = tmp_path / "absent" / "site.env"
    env = site_env if site_exists else {**site_env, "FACTORY_SITE": str(absent)}
    source = write_file(tmp_path, "input.txt", "plain\n")

    result = run_script(
        ["-c", 'command="$1"; source="$2"; shift 2; sh "$command" "$@" < "$source"', "sanitise"]
        + [str(SANITISE_COMMAND), str(source), *arguments],
        tmp_path,
        env,
    )

    message = USAGE if expected == "usage" else f"site: no site file at {absent}; run: site init"
    assert result.exit_status == 2
    assert result.stdout == ""
    assert message in result.stderr.splitlines()
