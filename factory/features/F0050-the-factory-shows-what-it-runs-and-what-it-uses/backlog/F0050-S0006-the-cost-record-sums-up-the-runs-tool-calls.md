# The cost record sums up the run's tool calls

## Description

The transcripts of S0005 stay inside the site, so an evaluation from a distance cannot read them. Most of its questions need no content, though: where a run spent its time and turns, how often it ran commands or read files, how many of its tool calls failed. This story puts a summary without content into every completed cost record, so that the records on GitHub and the Factory Timeline answer those questions: for each tool the run used, the number of calls, the number that failed, and the seconds they took. It holds no command text, no file content, no path and no argument, so it says nothing the record does not already say about the project. It is read from the run's transcript or the runtime's stream, before the transcript is copied or thrown away; it is written whether or not `FACTORY_TRANSCRIPT_DIR` is set.

## Interface

- A new model `ToolUse` in `factory.domain.cost_records`, frozen, unknown keys refused: `tool` (the tool's name as the runtime gives it, for example `Bash`, `Read`, `Edit`, `bash`; at most 64 characters of letters, digits, `_`, `-`, `.` and `:`), `calls` (`NonNegativeInt`), `failed` (`NonNegativeInt`, at most `calls`), `seconds` (a non-negative finite float, or `None` when the runtime gives no times).
- `CostRecord` gets `tools: list[ToolUse] | None = None`, sorted by `tool`, one entry per tool; `None` on a `started` record and when the run's tool calls cannot be read; `[]` for a run with no tool call. The records contract's version follows its rule.
- Each runtime's wrapper reads the calls from what it already has: Claude Code's session transcript (`tool_use` and its `tool_result` with `is_error`), opencode's stream events. A tool's name that breaks the form above is counted under `other`. The coder decides the reading; nothing of a call's input or output leaves the wrapper.

## Acceptance criteria

1. A completed run of each runtime carries `tools` with one entry per tool used, its calls, its failed calls and its seconds. Rows: Claude Code, opencode, a run with no tool call (`[]`).
2. A failed call (Claude Code's `is_error`, opencode's error state) counts in `failed`; `failed` above `calls` is refused by the model.
3. A tool name with a space, a slash, or more than 64 characters is counted under `other`.
4. A record's `tools` holds no text of any call's input or output: rows where a call's input holds a path, a command and a string shaped like a key, none of which appears in the record's JSON.
5. A transcript or stream that cannot be read leaves `tools` as `None` and does not fail the run.
6. `make check` stays green.
7. docs: `docs/operator-guide.md`: in the section on cost records, `tools` and its fields, and that it holds no content. `docs/decisions.md`: one entry with feature decision 6's second half. `README.md` and the project guide: none.

## Smoke test

```bash
grep -cE '^class ToolUse\(BaseModel\):$' src/factory/domain/cost_records.py
uv run pytest tests/domain tests/adapters -q -k tool 2>&1 | tail -1
```

Expect: `1`, then a line that ends in `passed` with no `failed`.

## Journal
