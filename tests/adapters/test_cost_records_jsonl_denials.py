"""The cost record line writes the denials after the instance, each only when it is set."""

import pytest

from cost_records_support import COMPLETED_LINE, _completed
from factory.adapters.cost_records_jsonl import (
    JsonLinesCostRecordReader,
    JsonLinesCostRecordWriter,
)
from factory.domain.cost_records import CostRecord


@pytest.mark.parametrize(
    ("denials", "denied_paths", "suffix"),
    [
        (None, None, ""),
        (2, ["src/a.py"], ',"denials":2,"denied_paths":["src/a.py"]'),
        (2, None, ',"denials":2'),
        (0, [], ',"denials":0,"denied_paths":[]'),
    ],
    ids=["neither", "both", "count-only", "zero-and-empty"],
)
def test_the_writer_writes_the_denials_after_the_instance_only_when_set(
    denials: int | None, denied_paths: list[str] | None, suffix: str
) -> None:
    record = _completed().model_copy(
        update={"instance": "shakedown", "denials": denials, "denied_paths": denied_paths}
    )
    record = CostRecord.model_validate(record.model_dump())

    rendered = JsonLinesCostRecordWriter().render([record])

    assert (
        rendered == COMPLETED_LINE.removesuffix("}\n") + ',"instance":"shakedown"' + suffix + "}\n"
    )
    assert JsonLinesCostRecordReader().parse(rendered) == [record]
