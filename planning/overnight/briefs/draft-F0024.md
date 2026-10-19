# Brief: draft F0024, mutation testing per story (step 7a of the order after F0011)

## Goal

Write the feature `F0024-mutation-testing-per-story` and its stories (two to four) so that v1.1 can build them after F0023 (a known result is not checked again). The content is the human's, confirmed on 2026-10-17, in `planning/overnight/restructure-after-f0011.md`, step 7a: `make mutants` over a large feature does not fit an agent run (the shell tool ends a command after 10 minutes; F0012's acceptance had about 12,000 mutants; F0021's acceptance reached 2,806 of about 5,750 in three 540 s runs, so its score was partial); instead the engine runs `make mutants` over the modules a story changed as a record after the coder (beside `duplicates`, with its own time limit), the reviewer reads the survivors while the story is open, and the acceptance re-runs only the survivors left from all stories against the final code. Leases stay as they are. Measure first: from F0019's and F0021's archived stories and their acceptances (journals, `.costs.jsonl`, `/state/records/project-commands.jsonl` read-only in the container), how many modules each story changed and how long `make mutants` would take per story (mutants per module times the time per mutant the acceptances saw); give the expected time per story and say whether it fits a report's time limit within the coder stage's lease, or what must give (a story-sized limit with a partial result recorded as partial, never as a pass).

## Inputs (read these first)

- The plan: `C:/Dev/Projects/factory-rf/planning/overnight/restructure-after-f0011.md` (step 7a; "The time `make check` takes").
- How mutants run today: the `Makefile`'s `mutants` target and its `FEATURE` argument, `MUTANTS_SECONDS`, `[tool.mutmut]` in `pyproject.toml`, the scripts the target calls, the acceptance reviewer's agent text (`claude/agents/acceptance-reviewer.md`) and how it reads the survivors; the pipeline definition's `reports` (`duplicates` after the coder) and how the stage finisher runs reports and hands their output to the next role (`src/factory/application/stage.py`, the handlers, the project-commands interface and its records).
- F0021's acceptance and its mutants result: `factory/features/F0021-the-factory-records-what-the-human-did/done/` (the acceptance's journal); F0019's acceptance with its two crashes from `mutants/seed` (`factory/features/F0019-the-write-guard-by-the-kernel/done/`).
- F0020, F0022 and F0023, built before F0024: `planning/overnight/stories/F0020-*/`, `F0022-*/`, `F0023-*/` (above all F0023's known results: a mutants report on the same tree is a known result too, or say why not), and their pre-checks in `planning/overnight/precheck/`.
- The forms and rules: `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, `CLAUDE.md`, `docs/project-guide.md`, `docs/operator-guide.md`, `docs/decisions.md`.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes) and a budget of a few dollars. A documents-only part may be its own story.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a smoke test's `Expect:` met exactly by the built code; every file a smoke test or a test names exists or is made by the story. The smoke test runs in v1.1's container (Linux, as the factory user, umask 002) under the kernel's write guard, with no paid call. The plan's short smoke run after the feature is paid: put it under *The human's changes* as a check after the feature, not in a smoke test.
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md`, names them in its Interface, and `feature.md` gives the leave as a decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`, `claude/` if it is outside) is under *The human's changes* in `feature.md`, with exact lines and the story it must come before.
- No secret-like key with a value in a story's text, and no 32-character hex value.
- Keep it small and generic (the human's rule: solid over clever): the engine learns no target names and no stage names; a partial mutants result is recorded as partial, never as a pass; mutants stay a record for the reviewer, never a check that fails a stage.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0024-mutation-testing-per-story/feature.md` (in the sections of `factory/feature-form.md`) and the stories under its `backlog/` as `F0024-S000N-<slug>.md` (in the sections of `factory/story-form.md`). Check each story with `uv run --project C:/Dev/Projects/factory-rf factory-check-story <path>`, run from the temporary folder `C:/Users/pasca/AppData/Local/Temp/f24draft` (and nowhere else), which holds a copy of the story laid out as `factory/features/F0024-.../backlog/` beside a copy of `factory/story-form.md`; every line must end in `: ok`. If the check needs the Landlock adapter, which does not import on Windows, stub it in that temporary folder only.

## Not

No git commands. No network calls. No file outside `planning/overnight/stories/F0024-mutation-testing-per-story/` and the temporary folder. Do not start sub-agents. No paid model call of your own. Remove the temporary folder when done (if a removal is refused, say so). You may look inside v1.1's container read-only with `docker exec factory-self-factory-1 <command>` (set `MSYS_NO_PATHCONV=1` first); change nothing there, and never read a token or key file.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human (the report's time limit and a partial result above all), the measured time per story, and anything you could not place.
