"""The verdict of the write-path guard on a Claude Code `PreToolUse` payload."""

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, StrictStr, ValidationError

from factory.domain.agent_runs import GuardSettings
from factory.domain.errors import GuardSettingsInvalid
from factory.domain.write_paths import refusal


class GuardVerdict(BaseModel):
    """Whether a tool call may write, and the refusal text when it may not."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    allowed: bool
    message: str = ""


class _ToolInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    file_path: StrictStr | None = None


class _Payload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tool_input: _ToolInput | None = None


_ALLOWED = GuardVerdict(allowed=True)


def read_guard_settings(path: Path) -> GuardSettings:
    """Read the settings file that `GuardSettings.model_dump_json()` wrote."""
    try:
        return GuardSettings.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValidationError) as error:
        raise GuardSettingsInvalid(str(path), str(error)) from error


def judge(payload: str, settings: GuardSettings) -> GuardVerdict:
    """Judge the file a tool call names against the settings; never raises."""
    file_path = _file_path(payload)
    if not file_path:
        # Fail open for what cannot be read, as v1 does.
        return _ALLOWED
    relative = _relative_real_path(file_path, settings.root)
    if relative is None:
        return GuardVerdict(allowed=False, message=f"{file_path} is outside the checkout.")
    message = refusal(relative, settings)
    if message is None:
        return _ALLOWED
    return GuardVerdict(allowed=False, message=message)


def _file_path(payload: str) -> str | None:
    try:
        tool_input = _Payload.model_validate_json(payload).tool_input
    # Pydantic reports malformed JSON as a ValidationError too.
    except ValidationError:
        return None
    return None if tool_input is None else tool_input.file_path


def _relative_real_path(file_path: str, root: Path) -> str | None:
    try:
        real_root = Path(os.path.realpath(root))
        real_path = Path(os.path.realpath(root / file_path))
    except (ValueError, OSError):
        return None
    if not real_path.is_relative_to(real_root):
        return None
    return real_path.relative_to(real_root).as_posix()
