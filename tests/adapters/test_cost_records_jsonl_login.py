"""The cost record line writes the login as its last key, only when it is set."""

import pytest

from cost_records_support import COMPLETED_LINE, _completed
from factory.adapters.cost_records_jsonl import (
    JsonLinesCostRecordReader,
    JsonLinesCostRecordWriter,
)
from factory.domain.cost_records import CostRecord


@pytest.mark.parametrize(
    ("update", "suffix"),
    [
        pytest.param({"login": "api_key"}, ',"login":"api_key"', id="login"),
        pytest.param({"login": None}, "", id="none"),
        pytest.param(
            {"instance": "shakedown", "denials": 1, "denied_paths": ["src/a.py"], "login": "none"},
            ',"instance":"shakedown","denials":1,"denied_paths":["src/a.py"],"login":"none"',
            id="after-the-denials",
        ),
    ],
)
def test_the_writer_writes_the_login_last_only_when_set(
    update: dict[str, object], suffix: str
) -> None:
    record = CostRecord.model_validate({**_completed().model_dump(), **update})

    rendered = JsonLinesCostRecordWriter().render([record])

    assert rendered == COMPLETED_LINE.removesuffix("}\n") + suffix + "}\n"
    assert JsonLinesCostRecordReader().parse(rendered) == [record]
