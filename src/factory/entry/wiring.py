"""The one module that picks the concrete adapters behind the application's interfaces."""

from factory.adapters.claude_guard import judge, read_guard_settings
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.application.files import WorkItemReader

__all__ = ["build_work_item_reader", "judge", "read_guard_settings"]


def build_work_item_reader() -> WorkItemReader:
    """Return the reader of work item files."""
    return FrontmatterWorkItemReader()
