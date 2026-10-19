"""The compose file the image ships, shared by the tests that read it."""

from pathlib import Path

COMPOSE = Path(__file__).parent.parent / "image" / "compose.yml"
