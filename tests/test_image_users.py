"""The image's second user: the one `sudo` rule, its defaults, and the uids of both users."""

import re
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).parent.parent
DOCKERFILE = ROOT / "image" / "Dockerfile"
COMPOSE = ROOT / "image" / "compose.yml"
SUDOERS = ROOT / "image" / "sudoers-factory-agent"
ENTRYPOINT = ROOT / "image" / "entrypoint.sh"
SUDOERS_TARGET = "/etc/sudoers.d/factory-agent"
RULE = "factory ALL=(agent) NOPASSWD: ALL"


def _instructions() -> list[str]:
    """Every instruction of the Dockerfile on one line, continuations joined, comments dropped."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    joined = re.sub(r"\\\n", " ", "\n".join(lines))
    return [" ".join(line.split()) for line in joined.splitlines() if line.strip()]


def _sudoers_lines() -> list[str]:
    """The sudoers file's lines, blank and comment lines dropped."""
    text = SUDOERS.read_text(encoding="utf-8")
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _uid_of(user: str) -> int:
    """The uid the Dockerfile's `useradd` gives `user`."""
    uids = []
    for instruction in _instructions():
        for command in re.split(r"&&|\bRUN\b", instruction):
            words = command.split()
            if words[:1] == ["useradd"] and words[-1] == user and "--uid" in words:
                uids.append(int(words[words.index("--uid") + 1]))
    assert len(uids) == 1, f"one useradd with --uid for {user}, found {uids}"
    return uids[0]


def test_the_dockerfile_installs_the_validated_sudoers_file_and_the_agent_user() -> None:
    instructions = _instructions()
    user = instructions.index("USER factory")
    copy = instructions.index(f"COPY image/sudoers-factory-agent {SUDOERS_TARGET}")
    installing = [
        index
        for index, instruction in enumerate(instructions)
        if instruction.startswith("RUN ")
        and f"chmod 0440 {SUDOERS_TARGET}" in instruction
        and f"visudo -cf {SUDOERS_TARGET}" in instruction
    ]
    setting = instructions.index("ENV FACTORY_AGENT_USER=agent")

    assert copy < user
    assert len(installing) == 1
    assert copy < installing[0] < user
    assert setting < user


def test_the_sudoers_file_holds_exactly_the_three_defaults_and_the_rule_in_order() -> None:
    assert _sudoers_lines() == [
        "Defaults:factory umask=0002",
        "Defaults:factory umask_override",
        "Defaults:factory !use_pty",
        RULE,
    ]


def test_the_only_sudoers_rule_lets_the_factory_become_agent_and_nobody_else_more() -> None:
    lines = _sudoers_lines()

    assert [line for line in lines if not line.startswith("Defaults")] == [RULE]
    assert not [line for line in lines if "root" in line]
    assert not [line for line in lines if "ALL=(ALL" in line]
    assert not [line for line in lines if line.split()[0] == "agent"]
    assert not [line for line in lines if line.startswith("Defaults:agent")]


def test_the_sudoers_umask_equals_the_entrypoints_umask() -> None:
    sudoers = [
        match["value"]
        for line in _sudoers_lines()
        if (match := re.fullmatch(r"Defaults:factory umask=(?P<value>[0-7]+)", line))
    ]
    entrypoint = [
        match["value"]
        for line in ENTRYPOINT.read_text(encoding="utf-8").splitlines()
        if (match := re.fullmatch(r"umask (?P<value>[0-7]+)", line.strip()))
    ]

    assert len(sudoers) == 1
    assert len(entrypoint) == 1
    assert int(sudoers[0], 8) == int(entrypoint[0], 8) == 0o002


def test_the_token_secret_belongs_to_the_factory_user_and_not_to_the_agent() -> None:
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))
    secrets = loaded["services"]["factory"]["secrets"]
    token = [secret for secret in secrets if secret["target"] == "hosting-token"]
    factory_uid = _uid_of("factory")
    agent_uid = _uid_of("agent")

    assert len(token) == 1
    assert int(token[0]["uid"]) == factory_uid
    assert factory_uid != agent_uid
    assert agent_uid != 0
