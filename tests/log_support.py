"""Reading the factory log a test's state directory holds."""

from pathlib import Path


def log_lines(tmp_path: Path) -> list[str]:
    """Return the lines of the factory log under `tmp_path`, none when it does not exist."""
    log = tmp_path / "state" / "factory.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []
