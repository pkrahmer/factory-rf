# The documents name the handover

## Goal

On 2026-10-18 v1 handed this repository over to v1.1 (commit `3bcee441`): v1.1's instance `self` builds it from `factory/pipeline.yml`, `factory/story-form.md` and the features under `factory/features/`, and v1's stage table, forms and features F0001 to F0017 lie in `factory/v1/` as history. The documents still say that v1 builds this repository, that its `factory/` tree is v1's, and that a stage's agent run is first observed at the shakedown run. This feature makes them true again, for the newcomer, the operator and the agents. It is also the first work item v1.1 builds on itself, so that factory-rf's own `make check` runs through v1.1's stages inside its container on a story with little at stake. Done when S0001 is merged and `make check` is green.

## Scope

- The README's opening paragraph and its section *How it is built*.
- The operator guide's bullet on this repository's own `factory/` tree (under *Replaced from v1*).
- A decision-log entry for the handover.

## Out of scope

- Any change under `src/`, `tests/`, `image/`, `template/` or `claude/`.
- The files under `factory/v1/`: history, left as it is.
- The night log and `planning/` (the human's).

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The documents name the handover

## The human's changes

None. Checked against `factory/pipeline.yml`: the documenter writes `README.md` and `docs/*`, which hold every change of S0001; no story here needs `Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md` or `.secrets.baseline`.

## Decisions taken for the human

1. The first work item v1.1 builds on itself is this documentation story, before 5a (the write guard): the human's choice of 2026-10-18 on the handover plan (`planning/overnight/handover-plan.md`, section 5, option C). (Feature)
2. v1's history stays in `factory/v1/` and v1.1's features continue v1's numbers from F0018, because the `Makefile`'s `mutants` target finds a feature's modules by the feature's id in the commit subjects, and v1's F0001 to F0017 commits are on `main`. (The handover plan, section 2.1)
