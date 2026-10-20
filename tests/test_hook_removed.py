"""The hook's code is gone, and the kernel's guard and its settings are kept."""

import importlib
import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.agent_runs import GuardSettings
from factory.entry import wiring


def _has(module: str, name: str) -> bool:
    return hasattr(importlib.import_module(module), name)


def _confine_command() -> object:
    return getattr(importlib.import_module("factory.domain.agent_runs"), "CONFINE_COMMAND", None)


@pytest.mark.parametrize(
    ("check", "expected"),
    [
        pytest.param(
            lambda: importlib.util.find_spec("factory.adapters.claude_guard"),
            None,
            id="adapter-module",
        ),
        pytest.param(
            lambda: importlib.util.find_spec("factory.entry.guard"), None, id="entry-module"
        ),
        pytest.param(
            lambda: _has("factory.domain.agent_runs", "GUARD_COMMAND"), False, id="guard-command"
        ),
        pytest.param(
            lambda: _has("factory.domain.errors", "GuardSettingsInvalid"),
            False,
            id="settings-error",
        ),
        pytest.param(lambda: _has("factory.entry.wiring", "judge"), False, id="wiring-judge"),
        pytest.param(
            lambda: _has("factory.entry.wiring", "read_guard_settings"), False, id="wiring-read"
        ),
        pytest.param(lambda: "judge" in wiring.__all__, False, id="exported-judge"),
        pytest.param(lambda: "read_guard_settings" in wiring.__all__, False, id="exported-read"),
        pytest.param(_confine_command, "factory-confine", id="confine-command"),
        pytest.param(
            lambda: _has("factory.domain.agent_runs", "GuardSettings"), True, id="guard-settings"
        ),
        pytest.param(lambda: _has("factory.domain.write_paths", "refusal"), True, id="refusal"),
        pytest.param(
            lambda: _has("factory.domain.write_paths", "PROTECTED_PATHS"), True, id="protected"
        ),
        pytest.param(
            lambda: _has("factory.application.preflight", "confinement_item"),
            True,
            id="confinement-item",
        ),
    ],
)
def test_the_hook_s_code_is_gone_and_the_kernel_s_guard_is_kept(
    check: Callable[[], object], expected: object
) -> None:
    assert check() == expected


def _build(extra: dict[str, Any]) -> object:
    model: type[BaseModel] = GuardSettings
    return model(root=Path("/w"), write_paths=["src/*"], protected_paths=[], **extra)


def _fields() -> None:
    assert list(GuardSettings.model_fields) == [
        "root",
        "write_paths",
        "protected_paths",
        "tool_paths",
    ]


def _builds() -> None:
    _build({})


def _refuses_a_temporary_folder() -> None:
    with pytest.raises(ValidationError):
        _build({"temporary_directory": Path("/t")})


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(_fields, id="four-fields"),
        pytest.param(_builds, id="without-temporary-folder"),
        pytest.param(_refuses_a_temporary_folder, id="with-temporary-folder"),
    ],
)
def test_the_guard_settings_have_no_temporary_folder(check: Callable[[], None]) -> None:
    check()
