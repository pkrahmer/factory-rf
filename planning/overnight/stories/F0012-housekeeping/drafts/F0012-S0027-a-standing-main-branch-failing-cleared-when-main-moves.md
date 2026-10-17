# A standing main_branch_failing cleared when main moves

## Assignment (as of log entry 1)

The preflight probes `main` with `lint` only after the machine's items have passed. When they fail (a new image without `make`, say), the preflight stops with `preflight_failed` and returns before the probe, so a `main_branch_failing` raised earlier stays in the health status even after the human has pushed the fix to `main` (F0010's acceptance, open point 5; `docs/decisions.md`, the S0009 entry's "Open:"). The human's answer of 2026-10-17 (item 1.10): a standing `main_branch_failing` is cleared when `main` is green again. Whether the new `main` is green cannot be known while the machine cannot run `lint`; what is known is that the stop names a commit that is no longer `main`. This story clears the stop then, and the new `main` is probed as soon as the machine's items pass again, which raises the stop anew if it is red (FEATURE decision 30). A stop whose commit is still `main` stays.

## Interface

`src/factory/application/preflight.py`, `Preflight.run`: when the machine's items fail, before it returns `preflight_failed`, it reads the stamp it started with. When that stamp has a `main_failed` commit and `git.resolve("origin/main")` gives another commit (or `None`), it calls `clear_stop("main_branch_failing")`; when it gives the same commit, or the stamp has no `main_failed`, the stop is left as it is. A `GitError` of the `resolve` leaves the stop as it is and does not change the result. The result is still `preflight_failed`, and the stamp is not rewritten. Nothing else in the preflight changes.

Tests: `tests/application/test_preflight_stale_main_stop.py`, with the `rig` and `red_main` fixtures of `tests/application/test_preflight_run.py` (imported or rebuilt the same way): a red `main` probed once (so the stamp holds `main_failed`), then the machine's items made to fail by removing `make` from the rig's `which` and running the preflight with another image. No existing test changes.

## Acceptance criteria

1. After the human pushes a fix to `main`, a preflight whose machine's items fail returns `preflight_failed`, and the health status holds `preflight_failed` and no `main_branch_failing`; the factory log gains `stop cleared main_branch_failing`.
2. When `main` has not moved, the same preflight returns `preflight_failed` and the health status holds both stops, `main_branch_failing` with its earlier detail.
3. When the stamp has no `main_failed` (a green `main` probed before), the machine's failure leaves the health status with `preflight_failed` only, and nothing is cleared.
4. A `git` whose `resolve` raises `GitError` (a fake written in the test) leaves `main_branch_failing` in force and the result `preflight_failed`.
5. When the machine's items pass again on the fixed `main`, the preflight probes it once: green clears nothing more and returns `None`; red raises `main_branch_failing` for the new commit. Two rows of one parametrized test.
6. Every test of `tests/application/test_preflight_run.py` and `tests/application/test_tick_preflight.py` still passes.
7. `make check` stays green.
8. docs: the operator guide's section *The stamp and the probe of the main branch* says that while the machine's items fail, a `main_branch_failing` of a commit that is no longer `main` is cleared, and that the new `main` is probed when the machine passes again; the decision log answers the S0009 entry's open point (the human's answer of 2026-10-17). No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_preflight_stale_main_stop.py tests/application/test_preflight_run.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
