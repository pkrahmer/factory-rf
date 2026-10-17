# Brief: draft F0012, the housekeeping feature, for v1 to build

## Goal

Write the feature `F0012-housekeeping` and its stories so that v1's pipeline can build step 1 of the plan's order: the small fixes after F0011. The human decided its content on 2026-10-17; this brief turns it into a FEATURE.md and story drafts in v1's forms, ready for a pre-check.

## Inputs (read these first)

- The content: `C:\Dev\Projects\factory-rf\planning\overnight\restructure-after-f0011.md`, the section "The order of the work after F0011", step 1 (items 1.1 to 1.10 and the parked drafts), and every section it points to (the `make check` time, duplicates and dead code, the DTOs' configuration, disk space, telemetry, the demo, the renaming's compose collision, the further findings, F0010's and F0011's acceptance notes). Steps 2 to 8 are not this feature.
- The forms and rules v1 applies: `C:\Dev\Projects\factory-rf\factory\TICKET.md`, `factory\FEATURE.md`, `factory\stages.yml`; v1's role files under `C:\Dev\Projects\factory\claude\skills\` (`factory-rules`, `stage-intake`, `role-tester`, `role-coder`, `role-reviewer`, `role-documenter`, `stage-demo`).
- How a feature and its stories look when they pass: `C:\Dev\Projects\factory-rf\factory\features\F0011-proof-and-documents\FEATURE.md` and two of its stories in `done\` (S0004 and S0006).
- The project's rules: `C:\Dev\Projects\factory-rf\CLAUDE.md` (Tests, Checks, Not without asking), `planning\lessons-for-the-skills.md`, `pyproject.toml`, `Makefile`, `image\compose.yml`, `image\Dockerfile`, `image\entrypoint.sh`.
- The parked drafts to fold in: `factory\features\F0003-*\drafts\F0003-S0011-*.md`, `factory\features\F0008-*\drafts\F0008-S0007-*.md`, `factory\features\F0010-machine\drafts\F0010-S0025-*.md`, `factory\features\F0011-proof-and-documents\drafts\F0011-S0007-*.md`.
- The code a story touches, under `src\factory\` and `tests\`: read each module a story names before writing its Interface.

## What to write

1. `C:\Dev\Projects\factory-rf\planning\overnight\stories\F0012-housekeeping\FEATURE.md` in the form of `factory\FEATURE.md`: Goal, Scope, Out of scope (steps 2 to 8, the restructure, a project's own skills and agents), Stories in their build order, and "Decisions taken for the human": the human's answers of 2026-10-17 as decisions with their source, and any choice you make, marked "taken by the session for the human, to confirm".
2. One story per file under `...\F0012-housekeeping\drafts\`, named `F0012-S000N-<slug>.md`, in the form of `factory\TICKET.md`, with Assignment, Interface, Acceptance criteria and Demo.

## Rules for the split

- One story is one coder's work within $4 and a 60-minute lease; split an item that is larger.
- The coder may write only `src/*` (and the tester `tests/*`, the documenter the four documents). `Makefile`, `pyproject.toml`, `uv.lock`, `factory/stages.yml`, `image/*`, `claude/*` and `template/*` are outside every write path in v1's `factory/stages.yml`: check what the write paths really are. For each item that needs such a file (the xdist dependency and `-n` option, the `duplicates`, `mutants` and `documents` targets and their dependencies, the `records:` and `checks:` entries in `factory/stages.yml`, the compose project name), write the exact change as "The human's change before S000N" in FEATURE.md (a section of its own, with the file, the lines and the reason), so that the session can commit it between two stories, and let the story build and test only what lies inside the write paths. If a file under `image/` or `claude/` is inside some role's write paths, say which.
- A story that changes tests another story wrote names them and asks the human's leave as a FEATURE decision, in the form of F0011's decisions 20 to 22.
- Every behaviour has its own criterion, both sides of every rule as rows of one parametrized test, test data valid under the built code (the `CLAUDE.md` Tests rules, the lessons file).
- A Demo's `Expect:` must be met exactly by the built code.
- The order: what makes later stories cheaper first (1.1 faster `make check`), the duplicates report before the fixes it finds, the measuring items before the demo frame.

## Not

- No git commands. No file outside `planning\overnight\stories\F0012-housekeeping\`. Do not change the parked drafts; say in FEATURE.md which story takes each in.

## Reply

The list of stories with one line each, the human's changes with the story each precedes, the decisions you took for the human, and anything in the plan you could not place.

Model: opus.
