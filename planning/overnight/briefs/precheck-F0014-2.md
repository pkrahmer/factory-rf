# Brief: pre-check F0014 round 2 with v1's own roles (the acceptance's three drafts)

## Goal

F0014's acceptance (`factory/features/F0014-the-first-start-findings/ACCEPTANCE.md`, merged) proposed three drafts: S0011 (the nested-repository walk's untested sides), S0012 (the stamp of an acceptance merged before approval) and S0013 (documentation only). For each, play v1's intake exactly, then predict whether the tester, coder, reviewer, documenter, demo stage or acceptor would stop it, and give it one verdict line. The acceptor wrote them; they have not been checked against v1's roles.

The acceptance found that six of the feature's nine human answers fixed a contradiction in the drafted text (a test that the domain refuses, a demo naming a module nobody made, a `noqa` a structural test forbids, an equality against a post that always carries the marker). So in this round, also: for every test a draft names or describes, check it against the built code and the tests that pin it (validators, structural tests such as `tests/test_process_search.py`, the marker on every post, fixture order, `mypy --strict`); and for every Demo command, run it against today's code where it can run before the story, and check that every file it names exists or is created by the story.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:/Dev/Projects/factory-rf/factory/features/F0014-the-first-start-findings/FEATURE.md` (its decisions), `ACCEPTANCE.md`, and the three drafts under `drafts/`. The ten built stories are under `done/`; read one only where a draft depends on it.
- v1's role files, verbatim, under `C:/Dev/Projects/factory/claude/skills/` (`factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo`, each `<name>/SKILL.md`) and `C:/Dev/Projects/factory/claude/agents/*.md`.
- `C:/Dev/Projects/factory-rf/CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory/stages.yml` (the write paths per stage), `factory/TICKET.md`, `planning/lessons-for-the-skills.md`.
- The code and tests each draft touches under `C:/Dev/Projects/factory-rf/src/factory/` and `tests/`: read every module a draft imports, extends or whose tests it changes.

## Check in particular

- Every behaviour the Assignment, the Interface or a FEATURE decision states has its own criterion, on both sides; the sides of one rule are rows of one parametrized test; a story that changes tests another story wrote names them exactly, and needs a new FEATURE decision giving the leave (write that decision's exact text).
- Test data and helpers valid under the built code (`CLAUDE.md` Tests); criteria pass `mypy --strict`, ruff, semgrep and detect-secrets; each Demo's `Expect:` met exactly.
- S0011: a symbolic link to a folder holding a `.git`, and a link to `.`, in a real checkout under `tmp_path`; that the walk then removes nothing through the link and leaves the checkout's own `.git`; a `.git` inside a `.git`; two or more paths in the stall detail, the probe detail and the preparer's log line. Say whether a symbolic link to a nested repository should itself count as a nested repository (FEATURE decision 31); recommend one answer.
- S0013: every sentence it changes, against the code as built (the nine entries, the login shell's command line, the token file and the manual fallback, the README status after the first start of 2026-10-17).
- Write paths: each file a stage must write is inside that stage's write paths in `factory/stages.yml`.
- Each story fits the tester's $2 and the coder's $4 with one resume, inside a 60-minute lease.

## Output

One file per draft, `F0014-S0011-1.md`, `F0014-S0012-1.md`, `F0014-S0013-1.md`, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`. Each holds the intake outcome exactly as v1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands. No file other than your outputs. Do not change the drafts or FEATURE.md. Do not start sub-agents. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and leave nothing behind.

## Reply

Per draft its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers.
