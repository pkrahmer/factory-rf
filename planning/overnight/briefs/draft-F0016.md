# Brief: draft F0016, the shakedown run's findings, for v1 to build

## Goal

Write the feature `F0016-the-shakedown-findings` and its stories so that v1 can fix, before the handover (plan step 5), the findings of v1.1's shakedown run of 2026-10-18 that the human chose: findings 1, 2 and 3 below. Finding 4 is the human's change to `demo/`, drafted separately (see the end).

The run: v1.1 built the todo demo (`demo/todo-service/`, eight stories, three acceptances) on `pkrahmer/factory-demo-todo`, instance `shakedown` under Docker Desktop, image built from factory-rf `0f617cde`; all accepted, no stall, 82 runs, $17.88.

## Inputs (read these first)

- The night log's section "2026-10-18, the shakedown run (plan step 4): result" and the rows of 2026-10-18 from 07:45 on: `C:/Dev/Projects/factory-rf/docs/runs/2026-10-12-overnight/night-log.md`.
- The shipped agents and the template: `C:/Dev/Projects/factory-rf/claude/agents/*.md` (above all `reviewer.md`, `tester.md`, `coder.md`, `acceptance-reviewer.md`), `template/CLAUDE.md` (its "Not without asking" section), `template/factory/pipeline.yml`, and the demo project's own copy `demo/todo-service/project/CLAUDE.md` (compare it with the template's).
- The tests that pin the shipped agents and the template (search `tests/` for `claude/agents`, `template/CLAUDE.md`, `reviewer.md`; e.g. `tests/test_claude_files.py` and any document check), so that a new line does not turn one red and a new rule gets its own test where the others have one.
- For finding 3: `src/factory/application/handlers/hand_over.py`, `src/factory/application/acceptance.py`, how a pull request's description is written (search for the description or body writer in `src/factory/`), the order in which a stage's end, the hand-over to `approval`, the push and the description update happen, and the tests that pin that order.
- The forms and rules v1 applies: `factory/TICKET.md`, `factory/FEATURE.md`, `factory/stages.yml` (write paths: the coder writes `src/*`, `image/*`, `template/*`, `claude/*`; the tester `tests/*`; the documenter `README.md` and `docs/*`; check whether `demo/*` is in any), v1's role files under `C:/Dev/Projects/factory/claude/skills/`, `CLAUDE.md`, `planning/lessons-for-the-skills.md`.
- How a feature passes: `factory/features/F0015-the-tiny-storys-findings/` (FEATURE.md, its stories in `done/`, its acceptance) and `F0014`'s ACCEPTANCE.md: most human answers there fixed a contradiction in the drafted text. Check every drafted test and Demo against the built code before you finish.

## The content (the session's proposals, chosen by the human on 2026-10-18)

1. **A standing leave to move a shared test helper** (findings 1 and 2). In the template's `CLAUDE.md` (and so in every project the factory sets up): a helper, constant or fixture that a new test would copy from another story's test module may be moved to one shared place under `tests/` (a module at its root or `tests/conftest.py`), and the earlier tests that held it changed to use it, without asking, as long as every earlier test keeps its name and checks the same thing; any other change to a test another story wrote still needs the human's leave. Say exactly how the "Not without asking" line changes. The shipped tester and coder agents may need a line too (who makes the move, when the coder hands it to the tester); keep them consistent with the template.
2. **The reviewer names every earlier test it sees changed** (finding 1). The shipped reviewer's checklist gains an item: list each changed test file that another story created, and for each the leave it was changed under (the standing leave of 1, or the human's answer by journal entry); a change outside both is a finding. Decide whether the acceptance reviewer needs the same check over the whole feature, and recommend one.
3. **An acceptance's report is in its pull request before the hand-over** (finding 3). Seen on demo #12: the board showed the acceptance at `approval` about 25 s before its pull request's description held the report; it first showed only the journal. Find in the code why (the order of the push, the hand-over and the description update, or the reading of the report from a commit not yet pushed), say whether stories have the same gap, and give the fix and its test: a human who opens the pull request the moment it reaches `approval` sees the full description.

## Rules for the split

- One story is one coder's work within $4 and a 60-minute lease. Documentation-only items may be one story whose coder changes nothing and whose docs criterion carries the text.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a Demo's `Expect:` met exactly by the built code; every file a Demo or a test names exists or is made by the story.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/stages.yml`, `security/*`, and `demo/*` if no stage writes it) is "The human's change before S000N" in FEATURE.md, with exact lines.
- A story that changes tests another story wrote names them exactly, and FEATURE.md gives the leave as a decision.
- No word of `GLOSSARY_FORBIDDEN` outside a `## Replaced from v1` section in the documents. No secret-like key with a value in a story's text, and no 32-character hex value.

## Finding 4, the human's change to `demo/` (separate output)

Read the demo's eight stories under `demo/todo-service/features/` and the six questions the run raised about them (night log, 2026-10-18 08:16, 08:33, 08:36, 08:48 and the result section, item 4; the answers are decisions 12 to 17 in the run's `factory/features/F0001-todo-service/feature.md` on the demo repository, quoted in the night log). Write `C:/Dev/Projects/factory-rf/planning/overnight/demo-fixes-F0016.md`: for each story, the exact criterion text to add or change so that both sides of every rule its Interface states have a criterion (the `null` PATCH rows, the SQLite storage format read back, `from_path` with `str` and `Path`, the no-inheritance row per repository, and any other gap of the same kind you find), and the decisions to add to the features' `feature.md`. Also the line for the demo project's `CLAUDE.md` matching item 1. Keep each story's numbering of the two closing criteria (`make check`, docs) last.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0016-the-shakedown-findings/FEATURE.md` (Goal, Scope, Out of scope, Stories in build order, the human's changes, Decisions taken for the human with their source), the stories under its `drafts/` as `F0016-S000N-<slug>.md`, and `planning/overnight/demo-fixes-F0016.md`.

## Not

No git commands. No network calls. No file outside `planning/overnight/stories/F0016-the-shakedown-findings/` and `planning/overnight/demo-fixes-F0016.md`. Do not start sub-agents. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and leave nothing behind.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human, what you found for finding 3 (cause and whether stories share it), and the demo fixes in one line per story.
