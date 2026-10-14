"""The bill service: a work item's bill from its sidecar on the remote-tracking refs only."""

from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from bill_support import completed_records, sidecar_text
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader
from factory.adapters.git_cli import GitCli
from factory.application.costs import BillService, WorkItemBill
from factory.domain.bills import bill, bills_by_stage, cost_line, cost_table
from factory.domain.identifiers import branch_name
from factory.domain.paths import cost_records_path
from git_support import CHECKOUT, clone, write_files
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
SIDECAR = cost_records_path(PATH)
ARCHIVED = "F0001-S0002"
ARCHIVED_PATH = "factory/features/F0001-example/done/F0001-S0002-second.md"


def _service(git: GitCli) -> BillService:
    return BillService(git, JsonLinesCostRecordReader())


def _on_branch_with_records(human: HumanClone, count: int) -> None:
    human.start(BACKLOG_PATH)
    human.push_file("main", SIDECAR, sidecar_text(completed_records(WORK_ITEM, 1)))
    human.push_file(BRANCH, SIDECAR, sidecar_text(completed_records(WORK_ITEM, count)))


def test_a_work_item_with_a_branch_is_billed_from_the_branch(
    checkout: GitCli, human: HumanClone
) -> None:
    _on_branch_with_records(human, 2)
    checkout.fetch()
    records = completed_records(WORK_ITEM, 2)

    result = _service(checkout).for_work_item(WORK_ITEM)

    assert result is not None
    assert result.work_item == WORK_ITEM
    assert result.total == bill(records)
    assert result.total.runs == 2
    assert result.stages == bills_by_stage(records)
    assert result.line == cost_line(bill(records))
    assert result.table == cost_table(bills_by_stage(records))


def test_an_archived_work_item_is_billed_from_its_sidecar_on_main(
    checkout: GitCli, human: HumanClone
) -> None:
    records = completed_records(ARCHIVED, 3)
    human.push_file("main", ARCHIVED_PATH, "# Second story\n")
    human.push_file("main", cost_records_path(ARCHIVED_PATH), sidecar_text(records))
    checkout.fetch()

    result = _service(checkout).for_work_item(ARCHIVED)

    assert result is not None
    assert result.total == bill(records)
    assert result.stages == bills_by_stage(records)


def test_an_id_without_a_file_has_no_bill(checkout: GitCli) -> None:
    assert _service(checkout).for_work_item("F0009-S0001") is None


def test_a_work_item_without_a_sidecar_has_an_empty_bill(checkout: GitCli) -> None:
    result = _service(checkout).for_work_item(WORK_ITEM)

    assert result is not None
    assert result.total == bill([])
    assert result.total.runs == 0
    assert result.stages == []


def test_the_cost_line_in_the_journal_has_no_influence(checkout: GitCli, human: HumanClone) -> None:
    human.start(BACKLOG_PATH)
    story = "# First story\n\n## Journal\n\n1. done: cost: 99 runs, $999.00\n"
    human.push_file(BRANCH, PATH, story)
    human.push_file(BRANCH, SIDECAR, sidecar_text(completed_records(WORK_ITEM, 2)))
    checkout.fetch()

    result = _service(checkout).for_work_item(WORK_ITEM)

    assert result is not None
    assert result.total.runs == 2


def test_a_local_commit_that_was_not_pushed_has_no_influence(
    tmp_path: Path, checkout: GitCli, human: HumanClone
) -> None:
    _on_branch_with_records(human, 2)
    checkout.fetch()
    checkout.checkout(BRANCH)
    write_files(tmp_path / CHECKOUT, {SIDECAR: sidecar_text(completed_records(WORK_ITEM, 3))})
    checkout.commit("local sidecar")

    result = _service(checkout).for_work_item(WORK_ITEM)

    assert result is not None
    assert result.total.runs == 2


def test_a_fresh_clone_gives_the_same_bill(
    tmp_path: Path, remote: Path, checkout: GitCli, human: HumanClone
) -> None:
    _on_branch_with_records(human, 2)
    checkout.fetch()
    fresh = GitCli(clone(remote, tmp_path / "fresh"))

    original = _service(checkout).for_work_item(WORK_ITEM)

    assert original is not None
    assert _service(fresh).for_work_item(WORK_ITEM) == original


def test_in_flight_lists_the_work_item_branches_in_work_item_order(
    checkout: GitCli, human: HumanClone
) -> None:
    for branch in [
        "work-item/F0001-A0001",
        "work-item/F0001-S0002",
        "feature/notes",
        "work-item/F0001-S0001",
        "work-item/notes",
    ]:
        human.push_file(branch, "notes.txt", f"{branch}\n")
    checkout.fetch()

    assert _service(checkout).in_flight() == ["F0001-S0001", "F0001-S0002", "F0001-A0001"]


def test_a_work_item_bill_is_frozen() -> None:
    field = "line"
    result = WorkItemBill(
        work_item=WORK_ITEM,
        total=bill([]),
        stages=[],
        line=cost_line(bill([])),
        table=cost_table([]),
    )
    with pytest.raises(ValidationError):
        setattr(result, field, "changed")


def test_a_work_item_bill_refuses_an_unknown_key() -> None:
    model: type[BaseModel] = WorkItemBill
    with pytest.raises(ValidationError):
        model(
            work_item=WORK_ITEM,
            total=bill([]),
            stages=[],
            line=cost_line(bill([])),
            table=cost_table([]),
            colour="red",
        )
