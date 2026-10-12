# Brief: improve feature F0001 after the audit round 1 and the pre-check round 1 (Phase 3/4)

## Goal

Fix every finding of the reports below in feature F0001's files, or defer it with a reason, and record each in a handling table.

## Inputs (read these; nothing else unless a finding names it)

- The reports: `C:\Dev\Projects\factory-rf\planning\overnight\audits\F0001-1.md` and `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0001-1.md`; and the binding answers in `C:\Dev\Projects\factory-rf\planning\overnight\skeleton-answers.md`, section "Answers for F0001's round 1".
- The feature folder: `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0001-boundaries\`.
- `C:\Dev\Projects\factory-rf\planning\overnight\interfaces.md` and `skeleton.md`.
- `C:\Dev\Projects\factory-rf\planning\overnight\briefs\draft-template.md`: the format rules a story must keep (sections "The format v1 requires", "What makes a story pass v1", "From conditions to criteria").
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`, the sections a finding cites.

## Output

- The changed files in the feature folder (FEATURE.md, drafts/).
- `C:\Dev\Projects\factory-rf\planning\overnight\audits\F0001-1-handling.md`: a table, one row per finding: report and number, severity, "fixed" with the story and criterion numbers changed (old wording → new wording for every changed criterion), or "deferred" with the reason.

## Rules

- Keep every rule of the format: the two closing criteria, numbering 1 to n without gaps, `Expect:` after every Demo block, no headings in fences, the log line `1. 2026-10-12 human: created.`, no front matter.
- Never weaken a criterion below its handover condition to make a finding go away.
- A story that grows beyond 26 criteria is split into two stories with consecutive ids; renumber the later stories of the feature and update `FEATURE.md`'s Stories list.
- Names only from the interface sheet and the glossary. If a finding needs a change to the interface sheet, defer it with "needs interfaces.md: <what>".

## Not

- No git commands. No file outside the feature folder and the handling file.

## Reply

At most 15 lines: counts fixed and deferred, every criterion whose meaning changed (story and number), and every "needs interfaces.md" item.

Model: sonnet.
