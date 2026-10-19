# Brief: draft F0025, the project guide split by domain (step 8 of the order after F0011)

## Goal

Write the feature `F0025-the-project-guide-split-by-domain` and its stories (one or two, documents-sized) so that v1.1 can build it next, possibly before F0023: the guide has 1,905 lines and two pre-checks (F0023, F0024) recommend splitting it before it passes about 1,950, because the file tool reads 2,000 lines by default and the documenter's lesson says to split before that. The content is the human's, in `planning/overnight/restructure-after-f0011.md`: step 8 of "The order of the work after F0011" (the human's word of 2026-10-18: the project guide split by domain only, a docs-only story, one guide file per domain, read when needed, so that every agent run reads less; the tree move stays deferred) and the section "The project guide split by domain" (`docs/project-guide/` with a `README.md` index holding what holds for all code: layers, errors, kill points, test rules; one file per domain; `CLAUDE.md` then says read the index, then the files of the domains the story touches; the operator guide and the decision log stay single files; F0011-S0005's document check reads `PROJECT_GUIDE = "docs/project-guide.md"` and must point at the index, which keeps the sections it checks). Choose the domains from the guide's own 41 sections and today's code tree (the tree is not moved), and give a table in `feature.md`: each section to its new file, with its line count, so that no file passes about 600 lines. Nothing in the guide's text changes except links and the index; a moved section keeps its heading and words, so the change is checkable as a move (say how: for example a test or smoke command that every heading of the old guide is in exactly one new file).

## Inputs (read these first)

- The plan: `C:/Dev/Projects/factory-rf/planning/overnight/restructure-after-f0011.md` (step 8 and "The project guide split by domain").
- The guide: `docs/project-guide.md` (all of it), and every place that names it: `grep -rn "project-guide" --include=*.md --include=*.py --include=*.yml --include=Makefile .` from the repository root (the agents' texts in `claude/agents/`, `CLAUDE.md`, `README.md`, `docs/operator-guide.md`, `factory/pipeline.yml`'s write paths, the document check `src/factory/entry/check_documents.py` and its tests, the template and the demo).
- The drafted features that name the guide in their docs criteria: `planning/overnight/stories/F0020-*/`, `F0022-*/`, `F0023-*/`, `F0024-*/`; list each story whose docs criterion must be reworded to the new paths, with the new path, under *The human's changes* (the human or a fix agent rewords them before each is started).
- The forms and rules: `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, `CLAUDE.md`, `docs/operator-guide.md`, `docs/decisions.md`.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes) and a budget of a few dollars. A documents-only part may be its own story.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a smoke test's `Expect:` met exactly by the built code; every file a smoke test or a test names exists or is made by the story. The smoke test runs in v1.1's container (Linux, as the factory user, umask 002) under the kernel's write guard, with no paid call. 
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md`, names them in its Interface, and `feature.md` gives the leave as a decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`, `claude/` if it is outside) is under *The human's changes* in `feature.md`, with exact lines and the story it must come before.
- No secret-like key with a value in a story's text, and no 32-character hex value.
- Keep it small and generic (the human's rule: solid over clever): a move, not a rewrite; the engine learns no file of the guide by name beyond the index the document check reads.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0025-the-project-guide-split-by-domain/feature.md` (in the sections of `factory/feature-form.md`) and the stories under its `backlog/` as `F0025-S000N-<slug>.md` (in the sections of `factory/story-form.md`). Check each story with `uv run --project C:/Dev/Projects/factory-rf factory-check-story <path>`, run from the temporary folder `C:/Users/pasca/AppData/Local/Temp/f25draft` (and nowhere else), which holds a copy of the story laid out as `factory/features/F0025-.../backlog/` beside a copy of `factory/story-form.md`; every line must end in `: ok`. If the check needs the Landlock adapter, which does not import on Windows, stub it in that temporary folder only.

## Not

No git commands. No network calls. No file outside `planning/overnight/stories/F0025-the-project-guide-split-by-domain/` and the temporary folder. Do not start sub-agents. No paid model call of your own. Remove the temporary folder when done (if a removal is refused, say so). You may look inside v1.1's container read-only with `docker exec factory-self-factory-1 <command>` (set `MSYS_NO_PATHCONV=1` first); change nothing there, and never read a token or key file.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human (the domains and the size limit above all), the section table, and anything you could not place.
