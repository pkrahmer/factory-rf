"""The wired boundaries wait by sleeping."""

from factory.entry.wiring import build_boundaries
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.shared.adapters.clock import SleepingWaiter
from factory.shared.domain.settings import InstanceSettings
from support.wiring_support import CREDENTIAL


def test_the_built_boundaries_wait_by_sleeping(local_settings: InstanceSettings) -> None:
    boundaries = build_boundaries(local_settings, CREDENTIAL, hosting=FakeHostingService())

    assert isinstance(boundaries.waiter, SleepingWaiter)
