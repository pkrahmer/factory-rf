# The operator guide on a failing report

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

The second feature acceptance of F0005 ran a stage whose report (`test`) was red. The agent's entry ended with `` `test`: 1 failed ``, and the stage moved forward as decided. That is the built behaviour. `StageFinisher` adds one line `` `<command>`: <last line> `` for every report that ran, passed or not (`src/factory/application/stage.py`, `_run_checks_and_reports`). `tests/application/test_stage_finish.py::test_each_green_check_and_each_report_adds_its_last_line_to_the_entry` asserts it. `docs/project-guide.md`, "The stage protocol", step 4, says the same.

`docs/operator-guide.md`, "A stall by a red check", contradicts this in its bullet on reports: "They are recorded and never hold a move: a failing report adds no line to the entry and stops nothing." An operator who trusts it reads every report line in the journal as a passed report. This story corrects that bullet. A report's line is added whether the report passed or failed, and only its last line tells which. A failing report still holds nothing.

This story is documentation only. The tester writes no tests, the coder has nothing to build, and the documenter writes it from the docs criterion. The human may prefer to make the one-sentence edit by hand.

## Interface

None: no code changes. File: `docs/operator-guide.md`, the bullet on reports in "A stall by a red check". `docs/project-guide.md` ("The stage protocol", step 4) and the operator guide's "What a stage run shows" (item 3) are read for consistency. They already say "each report" and change only if they contradict the new text.

## Acceptance criteria

1. make check stays green.
2. docs: `docs/operator-guide.md`, "A stall by a red check": the bullet on reports keeps these statements:
   - reports run after all checks are green;
   - they never hold a move;
   - a failing report stops nothing.

   It no longer says that a failing report adds no line. Instead it says that every report that ran adds one line `` `<command>`: <last line of its output> `` to the agent's entry, passed or failed, and that the line has the same form either way, so only its last line shows whether the report passed. No sentence in `docs/operator-guide.md` says that a failing report adds no line to the entry.

## Demo

```bash
grep -n "Reports (the stage" docs/operator-guide.md
```
Expect: one line, the reports bullet of "A stall by a red check". It says that a report adds its line `` `<command>`: <last line of its output> `` whether it passed or failed, and that a failing report holds nothing and stops nothing.

```bash
grep -c "adds no line" docs/operator-guide.md
```
Expect: `0`.

## Log (append only)

1. 2026-10-14 human: created.
