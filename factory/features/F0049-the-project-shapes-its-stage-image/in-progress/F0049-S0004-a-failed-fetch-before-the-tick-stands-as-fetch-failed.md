---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-04T02:20:55.662567Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T02:20:55.654969Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T02:20:55.662567Z'
  stage: intake
---

# A fetch that fails before the tick stands as the stop fetch_failed

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

Since F0049-S0003 the factory fetches before every tick, in `_ProjectImageStart.prepare`, to compare the stage file on `origin/main` with the one in use. That fetch is not guarded: when it fails (the network is down, the token expired or was revoked, the address is wrong), `FetchFailed` escapes to the scheduler's catch-all, which logs a multi-line `iteration failed: FetchFailed: ...` and runs no tick. The tick's own fetch, which raises the stop `fetch_failed`, is never reached. So `factory-health` reports `healthy` while the factory does nothing, no stop record is written, and the operator guide's promise that "an expired or revoked token shows as `fetch_failed`" no longer holds (the feature acceptance F0049-A0001 reproduced it: three failed iterations, `factory-health` exit 0 `healthy`, no `fetch_failed` line). The human accepted the `iteration failed` behaviour "for now" in F0049-S0003 entry 11; this story ends it. A fetch that fails before the tick raises the stop `fetch_failed` exactly as the tick's fetch does (scope `repository`, the error's text as its detail), runs no tick in that iteration and changes neither the image, its identity, its `PATH` nor the stage file last handled. The next fetch that passes clears the stop, and the comparison of the stage file goes on as before. How the tick itself fetches does not change; whether the second fetch per iteration (prepare's and the tick's) should become one is left to a later story.

## Interface

- `factory.entry.run._ProjectImageStart` (entry):
  ```python
  def _follow_main(self) -> bool: ...
  ```
  - It returns `False` when `git.fetch()` raises `FetchFailed` (`factory.domain.errors`), after `StopService(boundaries).raise_stop(RepositoryStop(scope="repository", reason="fetch_failed", detail=str(error), at=boundaries.clock.now()))`; it reads no stage file then, and the tick, the stage file last handled and the image in use stay as they were.
  - After a fetch that passes it calls `clear_stop("fetch_failed")` and returns `True`, then compares the stage file as today.
  - `prepare` returns `False` when `_follow_main` does, so no tick runs in that iteration and the scheduler logs no `iteration failed` for it.
- Any other `GitError` from the fetch is not caught here and keeps today's path.
- The tester writes `tests/entry/test_run_fetch_before_tick.py`, driving `run_instance` over a real bare remote that becomes unreachable after the start (renamed away), with `FakeHostingService` and `FakeImages`, the way `tests/entry/test_run_project_image_rebuild.py` drives it.

## Acceptance criteria

1. After a start whose first tick ran, a fetch before the next tick that fails leaves the stop `fetch_failed` with scope `repository` and the fetch's error text as its detail in the health status; the factory log holds a `stop repository fetch_failed:` line and no `iteration failed` line, and no tick runs in that iteration. Row: a fetch that passes leaves no `fetch_failed` stop and the tick runs.
2. While the fetch fails, the image, the identity and the `PATH` stay those in use before the outage, and no build is asked for; rows: a project without a stage file (the base image and its identity) and one with a stage file (the project image and the layer's identity).
3. The first fetch that passes after the outage clears `fetch_failed`, and the tick of that iteration runs; when `main` changed the stage file during the outage, that file is built once before that tick and the tick takes the new image, identity and `PATH`.
4. `make check` stays green.
5. docs: `docs/operator-guide.md`: in "The stops of the tick" and in the stops table's `fetch-failed` row, that the fetch before every tick (the one that compares the stage file) raises the same stop. `docs/project-guide/stage-environment.md`: in *The project's stage image*, that `_ProjectImageStart.prepare` raises `fetch_failed` on a failed fetch and runs no tick. `docs/decisions.md`: one entry: a failed fetch before the tick stands as `fetch_failed`, because the operator and the container's health check read `factory-health`, and an `iteration failed` line alone left it `healthy` while nothing ran; it replaces what F0049-S0003 entry 11 accepted for now. `README.md`: none, it names no stop.

## Smoke test

```bash
uv run pytest tests/entry/test_run_fetch_before_tick.py 2>&1 | tail -1
```

Expect: a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
