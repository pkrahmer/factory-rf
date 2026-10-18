# Brief: draft F0017, the seal tests leave no folders behind, for v1 to build

## Goal

Write the feature `F0017-the-seal-tests-leave-no-folders` with one story (or two, if the split rules need it) so that v1 can fix, before the handover, a fault of factory-rf's own test suite: every `make test` in v1's container leaves folders under `/tmp/pytest-of-factory` that pytest cannot remove, because the seal tests (F0014-S0006 and its followers: the factory alone writes the checkout's `.git`) close a `.git` (permissions, owner or group) that the test user then cannot delete. On 2026-10-18 they had grown to 10 `garbage-*` and 198 `pytest-*` folders, 5.4 GB, removed by hand as root (night log, 07:37). The human chose a fixture that unlocks what the seal tests closed (to-do item 17, 2026-10-18).

## Inputs (read these first)

- The night log rows of 2026-10-18 07:37 and earlier mentions of `garbage-` or `pytest-of-factory`: `C:/Dev/Projects/factory-rf/docs/runs/2026-10-12-overnight/night-log.md`.
- The seal code and its tests: search `src/factory/` for the seal (`seal`, `chmod`, `factory-work`, `2750`) and `tests/` for the tests that call it or check it (F0014's stories in `factory/features/F0014-the-first-start-findings/done/`, above all S0006 and those after it, name them).
- How pytest's `tmp_path` cleanup works (pytest keeps the last three base temp directories and renames ones it cannot remove to `garbage-*`), `tests/conftest.py`, and the rules in `CLAUDE.md` (Tests) and `docs/project-guide.md` on fixtures.
- The forms and rules v1 applies: `factory/TICKET.md`, `factory/FEATURE.md`, `factory/stages.yml`, v1's role files under `C:/Dev/Projects/factory/claude/skills/`, `planning/lessons-for-the-skills.md`, and how F0015 and F0016 passed (`factory/features/F0015-the-tiny-storys-findings/`, `factory/features/F0016-the-shakedown-findings/`).

## The content (the session's proposal, chosen by the human)

Find exactly which tests leave a folder pytest cannot remove, and why (the mode bits, the owner, the group, a read-only parent, a sticky bit; under which user `make test` runs in v1's container and in v1.1's instance). Then a fixture (or a change to the existing seal fixtures) that, after each such test, gives the test user back write and search permission on everything the test closed, so that pytest's own cleanup removes the folder; with a test that holds it (for example: after a seal test's teardown, the tree under its `tmp_path` is writable by the test user and can be removed with `shutil.rmtree`). Say whether the tests need `sudo` or a second user to seal, and if the cleanup needs root, say how the fixture does it without root, or recommend another way (for example sealing a copy the test owns). The tests must keep checking what they check today.

## Rules for the split

- One story is one coder's work within $4 and a 60-minute lease. The changes are in `tests/` (the tester's), so the coder may change nothing; say so in the criteria.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a Demo's `Expect:` met exactly; every file a Demo or a test names exists or is made by the story.
- A story that changes tests another story wrote names them exactly, and FEATURE.md gives the leave as a decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/stages.yml`, `security/*`) is "The human's change before S000N" in FEATURE.md, with exact lines.
- No word of `GLOSSARY_FORBIDDEN` outside a `## Replaced from v1` section in the documents. No secret-like key with a value in a story's text, and no 32-character hex value.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0017-the-seal-tests-leave-no-folders/FEATURE.md` (Goal, Scope, Out of scope, Stories in build order, the human's changes, Decisions taken for the human with their source) and the stories under its `drafts/` as `F0017-S000N-<slug>.md`.

## Not

No git commands at all, not even read-only ones. No network calls. No file outside `planning/overnight/stories/F0017-the-seal-tests-leave-no-folders/`. Do not start sub-agents. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and leave nothing behind (remove what you create; if a removal is refused, say so in your reply). You may look inside v1's container read-only with `docker compose exec -T factory <command>` run from `C:/Dev/Projects/factory` (set `MSYS_NO_PATHCONV=1` first); change nothing there.

## Reply

The stories with one line each, which tests leave folders and why, the human's changes, the decisions you took for the human, and anything you could not place.
