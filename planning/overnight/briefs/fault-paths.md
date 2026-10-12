# Brief: the table of v1's thirteen fault-injection paths (Phase 2, decision 007 question 3)

## Goal

Map each of v1's thirteen fault-injection paths (v1: hardening paths) either to a named injection test of v1.1 or to the v1.1 item that removed the mechanism the path exercised, as the content of WE1.2's story.

## Inputs (read these; nothing else)

- `C:\Dev\Projects\factory\docs\reference\16-evidence\README.md`: the book's chapter 16, its list of paths walked and its planner.
- `C:\Dev\Projects\factory-v2\planning\01-discovery\v1-16-17.md`: the extraction of chapters 16 and 17 (the limits L1 to L74).
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`: section 5 (the items, especially GH1 to GH5, WE1, WE2, ST1 to ST3) and section 7.2 (the kill points and what a crash or stall test must show).
- `C:\Dev\Projects\factory-v2\planning\v1.1\run-facts.md`, section "How run 4 was driven" (the twelve paths of v1's demo hardening mode).
- `C:\Dev\Projects\factory-v2\planning\decisions\006-v1-1-open-points.md` (points 15 and 16) and `007-overnight-defaults.md` (question 3).

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\fault-paths.md`, with:

- `## Summary` (at most ten lines).
- `## The thirteen paths`: a table, one row per path of the book's list, in the book's order: number; the path in the book's words (short); what it exercised in v1 (the mechanism); in v1.1 either "walked by `<test name>`" (a test name in `snake_case`, starting `test_`, saying the kill point and the expected recovery, against a real local bare git remote and the fake hosting client) with the kill point of section 7.2 and its class (crash or stall), or "mechanism removed by <item and condition id>" with one sentence why; and the source (chapter 16 section or limit number).
- `## Differences from the demo's twelve paths`: which path of the book's list the demo mode lacks or names otherwise, and why the counts differ, from the inputs only.
- `## Kill points without a path`: each kill point of section 7.2 that no path maps to, with the test name it still needs.
- `## Open questions`.
- `## Sources`.

## Rules

- Injection tests only: injection points in the wrappers raise or end the process at the named point. No real container kill, no second-instance test (006, points 15 and 16).
- Use the glossary's names (handover appendix): fault-injection run, recovery state, crash, stall, error, lease.
- Where the book counts thirteen and you find another number, say so; do not invent a path.

## Not

- No git commands. No file other than the output. Do not read v1's code.

## Reply

The Summary and the Open questions, nothing else.

Model: opus.
