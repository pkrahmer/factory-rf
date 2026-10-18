# Brief: pre-check F0017 round 1 with v1's own roles (all three stories)

## Goal

For the draft of `F0017-the-seal-tests-leave-no-folders`, play v1's intake exactly, then predict whether the tester, coder, reviewer, documenter, demo stage or acceptor would stop it, and give it one verdict line. The drafts were written by the session's drafting agent for the seal-test leftovers (the human's to-do item 17, 2026-10-18); they have not been checked against v1's roles. Also judge the feature's human's change (exact lines, needed before which story, and whether one is missing).

F0014's acceptance found that six of its nine human answers fixed a contradiction in the drafted text (a test the domain refuses, a demo naming a module nobody made, a `noqa` a structural test forbids, an equality against a post that always carries the marker). So: for every test a draft names or describes, check it against the built code and the tests that pin it (structural tests such as `tests/test_process_search.py`, `tests/test_claude_files.py`, `tests/test_compose*.py`, fixture order, `mypy --strict`, ruff); and run every Demo command against today's code where it can run before the story, and check that every file it names exists or is made by the story.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0017-the-seal-tests-leave-no-folders/FEATURE.md` and the three drafts under `drafts/`.
- The findings and the run they came from: `C:/Dev/Projects/factory-rf/docs/runs/2026-10-12-overnight/night-log.md`, the rows of 2026-10-18 07:37 and 13:45.
- v1's role files, verbatim, under `C:/Dev/Projects/factory/claude/skills/` (`factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo`, each `<name>/SKILL.md`) and `C:/Dev/Projects/factory/claude/agents/*.md`.
- `C:/Dev/Projects/factory-rf/CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory/stages.yml` (the write paths per stage), `factory/TICKET.md`, `factory/FEATURE.md`, `planning/lessons-for-the-skills.md`.
- The code, files and tests the draft touches: `tests/conftest.py`, the seal code in `src/factory/adapters/git_cli.py` and its tests (`tests/**/test_git_cli_seal.py`, `test_sealed_runs.py`, `test_checkout_preparer_seal.py`, `test_nested_repositories.py`), pytest's `_pytest/tmpdir.py` and `_pytest/pathlib.py` in the project's `.venv`, `pyproject.toml`'s pytest and mutmut settings, and the `Makefile`'s `test` and `mutants` recipes.

## Check in particular

- Every behaviour the Assignment, the Interface or a FEATURE decision states has its own criterion, on both sides; the sides of one rule are rows of one parametrized test; a story that changes tests another story wrote names them exactly, and FEATURE.md gives the leave as a decision (write its exact text if it is missing).
- Test data and helpers valid under the built code (`CLAUDE.md` Tests); criteria pass `mypy --strict`, ruff, semgrep and detect-secrets; each Demo's `Expect:` met exactly.
- S0001: the cause the FEATURE gives (mutants of the seal, mutmut's stopped runs) against the code and pytest's own cleanup (`_pytest/pathlib.py` in the project's venv); `reopen` and the autouse fixture against fixture order (it must run after every test's own teardown, also the seal fixtures'), `tmp_path_factory` and session-scoped temporary folders, symbolic links, and pytest-xdist workers; the child-pytest wiring test (`-p conftest`) under `make test`'s options (`-n auto`, `--cov`, `-p no:cacheprovider`) and `mypy --strict`; whether the coder truly has nothing to build; the human's `Makefile` change (already made in the working tree) against `.ONESHELL`, `bash -eu -o pipefail` and the `|| { ... }` status handling.
- Write paths: each file a stage must write is inside that stage's write paths in `factory/stages.yml`.
- Each story fits the tester's $2 and the coder's $4 with one resume, inside a 60-minute lease.

## Output

One file, `F0017-S0001-1.md`, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`. Each holds the intake outcome exactly as v1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands. No network calls. No file other than your outputs. Do not change the drafts or FEATURE.md. Do not start sub-agents. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and leave nothing behind.

## Reply

Per draft its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers; anything wrong with the human's changes.
