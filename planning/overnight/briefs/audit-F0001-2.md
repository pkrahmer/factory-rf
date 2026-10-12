# Brief: audit feature F0001, round 2 (Phase 3)

## Goal

Find, adversarially, every defect in feature F0001's `FEATURE.md` and stories that would make v1 refuse a story, build the wrong thing, or miss a condition of the handover. You did not write them.

## Inputs (read these; nothing else)

- The feature folder: `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0001-boundaries\` (FEATURE.md and drafts/).
- `C:\Dev\Projects\factory-rf\planning\overnight\skeleton.md`, `interfaces.md`, `traceability.md` (if present), and the latest `cross-check-*.md` (if present).
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`, sections 3 to 8 and the appendix.
- `C:\Dev\Projects\factory-v2\planning\decisions\001-truth-on-the-remote.md` to `007-overnight-defaults.md`.
- `C:\Dev\Projects\factory-v2\planning\v1.1\run-facts.md`, sections "Writing features and stories" and "What makes v1 refuse, ask or send back".
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `factory\stages.yml`, `factory\TICKET.md`.
- `C:\Dev\Projects\factory-rf\planning\overnight\audits\F0001-1.md`, `audits\F0001-1-handling.md` and `precheck\F0001-1.md`: round 1 and how it was handled.
- `C:\Dev\Projects\factory-rf\planning\overnight\skeleton-answers.md` (binding answers, including the corrections at 01:00).

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\audits\F0001-2.md`, with `## Summary` (at most ten lines, with the count of blockers, should-fixes and notes), `## Findings` (a table: number, story and section or criterion, finding, severity, what would fix it), `## Sources`.

## Look for

- Missing: a condition of the handover the feature carries without a criterion; a kept thing without a story; a rule without its failing-side criterion; a limit without its number.
- Invented: behaviour neither v1's book (as the handover and run-facts describe it) nor the handover gives.
- Contradiction: with a decision 001 to 007, with the interface sheet, with another story, with `CLAUDE.md`'s architecture or layers.
- Ambiguity: a criterion two testers would test differently; an Interface two coders would implement differently and both pass.
- Weaker than its condition: a criterion that would pass while the handover's condition fails.
- Too large: more than 26 criteria, or more than the coder's $4 budget and 60-minute lease plausibly allow.
- Order: a story that needs a story with a higher id.
- Untestable in v1's container: Docker, root, a second OS user, network or real GitHub; a Demo that cannot run there or an `Expect:` the correct code cannot meet.
- Form: anything `factory-check-story` or intake would refuse (sections, numbering, the two closing criteria, `Expect:` lines, headings inside fences, front matter, clock times).
- Names: any name not the glossary's or the interface sheet's.
- Write paths and "Not without asking": a needed new dependency, a write outside `src/*`, `image/*`, `template/*`, `claude/*`, `tests/*`, a write to a file named `FEATURE.md`.

Severity: **blocker** (v1 would refuse or build the wrong thing, or a condition is lost), **should fix** (likely to cost a round or an answer), **note**.

## This round is narrow

Audit only: (a) every row of `audits\F0001-1-handling.md`, whether the fix holds and whether it opened a new hole; (b) every criterion and Interface rule the improver changed or added (the handling table lists them, with the old-to-new story-number map); (c) the findings of `cross-check-1.md` that name F0001 (findings 3, 4, 12, 13) as far as F0001 must act; (d) S0009's argument list, where the main session restored `--permission-prompts none`. Do not re-audit unchanged text.

## Not

- No git commands. No file other than the output. Do not fix anything.

## Reply

The Summary only.

Model: opus.
