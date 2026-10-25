"""The guard settings of a stage hold the root, its write paths and the protected paths only."""

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.write_paths import WritePathService
from factory.domain.agent_runs import GuardSettings
from factory.domain.write_paths import PROTECTED_PATHS
from write_path_support import stage_start

PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"


def test_a_tester_s_stage_gives_the_root_the_write_paths_and_the_protected_paths(
    boundaries: Boundaries, checkout: GitCli
) -> None:
    settings = WritePathService(boundaries).at(stage_start(checkout, "tests"), PATH)

    assert settings == GuardSettings(
        root=boundaries.checkout, write_paths=["tests/*"], protected_paths=list(PROTECTED_PATHS)
    )
    assert set(settings.model_dump()) == {"root", "write_paths", "protected_paths"}
