# Brief: traceability and the cross-feature check, round 1 (Phase 2/3)

## Goal

Check the whole set of features and stories as one, and write the traceability from the handover's conditions, kept things and rules to the stories.

## Inputs (read these; nothing else)

- Every feature folder under `C:\Dev\Projects\factory-rf\planning\overnight\stories\` (each `FEATURE.md` and `drafts\*.md`).
- `C:\Dev\Projects\factory-rf\planning\overnight\skeleton.md`, `skeleton-answers.md`, `interfaces.md`, `fault-paths.md`.
- `C:\Dev\Projects\factory-v2\planning\v1.1\overnight-run-plan.md`, section 5 (the dependency table, "Traceability", "Cross-feature check").
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`, sections 3 to 5 and 8, and the appendix.
- `C:\Dev\Projectsactory-rf\planning\overnight\drafter-reports.md`: the drafters' replies and open questions; check each cross-feature question and report it as a finding where it holds.

## Output

Two files:

1. `C:\Dev\Projects\factory-rf\planning\overnight\traceability.md`:
   - `## Conditions`: one row per acceptance condition ST1.1 to WE6.5: the story id and criterion numbers, or "morning observation" (with the static test's story), or "not tonight" with the reason.
   - `## Kept things and rules`: one row per kept thing 1 to 21 of handover section 3 and per rule R1 to R38: the stories that keep or obey it, or "configuration in the seed".
   - `## Reverse index`: story → the conditions it covers.
2. `C:\Dev\Projects\factory-rf\planning\overnight\cross-check-1.md`: `## Summary` (at most ten lines, with counts by severity), `## Findings` (a table: number, feature and story, finding, severity blocker/should fix/note, the feature whose improver must act), `## Sources`. It checks that:
   - ids are unique and contiguous per feature, file stems match folders, and slugs start with a letter;
   - no story needs a story with a higher id, and the plan's dependency table holds per condition (skeleton-answers, answer 12);
   - every name used across features is in the interface sheet (list each one that is not);
   - every condition is traced exactly once, to a story that builds it;
   - no two stories build the same thing;
   - each `FEATURE.md`'s Stories list matches its drafts;
   - every story's last criterion starts with `docs:` and names the documents it touches (WE6.3), and the second-to-last is `make check stays green.`

## Not

- No git commands. No file other than the two outputs. Do not fix stories.

## Reply

The cross-check's Summary and the count of conditions traced, observation-only and not tonight.

Model: opus.
