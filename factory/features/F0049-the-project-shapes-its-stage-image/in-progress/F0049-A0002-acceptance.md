---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 533
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-04T03:03:00.762025Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-04T03:09:50.176400Z'
  stage: acceptance
  run: f57f586d89454992b51616021d05cee8
stories: [F0049-S0001, F0049-S0002, F0049-S0003, F0049-S0004, F0049-S0005, F0049-S0006]
outcome: null
---

# Acceptance of The project shapes its stage image

## Recommendation

**accepted with stories.** The feature does what `feature.md` promised, and the three stories from the first acceptance (F0049-A0001) closed its findings. A fetch that fails before the tick now stands as `fetch_failed` in `factory-health`. The documents say what the code does and give the human's reasons. The tests share their helpers. The feature's smoke test below is green end to end: it ran through ten changes, an outage of the remote among them, and also covered a build cut off by its time limit. Two small documentation gaps remain, and neither breaks a promise. The stops table still tells the operator to restart `factory-run` after fixing the stage file, although no restart is needed. The project guide's index of shared test helpers does not list the support module and fixtures that S0004 added. One proposed story, F0049-S0007, repairs both. The one open item of weight is the human's own check of a real build on factory-vm, which is outside the factory (see 6).

## 1 Scope

Every scope item has its story, and no story goes beyond the scope. I checked the code each story names:

- **The base image (S0001).** `vm/Dockerfile` installs Node 22 pinned by version and SHA-256 into `/opt/factory/node`, and installs the runtimes under `--prefix /opt/factory`. The wrappers `exec /opt/factory/bin/<runtime> "$@"` (decision 6). The image keeps six Debian packages and no `node` or `npm` on the `PATH`. Unchanged since A0001.
- **The project's layer (S0002).** The rule is in `src/factory/domain/stage_layer.py`. The build goes through `Images` (`src/factory/application/images.py`) and `PodmanImages` (`src/factory/adapters/podman_images.py`: empty context, `--network=host`, `-project` tag, `image prune -f`). The one place that chooses the image is `project_image_settings` (`src/factory/entry/wiring.py`), and its `PATH` reaches the sync, the checks and the agent through `Boundaries.image_path`.
- **The rebuild (S0003), with its repair (S0004).** `_ProjectImageStart.prepare` → `_follow_main` → `_choose` (`src/factory/entry/run.py:216-265`). Since S0004, `_follow_main` catches `FetchFailed`, raises the repository stop `fetch_failed` with `str(error)`, returns `False` before it reads the stage file, and clears the stop after a fetch that passes. Any other `GitError` still reaches the scheduler. This is the finding of weight from A0001, and it is closed. The smoke test below shows it.
- **The follow-up stories S0005 and S0006** stay inside the scope: one is documents only and the other is tests only. `git diff --name-status` of their merges (`60614a69c`, `a33e9c597`) shows `docs/` and `tests/` alone.
- **The goal.** "A new image identity makes the preflight and the reuse of passed checks start afresh" holds, as A0001 found. It holds only while the base identity is known (the human kept that in S0002 entry 17).
- **Out of scope.** Respected: the factory ships no project's own stage file, every stage uses one image, the build context is empty, and there is no registry.

Still not reached inside the factory: no stage ran a real `podman build`, because the stage container has no podman. The human answered A0001's (e) with "my check on factory-vm at the end". That check is outside this pull request and is not recorded yet (listed under 6).

## 2 The feature's smoke test

The walk-through follows an operator whose project needs more tools, from a fresh `factory-run` on a `main` with no stage file. It goes through ten changes, and `factory-health` is read after each iteration:

1. The human merges the template from the operator guide.
2. An unrelated commit.
3. A layer that puts a JDK on its `PATH`.
4. The remote becomes unreachable.
5. `main` changes the layer while the remote stays unreachable.
6. The remote is reachable again.
7. A file that breaks the rule.
8. A file whose build fails.
9. A file whose build reaches its time limit.
10. The file's removal.

The script drives these real entry points:

- `run_instance`, with no `images` replacement, so `build_images(settings)` wires the real `PodmanImages`.
- A real bare remote (`make_remote`), with the human's clone (`HumanClone`) pushing to `main`, and the remote renamed away and back for the outage.
- `factory.entry.health.main` for `factory-health`.

The stand-ins are a `podman` script and a recording tick in place of `build_tick`:

- The `podman` script records its arguments and the build context's entries, prints 25 lines and exits 1 for a file marked `FAIL`, sleeps 30 s for one marked `SLOW`, and answers `image inspect` with the `PATH` from the file's `ENV PATH`.
- The recording tick prints the image, identity and `PATH` a stage would run in.

To reach the time-limit path in seconds, the script set the build limit `IMAGE_BUILD_TIME_LIMIT` to 2 s in `factory.entry.wiring`. No real container ran: the stage container has no podman. The script is in the agent's home, outside the repository and outside any commit (its removal was refused this stage). Its runs of `run_instance` used a `tempfile.TemporaryDirectory`, and `/tmp` holds nothing it left.

```
$ uv run python feature_smoke.py 2>&1 | grep -v Bytecode
base image: factory-stage:1  base identity: sha256-base
start of factory-run on a main without a stage file
2026-11-04T03:05:49Z disk start: /tmp/tmpdd3a4prw 23.8 GB free, 0.0 GB used; /tmp/tmpdd3a4prw/state 23.8 GB free, 0.0 GB used
  stage ran in image=factory-stage:1 identity=sha256-base PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (after the start): exit 0: healthy
human/world: merge the template (build-essential, cmake)
2026-11-04T03:05:49Z stage image: built sha256-base+20733148ba61 at f4496ec6272b in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+20733148ba61 PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (merge the template (build-essential, cmake)): exit 0: healthy
human/world: merge an unrelated commit
  stage ran in image=factory-stage:1-project identity=sha256-base+20733148ba61 PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (merge an unrelated commit): exit 0: healthy
human/world: merge a layer that adds a JDK to its PATH
2026-11-04T03:05:49Z stage image: built sha256-base+d4cd1d17259b at 0f538a1015d3 in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+d4cd1d17259b PATH=/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin
  factory-health (merge a layer that adds a JDK to its PATH): exit 0: healthy
human/world: the remote becomes unreachable
2026-11-04T03:05:49Z stop repository fetch_failed: git fetch --prune origin failed (exit 128): fatal: '/tmp/tmpdd3a4prw/origin/remote.git' does not appear to be a git repository
2026-11-04T03:05:49Z fatal: Could not read from remote repository.
2026-11-04T03:05:49Z 
2026-11-04T03:05:49Z Please make sure you have the correct access rights
2026-11-04T03:05:49Z and the repository exists.
  factory-health (the remote becomes unreachable): exit 1: fetch_failed (repository): git fetch --prune origin failed (exit 128): fatal: '/tmp/tmpdd3a4prw/origin/remote.git' does not appear to be a git repository
    | fatal: Could not read from remote repository.
    | 
    | Please make sure you have the correct access rights
human/world: main changes the layer while the remote stays unreachable
2026-11-04T03:05:49Z stop repository fetch_failed: git fetch --prune origin failed (exit 128): fatal: '/tmp/tmpdd3a4prw/origin/remote.git' does not appear to be a git repository
[... the same four continuation lines ...]
  factory-health (main changes the layer while the remote stays unreachable): exit 1: fetch_failed (repository): git fetch --prune origin failed (exit 128): fatal: '/tmp/tmpdd3a4prw/origin/remote.git' does not appear to be a git repository
    | fatal: Could not read from remote repository.
    | 
    | Please make sure you have the correct access rights
human/world: the remote is reachable again
2026-11-04T03:05:49Z stop cleared fetch_failed
2026-11-04T03:05:49Z stage image: built sha256-base+e1006ea1e306 at 8ed9c11fa29a in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+e1006ea1e306 PATH=/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin
  factory-health (the remote is reachable again): exit 0: healthy
human/world: merge a file that breaks the rule
2026-11-04T03:05:49Z stage image: failed at 491b46d61395
2026-11-04T03:05:49Z stop machine stage_image_failed: at 491b46d61395: the FROM must be FROM ${FACTORY_BASE} alone: FROM debian:bookworm
  factory-health (merge a file that breaks the rule): exit 1: stage_image_failed (machine): at 491b46d61395: the FROM must be FROM ${FACTORY_BASE} alone: FROM debian:bookworm (since 2026-11-04T03:05:49Z)
human/world: merge a file whose build fails
2026-11-04T03:05:49Z stage image: failed at 5905ada198f8
2026-11-04T03:05:49Z stop machine stage_image_failed: at 5905ada198f8: the stage file did not build in 1 s:
2026-11-04T03:05:49Z step line 6
[... "step line 7" to "step line 24", one log line each ...]
2026-11-04T03:05:49Z step line 25
  factory-health (merge a file whose build fails): exit 1: stage_image_failed (machine): at 5905ada198f8: the stage file did not build in 1 s:
    | step line 6
    | step line 7
    | step line 8
human/world: merge a file whose build reaches its time limit
2026-11-04T03:05:51Z stage image: failed at fd98d626152f
2026-11-04T03:05:51Z stop machine stage_image_failed: at fd98d626152f: the stage file did not build in 3 s:
2026-11-04T03:05:51Z container command /tmp/tmpdd3a4prw/fake-podman/podman build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f /tmp/factory-stage-file-k2st2yl2/Containerfile /tmp/factory-stage-file-k2st2yl2/context failed: no end within 2 s
  factory-health (merge a file whose build reaches its time limit): exit 1: stage_image_failed (machine): at fd98d626152f: the stage file did not build in 3 s:
    | container command /tmp/tmpdd3a4prw/fake-podman/podman build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f /tmp/factory-stage-file-k2st2yl2/Containerfile /tmp/factory-stage-file-k2st2yl2/context failed: no end within 2 s (since 2026-11-04T03:05:51Z)
human/world: merge the removal of the file
2026-11-04T03:05:51Z stop cleared stage_image_failed
2026-11-04T03:05:51Z stage image: back to the base at 1b4e6d8411c5
  stage ran in image=factory-stage:1 identity=sha256-base PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (merge the removal of the file): exit 0: healthy
[... the script then repeats the log's stage image and stop lines, elided here ...]
podman calls (builds and inspects):
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

(The podman listing comes from a second run of the same script, whose only change was that it no longer printed the word `build` twice. The paths, which change with every run, are left out of it.)

Green. What it shows, against `feature.md` and the documents:

- **No stage file.** The base runs.
- **The template.** It builds to `sha256-base+20733148ba61`, the identity the operator guide gives as its example.
- **An unrelated commit** builds nothing and logs nothing.
- **A changed file** is rebuilt between stages, and its `ENV PATH` reaches the stage.
- **The outage (S0004).** A failed fetch stands as `fetch_failed`, and `factory-health` exits 1. No stage runs, and nothing is built, though `main` changed the file during the outage. The first fetch that passes clears the stop and builds the changed file once, before the next stage.
- **A broken rule, a failed build and a timed-out build** each stand as `stage_image_failed`. A failed build's detail is its last 20 lines (6 to 25). A timed-out build's detail is podman's `no end within <s> s` with no build output, exactly as S0005 now documents it. No prune follows a timed-out build, as the code's comment says.
- **The removal** clears the stop and returns to the base.
- **Every build** has an empty context, `--network=host` and the `-project` tag.

`make check` was green as found: `test: green (85.0 s)`, coverage 99.52 %, `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

The items A0001 collected from S0001 to S0003 went to S0004 to S0006 or to the human's answers (see 6). What is new, from S0004 to S0006 and from this stage's own run:

- **The tick's `fetch_failed` writes git's multi-line text as one log line per line** (S0004 coder entries 13, 17, 25). Both fetches do it. It comes from the log writer, which predates the feature, and A0001 saw the same. The smoke test shows one consequence: during an outage, each iteration writes the stop's five lines again (`raise_stop` logs every raise, and the tick's own fetch always did the same). With the idle pause at up to 120 s, that is a few lines a minute. No story.
- **Two fetches per iteration**, one in `prepare` and one in the tick (S0004 coder entries 17, 25). The human answered A0001 (d) with "later". No story.
- **`_project` exists twice with different signatures**: `tests/entry/test_run_fetch_before_tick.py:164` takes the base and returns a `StageSeen`, and `tests/entry/test_run_project_image_rebuild.py:309` returns a function of the base and keeps the build index apart from the build count (S0004 reviewer entry 27, a note). Folding them means a new shared signature for two call shapes, and that is little gain. No story.
- **`STAND_IN` in `tests/adapters/test_podman_images.py`** is still a variant of `PODMAN_SCRIPT` (S0006 Description and coder entry 7). It is left to a later story, as A0001 judged. No story.
- **Seen in the smoke test, not in a journal**:
  - While `prepare`'s fetch fails, and while `stage_image_failed` stands, no tick runs, so the tick's disk check does not run either. `disk_low` is neither raised nor cleared in that time. The stop that stands already says that nothing runs. No story.
  - The new support module `tests/stage_image_support.py`, and the fixtures `base_identity_settings` and `base_image` in `tests/conftest.py`, are missing from the project guide's *Shared test helpers* index. S0004's docs criterion did not name the index → F0049-S0007 (see 5).
- **Still open from A0001's list, each with no story then and none now**:
  - `floating_references` misses npm called by its full path.
  - The 12-digit commit is sliced inline in several modules.
  - `tests/entry/test_wiring_image_path.py` builds its `InstanceSettings` by hand.
  - The coder's and tester's edits to the work item are dropped (the pipeline's write paths, the human's).

## 5 The documentation as a whole

S0005 closed the three differences A0001 named:

- The timed-out build's detail. The smoke test confirms the new text.
- What a restart does.
- The base's `PATH` without a stage file.

`docs/decisions.md` now carries the reasons and rejected options of decisions 1, 3, 4 and 5, and marks "ends with the next start" as replaced. S0004's entry "A failed fetch before the tick stands as `fetch_failed`" and the operator guide's *The stops of the tick* and stops table now agree with the code. `README.md` has one sentence on the stage file, which is true. `uv run python -m factory.entry.check_documents` prints `documents ok`.

Two places are left:

1. **The stops table** (`docs/operator-guide.md:1608`). Its `stage-image-failed` row says "Fix the file on `main` and start `factory-run` again". That text is from S0002. Since S0003 the same guide says "No restart is needed" (`:517`), and *The stop `stage_image_failed`* (`:568`) says the next `main` with another file ends the stop. A restart still works, so the row costs the operator a needless step rather than a wrong result. In a job it is not possible at all. → F0049-S0007.
2. **The project guide's *Shared test helpers*** (`docs/project-guide/README.md:29-109`). It lists every `tests/*_support.py` except `stage_image_support.py`, which S0004 added. Its `conftest.py` entry does not name `base_identity_settings` or `base_image`. The guide tells agents to look there before writing a helper, and the reviewer counts a copy as a finding. So the gap invites the next copy, the kind of copy S0004's review round had to move. → F0049-S0007.

No two stories explain the same thing differently. The operator guide's *The project's stage file* and the project guide's *The project's stage image* name the same seams, now including `_follow_main`'s stop.

## 6 Decisions taken for the human

**From `feature.md`, decisions 1 to 8** (unchanged since A0001):

1. A Containerfile and not a package list.
2. The factory's tools apart.
3. One image, named in one place.
4. An empty build context.
5. Rebuild by hash between stages.
6. The runtimes exec'd without Node.
7. The leave in `tests/entry/test_health.py`.
8. The checks take the image's `PATH`, and four more leaves for S0002.

**The human's answers in the journals.** S0001 to S0003 are as A0001 listed them. Since then:

- **A0001's questions** (night log, 02:18Z):
  - (a) Documents only for the timed-out build's detail, done in S0005.
  - (b) Keep the reset of the error counts on a rebuilt tick.
  - (c) `FakeImages` into `security/duplicates-baseline.txt`, done in `b0c9b2d77`. `make duplicates` now reads `0 new, 43 known, 0 gone`.
  - (d) One fetch per iteration: later.
  - (e) A real build on factory-vm: the human's own check "at the end". **Still open**: confirm that the image built from the merged `vm/Dockerfile` reports the pinned `claude --version` and `opencode --version`, and that a real stage file (the ESP32 template's) builds and runs `make check` in the project image.
- **S0004**
  - Entry 4: added the criterion that another `GitError` is not turned into `fetch_failed`.
  - Entry 11: option (a). The test checks the first line of the multi-line detail, and the code keeps `detail=str(error)`, the same as the tick's own stop.
- **S0005, S0006**: no questions.

**Defaults the agents took without asking:**

- S0004 coder: the error is caught in `_follow_main` and not in `prepare`. The Interface placed it there.
- S0004 documenter: the decisions entry has no Rejected line, because the story named no rejected option.
- S0004 tester: the fixtures moved to `conftest.py` were renamed to `base_identity_settings` and `base_image`, to avoid clashing with other `settings` fixtures.
- S0006 tester: rejected a structural test that would scan `tests/` for copies of the `PATH` text.
- A0001's list stands for the rest: `image prune -f` prunes every dangling image of the user, and a removed stage file leaves the last `-project` image tagged.

**Earlier tests changed, each with its leave.** `git diff --name-status <merge>^1 <merge>` of each merge matches the reviewers' lists:

- **S0004** (`ac67003c2`): `tests/conftest.py` and `tests/entry/test_run_project_image_rebuild.py`, under the standing leave to move a shared helper (tester entry 23, reviewer entry 27).
- **S0005** (`60614a69c`): none.
- **S0006** (`a33e9c597`):
  - `tests/entry/test_wiring_run.py` and `tests/application/test_tick_preflight.py`, under the standing leave.
  - `tests/entry/test_wiring_image_path.py`, under the standing leave.
  - `tests/adapters/test_podman_images.py`: the helper move is under the standing leave. Its new `null` row in an S0002 test is a change beyond that leave. The reviewer (entry 9) named as its leave the story's own Interface, which the human merged and started. `feature.md` gives no leave for it, as the story form asks. It is a leave named, so it is not a finding. The human may confirm that a story they start counts as the leave.

No earlier test was changed with no leave named.

## 7 The slow checks

The project offers no image scan or SBOM target. `make mutants` is not run here (check 3).

**`make duplicates`** (a record, not a check): `duplicates: 0 new, 43 known, 0 gone`. The `FakeImages` false positive is now in the baseline.

**Test times**, from `.reports/junit.xml`: 8749 tests, 729.8 s summed across workers, and `make test` took 85.0 s of wall time.

- The feature's slowest test is still `tests/adapters/test_podman_images.py::test_a_build_that_reaches_its_time_limit_has_not_passed`, at 10.0 s. That is `ROOMY_LIMIT` by design.
- S0004's 8 cases in `tests/entry/test_run_fetch_before_tick.py` take 0.57 s together, the slowest 0.14 s.
- The 11 cases of `tests/entry/test_run_project_image_rebuild.py` take 1.42 s.
- The suite's slowest tests are older 10 s time-limit tests (`test_podman_timeout_status`, `test_opencode_resume_session`, `test_claude_runtime_provider_limit`, `test_process_session`).

**Disk.** Now `/srv/factory/vm` has 23.8 GB free and 1.3 GB used. At the previous record (`disk start`) it had 23.9 GB free and 1.3 GB used, and `/srv/factory/vm/state` and `/tmp` show the same 0.1 GB. Used space is unchanged. The 0.1 GB less free space lies outside the factory's directories, on the shared filesystem. The feature's last three stories added only text, and this stage's own `make check`, `make duplicates` and two smoke runs ran in between. No growth to name.

## 8 Cost

The stories cost 85 runs, 141.7 min, 856 turns and $33.16:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 22 | 22.6 | $6.60 |
| S0002 | 21 | 69.5 | $15.10 |
| S0003 | 16 | 27.7 | $5.86 |
| S0004 | 14 | 13.9 | $3.66 |
| S0005 | 6 | 3.5 | $0.86 |
| S0006 | 6 | 4.6 | $1.08 |

The per-story minutes are each rounded, so they sum to 141.8.

**S0002 still stands out**: 46 % of the money and 49 % of the time. The reason is the one A0001 gave. Its Interface named no seams, so it took 5 stops for the human and three review rounds whose findings were test rows.

The three follow-up stories cost $5.60 together, 17 % of the feature. Among them, S0004 took 14 runs for a one-function change:

- The coder stopped on a test assertion that could not hold, because git's error runs over several lines and the log writes each as its own line (entry 10).
- That answer needed a coder → tester → coder round trip (entries 13 to 17).
- One review round followed, to move helper copies its tester had made from S0003's test module (entries 19 to 25).

S0005 and S0006 were docs-only and tests-only. Each passed its stages without a finding, but each still ran tester, coder and reviewer stages that had nothing to do.

**Human interventions**: 11 questions answered (10 `question`, 1 `round_cap`), and the stories waited 0.4 h for them. By story:

- S0001: 1 question (entry 3) and the round cap (entry 40).
- S0002: 5 questions (entries 3, 8, 11, 16, 27).
- S0003: 2 questions (entries 3, 10).
- S0004: 2 questions (entries 3, 10).
- S0005 and S0006: none.

S0002 needed the human most. Its Interface named neither the seams nor the earlier tests it would change, so the tester stopped twice and the coder stopped twice. The follow-ups, whose Interfaces named both, needed the human for S0004 alone, once for a missing criterion and once for the log's line splitting.

## Proposed stories

- **F0049-S0007** *The stops table and the test helper index follow the stage image*: the two documentation gaps under 5. The stops table's `stage-image-failed` row still asks for a restart that S0003 made needless. The project guide's index of shared test helpers lacks `tests/stage_image_support.py` and the two fixtures S0004 moved, the place agents look before they write a copy. Documents only.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 1 story proposed (F0049-S0007). The feature does what `feature.md` promised, and S0004 to S0006 closed the findings of the first acceptance (A0001). What is left is two small documentation gaps, and neither breaks a promise.
   1 Scope: every scope item has its story, and no story goes beyond the scope. S0004 closed A0001's finding of weight: `_follow_main` (`src/factory/entry/run.py`) now raises `fetch_failed`, runs no tick, and clears the stop after a fetch that passes. S0005 changed only documents and S0006 only tests. Still not reached inside the factory: a real `podman build`, which is the human's own check (e).
   2 Feature smoke test: green. It drove `run_instance` with the real `PodmanImages` on a stand-in `podman`, a real bare remote and `factory-health` through ten changes. Base, template build, unrelated commit (no build) and JDK layer with its `PATH` all behaved as documented. During a remote outage, `fetch_failed` showed in health, nothing ran and nothing was built, though `main` changed. Recovery built the changed file once. A broken rule, a failed build (last 20 lines) and a timed-out build (podman's `no end within` text) each raised the stop, and the removal returned to the base. `make check` was green as found (99.52 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the multi-line fetch error is written line by line and repeats each iteration during an outage (log writer, older than the feature). There are two fetches per iteration (the human said later), `_project` exists twice with different signatures, and `STAND_IN` is still a variant of `PODMAN_SCRIPT`. While a stop holds the tick, the disk check does not run. No story for these. The missing helper index entry goes to S0007.
   5 Docs: S0005's repairs hold, and `documents ok`. Two gaps remain, both for S0007. The stops table's `stage-image-failed` row still says to restart `factory-run`, against "No restart is needed". The project guide's shared test helper index lacks `stage_image_support.py` and the fixtures `base_identity_settings` and `base_image`.
   6 Decisions: feature decisions 1 to 8, the human's answers to A0001's (a) to (d), and S0004 entries 4 and 11. (e), a real build on factory-vm, is still open with the human. Every earlier test changed had a leave named. The `null` row S0006 added to an S0002 test rests on the human-started story's Interface, not on `feature.md`, for the human to confirm.
   7 Slow checks: none beyond `make check`. `make duplicates` shows 0 new and 43 known. The feature's slowest test is the 10 s build time-limit test, which is `ROOMY_LIMIT` by design. Disk: used space is unchanged at 1.3 GB, and 0.1 GB less free space lies outside the factory's directories. No growth to name.
   8 Cost: $33.16, 85 runs, 141.7 min. S0002 still stands out at 46 % of the money, because its Interface named no seams: 5 of the 11 human interventions were its own. The three follow-ups cost $5.60. S0004 took 14 runs because of a test assertion on the multi-line detail and a review round for test helper copies. The stories waited 0.4 h for the human. My scratch smoke script stays in the agent's home, outside the repository, because its removal was refused.
