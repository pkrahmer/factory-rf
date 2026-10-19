# The baseline todo run (step 10): the report

Written on 2026-10-20 (00:16 local, 22:16 UTC on 2026-10-19), after the run, by a read-only helper. It follows `planning/overnight/baseline-run-plan.md` section 5. The operator saved it here (the helper could not write files) and copied the instance's records into `data/` afterwards.

Sources:

- the target's records on `origin/main` of `C:/Dev/Projects/factory-baseline-todo`: the work items and their `.costs.jsonl` sidecars under `factory/features/*/done/`, read with `git archive origin/main factory` (the clone's `main` is 21 commits behind `origin/main`; nothing was pulled);
- the target's git log, its `work-item/*` branches included;
- the stopped instance's `state` volume, read through the Docker Desktop share: `factory.log`, `health.json`, `records/disk.jsonl`, `records/project-commands.jsonl` (copied to `data/` by the operator, read-only, after the report);
- the `claude-home` volume, for the `model` and `version` fields only (G2; no message text read);
- the operator's "Baseline" rows in `docs/runs/2026-10-12-overnight/night-log.md`;
- run 4's first 59 lines of `docs/reference/data/demo-dispatches.jsonl` in v1's clone `C:/Dev/Projects/factory` at `f8bc9d2`;
- the plan's section 1 for the shakedown.

Where this report gives its own judgement, it says **(judgement)**. Everything else comes from the records. Minutes are agent minutes, the sum of the runs' `duration_seconds`; cost is the sum of `cost_usd`, in USD.

## 1. Verdict

**Failed**, on conditions 1 and 4. The comparison was measured on two stories.

| # | Condition | Result | Evidence |
| :- | :- | :- | :- |
| 1 | Every story and acceptance accepted | **failed** | F0001-A0001, the acceptance of F0001 "the to-do service", has `outcome: refused`. Pull request #5 was closed by the human at 21:09:14 UTC "as the acceptance recommends": the acceptance reviewer itself returned "not accepted; 4 stories proposed". All 8 stories, F0002-A0001 and F0003-A0001 were merged. |
| 2 | No fix to `factory-rf` during the run | met | `C:/Dev/Projects/factory-baseline` is clean at `d0ec553217195c2dc72a9bd48cd76c54814f7a34`, which is exactly `baseline-v1.1`. The image was built once (20:03:59 UTC); the container was created once (20:04:27) with restart count 0, and every cost record names the same image. No commit to a protected file of the target (`CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `factory/pipeline.yml`, `factory/story-form.md`, `.secrets.baseline`, `security/`). The human's 11 commits are only feature copies and starts. The 4 branch-only commits on `work-item/*` are all the factory's. The three features' texts are identical to the tag's `demo/todo-service/features/`. |
| 3 | Every stop reached the human | met | There were no stops. `health.json` is `{"stops":[]}`, `factory.log` has no `stop` or `iteration failed` line, every work item has `blocked: null`, and no `factory/stops.jsonl` was written. |
| 4 | Every compared story within the band | **failed** | F0003-S0001 "title search" took 2.93 agent minutes, 127.3 % of run 4's 2.30, over the cap of 2.875 by 3.2 s. Its cost, and both numbers of F0001-S0003 "HTTP API", are within the band. The minutes were taken with `self` running beside the baseline (the human's word at 22:05 local), and are marked so. |

**(judgement)** Condition 4 fails narrowly, and only on minutes. The minutes were taken beside `self`, which the human accepted knowing they would be skewed, so this failure is weak evidence of a v1.1 regression. On cost, the clean measure, both compared stories pass with room to spare.

## 2. What ran

- **v1.1:** tag `baseline-v1.1` = `d0ec55321719` on `pkrahmer/factory-rf`'s `main`. The image label is `factory.image=d0ec55321719`, the compose project `factory-baseline`, the container `factory-baseline-factory-1`. The cost records' `image` field is `1df3550f-…` on all 67 runs.
- **Claude Code:** 2.1.296 (`ARG CLAUDE_CODE_VERSION=2.1.296` in the tag's `image/Dockerfile`). All 2,614 transcript lines that carry `version` say `2.1.296`. Run 4 used 2.1.289; the shakedown also pinned 2.1.296 (G3).
- **Models (G2):** 68 transcript files under `claude-home/projects/-work-checkout/`, one more than the 67 runs (**(judgement)** probably the preflight's `agent-run-probe`). Of the lines that carry `"model"`, 506 say `claude-opus-5-5` and 91 say `claude-sonnet-5-5`; no other model appears. These are the same two models as in run 4, so no comparison is marked "model changed".
  - Run 4's counts (429 and 100) are "messages". These counts are lines carrying the field, and Claude Code may write one message over several lines. **(judgement)** So the two counts show which models ran, not comparable volumes.
- **Runtime and login:** Claude Code (`FACTORY_AGENT_RUNTIME` unset), `login: subscription` on all 67 records. The preflight's `agent-run-probe` logged in with the subscription token (`factory.log`, 20:04:40 UTC).
- **Machine:** Docker Desktop 4.95.0 (242831), engine 29.8.2; WSL 3.0.3.0, kernel 6.18.54.1-1. These were read at report time; nothing in the night log says they changed during the run.
- **`self`:** not stopped. The human chose at 22:05 local to run the baseline "beside `self` anyway". `self` built and merged F0022-S0003 to F0023-S0005 during the run and was rebuilt several times. That is a deviation from the plan's Q5. Under the plan's own rules it is not a fix (it is not caused by the run), but it shares CPU and the usage windows.
- **Target:** `pkrahmer/factory-baseline-todo`, set up at `e205613` "Set up the repository for the factory" (20:02:49 UTC). F0001 went in at `5e5c27c`, F0002 at `5bffab5` and F0003 at `fbd86dd`.
- **Wall clock:**
  - container started 20:04:27 UTC, stopped 22:11:20 UTC;
  - first story start (`c8baff2`) 20:05:01 UTC;
  - last archive (`71e62e6`, F0003-A0001) 22:11:03 UTC;
  - **2 h 06 min** from first start to last archive (shakedown: 2 h 08 min; run 4: 16:49 to 19:36 UTC, 2 h 47 min).
- **No provider limit (G5):** every run ended `completed`, `attempt 0`. No `provider_limit` record, so every story is comparable.

## 3. The comparison (judged)

Comparison set: the stories that were first-pass in run 4 (F0001-S0002, F0001-S0003, F0002-S0002, F0002-S0003, F0003-S0001) and also first-pass in the baseline. First-pass means six runs, one per stage, and a journal with only `created`, `started`, `result` and `done` records: no question, stall, crash or round.

F0001-S0002 "service layer with filtering", F0002-S0002 "version command" and F0002-S0003 "to-do statistics" each had one review round in the baseline (10 runs, `round: 1`), so they drop out. **Two stories remain.**

The cap is 125 % of run 4's value (Q1 A, upper bound only).

| Story | Run 4 cost | Baseline cost | Δ % | Run 4 min | Baseline min | Δ % | First-pass in baseline | Within band |
| :- | -: | -: | -: | -: | -: | -: | :- | :- |
| F0001-S0003 HTTP API | 1.536 | 1.456 | −5.2 | 4.05 | 4.52 | +11.5 | yes (6 runs) | **yes** (cost cap 1.920, minutes cap 5.06) |
| F0003-S0001 Title search | 0.998 | 0.921 | −7.8 | 2.30 | 2.93 | +27.3 | yes (6 runs) | **no**: cost yes (cap 1.248), minutes no (cap 2.875; 2.928); minutes taken beside `self` |
| **Sum of the two** | 2.534 | 2.377 | −6.2 | 6.35 | 7.44 | +17.2 | | within on both (for information; the rule is per story) |

The shakedown beside them, for information (plan section 1):

| Story | Shakedown runs / cost / min | Baseline against the shakedown |
| :- | :- | :- |
| F0001-S0003 HTTP API | 12 / 2.350 / 7.61 (not first-pass) | not comparable |
| F0003-S0001 Title search | 6 / 0.785 / 2.63 (first-pass) | cost +17 %, minutes +11 % |

**(judgement)** The shakedown was 21 to 35 % cheaper than run 4. The baseline is only 5 to 8 % cheaper on the two compared stories. That fits the plan's expectation in section 4: the demo's texts gained criteria after the shakedown, so the tester and the coder had more to do. The tests stage below is where most of it sits.

## 4. Every work item (recorded, not judged)

Notes on the columns:

- "Start to approval" runs from the human's `<id>: start` commit (for an acceptance, its `opens` commit) to `handed over at approval`.
- "Start to archive" runs to `merged, archived` (for F0001-A0001, to the close at 21:09:15).
- Model minutes are the sum of `model_seconds`.
- No work item had a question, a stall or a crash: `attempts: 0`, `crashes: 0` and `blocked: null` on all eleven.
- The shakedown's numbers are the plan's.

| Item | Runs | Agent min | Model min | Cost | Start to approval (min) | Start to archive (min) | Questions (cause) | Rounds | Stalls / crashes | Run 4 cost / min | Shakedown cost / min |
| :- | -: | -: | -: | -: | -: | -: | :- | -: | :- | :- | :- |
| F0001-S0001 Domain model and in-memory repository | 6 | 3.60 | 3.32 | 1.193 | 6.5 | 14.6 | 0 | 0 | 0 / 0 | 2.846 / 6.10 | 1.520 / 3.86 |
| F0001-S0002 Service layer with filtering | 10 | 4.56 | 4.05 | 1.571 | 9.1 | 10.9 | 0 | 1 | 0 / 0 | 1.314 / 2.47 | 0.858 / 2.96 |
| F0001-S0003 HTTP API | 6 | 4.52 | 4.13 | 1.456 | 7.8 | 11.7 | 0 | 0 | 0 / 0 | 1.536 / 4.05 | 2.350 / 7.61 |
| F0001-S0004 SQLite repository and persistence switch | 10 | 5.71 | 4.84 | 1.950 | 10.8 | 11.6 | 0 | 1 | 0 / 0 | 1.944 / 5.00 | 4.214 / 12.94 |
| F0001-A0001 acceptance of "the to-do service" (refused) | 1 | 9.56 | 8.03 | 2.544 | 10.4 | 14.3 (closed) | 0 | 0 | 0 / 0 | 1.588 / 5.03 | 2.247 / 8.12 |
| **F0001 the to-do service** | 33 | 27.95 | 24.36 | 8.713 | | | 0 | 2 | 0 / 0 | 9.228 / 22.65 | 11.189 / 35.49 |
| F0002-S0001 Health endpoint | 6 | 2.80 | 2.41 | 0.935 | 6.0 | 9.9 | 0 | 0 | 0 / 0 | 1.356 / 2.77 | 0.740 / 2.62 |
| F0002-S0002 Version command | 10 | 3.48 | 2.75 | 1.186 | 8.1 | 10.0 | 0 | 1 | 0 / 0 | 0.853 / 2.08 | 0.568 / 2.20 |
| F0002-S0003 Todo statistics | 10 | 5.17 | 4.45 | 1.798 | 10.0 | 13.9 | 0 | 1 | 0 / 0 | 1.124 / 2.23 | 2.287 / 6.69 |
| F0002-A0001 acceptance of "operations" | 1 | 4.96 | 4.40 | 1.594 | 5.8 | 9.7 | 0 | 0 | 0 / 0 | 1.466 / 4.97 | 1.208 / 4.26 |
| **F0002 operations** | 27 | 16.41 | 14.00 | 5.512 | | | 0 | 2 | 0 / 0 | 4.799 / 12.05 | 4.803 / 15.77 |
| F0003-S0001 Title search | 6 | 2.93 | 2.51 | 0.921 | 5.9 | 9.8 | 0 | 0 | 0 / 0 | 0.998 / 2.30 | 0.785 / 2.63 |
| F0003-A0001 acceptance of "search" | 1 | 3.77 | 2.99 | 0.950 | 4.6 | 4.9 | 0 | 0 | 0 / 0 | 0.867 / 3.15 | 1.087 / 3.96 |
| **F0003 search** | 7 | 6.69 | 5.50 | 1.871 | | | 0 | 0 | 0 / 0 | 1.865 / 5.45 | 1.872 / 6.59 |
| **Run** | **67** | **51.05** | **43.87** | **16.096** | | | **0** | **4** | **0 / 0** | 59 runs / 15.89 / 40.1 | 82 runs / 17.88 / 57.9 |

What caused the four rounds. Each round sent the story back through doing, tests, doing and review, which is four extra runs.

- **F0001-S0002 "service layer with filtering":** the reviewer added criterion 16. `rename` looks the todo up before it checks the title, so an unknown id with a blank title raises `TodoNotFound`; no criterion pinned that order.
- **F0001-S0004 "SQLite repository and persistence switch":** a find-and-replace of `_todo` into `make_todo` renamed the earlier test `test_update_replaces_the_stored_todo` (from F0001-S0001) into `test_update_replaces_the_storedmake_todo`.
- **F0002-S0002 "version command":** a `# noqa: S603` in `tests/test_main.py` that nobody had asked for, and that `pyproject.toml` already makes unnecessary.
- **F0002-S0003 "to-do statistics":** the new API test copied helpers from an earlier test module. The tester then moved them under the standing leave and changed three earlier test files.

**(judgement)** Agent wall clock minus model time is 7.2 min over the run (14 %), the per-run start overhead that F0019's confinement and the start through `sudo` add.

## 5. Per stage, over the compared stories (F0001-S0003 and F0003-S0001)

| Stage (v1 / v1.1) | Run 4 runs / s / cost | Baseline runs / s / cost | Δ s | Δ cost |
| :- | :- | :- | -: | -: |
| intake | 2 / 26 / 0.198 | 2 / 39.7 / 0.119 | +53 % | −40 % |
| tester / tests | 2 / 93 / 0.514 | 2 / 126.5 / 0.651 | +36 % | +27 % |
| coder / doing | 2 / 103 / 0.645 | 2 / 96.8 / 0.553 | −6 % | −14 % |
| reviewer / review | 2 / 71 / 0.604 | 2 / 75.9 / 0.507 | +7 % | −16 % |
| documenter / docs | 2 / 51 / 0.278 | 2 / 68.9 / 0.234 | +35 % | −16 % |
| demo / smoke-test | 2 / 37 / 0.295 | 2 / 38.9 / 0.311 | +5 % | +5 % |
| **Sum** | 12 / 381 / 2.534 | 12 / 446.7 / 2.377 | +17 % | −6 % |

- **Shakedown:** its per-stage numbers for these two stories are not in a local record. The sidecars sit on `pkrahmer/factory-demo-todo`'s `main`, which needs `gh api`, and this helper had no network. The plan gives only its sums over three other stories.
- **(judgement)** On minutes, F0003-S0001 lost most in intake (20.4 s against 10 s) and tests (47.3 s against 33 s). On cost, the tests stage is the only stage clearly dearer than run 4: +27 % over both stories. That fits the larger criteria tables of the demo's texts after F0016.

## 6. The human's part

- **Questions:** none. No work item was blocked.
- **New product decisions:** none. Each `feature.md` has only its "add the feature" commit, and the three texts are identical to the tag's.
- **Send-backs:** none by the human. The four rounds were the reviewer's.
- **Refusals:** one, F0001-A0001. The comment at 21:09:14 UTC refused "as the acceptance recommends": the committed `docs/openapi.json` describes every 422 as a list of errors and declares no 404, while the service returns `{"detail": "<text>"}` for both. The pull request was then closed.
  - The refusal was the human's word "refuse, keep measuring" (night log, 23:12 local).
  - The four proposed stories stay unbuilt, and lie only on the closed branch `work-item/F0001-A0001`: F0001-S0005 "the OpenAPI schema states the error body", F0001-S0006 "the done filter takes only true or false", F0001-S0007 "the UTC rule holds in any local time zone" and F0001-S0008 "clear refusal of a missing database folder".
- **Merges:** 10 (#1 to #4, #6 to #11). F0002-A0001 proposed F0002-S0004 "one forbidden-import check and the guide repaired". It stays in `backlog/` on `main`, unbuilt, by the demo's rule.
- **Interventions:** none on the baseline. The hand fix as root at 23:53 local was inside `self`, not `baseline`.
- **Hours waited** (handed over at approval → merge or close), per item in minutes:

  | S0001 | S0002 | S0003 | S0004 | F0001-A0001 | F0002-S0001 | F0002-S0002 | F0002-S0003 | F0002-A0001 | F0003-S0001 | F0003-A0001 |
  | -: | -: | -: | -: | -: | -: | -: | -: | -: | -: | -: |
  | 6.7 | 1.8 | 2.7 | 0.5 | 4.0 | 3.2 | 1.5 | 2.9 | 2.1 | 2.4 | 0.1 |

  The first four are F0001's stories. Total: 27.9 min (0.47 h).

## 7. Stops

None.

- `factory.log` holds only the four disk lines and the preflight's login line.
- `health.json` lists no stop, and no work item was blocked.
- No `factory/stops.jsonl` exists on the target's `main`, which is consistent with no stop.
- One closed pull request (#5, the refusal) carried the human's comment.

## 8. Disk

| Measure | Start (20:04 to 20:05 UTC) | End | Growth | Bound | Verdict |
| :- | :- | :- | :- | :- | :- |
| Host C: free | 254 GB | 251 GB (22:16 UTC, at report time, `self` running) | −3 GB | none | recorded |
| `docker_data.vhdx` | 69,050,826,752 B | 70,795,657,216 B (22:16 UTC) | +1,744,830,464 B (1.74 GB) | +5 GB beyond the build | **met** |
| `docker system df` images / volumes / build cache | 26.32 / 14.67 / 14.29 GB | 26.38 / 15.2 / 14.35 GB (22:16 UTC) | +0.06 / +0.53 / +0.06 GB | none | recorded |
| Container `/tmp` | 8 K, 3 entries (session) | the factory's record: 0 B used at 22:06 UTC; the session's end exec not taken (container stopped) | about 0 | +100 MB | **met** (from the factory's record) |
| Container `/work` | 700 K (session) | 0.5 GB (the factory's record: 500,498,476 B at 22:06 UTC; `du` of the volume 499 M at 22:16) | about +0.5 GB | +2 GB | **met** |
| Container `/state` | 28 K (session) | 42,142 B (the factory's record), `du` 68 K | +40 K | none | recorded |
| Shared Docker disk behind `/work` | 971.56 GB free (the factory's record, 20:04:28) | 970.42 GB free (22:06:31; the factory's line "/work 970.4 GB free, 0.5 GB used"); `df` 52 GB used of 1007 G | −1.14 GB free | none | recorded |

Notes:

- The factory's own records are `start` at 20:04:28 and `acceptance` at 20:55:16, 21:46:31 and 22:06:31 UTC. In the factory's records, `/work` used went 0 → 493,859,068 → 500,206,057 → 500,498,476 B.
- F0001-A0001's reviewer explained the jump: `/work` grew 0.4 GB, which is the checkout's `.venv` (482 MB). No growth is unexplained.
- **(judgement)** The host and Docker growth also contains `self`'s work in the same two hours, so 1.74 GB is an upper bound on the baseline's share.
- Not taken: the plan's separate record after `up --build` (the start record came after the build); and the session's end records, host and container, at the last archive. The end host numbers above are this helper's, taken six minutes after the container stopped.

## 9. Project commands

83 records in `project-commands.jsonl`, from 20:04:40 to 22:11 UTC.

| Command | Count | Total s | Mean s | Status |
| :- | -: | -: | -: | :- |
| `check` | 20 | 154.7 | 7.7 | 20 passed |
| `test` | 12 | 40.5 | 3.4 | 8 failed (the tester's red tests, as intended), 4 passed |
| `lint` | 39 | 10.8 | 0.3 | 39 passed |
| `duplicates` | 12 | 19.3 | 1.6 | 12 passed |

| Target (inside the commands) | Count | Total s | Mean s |
| :- | -: | -: | -: |
| lint | 59 | 8.9 | 0.2 |
| test | 24 | 85.0 | 3.5 |
| types | 20 | 28.4 | 1.4 |
| sast | 20 | 38.1 | 1.9 |
| secrets | 20 | 5.1 | 0.3 |
| layers | 20 | 2.1 | 0.1 |
| licenses | 20 | 2.1 | 0.1 |

- **`make check` per commit:** 20 commits, each checked exactly once.
- **The F0023 lever:** the demo did not opt in to `not_read`. **(judgement)** By the stage sequence, 8 of the 20 checks are the docs stage's, one per story, on commits that changed only `README.md` and `docs/`. With `not_read` they could have been reused: about 8 × 7.7 s = 1 min of start-to-archive over the run, and no agent minutes.
- `known-results.jsonl` holds 56 records, although the demo did not opt in.

## 10. Findings

Proposed only; nothing was fixed.

1. **F0003-S0001 "title search" over the minutes cap by 3.2 s** (2.93 against a cap of 2.875; +27.3 %).
   - Where: machine. `self` ran beside the baseline, and the extra time sits in the intake and tests stages.
   - Proposed **(judgement)**: re-measure the minutes of the compared stories with `self` stopped, as Q5 intended, before calling it a regression. Also record model minutes beside agent minutes in the yardstick, as they move less with the host's load.
2. **F0001-A0001 refused: the committed OpenAPI schema contradicts the error body.**
   - Where: demo and agents. F0001-S0003 "HTTP API" pins `{"detail": ...}` as the only key (criterion 20) and pins that the schema is current (criterion 21), but no criterion pins what the schema says about errors; neither the reviewer nor the documenter caught it.
   - Run 4 needed an extra story on the same edge (F0001-S0005 "API error contract edges" in v1's demo).
   - Proposed: the demo's F0001-S0003 text gains a criterion that the schema declares the 404 and the `{"detail": str}` body. Or the proposed F0001-S0005 "the OpenAPI schema states the error body" is built in a later run.
3. **A refused acceptance's proposed stories never reach `main`.**
   - Where: engine. F0001-S0005 to S0008 lie only on the closed branch `work-item/F0001-A0001`.
   - **(judgement)** This may be intended, so check it against the decision log. If not, a story should keep a refused acceptance's proposals in `backlog/` on `main`.
4. **Four of eight stories took one review round each, against three first-pass in run 4 among them.** The comparison set shrank from five stories to two.
   - Where: agents (tester and coder). The causes: an unpinned order (F0001-S0002 "service layer with filtering"), a renamed earlier test from a blind replace (F0001-S0004 "SQLite repository and persistence switch"), an unneeded `noqa` (F0002-S0002 "version command"), and copied test helpers (F0002-S0003 "to-do statistics").
   - **(judgement)** Two of them, the blind replace and the copied helpers, are standing-leave mistakes the tester could catch itself. A round also costs four extra runs (doing, tests, doing, review), which is worth a look in the pipeline definition (`doing: next [review, tests]`).
5. **`self` was not stopped.**
   - Where: operator, by the human's choice. The plan's Q5 had `self` stopped.
   - It skews the minutes and the host disk growth, but not the cost.
   - Proposed: the next measured run follows Q5.
6. **The run log and the data copies of plan section 3 were not made.**
   - Where: operator. `docs/runs/<date>-baseline-todo/run-log.md` does not exist; the night log's "Baseline" rows stand in for it. There are no heartbeat rows, no session-side end disk record, and no copied `costs.jsonl`, `disk.jsonl`, `project-commands.jsonl` or G2 counts in this folder.
   - Proposed: copy them read-only now, while the `factory-baseline` volumes still exist. (Done by the operator after the report: `data/` holds `factory.log`, `health.json`, `disk.jsonl`, `known-results.jsonl` and `project-commands.jsonl`; the `.costs.jsonl` sidecars stay in the target repository.)
7. **A denial without a path.**
   - Where: engine or runtime record. F0002-A0001's cost record has `denials: 1` and `denied_paths: []`.
   - Proposed: find out what was refused, and a story so that every denial names what it refused.
8. **The acceptance reviewers still ran `make mutants`** (F0001 224/231, F0002 101/104, F0003 41/41 on a fresh run outside the checkout, after the cached `mutants/` gave stale survivors). F0001-A0001 took 9.56 min against run 4's 5.03.
   - Where: agent (acceptance reviewer), as tagged.
   - **(judgement)** Already taken up on `factory-rf` after the tag (F0031 "no stage runs mutation testing", F0032 "mutation testing keeps only its sweep form"). There is no new story, but the acceptances' minutes are not a yardstick for later runs without `make mutants`.
9. **`docs/decisions.md` is missing in the target after all three features**, which each acceptance noted.
   - Where: demo or agent (documenter).
   - Proposed: check whether the demo's docs criteria name it; if they do, the documenter misses it.
10. **G2 counts are lines, not messages.**
    - Where: the plan's method.
    - Proposed: count by message id, so that a later run's counts compare with run 4's 429 and 100.

## 11. For later changes

The yardstick every later change of v1.1 is measured against, from this run on Claude Code 2.1.296, the subscription, Docker Desktop, with `self` running beside it:

- **Compared stories:**
  - F0001-S0003 "HTTP API": 6 runs, $1.456, 4.52 agent min (4.13 model min);
  - F0003-S0001 "title search": 6 runs, $0.921, 2.93 agent min (2.51 model min);
  - sum $2.377, 7.44 agent min.
- **Other first-pass stories:**
  - F0001-S0001 "domain model and in-memory repository": 6 runs, $1.193, 3.60 min;
  - F0002-S0001 "health endpoint": 6 runs, $0.935, 2.80 min.
- **Stories with a round:**
  - F0001-S0002 "service layer with filtering": 10 runs, $1.571, 4.56 min;
  - F0001-S0004 "SQLite repository and persistence switch": 10 runs, $1.950, 5.71 min;
  - F0002-S0002 "version command": 10 runs, $1.186, 3.48 min;
  - F0002-S0003 "to-do statistics": 10 runs, $1.798, 5.17 min.
- **Acceptances (with `make mutants`):**
  - F0001-A0001: $2.544, 9.56 min (refused);
  - F0002-A0001: $1.594, 4.96 min;
  - F0003-A0001: $0.950, 3.77 min.
- **Totals:**
  - F0001 "the to-do service": 33 runs, $8.713, 27.95 min;
  - F0002 "operations": 27 runs, $5.512, 16.41 min;
  - F0003 "search": 7 runs, $1.871, 6.69 min;
  - **run: 67 runs, $16.096, 51.05 agent min, 43.87 model min, 2 h 06 min from first start to last archive, 0 questions, 4 rounds, 0 stops, 1 refusal.**
- **Per stage over the compared stories:** see section 5.
- **Disk growth:** `/work` +0.5 GB, `/tmp` 0, `/state` +40 K, `docker_data.vhdx` +1.74 GB (with `self`'s work included).
- **Project commands:** 20 `make check` runs at 7.7 s mean, one per commit.
