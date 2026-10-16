"""Helpers for tests that read the image's Dockerfile."""

import re
from pathlib import Path

DOCKERFILE = Path(__file__).parent.parent / "image" / "Dockerfile"


def dockerfile_instructions() -> list[str]:
    """Every instruction of the Dockerfile on one line, continuations joined, comments dropped."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    joined = re.sub(r"\\\n", " ", "\n".join(lines))
    return [" ".join(line.split()) for line in joined.splitlines() if line.strip()]
