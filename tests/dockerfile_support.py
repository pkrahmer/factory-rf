"""Helpers for tests that read a Dockerfile: its instructions, its commands and its pins."""

import re
import shlex
from pathlib import Path

SECRET_WORDS = ("TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
THREE_NUMBERS = re.compile(r"^\d+\.\d+\.\d+$")
NPM_PINNED = re.compile(r"@\d+\.\d+\.\d+$")
APT_PINNED = re.compile(r"^[^=\s]+=(?!\*$)\S+$")
PIP_PINNED = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\[\],-]*==[^=<>*\s]+$")
SHELL_OPERATOR = re.compile(r"&&|\|\||;")
VARIABLE = re.compile(r"\$\{(\w+)\}|\$(\w+)")
LATEST = re.compile(r"\blatest\b")
DOCKER_KEYWORDS = {"FROM", "ARG", "ENV", "LABEL", "COPY", "USER", "WORKDIR", "ENTRYPOINT", "RUN"}
Instruction = tuple[str, str]
Command = list[str]


def _uncommented(dockerfile: str) -> str:
    """The text of `dockerfile` with its comment lines dropped."""
    return "\n".join(line for line in dockerfile.splitlines() if not line.strip().startswith("#"))


def _declared_names(instructions: list[str]) -> list[str]:
    """The names every `ENV` and `ARG` instruction declares."""
    names: list[str] = []
    for instruction in instructions:
        keyword, _, arguments = instruction.partition(" ")
        if keyword.upper() in {"ENV", "ARG"}:
            names.extend(word.partition("=")[0] for word in arguments.split() if "=" in word)
            if "=" not in arguments:
                names.append(arguments.split()[0])
    return names


def _after(command: list[str], program: str, subcommands: set[str]) -> tuple[str, list[str]] | None:
    """The subcommand that follows `program` in `command`, and the words after it."""
    if program not in command:
        return None
    rest = command[command.index(program) + 1 :]
    words = [word for word in rest if not word.startswith("-")]
    if not words or words[0] not in subcommands:
        return None
    return words[0], words[1:]


def _apt_packages(commands: list[list[str]]) -> list[str]:
    """The packages every `apt-get install` among `commands` names."""
    return [
        package
        for command in commands
        if (found := _after(command, "apt-get", {"install"})) is not None
        for package in found[1]
    ]


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


def _env(instructions: list[Instruction]) -> dict[str, str]:
    pairs = [
        pair.partition("=")
        for keyword, arguments in instructions
        if keyword == "ENV"
        for pair in arguments.split()
    ]
    return {name: value for name, _, value in pairs}
