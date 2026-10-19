# Pre-check F0026, round 2: the feature after its edits

I checked `planning/overnight/stories/F0026-the-board-shows-only-real-crashes/feature.md` and its one story against today's `main`. Since round 1, F0020-S0001 to S0005 and F0025 have merged. The story's own result is in `F0026-S0001-2.md`.

## Round 1's verdict, carried in

- **Edit A** (build after F0020-S0007) is in decision 4, word for word.
- **Edit B** is in the Goal and in decision 3. The Goal's wording ("a role's `time_limit` and its stage's checks and reports fit within its `lease_duration`") matches `factory/pipeline.yml` today: 40 + 15 + 5 = 60 minutes for the coder and the documenter, and 90 against 100 for the acceptance reviewer.
- **Edit C** is in change 1's reason.
- **Point 5**, the story's optional edit 1, is in S0001's criterion 8.
- **Decision 8** records the answers and the folder's new name. The folder name now matches decision 7 and the path in the brief.

Nothing round 1 asked for is missing.

## Checked again on today's `main`

- **Scope and Out of scope.** They match the story. On `main`, `Tick` builds `Watcher(self._boundaries, self._instance)` and `RecoveryHandler` judges by `ClaimService.status`. Neither changes.
- **Decision 4's sentence.** "S0001 touches `watcher.py`, `watch.py`, `claims.py` and `lease.py`, none of which F0020, F0022, F0023 or F0024 change" still holds:
  - F0020-S0006 changes only `opencode_runtime`.
  - S0007 changes `machine`, `clock`, `boundaries` (the last field, `waiter`), `provider_limits`, `settings`, `sealed_runs`, `stage` and `wiring`.
  - The drafted stories of F0022 to F0024 name none of the four modules.
- **Change 1** is not yet on `main`. That is right, since it comes before S0001 starts. Its anchor bullet, "A test that waits for a time limit gives the process it starts room to start", still exists verbatim in `CLAUDE.md`, *Tests*.
- **The records contract** is at 1.2 and is not touched. The story writes nothing outside the write paths and adds no suppression marker. `[tool.mutmut]` stays as it is.
- **The docs criterion.** It names only files and sections that the split guide has.

## What F0020-S0006 and S0007 change for F0026

Nothing in F0026's code, its tests or its fixtures; the details are in `F0026-S0001-2.md`.

The one link is S0007's provider-limit wait. It holds the claim unchanged past its lease, and F0026's docs criterion describes how that shows on the board. That is why F0026 must wait for S0007's archive. Today S0006 and S0007 are still in F0020's `backlog/`.

## The story

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 | accepted (`tests`) | no stop predicted; at most one reviewer round on `watch.py`'s module docstring, fix 1 (optional) |

Prototype tests and smoke tests ran in throwaway containers (`--cpus 2 --network none`). The prototype's criteria tests pass, and both smoke blocks print their `Expect:` lines. The whole suite shows only the container's 35 known environment failures.

## Verdict

Feature ready to build, once two things are done:

- F0020-S0007 is archived in `done/` (decision 4);
- the human's change 1 is committed on `main`.

No edit is needed. The one optional fix is S0001's fix 1 (`F0026-S0001-2.md`): name `watch.py`'s module docstring in the Interface.
