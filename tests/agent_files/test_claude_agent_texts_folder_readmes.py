"""The documenter may write the folder READMEs, which only point to the guides."""

from support.shipped_agents import agent_body

FRAGMENTS = (
    "write",
    "folder readme",
    "`factory.shared.domain.folder_readmes`",
    "points to the guides",
    "guide page",
)


def test_the_documenter_may_write_the_folder_readmes_which_point_to_the_guides() -> None:
    lines = [line.lower() for line in agent_body("documenter").splitlines()]

    naming = [line for line in lines if all(fragment in line for fragment in FRAGMENTS)]

    assert len(naming) == 1, FRAGMENTS
