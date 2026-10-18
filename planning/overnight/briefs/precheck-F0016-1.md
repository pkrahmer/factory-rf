# Brief: pre-check F0016 round 1 with v1's own roles (all three stories)

## Goal

For each draft of `F0016-the-shakedown-findings`, play v1's intake exactly, then predict whether the tester, coder, reviewer, documenter, demo stage or acceptor would stop it, and give it one verdict line. The drafts were written by the session's drafting agent from the shakedown run's findings 1 to 3 (the human chose them on 2026-10-18); they have not been checked against v1's roles. Also judge the feature's "human's changes" and the demo fixes in `C:/Dev/Projects/factory-rf/planning/overnight/demo-fixes-F0016.md` (exact lines, needed before which story, and whether one is missing).

F0014's acceptance found that six of its nine human answers fixed a contradiction in the drafted text (a test the domain refuses, a demo naming a module nobody made, a `noqa` a structural test forbids, an equality against a post that always carries the marker). So: for every test a draft names or describes, check it against the built code and the tests that pin it (structural tests such as `tests/test_process_search.py`, `tests/test_claude_files.py`, `tests/test_compose*.py`, fixture order, `mypy --strict`, ruff); and run every Demo command against today's code where it can run before the story, and check that every file it names exists or is made by the story.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0016-the-shakedown-findings/FEATURE.md` and the three drafts under `drafts/`.
- The findings and the run they came from: `C:/Dev/Projects/factory-rf/docs/runs/2026-10-12-overnight/night-log.md`, the rows of 2026-10-18 from 07:45 on and the section "2026-10-18, the shakedown run (plan step 4): result".
- v1's role files, verbatim, under `C:/Dev/Projects/factory/claude/skills/` (`factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo`, each `<name>/SKILL.md`) and `C:/Dev/Projects/factory/claude/agents/*.md`.
- `C:/Dev/Projects/factory-rf/CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory/stages.yml` (the write paths per stage), `factory/TICKET.md`, `factory/FEATURE.md`, `planning/lessons-for-the-skills.md`.
- The code, files and tests each draft touches: `template/CLAUDE.md`, `claude/agents/*.md`, `src/factory/application/` (the stage finisher, the hand-over handler, the description writers, the prompts), the test modules each draft extends or changes (above all `tests/test_stop_table.py`, `tests/test_stage_run_acceptance.py`, the tests holding `TEMPLATE_RULES_LINES`, `LESSONS`, `ROLE_AND_STAGE_ANCHORS`), `tests/test_demos.py`, and the documents each docs criterion names.

## Check in particular

- Every behaviour the Assignment, the Interface or a FEATURE decision states has its own criterion, on both sides; the sides of one rule are rows of one parametrized test; a story that changes tests another story wrote names them exactly, and FEATURE.md gives the leave as a decision (write its exact text if it is missing).
- Test data and helpers valid under the built code (`CLAUDE.md` Tests); criteria pass `mypy --strict`, ruff, semgrep and detect-secrets; each Demo's `Expect:` met exactly.
- S0001: the standing leave's exact text in `template/CLAUDE.md` and the agents' lessons, against the tests that pin them (`TEMPLATE_RULES_LINES`, `LESSONS` and any other anchor); whether the leave is narrow enough that an agent cannot read it as leave to change what an earlier test checks.
- S0002: the reviewer's item 6 against the reviewer's checklist as shipped and the anchors that pin it (`ROLE_AND_STAGE_ANCHORS`); whether "the files `main` already holds" is something the reviewer can list with the tools and commands it has; the acceptance reviewer's part.
- S0003: the cause the draft gives for finding 3, against `StageFinisher.finish`, `HandOverHandler` and the tick as built; whether writing the description before the push breaks a kill point, a fault path or the error cap (the draft moves one `fail_next` line in `tests/test_stop_table.py`: is that the only test it turns red?); whether the description written then holds what the hand-over writes.
- The demo fixes: each added criterion against the demo's built code as the run left it (the clone at `C:/Users/pasca/AppData/Local/Temp/claude/C--Dev-Projects/1df7a32a-7f34-4bfa-b4b6-795c95bba93b/scratchpad/demo-todo`, read only) and against `tests/test_demos.py` in factory-rf, which reads the demo's stories.
- Write paths: each file a stage must write is inside that stage's write paths in `factory/stages.yml`.
- Each story fits the tester's $2 and the coder's $4 with one resume, inside a 60-minute lease.

## Output

One file per draft, `F0016-S0001-1.md`, `F0016-S0002-1.md`, `F0016-S0003-1.md`, and `demo-fixes-F0016-1.md` for the demo fixes, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`. Each holds the intake outcome exactly as v1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands. No network calls. No file other than your outputs. Do not change the drafts or FEATURE.md. Do not start sub-agents. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and leave nothing behind.

## Reply

Per draft its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers; anything wrong with the human's changes.
