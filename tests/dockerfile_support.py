"""Helpers for tests that read the image's Dockerfiles."""

import re
from pathlib import Path

DOCKERFILE = Path(__file__).parent.parent / "image" / "Dockerfile"
SECRET_WORDS = ("TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


def _uncommented(dockerfile: str) -> str:
    """The text of `dockerfile` with its comment lines dropped."""
    return "\n".join(line for line in dockerfile.splitlines() if not line.strip().startswith("#"))


def dockerfile_instructions() -> list[str]:
    """Every instruction of the Dockerfile on one line, continuations joined, comments dropped."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    joined = re.sub(r"\\\n", " ", _uncommented(text))
    return [" ".join(line.split()) for line in joined.splitlines() if line.strip()]


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
