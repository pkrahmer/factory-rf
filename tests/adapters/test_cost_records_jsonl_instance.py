"""The cost record line writes the instance last when it is set and leaves it out when not."""

import json

import pytest

from cost_records_support import (
    COMPLETED_LINE,
    REQUIRED,
    STARTED_LINE,
    _completed,
    _started,
)
from factory.adapters.cost_records_jsonl import (
    JsonLinesCostRecordReader,
    JsonLinesCostRecordWriter,
)
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CostRecordFormatError


def _with_instance(record: CostRecord) -> CostRecord:
    return record.model_copy(update={"instance": "shakedown"})


def _ending_with_instance(line: str) -> str:
    return line.removesuffix("}\n") + ',"instance":"shakedown"}\n'


@pytest.mark.parametrize(
    ("records", "text"),
    [
        ([_completed(), _started()], COMPLETED_LINE + STARTED_LINE),
        (
            [_with_instance(_completed()), _with_instance(_started())],
            _ending_with_instance(COMPLETED_LINE) + _ending_with_instance(STARTED_LINE),
        ),
    ],
    ids=["without", "with"],
)
def test_the_writer_writes_the_instance_last_only_when_it_is_set(
    records: list[CostRecord], text: str
) -> None:
    rendered = JsonLinesCostRecordWriter().render(records)

    assert rendered == text
    assert JsonLinesCostRecordReader().parse(rendered) == records


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        (REQUIRED, None),
        ({**REQUIRED, "instance": None}, None),
        ({**REQUIRED, "instance": "shakedown"}, "shakedown"),
        ({**REQUIRED, "instance": "Shakedown"}, CostRecordFormatError),
    ],
    ids=["no-key", "null", "name", "not-a-name"],
)
def test_the_reader_reads_the_instance_or_refuses_one_that_is_not_a_name(
    fields: dict[str, object], expected: str | type[CostRecordFormatError] | None
) -> None:
    line = json.dumps(fields, separators=(",", ":")) + "\n"
    reader = JsonLinesCostRecordReader()

    if expected is CostRecordFormatError:
        with pytest.raises(CostRecordFormatError) as caught:
            reader.parse(line)
        assert caught.value.fault.startswith("invalid instance: ")
        return

    assert [record.instance for record in reader.parse(line)] == [expected]
