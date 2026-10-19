"""The preflight's rig after one probe of a red main, shared by the stale-stop tests."""

import pytest

from application.test_preflight_run import IMAGE, Rig

CLEARED_LINE = "stop cleared main_branch_failing"


def fail_once(rig: Rig) -> Rig:
    """Probe the rig's red main once and return it, the stamp holding `main_failed`."""
    assert rig.preflight(IMAGE).run() == "main_branch_failing"
    stamp = rig.stamps.read()
    assert stamp is not None
    assert stamp.main_failed == rig.main()
    return rig


@pytest.fixture
def failed_once(red_main: Rig) -> Rig:
    """Return the rig after one probe of its red main, the stamp holding `main_failed`."""
    return fail_once(red_main)
