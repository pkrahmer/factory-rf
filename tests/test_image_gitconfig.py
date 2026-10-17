"""The image's git system configuration: the agent's git trusts the checkout the factory owns."""

from pathlib import Path

from dockerfile_support import DOCKERFILE, dockerfile_instructions
from factory.domain.settings import CHECKOUT_PATH
from git_support import run_git
from test_image import _path_settings

ROOT = Path(__file__).parent.parent
GITCONFIG = (ROOT / "image" / "gitconfig").absolute()
COPY = "COPY image/gitconfig /etc/gitconfig"
INSTALL = "RUN sed -i 's/\\r$//' /etc/gitconfig && chmod 0644 /etc/gitconfig"
CREDENTIAL_HELPER_CHMOD = "chmod 0755 /usr/local/bin/git-credential-factory"
FILE_SETTING = "ENV FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token"


def _entries() -> list[str]:
    """The entries git reads from the image's configuration file, one per line."""
    listed = run_git(ROOT, "config", "--file", str(GITCONFIG), "--list")
    return listed.splitlines()


def test_the_configuration_holds_only_the_checkout_as_safe_directory() -> None:
    entries = _entries()

    assert entries == ["safe.directory=/work/checkout"]
    assert "safe.directory=*" not in entries


def test_the_safe_directory_is_the_settings_checkout_path() -> None:
    names_and_values = [entry.partition("=") for entry in _entries()]
    directories = [value for name, _, value in names_and_values if name == "safe.directory"]

    assert directories == [str(CHECKOUT_PATH)]


def test_the_file_says_why_and_holds_only_the_safe_section() -> None:
    lines = [line.strip() for line in GITCONFIG.read_text(encoding="utf-8").splitlines()]
    comments = [line for line in lines if line.startswith("#")]
    others = [line for line in lines if line and not line.startswith("#")]

    assert comments
    assert others == ["[safe]", "directory = /work/checkout"]


def test_the_image_copies_the_configuration_as_root_after_the_credential_helper() -> None:
    instructions = dockerfile_instructions()
    copies = [each for each in instructions if each.startswith("COPY") and "gitconfig" in each]
    helper = [index for index, each in enumerate(instructions) if CREDENTIAL_HELPER_CHMOD in each]

    assert copies == [COPY]
    assert "--chown" not in copies[0]
    assert "--chmod" not in copies[0]
    copy_index = instructions.index(COPY)
    assert instructions[copy_index + 1] == INSTALL
    assert len(helper) == 1
    assert helper[0] < copy_index
    assert helper[0] < instructions.index(FILE_SETTING)


def test_a_comment_stands_directly_above_the_copy() -> None:
    lines = DOCKERFILE.read_text(encoding="utf-8").splitlines()
    copy_line = [index for index, line in enumerate(lines) if line.strip() == COPY]

    assert len(copy_line) == 1
    assert copy_line[0] > 0
    assert lines[copy_line[0] - 1].strip().startswith("#")


def test_the_configuration_is_readable_by_all_and_owned_by_root() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert _path_settings(dockerfile, "chmod").get("/etc/gitconfig") == "0644"
    assert "/etc/gitconfig" not in _path_settings(dockerfile, "chown")
