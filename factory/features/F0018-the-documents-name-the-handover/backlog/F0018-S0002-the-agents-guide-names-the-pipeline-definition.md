# The agents' guide names v1.1's pipeline definition

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

S0001 made the README and the operator guide name the handover, but two passages outside its scope still say that v1's configuration runs this repository. `docs/project-guide.md`, section *The document check*, says "v1's pipeline configuration for this repository runs it as a check of the docs stage through `make documents`". Since the handover, `factory/pipeline.yml` (stage `docs`, `checks: [check, documents]`) does that. `docs/decisions.md`, entry *Three top-level paths for the product beyond `src/` and `tests/`*, says "The coder's write paths in `factory/stages.yml` name them". That file now lies at `factory/v1/stages.yml`, and the coder's write paths are in `factory/pipeline.yml` (`src/*`, `image/*`, `template/*`, `claude/*`). This story makes both passages true for the agents who read them. It is documentation only: the tester and the coder change nothing. Everything else in the two documents stays as it is, and so do `factory/v1/` and the dated history in the decision log's other entries.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `docs/project-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in `docs/project-guide.md`, section *The document check*, the sentence that begins "v1's pipeline configuration for this repository runs it" says instead that this repository's pipeline definition (`factory/pipeline.yml`) runs it as a check of the docs stage through `make documents`; the rest of the paragraph stays. In `docs/decisions.md`, entry *Three top-level paths for the product beyond `src/` and `tests/`*, the sentence "The coder's write paths in `factory/stages.yml` name them" says that the coder's write paths in the pipeline definition (`factory/pipeline.yml`; v1's `factory/stages.yml` until the handover of 2026-10-18) name them. No other passage of either document changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "v1's pipeline configuration for this repository" docs/project-guide.md
```
Expect: `0`

```bash
grep -c "The coder's write paths in \`factory/stages.yml\` name them" docs/decisions.md
```
Expect: `0`

```bash
grep -c "v1's \`factory/stages.yml\` until the handover of 2026-10-18" docs/decisions.md
```
Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal
