# Brief: draft F0026, two small faults seen on the night of 2026-10-19 (housekeeping, the human's word)

## Goal

Write the feature `F0026-the-board-shows-only-real-crashes-and-a-flaky-test-is-fixed` and its stories (one or two) so that v1.1 can build them after F0020. Find each fault's cause first, in the code and the records, and say it in `feature.md`; then the fix.

1. **`factory-watch` shows `event: crash:<id>` at every acceptance start**, though the records hold none: `F0021-A0001`, `A0002`, `A0003` and `F0025-A0001` each showed it while running, and A0001 ended with `crashes: 0` and no `iteration failed` line in `/state/factory.log`. Read `factory-watch`'s code (find it from the console script in `pyproject.toml`) and how it derives its `event:` line (the evaluation, `src/factory/domain/` and `src/factory/application/`), and find why an acceptance's start reads as a crash (for example a claim with no run record yet, or an acceptance's front matter without the fields a story has). Look read-only at the live board: `MSYS_NO_PATHCONV=1 docker exec -w /work/checkout factory-self-factory-1 factory-watch`. A real crash must still show.
2. **A flaky test**: `tests/application/test_watcher_move_rule.py::test_every_factory_move_is_no_reject[tests-doing]` failed once under the parallel `make check` (pytest-xdist on every core) and passed three times alone (F0021-S0004, journal entry 10, `factory/features/F0021-the-factory-records-what-the-human-did/done/`). Read the test and what it calls, and name the likely cause (a time limit too tight under load, shared state, a file outside `tmp_path`, ordering); CLAUDE.md *Tests* has the rules a test that waits on a time limit must follow. The fix keeps the test's name and what it checks; changing it is a test change another story wrote, so `feature.md` gives the leave as a decision.

## Inputs (read these first)

- The code and tests named above; `CLAUDE.md`; `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`; `docs/project-guide/README.md` and the guide files it names for the domains touched; `docs/operator-guide.md`; `docs/decisions.md`.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes) and a budget of a few dollars. A documents-only part may be its own story.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a smoke test's `Expect:` met exactly by the built code; every file a smoke test or a test names exists or is made by the story. The smoke test runs in v1.1's container (Linux, as the factory user, umask 002) under the kernel's write guard, with no paid call. 
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md`, names them in its Interface, and `feature.md` gives the leave as a decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`, `claude/` if it is outside) is under *The human's changes* in `feature.md`, with exact lines and the story it must come before.
- No secret-like key with a value in a story's text, and no 32-character hex value.
- Keep it small (the human's rule: solid over clever): fix the cause, not the symptom; no new mechanism.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0026-the-board-shows-only-real-crashes-and-a-flaky-test-is-fixed/feature.md` (in the sections of `factory/feature-form.md`) and the stories under its `backlog/` as `F0026-S000N-<slug>.md` (in the sections of `factory/story-form.md`). Check each story with `uv run --project C:/Dev/Projects/factory-rf factory-check-story <path>`, run from the temporary folder `C:/Users/pasca/AppData/Local/Temp/f26draft` (and nowhere else), which holds a copy of the story laid out as `factory/features/F0026-.../backlog/` beside a copy of `factory/story-form.md`; every line must end in `: ok`. If the check needs the Landlock adapter, which does not import on Windows, stub it in that temporary folder only.

## Not

No git commands. No network calls. No file outside `planning/overnight/stories/F0026-the-board-shows-only-real-crashes-and-a-flaky-test-is-fixed/` and the temporary folder. Do not start sub-agents. No paid model call of your own. Remove the temporary folder when done (if a removal is refused, say so). You may look inside v1.1's container read-only with `docker exec factory-self-factory-1 <command>` (set `MSYS_NO_PATHCONV=1` first); change nothing there, and never read a token or key file.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human (each fault's cause above all), and anything you could not place.
