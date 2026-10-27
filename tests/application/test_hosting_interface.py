"""The hosting-service interface: its operations and what they return."""

import inspect
from typing import get_type_hints

from factory.application.hosting import HostingService
from factory.domain.hosting import PullRequestView
from hosting_interface_support import OPERATIONS


def _public_operations() -> set[str]:
    return {
        name
        for name, member in inspect.getmembers(HostingService, callable)
        if not name.startswith("_")
    }


def test_hosting_service_has_exactly_the_ten_operations() -> None:
    assert _public_operations() == set(OPERATIONS)


def test_no_operation_returns_or_reads_labels() -> None:
    for name, expected in OPERATIONS.items():
        returned = get_type_hints(getattr(HostingService, name))["return"]
        assert returned == expected, name
    assert [name for name in _public_operations() if "label" in name] == ["set_labels"]
    assert not [field for field in PullRequestView.model_fields if "label" in field]
