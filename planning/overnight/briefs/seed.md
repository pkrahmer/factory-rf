# Brief: seed factory-rf (Phase 1)

## Goal

Turn `factory-rf` (`C:\Dev\Projects\factory-rf`) into a project v1 of the factory can work on, so that `make check` is green on an empty project and v1 accepts it. Two parts, kept apart in your summary: (a) the minimal fixes to v1's template so its check passes; (b) the project setup a human gives every v1 project.

## Inputs (read these, nothing else unless a step below names it)

- `C:\Dev\Projects\factory-v2\planning\v1.1\overnight-run-plan.md`, section 4 only ("Phase 1, seed `factory-rf`"): your specification.
- `C:\Dev\Projects\factory-v2\planning\v1.1\run-facts.md`, sections "The project contract" and "What is known not to work in the template as shipped".
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md`, section 4 (rules R1 to R17), for `CLAUDE.md`'s architecture paragraphs.
- v1's template: `C:\Dev\Projects\factory\template\` (read only; never write under `C:\Dev\Projects\factory`).
- `C:\Dev\Projects\factory-demo-todo\pyproject.toml`, `.gitignore`, `Makefile`, `CLAUDE.md` (read only): the exemplar for configuration and exemptions.
- `C:\Dev\Projects\factory\Dockerfile` (read only): which Python version and tools v1's container has, since stages run `make check` there.
- What is in `factory-rf` now: a copy of the template (root `Makefile`, `CLAUDE.md`, `README.md`, `.gitignore`, `LICENSE`; `factory/stages.yml`, `factory/TICKET.md`, `factory/FEATURE.md`).

## Decisions already taken by the main session (apply them, do not reopen)

- Package: `src/factory/` (src layout), with the four layer packages `factory.domain`, `factory.application`, `factory.adapters`, `factory.entry`, each an `__init__.py` with a module docstring. import-linter contract `layers = ["factory.entry", "factory.adapters", "factory.application", "factory.domain"]` (higher may import lower; R8, 006 point 20).
- Top-level paths for v1.1's product beyond `src/` and `tests/`: `image/` (Dockerfile, compose file, entrypoint), `template/` (v1.1's own project template), `claude/` (the agent and skill files v1.1 ships). Create none of these folders; only name them in `factory/stages.yml` and `CLAUDE.md`.
- `factory/stages.yml`: v1's template unchanged except the `coder` lane, which becomes `["factory/features/*/ongoing/*.md", "src/*", "image/*", "template/*", "claude/*"]` (no `docs/openapi.json`: no HTTP API). Keep `version: 5`, caps, lease and budgets. v1's lane globs: `*` also crosses `/`.
- No `mutants` target, no `mutmut`. No `openapi` target and no mention of `make openapi`.
- Runtime dependencies, pinned exactly (`==`, latest stable that supports Python 3.12): pydantic, PyGithub, ruamel.yaml, python-frontmatter. Dev group, pinned exactly: ruff, mypy, import-linter, pytest, pytest-cov, semgrep, bandit, detect-secrets, pip-licenses, plus type stubs mypy --strict needs for the runtime dependencies if any. `requires-python = ">=3.12,<3.13"` and a `.python-version` with `3.12`.
- The `licenses` allow list: PyGithub is LGPL-3.0. Add exactly the LGPL spellings `pip-licenses` reports for it (for example `GNU Lesser General Public License v3 (LGPLv3)`), and nothing else beyond the template's list unless another runtime dependency needs it; report every addition.
- The `secrets` target excludes `planning/` and `docs/runs/` (they will carry commit hashes) besides `uv.lock` and `.secrets.baseline`.

## What to produce (all in `C:\Dev\Projects\factory-rf`)

1. `pyproject.toml` modelled on the todo demo's: ruff with `select = ["E","F","W","I","N","UP","B","C4","SIM","RET","ARG","PL","C90","S","D"]`, line length 100, google convention, max-complexity 8, max-args 5, `extend-exclude = ["*.md"]`; per-file ignores for `tests/**` = `["S101","S603","S607","PLR0913","D"]`; mypy strict with the pydantic plugin over `src` and `tests`; `[tool.importlinter]` as above; pytest and coverage (`source = ["src/factory"]`, branch, no `fail_under` while the package is empty, or a value the seed passes: report which); `[tool.bandit]` with `targets = ["src"]` and `skips = ["B101"]` for asserts if bandit scans tests (it should not: targets is `src`); hatchling build of `src/factory`.
2. `uv.lock` and `.venv` via `uv sync` (run `uv lock` and `uv sync` yourself).
3. `Makefile`: v1's template's, with a `types` target (`uv run mypy`) and a `layers` target (`uv run lint-imports`, exit status is the tool's, no pipe), both in `check` (`check: lint types layers sast secrets licenses test`), not in `lint`; the secrets exclusion above; no `mutants`.
4. `security/semgrep/`: a minimal, valid rule set (for example a few Python rules of your own: `eval`/`exec`, `subprocess` with `shell=True`, `yaml.load` without a safe loader, `pickle.loads`). Each rule must have `id`, `languages`, `message`, `severity`, and a pattern.
5. `.secrets.baseline` from `uv run detect-secrets scan` with the same exclusions as the target.
6. `src/factory/__init__.py` and the four layer packages, each with a one-sentence module docstring.
7. `tests/test_layers.py`: one real test that uses `assert` (for example that the four layer packages import and that `factory.domain` imports nothing from the other three), so `test` collects something and the exemptions are proven.
8. `.gitignore`: keep what is there; make sure it covers `.venv/`, the tool caches, `mutants/`, `.coverage`, `.env`, `.licenses-requirements.txt`.
9. `CLAUDE.md`, filled (no `<…>` placeholders left), keeping the template's section order and its "Not without asking" list (drop the `openapi` sentences):
   - Architecture: the four layers and what lives in each; R5 to R13 of the handover as one short paragraph each, in the glossary's names.
   - Tests: pytest under `tests/`, mirroring the package; what may be faked (the hosting service, through its one fake; the agent runtime) and what may not (git: tests use a real local bare remote in a temporary directory).
   - Docs: `README.md` for the newcomer; `docs/operator-guide.md` (install, configure, stops and what to do); `docs/project-guide.md` (the project guide for agents, R17); `docs/decisions.md` (the decision log). The documenter keeps these four true from each story's docs criterion.
   - Checks: exactly what `make check`, `make lint`, `make test` run.
   - Vocabulary: two sentences. The pipeline's own files under `factory/` use v1's words because v1 reads them; code, documentation and the file formats v1.1 defines use the glossary's names (R3).
   - `planning/` and `docs/runs/` are the human's; no stage edits them.
   - Points to `docs/project-guide.md` for agents.
10. `README.md`: filled, short: what v1.1 is (the factory, reimplemented by v1 of itself), that it is under construction, `uv sync` and `make check`, where to look next. No placeholders.
11. `docs/project-guide.md`, `docs/operator-guide.md`, `docs/decisions.md`: short honest stubs saying what each will hold and that nothing is built yet. `docs/decisions.md` gets its first entries: the seed's choices (package name and layers; the three product paths; no `mutants`; the LGPL allow-list entry; the project guide in `docs/` so the documenter can keep it true).
12. Do not create anything under `factory/features/`, no `.gitkeep` anywhere, no `template/tasks/`.

## Verify

Run on this Windows host in `C:\Dev\Projects\factory-rf`: `uv sync`, then each of `make lint`, `make types`, `make layers`, `make test`, `make secrets`, `make licenses`. Run `make sast` too; if semgrep cannot run on Windows, say so exactly (the main session runs the full check in v1's container). Fix what is red in the seed's own files. Never weaken a rule to get green; if a rule fights the empty package, report it.

## Not

- No git commands at all (no add, commit, push). The main session commits.
- No write outside `C:\Dev\Projects\factory-rf`.
- No placeholder left in `CLAUDE.md` or `README.md`.

## Reply

A summary of at most 40 lines: every file created or changed, split into (a) template fixes and (b) project setup; the exact pinned versions; the licence entries added; the result of each make target; anything you could not do, and every choice you made that this brief did not fix.

Model: sonnet.
