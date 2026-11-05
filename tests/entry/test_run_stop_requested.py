"""The factory's own stop reaches the boundaries every tick, and so its preflight, is built from."""

from collections.abc import Callable
from typing import override

import pytest

import factory.entry.run as run_module
from factory.adapters.fake_images import FakeImages
from factory.application.boundaries import Boundaries
from factory.application.tick import Tick, TickOutcome
from factory.entry.run import run_instance
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.shared.domain.settings import InstanceSettings


class AskingTick(Tick):
    """Asks its boundaries' `stop_requested` before and after the factory's stop is requested."""

    def __init__(
        self,
        stop_requested: Callable[[], bool],
        request: Callable[[], None],
        seen: list[bool],
    ) -> None:
        self._stop_requested = stop_requested
        self._request = request
        self._seen = seen

    @override
    def run(self, *, fetched: bool = False) -> TickOutcome:
        self._seen.append(self._stop_requested())
        self._request()
        self._seen.append(self._stop_requested())
        return TickOutcome()


def test_the_tick_built_after_the_image_is_chosen_sees_the_factorys_own_stop(
    base_identity_settings: InstanceSettings,
    hosting: FakeHostingService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stopping = [False]
    seen: list[bool] = []

    def request() -> None:
        stopping[0] = True

    def build(boundaries: Boundaries, _given: InstanceSettings) -> Tick:
        return AskingTick(boundaries.stop_requested, request, seen)

    monkeypatch.setattr(run_module, "build_tick", build)

    run_instance(
        base_identity_settings,
        sleep=lambda _seconds: None,
        should_stop=lambda: stopping[0],
        hosting=hosting,
        images=FakeImages(),
    )

    assert seen == [False, True]
