"""The rules of one confined run, the Landlock ABI they need and the fault of one that is less."""

from pydantic import BaseModel, ConfigDict

from factory.domain.agent_runs import AbsolutePath

LANDLOCK_MINIMUM_ABI = 3


def abi_fault(abi: int) -> str | None:
    """The fault of a kernel that offers Landlock ABI `abi`, or `None` when it suffices."""
    if abi >= LANDLOCK_MINIMUM_ABI:
        return None
    return (
        f"the kernel offers Landlock ABI {abi}, "
        f"the write guard needs ABI {LANDLOCK_MINIMUM_ABI} or higher"
    )


class Confinement(BaseModel):
    """The writes one agent run may make: folders, single files and its own temporary folder."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    folders: list[AbsolutePath]
    files: list[AbsolutePath]
    temporary_directory: AbsolutePath
