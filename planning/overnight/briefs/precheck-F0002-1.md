# Brief: F0002 round 1, narrow re-audit and pre-check with v1's own roles (Phase 3/4)

## Goal

Decide, story by story, whether F0002's stories S0001 to S0008 now pass v1's roles. Play v1's intake exactly on each story, then predict whether the tester, coder, reviewer, documenter, demo stage or acceptor would stop it. Re-audit only what the improve step changed.

## Inputs (read these; nothing else unless a step needs a named source file)

- The audit and its handling: `C:\Dev\Projects\factory-rf\planning\overnight\audits\F0002-1.md` and `audits\F0002-1-handling.md`.
- The feature: `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0002-work-item-data\` (FEATURE.md and drafts/).
- The form check: `factory-check-story` found nothing in the eight drafts (exit 0) in v1's container.
- v1's role files, verbatim, under `C:\Dev\Projects\factory\claude\skills\`: `factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo`, `role-acceptor`, `stage-feature` (each `<name>\SKILL.md`), and the agent files `C:\Dev\Projects\factory\claude\agents\*.md`.
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory\stages.yml`, `factory\TICKET.md`, `docs\project-guide.md`, `docs\decisions.md`.
- What F0001 built and F0002 builds on: `C:\Dev\Projects\factory-rf\src\factory\` and `tests\conftest.py`; read the modules a story imports or extends.
- The human's answers: `C:\Dev\Projects\factory-rf\planning\questionnaires\01-working-answers.md` (section "Answers") and `C:\Dev\Projects\factory-v2\planning\decisions\008-v1-1-starts-fresh.md`.
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`, R13 and the conditions F0002's stories cite.

## Check in particular

- The main session's decision, to be applied in the next improve step: the work item adapter keeps R13 as written. python-frontmatter splits the file, with a handler that reads and writes the YAML with ruamel.yaml. The splitting rules the stories state (blank lines before `---`, other boundary lines) then follow python-frontmatter's behaviour. Check python-frontmatter 1.3.0 in the project's `.venv` for how a custom handler is given (`frontmatter.loads(text, handler=...)`, `frontmatter.dumps(post, handler=...)`) and what exactly it accepts as a boundary, so the next improve step can write exact criteria. Write the replacement text for S0003's Interface rule, decision 4 and every criterion that names the splitting.
- Every row of the handling table: does the fix hold, and did it open a hole?
- The lessons of F0001: every behaviour the Assignment, the Interface or a FEATURE.md decision states has its own criterion, on both sides of each rule; a test change to a test another story wrote is allowed by the story; criteria pass `mypy --strict` and detect-secrets (`CLAUDE.md`, Tests).
- Each Demo: run it against today's code in a temporary directory outside the repository with `uv run --project C:\Dev\Projects\factory-rf python ...` where it can run before the story is built, and say what the built code would print. The `Expect:` line must be met exactly; mind pytest's `-q` in `pyproject.toml` and `grep -c` exit codes.
- Order: no story needs a story with a higher id; every name a story imports from F0001 exists with that name and signature.
- Size: each story fits the coder's $4 with one resume and a 60-minute lease.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0002-1.md` with:

- `## Findings`: a table (story and criterion, finding, severity blocker/should fix/note, exact replacement text).
- `## R13`: the replacement texts for the python-frontmatter decision.
- `## Verdicts`: exactly one line per story S0001 to S0008: `F0002-S000M: pass` or `F0002-S000M: predicted refusal (<category>): <reason>`. A predicted refusal needs a concrete reason that intake, the tester, the coder (ruff, mypy, write paths, "Not without asking"), the demo stage or the container would hit; a preference is a note.
- `## Feature`: the acceptor's scope check on `FEATURE.md`.

## Not

- No git commands. No file other than the output. Do not fix the stories.

## Reply

The `## Verdicts` lines, the count of blockers and should-fixes, and one line on the R13 texts.

Model: opus.
