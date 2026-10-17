---
stage: tests
pr: 164
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Each target's time in a check's result

## Assignment (as of log entry 1)

The session measured the split of `make check` by hand on 2026-10-17 (`test` 177 s, `secrets` 23 s, the rest under 3 s). The human's word ("Telemetry in v1.1") is that v1.1 records it itself: since the human's change H1, every target of this repository's `Makefile` ends with the line `<target>: green (<seconds> s)`. This story reads those lines out of the whole output of a project command into its result, so that F0012-S0013 can record them. A target that is red prints no such line, and a project whose `Makefile` prints none gets an empty list; the factory knows no target names. The test that pins the result's fields gains the new one by the human's leave (FEATURE decision 45).

## Interface

`src/factory/domain/checks.py`:

```python
class TargetTime(BaseModel):
    """One target of a project command that ended green, and the seconds it took."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    target: CommandName
    seconds: NonNegativeFloat


def target_times(output: str) -> list[TargetTime]:
    """The `<target>: green (<seconds> s)` lines of `output`, in their order."""
```

- A line counts when it matches the whole pattern `<name>: green \(([0-9]+(\.[0-9]+)?) s\)`, where `<name>` is `COMMAND_NAME_PATTERN` without its anchors (`[a-z][a-z0-9-]*`), built from that constant rather than written again; ASCII digits only, with nothing before or after it on the line (a trailing `\r` is not part of the line). Any other line is skipped, `check: green` among them.
- A target that occurs twice gives two entries.

`CheckResult` gains `targets: list[TargetTime] = []`, the last field.

`src/factory/adapters/make_commands.py`: `MakeProjectCommands.run` sets `targets=target_times(<the whole output>)`, not only the tail.

Tests: `tests/domain/test_target_times.py` (criteria 1 to 3), and for criterion 4 new test functions in `tests/adapters/test_make_commands.py`, which writes a `Makefile` into `tmp_path` through its `_commands` helper and runs the real `make`. By the human's leave (FEATURE decision 45), and no other change to an earlier story's test: `test_fields_are_exactly_the_generic_six` in `tests/domain/test_checks.py` becomes `test_fields_are_exactly_the_generic_seven`, its set gaining `targets`.

## Acceptance criteria

1. `target_times("lint: green (0.1 s)\ntypes: green (12 s)\ncheck: green\n")` is `[TargetTime(target="lint", seconds=0.1), TargetTime(target="types", seconds=12.0)]`.
2. Each of these lines gives no entry: `check: green`, `  lint: green (0.1 s)`, `lint: green (0.1 s) `, `lint: green (0.1s)`, `lint: green (-1 s)`, `lint: green (1. s)`, `Lint: green (1 s)`, `lint: red (1 s)`, `lint: green (١ s)` (an Arabic-Indic digit); each of `lint: green (0 s)` and `lint: green (0.1 s)\r` gives one. Rows of one parametrized test.
3. A target printed twice gives two entries in order; an empty output gives `[]`.
4. `MakeProjectCommands.run("check", ...)` on a `Makefile` whose `check` target prints `lint: green (0.5 s)`, then forty lines of other output, then `test: green (2.0 s)` and `check: green` gives a result whose `targets` are those two entries, though the first is outside `output_tail`; a target that prints no such line gives `targets == []`.
5. `make check` stays green.
6. docs: the project guide's section *Project commands* names `targets` among `CheckResult`'s fields, and says that a result carries the targets that printed `<target>: green (<seconds> s)`, read from the whole output, and that this repository's `Makefile` prints that line for each target. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from factory.domain.checks import target_times
for time in target_times('lint: green (0.1 s)\nsecrets: green (22.6 s)\nsomething else\ncheck: green\n'):
    print(time.target, time.seconds)
"
```
Expect: two lines: `lint 0.1` and `secrets 22.6`.

```bash
make lint | tail -1
```
Expect: one line of the form `lint: green (<n>.<d> s)`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names `factory.domain.checks` (`TargetTime`, `target_times`, `CheckResult.targets` as last field) and `MakeProjectCommands.run` in `adapters/make_commands.py`. `COMMAND_NAME_PATTERN` and `CommandName` already exist in `checks.py`, so building the pattern from the constant is possible. The pattern, the digits rule, the `\r` rule and the duplicate-target rule are each stated precisely.
   - Criteria: 1 to 4 are each testable by one function (2 as one parametrized table). Every rule has both sides: the matching lines in 1 and 3, the rejected lines in 2 (`check: green`, indentation, trailing space, missing space, negative, `1.`, uppercase, `red`, Arabic-Indic digit), and the whole-output read plus the no-line case in 4. Every behaviour in the Interface comments is covered. The change to `test_fields_are_exactly_the_generic_six` is authorised by FEATURE decision 45.
   - Demo: both blocks are runnable. Each `Expect:` line can be checked against the output: `lint 0.1` and `secrets 22.6`, and a `lint: green (<n>.<d> s)` line.
   - Architecture: pure parsing sits in domain, the adapter only calls it, and no layer rule is broken.
   - Scope: this is item 1.4 of FEATURE.md (S0012). It is not under Out of scope, and S0013 is left to record the result.
