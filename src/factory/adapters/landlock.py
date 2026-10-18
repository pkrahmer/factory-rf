"""Landlock through `ctypes`: a process restricts its own writes and those of its children."""

import ctypes
import os
import stat
from collections.abc import Sequence
from pathlib import Path

from factory.domain.errors import ConfinementError

WRITE_RIGHTS = 0x7FF2  # the twelve write rights of ABI 3: bits 1 and 4 to 14
FILE_RIGHTS = 0x4002  # write a file and truncate it: bits 1 and 14

_SYS_LANDLOCK_CREATE_RULESET = 444
_SYS_LANDLOCK_ADD_RULE = 445
_SYS_LANDLOCK_RESTRICT_SELF = 446
_LANDLOCK_CREATE_RULESET_VERSION = 1
_LANDLOCK_RULE_PATH_BENEATH = 1
_PR_SET_NO_NEW_PRIVS = 38

_libc = ctypes.CDLL(None, use_errno=True)
_libc.syscall.restype = ctypes.c_long
_libc.prctl.restype = ctypes.c_int


class _RulesetAttr(ctypes.Structure):
    _fields_ = (("handled_access_fs", ctypes.c_uint64),)


class _PathBeneathAttr(ctypes.Structure):
    # The kernel declares this struct packed: 12 bytes, no padding after the descriptor.
    _pack_ = 1
    _fields_ = (("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32))


def abi_version() -> int:
    """The Landlock ABI the kernel offers; 0 when it offers none."""
    version = _libc.syscall(
        ctypes.c_long(_SYS_LANDLOCK_CREATE_RULESET),
        ctypes.c_void_p(None),
        ctypes.c_size_t(0),
        ctypes.c_uint32(_LANDLOCK_CREATE_RULESET_VERSION),
    )
    return max(int(version), 0)


def restrict_writes(folders: Sequence[Path], files: Sequence[Path]) -> None:
    """Refuse every write of this process and its children but beneath `folders` and on `files`."""
    # Every path is checked before the first system call, so a refusal restricts nothing.
    for folder in folders:
        _check_path(folder, expect_folder=True)
    for file in files:
        _check_path(file, expect_folder=False)
    ruleset_fd = _create_ruleset()
    try:
        for folder in folders:
            _add_rule(ruleset_fd, folder, WRITE_RIGHTS)
        for file in files:
            _add_rule(ruleset_fd, file, FILE_RIGHTS)
        _restrict_self(ruleset_fd)
    finally:
        os.close(ruleset_fd)


def _check_path(path: Path, *, expect_folder: bool) -> None:
    try:
        mode = os.lstat(path).st_mode
    except OSError as error:
        raise ConfinementError(f"cannot open {path}: {error.strerror}") from error
    if stat.S_ISLNK(mode):
        raise ConfinementError(f"{path} is a symbolic link")
    if expect_folder and not stat.S_ISDIR(mode):
        raise ConfinementError(f"{path} is not a folder")
    if not expect_folder and stat.S_ISDIR(mode):
        raise ConfinementError(f"{path} is a folder")


def _create_ruleset() -> int:
    attr = _RulesetAttr(handled_access_fs=WRITE_RIGHTS)
    ruleset_fd = _libc.syscall(
        ctypes.c_long(_SYS_LANDLOCK_CREATE_RULESET),
        ctypes.byref(attr),
        ctypes.c_size_t(ctypes.sizeof(attr)),
        ctypes.c_uint32(0),
    )
    _raise_on_failure(ruleset_fd, "landlock_create_ruleset")
    return int(ruleset_fd)


def _add_rule(ruleset_fd: int, path: Path, rights: int) -> None:
    try:
        parent_fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
    except OSError as error:
        raise ConfinementError(f"cannot open {path}: {error.strerror}") from error
    try:
        attr = _PathBeneathAttr(allowed_access=rights, parent_fd=parent_fd)
        result = _libc.syscall(
            ctypes.c_long(_SYS_LANDLOCK_ADD_RULE),
            ctypes.c_int(ruleset_fd),
            ctypes.c_int(_LANDLOCK_RULE_PATH_BENEATH),
            ctypes.byref(attr),
            ctypes.c_uint32(0),
        )
        _raise_on_failure(result, f"landlock_add_rule for {path}")
    finally:
        os.close(parent_fd)


def _restrict_self(ruleset_fd: int) -> None:
    result = _libc.prctl(
        ctypes.c_int(_PR_SET_NO_NEW_PRIVS),
        ctypes.c_ulong(1),
        ctypes.c_ulong(0),
        ctypes.c_ulong(0),
        ctypes.c_ulong(0),
    )
    _raise_on_failure(result, "prctl PR_SET_NO_NEW_PRIVS")
    result = _libc.syscall(
        ctypes.c_long(_SYS_LANDLOCK_RESTRICT_SELF), ctypes.c_int(ruleset_fd), ctypes.c_uint32(0)
    )
    _raise_on_failure(result, "landlock_restrict_self")


def _raise_on_failure(result: int, call: str) -> None:
    if result < 0:
        raise ConfinementError(f"{call} failed: {os.strerror(ctypes.get_errno())}")
