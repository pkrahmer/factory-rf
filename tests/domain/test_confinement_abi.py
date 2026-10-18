"""The minimum Landlock ABI, its fault text and the error of a restriction that cannot be made."""

import pytest

from factory.domain.confinement import abi_fault
from factory.domain.errors import ConfinementError


@pytest.mark.parametrize(
    ("abi", "fault"),
    [
        (0, "the kernel offers Landlock ABI 0, the write guard needs ABI 3 or higher"),
        (2, "the kernel offers Landlock ABI 2, the write guard needs ABI 3 or higher"),
        (3, None),
        (7, None),
    ],
)
def test_a_kernel_below_abi_3_has_a_fault(abi: int, fault: str | None) -> None:
    assert abi_fault(abi) == fault


def test_confinement_error_carries_its_detail_as_the_message() -> None:
    error = ConfinementError("x")

    assert error.detail == "x"
    assert str(error) == "x"
