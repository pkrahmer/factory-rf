# Brief: pre-check feature F0001 with v1's own roles, round 1 (Phase 4)

## Goal

Play v1's intake exactly on each story of feature F0001, then predict whether the tester, coder, reviewer, documenter, demo stage and acceptor would stop it, and give each story one verdict line.

## Inputs (read these; nothing else)

- v1's role files, verbatim, under `C:\Dev\Projects\factory\claude\skills\`: `factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo`, `role-acceptor`, `stage-feature` (each `<name>\SKILL.md`), and the agent files `C:\Dev\Projects\factory\claude\agents\*.md` (budgets, tools).
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory\stages.yml` (write paths), `factory\TICKET.md`, and `docs\*.md`.
- The feature: `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0001-boundaries\` (FEATURE.md and drafts/).
- The form check's output for these drafts: factory-check-story reported no findings for any draft of this feature (exit 0), run in v1's container on the drafts as they are now.
- `C:\Dev\Projects\factory-rf\planning\overnight\interfaces.md` (for what earlier features provide).

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0001-1.md` with:

- For each story, the intake outcome exactly as v1's intake would end: `question` with numbered questions, or `accepted` with one line per check of `stage-intake` steps 2 to 4.
- Then, per story, the predicted later stops by role, each with its reason or "none".
- `## Verdicts`: exactly one line per story, in id order: `F0001-S000M: pass` or `F0001-S000M: predicted refusal (<category>): <reason>`. Categories: form, intake, tester, coder, reviewer, documenter, demo, acceptor, container, size, guard.
- `## Feature`: the acceptor's scope check on `FEATURE.md`: every Scope line has a story and every story is within Scope.

## Categories, for the verdict

- form: any finding of the form check. intake: intake would end with `question`. tester: a criterion the tester must interpret, or an Interface too vague to test. coder: a "Not without asking" item (new dependency, new top-level package, change to `factory/`), a write outside the coder's write paths, a test contradicting the Interface, or a tool the container lacks. reviewer: a rule whose failing side has no criterion. documenter: the docs criterion names a file outside `README.md` and `docs/*`, or a public interface lacks the docstring `CLAUDE.md` asks for. demo: a command that cannot run in the container (Linux, no network, nothing listening) or an `Expect:` the correct implementation cannot meet. acceptor: a Scope line without a story or a story outside Scope. container: a criterion needs Docker, root, a second OS user, the network or real GitHub. size: too large for the coder's $4 with one resume or a 60-minute lease. guard: an agent would write a file named `FEATURE.md`.

## Not

- No git commands. No file other than the output. Do not fix the stories.

## Reply

The `## Verdicts` lines and the `## Feature` result, nothing else.

Model: opus (sonnet would play intake in v1; you play every role).
