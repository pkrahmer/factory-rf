"""The faults a file reader reports for a pydantic validation error, in the readers' order."""

from pydantic import ValidationError
from pydantic_core import ErrorDetails

# The rank of each kind of validation fault; the lowest comes first.
_UNKNOWN_KEY, _MISSING_KEY, _INVALID_VALUE, _INVALID_WHOLE = range(4)


def _key_path(location: tuple[int | str, ...]) -> str:
    path = ""
    for part in location:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}" if path else part
    return path


def _rank(error: ErrorDetails) -> int:
    if error["type"] == "extra_forbidden":
        return _UNKNOWN_KEY
    if error["type"] == "missing":
        return _MISSING_KEY
    if error["loc"]:
        return _INVALID_VALUE
    return _INVALID_WHOLE


def _fault(error: ErrorDetails, whole: str) -> str:
    path = _key_path(error["loc"])
    rank = _rank(error)
    if rank == _UNKNOWN_KEY:
        return f"unknown key: {path}"
    if rank == _MISSING_KEY:
        return f"missing key: {path}"
    if rank == _INVALID_VALUE:
        return f"invalid {path}: {error['msg']}"
    return f"invalid {whole}: {error['msg']}"


def all_faults(validation_error: ValidationError, whole: str) -> list[str]:
    """Every fault, ranked: unknown key, missing key, invalid value, then invalid `whole`."""
    # The sort is stable, so faults of one rank keep pydantic's order, which is the fields' order.
    ranked = sorted(validation_error.errors(), key=_rank)
    return [_fault(error, whole) for error in ranked]


def first_fault(validation_error: ValidationError, whole: str) -> str:
    """The first fault of `all_faults`."""
    return all_faults(validation_error, whole)[0]
