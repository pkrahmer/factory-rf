"""The bill command: one work item's table and cost line, or those of every one in flight."""

import io
import runpy
import sys
from pathlib import Path

import pytest

from bill_support import completed_records, sidecar_text
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader
from factory.adapters.git_cli import GitCli
from factory.application.costs import BillService
from factory.domain.identifiers import branch_name
from factory.domain.paths import cost_records_path
from factory.entry.bill import main, run
from git_support import CHECKOUT
from human_clone import HumanClone

FIRST = "F0001-S0001"
FIRST_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
SECOND = "F0001-S0002"
SECOND_PATH = "factory/features/F0001-example/in-progress/F0001-S0002-second.md"
WITHOUT_FILE = "F0001-S0003"
UNKNOWN = "F0009-S0001"
USAGE = "usage: factory-bill [<work item id>]"


def _service(git: GitCli) -> BillService:
    return BillService(git, JsonLinesCostRecordReader())


def _two_in_flight(checkout: GitCli, human: HumanClone) -> None:
    human.push_file(
        branch_name(FIRST),
        cost_records_path(FIRST_PATH),
        sidecar_text(completed_records(FIRST, 2)),
    )
    human.push_file(branch_name(SECOND), SECOND_PATH, "# Second story\n")
    human.push_file(
        branch_name(SECOND),
        cost_records_path(SECOND_PATH),
        sidecar_text(completed_records(SECOND, 3)),
    )
    human.push_file(branch_name(WITHOUT_FILE), "notes.txt", "no work item file\n")
    checkout.fetch()


def _block(service: BillService, work_item: str) -> list[str]:
    result = service.for_work_item(work_item)
    assert result is not None
    return [*result.table.split("\n"), "", f"Cost: {result.line}"]


def test_one_id_prints_the_table_and_the_cost_line(checkout: GitCli, human: HumanClone) -> None:
    _two_in_flight(checkout, human)
    service = _service(checkout)
    out = io.StringIO()

    status = run([FIRST], service, out)

    assert out.getvalue().splitlines() == _block(service, FIRST)
    assert status == 0


@pytest.mark.parametrize(
    ("argv", "line", "expected"),
    [
        ([UNKNOWN], f"no work item {UNKNOWN}", 1),
        (["F1"], "not a work item id: F1", 2),
        ([FIRST, SECOND], USAGE, 2),
    ],
    ids=["no-bill", "not-an-id", "two-arguments"],
)
def test_a_wrong_argument_prints_why_and_returns_its_status(
    checkout: GitCli, argv: list[str], line: str, expected: int
) -> None:
    out = io.StringIO()

    status = run(argv, _service(checkout), out)

    assert out.getvalue().splitlines() == [line]
    assert status == expected


def test_no_argument_prints_every_in_flight_work_item_that_has_a_bill(
    checkout: GitCli, human: HumanClone
) -> None:
    _two_in_flight(checkout, human)
    service = _service(checkout)
    out = io.StringIO()

    status = run([], service, out)

    assert out.getvalue().splitlines() == [
        FIRST,
        *_block(service, FIRST),
        "",
        SECOND,
        *_block(service, SECOND),
    ]
    assert status == 0


def test_main_reads_the_id_from_sys_argv_in_the_current_checkout(
    tmp_path: Path,
    checkout: GitCli,
    human: HumanClone,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _two_in_flight(checkout, human)
    monkeypatch.chdir(tmp_path / CHECKOUT)
    monkeypatch.setattr(sys, "argv", ["factory-bill", FIRST])

    status = main()

    assert capsys.readouterr().out.splitlines() == _block(_service(checkout), FIRST)
    assert status == 0


def test_main_with_a_list_uses_the_list_instead_of_sys_argv(
    tmp_path: Path,
    checkout: GitCli,
    human: HumanClone,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _two_in_flight(checkout, human)
    monkeypatch.chdir(tmp_path / CHECKOUT)
    monkeypatch.setattr(sys, "argv", ["factory-bill", "F1"])

    status = main([SECOND])

    assert capsys.readouterr().out.splitlines() == _block(_service(checkout), SECOND)
    assert status == 0


def test_the_module_runs_as_a_program_and_exits_with_the_status(
    tmp_path: Path,
    checkout: GitCli,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checkout.fetch()
    monkeypatch.chdir(tmp_path / CHECKOUT)
    monkeypatch.setattr(sys, "argv", ["factory-bill", UNKNOWN])

    with pytest.warns(RuntimeWarning), pytest.raises(SystemExit) as exit_info:
        runpy.run_module("factory.entry.bill", run_name="__main__")

    assert exit_info.value.code == 1
    assert capsys.readouterr().out.splitlines() == [f"no work item {UNKNOWN}"]
