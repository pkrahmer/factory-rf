# Brief: F0001 round 3, narrow re-audit and pre-check in one (Phase 3/4)

## Goal

Decide, story by story, whether F0001's stories S0002 to S0014 now pass v1's roles, looking only at what round 2 changed and at what rounds 1 and 2 predicted would stop them.

## Inputs (read these; nothing else)

- Round 2: `C:\Dev\Projects\factory-rf\planning\overnight\audits\F0001-2.md`, `audits\F0001-2-handling.md`, `precheck\F0001-2.md`.
- The stories: `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0001-boundaries\` (FEATURE.md and drafts; S0001 has started and is out of scope).
- `C:\Dev\Projects\factory-rf\planning\overnight\skeleton-answers.md`, sections "Answers for F0001's round 1" and "Answers for F0001's round 2".
- v1's role files `C:\Dev\Projects\factory\claude\skills\stage-intake\SKILL.md`, `role-tester\SKILL.md`, `role-coder\SKILL.md`, `stage-demo\SKILL.md`.
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml` (ruff `max-args = 5`, B008, D rules), `Makefile`, `factory\stages.yml`.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0001-3.md`, with:

- `## Findings`: a table (story and criterion, finding, severity blocker/should fix/note). Look only at: every row of the round-2 handling table (does the fix hold, did it open a hole); every criterion, rule and Demo round 2 changed; every predicted refusal of `precheck\F0001-2.md` (is it gone).
- `## Verdicts`: exactly one line per story S0002 to S0014: `F0001-S000M: pass` or `F0001-S000M: predicted refusal (<category>): <reason>`. A predicted refusal needs a concrete reason that intake, the tester, the coder (ruff, mypy, write paths, "Not without asking"), the demo stage or the container would hit; a mere preference is a note, not a refusal.

## Not

- No git commands. No file other than the output. Do not fix the stories.

## Reply

The `## Verdicts` lines and the count of blockers, nothing else.

Model: opus.
