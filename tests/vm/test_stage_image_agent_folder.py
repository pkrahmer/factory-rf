"""The stage image holds the agent files in `/etc/factory/agents`, none at the old place."""

from pathlib import Path

ROOT = Path(__file__).parents[2]
STAGE_DOCKERFILE = ROOT / "vm" / "Dockerfile"
# Built from its parts, so that this file does not name the old place itself.
OLD_PLACE = "/etc/factory/" + "claude"
NEW_PLACE = "/etc/factory/agents"


def test_the_image_names_no_agent_file_at_the_old_place() -> None:
    dockerfile = STAGE_DOCKERFILE.read_text(encoding="utf-8")

    assert OLD_PLACE not in dockerfile
    assert f"COPY agents {NEW_PLACE}" in dockerfile.splitlines()
