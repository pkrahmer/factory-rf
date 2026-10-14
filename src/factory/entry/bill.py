"""The bill command: the cost table and cost line of one work item, or of every one in flight."""

import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from factory.application.costs import BillService, WorkItemBill
from factory.domain.identifiers import ACCEPTANCE_ID, STORY_ID
from factory.entry.wiring import build_bill_service

_USAGE = "usage: factory-bill [<work item id>]"
_OK = 0
_NO_BILL = 1
_FAILURE = 2


def _block(work_item_bill: WorkItemBill) -> str:
    return f"{work_item_bill.table}\n\nCost: {work_item_bill.line}\n"


def _is_work_item_id(argument: str) -> bool:
    return re.fullmatch(f"{STORY_ID}|{ACCEPTANCE_ID}", argument) is not None


def _one(service: BillService, argument: str, out: TextIO) -> int:
    if not _is_work_item_id(argument):
        out.write(f"not a work item id: {argument}\n")
        return _FAILURE
    work_item_bill = service.for_work_item(argument)
    if work_item_bill is None:
        out.write(f"no work item {argument}\n")
        return _NO_BILL
    out.write(_block(work_item_bill))
    return _OK


def _all_in_flight(service: BillService, out: TextIO) -> int:
    blocks: list[str] = []
    for work_item in service.in_flight():
        work_item_bill = service.for_work_item(work_item)
        if work_item_bill is not None:
            blocks.append(f"{work_item}\n{_block(work_item_bill)}")
    out.write("\n".join(blocks))
    return _OK


def run(argv: Sequence[str], service: BillService, out: TextIO) -> int:
    """Write the bill of the one id in `argv`, or of every work item in flight, and return."""
    if len(argv) > 1:
        out.write(f"{_USAGE}\n")
        return _FAILURE
    if argv:
        return _one(service, argv[0], out)
    return _all_in_flight(service, out)


def main(argv: Sequence[str] | None = None) -> int:
    """Bill from the checkout in the current directory, the arguments `argv` or the command's."""
    arguments = sys.argv[1:] if argv is None else argv
    return run(arguments, build_bill_service(Path.cwd()), sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
