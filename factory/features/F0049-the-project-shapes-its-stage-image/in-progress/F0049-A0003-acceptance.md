---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 535
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-04T03:17:52.656946Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-04T03:23:58.891111Z'
  stage: acceptance
  run: 35846d6468944deebddf7ce0b8b0e2a0
stories: [F0049-S0001, F0049-S0002, F0049-S0003, F0049-S0004, F0049-S0005, F0049-S0006, F0049-S0007]
outcome: null
---

# Acceptance of The project shapes its stage image

## Recommendation

**accepted with stories.** The feature does what `feature.md` promised. S0007 closed the two documentation gaps of the second acceptance (A0002), and the human's own check (e) on factory-vm, the one open item of weight, is now recorded in the night log (03:13Z): a real stage file built and ran `make check` in the project image. The feature's smoke test below is green end to end through eleven changes. One small gap remains in the decision log: the 2026-11-01 entry on Debian's packages still names seven packages, `nodejs` and `npm` among them, and does not point to the F0049 entry that superseded it. It misleads no operator, but it breaks the log's own convention. One proposed story, F0049-S0008, adds the missing pointer.

## 1 Scope

Every scope item has its story, and no story goes beyond the scope. The code is unchanged since A0002, apart from S0007, which changed documents only (`git diff --name-status d93a31b6b^1 d93a31b6b`: `docs/operator-guide.md`, `docs/project-guide/README.md` and its own work item).

- **The base image (S0001).** `vm/Dockerfile` installs six Debian packages (`git make curl ca-certificates procps xz-utils`, line 15). It installs Node 22 from nodejs.org, pinned and checked, into `/opt/factory/node`, and installs the runtimes under `--prefix /opt/factory`. The wrappers exec `/opt/factory/bin/<runtime>` (decision 6).
- **The project's layer (S0002).** `src/factory/domain/stage_layer.py` holds the rule and the identity. The build goes through `Images` / `PodmanImages` (`src/factory/adapters/podman_images.py`): an empty context, `--network=host`, the `-project` tag and `image prune -f`. The one place that chooses the image is `project_image_settings` (`src/factory/entry/wiring.py:395`). `Boundaries.image_path` carries its `PATH` to the sync, the checks and the agent.
- **The rebuild (S0003, with S0004's repair).** The path is `_ProjectImageStart.prepare` → `_follow_main` → `_choose` (`src/factory/entry/run.py:216-265`). A failed fetch stands as `fetch_failed`.
- **The follow-up stories** S0005 to S0007 stayed inside the scope: S0005 and S0007 changed documents only, and S0006 changed tests only.
- **The goal.** "A changed file on `main` is rebuilt by the factory itself … a new image identity makes the preflight and the reuse of passed checks start afresh" holds. The smoke test below shows it.
- **Reached outside the factory too.** The human's check (e) on factory-vm (night log, `87d541fd4`): the ESP32 template's `factory/stage.Containerfile` passed `stage_layer` and built on `factory-stage:vm` in 7 s with an empty context. gcc 12.2.0 and cmake 3.25.1 were in the project image and not in the base. `claude` reported 2.1.296, and there was no `node`. `make sync` and `make check` ran green in the project image. That is the goal's motivating case, the ESP32 template that grew everyone's image by 288 MB, now carried by its own layer. The log names no `opencode --version`, the one part of (e) as A0002 phrased it that is not on record.
- **Out of scope.** Respected: the factory ships no project's stage file (the template's file lives in the template's repository, commit 620114f), every stage uses one image, the build context is empty, and there is no registry.

## 2 The feature's smoke test

The walk-through follows an operator whose project needs more tools, from a fresh `factory-run` on a `main` with no stage file. After each iteration it reads `factory-health`, then makes the next change on the remote:

1. Merge the operator guide's template.
2. Merge an unrelated commit.
3. Merge a layer that puts a JDK on its `PATH`.
4. The remote becomes unreachable.
5. `main` changes the layer to a Node of the project's own, during the outage.
6. The remote is reachable again.
7. Merge a file that breaks the rule.
8. Merge an unrelated commit that leaves the broken file as it is.
9. Merge a file whose build fails.
10. Merge a file whose build reaches its time limit.
11. Merge the removal of the file.

The real entry points:

- `run_instance`, with no `images` replacement, so `build_images(settings)` wires the real `PodmanImages`.
- A real bare remote (`make_remote`), with the human's clone (`HumanClone`) pushing to `main`, and the remote renamed away and back for the outage.
- `factory.entry.health.main` as `factory-health`.

The stand-ins:

- A `podman` script. It records its calls and the build context's entries. It prints 25 lines and exits 1 for a file marked `FAIL`, and sleeps 30 s for one marked `SLOW`. It answers `image inspect` with the `PATH` from the file's `ENV PATH`, or `null`.
- A recording tick in place of `build_tick`, which prints the image, identity and `PATH` a stage would run in.

`IMAGE_BUILD_TIME_LIMIT` was set to 2 s in `factory.entry.wiring`, so that the time limit is reached in seconds. No real container ran: the stage container has no podman. The script and the stand-in were written to a `mktemp -d` folder (`/tmp/f0049-smoke-0hnR`). Its removal was refused this stage, so it stays until the stage's container ends. `run_instance`'s files went to a `tempfile.TemporaryDirectory`, and the build's own `factory-stage-file-*` folder was removed even after the time limit.

```
$ uv run python $d/feature_smoke.py $d/podman 2>&1 | grep -v Bytecode
start of factory-run on a main without a stage file; base identity sha256-base
2026-11-04T03:21:05Z disk start: /tmp/tmpzog4wdye 23.7 GB free, 0.0 GB used; /tmp/tmpzog4wdye/state 23.7 GB free, 0.0 GB used
  stage ran in image=factory-stage:1 identity=sha256-base PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (the start): exit 0: healthy
human/world: merge the template (build-essential, cmake)
2026-11-04T03:21:05Z stage image: built sha256-base+20733148ba61 at 154068ce344e in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+20733148ba61 PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (merge the template (build-essential, cmake)): exit 0: healthy
human/world: merge an unrelated commit
  stage ran in image=factory-stage:1-project identity=sha256-base+20733148ba61 PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (merge an unrelated commit): exit 0: healthy
human/world: merge a layer that adds a JDK to its PATH
2026-11-04T03:21:05Z stage image: built sha256-base+74c607e48648 at 430a793de3a1 in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+74c607e48648 PATH=/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin
  factory-health (merge a layer that adds a JDK to its PATH): exit 0: healthy
human/world: the remote becomes unreachable
2026-11-04T03:21:05Z stop repository fetch_failed: git fetch --prune origin failed (exit 128): fatal: '/tmp/tmpzog4wdye/origin/remote.git' does not appear to be a git repository
2026-11-04T03:21:05Z fatal: Could not read from remote repository.
2026-11-04T03:21:05Z 
2026-11-04T03:21:05Z Please make sure you have the correct access rights
2026-11-04T03:21:05Z and the repository exists.
  factory-health (the remote becomes unreachable): exit 1: fetch_failed (repository): git fetch --prune origin failed (exit 128): fatal: '/tmp/tmpzog4wdye/origin/remote.git' does not appear to be a git repository
    | fatal: Could not read from remote repository.
    | 
    | Please make sure you have the correct access rights
human/world: main changes the layer to a Node of its own during the outage
2026-11-04T03:21:05Z stop repository fetch_failed: git fetch --prune origin failed (exit 128): fatal: '/tmp/tmpzog4wdye/origin/remote.git' does not appear to be a git repository
[... the same four continuation lines ...]
  factory-health (main changes the layer to a Node of its own during the outage): exit 1: fetch_failed (repository): git fetch --prune origin failed (exit 128): fatal: '/tmp/tmpzog4wdye/origin/remote.git' does not appear to be a git repository
    | fatal: Could not read from remote repository.
    | 
    | Please make sure you have the correct access rights
human/world: the remote is reachable again
2026-11-04T03:21:05Z stop cleared fetch_failed
2026-11-04T03:21:05Z stage image: built sha256-base+007a66db0585 at 37bed1a36bdb in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+007a66db0585 PATH=/opt/node24/bin:/usr/local/bin:/usr/bin:/bin
  factory-health (the remote is reachable again): exit 0: healthy
human/world: merge a file that breaks the rule
2026-11-04T03:21:06Z stage image: failed at 86372774808e
2026-11-04T03:21:06Z stop machine stage_image_failed: at 86372774808e: the FROM must be FROM ${FACTORY_BASE} alone: FROM debian:bookworm
  factory-health (merge a file that breaks the rule): exit 1: stage_image_failed (machine): at 86372774808e: the FROM must be FROM ${FACTORY_BASE} alone: FROM debian:bookworm (since 2026-11-04T03:21:06Z)
human/world: merge the same broken file again with an unrelated commit
  factory-health (merge the same broken file again with an unrelated commit): exit 1: stage_image_failed (machine): at 86372774808e: the FROM must be FROM ${FACTORY_BASE} alone: FROM debian:bookworm (since 2026-11-04T03:21:06Z)
human/world: merge a file whose build fails
2026-11-04T03:21:06Z stage image: failed at 5051d052894e
2026-11-04T03:21:06Z stop machine stage_image_failed: at 5051d052894e: the stage file did not build in 1 s:
2026-11-04T03:21:06Z step line 6
[... "step line 7" to "step line 24", one log line each ...]
2026-11-04T03:21:06Z step line 25
  factory-health (merge a file whose build fails): exit 1: stage_image_failed (machine): at 5051d052894e: the stage file did not build in 1 s:
    | step line 6
    | step line 7
    | step line 8
human/world: merge a file whose build reaches its time limit
2026-11-04T03:21:08Z stage image: failed at 3bc81bdf3d58
2026-11-04T03:21:08Z stop machine stage_image_failed: at 3bc81bdf3d58: the stage file did not build in 3 s:
2026-11-04T03:21:08Z container command /tmp/f0049-smoke-0hnR/podman build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f /tmp/factory-stage-file-q5tp1nj3/Containerfile /tmp/factory-stage-file-q5tp1nj3/context failed: no end within 2 s
  factory-health (merge a file whose build reaches its time limit): exit 1: stage_image_failed (machine): at 3bc81bdf3d58: the stage file did not build in 3 s:
    | container command /tmp/f0049-smoke-0hnR/podman build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f /tmp/factory-stage-file-q5tp1nj3/Containerfile /tmp/factory-stage-file-q5tp1nj3/context failed: no end within 2 s (since 2026-11-04T03:21:08Z)
human/world: merge the removal of the file
2026-11-04T03:21:08Z stop cleared stage_image_failed
2026-11-04T03:21:08Z stage image: back to the base at 0143af07791c
  stage ran in image=factory-stage:1 identity=sha256-base PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (merge the removal of the file): exit 0: healthy
factory log:
[... the "stage image" and "stop" lines above again, as the state log holds them, one line per stop ...]
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

Green. What it shows, against `feature.md` and `docs/operator-guide.md`, *The project's stage file*:

- **No stage file.** The base runs, with the base's identity and the default `PATH`, because the stand-in's base configures none.
- **The template** builds to `sha256-base+20733148ba61`, the identity the operator guide gives as its example.
- **An unrelated commit** builds nothing and logs nothing.
- **A changed file** is rebuilt between stages. Its `ENV PATH` reaches the stage, and the identity changes.
- **A project's own Node** (step 5) builds as any layer does. Its `PATH` comes first, and the factory's runtimes are not on that `PATH` to be shadowed (decision 2).
- **The outage.** A failed fetch stands as `fetch_failed`, and `factory-health` exits 1. No stage runs, and nothing is built, though `main` changed the file during the outage. The first fetch that passes clears the stop and builds the changed file once.
- **A broken rule** stands as `stage_image_failed`. An unrelated commit that leaves the broken file as it is does not end the stop and builds nothing, as *The stop `stage_image_failed`* says.
- **A failed build** gives its last 20 lines (6 to 25). **A timed-out build** gives podman's `no end within <s> s` and no build output, and no prune follows it.
- **The removal** clears the stop and returns to the base, with `back to the base`.
- **Every build** has an empty context, `--network=host` and the `-project` tag.

`make check` was green as found: `test: green (86.8 s)`, coverage 99.52 %, `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

What A0001 and A0002 collected went to stories S0004 to S0007, or to the human's answers, or stands with no story, as A0002 listed. Two things are new: S0007's journal, and this stage's own run.

- **A docs-only story runs four stages with nothing to do.** In S0007, the tester wrote no test (entry 5) and the coder built nothing (entry 7). The coder's note: "criteria 1 and 2 can only be checked after the docs stage. A reviewer reading this stage's diff will find nothing to check against them." The reviewer (entry 9) checked the Interface's facts against `main` instead. Those three runs cost $0.43 of S0007's $0.82. A0002 saw the same in S0005 and S0006. This belongs to the pipeline's definition, which is the human's (`factory/pipeline.yml`), not to this feature. No story; listed for the human under 6.
- **The smoke test's first grep exits 1 while it prints the expected `0`** (S0007 intake entry 3 and smoke-tester entry 13). It was harmless there, and it is a habit of story writing. The story proposed here avoids it, because its greps are expected to print `1`. No story.
- **Seen in the smoke test, not in a journal.** During an outage, each iteration writes the `fetch_failed` stop's five lines again. A0002 saw this, and it comes from the log writer, which is older than the feature. No story.
- **Seen in reading `docs/` for check 5.** The decision log's 2026-11-01 entry on Debian's packages has no forward pointer to the F0049 entry that superseded it → F0049-S0008 (see 5).
- **Still open from A0001's and A0002's lists, each with no story then and none now:**
  - Two fetches per iteration (the human said "later").
  - `_project` exists twice in the tests, with different signatures.
  - `STAND_IN` is a variant of `PODMAN_SCRIPT`.
  - `floating_references` misses npm called by its full path.
  - The 12-digit commit is sliced inline in several modules.
  - The disk check does not run while a stop holds the tick.

## 5 The documentation as a whole

S0007 closed both of A0002's gaps:

- The stops table's `stage-image-failed` row (`docs/operator-guide.md:1608`) now says "Fix the file on `main`: the fix takes effect before the next stage, with no restart; see "The project's stage file"". That agrees with `:517` and `:568`.
- The project guide's *Shared test helpers* lists `stage_image_support.py` (`docs/project-guide/README.md:44`). Its `conftest.py` entry names `base_identity_settings` and `base_image`.

`README.md`'s one sentence on the stage file is true. The operator guide's *The project's stage file* matches what the smoke test printed, line for line: the log lines, the details of the stop, the identity example, the `PATH` and the time-limit text. The project guide's *The project's stage image* (`docs/project-guide/stage-environment.md:366`) names the same seams. `uv run python -m factory.entry.check_documents` prints `documents ok`.

One place is left: **`docs/decisions.md`, *Debian's packages follow the base image's release*** (`:1305-1314`).

- It still says "the stage image's seven Debian packages (`git`, `make`, `curl`, `ca-certificates`, `procps`, `nodejs`, `npm`)" and "`tests/test_stage_image.py` allows the findings of an `apt-get install` of exactly those seven names".
- The image installs six (`vm/Dockerfile:15`), and the test's `STAGE_PACKAGES` lists six (`tests/test_stage_image.py:32`).
- The F0049 entry *The factory's tools live apart* (`:1455`) says that it supersedes the seven for `nodejs` and `npm`, "the rest of that entry stands". The old entry has no pointer back. The log's convention is a `- Superseded in part by "…"` line on the older entry: *Every tool of the machine's image is pinned* (`:291`) carries one that points to this very entry.

A newcomer reading from the top meets the seven packages with nothing that sends them on. The operator guide (`:493`) has it right, so no operator is misled. It is a contradiction within the decision log, not between the documents and the behaviour. → F0049-S0008.

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
9. S0006's inspect `null` row confirmed, the human's answer to A0002.

**The human's answers in the journals.** S0001 to S0006 and A0001's (a) to (e) are as A0002 listed them. Since then:

- **(e), a real build on factory-vm: done by the human** (night log 03:13Z, `87d541fd4`). The record names `claude` 2.1.296 and no `opencode --version`. The human may confirm that opencode was not part of what they meant to check, or check it at the next rebuild.
- **The fix it took in the template**, `extend-exclude` for Unity's helpers under `build/` (template commit 7c772a5), is outside this repository and outside the feature's scope.
- **S0007:** no questions.

**Defaults the agents took without asking, new since A0002:**

- S0007 tester: wrote no grep-style tests of document text, because the Interface ruled out test changes.
- S0007 coder: left both edits to the documenter, by `CLAUDE.md` *Docs*.
- S0007 documenter: placed the new index entry alphabetically, before `story_form_support.py`.

A0002's list stands for the rest. For instance, `image prune -f` prunes every dangling image of the user, and a removed stage file leaves the last `-project` image tagged.

**For the human to consider, outside this feature:** docs-only and tests-only follow-up stories still run tester, coder and reviewer stages that have nothing to do (see 4 and 8). That is the pipeline definition's business.

**Earlier tests changed, each with its leave.** S0007 (`d93a31b6b`) changed no test, so it adds none. S0001 to S0006 are as A0001 and A0002 listed them, every one with a leave named. Decision 9 now confirms S0006's `null` row. No earlier test was changed with no leave named.

## 7 The slow checks

The project offers no image scan or SBOM target. `make mutants` is not run here (check 3).

**`make duplicates`** (a record, not a check): `duplicates: 0 new, 43 known, 0 gone`.

**Test times**, from `.reports/junit.xml`: 8749 tests, 731.8 s summed across workers, and `make test` took 86.8 s of wall time.

- The feature's tests (the 283 cases whose names hold `image`, `stage_layer` or `fetch_before`) take 21.4 s together.
- The slowest of them is `tests/adapters/test_podman_images.py::test_a_build_that_reaches_its_time_limit_has_not_passed`, at 10.0 s, which is `ROOMY_LIMIT` by design. Next is `test_podman_runs_results::test_image_exists_reads_podman_s_exit_status[time-limit]`, at 1.5 s.
- The suite's slowest tests are older 10 s time-limit tests: `test_podman_timeout_status` (two rows), `test_claude_runtime_resume`, `test_opencode_resume_session` and `test_opencode_budget`.

**Disk.** Now `/srv/factory/vm` has 23.7 GB free and 1.3 GB used. At the previous record (`disk acceptance`, A0002's) it had 23.8 GB free and 1.3 GB used. `/srv/factory/vm/state` and `/tmp` show the same 0.1 GB less free space, with used space at 0.0 GB. The factory's used space is unchanged. The 0.1 GB less free space lies outside the factory's directories, on the shared filesystem. In between ran S0007 (documents only), the human's check (e) on the VM, whose leftovers the human removed, and this stage's `make check`. No growth to name.

## 8 Cost

The stories cost 91 runs, 145.0 min, 884 turns and $33.98:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 22 | 22.6 | $6.60 |
| S0002 | 21 | 69.5 | $15.10 |
| S0003 | 16 | 27.7 | $5.86 |
| S0004 | 14 | 13.9 | $3.66 |
| S0005 | 6 | 3.5 | $0.86 |
| S0006 | 6 | 4.6 | $1.08 |
| S0007 | 6 | 3.3 | $0.82 |

**S0002 still stands out**: 44 % of the money and 48 % of the time. The reason is the one A0001 gave. Its Interface named no seams, so it took 5 stops for the human and three review rounds whose findings were test rows.

**S0007** was the cheapest story of the feature. It ran first-pass through six stages with no finding and no question. Three of its six runs had nothing to do: the tester, the coder and the reviewer, $0.43 together. The same was true of S0005 and S0006. The four follow-up stories together cost $6.42, 19 % of the feature. The acceptances come on top of the stories: A0001 cost $4.20 and A0002 $2.48, and this one's cost is not yet known.

**Human interventions**: 11 questions answered (10 `question`, 1 `round_cap`), and the stories waited 0.4 h for them. The count is unchanged since A0002, because S0007 asked nothing. By story:

- S0001: 1 question (entry 3) and the round cap (entry 40).
- S0002: 5 questions (entries 3, 8, 11, 16, 27).
- S0003: 2 questions (entries 3, 10).
- S0004: 2 questions (entries 3, 10).
- S0005 to S0007: none.

S0002 needed the human most. Its Interface named neither the seams nor the earlier tests it would change, so the tester stopped twice and the coder stopped twice.

## Proposed stories

- **F0049-S0008** *The Debian packages decision points to the entry that superseded it*: the one gap under 5. The 2026-11-01 entry in `docs/decisions.md` still names seven Debian packages, `nodejs` and `npm` among them, and it lacks the `Superseded in part by` line that the log's convention gives an entry a later one replaced. One line, documents only.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 1 story proposed (F0049-S0008). The feature does what `feature.md` promised. S0007 closed A0002's two documentation gaps, and the human's check (e) on factory-vm is now on record. One small gap remains in the decision log.
   1 Scope: every scope item has its story, and no story goes beyond the scope. S0007 changed only `docs/operator-guide.md` and `docs/project-guide/README.md`. The night log (`87d541fd4`) records the human's real build of the ESP32 template's stage file on factory-vm: an empty context, gcc and cmake in the project image only, `claude` 2.1.296, no `node`, and `make check` green in the project image. No `opencode --version` is on record.
   2 Feature smoke test: green. It drove `run_instance` with the real `PodmanImages` on a stand-in `podman`, a real bare remote and `factory-health` through eleven changes. The base ran first. The template built to the operator guide's example identity. An unrelated commit built nothing. A JDK layer and then a project's own Node put their `PATH`s in place. During a remote outage, `fetch_failed` stood, nothing ran and nothing was built; recovery built the changed file once. A broken rule raised the stop, and an unrelated commit did not end it. A failed build gave its last 20 lines, and a timed-out build gave podman's `no end within`. Removing the file went back to the base. `make check` was green as found (99.52 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: docs-only stories run a tester, a coder and a reviewer with nothing to do ($0.43 of S0007's $0.82; it is the pipeline definition's business and the human's). Smoke greps that print `0` exit 1. The log repeats `fetch_failed` on every iteration of an outage. A0002's items with no story still stand. The stale decision-log entry goes to S0008.
   5 Docs: S0007's repairs hold, and `documents ok`. One gap: in `docs/decisions.md`, "Debian's packages follow the base image's release" (2026-11-01) still names seven packages, `nodejs` and `npm` among them, and says the test allows those seven. It has no `Superseded in part by` line pointing to F0049's entry, against the log's convention. No operator is misled, because the operator guide says six. → F0049-S0008.
   6 Decisions: feature decisions 1 to 9. A0001's (e) is now done by the human; opencode's version is not in the record, for the human to confirm. S0007 asked no questions and changed no test. Every earlier test the feature changed had a leave named.
   7 Slow checks: none beyond `make check`. `make duplicates`: 0 new, 43 known. The feature's 283 tests take 21.4 s; its slowest is the 10 s build time-limit test (`ROOMY_LIMIT` by design). Disk: used space unchanged at 1.3 GB, and the 0.1 GB less free space lies outside the factory's directories. No growth to name.
   8 Cost: $33.98, 91 runs, 145.0 min. S0002 still stands out at 44 % of the money: its Interface named no seams, and 5 of the 11 human interventions were its own. S0007 cost $0.82, first-pass. The four follow-ups cost $6.42 together. The stories waited 0.4 h for the human. The smoke test's scratch folder `/tmp/f0049-smoke-0hnR` was left in place because its removal was refused; it goes with the stage.
