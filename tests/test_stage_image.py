"""The stage image: the tools alone, pinned."""

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from dockerfile_support import (
    DIGEST,
    SECRET_WORDS,
    THREE_NUMBERS,
    Command,
    Instruction,
    _after,
    _apt_packages,
    _arg_defaults,
    _commands,
    _declared_names,
    _env,
    _from_references,
    _instructions,
    _piped_download_findings,
    _pipelines,
    _shell_lines,
    _uncommented,
    floating_references,
)

ROOT = Path(__file__).parent.parent
STAGE_DOCKERFILE = ROOT / "vm" / "Dockerfile"
STAGE_PACKAGES = ["git", "make", "curl", "ca-certificates", "procps", "xz-utils"]
FACTORY_PREFIX = "/opt/factory"
FACTORY_NODE_DIRECTORY = "/opt/factory/node"
FACTORY_NODE = "/opt/factory/node/bin/node"
FACTORY_NPM = "/opt/factory/node/bin/npm"
NPM_FLAGS = ["--prefix", "--no-audit", "--no-fund"]
NODE_VERSION = re.compile(r"22\.\d+\.\d+")
LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
CLAUDE_CODE = "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}"
OPENCODE = "opencode-ai@${OPENCODE_VERSION}"
AGENT_FILES_COPY = "claude /etc/factory/claude"
AGENT_FILES_MODES = (
    "chmod 0755 /etc/factory/claude /etc/factory/claude/agents"
    " && find /etc/factory/claude -type f -exec chmod 0644 {} +"
)
ENV_NAMES = [
    "UV_LINK_MODE",
    "PYTHONDONTWRITEBYTECODE",
    "DISABLE_AUTOUPDATER",
    "FACTORY_CLAUDE_VERSION",
    "FACTORY_OPENCODE_VERSION",
    "FACTORY_OPENCODE_MODELS",
]
ONE_SETTING = re.compile(r"ENV \w+=\S*[^\s\\]")
ABSENT_WORDS = [
    "useradd",
    "groupadd",
    "sudo",
    "sudoers",
    "visudo",
    "USER",
    "WORKDIR",
    "ENTRYPOINT",
    "CMD",
    "gitconfig",
    "src",
    "pyproject.toml",
    "uv.lock",
    "image-id",
    "entrypoint",
    "/home/agent",
    "/home/factory",
    "FACTORY_AGENT_USER",
    "FACTORY_CLAUDE_HOME",
    "FACTORY_TOKEN_FILE",
    "FACTORY_CLAUDE_LOGIN_FILE",
    "FACTORY_API_LOGIN_FILE",
    "latest",
]


@pytest.fixture
def stage_dockerfile() -> str:
    return STAGE_DOCKERFILE.read_text(encoding="utf-8")


@pytest.fixture
def stage_instructions(stage_dockerfile: str) -> list[Instruction]:
    return _instructions(stage_dockerfile)


def _pins(instructions: list[Instruction]) -> dict[str, str]:
    """The ARG defaults, with the ENV values over them."""
    return _arg_defaults(instructions, before_from=False) | _env(instructions)


def _installs(dockerfile: str, program: str) -> list[Command]:
    return [command for command in _commands(dockerfile) if command[:2] == [program, "install"]]


def _run_commands(arguments: str) -> list[Command]:
    return [command for pipeline in _pipelines(arguments) for command in pipeline]


# The Debian packages follow the base image's release, which its digest fixes (docs/decisions.md).
RELEASE_PACKAGES = sorted(f"apt package {package}" for package in STAGE_PACKAGES)


@pytest.mark.parametrize(
    ("change", "pinned"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        pytest.param(
            lambda text: re.sub(r"@sha256:[0-9a-f]{64}", "", text), False, id="floating-base"
        ),
        pytest.param(
            lambda text: re.sub(r"CLAUDE_CODE_VERSION=\S+", "CLAUDE_CODE_VERSION=2.1", text),
            False,
            id="claude-code",
        ),
        pytest.param(
            lambda text: re.sub(r"OPENCODE_VERSION=\S+", "OPENCODE_VERSION=1.19", text),
            False,
            id="opencode",
        ),
        pytest.param(lambda text: text.replace("uv==${UV_VERSION}", "uv"), False, id="uv"),
        pytest.param(
            lambda text: text.replace(
                "--no-install-recommends ", "--no-install-recommends wget ", 1
            ),
            False,
            id="seventh-package",
        ),
    ],
)
def test_the_stage_image_has_no_floating_reference(
    stage_dockerfile: str, change: Callable[[str], str], pinned: bool
) -> None:
    # floating_references knows npm by its bare name and an option's value only after "=".
    text = change(stage_dockerfile).replace(FACTORY_NPM, "npm")
    findings = floating_references(text.replace(f"--prefix {FACTORY_PREFIX}", "--prefix=_"))
    others = [finding for finding in findings if finding not in RELEASE_PACKAGES]

    assert (others == []) == pinned
    if pinned:
        assert sorted(findings) == RELEASE_PACKAGES


def test_the_one_base_image_is_the_pinned_build_argument(
    stage_instructions: list[Instruction],
) -> None:
    keywords = [keyword for keyword, _ in stage_instructions]
    base_argument = [
        index
        for index, (keyword, arguments) in enumerate(stage_instructions)
        if keyword == "ARG" and arguments.startswith("BASE_IMAGE=")
    ]
    references = _from_references(stage_instructions)

    assert [arguments for keyword, arguments in stage_instructions if keyword == "FROM"] == [
        "${BASE_IMAGE}"
    ]
    assert len(base_argument) == 1
    assert base_argument[0] < keywords.index("FROM")
    assert len(references) == 1
    assert DIGEST.search(references[0])


@pytest.mark.parametrize("keyword", ["FROM", "LABEL", "COPY"])
def test_the_stage_image_has_one_instruction_of_each_kind(
    stage_instructions: list[Instruction], keyword: str
) -> None:
    assert [each for each, _ in stage_instructions].count(keyword) == 1


MODEL = re.compile(r"^[\w.-]+/[\w.-]+$")


def _is_digest(value: str) -> bool:
    return DIGEST.search(value) is not None


def _is_three_numbers(value: str) -> bool:
    return THREE_NUMBERS.match(value) is not None


def _maps_the_three_models(value: str) -> bool:
    pairs = [pair.partition("=") for pair in value.strip("\"'").split(",")]
    models = {name: model for name, _, model in pairs}
    return sorted(models) == ["haiku", "opus", "sonnet"] and all(
        MODEL.match(model) for model in models.values()
    )


@pytest.mark.parametrize(
    ("name", "has_its_form"),
    [
        ("BASE_IMAGE", _is_digest),
        ("CLAUDE_CODE_VERSION", _is_three_numbers),
        ("OPENCODE_VERSION", _is_three_numbers),
        ("UV_VERSION", _is_three_numbers),
        ("FACTORY_OPENCODE_MODELS", _maps_the_three_models),
    ],
)
def test_each_pin_of_the_stage_image_has_its_form(
    stage_instructions: list[Instruction], name: str, has_its_form: Callable[[str], bool]
) -> None:
    assert has_its_form(_pins(stage_instructions)[name])


@pytest.mark.parametrize("package", STAGE_PACKAGES)
def test_each_debian_package_is_installed_by_name_alone(
    stage_dockerfile: str, package: str
) -> None:
    stage = [
        each
        for each in _apt_packages(_commands(stage_dockerfile))
        if each.partition("=")[0] == package
    ]

    assert stage == [package]


def test_the_one_apt_install_is_the_tools_without_recommends(
    stage_dockerfile: str, stage_instructions: list[Instruction]
) -> None:
    runs = [
        arguments
        for keyword, arguments in stage_instructions
        if keyword == "RUN"
        and any(_after(command, "apt-get", {"install"}) for command in _run_commands(arguments))
    ]
    commands = _run_commands(runs[0]) if len(runs) == 1 else []
    install = [command for command in commands if _after(command, "apt-get", {"install"})]
    removals = [
        path
        for command in commands
        if command[:1] == ["rm"]
        for path in command[1:]
        if path.startswith("/var/lib/apt/lists")
    ]

    assert len(runs) == 1
    assert len(install) == 1
    assert sorted(
        each.partition("=")[0] for each in _apt_packages(_commands(stage_dockerfile))
    ) == sorted(STAGE_PACKAGES)
    assert "--no-install-recommends" in install[0]
    assert removals != []


@pytest.mark.parametrize(
    ("program", "requirement", "flags"),
    [
        pytest.param("pip", "uv==${UV_VERSION}", ["--no-cache-dir"], id="uv"),
        pytest.param(FACTORY_NPM, CLAUDE_CODE, NPM_FLAGS, id="claude-code"),
        pytest.param(FACTORY_NPM, OPENCODE, NPM_FLAGS, id="opencode"),
    ],
)
def test_each_tool_is_installed_once_at_its_pinned_version(
    stage_dockerfile: str, program: str, requirement: str, flags: list[str]
) -> None:
    installs = [
        command for command in _installs(stage_dockerfile, program) if requirement in command
    ]

    assert len(installs) == 1
    assert set(flags) <= set(installs[0])
    if program == FACTORY_NPM:
        assert installs[0][installs[0].index("--prefix") + 1] == FACTORY_PREFIX
    if program == "pip":
        assert len(_installs(stage_dockerfile, "pip")) == 1
        assert [word for word in installs[0][2:] if not word.startswith("-")] == [requirement]


def test_opencode_is_installed_after_claude_code(stage_dockerfile: str) -> None:
    installs = _installs(stage_dockerfile, FACTORY_NPM)
    claude = [index for index, command in enumerate(installs) if CLAUDE_CODE in command]
    opencode = [index for index, command in enumerate(installs) if OPENCODE in command]

    assert len(claude) == len(opencode) == 1
    assert claude[0] < opencode[0]


@pytest.mark.parametrize("words", [["npx"], ["uv", "sync"], ["uv", "tool", "install"]])
def test_no_other_install_is_made(stage_dockerfile: str, words: list[str]) -> None:
    found = [command for command in _commands(stage_dockerfile) if command[: len(words)] == words]

    assert found == []


def test_the_agent_files_are_copied_read_only_to_their_place(
    stage_dockerfile: str, stage_instructions: list[Instruction]
) -> None:
    copies = [index for index, (keyword, _) in enumerate(stage_instructions) if keyword == "COPY"]
    lines = stage_dockerfile.splitlines()
    copy_lines = [index for index, line in enumerate(lines) if line.strip().startswith("COPY ")]

    assert [stage_instructions[index][1] for index in copies] == [AGENT_FILES_COPY]
    assert stage_instructions[copies[0] + 1] == ("RUN", AGENT_FILES_MODES)
    assert len(copy_lines) == 1
    assert copy_lines[0] > 0
    assert lines[copy_lines[0] - 1].strip().startswith("#")
    assert "chown" not in stage_dockerfile


def test_the_environment_names_are_the_runtimes_alone(
    stage_instructions: list[Instruction],
) -> None:
    assert sorted(_env(stage_instructions)) == sorted(ENV_NAMES)


@pytest.mark.parametrize(
    ("extra", "one_name_each"),
    [
        pytest.param("", True, id="as-built"),
        pytest.param("ENV FIRST=1 SECOND=2", False, id="two-names-on-a-line"),
        pytest.param("ENV FIRST=1 \\\n    SECOND=2", False, id="continued-line"),
        pytest.param("ENV FIRST=1\\", False, id="trailing-backslash"),
        pytest.param("ENV FIRST", False, id="no-value"),
    ],
)
def test_each_setting_is_one_name_on_a_line_of_its_own(
    stage_dockerfile: str, extra: str, one_name_each: bool
) -> None:
    text = f"{stage_dockerfile}\n{extra}\n"
    lines = [line for line in text.splitlines() if line.startswith("ENV ")]
    names = _env(_instructions(text))
    one_pair_per_line = all(ONE_SETTING.fullmatch(line) for line in lines)

    assert (one_pair_per_line and len(lines) == len(names)) == one_name_each
    assert not one_name_each or len(lines) == len(ENV_NAMES)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("UV_LINK_MODE", "copy"),
        ("PYTHONDONTWRITEBYTECODE", "1"),
        ("DISABLE_AUTOUPDATER", "1"),
        ("FACTORY_CLAUDE_VERSION", "${CLAUDE_CODE_VERSION}"),
        ("FACTORY_OPENCODE_VERSION", "${OPENCODE_VERSION}"),
    ],
)
def test_each_runtime_setting_has_its_value(
    stage_instructions: list[Instruction], name: str, value: str
) -> None:
    assert _env(stage_instructions).get(name) == value


@pytest.mark.parametrize("word", SECRET_WORDS)
def test_no_setting_or_build_argument_names_a_secret(
    stage_instructions: list[Instruction], word: str
) -> None:
    names = _declared_names([f"{keyword} {arguments}" for keyword, arguments in stage_instructions])

    assert [name for name in names if word in name] == []


def test_the_image_build_argument_is_only_the_label(
    stage_instructions: list[Instruction],
) -> None:
    users = [
        keyword
        for keyword, arguments in stage_instructions
        if re.search(r"\bFACTORY_IMAGE\b", arguments)
    ]

    assert _arg_defaults(stage_instructions, before_from=False).get("FACTORY_IMAGE") == (
        "unlabelled"
    )
    assert ("LABEL", 'factory.image="${FACTORY_IMAGE}"') in stage_instructions
    assert sorted(users) == ["ARG", "LABEL"]


@pytest.mark.parametrize("word", ABSENT_WORDS)
def test_nothing_of_the_long_lived_container_is_left(stage_dockerfile: str, word: str) -> None:
    assert word not in _uncommented(stage_dockerfile)


def test_the_first_line_names_the_build_command(stage_dockerfile: str) -> None:
    first = stage_dockerfile.splitlines()[0]

    assert first.startswith("#")
    assert "podman build -f vm/Dockerfile" in first


def _node_is_pinned(dockerfile: str) -> bool:
    pins = _arg_defaults(_instructions(dockerfile), before_from=False)
    return bool(
        NODE_VERSION.fullmatch(pins.get("NODE_VERSION", ""))
        and LOWER_SHA256.fullmatch(pins.get("NODE_SHA256", ""))
    )


@pytest.mark.parametrize(
    ("change", "pinned"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        pytest.param(
            lambda text: re.sub(r"NODE_VERSION=\S+", "NODE_VERSION=20.1.0", text),
            False,
            id="node-20",
        ),
        pytest.param(
            lambda text: re.sub(r"NODE_VERSION=\S+", "NODE_VERSION=22.1", text),
            False,
            id="two-numbers",
        ),
        pytest.param(lambda text: re.sub(r"(NODE_SHA256=)\S", r"\1", text), False, id="63-digits"),
        pytest.param(
            lambda text: re.sub(
                r"NODE_SHA256=(\S+)", lambda match: f"NODE_SHA256={match[1].upper()}", text
            ),
            False,
            id="upper-case",
        ),
    ],
)
def test_the_factory_node_is_pinned_by_version_and_checksum(
    stage_dockerfile: str, change: Callable[[str], str], pinned: bool
) -> None:
    assert _node_is_pinned(change(stage_dockerfile)) == pinned


def _replace_on_lines_with(marker: str, old: str, new: str) -> Callable[[str], str]:
    """A change that replaces `old` by `new` on the joined lines that hold `marker`."""

    def change(text: str) -> str:
        lines = re.sub(r"\\\n", " ", text).splitlines()
        return "\n".join(line.replace(old, new) if marker in line else line for line in lines)

    return change


def _node_archive_is_checked(dockerfile: str) -> bool:
    instructions = _instructions(dockerfile)
    commands = _commands(dockerfile)
    downloads = [command for command in commands if any("nodejs.org" in w for w in command)]
    checks = [
        index
        for index, command in enumerate(commands)
        if Path(command[0]).name == "sha256sum" and "-c" in command
    ]
    unpacks = [
        index
        for index, command in enumerate(commands)
        if Path(command[0]).name == "tar"
        and any(word.rstrip("/").endswith(FACTORY_NODE_DIRECTORY) for word in command[1:])
    ]
    checked_runs = [
        arguments
        for keyword, arguments in instructions
        if keyword == "RUN" and "sha256sum -c" in arguments
    ]
    piped = [
        finding
        for line in _shell_lines(instructions)
        for pipeline in _pipelines(line)
        for finding in _piped_download_findings(pipeline)
    ]
    return bool(
        downloads
        and all(Path(command[0]).name == "curl" for command in downloads)
        and checks
        and unpacks
        and max(checks) < min(unpacks)
        and all("NODE_SHA256" in arguments for arguments in checked_runs)
        and piped == []
    )


@pytest.mark.parametrize(
    ("change", "checked"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        pytest.param(lambda text: text.replace("sha256sum -c", "sha256sum"), False, id="no-check"),
        pytest.param(
            lambda text: (
                text.replace("sha256sum -c", "sha256sum")
                + '\nRUN echo "${NODE_SHA256}  /tmp/node.tar.xz" | sha256sum -c -\n'
            ),
            False,
            id="check-after-unpack",
        ),
        pytest.param(
            lambda text: f"{text}\nRUN curl -fsSL https://example.org/install.sh | sh\n",
            False,
            id="piped-into-a-shell",
        ),
        pytest.param(_replace_on_lines_with("nodejs.org", "curl", "wget"), False, id="not-curl"),
        pytest.param(
            _replace_on_lines_with("tar ", FACTORY_NODE_DIRECTORY, "/opt/node"),
            False,
            id="another-target",
        ),
    ],
)
def test_the_node_archive_is_checked_before_it_is_unpacked(
    stage_dockerfile: str, change: Callable[[str], str], checked: bool
) -> None:
    assert _node_archive_is_checked(change(stage_dockerfile)) == checked


@pytest.mark.parametrize(
    ("change", "exact"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        *[
            pytest.param(
                lambda text, package=package: text.replace(
                    "--no-install-recommends ", f"--no-install-recommends {package} ", 1
                ),
                False,
                id=package,
            )
            for package in ["nodejs", "npm"]
        ],
    ],
)
def test_the_apt_install_names_exactly_the_six_packages(
    stage_dockerfile: str, change: Callable[[str], str], exact: bool
) -> None:
    packages = _apt_packages(_commands(change(stage_dockerfile)))

    assert (sorted(packages) == sorted(STAGE_PACKAGES)) == exact


def _runs_on_the_factory_node(dockerfile: str, name: str) -> bool:
    runs = [
        arguments
        for keyword, arguments in _instructions(dockerfile)
        if keyword == "RUN" and f"/usr/local/bin/{name}" in arguments
    ]
    return bool(runs) and all(FACTORY_NODE in each and '"$@"' in each for each in runs)


@pytest.mark.parametrize("name", ["claude", "opencode"])
@pytest.mark.parametrize(
    ("change", "runs"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        pytest.param(lambda text: text.replace('"$@"', ""), False, id="no-arguments"),
    ],
)
def test_each_runtime_command_runs_on_the_factory_node(
    stage_dockerfile: str, name: str, change: Callable[[str], str], runs: bool
) -> None:
    assert _runs_on_the_factory_node(change(stage_dockerfile), name) == runs


def _keeps_the_factory_node_off_the_path(dockerfile: str) -> bool:
    instructions = _instructions(dockerfile)
    named = re.search(r"/usr/local/bin/(node|npm)\b", _uncommented(dockerfile))
    links = [
        command
        for command in _commands(dockerfile)
        if Path(command[0]).name in {"ln", "cp", "install"}
        and any(Path(word).name in {"node", "npm"} for word in command[1:])
        and any(word.rstrip("/") == "/usr/local/bin" for word in command[1:])
    ]
    paths = [
        arguments
        for keyword, arguments in instructions
        if keyword == "ENV" and "PATH" in arguments and FACTORY_PREFIX in arguments
    ]
    return named is None and links == [] and paths == []


@pytest.mark.parametrize(
    ("extra", "off_the_path"),
    [
        pytest.param("", True, id="as-built"),
        pytest.param(f"RUN ln -s {FACTORY_NODE} /usr/local/bin/node", False, id="node-link"),
        pytest.param(f"RUN ln -s {FACTORY_NPM} /usr/local/bin/", False, id="npm-link"),
        pytest.param(
            f"RUN printf '#!/bin/sh\\nexec {FACTORY_NPM} \"$@\"\\n' > /usr/local/bin/npm",
            False,
            id="npm-created",
        ),
        pytest.param("ENV PATH=/opt/factory/node/bin:${PATH}", False, id="env-path"),
    ],
)
def test_the_factory_node_stays_off_the_path(
    stage_dockerfile: str, extra: str, off_the_path: bool
) -> None:
    assert _keeps_the_factory_node_off_the_path(f"{stage_dockerfile}\n{extra}\n") == off_the_path
