"""A factory log that keeps the lines written to it, for the tests that read what was logged."""

from factory.application.machine import FactoryLog


class RecordingLog(FactoryLog):
    """Keeps the lines written to it."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def line(self, text: str) -> None:
        self.lines.append(text)
