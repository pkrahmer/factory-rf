"""The backlog path, story and completed run of the tick's agent definition tests."""

from datetime import timedelta

from factory.domain.agent_runs import AgentRunResult

BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"


STORY = """\
# First story

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.

## Journal
"""


COMPLETED = AgentRunResult(
    end_reason="completed", decision="tests", entry="checked.", duration=timedelta(minutes=1)
)
