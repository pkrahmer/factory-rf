"""The stage image: the tools alone, pinned."""

import re
from collections.abc import Callable
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

import pytest

from support.dockerfile_support import (
    DIGEST,
    SECRET_WORDS,
    STAGE_DOCKERFILE,
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
    _instruction_commands,
    _instructions,
    _piped_download_findings,
    _pipelines,
    _shell_lines,
    _substitute,
    _uncommented,
    floating_references,
)

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
RUNTIMES = {"claude": CLAUDE_CODE, "opencode": OPENCODE}
RUNTIME_REFERENCE = re.compile(r"\$\{AGENT_RUNTIME\}|\$AGENT_RUNTIME\b")
RUNTIME_NAMES = ("claude", "opencode", "anthropic")
LEFT_FROM_THE_INSTALL = ("/opt/factory/node", "/root/.npm")
# Built from its parts: the path is the one the final stage empties, not a file a test writes.
TEMPORARY = str(PurePosixPath("/", "tmp"))
AGENT_FILES_COPY = "agents /etc/factory/agents"
AGENT_FILES_MODES = (
    "chmod 0755 /etc/factory/agents /etc/factory/agents/agents"
    " && find /etc/factory/agents -type f -exec chmod 0644 {} +"
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


def _final_from(instructions: list[Instruction]) -> int:
    return max(index for index, (keyword, _) in enumerate(instructions) if keyword == "FROM")


def _final_stage(instructions: list[Instruction]) -> list[Instruction]:
    """The instructions after the final stage's FROM."""
    return instructions[_final_from(instructions) + 1 :]


def _final_stage_text(dockerfile: str) -> str:
    """The text of `dockerfile` after its final FROM line."""
    lines = dockerfile.splitlines()
    final = max(index for index, line in enumerate(lines) if re.match(r"FROM\s", line.strip()))
    return "\n".join(lines[final + 1 :])


def _in_final_stage(change: Callable[[str], str]) -> Callable[[str], str]:
    """A change applied to the text after the final FROM line alone."""

    def changed(text: str) -> str:
        tail = _final_stage_text(text)
        return text[: len(text) - len(tail)] + change(tail)

    return changed


def _is_npm(command: Command) -> bool:
    return Path(command[0]).name in {"npm", "npx"}


def _npm_packages(command: Command) -> list[str] | None:
    """The packages an `npm install` names, None for any other command."""
    if Path(command[0]).name != "npm" or "install" not in command:
        return None
    rest = command[command.index("install") + 1 :]
    return [
        word
        for index, word in enumerate(rest)
        if not word.startswith("-") and (index == 0 or rest[index - 1] != "--prefix")
    ]


def _for_runtime(dockerfile: str, requirement: str) -> str:
    """The instructions of `dockerfile` with every `npm install` naming `requirement` alone."""
    lines: list[str] = []
    for keyword, arguments in _instructions(dockerfile):
        commands = _run_commands(arguments) if keyword == "RUN" else []
        installs = [command for command in commands if _npm_packages(command) is not None]
        if installs:
            install = installs[0]
            packages = _npm_packages(install) or []
            words = [word for word in install if word not in packages]
            lines.append(f"{keyword} {' '.join([*words, requirement])}")
        else:
            lines.append(f"{keyword} {arguments}")
    return "\n".join(lines)


def _with_runtime(dockerfile: str, name: str) -> str:
    return RUNTIME_REFERENCE.sub(name, dockerfile)


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
    texts = [
        _for_runtime(change(stage_dockerfile), requirement).replace(FACTORY_NPM, "npm")
        for requirement in RUNTIMES.values()
    ]
    # The final stage declares the version again, without a default, for its settings.
    each_findings = [
        [
            finding
            for finding in floating_references(
                text.replace(f"--prefix {FACTORY_PREFIX}", "--prefix=_")
            )
            if finding != "ARG CLAUDE_CODE_VERSION"
        ]
        for text in texts
    ]
    others = [
        finding
        for findings in each_findings
        for finding in findings
        if finding not in RELEASE_PACKAGES
    ]

    assert (others == []) == pinned
    if pinned:
        assert all(sorted(set(findings)) == RELEASE_PACKAGES for findings in each_findings)


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

    assert stage_instructions[_final_from(stage_instructions)] == ("FROM", "${BASE_IMAGE}")
    assert len(base_argument) == 1
    assert base_argument[0] < keywords.index("FROM")
    assert len(references) == 2
    assert all(DIGEST.search(reference) for reference in references)


def _kind(instruction: Instruction) -> str:
    keyword, arguments = instruction
    return "COPY --from" if keyword == "COPY" and "--from=" in arguments else keyword


@pytest.mark.parametrize(("keyword", "count"), [("FROM", 2), ("LABEL", 1), ("COPY", 1)])
def test_the_stage_image_has_its_count_of_each_instruction(
    stage_instructions: list[Instruction], keyword: str, count: int
) -> None:
    assert [_kind(each) for each in stage_instructions].count(keyword) == count


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
        for each in _apt_packages(_commands(_final_stage_text(stage_dockerfile)))
        if each.partition("=")[0] == package
    ]

    assert stage == [package]


def test_the_one_apt_install_is_the_tools_without_recommends(
    stage_dockerfile: str, stage_instructions: list[Instruction]
) -> None:
    runs = [
        arguments
        for keyword, arguments in _final_stage(stage_instructions)
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
        each.partition("=")[0]
        for each in _apt_packages(_commands(_final_stage_text(stage_dockerfile)))
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
    text = _for_runtime(stage_dockerfile, requirement)
    installs = [command for command in _installs(text, program) if requirement in command]

    assert len(installs) == 1
    assert set(flags) <= set(installs[0])
    if program == FACTORY_NPM:
        assert installs[0][installs[0].index("--prefix") + 1] == FACTORY_PREFIX
    if program == "pip":
        assert len(_installs(stage_dockerfile, "pip")) == 1
        assert [word for word in installs[0][2:] if not word.startswith("-")] == [requirement]


def _installed_by_the_factory_npm(dockerfile: str, requirement: str) -> bool:
    installs = [command for command in _installs(dockerfile, FACTORY_NPM) if requirement in command]
    return len(installs) == 1 and installs[0][installs[0].index("--prefix") + 1] == FACTORY_PREFIX


@pytest.mark.parametrize("requirement", [CLAUDE_CODE, OPENCODE], ids=["claude-code", "opencode"])
@pytest.mark.parametrize(
    ("change", "installed"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        pytest.param(lambda text: text.replace(FACTORY_NPM, "npm"), False, id="bare-npm"),
        pytest.param(
            lambda text: text.replace(f"--prefix {FACTORY_PREFIX}", "--prefix /usr/local"),
            False,
            id="other-prefix",
        ),
    ],
)
def test_the_runtimes_are_installed_by_the_factory_npm_into_its_prefix(
    stage_dockerfile: str, requirement: str, change: Callable[[str], str], installed: bool
) -> None:
    text = _for_runtime(change(stage_dockerfile), requirement)

    assert _installed_by_the_factory_npm(text, requirement) == installed


@pytest.mark.parametrize("words", [["npx"], ["uv", "sync"], ["uv", "tool", "install"]])
def test_no_other_install_is_made(stage_dockerfile: str, words: list[str]) -> None:
    found = [command for command in _commands(stage_dockerfile) if command[: len(words)] == words]

    assert found == []


def test_the_agent_files_are_copied_read_only_to_their_place(
    stage_dockerfile: str, stage_instructions: list[Instruction]
) -> None:
    copies = [index for index, each in enumerate(stage_instructions) if _kind(each) == "COPY"]
    lines = stage_dockerfile.splitlines()
    copy_lines = [
        index
        for index, line in enumerate(lines)
        if line.strip().startswith("COPY ") and "--from=" not in line
    ]

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


@pytest.mark.parametrize(
    ("change", "named"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        pytest.param(
            lambda text: text.replace(" --build-arg AGENT_RUNTIME=<claude|opencode>", "", 1),
            False,
            id="without-the-runtime",
        ),
    ],
)
def test_the_first_line_names_the_build_command_with_the_runtime(
    stage_dockerfile: str, change: Callable[[str], str], named: bool
) -> None:
    first = change(stage_dockerfile).splitlines()[0]

    assert first.startswith("#")
    assert "podman build -f operator/vm/Dockerfile" in first
    assert ("--build-arg AGENT_RUNTIME=<claude|opencode>" in first) == named


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


def _drop_lines_with(marker: str) -> Callable[[str], str]:
    """A change that drops the joined lines that hold `marker`."""

    def change(text: str) -> str:
        lines = re.sub(r"\\\n", " ", text).splitlines()
        return "\n".join(line for line in lines if marker not in line)

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
        pytest.param(
            _replace_on_lines_with("sha256sum -c", "${NODE_SHA256}", "a" * 64),
            False,
            id="literal-checksum",
        ),
    ],
)
def test_the_node_archive_is_checked_before_it_is_unpacked(
    stage_dockerfile: str, change: Callable[[str], str], checked: bool
) -> None:
    assert _node_archive_is_checked(change(stage_dockerfile)) == checked


def _add_apt_package(package: str) -> Callable[[str], str]:
    """A change that adds `package` to the first apt install."""

    def change(text: str) -> str:
        return text.replace("--no-install-recommends ", f"--no-install-recommends {package} ", 1)

    return change


@pytest.mark.parametrize(
    ("change", "exact"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        *[
            pytest.param(
                _in_final_stage(_add_apt_package(package)),
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
    packages = _apt_packages(_commands(_final_stage_text(change(stage_dockerfile))))

    assert (sorted(packages) == sorted(STAGE_PACKAGES)) == exact


def _execs_its_installed_command(dockerfile: str, name: str) -> bool:
    wrapper = re.compile(rf'exec {re.escape(FACTORY_PREFIX)}/bin/{name} "\$@"')
    runs = [
        arguments
        for keyword, arguments in _instructions(dockerfile)
        if keyword == "RUN" and f"/usr/local/bin/{name}" in arguments
    ]
    return bool(runs) and all(
        wrapper.search(each) and FACTORY_NODE not in each and not re.search(r"\bnode ", each)
        for each in runs
    )


@pytest.mark.parametrize("name", ["claude", "opencode"])
@pytest.mark.parametrize(
    ("change", "execs"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        pytest.param(lambda text: text.replace('"$@"', ""), False, id="no-arguments"),
        pytest.param(_drop_lines_with("> /usr/local/bin/"), False, id="no-command"),
        pytest.param(
            lambda text: text.replace(
                f"exec {FACTORY_PREFIX}/bin/", f"exec {FACTORY_NODE} {FACTORY_PREFIX}/bin/"
            ),
            False,
            id="factory-node",
        ),
        pytest.param(
            lambda text: text.replace(
                f"exec {FACTORY_PREFIX}/bin/", f"exec node {FACTORY_PREFIX}/bin/"
            ),
            False,
            id="bare-node",
        ),
    ],
)
def test_each_runtime_command_execs_its_installed_command(
    stage_dockerfile: str, name: str, change: Callable[[str], str], execs: bool
) -> None:
    text = _with_runtime(change(stage_dockerfile), name)

    assert _execs_its_installed_command(text, name) == execs


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


@pytest.mark.parametrize(
    ("change", "without_default"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        pytest.param(
            lambda text: re.sub(r"(?m)^ARG AGENT_RUNTIME$", "ARG AGENT_RUNTIME=claude", text),
            False,
            id="claude-default",
        ),
        pytest.param(
            lambda text: re.sub(r"(?m)^ARG AGENT_RUNTIME$", "ARG AGENT_RUNTIME=", text),
            False,
            id="empty-default",
        ),
    ],
)
def test_the_runtime_build_argument_has_no_default(
    stage_dockerfile: str, change: Callable[[str], str], without_default: bool
) -> None:
    declared = [
        arguments
        for keyword, arguments in _instructions(change(stage_dockerfile))
        if keyword == "ARG" and arguments.partition("=")[0] == "AGENT_RUNTIME"
    ]

    assert (declared != [] and all(each == "AGENT_RUNTIME" for each in declared)) == (
        without_default
    )


def _installs_one_runtime_by_its_name(instructions: list[Instruction]) -> bool:
    final = _final_from(instructions)
    late_npm = [
        command for command in _instruction_commands(instructions[final:]) if _is_npm(command)
    ]
    holders = [
        (arguments, packages)
        for keyword, arguments in instructions
        if keyword == "RUN"
        for command in _run_commands(arguments)
        if (packages := _npm_packages(command)) is not None
    ]
    if late_npm or len(holders) != 1 or len(holders[0][1]) != 1:
        return False
    arguments, packages = holders[0]
    package = _substitute(packages[0], _arg_defaults(instructions, before_from=False))
    return bool(
        "$" in package
        and RUNTIME_REFERENCE.search(arguments)
        and all(requirement in arguments for requirement in RUNTIMES.values())
    )


def _install_index(instructions: list[Instruction]) -> int:
    return next(
        index
        for index, (keyword, arguments) in enumerate(instructions)
        if keyword == "RUN"
        and any(_npm_packages(command) is not None for command in _run_commands(arguments))
    )


def _second_install(instructions: list[Instruction]) -> list[Instruction]:
    index = _install_index(instructions)
    return [*instructions[: index + 1], instructions[index], *instructions[index + 1 :]]


def _independent_install(instructions: list[Instruction]) -> list[Instruction]:
    index = _install_index(instructions)
    keyword, arguments = instructions[index]
    literal = re.sub(r"(npm install[^&|;]*\s)(\S+)", lambda m: m[1] + CLAUDE_CODE, arguments)
    return [*instructions[:index], (keyword, literal), *instructions[index + 1 :]]


@pytest.mark.parametrize(
    ("change", "one_by_name"),
    [
        pytest.param(lambda each: each, True, id="as-built"),
        pytest.param(
            lambda each: [*each, ("RUN", f"{FACTORY_NPM} --version")], False, id="npm-in-final"
        ),
        pytest.param(_second_install, False, id="two-installs"),
        pytest.param(_independent_install, False, id="package-without-the-runtime"),
    ],
)
def test_the_first_stage_installs_the_one_runtime_its_name_chooses(
    stage_instructions: list[Instruction],
    change: Callable[[list[Instruction]], list[Instruction]],
    one_by_name: bool,
) -> None:
    assert _installs_one_runtime_by_its_name(change(stage_instructions)) == one_by_name


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("CLAUDE_CODE_VERSION", "2.1.318"),
        ("OPENCODE_VERSION", "1.19.5"),
        ("NODE_VERSION", "22.23.4"),
        # The checksum as its number: its hex digits read as a secret to make secrets.
        (
            "NODE_SHA256",
            "10865645828126401455792825685472766161388442199184181265352319439912524310990",
        ),
    ],
)
def test_each_install_pin_has_its_value(
    stage_instructions: list[Instruction], name: str, value: str
) -> None:
    pin = _arg_defaults(stage_instructions, before_from=False).get(name, "")
    if name == "NODE_SHA256":
        pin = str(int(pin, 16))

    assert pin == value


def _is_install(command: Command) -> bool:
    return bool(
        _after(command, "apt-get", {"install"})
        or _after(command, "pip", {"install"})
        or _npm_packages(command) is not None
        or Path(command[0]).name == "curl"
    )


def _checks_the_runtime_first(commands: list[Command]) -> bool:
    first = next(index for index, command in enumerate(commands) if _is_install(command))
    before = commands[:first]
    messages = [
        VARIABLE_FREE.sub("", " ".join(command[command.index(word) + 1 :]))
        for command in before
        for word in command
        if word in {"echo", "printf"}
    ]
    fails = any(
        command[index + 1 : index + 2] not in ([], ["0"])
        for command in before
        for index, word in enumerate(command)
        if word == "exit"
    )
    return bool(
        any(RUNTIME_REFERENCE.search(word) for command in before for word in command)
        and fails
        and any(all(word in message for word in RUNTIME_MESSAGE_WORDS) for message in messages)
    )


VARIABLE_FREE = re.compile(r"\$\{\w+\}|\$\w+")
RUNTIME_MESSAGE_WORDS = ("AGENT_RUNTIME", "claude", "opencode")


def _drop_the_message(commands: list[Command]) -> list[Command]:
    return [command for command in commands if not {"echo", "printf", "exit"} & set(command)]


def _without_word(word: str) -> Callable[[list[Command]], list[Command]]:
    def change(commands: list[Command]) -> list[Command]:
        return [
            [each.replace(word, "") for each in command]
            if {"echo", "printf"} & set(command)
            else command
            for command in commands
        ]

    return change


@pytest.mark.parametrize(
    ("change", "checked"),
    [
        pytest.param(lambda commands: commands, True, id="as-built"),
        pytest.param(_drop_the_message, False, id="no-check"),
        *[
            pytest.param(_without_word(word), False, id=f"message-without-{word}")
            for word in RUNTIME_MESSAGE_WORDS
        ],
    ],
)
def test_the_runtime_build_argument_is_checked_before_any_install(
    stage_dockerfile: str,
    change: Callable[[list[Command]], list[Command]],
    checked: bool,
) -> None:
    assert _checks_the_runtime_first(change(_commands(stage_dockerfile))) == checked


def _covers(pattern: str, path: str) -> bool:
    return fnmatch(path, pattern) or path.startswith(pattern.rstrip("/") + "/")


CLEANED = [f"{TEMPORARY}/a", "/var/lib/apt/lists/a", "/var/cache/debconf/a-old", "/var/log/a.log"]


def _final_stage_cleans_up(dockerfile: str) -> bool:
    commands = _instruction_commands(_final_stage(_instructions(dockerfile)))
    last_use = max(
        (
            index
            for index, command in enumerate(commands)
            if command[0] != "rm"
            and ("apt-get" in command or any(word.startswith(TEMPORARY) for word in command))
        ),
        default=-1,
    )
    removed = [
        word
        for command in commands[last_use + 1 :]
        if command[:1] == ["rm"]
        for word in command[1:]
        if not word.startswith("-")
    ]
    return all(any(_covers(word, path) for word in removed) for path in CLEANED)


def _drop_path(path: str) -> Callable[[str], str]:
    """A change that drops every word starting with `path`."""

    def change(text: str) -> str:
        return re.sub(rf"\s{path}[^\s\"']*", "", text)

    return change


@pytest.mark.parametrize(
    ("change", "clean"),
    [
        pytest.param(lambda text: text, True, id="as-built"),
        *[
            pytest.param(
                _in_final_stage(_drop_path(path)),
                False,
                id=path.strip("/").replace("/", "-"),
            )
            for path in [TEMPORARY, "/var/lib/apt/lists", "/var/cache/debconf", "/var/log"]
        ],
    ],
)
def test_the_final_stage_leaves_no_install_rest(
    stage_dockerfile: str, change: Callable[[str], str], clean: bool
) -> None:
    assert _final_stage_cleans_up(change(stage_dockerfile)) == clean


def _takes_from_the_install(source: str) -> bool:
    """Whether a source of the final stage's COPY --from takes more than the chosen runtime."""
    return bool(
        {"node", "npm", ".npm"} & set(PurePosixPath(source).parts)
        or any(_covers(source, left) or _covers(left, source) for left in LEFT_FROM_THE_INSTALL)
        or any(name in RUNTIME_REFERENCE.sub("", source) for name in RUNTIME_NAMES)
    )


def _takes_only_the_chosen_runtime(dockerfile: str) -> bool:
    copies = [
        [word for word in arguments.split() if not word.startswith("--")]
        for keyword, arguments in _final_stage(_instructions(dockerfile))
        if keyword == "COPY" and "--from=" in arguments
    ]
    return copies != [] and not any(
        any(_takes_from_the_install(source) for source in words[:-1])
        or any("baseline" in word for word in words)
        for words in copies
    )


def _first_stage_name(dockerfile: str) -> str:
    first = next(arguments for keyword, arguments in _instructions(dockerfile) if keyword == "FROM")
    words = first.split()
    return words[-1] if len(words) == 3 and words[1].upper() == "AS" else "0"


@pytest.mark.parametrize(
    ("source", "only_the_runtime"),
    [
        pytest.param(None, True, id="as-built"),
        pytest.param("/opt/factory/node", False, id="node"),
        pytest.param("/opt/factory/node/bin/node", False, id="node-executable"),
        pytest.param("/opt/factory/lib/node_modules/npm", False, id="npm"),
        pytest.param("/root/.npm", False, id="npm-cache"),
        pytest.param("/opt/factory", False, id="whole-prefix"),
        pytest.param("/opt/factory/lib/node_modules/opencode-ai", False, id="opencode-install"),
        pytest.param("/opt/factory/lib/node_modules/@anthropic-ai", False, id="claude-install"),
        pytest.param("/opt/runtime-baseline/bin/", False, id="baseline"),
    ],
)
def test_the_final_stage_takes_only_the_chosen_runtime_from_the_first_stage(
    stage_dockerfile: str, source: str | None, only_the_runtime: bool
) -> None:
    extra = (
        ""
        if source is None
        else (f"COPY --from={_first_stage_name(stage_dockerfile)} {source} /opt/factory/extra/")
    )

    assert _takes_only_the_chosen_runtime(f"{stage_dockerfile}\n{extra}\n") == only_the_runtime


@pytest.mark.parametrize(
    "name", ["FACTORY_CLAUDE_VERSION", "FACTORY_OPENCODE_VERSION", "FACTORY_OPENCODE_MODELS"]
)
@pytest.mark.parametrize("removed", [False, True], ids=["as-built", "removed"])
def test_the_version_settings_stay_in_the_image(
    stage_dockerfile: str, name: str, removed: bool
) -> None:
    text = _drop_lines_with(f"ENV {name}=")(stage_dockerfile) if removed else stage_dockerfile

    assert (name in _env(_final_stage(_instructions(text)))) != removed
