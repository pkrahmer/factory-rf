"""The wiring's public names, and the comparison that catches an event kind without a handler."""

from collections.abc import Callable
from typing import get_args

import pytest

import factory.entry.wiring
from definition_support import pipeline_definition
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler, unhandled_kinds
from factory.domain.events import EventKind
from factory.entry.wiring import build_handlers
from stage_run_support import INSTANCE

ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}
KEPT = (
    "CREDENTIAL_HELPER",
    "agent_environment",
    "agent_run_environment",
    "boundaries_from_environment",
    "build_bill_service",
    "build_boundaries",
    "build_handlers",
    "build_preflight",
    "build_tick",
    "build_work_item_reader",
    "git_environment",
    "git_options",
    "handler_factory",
    "health_store",
    "leftovers_command",
    "machine_extras",
    "machine_log",
    "production_environment",
    "project_command_environment",
    "read_environment_settings",
    "read_hosting_token",
    "repository_name",
    "system_clock",
)


@pytest.mark.parametrize(
    ("name", "offered"),
    [pytest.param("NOT_YET_HANDLED", False, id="NOT_YET_HANDLED")]
    + [pytest.param(name, True, id=name) for name in KEPT],
)
def test_the_wiring_offers_its_names_but_no_list_of_kinds_without_a_handler(
    name: str, *, offered: bool
) -> None:
    assert hasattr(factory.entry.wiring, name) is offered
    assert (name in factory.entry.wiring.__all__) is offered


def _built(handlers: dict[EventKind, Handler]) -> dict[EventKind, Handler]:
    return dict(handlers)


def _without_acceptance_due(handlers: dict[EventKind, Handler]) -> dict[EventKind, Handler]:
    return {kind: handler for kind, handler in handlers.items() if kind != "acceptance_due"}


@pytest.mark.parametrize(
    ("select", "complete", "missing"),
    [
        pytest.param(_built, True, [], id="built"),
        pytest.param(_without_acceptance_due, False, ["acceptance_due"], id="no-acceptance-due"),
    ],
)
def test_a_kind_without_a_handler_is_caught_by_comparing_the_handlers_with_every_kind(
    boundaries: Boundaries,
    *,
    select: Callable[[dict[EventKind, Handler]], dict[EventKind, Handler]],
    complete: bool,
    missing: list[str],
) -> None:
    built = build_handlers(boundaries, pipeline_definition(boundaries), INSTANCE, ENVIRONMENT)
    handlers = select(built)

    assert (set(handlers) == set(get_args(EventKind))) is complete
    assert unhandled_kinds(handlers) == missing
