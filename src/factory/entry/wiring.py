"""The one module that picks the concrete adapters behind the application's interfaces."""

from pathlib import Path

from factory.adapters.claude_guard import judge, read_guard_settings
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader
from factory.adapters.git_cli import GitCli
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.application.costs import BillService
from factory.application.files import WorkItemReader

__all__ = ["build_bill_service", "build_work_item_reader", "judge", "read_guard_settings"]


def build_work_item_reader() -> WorkItemReader:
    """Return the reader of work item files."""
    return FrontmatterWorkItemReader()


def build_bill_service(checkout: Path) -> BillService:
    """Return the bill service that reads the remote-tracking refs of `checkout`."""
    return BillService(GitCli(checkout), JsonLinesCostRecordReader())
