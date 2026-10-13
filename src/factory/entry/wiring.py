"""The one module that picks the concrete adapters behind the application's interfaces."""

from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.application.files import WorkItemReader


def build_work_item_reader() -> WorkItemReader:
    """Return the reader of work item files."""
    return FrontmatterWorkItemReader()
