"""The lines a program printed, read without the blank ones."""


def printed_lines(output: str) -> list[str]:
    """The non-blank lines of `output`, stripped."""
    return [line.strip() for line in output.splitlines() if line.strip()]
