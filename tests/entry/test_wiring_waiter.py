"""The wired boundaries wait by sleeping."""

from factory.adapters.clock import SleepingWaiter
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from wiring_support import CREDENTIAL


def test_the_built_boundaries_wait_by_sleeping(local_settings: InstanceSettings) -> None:
    boundaries = build_boundaries(local_settings, CREDENTIAL, hosting=FakeHostingService())

    assert isinstance(boundaries.waiter, SleepingWaiter)
