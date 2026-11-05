"""The interfaces through which the factory reads and writes its files."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from factory.domain.cost_records import CostRecord
from factory.domain.pipeline_definition import PipelineDefinition
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


class CostRecordReader(ABC):
    """Reads a cost record file; every fault raises `CostRecordFormatError`."""

    @abstractmethod
    def parse(self, text: str) -> list[CostRecord]:
        """The records of a text in file order, blank lines ignored."""

    @abstractmethod
    def read(self, path: Path) -> list[CostRecord]:
        """The records of the file at `path`, read as UTF-8; `[]` when there is no file."""


class CostRecordWriter(ABC):
    """Writes a cost record file, one line per record."""

    @abstractmethod
    def render(self, records: Sequence[CostRecord]) -> str:
        """The text of `records` in their order; a repeated run raises `CostRecordFormatError`."""

    @abstractmethod
    def write(self, path: Path, records: Sequence[CostRecord]) -> None:
        """Write the text of `render` to `path` as UTF-8, replacing an existing file."""


class PipelineDefinitionReader(ABC):
    """Reads the pipeline definition; every fault raises `PipelineDefinitionInvalid`."""

    @abstractmethod
    def parse(self, text: str) -> PipelineDefinition:
        """The definition of a text, its left-out keys at their defaults and all faults named."""


class RecordLog[R: BaseModel](ABC):
    """An append-only file of records, one JSON object per line."""

    @abstractmethod
    def append(self, record: R) -> None:
        """Add `record` as the last line, creating the file and its folder.

        Raises `OSError` when it cannot.
        """

    @abstractmethod
    def read(self) -> list[R]:
        """The records in file order; `[]` without a file.

        A line that is not UTF-8 or does not validate is skipped.
        """
