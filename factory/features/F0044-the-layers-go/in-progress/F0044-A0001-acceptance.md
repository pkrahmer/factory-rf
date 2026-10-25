---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 455
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-25T20:35:27.680068Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-25T20:45:53.187351Z'
  stage: acceptance
  run: 0eb26583b2ac42cdb660877b2f7fd45a
stories: [F0044-S0001, F0044-S0002, F0044-S0003, F0044-S0004, F0044-S0005, F0044-S0006, F0044-S0007, F0044-S0008, F0044-S0009, F0044-S0010, F0044-S0011]
outcome: null
---

# Acceptance of The layers go

## Recommendation

**Accepted with stories.** Every Scope item has a merged story. The feature's smoke test is green against the real entry points: the console scripts, the wiring, `factory-run`, and a whole tick on the container fakes in which the take leaves out what the role may not write. No stall reason and no stop reason names a removed layer. `make check` is green as found. Two findings are worth a story, and neither breaks a promise. Some names of the removed guard and seal survive on the code and the test helpers that replaced them (F0044-S0012). One operator-guide paragraph still gives the repair of the removed second user (F0044-S0013). Decision 27's line target is missed since `v1.1` (0.97 lines removed per line added) but met by this feature alone (3.3 to 1); decision 27 says that measure is reported, not a refusal.

## 1 Scope

None of weight. All eleven Scope items (S0001 to S0011) are in `done/` and merged, and the tree holds what their Descriptions promise:

- `src/factory` has one stage environment: `factory.application.stage_environment` defines `StageEnvironment` and `ContainerEnvironment` and nothing else.
- None of the twelve removed modules imports: `confine`, `landlock`, `confinement`, the two `leftovers`, `fresh_home`, `agent_home` ×2, `home_files`, `sealed_runs`, `undo`, `sessions`.
- `image/` is gone, and the credential helper is at `vm/git-credential-factory`.
- `tool_paths` is in none of the three pipeline definitions.
- The records contract is `3.0` (`factory.domain.contract.RECORDS_CONTRACT`).
- All seven agent files carry decision 4's R14, and the two agent texts of change 12 say "the take enforces".
- The suite's `boundaries` fixture and world run on `FakeSnapshots` and `FakeContainerRuns` (`tests/proof_support.py`, `tests/container_support.py::fake_dataset`).

A search of `src`, `template`, `claude`, `vm`, `Makefile` and `pyproject.toml` for the removed names finds only these, and each is allowed:

- `src/factory/application/recovery.py:97`: "leftovers" in its everyday sense.
- `InstanceSettings.agent_home`: kept by S0004 and decision 28.
- The default `/home/agent/.claude`: decision 28, left to F0045.

No story went outside the Scope.

Decision 27's measures, from `origin/main` after S0011 (`git diff --shortstat`):

| Path | since `v1.1` | F0044's eleven merges alone (sum of `merge^1..merge`) |
| --- | --- | --- |
| `src/factory` | +1804 −2361 | +285 −2642 |
| `tests` | +12305 −11921 | +4096 −12869 |
| `README.md` + `docs/` | +1345 −675 | +584 −987 |
| total | +15454 −14957 (0.97 removed per added) | +4965 −16498 (3.3 removed per added) |

The plan's target of three removed per one added is met by F0044 but not since `v1.1`. F0042 and F0043 count as the added part, and v1.1's own later features (F0039 and on) add to it. Reported, not a refusal.

- **Fast.** No run record exists at `v1.1`'s commit, so I ran both on this machine (`self`). At tag `v1.1`, in a temporary clone: `test: green (70.0 s)`. On this branch (`origin/main` plus the report): `test: green (61.1 s)`. The record nearest the tag (2026-10-21, F0039-S0010, 24 commits before it) says 61.7 s, and the runs of 2026-10-25 in `/state/records/project-commands.jsonl` range from 60.6 to 75.7 s. The suite is about as fast as at `v1.1`, a little faster on the same machine.
- **Clean.** The 18 values of `StallReason` and `RepositoryStopReason` include none that is `nested_repository` or names `seal`, `sudo`, `confine`, `leftovers`, `home`, `undo` or `inline` (step 3 of the smoke test). The criterion holds.

## 2 Feature smoke test

Green. The script (in a `mktemp -d` folder, run from the checkout with `tests/` on the path) does five things:

1. Lists the console scripts.
2. Imports every removed module.
3. Checks the reasons.
4. Builds the boundaries through `factory.entry.wiring.build_boundaries` without each of the three container settings, then with all three.
5. Runs a whole tick on the suite's world (`tests/proof_support.build_world`, container fakes): a story driven to `doing`, whose coder writes `src/smoke.py` (allowed), `docs/smoke.md` (the documenter's) and `factory/pipeline.yml` (protected).

```
$ uv run python "$d/feature_smoke.py"
1 console scripts: ['factory-bill', 'factory-check-story', 'factory-health', 'factory-run', 'factory-watch']
2 removed modules: none imports; environments in stage_environment: ['ContainerEnvironment', 'StageEnvironment']
3 reasons: 18 naming a removed layer: []
4 without dataset: FACTORY_DATASET: missing
4 without workspace: FACTORY_WORKSPACE: missing
4 without stage_image: FACTORY_STAGE_IMAGE: missing
4 with all three: ZfsSnapshots PodmanRuns RecordingProjectCommands
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
5 stage now: review
5 coder entry: coded the smoke | The factory left out changes outside the write paths: docs/smoke.md, factory/pipeline.yml. | `check`: true
5 on the branch: src/smoke.py True docs/smoke.md False pipeline.yml rewritten False
5 container runs of the fake: 3
feature smoke: green
```

The command line, with a token file and no `FACTORY_DATASET`, under `env -i`:

```
$ env -i PATH=… HOME=$d FACTORY_REPOSITORY_URL=/srv/none.git FACTORY_INSTANCE=smoke FACTORY_CHECKOUT=$d/checkout FACTORY_STATE_DIRECTORY=$d/state FACTORY_TOKEN_FILE=$d/tok FACTORY_WORKSPACE=$d/work FACTORY_STAGE_IMAGE=x .venv/bin/factory-run
2026-10-25T20:41:01Z settings invalid: FACTORY_DATASET: missing
exit 2
```

`make check` as found: `test: green (61.1 s)`, then `check: green` (7201 tests, 99.55 % branch coverage).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

These are collected from the coder, reviewer and documenter entries of the eleven stories, and checked against the tree now.

Settled since they were noticed:

- the `process.py` comment on `sudo` (S0005);
- `Layout.confine_bin` and the `CONFINE`/`LINE` constants (S0001);
- the `no_hook` rows (S0002);
- `tests/leftovers_runtime_support.py` (S0003);
- the `image/` entry in mutmut's `also_copy` (S0010);
- the duplicates baseline's `undo.py` entry (decision 39);
- "every recreated container has a fresh home" in the operator guide (S0004).

Still open:

- **The guard's and the seal's names on what replaced them.** `GuardSettings` (`factory.domain.agent_runs:74`) and its parameter `guard` in `factory.domain.write_paths.refusal`, `docs/project-guide/write-guard.md`, `tests/confine_support.py` and `tests/sealed_run_support.py`. Also `confine_support.Layout.temporary_root`, which no test reads since S0001 (S0001's reviewer left it to S0002, and nobody took it). Proposed as F0044-S0012.
- **`docs/operator-guide.md:1070`** still says "When an agent run left the path …" and "Repair with `chmod -R g+w <path>` as root". This is the second user's group layout (S0006's documenter, stale item 2), and S0011's name search could not find it. Proposed as F0044-S0013.
- **`CheckoutPreparer._log`** (`src/factory/application/scheduler.py:82`) is stored and never read (S0006). The human decided to keep the parameter (S0006, entry 14), so no story is proposed.
- **`read_hosting_token`** writes the literal `"missing"` beside the constant `_MISSING` (`src/factory/entry/wiring.py:187` against `:132`; S0008's coder). Too small for a story, so it is named here for the next story that touches the wiring.
- **The test literal and the walk loop.** `"stage environment: reset"` is a bare literal in `tests/test_suite_fixtures.py`, whose walk loop also repeats `drive` (S0007's reviewer). This is test hygiene that the tester can move under the standing leave. No story.
- **`FakeSnapshots` records no calls** (S0008). That would be a new capability, so it is out of F0044's scope and not proposed.
- **`make duplicates` (a record) now says `8 new, 35 known, 3 gone`.** The four similar-code pairs are lines that moved when the leftovers and the login state file went. The four dead-code findings are `FakeContainerRuns` and its `calls`, `FakeSnapshots`, and `MakeProjectCommands`, which only the tests use (decision 3). The three gone entries are the removed leftovers code. `security/duplicates-baseline.txt` is the human's, so the human refreshes it (see 6).
- **`pyproject.toml:15`** still says "The commands v1.1 installs". It is true, and it is the human's file.
- **`docs/operator-playbook.md`** still names `docker compose`, `image/secrets/` and the entrypoint umask (S0010's documenter). It is the human's playbook, and decision 15 keeps it as history.

## 5 The documentation as a whole

I read `README.md` from the top, the outline of `docs/operator-guide.md` and its *Configuration*, *The machine*, *The stops of the tick* and *Replaced in v1.2* sections, the project guide's index and `write-guard.md`, and the decision log's v1.2 entries. I also searched all of them for the removed names: `sudo -n -u`, `env -i`, `/home/agent`, `factory-work`, `2750`, `docker compose`, `compose.yml`, `entrypoint`, `image/`, `factory-confine`, Landlock, `InlineEnvironment`, `FACTORY_STAGE_ENVIRONMENT`, `UndoService`, seal.

- **One finding, F0044-S0013.** The `checkout_restore_failed` paragraph (`docs/operator-guide.md:1070`) contradicts the machine the rest of the guide describes. The guide says "There is one user, `factory`, and no second one" (`:286`), and that every agent call runs in a throwaway container. This paragraph still blames an agent run for the path and repairs it with the removed group's `chmod -R g+w`. An operator would be sent after a group that no longer exists, but the second repair it names, removal as root, still works, so the paragraph misleads without harming.
- **No other contradiction.** `README.md` points to *The machine* and *Replaced in v1.2* correctly. Its commands table matches the five console scripts the smoke test lists, and *Getting started* runs (`make check` ends `check: green`). The decision log's "Open: F0044 removes the Docker path" is followed by its "Done: F0044-S0010" line, so the history is closed as decision 15 asks.
- **Two small items, part of F0044-S0012.** The project guide's index names `confine_support.py` and `sealed_run_support.py` truthfully: they exist, under old names. `write-guard.md` is titled "The write paths and the take's rule", so only its file name is stale.
- **The `/home/agent/.claude` default** at `docs/operator-guide.md:64` is true of the code and is decision 28's, left to F0045.

## 6 Decisions taken for the human

These are from `feature.md` and the story journals, for the human to accept or revisit:

1. Split and order (decision 1): the guard as two stories, the leftovers and the home before the second user, the inline environment as two stories, the undo after the inline environment, the process table with the Docker path.
2. The runtimes keep `containers: ContainerRuns | None = None` and a direct call when it is `None`, for the some forty runtime tests on the host (decision 2). Option B, `containers` required, is still open as a later story.
3. `MakeProjectCommands` stays as the suite's project commands. No instance uses it, and `make duplicates` lists it as dead code (decision 3).
4. R14's new text, accepted by the human (decisions 4 and 29e).
5. The contract's major rises per narrowing story, to 2.0 at S0002 and 3.0 at S0006 (decisions 5 and 29d). The pipeline definition's own `contract` stays `1.0` (decision 31b).
6. `tests/confine_support.py` kept its shared helpers (decision 6). Its name is now F0044-S0012's.
7. `UV_COMPILE_BYTECODE` and `compile-bytecode` stay, with new comments (decision 8).
8. The suite's reach in S0007 was given as a broad leave (decision 29a), not the pre-check's list.
9. The three container settings keep their `None` defaults in the model, and `build_boundaries` refuses the first missing one (decision 10). Steps 4 and 5 of the smoke test confirm it.
10. The closing sentence reads `The factory left out changes outside the write paths: …` (decision 11). The smoke test confirms it.
11. The credential helper moved to `vm/`. `.gitignore` keeps `image/secrets/` (lines 15 and 16) until the human removes that folder everywhere (decision 12, change 10).
12. A layer's code was left without a caller between two stories (decision 13).
13. `left_branch` goes in F0045 with the contract's next major (decisions 14 and 29b).
14. History stays history (decision 15).
15. `opencode_item` narrowed (decision 16).
16. The defaults `/home/agent/.claude` and `/opt/factory/image-id` go in an F0045 story (decisions 28 and 29c).
17. The standing order of 2026-10-25 ("Decide for things that are actually not avoidable …") under which the pre-checks of S0007 to S0011 were decided (decisions 36 to 41). The human may want to read those five decisions again, since they were taken in their name.
18. `self` built S0009 to S0011 and this acceptance on its pre-S0008 image (decisions 37 and 41a). S0009's own entries may say "The factory undid …" (decision 38).
19. Answers in the journals:
    - S0001: entry 4 (a `sudo:` line without `os_user` is no refusal), entry 9 (the R14 text), entry 12 (`tool_paths` back on `main` while `self` still confined).
    - S0002: entry 12 (the `guard` updates dropped, the `no_hook` rows folded).
    - S0003: entries 6 and 11.
    - S0004: entry 4 (the `beneath_or_at` criterion).
    - S0005: entry 4 (run files under the process umask), entry 9.
    - S0006: entries 4, 9 (the one umask exemption) and 14 (`CheckoutPreparer` keeps `log`).
    - S0007: entries 8, 13 and 34 (one `fake_dataset`).
    - S0008: entries 4, 9, 16 (three inline-only stall tests deleted), 19 (the wiring tests check the `podman run` words, not a host run), 26 (the standing order's leave for findings 1 to 8) and 41 (the send-back for two `# noqa: SLF001` markers, fixed in round 2).
20. Still to do outside every write path:
    - The last bullet of change 10: remove `self`'s containers, volumes and image after this acceptance.
    - The refresh of `security/duplicates-baseline.txt` to the `8 new, 3 gone` above.
    - The leave of F0044-S0012's tests, which `feature.md` does not hold yet.

**Earlier tests changed.** Every reviewer's last entry names a leave for each earlier test the story changed or deleted:

- S0001: decision 17, plus the standing leave for `tests/shipped_agents.py`.
- S0002: decisions 18 and 31a, plus the human's entry 12.
- S0003: decision 19, plus entries 6 and 11.
- S0004: decision 20.
- S0005: decision 21, plus the standing leave for the moves to `tests/adapters/claude_stand_in.py`, `tests/conftest.py` and `tests/wiring_support.py`.
- S0006: decision 22, plus the standing leave for `RecordingRun`.
- S0007: decisions 23 and 29a.
- S0008: decisions 24 and 37, plus the human's entries 16, 26 and 41.
- S0009: decisions 25 and 38.
- S0010: decisions 26 and 40.
- S0011: none.

None was changed without a named leave. S0008's reviewer found three preflight modules changed without one (its finding 2). The human's entry 26 gave the leave before the merge.

## 7 The slow checks

- **Nothing to run.** The project offers nothing beyond `make check` but `make duplicates` (a record, reported under 4), `make documents` and `make mutants` (check 3).
- **The slowest tests** (`.reports/junit.xml`, 7201 tests) are the `ROOMY_LIMIT` tests at about 10 s each: `tests/adapters/test_podman_timeout_status.py` (two rows at the limit), `test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_process-group]`, `test_claude_runtime_resume.py`, `test_opencode_events.py` and `test_opencode_budget.py`. They wait by design.
- **Disk.**
  - At the start: `/work` 966.9 GB free, 0.5 GB used. Now: 966.3 GB free, 0.5 GB used.
  - `/state` and `/tmp` show the same free space and 0.0 GB used at both records, so the three share one pool.
  - The 0.6 GB less free space is not on `/work`, `/state` or `/tmp`, whose used space did not change. Nothing the feature changed explains it, and nothing in these mounts holds it.

## 8 Cost

- **Total.** 144 runs, 275.1 min, 1809 turns, 5.80 M tokens in (74.4 M more from cache), 0.82 M out, $68.13.
- **By story:**

  | Story | Runs | Minutes | Dollars |
  | --- | --- | --- | --- |
  | S0001 | 17 | 38.0 | 9.33 |
  | S0002 | 13 | 25.3 | 6.23 |
  | S0003 | 14 | 23.1 | 5.06 |
  | S0004 | 7 | 9.5 | 2.46 |
  | S0005 | 14 | 32.1 | 9.64 |
  | S0006 | 15 | 23.4 | 6.61 |
  | S0007 | 19 | 31.7 | 7.30 |
  | S0008 | 23 | 57.6 | 13.00 |
  | S0009 | 10 | 13.6 | 3.36 |
  | S0010 | 6 | 12.7 | 3.06 |
  | S0011 | 6 | 8.1 | 2.06 |

- **S0008 stands out.** It took 19 % of the money and 21 % of the minutes. Its journal says why: it was the widest removal (the inline environment, its setting and every wiring test that built it). The tester's adaptation came back three times for leaves, and the human sent it back at the approval for two `# noqa: SLF001` markers, which cost a second round of five stages.
- **Human interventions.** 20 questions answered, all of cause `question`, and 1.6 h waited:

  | Story | Answers |
  | --- | --- |
  | S0001 | 3 |
  | S0002 | 1 |
  | S0003 | 2 |
  | S0004 | 1 |
  | S0005 | 2 |
  | S0006 | 3 |
  | S0007 | 3 |
  | S0008 | 5, plus the send-back |
  | S0009 to S0011 | 0 |

- **S0008 needed the human most.** Most questions there were requests for leave on earlier tests that its pre-check's list had not named (entries 9, 16 and 26). Entry 19 was a design question: whether the wiring tests should run the container's words on the host.
- **Tests and leaves.** Across the feature the questions were mostly leaves for earlier tests found after a pre-check. Decision 29f made each of them need the human's word again. S0009 to S0011, decided under the standing order, needed none.

## Proposed stories

- `backlog/F0044-S0012-the-write-paths-and-the-test-helpers-lose-the-removed-layers-names.md`: `GuardSettings` becomes `WritePathSettings` (and `refusal`'s `guard` becomes `settings`), `write-guard.md` becomes `write-paths.md`, `confine_support.py` and `sealed_run_support.py` become `run_layout_support.py` and `agent_run_support.py`, and the unread `Layout.temporary_root` goes. These are the removed layers' names that are left on what replaced them. The behaviour is unchanged, and it needs the human's leave for the tests it names.
- `backlog/F0044-S0013-the-restore-stop-s-repair-names-the-one-user.md`: the operator guide's `checkout_restore_failed` paragraph loses the second user's `chmod -R g+w` and the agent run that can no longer leave a path in the checkout. It is a documents-only story.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 2 stories proposed
   1 Scope: all eleven Scope items are merged and present in the tree. `src/factory` has one stage environment (`ContainerEnvironment`), and none of the twelve removed modules imports. The records contract is 3.0, and all seven agent files carry R14. No stall or stop reason names a removed layer. Decision 27's lines: 0.97 removed per added since `v1.1`, below the 3 to 1 target; F0044's merges alone remove 3.3 per added (+4965 −16498). Suite at `v1.1`: 70.0 s; now: 61.1 s, on the same machine.
   2 Feature smoke test: green. It checked the console scripts, that the removed modules no longer import and the reasons. `build_boundaries` refuses each missing container setting and builds ZFS and Podman with all three. `factory-run` without `FACTORY_DATASET` exits 2. A whole tick on the container fakes takes `src/smoke.py` and leaves out `docs/smoke.md` and `factory/pipeline.yml` with the new closing sentence. `make check` is green as found.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: seven items are settled. Still open: `GuardSettings`, `write-guard.md`, `confine_support.py` and `sealed_run_support.py` carry removed layers' names, and `Layout.temporary_root` is unread (F0044-S0012). `CheckoutPreparer._log` was kept by the human. A literal `"missing"` remains in the wiring. `make duplicates` says 8 new, 3 gone; the baseline is the human's to refresh.
   5 Documentation: one contradiction. `docs/operator-guide.md:1070` repairs `checkout_restore_failed` with the removed group's `chmod -R g+w` and blames an agent run that can no longer write the checkout (F0044-S0013). Otherwise the documents match the code.
   6 Decisions: 20 for the human are listed, among them the standing order's decisions 36 to 41. Still to do: removing `self` after this acceptance, refreshing the duplicates baseline, and giving the leave for S0012's tests. Every earlier test was changed under a named leave.
   7 Slow checks: none beyond `make check`. The slowest tests are the about 10 s `ROOMY_LIMIT` tests. `/work` used is unchanged at 0.5 GB. Free space fell 0.6 GB in the shared pool, outside `/work`, `/state` and `/tmp`; the feature does not explain it.
   8 Cost: 144 runs, 275.1 min, $68.13. S0008 stands out at $13.00, 23 runs and 57.6 min: the widest removal, three requests for test leaves and a send-back at the approval for two `noqa` markers. 20 questions were answered, all of cause `question`, with 1.6 h waited; S0008 needed the human most (5 answers plus the send-back).
