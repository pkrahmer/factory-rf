"""factory-watch's main: the streams, the boundaries and the instance it hands to the watch."""

import io
from collections.abc import Mapping

import pytest

from factory.adapters.clock import ManualClock
from factory.application.boundaries import Boundaries
from factory.application.hosting import HostingService
from factory.domain.identifiers import Name
from factory.domain.settings import InstanceSettings
from factory.entry import watch
from factory.entry.watch import main
from human_clone import HumanClone
from stage_run_support import INSTANCE
from watch_support import STORY, aged_claim, push_story_claim

SETTINGS_INSTANCE = "factory-2"
HELD_LINE = f"event: idle:-  {STORY} is held by {INSTANCE}"
INVALID_YAML = "contract: [\n"


pytestmark = pytest.mark.usefixtures("installed_agents")


def _push_held_story(boundaries: Boundaries, human: HumanClone, clock: ManualClock) -> None:
    push_story_claim(boundaries, human, aged_claim(clock, INSTANCE, "intake", 1))
    boundaries.git.fetch()


def _push_invalid_definition(boundaries: Boundaries, human: HumanClone) -> None:
    human.push_file("main", "factory/pipeline.yml", INVALID_YAML)
    boundaries.git.fetch()


def test_main_watches_as_the_given_instance_on_the_given_boundaries(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock, monkeypatch: pytest.MonkeyPatch
) -> None:
    _push_held_story(boundaries, human, clock)
    monkeypatch.delenv("FACTORY_INSTANCE", raising=False)
    out, err = io.StringIO(), io.StringIO()

    status = main([], boundaries=boundaries, instance=INSTANCE, out=out, err=err)

    assert status == 0
    assert out.getvalue().splitlines()[0] == HELD_LINE
    assert err.getvalue() == ""


def test_main_writes_an_invalid_definition_to_the_given_error_stream(
    boundaries: Boundaries, human: HumanClone
) -> None:
    _push_invalid_definition(boundaries, human)
    out, err = io.StringIO(), io.StringIO()

    status = main([], boundaries=boundaries, instance=INSTANCE, out=out, err=err)

    assert status == 1
    assert out.getvalue() == ""
    lines = err.getvalue().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("factory-watch: ")


@pytest.mark.parametrize("invalid", [False, True], ids=["held-story", "invalid-definition"])
def test_main_writes_to_the_standard_streams_when_none_are_given(
    boundaries: Boundaries,
    human: HumanClone,
    clock: ManualClock,
    capsys: pytest.CaptureFixture[str],
    *,
    invalid: bool,
) -> None:
    if invalid:
        _push_invalid_definition(boundaries, human)
    else:
        _push_held_story(boundaries, human, clock)
    capsys.readouterr()

    main([], boundaries=boundaries, instance=INSTANCE)

    captured = capsys.readouterr()
    if invalid:
        assert captured.out == ""
        lines = captured.err.splitlines()
        assert len(lines) == 1
        assert lines[0].startswith("factory-watch: ")
    else:
        assert captured.out.startswith(HELD_LINE)
        assert captured.err == ""


@pytest.mark.parametrize(
    ("given_boundaries", "given_instance"),
    [(False, None), (False, INSTANCE), (True, None)],
    ids=["both-left-out", "only-instance", "only-boundaries"],
)
def test_main_takes_both_from_the_environment_when_either_is_left_out(
    boundaries: Boundaries,
    human: HumanClone,
    clock: ManualClock,
    local_settings: InstanceSettings,
    monkeypatch: pytest.MonkeyPatch,
    *,
    given_boundaries: bool,
    given_instance: Name | None,
) -> None:
    settings = local_settings.model_copy(update={"instance": SETTINGS_INSTANCE})

    def stand_in(
        _environ: Mapping[str, str], *, _hosting: HostingService | None = None
    ) -> tuple[InstanceSettings, Boundaries]:
        return settings, boundaries

    monkeypatch.setattr(watch, "boundaries_from_environment", stand_in)
    push_story_claim(boundaries, human, aged_claim(clock, SETTINGS_INSTANCE, "intake", 61))
    boundaries.git.fetch()
    out, err = io.StringIO(), io.StringIO()

    status = main(
        [],
        boundaries=boundaries if given_boundaries else None,
        instance=given_instance,
        out=out,
        err=err,
    )

    assert status == 0
    assert err.getvalue() == ""
    assert out.getvalue().splitlines()[0] == f"event: crash:{STORY}"
