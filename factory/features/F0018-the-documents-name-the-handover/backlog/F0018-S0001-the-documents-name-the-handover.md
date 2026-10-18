# The documents name the handover

## Description

Since the handover of 2026-10-18 (commit `3bcee441`), v1.1 builds this repository itself, and v1's stage table, forms and features F0001 to F0017 lie in `factory/v1/`. Three passages still describe the time before: the README says that the first implementation builds this repository and that a stage's agent run is first observed at the shakedown run; its section *How it is built* names v1 as the builder; and the operator guide's bullet under *Replaced from v1* says that this repository's own `factory/` tree is v1's "until this repository moves to v1.1's layout". This story makes the three passages true and records the handover in the decision log. It is documentation only: the tester and the coder change nothing.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `README.md`, `docs/operator-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in `README.md`, the opening paragraph says that this repository was built by the first implementation (github.com/pkrahmer/factory) until the handover of 2026-10-18 and is built by v1.1 itself since then, and it no longer says that a stage's agent run and a `time_limit` under `sudo` are first observed at the shakedown run (both were observed on 2026-10-18, on the todo demo); its section *How it is built* says that v1.1's instance builds the repository from `factory/pipeline.yml`, with its features and stories under `factory/features/`, and that v1's history lies in `factory/v1/`. In `docs/operator-guide.md`, the bullet that begins "This repository's own `factory/` tree is v1's" is replaced by one saying that this repository's v1 history lies in `factory/v1/` (v1's `stages.yml`, `TICKET.md`, `FEATURE.md` and its features F0001 to F0017), that nothing reads it and `factory-check-story` does not apply to it, and that since the handover v1.1 builds this repository from `factory/pipeline.yml`, `factory/story-form.md` and the features under `factory/features/`. `docs/decisions.md` gets a new entry at its end, *factory-rf is built by v1.1 since the handover*, dated 2026-10-18 (commit `3bcee441`), which says why v1's features left `factory/features/` (v1.1 reads no v1 work item, and v1's `done/` folders would have made each of v1's features count as due for an acceptance), why v1.1's features continue v1's numbers from F0018 (`make mutants` finds a feature's modules by its id in the commit subjects), and that v1 is stopped, not removed, as the fallback. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "until this repository moves to v1.1's layout" docs/operator-guide.md
```
Expect: `0`

```bash
grep -c "factory-rf is built by v1.1 since the handover" docs/decisions.md
```
Expect: `1`

```bash
grep -c "factory/v1/" README.md
```
Expect: a number of at least `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal
