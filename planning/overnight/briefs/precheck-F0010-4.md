# Brief: F0010 pre-check round 4, narrow re-audit and pre-check with v1's own roles (Phase 3/4)

## Goal

Decide, story by story, whether F0010's stories F0010-S0001 to F0010-S0016 now pass v1's roles. Play v1's intake exactly on each story, then predict whether the tester, coder, reviewer, documenter, demo stage or acceptor would stop it. Re-audit only what the last improve step changed, and every earlier predicted stop.

## Inputs (read these; nothing else unless a step needs a named source file)

- The last improve step's handling table: `C:\Dev\Projects\factory-rf\planning\overnight\audits\F0010-4-handling.md`, and the report it handled (named in it).
- The feature: `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0010-machine\` (FEATURE.md and drafts/).
- The form check: `factory-check-story` found nothing in these drafts (exit 0) in v1's container.
- v1's role files, verbatim, under `C:\Dev\Projects\factory\claude\skills\`: `factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo`, `role-acceptor`, `stage-feature` (each `<name>\SKILL.md`), and the agent files `C:\Dev\Projects\factory\claude\agents\*.md`.
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory\stages.yml`, `factory\TICKET.md`, `security\semgrep\`, `docs\project-guide.md`, `docs\decisions.md`.
- What earlier features built: `C:\Dev\Projects\factory-rf\src\factory\` and `tests\`; read the modules a story imports, extends or whose tests it could break.
- The human's answers: `C:\Dev\Projects\factory-rf\planning\questionnaires\01-working-answers.md` (section "Answers") and `C:\Dev\Projects\factory-v2\planning\decisions\008-v1-1-starts-fresh.md`.
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`, the conditions the stories cite.

## Check in particular

- Every row of the handling table: does the fix hold, and did it open a hole?
- The lessons of F0001 and F0002, each of which cost a round:
  - every behaviour the Assignment, the Interface or a FEATURE.md decision states has its own criterion;
  - every rule and every limit is tested on both sides, field types included (`CLAUDE.md`, Tests, last line);
  - a story that changes code or tests an earlier story built allows that change in its text;
  - criteria pass `mypy --strict`, ruff, semgrep (`factory-no-unsafe-yaml-load` matches any `yaml.load(...)`) and detect-secrets;
  - each Demo's `Expect:` is met exactly.
- Each Demo: run it against today's code in a temporary directory outside the repository with `uv run --project C:\Dev\Projects\factory-rf python ...` where it can run before the story is built, and say what the built code would print. Mind pytest's `-q` in `pyproject.toml` and `grep -c` exit codes.
- Order: no story needs a story with a higher id; every name a story imports from earlier features exists with that spelling and signature.
- Size: each story fits the coder's $4 with one resume and a 60-minute lease.
- This round is a fresh re-check against the built code: F0006 to F0009 were built since the last pre-check (`precheck\F0010-3.md`), and the stories were written against their drafts. Check every name, signature, module, handler, fixture and test file the F0010 stories use or change against `src\factory\` and `tests\` as they are now, in particular `factory.entry.wiring` (`build_handlers`, `handler_factory`, `production_environment`, `NOT_YET_HANDLED`, now empty), `factory.application.tick`, `factory.application.recovery`, `factory.domain.work_item.require_state`, the acceptance modules, and `tests/test_no_journal_reading.py`'s `ALLOWED` sets.
- Intake asked on most F0006 to F0009 stories for an Interface clause without its own criterion. Read every rule of each Interface clause by clause and name each clause without its own criterion, on both sides. Test data a story's tests build must be valid under the readers and validators already built (several stories lost a round to fixtures: a missing `## Journal`, an invalid claim, a folder git dropped, a constant mypy typed too wide).
- The human's answers of 2026-10-14 are final: decisions 28 (the named test changes, made by the tester), 29 (run files `0640`), 32 (`planning/v1-texts/` now exists: check it) and findings 22 (pin `hatchling`) and 52 (refuse a password in `FACTORY_REPOSITORY_URL`) as recommended; item B as today; decision 30 left open. Say where a story still says "pending the human's word" and give the replacement text.
- `C:\Dev\Projects\factory-rf\planning\lessons-for-the-skills.md`: say, with exact texts, how F0010-S0016 carries its general rows into the shipped agents as a part of their own after v1's verbatim texts, and whether any story ships a `template/CLAUDE.md` for Python projects; if none does, propose where its Python rows go (a criterion in the template story, or a new small story) with the exact text.
- `CLAUDE.md` gained rules on 2026-10-14 (helpers reused, the sides of a rule as rows of one parametrized test, make in the foreground): say where a story's text contradicts them.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0010-4.md`, with:

- `## Findings`: a table (story and criterion, finding, severity blocker/should fix/note, exact replacement text).
- `## Verdicts`: exactly one line per story, in id order: `F0010-S000M: pass` or `F0010-S000M: predicted refusal (<category>): <reason>`. A predicted refusal needs a concrete reason that intake, the tester, the coder (ruff, mypy, semgrep, write paths, "Not without asking"), the demo stage or the container would hit; a preference is a note.
- `## Feature`: the acceptor's scope check on `FEATURE.md`.

## Not

- No git commands. No file other than the output. Do not fix the stories.

## Reply

The `## Verdicts` lines, the count of blockers and should-fixes, and for each predicted refusal its exact replacement text in one line.

Model: opus.
