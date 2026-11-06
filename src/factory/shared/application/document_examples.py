"""The interfaces that run a document's runnable examples: the fixtures and the runner."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path

from factory.shared.domain.documents import Example


class Fixture(ABC):
    """The starting point a document's examples run on."""

    @abstractmethod
    def prepare(self, folder: Path) -> dict[str, str]:
        """Build the starting point in the empty `folder`; the extra environment of the commands.

        Raises `FixtureError` when the starting point cannot be built.
        """


class ExampleRunner(ABC):
    """Runs the examples of one document, in order, in one folder of their own."""

    @abstractmethod
    def run_document(
        self, document: str, examples: list[Example], fixtures: Mapping[str, Fixture]
    ) -> list[str]:
        """The findings of the document's examples, one line each, `<document>:<line>: ...`."""
