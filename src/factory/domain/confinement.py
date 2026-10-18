"""The Landlock ABI the kernel's write guard needs, and the fault of a kernel that offers less."""

LANDLOCK_MINIMUM_ABI = 3


def abi_fault(abi: int) -> str | None:
    """The fault of a kernel that offers Landlock ABI `abi`, or `None` when it suffices."""
    if abi >= LANDLOCK_MINIMUM_ABI:
        return None
    return (
        f"the kernel offers Landlock ABI {abi}, "
        f"the write guard needs ABI {LANDLOCK_MINIMUM_ABI} or higher"
    )
