# The stops table and the test helper index follow the stage image

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

Two documents still describe the stage image as it was before the feature's last stories. First, the stops table in `docs/operator-guide.md` (*The stops*) still says, in its `stage-image-failed` row, "Fix the file on `main` and start `factory-run` again". Since F0049-S0003 no restart is needed: the factory compares the stage file on `origin/main` before every tick, and the next `main` with another file, or without the file, ends the stop before the next stage. *A change on `main` takes effect before the next stage* ("No restart is needed") and *The stop `stage_image_failed`* already say so. The row is the one place that sends the operator to a restart. Second, F0049-S0004 moved the stage image tests' shared values into the new support module `tests/stage_image_support.py`, and their fixtures `base_identity_settings` and `base_image` into `tests/conftest.py`. Neither is in the index *Shared test helpers* of `docs/project-guide/README.md`, which the guide tells agents to read before writing a helper, and where the reviewer looks before counting a copy. This story corrects the row and adds both to the index. No code and no test change. What a restart does stays as *The stop `stage_image_failed`* says it.

## Interface

- No module under `src/factory/` changes, and no test: the story changes `docs/operator-guide.md` and `docs/project-guide/README.md` only.
- What the documenter carries into the index, from `tests/stage_image_support.py` and `tests/conftest.py` as they are on `main`:
  - `stage_image_support.py`: `BASE_IDENTITY` (the base image's identity, `"sha256-base"`), `FIRST` and `SECOND` (two stage files that satisfy the rule), `StageSeen` (what one tick ran with: image, identity, `PATH`, builds asked for), `built_path` (the project image's `PATH` after a given build).
  - `conftest.py`: `base_identity_settings` (the instance settings with `BASE_IDENTITY` as the image identity) and `base_image` (the base image those settings name).

## Acceptance criteria

1. `docs/operator-guide.md`, the stops table's `stage-image-failed` row: it says that the fix of `factory/stage.Containerfile` on `main` takes effect before the next stage with no restart, and it points to "The project's stage file". The text "start `factory-run` again" is gone from the row, and the other rows of the table are unchanged.
2. `docs/project-guide/README.md`, *Shared test helpers*: one entry for `stage_image_support.py` that names `BASE_IDENTITY`, `FIRST`, `SECOND`, `StageSeen` and `built_path`. The entry for `conftest.py` names the fixtures `base_identity_settings` and `base_image`. No other entry of the index changes.
3. `make check` stays green.
4. docs: `docs/operator-guide.md` and `docs/project-guide/README.md` as criteria 1 and 2 say. `README.md`: none, because its one sentence on the stage file stays true. `docs/decisions.md`: none, because no decision changes.

## Smoke test

```bash
grep -cF 'Fix the file on `main` and start `factory-run` again' docs/operator-guide.md
grep -qF '`stage_image_support.py`' docs/project-guide/README.md && echo listed
grep -qF '`base_identity_settings`' docs/project-guide/README.md && echo listed
uv run python -m factory.entry.check_documents
```

Expect: `0`, then `listed`, then `listed`, then `documents ok`.

## Journal
