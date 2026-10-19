"""The key of a project command's result, the digest of the definition and the known result."""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.checks import CheckResult, CheckStatus, ReusedRun
from factory.domain.known_results import (
    ResultKey,
    ResultRecord,
    definition_digest,
    known_result,
)
from git_support import PIPELINE_YAML

TREE = "a" * 40
DIGEST = "b" * 64
AT = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
KEY = ResultKey(command="check", tree=TREE, definition=DIGEST, image=None)
CHECK_TIME_LIMIT_11 = PIPELINE_YAML.replace("check: {time_limit: 10}", "check: {time_limit: 11}")
CHECK_NOT_READ = PIPELINE_YAML.replace(
    "check: {time_limit: 10}", 'check: {time_limit: 10, not_read: ["docs/*"]}'
)
CODER_LEASE_70 = PIPELINE_YAML.replace(
    'coder: {write_paths: ["src/*"]}', 'coder: {write_paths: ["src/*"], lease_duration: 70}'
)


def _digest(text: str) -> str:
    return definition_digest(RuamelPipelineDefinitionReader().parse(text))


@pytest.mark.parametrize(
    ("other", "same"),
    [
        pytest.param(PIPELINE_YAML, True, id="same-text"),
        pytest.param(CHECK_TIME_LIMIT_11, False, id="time-limit"),
        pytest.param(CHECK_NOT_READ, False, id="not-read"),
        pytest.param(CODER_LEASE_70, False, id="lease-duration"),
    ],
)
def test_the_definition_digest_changes_with_every_value_and_only_then(
    other: str, same: bool
) -> None:
    definition = RuamelPipelineDefinitionReader().parse(other)
    digest = definition_digest(definition)

    assert (digest == _digest(PIPELINE_YAML)) is same
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")
    assert digest == hashlib.sha256(definition.model_dump_json().encode("utf-8")).hexdigest()


def _record(**fields: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "key": {"command": "check", "tree": TREE, "definition": DIGEST, "image": None},
        "at": AT,
        "status": "passed",
        "last_line": "check: green",
        "duration_seconds": 12.5,
    }
    return base | fields


def _key(definition: str) -> dict[str, Any]:
    return {"command": "check", "tree": TREE, "definition": definition, "image": None}


def _check(status: str, exit_status: int | None) -> dict[str, Any]:
    return {
        "command": "check",
        "status": status,
        "exit_status": exit_status,
        "duration": timedelta(seconds=3),
        "last_line": "check: green",
        "output_tail": "",
        "reused": ReusedRun(tree=TREE, at=AT),
    }


@pytest.mark.parametrize(
    ("model", "fields", "accepted"),
    [
        pytest.param(ResultRecord, _record(reused=AT), True, id="reused-passed"),
        pytest.param(ResultRecord, _record(reused=AT, status="failed"), False, id="reused-failed"),
        pytest.param(
            ResultRecord, _record(reused=AT, status="time_limit"), False, id="reused-time-limit"
        ),
        pytest.param(ResultRecord, _record(key=_key("b" * 63)), False, id="definition-63"),
        pytest.param(ResultRecord, _record(key=_key("b" * 65)), False, id="definition-65"),
        pytest.param(ResultRecord, _record(key=_key("B" * 64)), False, id="definition-upper"),
        pytest.param(ResultRecord, _record(key=_key("b" * 64)), True, id="definition-64"),
        pytest.param(ResultRecord, _record(duration_seconds=-1), False, id="duration-minus-1"),
        pytest.param(ResultRecord, _record(duration_seconds=0), True, id="duration-0"),
        pytest.param(CheckResult, _check("passed", 0), True, id="check-reused-passed"),
        pytest.param(CheckResult, _check("failed", 2), False, id="check-reused-failed"),
        pytest.param(CheckResult, _check("time_limit", None), False, id="check-reused-limit"),
    ],
)
def test_a_reused_result_is_only_a_passed_one_and_the_key_holds_a_sha256_digest(
    model: type[BaseModel], fields: dict[str, Any], accepted: bool
) -> None:
    if accepted:
        model(**fields)
    else:
        with pytest.raises(ValidationError):
            model(**fields)


def _run(
    status: CheckStatus = "passed",
    *,
    command: str = "check",
    tree: str = TREE,
    definition: str = DIGEST,
    image: str | None = None,
    minute: int = 0,
    reused: datetime | None = None,
) -> ResultRecord:
    return ResultRecord(
        key=ResultKey(command=command, tree=tree, definition=definition, image=image),
        at=AT + timedelta(minutes=minute),
        status=status,
        last_line=f"check {status}",
        duration_seconds=0 if reused else 30,
        reused=reused,
    )


FIRST = _run(minute=0)


@pytest.mark.parametrize(
    ("records", "expected"),
    [
        pytest.param([], None, id="none"),
        pytest.param([FIRST], FIRST, id="one-passed"),
        pytest.param([FIRST, _run("failed", minute=1)], None, id="passed-then-failed"),
        pytest.param([_run("failed"), _run(minute=1)], _run(minute=1), id="failed-then-passed"),
        pytest.param([FIRST, _run(minute=5, reused=FIRST.at)], FIRST, id="passed-then-reused"),
        pytest.param([_run(command="lint")], None, id="other-command"),
        pytest.param([_run(tree="c" * 40)], None, id="other-tree"),
        pytest.param([_run(definition="d" * 64)], None, id="other-definition"),
        pytest.param([_run(image="img-2")], None, id="other-image"),
        pytest.param([FIRST, _run("time_limit", minute=1)], None, id="time-limit-last"),
        pytest.param([_run(reused=AT)], None, id="reuse-alone"),
    ],
)
def test_the_known_result_is_the_last_run_of_the_key_when_it_passed(
    records: list[ResultRecord], expected: ResultRecord | None
) -> None:
    assert known_result(records, KEY) == expected
