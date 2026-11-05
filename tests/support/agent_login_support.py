"""The stand-in logins the login shell hands a run, shared by the runtimes' login tests."""

from pathlib import Path

API_LOGIN = "stand-in-api-login"


SUBSCRIPTION = "stand-in-login"


def _utf_16(path: Path) -> None:
    path.write_bytes(API_LOGIN.encode("utf-16"))
