"""Bills: the sums of cost records by stage and in total, and their line and table texts."""

from collections.abc import Sequence
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, ConfigDict, NonNegativeInt

from factory.domain.agent_runs import TokenCounts
from factory.domain.cost_records import CostRecord
from factory.domain.identifiers import Name

_ZERO_TOKENS = TokenCounts(input=0, output=0)
_ONE_DECIMAL = Decimal("0.1")
_TWO_DECIMALS = Decimal("0.01")
_SECONDS_PER_MINUTE = Decimal(60)
_TABLE_HEADER = "| stage | runs | min | turns | in | cached | out | USD |"
_TABLE_ALIGNMENT = "| :-- | --: | --: | --: | --: | --: | --: | --: |"
_TOTAL_CELL = "**total**"


class Bill(BaseModel):
    """The sums of a set of cost records; a value the runtime did not report is not in them."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    runs: NonNegativeInt
    runs_cost_unknown: NonNegativeInt
    duration: timedelta
    turns: NonNegativeInt
    tokens: TokenCounts
    cost_usd: Decimal


class StageBill(BaseModel):
    """The bill of one stage's records."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stage: Name
    bill: Bill


def _add_tokens(left: TokenCounts, right: TokenCounts) -> TokenCounts:
    return TokenCounts(
        input=left.input + right.input,
        output=left.output + right.output,
        cache_read=left.cache_read + right.cache_read,
        cache_creation=left.cache_creation + right.cache_creation,
    )


def _record_bill(record: CostRecord) -> Bill:
    # An unknown measure contributes nothing; only the run itself is always counted.
    seconds = record.duration_seconds
    return Bill(
        runs=1,
        runs_cost_unknown=1 if record.cost_usd is None else 0,
        duration=timedelta(0) if seconds is None else timedelta(seconds=seconds),
        turns=0 if record.turns is None else record.turns,
        tokens=_ZERO_TOKENS if record.tokens is None else record.tokens,
        cost_usd=Decimal(0) if record.cost_usd is None else record.cost_usd,
    )


def _add(left: Bill, right: Bill) -> Bill:
    return Bill(
        runs=left.runs + right.runs,
        runs_cost_unknown=left.runs_cost_unknown + right.runs_cost_unknown,
        duration=left.duration + right.duration,
        turns=left.turns + right.turns,
        tokens=_add_tokens(left.tokens, right.tokens),
        cost_usd=left.cost_usd + right.cost_usd,
    )


def _sum(bills: Sequence[Bill]) -> Bill:
    result = Bill(
        runs=0,
        runs_cost_unknown=0,
        duration=timedelta(0),
        turns=0,
        tokens=_ZERO_TOKENS,
        cost_usd=Decimal(0),
    )
    for each in bills:
        result = _add(result, each)
    return result


def bill(records: Sequence[CostRecord]) -> Bill:
    """The bill of every record, whatever its end reason, with unknown values skipped."""
    return _sum([_record_bill(record) for record in records])


def bills_by_stage(records: Sequence[CostRecord]) -> list[StageBill]:
    """One bill per stage in the order of its first record; a returning stage joins it."""
    groups: dict[str, list[CostRecord]] = {}
    for record in records:
        groups.setdefault(record.stage, []).append(record)
    return [StageBill(stage=stage, bill=bill(group)) for stage, group in groups.items()]


def total(stage_bills: Sequence[StageBill]) -> Bill:
    """The field-by-field sum of the stage bills."""
    return _sum([stage_bill.bill for stage_bill in stage_bills])


def _minutes(bill: Bill) -> str:
    seconds = Decimal(str(bill.duration.total_seconds()))
    return str((seconds / _SECONDS_PER_MINUTE).quantize(_ONE_DECIMAL, rounding=ROUND_HALF_UP))


def _dollars(bill: Bill) -> str:
    dollars = str(bill.cost_usd.quantize(_TWO_DECIMALS, rounding=ROUND_HALF_UP))
    if bill.runs_cost_unknown > 0:
        return f"{dollars} + {bill.runs_cost_unknown} unknown"
    return dollars


def _tokens_in(tokens: TokenCounts) -> int:
    return tokens.input + tokens.cache_creation


def cost_line(bill: Bill) -> str:
    """The one-line text of a bill: runs, minutes, turns, tokens and dollars."""
    tokens = bill.tokens
    return (
        f"{bill.runs} runs, {_minutes(bill)} min, {bill.turns} turns, "
        f"{_tokens_in(tokens)} tokens in ({tokens.cache_read} more from cache), "
        f"{tokens.output} out, ${_dollars(bill)}"
    )


def _row(first_cell: str, bill: Bill) -> str:
    cells = [
        first_cell,
        str(bill.runs),
        _minutes(bill),
        str(bill.turns),
        str(_tokens_in(bill.tokens)),
        str(bill.tokens.cache_read),
        str(bill.tokens.output),
        _dollars(bill),
    ]
    return "| " + " | ".join(cells) + " |"


def cost_table(stage_bills: Sequence[StageBill]) -> str:
    """The Markdown table of the stage bills, one row each, and their total as the last row."""
    rows = [_row(stage_bill.stage, stage_bill.bill) for stage_bill in stage_bills]
    return "\n".join(
        [_TABLE_HEADER, _TABLE_ALIGNMENT, *rows, _row(_TOTAL_CELL, total(stage_bills))]
    )
