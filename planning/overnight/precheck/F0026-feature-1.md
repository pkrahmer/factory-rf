# Pre-check F0026, round 1: the feature, its human's changes and its decisions

I checked the feature `F0026-the-board-shows-only-real-crashes-and-a-flaky-test-is-fixed`, its one story and the drafter's brief (`planning/overnight/briefs/draft-F0026.md`) against these sources:

- v1.1's roles and forms (`claude/agents/*.md`, `factory/story-form.md`, `factory/feature-form.md`), `factory/pipeline.yml` and `CLAUDE.md`;
- the code (`factory.domain.lease`, `factory.domain.evaluation`, `factory.application.claims`, `watcher`, `tick` and `stage`, `factory.adapters.agent_launch`, `factory.entry.watch`) and its tests;
- F0021-S0004's journal;
- F0020's stories still to build (S0006 to S0008).

The story's own result is in `F0026-S0001-1.md`. A prototype of the story was built in a copy of the repository in the temporary folder, and its tests and smoke tests were run in throwaway containers of v1.1's image: no network, no volume, no secret. I also ran `factory-watch` once, read-only, in the running instance.

## The story in short

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 factory-watch judges its own instance's claim by the lease | accepted (`tests`) | no stop predicted; one optional docs edit |

## Order and sizing

- One story is right. The change is about 15 lines in four modules, four small test modules and one changed line in an earlier test. One documenter run covers five sections.
- No story touches these: the git interface's operations, `tests/application/test_interfaces.py`, the pipeline definition or its load tests, the stage finisher, the records contract, `tests/test_model_configuration.py`, the layers. No structural test is added that reads the source, so `[tool.mutmut]` stays as it is.
- Fixture order does not matter: the new tests use the existing `boundaries`, `clock`, `human` and `agent_home` fixtures.
- **When to build:** after F0020-S0007 (point 1). S0001's docs criterion describes the provider-limit wait that S0007 builds.

## The cause (decision 1): confirmed

- **Live.** `factory-watch` in `factory-self-factory-1` at 07:57:07 UTC printed `event: crash:F0020-S0005`, with the row `claim=self  running_since=2026-10-19T07:56:33Z`. That is a story claimed 34 seconds before, while the instance ran its tests stage. So the cause is the second process, not the acceptances.
- **Reproduced.** On today's code, smoke block 2 gives `crash` both for a claim made 1 minute before and for one made 61 minutes before. With the prototype it gives `idle:-  F0001-S0001 is held by self` and then `crash`.
- **The code path.** `run_watch` calls `Watcher(boundaries, instance).evaluate`, the tick's own evaluation. `ClaimService.status` calls `claim_status`, which returns `own` for the instance's claim whatever its age. `_agent_at_work` then maps `own` through `CLAIM_EVENTS` to `crash`.
- **The tick is one process.** `Scheduler` runs prepare and then tick, and the run handler runs the stage synchronously; there are no threads in `src/factory`. So the tick itself never looks while its own stage runs.
- **The suggested causes do not hold.** An acceptance's front matter and run records play no part.

## The decisions

1. **The cause:** right (above).
2. **`observed_claim_status`, and `observer` as a keyword of `Watcher`:** right, and the smallest fix. The evaluation already takes the status function. The tick keeps `claim_status`, and its immediate rerun after a restart is already guarded by `make check`: switching `Tick` to `observer=True` in the copy fails 20 existing tests (`tests/test_kill_points.py`, `tests/test_fault_paths*.py`, `tests/entry/test_run.py`).
3. **A real crash still shows, at the latest when its lease runs out:** right as a choice. One claim is slightly too strong (edit B): "at and past the lease no live stage can hold it". In this repository's pipeline the coder's and the documenter's stages sum to exactly their lease (40 + 15 + 5 = 60 minutes). On top of that come:
   - the agent run's `SUDO_GRACE` of 30 s (`factory.adapters.agent_launch`);
   - the steps between the claim's `started_at` and the run (ensuring the pull request, composing, sealing);
   - the steps after the checks (commit, push, labels).

   So a live stage that uses every limit can show `crash` on the board for up to about a minute past its lease. It is only a display, it is rare, and the tick does not act on it. The same margin already exists for another instance's `expired`, which the load-time rule `_lease_faults` accepts. The rule and the fix are unchanged; only the sentence should say so.
4. **A provider-limit wait past the lease after F0020-S0007:** right and accepted for good reasons. It touches F0020 in these places:
   - None of F0020's code files is shared: S0006 to S0008 touch `opencode_runtime`, `agent_launch`, `sealed_runs`, `provider_limits`, `boundaries`, `clock`, `settings`, `preflight`, `machine` and `wiring`, never `lease.py`, `claims.py`, `watcher.py` or `watch.py`.
   - S0007's docs criterion writes into the same documents (operator guide, *A provider's spend limit*; `stages.md`, *Starting a stage*; `watching.md`, *Boundaries*), in other sections. Built one after the other, they do not conflict.
   - S0007's operator-guide sentence says a claim held past its lease is something "only another instance on the same repository would act on". That stays true, and F0026's bullet adds the board's view of it.
   - **What is missing** is the order. S0001's docs criterion describes the provider-limit wait, which exists only after S0007, so F0026 must start after S0007 (edit A).
5. **The leave for `tests/test_claim_ownership.py`:** right and needed. Without it, the rule "only the claim service reaches the lease functions" would not cover the new one. With the one-line change, both tests pass on the prototype (only `factory.application.claims` imports `observed_claim_status`), and both keep their names. I confirmed that no other earlier test changes: the whole suite has only the container's 35 environment failures, the same set as earlier pre-checks.
6. **The flaky test: no cause, no fix:** sound. The test opens at `tests` and pushes `doing`. `last_stage_change` reads the newest commit beyond `origin/main` (`git log --date-order`, which never lists a parent before its child) and finds a legal factory move. No time limit is near, nothing is shared between workers, and nothing lies outside `tmp_path`.

   F0021-S0004's journal shows it failed once, in entry 10. Entries 13 to 28 only repeat the note. Entry 10 was the coder's stop on a red, in-progress `make check`: two other tests (`tests/application/test_costs.py`) failed in it because of the story's own change. So a failure caused by the work in progress, or by an edit during the parallel run, is as likely as load. That supports not guessing.

   Five more parallel runs (`-n auto`) of the module beside `test_watcher.py`, `test_watcher_observer.py` and `tests/entry/test_watch.py` passed here. Waiting for the failure text, through change 1, is the right call.
7. **The folder's name:** fine. Nothing names it yet.

## The human's changes

- **Write paths:** right as stated. The coder writes `src/*`. The tester writes `tests/*`, including the changed `tests/test_claim_ownership.py` under decision 5. The documenter writes `docs/*`.
- **Nothing outside a write path:** no `Makefile`, `pyproject.toml`, `factory/`, `security/`, `.secrets.baseline` or `image/` change, and no suppression marker. `[tool.mutmut]` stays as it is.
- **Change 1, the `CLAUDE.md` bullet:** right and harmless.
  - The anchor exists verbatim in *Tests*. No test reads the root `CLAUDE.md` (`tests/test_claude_files.py` pins only `template/CLAUDE.md`).
  - `make test` runs with `--tb=short`, so the `E` lines and the `file:line` it asks for are in the output an agent sees.
  - Its timing, before S0001, is right.
  - Two remarks:
    - (i) The reason's attribution is off (edit C). Entries 10, 13, 17 and 28 are the coder's, but 15 is the tester's, 21 the documenter's and 23 the smoke tester's. Also, only entry 10 saw the failure; the others repeated the note.
    - (ii) The bullet reaches failures that an agent sees in its own run. A failure in the factory's own check after an agent stalls the stage with the last 15 lines of output (`STALL_TAIL_LINES`). Under `-q` those lines hold the short summary's `FAILED <test> - <first message line>`, but not the `E` lines. That is partial text, and better than today's none. I recommend leaving the bullet as drafted.

## Points for the human, with recommended answers

1. **The build order** (edit A): (a) decision 4 says F0026 starts after F0020-S0007 is archived; (b) leave it implicit in the night plan. Recommended: (a). S0001's docs criterion describes S0007's wait.
2. **The lease margin** (edit B): (a) reword "no live stage can hold it" in the Goal and decision 3; (b) as drafted. Recommended: (a). A live coder or documenter stage can run up to about a minute past its 60-minute lease, so the board can briefly show `crash` for it. The fix does not change.
3. **Change 1's reason** (edit C): (a) correct the attribution; (b) as drafted. Recommended: (a). It is cosmetic, but the reason will be read later.
4. **Change 1 and the factory's own red check:** (a) as drafted; (b) also ask agents to quote the stall entry's tail. Recommended: (a). The stall entry already carries the `FAILED` line and its first message line.
5. **The story's optional edit 1**, the operator guide's opening sentence of `factory-watch` (see `F0026-S0001-1.md`): recommended (a), take it.

## Verdict

Feature accepted. Edits A, B and C are recommended, and none of them blocks. S0001 is accepted at intake as drafted, with one optional edit.

Edit A, decision 4: after "S0001 touches `watcher.py`, `watch.py`, `claims.py` and `lease.py`, none of which F0020, F0022, F0023 or F0024 change." insert:

```markdown
 S0001 starts after F0020-S0007 is archived: its docs criterion describes the provider-limit wait that S0007 builds.
```

Edit B, the Goal: replace "at and past the lease no live stage can hold it (a role's `time_limit` and its stage's checks fit within its `lease_duration`), and the line is `event: crash:<work item>`." with:

```markdown
at and past the lease a live stage can hold it only for the factory's own steps around its run and checks, at most about a minute (a role's `time_limit` and its stage's checks and reports fit within its `lease_duration`), so the line is `event: crash:<work item>`.
```

and in decision 3, after "**A real crash still shows**, at the latest when its lease runs out." insert:

```markdown
 A live stage that uses every limit can show as `crash:<id>` for up to about a minute past its lease (the agent run's 30-second grace, and the factory's steps before the run and after the checks); that is a display only, and the same margin another instance's `expired` already has.
```

Edit C, change 1's reason: replace "The reason: F0021-S0004's coder named the failing test in entries 10, 13, 15, 17, 21, 23 and 28 and quoted none of its failure;" with:

```markdown
The reason: F0021-S0004's coder saw the test fail once (entry 10), and its agents named it again in entries 13, 15, 17, 21, 23 and 28, but none quoted its failure;
```
