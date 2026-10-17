---
stage: done
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
3. tester: Wrote the tests for criteria 1 to 4, mapped below.
   - criterion 1: tests/domain/test_target_times.py::test_green_target_lines_are_read_in_order_and_others_skipped
   - criterion 2: tests/domain/test_target_times.py::test_only_a_line_matching_the_whole_pattern_counts. It is one parametrized test with 11 rows: the 9 lines that must give no entry, plus `lint: green (0 s)` and `lint: green (0.1 s)\r`, which must give one entry each. Each row's line is passed as the whole output. The Arabic-Indic digit is written as `١`.
   - criterion 3: tests/domain/test_target_times.py::test_target_printed_twice_gives_two_entries_in_order and ::test_empty_output_gives_no_entries
   - criterion 4: tests/adapters/test_make_commands.py::test_targets_are_read_from_the_whole_output checks that the `lint` line is outside `output_tail` but still appears in `targets`. ::test_target_printing_no_green_line_has_no_targets checks that a target printing only `check: green` gives `targets == []`.
   - Interface limits on `TargetTime`, as CLAUDE.md requires: tests/domain/test_target_times.py::test_target_time_requires_a_command_name_and_non_negative_seconds checks that seconds 0.0 is accepted, -0.1 is refused, and target `Lint` is refused. ::test_target_time_refuses_an_unknown_field checks the forbidden extra field.
   - By the human's leave (FEATURE decision 45), I renamed tests/domain/test_checks.py::test_fields_are_exactly_the_generic_six to `test_fields_are_exactly_the_generic_seven` and added `targets` to its set. I made no other change to that file.

   Files: I created tests/domain/test_target_times.py. In tests/adapters/test_make_commands.py I added two functions and the import `from factory.domain.checks import TargetTime`.

   State of the run: `make test` is red as intended. The test runner could not import `TargetTime` from `factory.domain.checks`, nor `target_times`, so both test_target_times.py and test_make_commands.py fail at collection. test_fields_are_exactly_the_generic_seven fails on the missing field. `make lint` is green. I skipped the type check, as the stage allows.

   Nothing open. I did not test that `CheckResult.targets` defaults to `[]`, because no criterion names it.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/domain/test_target_times.py - ImportError while importing test mo...
4. coder: implemented the target times in commit e7903b9. `make check` is green: all tests pass and coverage is 99.52 %.
      - `src/factory/domain/checks.py`: added `TargetTime` (frozen, extra fields forbidden, `target: CommandName`, `seconds: NonNegativeFloat`) and `target_times(output)`. The function checks each line from `output.splitlines()` with `fullmatch`, so it takes only whole lines and the trailing `\r` is gone before matching. The regex is built from `COMMAND_NAME_PATTERN` with `removeprefix("^")` and `removesuffix("$")`, then `: green \(([0-9]+(?:\.[0-9]+)?) s\)`. The explicit `[0-9]` accepts only ASCII digits, which `\d` would not do. `CheckResult` gained `targets: list[TargetTime] = []` as its last field.
      - `src/factory/adapters/make_commands.py`: `MakeProjectCommands.run` passes `targets=target_times(result.stdout)`, so it reads the whole output and not the 30-line tail.
      - Main decision: matching line by line with `fullmatch`. I rejected one `re.MULTILINE` `finditer` over the whole text: with it, a `\r` before the line end needs special handling, and an anchor mistake could let indented lines or lines with trailing text through.
      - Refactor: I reread the diff and nothing needed changing, so there is no refactor commit.
      - Noticed, not touched: `splitlines` also breaks on rare Unicode separators such as `\x85` and ` `. The Interface does not cover these, and such a fragment cannot match the pattern unless it is a whole `<target>: green (<n> s)` line anyway.

   `make check`: check: green
   `make duplicates`: duplicates: 3 new, 39 known, 0 gone
5. reviewer: no findings.
      - Acceptance criteria: criteria 1 to 4 each have a test that matches the criterion it is named for. Criterion 2 is one parametrized table: nine refused lines and two accepted ones (`0 s`, and a trailing `\r`). In criterion 4, the `check` target prints 43 lines, so the `lint` line falls outside the 30-line `output_tail`, and the test asserts this. The `TargetTime` limits are tested on both sides: `seconds` 0.0 is accepted and -0.1 refused, `Lint` is refused, and an extra field is refused. The coder's entry records `make check` green.
      - Implementation: in `src/factory/domain/checks.py`, `_TARGET_TIME_LINE` is built from `COMMAND_NAME_PATTERN` and uses `[0-9]`, so only ASCII digits match. `fullmatch` runs on each line from `splitlines()`. `run_process` decodes bytes without universal newlines, so a `\r` reaches the parser, and `splitlines` drops it as the Interface requires. `targets` is the last field of `CheckResult`. `MakeProjectCommands.run` reads `result.stdout` in full, not the tail.
      - Architecture: the parsing lives in the domain and has no I/O. The adapter only calls it. No layer rule is broken.
      - Security: no silencing markers, no command built from strings, no secrets.
      - `make duplicates` (3 new): one is vulture's `checks.py: unused variable 'targets'`. This is a false positive: it is a Pydantic field that S0013 will read. The other two (`disk_space.py` and `machine.py` `used_bytes`) are in files this diff does not touch.
      - Considered, not a finding: `splitlines` also splits on a `\r` in the middle of a line (and on `\x85` and similar characters), so `foo\rlint: green (1 s)` would count. The Interface does not define this case, and the coder's entry names it.
      - Ticket hygiene: the log gives the main decision (a per-line `fullmatch` rather than a `MULTILINE` `finditer`) and the rejected alternative. `Assignment` matches what was built. Criterion 6 still describes what the project guide must say.
6. documenter: changed `docs/project-guide.md`, section *Project commands*, as criterion 6 asks. The `CheckResult` field list now includes `targets`. A new paragraph says `targets` is a list of `TargetTime` (`target`, `seconds`) read by `target_times` from the whole output, not only the tail. It covers the exact line `<target>: green (<seconds> s)`, the order printed, two entries for a target printed twice, and `[]` when the Makefile prints no such line. It also says a red target prints none, and that this repository's `Makefile` prints the line for each target.
   - Checks: `python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, because I changed only docs. The factory runs it next.
   - Cross-read: `README.md`, `docs/operator-guide.md` and `docs/decisions.md` against the diff. None mentions `CheckResult`'s fields or the target lines, so I left them as they were. The code matches the Interface, so there are no findings for the coder.
   - Stale but unrelated: nothing seen.

   `make check`: check: green
   `make documents`: documents ok
7. demo: I ran both commands from the repository root, exactly as written. Both met their `Expect:` lines and nothing contradicts any acceptance criterion.

   1. `uv run python -c "from factory.domain.checks import target_times …"` exited with 0:
   ```
   lint 0.1
   secrets 22.6
   ```
   Met: the expectation was two lines, `lint 0.1` and `secrets 22.6`. The parser skipped `something else` and `check: green`, which agrees with criteria 1 and 2.

   2. `make lint | tail -1` exited with 0:
   ```
   lint: green (0.0 s)
   ```
   Met: the expectation was one line of the form `lint: green (<n>.<d> s)`. This also shows the line that criterion 6 says this repository's `Makefile` prints for each target.

   Findings: none. Open: nothing.
8. done (pull request merged); cost: 6 runs, 3.5 min, 32 turns, 147k tokens in (361k more from cache), 12k out, $0.88
