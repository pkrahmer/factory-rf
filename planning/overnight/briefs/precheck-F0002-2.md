# Brief: F0002 round 3, narrow re-audit and pre-check (Phase 3/4)

## Goal

Decide, story by story, whether F0002's stories S0001 to S0008 now pass v1's roles, looking only at what round 2 changed and at what round 1's pre-check predicted would stop them. This is the last round before the stories are committed and built.

## Inputs (read these; nothing else unless a step needs a named source file)

- Round 2: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0002-1.md` (the predicted stops and the `## R13` texts) and `audits\F0002-2-handling.md`.
- The stories: `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0002-work-item-data\` (FEATURE.md and drafts/).
- The form check: `factory-check-story` found nothing in the eight drafts after round 2 (exit 0) in v1's container.
- v1's role files `C:\Dev\Projects\factory\claude\skills\stage-intake\SKILL.md`, `role-tester\SKILL.md`, `role-coder\SKILL.md`, `role-reviewer\SKILL.md`, `stage-demo\SKILL.md`.
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory\stages.yml`, `security\semgrep\`.
- python-frontmatter 1.3.0 and ruamel.yaml in the project's `.venv`, and `src\factory\` for what F0001 built.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0002-2.md`, with:

- `## Findings`: a table (story and criterion, finding, severity blocker/should fix/note, exact replacement text). Look only at:
  - every row of the round-2 handling table: does the fix hold, and did it open a hole?
  - every criterion, rule and Demo that round 2 changed, especially S0003's python-frontmatter rules: check them with a probe against python-frontmatter 1.3.0 and ruamel.yaml;
  - every predicted refusal of `precheck\F0002-1.md`: is it gone?
- `## Verdicts`: exactly one line per story S0001 to S0008: `F0002-S000M: pass` or `F0002-S000M: predicted refusal (<category>): <reason>`. A predicted refusal needs a concrete reason that intake, the tester, the coder (ruff, mypy, semgrep, write paths, "Not without asking"), the demo stage or the container would hit. A preference is a note.

## Not

- No git commands. No file other than the output. Do not fix the stories.

## Reply

The `## Verdicts` lines, the count of blockers and should-fixes, and for each predicted refusal its exact replacement text.

Model: opus.
