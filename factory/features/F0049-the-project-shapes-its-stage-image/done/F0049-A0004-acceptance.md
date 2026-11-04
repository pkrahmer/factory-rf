---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 537
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-04T03:36:28.344745Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-04T03:41:21.175401Z'
  stage: acceptance
  run: bf4bca22fc764869abf73deedde313c5
- number: 3
  speaker: factory
  kind: done
  at: '2026-11-04T03:43:19.491049Z'
  stage: done
stories: [F0049-S0001, F0049-S0002, F0049-S0003, F0049-S0004, F0049-S0005, F0049-S0006, F0049-S0007, F0049-S0008]
outcome: accepted
---

# Acceptance of The project shapes its stage image

## Recommendation

**accepted.** The feature does what `feature.md` promised. Its smoke test is green end to end through eleven changes on `main`, and `make check` is green. S0008 closed the one gap the third acceptance (A0003) left: the 2026-11-01 decision on Debian's packages now points to the F0049 entry that superseded it. The human's live check after A0003 recorded `opencode` 1.19.3 beside `claude` 2.1.296 and no `node`, which was the last item on record as open. No story is proposed. The items noticed and still open are older than the feature or belong to the pipeline definition, and the human has seen each of them in an earlier acceptance.

## 1 Scope

Every scope item has its story, and no story goes beyond the scope. Since A0003 the repository changed in only two places outside `factory/`: one line in `docs/decisions.md` (S0008) and three lines in the human's night log (`git diff --stat 8223d2047 HEAD -- . ':!factory'`). No code changed.

- **The base image (S0001).** `vm/Dockerfile` installs six Debian packages. Node 22 is pinned and checked into `/opt/factory/node`, and the runtimes are installed under `/opt/factory`. The wrappers exec `/opt/factory/bin/<runtime>` (decision 6).
- **The project's layer (S0002).** The rule and the identity live in `src/factory/domain/stage_layer.py`. The build goes through `Images` / `PodmanImages` (`src/factory/adapters/podman_images.py`), with an empty context, `--network=host`, the `-project` tag and `image prune -f`. The image is chosen in one place, `project_image_settings` (`src/factory/entry/wiring.py:395`). `Boundaries.image_path` carries the image's `PATH` to the sync, the checks and the agent.
- **The rebuild (S0003, with S0004's repair).** The path is `_ProjectImageStart.prepare` → `_follow_main` → `_choose` (`src/factory/entry/run.py`). A failed fetch stands as `fetch_failed`, and nothing is built during the outage.
- **The follow-up stories** S0005 to S0008 stayed inside the scope. S0005, S0007 and S0008 changed documents only, and S0006 changed tests only.
- **The goal**, "a changed file on `main` is rebuilt by the factory itself … a new image identity makes the preflight and the reuse of passed checks start afresh", holds (see 2).
- **On the real machine.** The human's check (e) on factory-vm (night log 03:13Z) built the ESP32 template's stage file on `factory-stage:vm`, and `make check` ran green in the project image. The live check after A0003 (night log 03:26Z) records `claude` 2.1.296, `opencode` 1.19.3 and no `node`. That closes the one detail A0003 left for the human to confirm.
- **Out of scope** was respected: there is no project's stage file in this repository, one image serves every stage, the build context is empty, and there is no registry.

## 2 The feature's smoke test

The walk-through follows an operator whose project needs more tools, from a fresh `factory-run` on a `main` with no stage file. After each iteration it reads `factory-health`, then makes the next change on the remote:

1. Merge the operator guide's template.
2. Merge an unrelated commit.
3. Merge a layer that puts a JDK on its `PATH`.
4. The remote becomes unreachable.
5. During the outage, `main` changes the layer to a Node of the project's own.
6. The remote is reachable again.
7. Merge a file that breaks the rule.
8. Merge an unrelated commit that leaves the broken file as it is.
9. Merge a file whose build fails.
10. Merge a file whose build reaches its time limit.
11. Merge the removal of the file.

The real entry points:

- `run_instance`, with no `images` replacement, so `build_images(settings)` wires the real `PodmanImages`.
- A real bare remote (`make_remote`). The human's clone (`HumanClone`) pushes to it, and the remote is renamed away and back for the outage.
- `factory.entry.health.main`, which is `factory-health`.

The stand-ins:

- A `podman` script. It records its calls and the build context's entries. For a file marked `FAIL` it prints 25 lines and exits 1; for one marked `SLOW` it sleeps 30 s. It answers `image inspect` with the `PATH` from the file's `ENV PATH`, or with `null`.
- A recording tick in place of `build_tick`, which prints the image, the identity and the `PATH` a stage would run in.

`IMAGE_BUILD_TIME_LIMIT` was set to 2 s in `factory.entry.wiring`. No real container ran, because the stage container has no podman.

The script was written anew for this acceptance; A0003's was lost with its stage. It ran from a `mktemp -d` folder, which was removed afterwards, and `run_instance`'s files went to a `tempfile.TemporaryDirectory`.

```
$ uv run python $d/feature_smoke.py $d/podman 2>&1 | grep -v Bytecode
start of factory-run on a main without a stage file; base identity sha256-base
2026-11-04T03:39:29Z disk start: /tmp/tmp9rmj2wq6 23.6 GB free, 0.0 GB used; /tmp/tmp9rmj2wq6/state 23.6 GB free, 0.0 GB used
  stage ran in image=factory-stage:1 identity=sha256-base PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (the start): exit 0: healthy
human/world: merge the operator guide's template (build-essential, cmake)
2026-11-04T03:39:29Z stage image: built sha256-base+20733148ba61 at 7c9de50809b4 in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+20733148ba61 PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (merge the operator guide's template (build-essential, cmake)): exit 0: healthy
human/world: merge an unrelated commit
  stage ran in image=factory-stage:1-project identity=sha256-base+20733148ba61 PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (merge an unrelated commit): exit 0: healthy
human/world: merge a layer that adds a JDK to its PATH
2026-11-04T03:39:29Z stage image: built sha256-base+6cf3b4c658c1 at cc577daee3fc in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+6cf3b4c658c1 PATH=/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin
  factory-health (merge a layer that adds a JDK to its PATH): exit 0: healthy
human/world: the remote becomes unreachable
2026-11-04T03:39:29Z stop repository fetch_failed: git fetch --prune origin failed (exit 128): fatal: '/tmp/tmp9rmj2wq6/origin/remote.git' does not appear to be a git repository
2026-11-04T03:39:29Z fatal: Could not read from remote repository.
2026-11-04T03:39:29Z 
2026-11-04T03:39:29Z Please make sure you have the correct access rights
2026-11-04T03:39:29Z and the repository exists.
  factory-health (the remote becomes unreachable): exit 1: fetch_failed (repository): git fetch --prune origin failed (exit 128): fatal: '/tmp/tmp9rmj2wq6/origin/remote.git' does not appear to be a git repository
    | fatal: Could not read from remote repository.
    | 
    | Please make sure you have the correct access rights
human/world: main changes the layer to a Node of its own during the outage
2026-11-04T03:39:29Z stop repository fetch_failed: git fetch --prune origin failed (exit 128): fatal: '/tmp/tmp9rmj2wq6/origin/remote.git' does not appear to be a git repository
[... the same four continuation lines ...]
  factory-health (main changes the layer to a Node of its own during the outage): exit 1: fetch_failed (repository): git fetch --prune origin failed (exit 128): fatal: '/tmp/tmp9rmj2wq6/origin/remote.git' does not appear to be a git repository
    | fatal: Could not read from remote repository.
    | 
    | Please make sure you have the correct access rights
human/world: the remote is reachable again
2026-11-04T03:39:29Z stop cleared fetch_failed
2026-11-04T03:39:30Z stage image: built sha256-base+b824902e47b6 at 56b16b55f508 in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+b824902e47b6 PATH=/opt/node24/bin:/usr/local/bin:/usr/bin:/bin
  factory-health (the remote is reachable again): exit 0: healthy
human/world: merge a file that breaks the rule
2026-11-04T03:39:30Z stage image: failed at 12a182fcccde
2026-11-04T03:39:30Z stop machine stage_image_failed: at 12a182fcccde: the FROM must be FROM ${FACTORY_BASE} alone: FROM debian:bookworm
  factory-health (merge a file that breaks the rule): exit 1: stage_image_failed (machine): at 12a182fcccde: the FROM must be FROM ${FACTORY_BASE} alone: FROM debian:bookworm (since 2026-11-04T03:39:30Z)
human/world: merge an unrelated commit that leaves the broken file
  factory-health (merge an unrelated commit that leaves the broken file): exit 1: stage_image_failed (machine): at 12a182fcccde: the FROM must be FROM ${FACTORY_BASE} alone: FROM debian:bookworm (since 2026-11-04T03:39:30Z)
human/world: merge a file whose build fails
2026-11-04T03:39:30Z stage image: failed at e3725445f32c
2026-11-04T03:39:30Z stop machine stage_image_failed: at e3725445f32c: the stage file did not build in 1 s:
2026-11-04T03:39:30Z step line 6
[... "step line 7" to "step line 24", one log line each ...]
2026-11-04T03:39:30Z step line 25
  factory-health (merge a file whose build fails): exit 1: stage_image_failed (machine): at e3725445f32c: the stage file did not build in 1 s:
    | step line 6
    | step line 7
    | step line 8
human/world: merge a file whose build reaches its time limit
2026-11-04T03:39:32Z stage image: failed at 19f8f1fa32e2
2026-11-04T03:39:32Z stop machine stage_image_failed: at 19f8f1fa32e2: the stage file did not build in 3 s:
2026-11-04T03:39:32Z container command /tmp/f0049-a4-WkrH/podman build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f /tmp/factory-stage-file-l9hcxfyw/Containerfile /tmp/factory-stage-file-l9hcxfyw/context failed: no end within 2 s
  factory-health (merge a file whose build reaches its time limit): exit 1: stage_image_failed (machine): at 19f8f1fa32e2: the stage file did not build in 3 s:
    | container command /tmp/f0049-a4-WkrH/podman build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f /tmp/factory-stage-file-l9hcxfyw/Containerfile /tmp/factory-stage-file-l9hcxfyw/context failed: no end within 2 s (since 2026-11-04T03:39:32Z)
human/world: merge the removal of the file
2026-11-04T03:39:32Z stop cleared stage_image_failed
2026-11-04T03:39:32Z stage image: back to the base at defa733671c9
  stage ran in image=factory-stage:1 identity=sha256-base PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (merge the removal of the file): exit 0: healthy
factory log, stage image lines:
  stage image: built sha256-base+20733148ba61 at 7c9de50809b4 in 1 s
  stage image: built sha256-base+6cf3b4c658c1 at cc577daee3fc in 1 s
  stage image: built sha256-base+b824902e47b6 at 56b16b55f508 in 1 s
  stage image: failed at 12a182fcccde
  stage image: failed at e3725445f32c
  stage image: failed at 19f8f1fa32e2
  stage image: back to the base at defa733671c9
factory-stage-file-* folders left: 0
podman calls:
image inspect --format {{json .Config.Env}} factory-stage:1
build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f | context entries: 0
image prune -f
image inspect --format {{json .Config.Env}} factory-stage:1-project
build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f | context entries: 0
image prune -f
image inspect --format {{json .Config.Env}} factory-stage:1-project
build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f | context entries: 0
image prune -f
image inspect --format {{json .Config.Env}} factory-stage:1-project
build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f | context entries: 0
image prune -f
build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f | context entries: 0
image inspect --format {{json .Config.Env}} factory-stage:1
```

Green. Checked against `feature.md` and `docs/operator-guide.md`, *The project's stage file*:

- **No stage file.** The base runs with the base's identity and the default `PATH`.
- **The template** builds to `sha256-base+20733148ba61`, the identity the operator guide gives as its example.
- **An unrelated commit** builds nothing and logs nothing.
- **A changed file** is rebuilt between stages. Its `ENV PATH` reaches the stage, and the identity changes.
- **A project's own Node** puts its `PATH` first. The factory's runtimes are not on that `PATH` to be shadowed (decision 2).
- **The outage.** A failed fetch stands as `fetch_failed`, `factory-health` exits 1, and no stage runs. Nothing is built, though `main` changed the file during the outage. The first fetch that passes clears the stop and builds the changed file once.
- **A broken rule** stands as `stage_image_failed`. An unrelated commit that leaves the broken file as it is does not end the stop, and it builds nothing.
- **A failed build** gives its last 20 lines (6 to 25). **A timed-out build** gives podman's `no end within <s> s` and no build output, and no prune follows it.
- **The removal** clears the stop and returns to the base, with the line `back to the base`.
- **Every build** has an empty context, `--network=host` and the `-project` tag, and leaves no `factory-stage-file-*` folder behind.

`make check` was green as found: `test: green (86.7 s)`, coverage 99.52 %, `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

The only story since A0003 is S0008. Its coder wrote "Noticed, not touched: nothing", and its documenter saw no stale text. The reviewer and the smoke tester found nothing. One thing is new:

- **A docs-only story stopped for the human on whether to test a document line.** S0008's tester asked (entry 5) whether criterion 1 needs a grep-style test, because the Description ruled out test changes. The human answered (a), no test. The coder and the reviewer again had nothing to do. This is the pattern A0002 and A0003 named for S0005 to S0007: four stages with nothing to do for a docs-only story, here with a question added. It belongs to the pipeline definition and the story form (`factory/`), which are the human's. No story; listed under 6.

**Still open from A0001 to A0003, each rechecked on `main` and each with no story then or now.** All of them are older than the feature or are test-tidiness items. No user is affected.

- Two fetches per iteration (the human said "later").
- `_project` exists twice with different signatures: `tests/entry/test_run_project_image_rebuild.py:309` and `tests/entry/test_run_fetch_before_tick.py:164`.
- `STAND_IN` is a variant of `PODMAN_SCRIPT`.
- `floating_references` misses npm called by its full path.
- The 12-digit commit is sliced inline in several modules: `dispatcher.py:128`, `post_texts.py:100`, `checks.py:107`, and `wiring.py:387` through a named constant.
- The disk check does not run while a stop holds the tick.
- During an outage, the log repeats the `fetch_failed` stop's five lines on every iteration (seen again in 2).

## 5 The documentation as a whole

S0008's line holds. *Debian's packages follow the base image's release* (`docs/decisions.md:1306`) now ends with `- Superseded in part by "The factory's tools live apart, under `/opt/factory`, with their own Node": …` (`:1315`), and the later entry (`:1456`) says the same from its side. The only remaining mentions of `nodejs` or of seven packages in `README.md` and `docs/` are that superseded entry's own record (`:1310`, `:1313`) and the operator guide's nodejs.org download (`:497`), and both are correct.

`README.md`'s sentence on the stage file (`:24`) sends the newcomer to the right section. The operator guide's *The project's stage file* (`:509-568`) matched the smoke test's output line for line: the log lines, the details of the stop, the identity example, the `PATH` and the time-limit text. The stops table row (`:1608`) agrees with it. `uv run python -m factory.entry.check_documents` prints `documents ok`. No contradiction, no missing section and no stale example.

## 6 Decisions taken for the human

**From `feature.md`, decisions 1 to 9:**

1. A Containerfile and not a package list.
2. The factory's tools apart.
3. One image, named in one place.
4. An empty build context.
5. Rebuild by hash between stages.
6. The runtimes exec'd without Node.
7. The leave in `tests/entry/test_health.py`.
8. The checks take the image's `PATH`, and four more leaves for S0002.
9. S0006's inspect `null` row confirmed.

**The human's answers in the journals.** S0001 to S0007 and A0001's (a) to (e) are as A0002 and A0003 listed them. New since A0003:

- **S0008, entry 6:** (a), no test for a decision-log line. The smoke test and the reviewer check it.
- **A0003's open detail, `opencode --version`:** confirmed by the human's live check (night log 03:26Z, opencode 1.19.3). Nothing is left open.

**Defaults the agents took without asking, new since A0003:**

- S0008 coder: left the line to the documenter, by `CLAUDE.md` *Docs*.
- S0008 documenter: wrote no `Rejected:` line for the addition, because the story named none.

A0002's list stands for the rest. For instance, `image prune -f` prunes every dangling image of the user, and a removed stage file leaves the last `-project` image tagged.

**For the human to consider, outside this feature:** docs-only follow-up stories run a tester, a coder and a reviewer with nothing to do (S0005 to S0008). S0008's tester also needed a question to learn that a document line gets no test. A rule in the story form or the tester's role saying that "the story changes documents only" means no test would have saved a stop. This is `factory/` business and the human's own.

**Earlier tests changed, each with its leave.** S0008 changed no test. S0001 to S0006 are as A0001 and A0002 listed them, every one with a leave named. No earlier test was changed with no leave named.

## 7 The slow checks

The project offers no image scan or SBOM target. `make mutants` is not run here (check 3).

**`make duplicates`** (a record, not a check): `duplicates: 0 new, 43 known, 0 gone`.

**Test times**, from `.reports/junit.xml`: 8749 tests, 730.7 s summed across workers, 86.7 s of wall time.

- The feature's tests (the 283 cases whose names hold `image`, `stage_layer` or `fetch_before`) take 21.4 s together.
- The slowest of them is `tests/adapters/test_podman_images.py::test_a_build_that_reaches_its_time_limit_has_not_passed`, at 10.0 s, which is `ROOMY_LIMIT` by design. Next is `test_podman_runs_results::test_image_exists_reads_podman_s_exit_status[time-limit]`, at 1.5 s.
- The suite's slowest tests are older 10 s time-limit tests: `test_podman_timeout_status` (two rows), `test_claude_runtime_provider_limit`, `test_opencode_events` and `test_claude_runtime_resume`.

**Disk.** Now `/srv/factory/vm` has 23.6 GB free and 1.3 GB used. At the previous record (`disk acceptance`, A0003's) it had 23.7 GB free and 1.3 GB used. `/srv/factory/vm/state` and `/tmp` show the same 0.1 GB less free space, with 0.0 GB used. The factory's used space is unchanged, so the 0.1 GB less free space lies outside the factory's directories, on the shared filesystem. In between ran S0008 (one document line), A0003 and this stage's `make check`. No growth to name.

## 8 Cost

The stories cost 98 runs, 148.9 min, 917 turns and $34.83:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 22 | 22.6 | $6.60 |
| S0002 | 21 | 69.5 | $15.10 |
| S0003 | 16 | 27.7 | $5.86 |
| S0004 | 14 | 13.9 | $3.66 |
| S0005 | 6 | 3.5 | $0.86 |
| S0006 | 6 | 4.6 | $1.08 |
| S0007 | 6 | 3.3 | $0.82 |
| S0008 | 7 | 3.9 | $0.85 |

**S0002 stands out**: 43 % of the money and 47 % of the time. As A0001 said, its Interface named no seams, so it took 5 stops for the human and three review rounds whose findings were test rows.

**S0008**, a one-line document change, cost $0.85. Its seventh run was the tester's second, after the question. The five follow-up stories (S0004 to S0008) cost $7.27, 21 % of the feature. The acceptances come on top of the stories: A0001 cost $4.20, A0002 $2.48 and A0003 $1.76.

**Human interventions**: 12 questions answered (11 `question`, 1 `round_cap`), and the stories waited 0.4 h for them. By story:

- S0001: 1 question (entry 3) and the round cap (entry 40).
- S0002: 5 questions (entries 3, 8, 11, 16, 27).
- S0003: 2 questions (entries 3, 10).
- S0004: 2 questions (entries 3, 10).
- S0005 to S0007: none.
- S0008: 1 question (entry 5, whether to test a document line, about four minutes' wait).

S0002 needed the human most. Its Interface named neither the seams nor the earlier tests it would change, so the tester stopped twice and the coder stopped twice.

## Proposed stories

None. No finding of weight is left. The open noticed items (see 4) are older than the feature or are test-tidiness, and the human has left them without a story through three acceptances. The pipeline item under 6 is the human's own `factory/` business.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 0 stories proposed. The feature does what `feature.md` promised. S0008 closed the third acceptance's one gap in the decision log, and the human's live check now records opencode 1.19.3 beside claude 2.1.296, with no node.
   1 Scope: every scope item has its story, and no story goes beyond the scope. Since A0003, the only change outside `factory/` is S0008's one line in `docs/decisions.md` (plus the human's night log). No code changed. The goal holds on factory-vm through the human's checks (e) and 03:26Z.
   2 Feature smoke test: green, written anew because A0003's script went with its stage. It drove `run_instance` with the real `PodmanImages` on a stand-in `podman`, a real bare remote and `factory-health`, through eleven changes:
      - The base ran first. The template built to the operator guide's example identity, and an unrelated commit built nothing.
      - A JDK layer and then a project's own Node put their `PATH`s first.
      - During an outage, `fetch_failed` stood and nothing was built; recovery built the changed file once.
      - A broken rule raised `stage_image_failed`, and an unrelated commit did not end it. A failed build gave its last 20 lines, and a timed-out build gave podman's `no end within`.
      - Removing the file went back to the base.
      - Every build had an empty context, and no `factory-stage-file-*` folder was left.
      `make check` was green as found (99.52 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0008 noticed nothing. New: a docs-only story needed a tester question to learn that it gets no test; that is `factory/` business, so no story. A0001 to A0003's open items are rechecked and still stand with no story, all older than the feature or test-tidiness.
   5 Docs: S0008's `Superseded in part by` line holds, and `nodejs` and the seven packages appear only as the old entry's record. The operator guide matches the smoke test line for line. `documents ok`.
   6 Decisions: feature decisions 1 to 9; S0008's answer (a), no test for a document line; A0003's open opencode detail is confirmed by the human. For the human, outside the feature: docs-only stories still run a tester, coder and reviewer with nothing to do. S0008 changed no test, and every earlier test the feature changed had a leave named.
   7 Slow checks: none beyond `make check`. `make duplicates`: 0 new, 43 known. The feature's 283 tests take 21.4 s; the slowest is the 10 s build time-limit test (`ROOMY_LIMIT` by design). Disk: used space unchanged at 1.3 GB, and the 0.1 GB less free space lies outside the factory's directories. No growth to name.
   8 Cost: $34.83, 98 runs, 148.9 min. S0002 stands out at 43 % of the money, because its Interface named no seams; 5 of the 12 interventions were its own, and it needed the human most. S0008 cost $0.85 and asked 1 question. The follow-ups S0004 to S0008 cost $7.27 (21 %). 12 questions answered (11 question, 1 round_cap), 0.4 h waited.
3. factory: done (pull request merged); cost: 1 runs, 4.8 min, 30 turns, 81984 tokens in (1570684 more from cache), 20634 out, $1.38
