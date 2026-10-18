"""Constants and helpers the wiring and preflight tests share."""

CREDENTIAL = "example-value"
HOSTED_URL = "https://github.com/example/project.git"


def every_tool(name: str) -> str | None:
    """Find every tool, each under `/usr/bin`."""
    return f"/usr/bin/{name}"
