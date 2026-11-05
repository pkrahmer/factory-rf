"""The stage image holds the agent files in `/etc/factory/agents`, none at the old place."""

from support.dockerfile_support import STAGE_DOCKERFILE

# Built from its parts, so that this file does not name the old place itself.
OLD_PLACE = "/etc/factory/" + "claude"


def test_the_image_names_no_agent_file_at_the_old_place() -> None:
    dockerfile = STAGE_DOCKERFILE.read_text(encoding="utf-8")

    assert OLD_PLACE not in dockerfile
