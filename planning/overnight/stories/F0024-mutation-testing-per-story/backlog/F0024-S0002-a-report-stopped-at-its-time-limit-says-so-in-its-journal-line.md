# A report stopped at its time limit says so in its journal line

## Description

After a stage's agent the factory adds one line per green check and per report to the agent's journal entry: `` `<command>`: <last line of its output> ``. A command that reaches its time limit is killed with its process group. Its last line is then whatever it printed last, for example a progress line of mutmut, and the journal line does not say that the command was stopped. The records say it (`time_limit` in `project-commands.jsonl`), but the reviewer and the human read the journal. With `mutants` as a report of the doing stage (the feature's change 2), a run killed at its 10 minutes would read like an ordinary result. This story makes `command_line` (F0023-S0002) add ` (stopped at its time limit after <seconds> s)` to the line of a result whose status is `time_limit`. A passed line, a reused line and a failed line stay exactly as they are: a failed report's own last line already says what it is. Nothing else changes. The stall of a red check keeps its detail, the records keep their fields, and no status is added.

## Interface

`factory.domain.checks` (`domain`):

```python
def command_line(result: CheckResult) -> str: ...
```

- For a result whose `status` is `time_limit`: `` `<command>`: <last_line> (stopped at its time limit after <s> s) ``, where `<s>` is `int(result.duration.total_seconds())`, the whole seconds rounded down. When `last_line` is empty it is `` `<command>`: (stopped at its time limit after <s> s) ``.
- For `passed` and `failed` results the line is the one F0023-S0002 gives (`` `<command>`: <last_line> ``, followed by the reuse note for a reused result). A reused result is always `passed` (F0023), so the two notes never meet.

`factory.application.stage` (`application`): unchanged. `StageFinisher` already writes every green check and every report through `command_line`, so a time-limited report's line is the new one.

Unchanged: `CheckResult` and its statuses, `CommandRecord`, `ResultRecord`, `MakeProjectCommands`, the stall detail of a red check, and every line of a passed or failed command.

Tests (the tester writes them): `tests/domain/test_command_line_time_limit.py` and `tests/application/test_stage_time_limited_report.py`. The stage test uses `open_story`, `stage_makefile`, `completed`, `run_stage` and `branch_head` of `tests/stage_run_support.py` (the stage `tests` of `PIPELINE_YAML`: check `lint`, report `test`), `ScriptedRun` of the fake agent runtime, and boundaries built as `dataclasses.replace(boundaries, project_commands=...)`. Their project commands are a `ProjectCommands` subclass in the test module: it returns, for `test`, `CheckResult(command="test", status="time_limit", exit_status=None, duration=timedelta(seconds=600.7), last_line="1718/1858 mutants", output_tail="1718/1858 mutants")` and hands every other command to the fixture's `boundaries.project_commands`. No earlier test changes: F0023-S0002's `tests/domain/test_command_line.py` and `tests/application/test_stage_finish.py` stay as they are and pass.

## Acceptance criteria

1. `command_line` (rows of one parametrized test, results of the command `mutants`): status `time_limit` (exit status `None`), last line `1718/1858 mutants`, duration 600.7 s gives `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) ``. The same with duration 599.999 s gives `... after 599 s)`. The same with an empty last line gives `` `mutants`: (stopped at its time limit after 600 s) ``. Status `passed` (exit 0), last line `mutants: 3 killed`, gives `` `mutants`: mutants: 3 killed ``. Status `failed` (exit 1), last line `mutants: partial, 3 killed`, gives `` `mutants`: mutants: partial, 3 killed ``.
2. The stage (one test): a story at the stage `tests` whose tester ends with `doing`, with project commands whose `test` returns the `time_limit` result of the Interface and whose `lint` runs `stage_makefile`'s target. `run_stage` moves the work item to `doing` (rule 6), and the tester's entry in the work item's text at `branch_head` ends with the two lines `` `lint`: lint done `` and `` `test`: 1718/1858 mutants (stopped at its time limit after 600 s) ``.
3. `make check` stays green.
4. docs: `docs/operator-guide.md`, *What a stage run shows*, point 3: one sentence after the example. A report stopped at its time limit gets the line with ` (stopped at its time limit after <seconds> s)` at its end, for example `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) ``. Its last line is then only what it printed last, and the records hold `time_limit`. `docs/project-guide.md`, *Project commands*: `command_line`'s rule for a `time_limit` result. `docs/decisions.md`: an entry *The journal line of a command stopped at its time limit says so*, dated with the story, with the feature's decision 10 and the rejected alternatives: a suffix for failed results too (a failed report's own line says it, and an existing test pins one) and a gentler stop in the process module.

## Smoke test

```bash
uv run -q python - <<'EOF'
from datetime import timedelta
from factory.domain.checks import CheckResult, command_line

stopped = CheckResult(command="mutants", status="time_limit", exit_status=None, duration=timedelta(seconds=600.7), last_line="1718/1858 mutants", output_tail="")
silent = stopped.model_copy(update={"last_line": ""})
failed = CheckResult(command="mutants", status="failed", exit_status=1, duration=timedelta(seconds=540), last_line="mutants: partial, 3 killed", output_tail="")
print(command_line(stopped))
print(command_line(silent))
print(command_line(failed))
EOF
```
Expect: three lines, `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) ``, `` `mutants`: (stopped at its time limit after 600 s) ``, `` `mutants`: mutants: partial, 3 killed ``

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
