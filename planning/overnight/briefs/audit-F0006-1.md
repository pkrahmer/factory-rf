# Brief: audit feature F0006, round 1 (Phase 3)

## Goal

Find, adversarially, every defect in feature F0006's `FEATURE.md` and stories that would make v1 refuse a story, build the wrong thing, or miss a condition of the handover. You did not write them.

## Inputs (read these; nothing else)

- The feature folder: `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0006-reading-the-remote\` (FEATURE.md and drafts/).
- `C:\Dev\Projects\factory-rf\planning\overnight\skeleton.md`, `interfaces.md`, `traceability.md` (if present), and the latest `cross-check-*.md` (if present).
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`, sections 3 to 8 and the appendix.
- `C:\Dev\Projects\factory-v2\planning\decisions\001-truth-on-the-remote.md` to `007-overnight-defaults.md`.
- `C:\Dev\Projects\factory-v2\planning\v1.1\run-facts.md`, sections "Writing features and stories" and "What makes v1 refuse, ask or send back".
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `factory\stages.yml`, `factory\TICKET.md`.
- `C:\Dev\Projects\factory-rf\planning\overnight\drafter-reports.md`, section F0006 (the drafter's own open questions).
- `C:\Dev\Projects\factory-rf\planning\overnight\skeleton-answers.md`, and the human's answers that win over it: `C:\Dev\Projects\factory-rf\planning\questionnaires\01-working-answers.md`, section "Answers" (2026-10-13), and `C:\Dev\Projects\factory-v2\planning\decisions\008-v1-1-starts-fresh.md` (no recognition of v1 work items: v1.1 starts fresh). The interface sheet's last section, "Changes after the human's questionnaire 1 and F0002's rounds", wins over its body.
- What earlier features built or will build, and F0006 builds on: `C:\Dev\Projects\factory-rf\src\factory\` (read the modules a story imports or extends), `tests\conftest.py`, and every earlier feature's folder under `C:\Dev\Projects\factory-rf\factory\features\` (its `FEATURE.md`, `ACCEPTANCE.md` where present, and its stories in `done\` or still in `drafts\`; their names and story numbers are binding, with the renumberings the interface sheet's last changes record). A story that redefines, duplicates or contradicts something already built is a blocker; a story that needs a name the built code spells differently must use the built spelling.
- `C:\Dev\Projects\factory-rf\docs\project-guide.md` and `docs\decisions.md`.
- Lessons from building F0001 and F0002, each of which cost a round there:
  - a behaviour stated in the Assignment, the Interface or a FEATURE.md decision without its own criterion;
  - a rule or a limit tested on one side only (`CLAUDE.md`, Tests, last line: field types such as `NonNegativeInt` included);
  - a Demo whose `Expect:` the real output does not meet exactly (pytest's own `-q` from `pyproject.toml`, `grep -c` exit codes);
  - a test change to a test another story wrote that the story does not allow;
  - a criterion `mypy --strict`, semgrep or detect-secrets would refuse in the test;
  - a model the Interface calls frozen or closed to unknown fields, or a field typed `PositiveInt`, `NonNegativeInt`, `CommitId` or a `Literal`, without a criterion for the refused assignment, the unknown key and both sides of each type's limit (intake refuses it; seen five times in F0005);
  - a test that relies on a fixture story with form findings, or on a role that may not write the work item, where an earlier feature's undo or form check changes the outcome.

  Interfaces are abstract base classes that implementations inherit (`CLAUDE.md`, Architecture). R13 is kept literally: python-frontmatter for front matter (with a ruamel.yaml handler), ruamel.yaml for YAML.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\audits\F0006-1.md`, with `## Summary` (at most ten lines, with the count of blockers, should-fixes and notes), `## Findings` (a table: number, story and section or criterion, finding, severity, what would fix it), `## Sources`.

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

Also list, as a separate section `## Questionnaire answers to apply`, every place in F0006's FEATURE.md and drafts that the human's answers of questionnaire 1 or decision 008 change (for example Q3, no run record; Q15, no recognition of v1 work items; Q17, Q20, Q22, Q23 where they touch F0006), and every place where a draft uses a name, signature or rule that F0001 or F0002 built differently, each with the exact edit.

## Not

- No git commands. No file other than the output. Do not fix anything.

## Reply

The Summary only.

Model: opus.
