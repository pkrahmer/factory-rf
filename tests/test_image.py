"""The machine's image: nothing in its build floats, and its identity is generated at build."""

import importlib.metadata
import re
import shlex
import tomllib
from pathlib import Path

import pytest

from dockerfile_support import _after, _apt_packages, _uncommented

ROOT = Path(__file__).parent.parent
DOCKERFILE = ROOT / "image" / "Dockerfile"
PYPROJECT = ROOT / "pyproject.toml"
LOCKFILE = ROOT / "uv.lock"
TEMPLATE = ROOT / "template"
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
THREE_NUMBERS = re.compile(r"^\d+\.\d+\.\d+$")
NPM_PINNED = re.compile(r"@\d+\.\d+\.\d+$")
APT_PINNED = re.compile(r"^[^=\s]+=(?!\*$)\S+$")
PIP_PINNED = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\[\],-]*==[^=<>*\s]+$")
SHELL_OPERATOR = re.compile(r"&&|\|\||;")
VARIABLE = re.compile(r"\$\{(\w+)\}|\$(\w+)")
LATEST = re.compile(r"\blatest\b")
IMAGE_ID_COMMAND = "cat /proc/sys/kernel/random/uuid > /opt/factory/image-id"
APT_PACKAGES = ["git", "make", "curl", "ca-certificates", "procps", "sudo", "nodejs", "npm"]
PRODUCTION_DEPENDENCIES = ["pydantic", "PyGithub", "ruamel.yaml", "python-frontmatter"]
DOCKER_KEYWORDS = {"FROM", "ARG", "ENV", "LABEL", "COPY", "USER", "WORKDIR", "ENTRYPOINT", "RUN"}
Instruction = tuple[str, str]
Command = list[str]


def _instructions(dockerfile: str) -> list[Instruction]:
    """Every instruction as (keyword, arguments), continuations joined, comments dropped."""
    joined = re.sub(r"\\\n", " ", _uncommented(dockerfile))
    result: list[Instruction] = []
    for line in joined.splitlines():
        if line.strip():
            keyword, _, arguments = line.strip().partition(" ")
            if keyword.upper() in DOCKER_KEYWORDS:
                keyword = keyword.upper()
            result.append((keyword, " ".join(arguments.split())))
    return result


def _arg_defaults(instructions: list[Instruction], *, before_from: bool) -> dict[str, str]:
    defaults: dict[str, str] = {}
    for keyword, arguments in instructions:
        if keyword == "FROM" and before_from:
            break
        if keyword == "ARG" and "=" in arguments:
            name, _, value = arguments.partition("=")
            defaults[name] = value
    return defaults


def _substitute(text: str, defaults: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2)
        return defaults.get(name, match.group(0))

    return VARIABLE.sub(replace, text)


def _pipelines(arguments: str) -> list[list[Command]]:
    """The shell pipelines of `arguments`, each a list of commands, each a list of words."""
    pipelines: list[list[Command]] = []
    for part in SHELL_OPERATOR.split(arguments):
        commands = [shlex.split(segment) for segment in part.split("|")]
        pipelines.append([command for command in commands if command])
    return [pipeline for pipeline in pipelines if pipeline]


def _shell_lines(instructions: list[Instruction]) -> list[str]:
    """The text of every instruction that may hold shell commands: RUN, or a bare line."""
    return [
        arguments if keyword == "RUN" else f"{keyword} {arguments}".strip()
        for keyword, arguments in instructions
        if keyword == "RUN" or keyword not in DOCKER_KEYWORDS
    ]


def _commands(dockerfile: str) -> list[Command]:
    instructions = _instructions(dockerfile)
    return [
        command
        for line in _shell_lines(instructions)
        for pipeline in _pipelines(line)
        for command in pipeline
    ]


def _apt_findings(command: Command) -> list[str]:
    found = _after(command, "apt-get", {"install", "upgrade", "dist-upgrade"})
    if found is None:
        return []
    subcommand, packages = found
    if subcommand != "install":
        return [f"apt-get {subcommand}"]
    return [f"apt package {package}" for package in packages if not APT_PINNED.match(package)]


def _pip_findings(command: Command) -> list[str]:
    found = _after(command, "pip", {"install"})
    if found is None:
        return []
    return [f"pip requirement {each}" for each in found[1] if not PIP_PINNED.match(each)]


def _npm_findings(command: Command) -> list[str]:
    findings = ["npx"] if "npx" in command else []
    found = _after(command, "npm", {"install", "i"})
    if found is not None:
        findings += [f"npm package {each}" for each in found[1] if not NPM_PINNED.search(each)]
    return findings


def _uv_findings(command: Command) -> list[str]:
    tool = _after(command, "uv", {"tool"})
    if tool is not None and tool[1][:1] == ["install"]:
        return ["uv tool install"]
    sync = _after(command, "uv", {"sync"})
    if sync is not None and not {"--frozen", "--locked"} & set(command):
        return ["uv sync without --frozen or --locked"]
    return []


def _piped_download_findings(pipeline: list[Command]) -> list[str]:
    programs = [Path(command[0]).name for command in pipeline]
    for index, program in enumerate(programs):
        if program in {"curl", "wget"} and {"sh", "bash"} & set(programs[index + 1 :]):
            return [f"{program} piped into a shell"]
    return []


def _from_references(instructions: list[Instruction]) -> list[str]:
    """Every FROM image reference, with the ARG defaults before the first FROM substituted."""
    defaults = _arg_defaults(instructions, before_from=True)
    return [
        _substitute(next(word for word in arguments.split() if not word.startswith("--")), defaults)
        for keyword, arguments in instructions
        if keyword == "FROM"
    ]


def _from_findings(instructions: list[Instruction]) -> list[str]:
    return [f"FROM {each}" for each in _from_references(instructions) if not DIGEST.search(each)]


def _claude_version_findings(instructions: list[Instruction]) -> list[str]:
    return [
        f"ARG {arguments}"
        for keyword, arguments in instructions
        if keyword == "ARG"
        and arguments.partition("=")[0] == "CLAUDE_CODE_VERSION"
        and not THREE_NUMBERS.match(arguments.partition("=")[2])
    ]


def floating_references(dockerfile: str) -> list[str]:
    """One finding per item of `dockerfile` whose version can change between two builds."""
    instructions = _instructions(dockerfile)
    defaults = _arg_defaults(instructions, before_from=False)
    findings = _from_findings(instructions) + _claude_version_findings(instructions)
    for line in _shell_lines(instructions):
        for pipeline in _pipelines(_substitute(line, defaults)):
            findings += _piped_download_findings(pipeline)
            for command in pipeline:
                findings += _apt_findings(command) + _pip_findings(command)
                findings += _npm_findings(command) + _uv_findings(command)
    findings += [
        f"latest in {keyword} {arguments}"
        for keyword, arguments in instructions
        if LATEST.search(arguments) or LATEST.search(keyword)
    ]
    return findings


@pytest.fixture
def dockerfile() -> str:
    return DOCKERFILE.read_text(encoding="utf-8")


@pytest.fixture
def instructions(dockerfile: str) -> list[Instruction]:
    return _instructions(dockerfile)


def _env(instructions: list[Instruction]) -> dict[str, str]:
    pairs = [
        pair.partition("=")
        for keyword, arguments in instructions
        if keyword == "ENV"
        for pair in arguments.split()
    ]
    return {name: value for name, _, value in pairs}


def _indices(instructions: list[Instruction], keyword: str) -> list[int]:
    return [index for index, (each, _) in enumerate(instructions) if each == keyword]


def _path_settings(dockerfile: str, program: str) -> dict[str, str]:
    """The last value `program` (chmod or chown) gives each path: its mode or its owner."""
    settings: dict[str, str] = {}
    for command in _commands(dockerfile):
        if command[:1] == [program] and len(command) > 2:
            for path in command[2:]:
                settings[path] = command[1]
    return settings


def _option(command: Command, name: str) -> str | None:
    return command[command.index(name) + 1] if name in command else None


def _accounts(dockerfile: str, program: str) -> dict[str, Command]:
    return {command[-1]: command for command in _commands(dockerfile) if command[:1] == [program]}


def test_the_shipped_dockerfile_has_no_floating_reference(dockerfile: str) -> None:
    assert floating_references(dockerfile) == []


@pytest.mark.parametrize(
    "line",
    [
        "FROM python:3.12-slim-bookworm",
        "FROM python",
        "FROM python:latest",
        "ARG CLAUDE_CODE_VERSION=latest",
        "ARG CLAUDE_CODE_VERSION=2.1",
        "apt-get install -y git",
        "apt-get install -y git=*",
        "apt-get upgrade -y",
        "pip install uv",
        "pip install uv>=0.9",
        "npm install --global @anthropic-ai/claude-code",
        "npm install --global @anthropic-ai/claude-code@latest",
        "npm install --global @anthropic-ai/claude-code@2.1",
        "npx claude-code",
        "RUN curl -fsSL https://example.invalid/install.sh | bash",
        "RUN wget -qO- https://example.invalid/install.sh | sh",
        "uv tool install /opt/factory",
        "uv sync",
        "apt-get dist-upgrade -y",
        "npm i -g @anthropic-ai/claude-code",
        "pip install .",
        "ARG CLAUDE_CODE_VERSION=stable",
        "ARG CLAUDE_CODE_VERSION=",
        "RUN echo latest",
        "FROM python@sha256:" + "a" * 63,
        "FROM python@sha256:" + "a" * 65,
        "FROM python@sha256:" + "g" * 64,
        "ARG CLAUDE_CODE_VERSION=2.1.289.1",
        "npm install --global @anthropic-ai/claude-code@2.1.289.1",
    ],
)
def test_a_floating_item_is_reported(line: str) -> None:
    assert floating_references(line + "\n") != []


@pytest.mark.parametrize(
    "line",
    [
        "FROM python:3.12-slim-bookworm@sha256:" + "a" * 64,
        "ARG CLAUDE_CODE_VERSION=2.1.289",
        "apt-get install -y git=1:2.39.5-0+deb12u2",
        "pip install uv==0.9.2",
        "npm install --global @anthropic-ai/claude-code@2.1.289",
        "uv sync --frozen --no-dev",
        "uv sync --locked --no-dev",
        "RUN curl -fsSL https://example.invalid/file -o /opt/file",
        "# latest",
    ],
)
def test_a_pinned_item_is_not_reported(line: str) -> None:
    assert floating_references(line + "\n") == []


def test_every_base_image_is_pinned_by_digest(instructions: list[Instruction]) -> None:
    references = _from_references(instructions)

    assert references != []
    assert all(DIGEST.search(reference) for reference in references)


def test_claude_code_is_installed_from_npm_at_the_pinned_version(
    dockerfile: str, instructions: list[Instruction]
) -> None:
    defaults = _arg_defaults(instructions, before_from=False)
    installs = [
        command
        for command in _commands(dockerfile)
        if command[:2] == ["npm", "install"]
        and "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" in command
    ]

    assert THREE_NUMBERS.match(defaults["CLAUDE_CODE_VERSION"])
    assert len(installs) == 1


def test_claude_code_does_not_update_itself(instructions: list[Instruction]) -> None:
    assert _env(instructions)["DISABLE_AUTOUPDATER"] == "1"


def test_every_debian_package_is_pinned_and_the_set_is_the_tools(dockerfile: str) -> None:
    packages = _apt_packages(_commands(dockerfile))

    assert all(re.match(r"^[^=\s]+=\S+$", package) for package in packages)
    assert sorted(package.partition("=")[0] for package in packages) == sorted(APT_PACKAGES)


def test_every_pip_requirement_is_pinned(dockerfile: str) -> None:
    requirements = [
        requirement
        for command in _commands(dockerfile)
        if (found := _after(command, "pip", {"install"})) is not None
        for requirement in found[1]
    ]

    assert requirements != []
    assert all(re.match(r"^[^=\s]+==\S+$", requirement) for requirement in requirements)


def test_the_factory_is_installed_from_the_lockfile_after_it_is_copied(
    instructions: list[Instruction],
) -> None:
    syncs = [
        index
        for index, (keyword, arguments) in enumerate(instructions)
        if keyword == "RUN" and "uv sync --frozen --no-dev" in arguments
    ]
    copies = [
        index
        for index, (keyword, arguments) in enumerate(instructions)
        if keyword == "COPY" and {"pyproject.toml", "uv.lock"} <= set(arguments.split())
    ]

    assert len(syncs) == 1
    assert copies != []
    assert copies[0] < syncs[0]


def _pins() -> dict[str, str]:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    pins = [requirement.partition("==") for requirement in project["dependencies"]]
    return {name: version for name, _, version in pins}


def _locked() -> dict[str, str]:
    lock = tomllib.loads(LOCKFILE.read_text(encoding="utf-8"))
    return {package["name"]: package["version"] for package in lock["package"]}


@pytest.mark.parametrize("name", PRODUCTION_DEPENDENCIES)
def test_installed_versions_equal_the_locked_and_pinned_ones(name: str) -> None:
    locked = _locked()[re.sub(r"[-_.]+", "-", name).lower()]

    assert importlib.metadata.version(name) == locked
    assert _pins()[name] == locked


def test_the_image_build_argument_is_only_a_label(instructions: list[Instruction]) -> None:
    defaults = _arg_defaults(instructions, before_from=False)
    users = [
        keyword
        for keyword, arguments in instructions
        if "FACTORY_IMAGE" in arguments and keyword != "ARG"
    ]

    assert defaults.get("FACTORY_IMAGE", "") != ""
    assert users == ["LABEL"]
    assert all("FACTORY_IMAGE" not in value for value in _env(instructions).values())


def test_the_image_identity_is_generated_after_the_last_copy_and_before_the_user(
    instructions: list[Instruction],
) -> None:
    writes = [
        index
        for index, (keyword, arguments) in enumerate(instructions)
        if keyword == "RUN" and arguments == IMAGE_ID_COMMAND
    ]

    assert len(writes) == 1
    assert _indices(instructions, "COPY")[-1] < writes[0] < _indices(instructions, "USER")[0]


def test_the_pinned_claude_code_version_is_readable_at_run_time(
    instructions: list[Instruction],
) -> None:
    assert _env(instructions)["FACTORY_CLAUDE_VERSION"] == "${CLAUDE_CODE_VERSION}"


def test_the_container_runs_as_the_factory_user_and_both_users_share_the_work_group(
    dockerfile: str, instructions: list[Instruction]
) -> None:
    users = _accounts(dockerfile, "useradd")
    last_build_step = max(_indices(instructions, "RUN") + _indices(instructions, "COPY"))

    assert _option(users["factory"], "--uid") == "1000"
    assert _option(users["agent"], "--uid") == "1001"
    assert _option(users["factory"], "--gid") == "factory-work"
    assert _option(users["agent"], "--gid") == "factory-work"
    assert [arguments for keyword, arguments in instructions if keyword == "USER"] == ["factory"]
    assert _indices(instructions, "USER")[0] > last_build_step


def test_the_state_directory_is_the_factory_users_alone(dockerfile: str) -> None:
    groups = _accounts(dockerfile, "groupadd")
    users = _accounts(dockerfile, "useradd").values()

    assert _path_settings(dockerfile, "chmod")["/state"] == "0755"
    assert _path_settings(dockerfile, "chown")["/state"] == "factory:factory"
    assert _option(groups["factory"], "--gid") == "1000"
    assert all(_option(user, "--gid") != "factory" for user in users)
    assert all("--groups" not in user and "-G" not in user for user in users)


def test_the_runs_directory_is_readable_but_not_writable_by_the_work_group(
    dockerfile: str,
) -> None:
    created = [
        path for command in _commands(dockerfile) if command[:1] == ["mkdir"] for path in command
    ]

    assert "/state/runs" in created
    assert _path_settings(dockerfile, "chmod")["/state/runs"] == "2750"
    assert _path_settings(dockerfile, "chown")["/state/runs"] == "factory:factory-work"


@pytest.mark.parametrize("path", ["/work"])
def test_the_shared_directories_are_writable_by_the_work_group(dockerfile: str, path: str) -> None:
    assert _path_settings(dockerfile, "chmod")[path] == "2775"
    assert _path_settings(dockerfile, "chown")[path].partition(":")[2] == "factory-work"


def test_the_template_has_no_placeholder_files_and_no_tasks_directory() -> None:
    found = list(TEMPLATE.rglob(".gitkeep")) + [
        path for path in TEMPLATE.rglob("tasks") if path.is_dir()
    ]

    assert found == []


def test_the_build_backend_is_pinned() -> None:
    requires = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["build-system"]["requires"]

    assert requires != []
    assert all(re.match(r"^[A-Za-z0-9._-]+==\S+$", requirement) for requirement in requires)
