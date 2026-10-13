"""The one fault a file reader reports for a pydantic validation error, in the readers' order."""

from pydantic import ValidationError
from pydantic_core import ErrorDetails

# The rank of each kind of validation fault; the lowest is reported.
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


def first_fault(validation_error: ValidationError, whole: str) -> str:
    """The first fault: unknown key, missing key, invalid value, then invalid `whole`."""
    # `min` keeps the first of equal rank, and pydantic lists errors in the order of the fields.
    return _fault(min(validation_error.errors(), key=_rank), whole)
