# Brief: pre-check F0014 round 1 with v1's own roles (all eight stories)

## Goal

For each draft of `F0014-the-first-start-findings` in your range, play v1's intake exactly, then predict whether the tester, coder, reviewer, documenter, demo stage or acceptor would stop it, and give it one verdict line. The drafts were written by the session's drafting agent from the plan; they have not been checked against v1's roles or the real code. Your range is all eight drafts. Also judge the feature against the first start's results (`planning/overnight/first-start-checklist.md`, "Results", faults 1 to 6) and say for S0001 and S0006 together whether, after them, nothing an agent writes in the checkout (hooks, `.git/config`, `.git/info/attributes`, a renamed `.git`, `.gitattributes` in the work tree) can make the factory's git run a command as `factory`. For S0007, replace FEATURE decision 27's catch-all leave with the exact list of earlier tests and lines that change (find them by reading every test that builds or compares a `JournalRecord` or a written front matter), so the human confirms a list, not a rule.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0014-the-first-start-findings\FEATURE.md` (its decisions, and the human's changes, if any; each story is checked as if F0012 and the human's changes after its acceptance are committed) and the drafts in your range under `drafts\`. Read the other drafts' titles and Interfaces only where a story depends on them.
- The plan they come from: `C:\Dev\Projects\factory-rf\planning\overnight\restructure-after-f0011.md`, the section "The order of the work after F0011" and the sections it points to.
- v1's role files, verbatim, under `C:\Dev\Projects\factory\claude\skills\` (`factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo`, each `<name>\SKILL.md`) and `C:\Dev\Projects\factory\claude\agents\*.md`.
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory\stages.yml` (the write paths per stage), `factory\TICKET.md`, `planning\lessons-for-the-skills.md`, `security\semgrep\`.
- The code and tests each story touches under `C:\Dev\Projects\factory-rf\src\factory\` and `tests\`: read every module a story imports, extends or whose tests it changes.

## Check in particular

- The lessons of F0001 to F0011: every behaviour the Assignment, the Interface or a FEATURE.md decision states has its own criterion, on both sides; every Interface clause read clause by clause; every limit and closed model tested on both sides, the sides of one rule as rows of one parametrized test; a story that changes tests another story wrote names them and its FEATURE decision gives the leave; test data and helpers valid under the built code (`CLAUDE.md` Tests); shared helpers reused, no second copy; criteria pass `mypy --strict`, ruff, semgrep and detect-secrets; each Demo's `Expect:` met exactly.
- Write paths: each file a story's coder, tester or documenter must write is inside that stage's write paths in `factory\stages.yml`; anything outside is a human's change that must come before the story.
- Any human change the stories need: is it complete and correct for what the stories need (exact lines, a target that exists before a story or check calls it)? A change that would turn `make check` red, or that a stage would run before it exists, is a stop.
- Each story fits the tester's $2 and the coder's $4 with one resume, inside a 60-minute lease.
- Run each Demo against today's code in a temporary directory outside the repository with `uv run --project C:\Dev\Projects\factory-rf python ...` where it can run before the story is built, and say what it prints.
- Any decision the drafting agent took for the human that contradicts the plan or the human's answers: name it, with the plan's wording.

## Output

One file per story in your range, `F0014-S00NN-1.md`, in `C:\Dev\Projects\factory-rf\planning\overnight\precheck\`. Each holds the intake outcome exactly as v1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands. No file other than your outputs. Do not change the drafts or FEATURE.md.

## Reply

Per story its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers; any contradiction with the plan.

Model: opus.
