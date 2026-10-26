"""The machine's setup script, pinned by its text: the steps, their commands and their files."""

import re
from collections.abc import Callable
from dataclasses import dataclass

import pytest

from vm_support import FUNCTION, STEPS, setup_code, step_texts, write_helpers

ORDERED_COMMANDS = (
    "apt-get install -y --no-install-recommends",
    "zpool create -o ashift=12 -O compression=lz4 -O atime=off",
    "useradd --create-home --shell /bin/bash factory",
    "loginctl enable-linger factory",
    "zfs create",
    "zfs set compression=lz4 atime=off",
    "zfs set quota=",
    "zfs allow -u factory snapshot,destroy,rollback,diff,mount",
    "/etc/sudoers.d/factory-zfs",
    "/etc/sudoers.d/factory-drop-caches",
    "/home/factory/.secrets",
    "image-id",
    "/proc/sys/kernel/random/uuid",
    "hosting-token",
    "git clone -q --branch",
    "ARG UV_VERSION=",
    "python3 -m venv",
    "uv sync --frozen --no-dev",
    "/usr/local/bin/git-credential-factory",
    "factory.env",
    "factory@.service",
    "systemctl daemon-reload",
    "systemctl enable factory@",
)
PACKAGES = "zfsutils-linux podman uidmap slirp4netns git make python3.12-venv"
SUBID_LINE = (
    "setup: user: no subuid and subgid range for factory;"
    " add one with usermod --add-subuids and --add-subgids"
)
VALUE_END = r"(?![\w/.:{$-])"


@dataclass(frozen=True)
class Script:
    """The setup script's text and its steps' texts."""

    code: str
    steps: dict[str, str]


Check = Callable[[Script], bool]


@pytest.fixture
def script(code: str) -> Script:
    """Return the setup script's text and each step's text."""
    return Script(code, step_texts(code))


def _lines_with(text: str, word: str) -> list[str]:
    return [line for line in text.splitlines() if word in line]


def _in_order(text: str, words: list[str]) -> bool:
    positions = [text.find(word) for word in words]
    return -1 not in positions and positions == sorted(positions)


def test_the_commands_and_the_steps_come_in_their_order(code: str) -> None:
    assert [command for command in ORDERED_COMMANDS if command not in code] == []
    assert _in_order(code, list(ORDERED_COMMANDS))
    markers = [f"setup: {step}: " for step in STEPS]
    assert [marker for marker in markers if marker not in code] == []
    assert _in_order(code, markers)


def test_the_packages_are_the_seven_and_updated_before_install(code: str) -> None:
    joined = re.sub(r"\\\n", " ", code)
    lists = re.findall(r"zfsutils-linux(?:[ \t]+[\w.+-]+)*", joined)

    assert [" ".join(found.split()) for found in lists] == [PACKAGES]
    assert _in_order(code, ["apt-get update", "apt-get install"])


SECRETS_REDIRECT = re.compile(r">>?[\s\"']*[^\s;|&]*\.secrets")


@pytest.mark.parametrize(
    "forbidden",
    [
        pytest.param(
            lambda line: re.search(r"\b(?:curl|wget)\b.*\|\s*(?:ba)?sh\b", line), id="pipe"
        ),
        pytest.param(lambda line: "[ -b " in line, id="block-test-bracket"),
        pytest.param(lambda line: "test -b " in line, id="block-test"),
        pytest.param(lambda line: "latest" in line, id="latest"),
        pytest.param(lambda line: "systemctl start" in line, id="start"),
        pytest.param(lambda line: "enable --now" in line, id="enable-now"),
        pytest.param(lambda line: "FACTORY_AGENT_USER" in line, id="agent-user"),
        *(
            pytest.param(
                lambda line, form=form: ".secrets" in line and form in line, id=f"secrets-{form}"
            )
            for form in ("rm ", "mv ", "cp ", "tee ", "truncate", " -R ")
        ),
        pytest.param(
            lambda line: ".secrets" in line and SECRETS_REDIRECT.search(line),
            id="secrets-redirect",
        ),
    ],
)
def test_the_script_holds_no_forbidden_form(code: str, forbidden: Callable[[str], object]) -> None:
    assert [line for line in code.splitlines() if forbidden(line)] == []


@pytest.mark.parametrize(
    ("rule", "last"),
    [("snapshot ", False), ("destroy ", False), ("rollback -r ", False), ("diff -FH ", True)],
)
def test_the_sudoers_rule_names_each_zfs_command_once_on_base(rule: str, last: bool) -> None:
    code = setup_code()
    found = re.findall(re.escape(f"/usr/sbin/zfs {rule}") + r"(\S*)", code)

    assert len(found) == 1
    word = found[0]
    assert word.endswith("@base") or (not last and word.endswith("@base,"))


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(lambda s: "diff -H " not in s.code, id="no-diff-H"),
        *(
            pytest.param(lambda s, word=word: word in s.code, id=word)
            for word in (
                "factory ALL=(root) NOPASSWD:",
                "chmod 0440",
                "visudo -cf",
                "/usr/local/bin/zfs-factory",
                "rollback|destroy|snapshot|diff)",
                'exec sudo -n /usr/sbin/zfs "$@"',
                'exec /usr/sbin/zfs "$@"',
            )
        ),
        pytest.param(lambda s: _if_before_zfs(s.steps["sudoers"]), id="if-before-the-files"),
        pytest.param(
            lambda s: any(
                "zfs allow" in line.partition("setup: sudoers: ")[2]
                for line in _lines_with(s.code, "setup: sudoers: ")
            ),
            id="not-asked-names-zfs-allow",
        ),
    ],
)
def test_the_sudoers_fallback_is_written_only_when_asked(script: Script, check: Check) -> None:
    assert check(script)


def _if_before_zfs(text: str) -> bool:
    lines = text.splitlines()
    first = next(index for index, line in enumerate(lines) if "/usr/sbin/zfs" in line)
    return any(line.lstrip().startswith("if ") for line in lines[:first])


ENVIRONMENT = (
    ("FACTORY_INSTANCE", re.escape("$instance") + VALUE_END),
    ("FACTORY_REPOSITORY_URL", re.escape("$repository_url") + VALUE_END),
    ("FACTORY_AGENT_RUNTIME", re.escape("$runtime") + VALUE_END),
    ("FACTORY_DATASET", re.escape("$pool/factory/$instance") + VALUE_END),
    ("FACTORY_WORKSPACE", re.escape("$base/work") + VALUE_END),
    ("FACTORY_STAGE_IMAGE", re.escape("$image") + VALUE_END),
    ("FACTORY_ZFS", r"\$"),
    ("FACTORY_CHECKOUT", re.escape("$base/repo") + VALUE_END),
    ("FACTORY_STATE", re.escape("$base/state") + VALUE_END),
    ("FACTORY_IMAGE_ID_FILE", re.escape("$base/image-id") + VALUE_END),
    ("FACTORY_CLAUDE_HOME", re.escape("$base/factory/claude") + VALUE_END),
    ("FACTORY_TOKEN_FILE", re.escape("/home/factory/.secrets/hosting-token") + VALUE_END),
    ("FACTORY_CLAUDE_LOGIN_FILE", re.escape("/home/factory/.secrets/claude-token") + VALUE_END),
    ("FACTORY_API_LOGIN_FILE", re.escape("/home/factory/.secrets/anthropic-api-key") + VALUE_END),
    ("FACTORY_CLAUDE_VERSION", r"\$(?P<pin>[A-Za-z_]\w*)" + VALUE_END),
    ("FACTORY_OPENCODE_VERSION", r"\$(?P<pin>[A-Za-z_]\w*)" + VALUE_END),
    ("FACTORY_OPENCODE_MODELS", r"\$(?P<pin>[A-Za-z_]\w*)" + VALUE_END),
    (
        "PATH",
        re.escape("/srv/factory/")
        + r"\S*"
        + re.escape("/tools/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"),
    ),
    ("XDG_RUNTIME_DIR", re.escape("/run/user/$(id -u factory)") + VALUE_END),
)
PINS = {
    "FACTORY_CLAUDE_VERSION": "ARG CLAUDE_CODE_VERSION=",
    "FACTORY_OPENCODE_VERSION": "ARG OPENCODE_VERSION=",
    "FACTORY_OPENCODE_MODELS": "ENV FACTORY_OPENCODE_MODELS=",
}


def _name_positions(code: str, name: str) -> list[int]:
    return [
        found.start()
        for found in re.finditer(rf"(?<![A-Za-z_]){name}=", code)
        if not code[: found.start()].endswith("ENV ")
    ]


@pytest.mark.parametrize(
    ("index", "name", "value"), [(i, *row) for i, row in enumerate(ENVIRONMENT)]
)
def test_the_environment_file_holds_each_name_once_with_its_value(
    code: str, index: int, name: str, value: str
) -> None:
    positions = _name_positions(code, name)

    assert len(positions) == 1
    position = positions[0]
    assert code.find("factory.env") < position < code.find("factory@.service")
    if index > 0:
        assert _name_positions(code, ENVIRONMENT[index - 1][0]) < [position]
    line_end = code.find("\n", position)
    line = code[position : len(code) if line_end < 0 else line_end]
    matched = re.match(rf"{name}={value}", line)
    assert matched is not None, line
    if name in PINS:
        variable = matched["pin"]
        assignments = re.findall(rf"(?m)^.*(?<![\w$]){variable}=.*$", code)
        assert [line for line in assignments if PINS[name] in line] != []


@pytest.mark.parametrize(
    "check",
    [
        *(pytest.param(lambda s, pin=pin: pin in s.code, id=pin) for pin in PINS.values()),
        pytest.param(lambda s: "FACTORY_PODMAN" not in s.code, id="no-podman"),
        pytest.param(lambda s: "=zfs" in s.steps["sudoers"], id="plain-zfs"),
        pytest.param(
            lambda s: "=/usr/local/bin/zfs-factory" in s.steps["sudoers"], id="wrapper-zfs"
        ),
    ],
)
def test_the_environment_file_reads_its_pins_and_picks_the_zfs_command(
    script: Script, check: Check
) -> None:
    assert check(script)


def _before_end_of_line(text: str, earlier: str, word: str) -> bool:
    position = text.find(word)
    end = text.find("\n", position)
    return position >= 0 and earlier in text[: len(text) if end < 0 else end]


def _waiting_then_exit(text: str) -> bool:
    waiting = [
        line
        for line in _lines_with(text, "waiting for /home/factory/.secrets/hosting-token")
        if "run this script again" in line
    ]
    if not waiting:
        return False
    after = text[text.find(waiting[0]) :]
    return "exit 0" in after and after.find("exit 0") < after.find("git clone")


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(lambda s: _waiting_then_exit(s.steps["checkout"]), id="waiting"),
        pytest.param(
            lambda s: "Username" in s.steps["checkout"] and "x-access-token" in s.steps["checkout"],
            id="askpass-answers",
        ),
        *(
            pytest.param(
                lambda s, word=word: _before_end_of_line(
                    s.steps["checkout"], word, "git clone -q --branch"
                ),
                id=word,
            )
            for word in ("GIT_ASKPASS=", "GIT_TERMINAL_PROMPT=0")
        ),
        pytest.param(
            lambda s: any(
                "--config core.askPass=" in line
                for line in _lines_with(s.code, "git clone -q --branch")
            ),
            id="clone-writes-askpass",
        ),
        pytest.param(lambda s: "git config" not in s.code, id="no-git-config"),
        *(
            pytest.param(
                lambda s, later=later: _in_order(s.code, ["runuser -u factory --", later]),
                id=f"runuser-before-{later}",
            )
            for later in ("git clone", "uv sync")
        ),
        pytest.param(
            lambda s: any("0700" in line for line in _lines_with(s.code, "/home/factory/.secrets")),
            id="secrets-0700",
        ),
        pytest.param(lambda s: "0755" in s.steps["folders"], id="folders-0755"),
        pytest.param(lambda s: "0644" in s.steps["image-id"], id="image-id-0644"),
    ],
)
def test_the_checkout_waits_for_the_token_and_clones_as_factory(
    script: Script, check: Check
) -> None:
    assert check(script)


def _after_in_order(text: str, first: str, words: list[str]) -> bool:
    position = text.find(first)
    return position >= 0 and _in_order(text[position:], words)


AS_FACTORY = ("chown factory:factory", "-o factory -g factory")
OWN_WORD_BASE = re.compile(r"(?:^|\s)\"?\$base\"?(?:\s|$)")


@pytest.mark.parametrize(
    "check",
    [
        *(
            pytest.param(lambda s, word=word: word in s.steps["user"], id=f"user-{word}")
            for word in ("/etc/subuid", "/etc/subgid", "exit 1")
        ),
        pytest.param(lambda s: SUBID_LINE in s.steps["user"], id="subid-line"),
        pytest.param(
            lambda s: _after_in_order(
                s.steps["sudoers"], "visudo -cf", ["rm -f /etc/sudoers.d/factory-zfs", "exit 1"]
            ),
            id="failed-visudo-removes",
        ),
        pytest.param(
            lambda s: any(
                "0755" in line
                for line in _lines_with(s.steps["sudoers"], "/usr/local/bin/zfs-factory")
            ),
            id="wrapper-0755",
        ),
        *(
            pytest.param(lambda s, word=word: word in s.steps["tools"], id=f"tools-{word}")
            for word in ("pip", "install", "uv==", "uv --version")
        ),
        pytest.param(lambda s: "0755" in s.steps["checkout"], id="askpass-0755"),
        pytest.param(lambda s: "0644" in s.steps["environment"], id="environment-0644"),
        pytest.param(lambda s: "0644" in s.steps["service"], id="service-0644"),
        *(
            pytest.param(lambda s, guard=guard: guard in s.code, id=f"guard-{guard}")
            for guard in ("zpool list -H -o name", "id factory", "/.git", "-s ")
        ),
        pytest.param(lambda s: s.code.count("base=/srv/factory/$instance") == 1, id="base-once"),
        pytest.param(
            lambda s: any(owner in s.steps["datasets"] for owner in AS_FACTORY),
            id="mount-point-owner",
        ),
        pytest.param(
            lambda s: any(
                OWN_WORD_BASE.search(line)
                for line in s.steps["folders"].splitlines()
                if any(owner in line for owner in AS_FACTORY)
            ),
            id="instance-folder-owner",
        ),
        *(
            pytest.param(lambda s, step=step: "found" in s.steps[step], id=f"found-{step}")
            for step in STEPS
        ),
        pytest.param(
            lambda s: any(
                'see the operator guide, "The machine"' in line
                for line in _lines_with(
                    s.code[s.code.rfind("setup: service: ") :],
                    "setup: done: build the stage image and start factory@",
                )
            ),
            id="done-line",
        ),
    ],
)
def test_the_refusals_modes_and_rerun_guards_are_in_their_steps(
    script: Script, check: Check
) -> None:
    assert check(script)


OPTION_PARSING = re.compile(r"\bcase\s+\"?\$\{?1\b")


@pytest.mark.parametrize(
    "assignment", ["instance=vm", "pool=tank", "quota=30G", "ref=main", "runtime=claude"]
)
def test_each_default_is_assigned_once_before_the_option_parsing(
    code: str, assignment: str
) -> None:
    found = [match.start() for match in re.finditer(rf"(?<![\w$-]){re.escape(assignment)}\b", code)]
    parsing = OPTION_PARSING.search(code)

    assert len(found) == 1
    assert parsing is not None
    assert found[0] < parsing.start()


@pytest.mark.parametrize(
    ("option", "variable"),
    [
        ("instance", "instance"),
        ("pool", "pool"),
        ("quota", "quota"),
        ("ref", "ref"),
        ("runtime", "runtime"),
        ("image", "image"),
        ("device", "device"),
        ("repository-url", "repository_url"),
    ],
)
def test_the_options_land_in_their_named_variables(code: str, option: str, variable: str) -> None:
    parse = re.compile(rf"(?<![\w-])--{re.escape(option)}\)[^\n]*(?<![\w$]){variable}=")

    assert parse.search(code)


def test_the_image_defaults_to_one_named_after_the_instance(code: str) -> None:
    assert "image=factory-stage:$instance" in code


WRITE_FORMS = ("install ", "cp ", "mv ", "tee ")


def _under_base(code: str) -> list[str]:
    variables = re.findall(r"(?m)^\s*(\w+)=\"?\$\{?base\}?/", code)
    return [rf"\$\{{?{name}(?!\w)" for name in ("base", *variables)]


def _calls(line: str, names: list[str]) -> bool:
    return any(re.search(rf"(?<![\w-]){name}(?![\w-])", line) for name in names)


def _writes(line: str, path: str, helpers: list[str]) -> bool:
    if not re.search(path, line):
        return False
    redirect = re.search(rf">>?[\s\"']*(?:{path})", line)
    return (
        redirect is not None or any(form in line for form in WRITE_FORMS) or _calls(line, helpers)
    )


def _as_factory(code: str, line: str) -> bool:
    helpers = [name for name, body in FUNCTION.findall(code) if "runuser -u factory" in body]
    helpers += write_helpers(code)
    return "runuser -u factory" in line or _calls(line, helpers)


def _written_as_factory(script: Script, step: str, name: str) -> bool:
    file = rf"\$\{{?base\}}?/{re.escape(name)}"
    variables = re.findall(rf"(?m)^\s*(\w+)=\"?{file}\"?\s*$", script.code)
    paths = [rf"{file}(?![\w.-])", *(rf"\$\{{?{found}(?!\w)" for found in variables)]
    helpers = write_helpers(script.code)
    writes = [
        line
        for line in script.steps[step].splitlines()
        if any(_writes(line, path, helpers) for path in paths)
    ]
    return writes != [] and all(_as_factory(script.code, line) for line in writes)


def _chown_without_h(script: Script) -> list[str]:
    found = []
    for line in script.code.splitlines():
        chown = re.search(r"(?<![\w-])chown((?:\s+-[\w-]+)*)", line)
        if chown is None or not any(re.search(path, line) for path in _under_base(script.code)):
            continue
        options = chown.group(1).split()
        if not any(
            option == "--no-dereference" or (not option.startswith("--") and "h" in option)
            for option in options
        ):
            found.append(line)
    return found


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(lambda s: _written_as_factory(s, "image-id", "image-id"), id="image-id"),
        pytest.param(lambda s: _written_as_factory(s, "checkout", "askpass"), id="askpass"),
        pytest.param(
            lambda s: _written_as_factory(s, "environment", "factory.env"), id="factory-env"
        ),
        pytest.param(lambda s: _chown_without_h(s) == [], id="chown-keeps-links"),
    ],
)
def test_the_files_under_the_instance_folder_are_written_as_factory(
    script: Script, check: Check
) -> None:
    assert check(script)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _enclosing_if(lines: list[str], index: int) -> int | None:
    for earlier in range(index - 1, -1, -1):
        line = lines[earlier]
        if line.strip() and _indent(line) < _indent(lines[index]):
            return earlier if line.lstrip().startswith("if ") else None
    return None


def _clone_variables(checkout: str) -> list[str]:
    lines = checkout.splitlines()
    clone = next((i for i, line in enumerate(lines) if "git clone" in line), None)
    start = None if clone is None else _enclosing_if(lines, clone)
    if start is None:
        return []
    branch = []
    for line in lines[start + 1 :]:
        if line.strip() and _indent(line) <= _indent(lines[start]):
            break
        branch.append(line)
    return re.findall(r"(?m)^\s*(\w+)=", "\n".join(branch))


def _install_conditions(script: Script, step: str, path: str) -> list[str] | None:
    lines = script.steps[step].splitlines()
    installs = [
        i
        for i, line in enumerate(lines)
        if re.search(r"(?<![\w-])install\s", line) and path in line
    ]
    conditions = [_enclosing_if(lines, i) for i in installs]
    if installs == [] or None in conditions:
        return None
    return [lines[condition] for condition in conditions if condition is not None]


def _tests_the_clone(script: Script, condition: str, _path: str) -> bool:
    variables = _clone_variables(script.steps["checkout"])
    return any(re.search(rf"\$\{{?{name}(?!\w)", condition) for name in variables)


def _tests_the_missing_target(_script: Script, condition: str, path: str) -> bool:
    missing = rf"\[\s+!\s+-e\s+\"?{re.escape(path)}\"?\s+\]"
    return re.search(rf"\|\|\s*{missing}|{missing}\s*\|\|", condition) is not None


@pytest.mark.parametrize(
    ("step", "path"),
    [
        ("tools", "/usr/local/bin/git-credential-factory"),
        ("service", "/etc/systemd/system/factory@.service"),
    ],
)
@pytest.mark.parametrize(
    "side",
    [
        pytest.param(_tests_the_clone, id="cloned"),
        pytest.param(_tests_the_missing_target, id="target-missing"),
    ],
)
def test_the_checkout_files_are_installed_only_in_the_run_that_cloned(
    script: Script, step: str, path: str, side: Callable[[Script, str, str], bool]
) -> None:
    conditions = _install_conditions(script, step, path)

    assert conditions is not None
    assert all(side(script, condition, path) for condition in conditions)
    assert [
        line
        for line in _lines_with(script.steps[step], f"setup: {step}: ")
        if "differs from the checkout; not installed" in line
    ] != []


def _before_first_install_d(text: str) -> str:
    position = text.find("install -d")
    return text if position < 0 else text[:position]


@pytest.mark.parametrize(
    "check",
    [
        *(
            pytest.param(
                lambda text, folder=folder: re.search(
                    rf"-L\s+\"?\$\{{?base\}}?/{folder}(?![\w.-])", text
                ),
                id=f"link-test-{folder}",
            )
            for folder in ("state", "repo")
        ),
        pytest.param(
            lambda text: re.search(r"-L\s+\"?/home/factory/\.secrets(?![\w.-])", text),
            id="link-test-secrets",
        ),
        pytest.param(
            lambda text: [line for line in _lines_with(text, "setup: folders: ") if ">&2" in line],
            id="line-to-standard-error",
        ),
        pytest.param(lambda text: "exit 1" in text, id="exit-1"),
    ],
)
def test_the_folders_step_refuses_a_link_at_state_or_repo(
    script: Script, check: Callable[[str], object]
) -> None:
    folders = script.steps["folders"]

    assert "install -d" in folders
    assert check(_before_first_install_d(folders))
