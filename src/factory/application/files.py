"""The interfaces through which the factory reads and writes its files."""

from abc import ABC, abstractmethod
from pathlib import Path

from factory.domain.work_item import WorkItemDocument


class WorkItemReader(ABC):
    """Reads a work item file; every fault raises `WorkItemFormatError`."""

    @abstractmethod
    def parse(self, text: str) -> WorkItemDocument:
        """The document of a work item's text, its state required and validated."""

    @abstractmethod
    def parse_specification(self, text: str) -> WorkItemDocument:
        """The body of a text whose front matter the factory does not own, its keys ignored."""

    @abstractmethod
    def read(self, path: Path) -> WorkItemDocument:
        """The document of the file at `path`, read as UTF-8 and parsed like `parse`."""


class WorkItemWriter(ABC):
    """Writes a work item file in the factory's one notation."""

    @abstractmethod
    def render(self, document: WorkItemDocument) -> str:
        """The text of `document`; a document without state raises `WorkItemFormatError`."""

    @abstractmethod
    def write(self, path: Path, document: WorkItemDocument) -> None:
        """Write the text of `render` to `path` as UTF-8, replacing an existing file."""
