---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 458
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-25T21:18:50.814875Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-25T21:24:02.853496Z'
  stage: acceptance
  run: b354818f5cd54dc890e5d2c1d5e87a4f
stories: [F0044-S0001, F0044-S0002, F0044-S0003, F0044-S0004, F0044-S0005, F0044-S0006, F0044-S0007, F0044-S0008, F0044-S0009, F0044-S0010, F0044-S0011, F0044-S0012, F0044-S0013]
outcome: null
---

# Acceptance of The layers go

## Recommendation

**Accepted.** All eleven Scope items and both stories the first acceptance proposed (S0012 and S0013, decision 42) are merged, and the tree holds what they promised. The feature's smoke test is green against the wiring and a whole tick on the container fakes, no stall reason or stop reason names a removed layer, and `make check` is green as found. One stale sentence on the preflight's probe ("a guard that gives no write path") and one on its nested repositories remain. They are noticed items, not a broken promise, and are proposed as one documents-only story (F0044-S0014).

## 1 Scope

None of weight. This is F0044's second acceptance. The first (F0044-A0001, `done/`) checked S0001 to S0011 item by item against the Scope. I checked that again against the tree now:

- `factory.application.stage_environment` holds `StageEnvironment` and `ContainerEnvironment` only.
- None of the twelve removed modules imports.
- `image/` is gone.
- The records contract is 3.0.
- The seven agent files carry decision 4's R14.
- The human's changes 1 to 9, 11 and 12 are on `main`. For example, `factory/pipeline.yml`'s `coder:` line holds `vm/*`, the `Makefile` and `pyproject.toml` comments are those of changes 7 and 10, and the tester's and the documenter's line 57 says "the take enforces".

The two stories since then:

- **S0012** renamed what the removed layers had left on what replaced them:
  - `GuardSettings` is now `WritePathSettings` (`src/factory/domain/agent_runs.py`).
  - `refusal`'s parameter `guard` is now `settings`.
  - `tests/confine_support.py` and `tests/sealed_run_support.py` are now `tests/run_layout_support.py` and `tests/agent_run_support.py`, and `Layout.temporary_root` is gone.
  - `docs/project-guide/write-guard.md` is now `write-paths.md`.
- **S0013** rewrote the operator guide's `checkout_restore_failed` paragraph (`docs/operator-guide.md:1070`) for the one user.

Neither went outside the Scope. A search of `src/factory` for the removed layers' names finds only the everyday "leftovers" at `src/factory/application/recovery.py:97`. The `/home/agent/.claude` default is decision 28's and left to F0045.

Decision 27's measures, from `origin/main` (`git diff --shortstat`):

| Path | since `v1.1` | F0044's thirteen merges alone |
| --- | --- | --- |
| `src/factory` | +1813 −2370 | — |
| `tests` | +12517 −12022 | — |
| `README.md` + `docs/` | +1399 −726 | — |
| total | +15729 −15118 (0.96 removed per added) | +5145 −16567 (3.2 removed per added) |

How the measures were taken:

- The feature's own column is A0001's eleven merges (+4965 −16498) plus #456 (S0012, +179 −68) and #457 (S0013, +1 −1).
- `docs/` includes the human's night logs under `docs/runs/`, which grew since A0001.
- The plan's target of three removed per added is met by the feature and not since `v1.1`. It is reported, not a refusal.

The other two measures:

- **Fast.** On `origin/main` the suite took 61.1 s (`test: green (61.1 s)`). At `v1.1` it took 70.0 s. That is A0001's run on this machine; I did not repeat it.
- **Clean.** None of the 18 values of `StallReason` and `RepositoryStopReason` is `nested_repository` or names `seal`, `sudo`, `confine`, `leftovers`, `home`, `undo` or `inline` (step 3 below). The criterion holds.

## 2 Feature smoke test

Green. The script ran in a `mktemp -d` folder that removed itself, from the checkout with `tests/` on the path. It does five things:

1. Lists the console scripts.
2. Imports the twelve removed modules, lists the environments of `stage_environment`, and checks S0012's names and that the old helper, guide and `image/` paths are gone.
3. Checks the reasons.
4. Calls `factory.entry.wiring.build_boundaries` without each of the three container settings, then with all three.
5. Runs a whole tick on the suite's world (`tests/proof_support.build_world`, on `FakeSnapshots` and `FakeContainerRuns`). A story is driven to `doing`, and its coder writes three files:
   - `src/smoke.py`, which the coder may write;
   - `docs/smoke.md`, which is the documenter's;
   - `factory/pipeline.yml`, which is protected.

```
$ uv run python "$d/feature_smoke.py"
1 console scripts: ['factory-bill', 'factory-check-story', 'factory-health', 'factory-run', 'factory-watch']
2 removed modules importable (12 tried): [] | environments: ['ContainerEnvironment', 'StageEnvironment']
2 names: WritePathSettings True GuardSettings False refusal ['path', 'settings']
2 old helper/doc/image paths present: []
3 reasons: 18 naming a removed layer: []
4 without dataset: FACTORY_DATASET: missing
4 without workspace: FACTORY_WORKSPACE: missing
4 without stage_image: FACTORY_STAGE_IMAGE: missing
4 with all three: ZfsSnapshots PodmanRuns RecordingProjectCommands
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
5 stage now: review
5 coder entry: 7. coder: coded the smoke | The factory left out changes outside the write paths: docs/smoke.md, factory/pipeline.yml.
5 on the branch: src/smoke.py True docs/smoke.md False pipeline.yml unchanged True
5 container runs of the fake: 3
feature smoke: green
```

`make check` as found ended `test: green (61.1 s)`, then `check: green`: 7215 tests, none failed, and 99.55 % branch coverage.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Settled since A0001:

- `GuardSettings`, `write-guard.md`, the two test helpers' names and `Layout.temporary_root` (S0012).
- The `chmod -R g+w` repair of `checkout_restore_failed` (S0013).

Still open:

- **The probe's paragraph** (`docs/operator-guide.md:701`) says the probe runs "with … a guard that gives no write path" (S0012's documenter, entry 19). `_probe_request` (`src/factory/application/preflight.py`) builds an `AgentRunRequest`, which has no write-path field, and the probe takes nothing. The project guide's bullet on `agent_run_probe_item` (`docs/project-guide/stage-environment.md:190`) still says that "the probe reports no fault for a nested repository", which denies a search that went with S0006. Both are proposed as F0044-S0014.
- **Three test modules named after removed layers** still check behaviour that exists: `tests/application/test_sealed_runs_runner.py` (the probe's provider limit), `tests/application/test_probe_nested_repository.py` and `tests/test_kernel_guard_removed.py`. S0012's Description left their renaming to the human, because renaming a test module another story wrote needs a leave. No story is proposed; it is for the human to want.
- **A one-off `make sast` segfault** (`Error 139`, `Makefile:51`) in S0012's coder run (entry 15). A rerun was green, and it did not come back in this acceptance's `make check`. It is a tool crash, recorded here in case it returns.
- **Open since A0001, unchanged:**
  - `CheckoutPreparer._log` is stored and unread (`src/factory/application/scheduler.py:82`). The human kept it.
  - The literal `"missing"` sits beside `_MISSING` in `read_hosting_token` (`src/factory/entry/wiring.py:187` against `:132`). It is for the next story that touches the wiring.
  - The bare `"stage environment: reset"` literal is still in `tests/test_suite_fixtures.py:79`. It is test hygiene under the standing leave.
  - `FakeSnapshots` records no calls. That would be a new capability, outside F0044.
  - `pyproject.toml:15`'s "The commands v1.1 installs".
  - The human's playbook names of the Docker path. Decision 15 keeps them as history.
- **`make duplicates`** (a record) still says `8 new, 35 known, 3 gone`, the same findings A0001 named:
  - four similar-code pairs;
  - `FakeContainerRuns` and its `calls`, `FakeSnapshots` and `MakeProjectCommands` as dead code (decision 3);
  - three gone leftovers entries.

  `security/duplicates-baseline.txt` was last changed for decision 39. Decision 42 has the human refresh it after S0013, which is now merged (see 6).

## 5 The documentation as a whole

I read `README.md` from the top. I read the operator guide's *Configuration*, *The machine*, the preflight items, *The probe of the agent run*, *The stops of the tick* and *Replaced in v1.2*, and the project guide's index, `write-paths.md` and `stage-environment.md` (*Who calls what*). I also searched `README.md`, the operator guide and the project guide for: guard, kernel, Landlock, the agent's user, second user, seal, re-clone, ignored paths, nested repository, long-lived, `/home/agent`, `sudo`, `env -i`, inline, undo, `docker` and compose.

- **One finding, F0044-S0014.** The probe's paragraph names a guard that no code builds. A reader who wants to know what the probe may write is pointed at a mechanism that is gone. The project guide's probe bullet denies a nested-repository fault that nothing checks any more. Neither breaks an operator's repair, so this is a repair of wording, not a contradiction that misleads a user into a wrong action.
- **No other contradiction.** S0013's paragraph matches `Tick._restore`: the stop is raised before any stage is dispatched, and no crash is recorded. The operator guide's "There is one user, `factory`" (`:286`) and *Replaced in v1.2* (`:1686` to `:1693`) agree with it. `README.md` points to *The machine* and *Replaced in v1.2*, and its five console commands match the smoke test's step 1. S0012 renamed `write-guard.md` to `write-paths.md`, and the index and every link follow it. The remaining "kernel" hits are the Linux kernel's ZFS module and the `uuid` file, and the remaining `sudo` hits are the host's root steps and the `--sudoers` fallback. All of them are true.
- **`docs/decisions.md`** keeps `GuardSettings` and the closed layers as history, as decision 15 and S0012's criterion 6 ask.

## 6 Decisions taken for the human

A0001's report (section 6, items 1 to 20) lists decisions 1 to 41 and the answers in S0001 to S0011's journals. They stand and are not repeated here. Since then:

1. **Decision 42.** S0012 and S0013 were proposed by A0001 and decided under the human's standing order of 2026-10-25. They were built on `self`'s pre-S0008 image without a pre-check, to spare the weekly budget. S0012's leave was given in decision 42, after a `grep` of every importer.
2. **S0012's tester extended a shared helper.** `tests/search_support.modules_matching` gained an optional `root` (default `TESTS`) under the standing leave for shared test helpers (entry 13), so that the new test would not copy it. The reviewer (entry 17) flagged it for the human: it extends the shared helper rather than only moving it there. Its three earlier callers are unchanged and check the same thing. It is for the human to accept, or to narrow the standing leave's wording.
3. **S0012's documenter departed from the letter of criterion 6** (entry 19). In `docs/project-guide/agents.md` and `stages.md` it removed the claims that `AgentRunRequest` and `TaskContext` carry the guard settings, instead of renaming them, because neither model has such a field.
4. **S0013's crash-cap sentence.** The documenter read `Tick._restore` and wrote that the stop records no crash (entry 11). The smoke tester confirmed it against `src/factory/application/tick.py:155-160`.
5. **Still to do outside every write path:**
   - change 10's last bullet: remove `self`'s containers, volumes and image after this acceptance, with the kept `compose.yml`, `FACTORY_INSTANCE=self` and `FACTORY_REPOSITORY_URL=unused` (decision 40);
   - the refresh of `security/duplicates-baseline.txt` to `8 new, 3 gone` (decision 42);
   - `.gitignore`'s `image/secrets/` lines (15 and 16), until that folder is removed by hand everywhere (decision 12).

**Earlier tests changed.** In S0012, every earlier test was changed under decision 42, as both reviewer entries list. `tests/search_support.py` was changed under the standing leave (item 2 above). S0013 changed no test. None was changed without a named leave.

## 7 The slow checks

- **Nothing to run.** The project offers nothing beyond `make check` but `make duplicates` (a record, under 4), `make documents` and `make mutants` (check 3).
- **The slowest tests** in `.reports/junit.xml` (7215 tests) are the `ROOMY_LIMIT` tests, which wait about 10.0 s each by design:
  - `tests/adapters/test_podman_timeout_status.py`, its two at-the-limit rows;
  - `test_opencode_resume_session.py`'s `timed-out-with-events` row;
  - `test_opencode_events.py`;
  - `test_claude_runtime_provider_limit.py`;
  - `test_make_commands.py::test_command_reaching_its_time_limit_is_killed`;
  - `test_claude_runtime_resume.py`;
  - `test_opencode_budget.py`.
- **Disk.**
  - At the previous record (occasion `acceptance`, A0001): `/work` 966.3 GB free, 0.5 GB used.
  - Now: `/work` 965.8 GB free, 0.5 GB used.
  - `/state` and `/tmp` show the same free space and 0.0 GB used at both records, so the three share one pool.
  - Free space fell another 0.5 GB while no mount's used space changed. S0012 and S0013 changed about 250 lines, which does not explain it. Like the 0.6 GB A0001 saw, it is outside these three mounts, most likely on the host that also holds `self`'s Docker image and logs.

## 8 Cost

- **Total.** 160 runs, 289.4 min, 1905 turns, 6.15 M tokens in (76.2 M more from cache), 0.85 M out, $71.37.
- **By story.** S0001 to S0011 are as A0001 reported: 144 runs, 275.1 min, $68.13. The two stories since then:

  | Story | Runs | Minutes | Dollars |
  | --- | --- | --- | --- |
  | S0012 | 10 | 10.2 | 2.45 |
  | S0013 | 6 | 4.1 | 0.79 |

  - S0012's ten runs are one review round. The reviewer found a copy of `search_support.modules_matching` in the new test, the tester folded it back, and the coder ran twice to hand the round on.
  - S0013 is a documents-only story at the six-run minimum.
- **S0008 still stands out.** It took $13.00, 23 runs and 57.6 min, 18 % of the money. It was the widest removal, with three requests for test leaves and a send-back at the approval for two `noqa` markers (A0001, section 8).
- **Human interventions.** 20 questions answered, all of cause `question`, with 1.6 h waited. These are the same as at A0001: S0012 and S0013 asked nothing, since decision 42 gave their leave before they started. S0008 needed the human most, with five answers plus the send-back. Most were leaves for earlier tests that its pre-check had not named (entries 9, 16 and 26), and one was a design question about the wiring tests (entry 19).

## Proposed stories

- `backlog/F0044-S0014-the-probe-s-descriptions-name-no-removed-layer.md`: the operator guide's probe paragraph loses "a guard that gives no write path", and the project guide's `agent_run_probe_item` bullet loses its nested-repository sentence. Both say instead that the probe takes nothing from the dataset. It is the last removed layer named in the documents of v1.2, and the story changes documents only.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 stories proposed
   1 Scope: all eleven Scope items and A0001's two stories are merged and present. S0012 renamed `GuardSettings` to `WritePathSettings`, `refusal(path, guard)` to `refusal(path, settings)`, the two test helpers and `write-paths.md`; S0013 rewrote the restore stop's repair for the one user. Since `v1.1`: +15729 −15118 (0.96 removed per added); F0044 alone: +5145 −16567 (3.2). Suite: 61.1 s now against 70.0 s at `v1.1` (A0001's run on this machine). No stall or stop reason names a removed layer.
   2 Feature smoke test: green. None of the twelve removed modules imports, and `ContainerEnvironment` is the only environment. S0012's names and paths are as promised. `build_boundaries` refuses each missing container setting and builds ZFS and Podman with all three. A whole tick on the container fakes takes `src/smoke.py` and leaves out `docs/smoke.md` and `factory/pipeline.yml`. `make check` is green as found: 7215 tests, 99.55 % coverage.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: still open are `docs/operator-guide.md:701`'s "a guard that gives no write path" (from S0012's documenter) and `stage-environment.md:190`'s nested-repository sentence (F0044-S0014). Also open: three test modules named after removed layers, left to the human; a one-off `make sast` segfault in S0012; A0001's small items, unchanged. `make duplicates` still says 8 new, 3 gone.
   5 Documentation: one wording finding, the probe's two passages (F0044-S0014). Otherwise S0013's paragraph matches `Tick._restore`, and `README.md`, the operator guide and the project guide agree with the code.
   6 Decisions: A0001's list stands. New since then: decision 42 (S0012 and S0013 under the standing order, with no pre-check). S0012's tester extended `search_support.modules_matching` under the standing leave, which the reviewer flagged for the human. S0012's documenter departed from criterion 6's letter in `agents.md` and `stages.md`. Still to do: remove `self` (change 10), refresh the duplicates baseline, and later the `image/secrets/` lines. Every earlier test was changed under a named leave.
   7 Slow checks: none beyond `make check`. The slowest tests are the 10 s `ROOMY_LIMIT` ones. `/work` used is unchanged at 0.5 GB; free space in the shared pool fell 0.5 GB since A0001, outside the three mounts, which the feature does not explain.
   8 Cost: 160 runs, 289.4 min, $71.37. S0012 cost $2.45 over 10 runs (one review round for a copied helper) and S0013 $0.79 over 6 runs. S0008 still stands out at $13.00. 20 questions were answered, all of cause `question`, with 1.6 h waited; none were in S0012 or S0013, and S0008 needed the human most.
