---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 529
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-04T02:05:12.541541Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-04T02:17:11.515403Z'
  stage: acceptance
  run: d8226b6ebc15438db80d64dc8acc9984
stories: [F0049-S0001, F0049-S0002, F0049-S0003]
outcome: null
---

# Acceptance of The project shapes its stage image

## Recommendation

**not accepted.** The feature does what `feature.md` promised. The base image keeps the factory's tools apart under `/opt/factory`. A project's `factory/stage.Containerfile` on `main` is checked, built on the base and run in every container with its own `PATH` and identity. A change on `main` is rebuilt between stages. The feature's smoke test below is green end to end. The reason for `not accepted` is something S0003 left behind. Its fetch before every tick is unguarded, so since that story a fetch that fails after the start (a revoked token, the network down) never reaches the tick's `fetch_failed` stop. `factory-health` stays `healthy` while no tick runs, and the operator guide's promise that "an expired or revoked token shows as `fetch_failed`" is now false. That is a contradiction between documentation and behaviour that misleads the operator. It is reproduced under *1 Scope*. The proposed story F0049-S0004 fixes it. Merging this pull request brings that story and two smaller ones (documents, test helpers) into the backlog. Closing it keeps these findings on `main` but drops the stories.

## 1 Scope

Every scope item has its story, and no story goes beyond the scope:

- **The base image (S0001).** `vm/Dockerfile` pins Node 22.23.4 by version and SHA-256. It checks the archive with `sha256sum -c` before unpacking it into `/opt/factory/node`, and installs Claude Code 2.1.296 and opencode 1.19.3 with that Node's npm under `--prefix /opt/factory`. `/usr/local/bin/claude` and `/usr/local/bin/opencode` `exec /opt/factory/bin/<runtime> "$@"` (decision 6). There is no `ENV PATH` line, no `node` or `npm` on the `PATH`, and the six Debian packages are `git make curl ca-certificates procps xz-utils`.
- **The project's layer (S0002).** The rule is in `src/factory/domain/stage_layer.py`: one `FROM ${FACTORY_BASE}`, only `ARG FACTORY_BASE` before it, at most 64 KiB, no U+FFFD. The identity is `<base>+<12 hex>`. The build goes through `Images` (`src/factory/application/images.py`), whose implementations are `PodmanImages` (empty context, `--network=host`, `-t <stage image>-project`, then `image prune -f`) and `FakeImages`. The image in use is chosen in one place, `project_image_settings` in `src/factory/entry/wiring.py` (decision 3). `Boundaries.image_path` feeds the sync, the checks and the agent (decision 8). The stop is `stage_image_failed`, with machine scope.
- **The rebuild (S0003).** `_ProjectImageStart.prepare` → `_follow_main` / `_choose` in `src/factory/entry/run.py`. It compares the file on `origin/main` before every tick, rebuilds into a new tick on new boundaries, returns to the base when the file is removed, and writes the three `stage image:` log lines.
- **Goal.** "A new image identity makes the preflight and the reuse of passed checks start afresh" holds: `settings.image` becomes the layer's identity, which the stamp and `known_results` key on. It holds only while the base identity is known: with `settings.image` `None` no stamp is reused at all (kept by the human, S0002 entry 17).
- **Out of scope.** Respected: no project's own stage file, one image for every stage, an empty build context, no registry.

What the goal could not reach inside the factory: no stage ran a real `podman build` of a stage file. The VM has no podman in the stage container, so every build here ran against a stand-in. The human's build of S0001's image (entry 25) is the only real build in the journals. The rebuild after S0001's fix, and a real build of the ESP32 template's stage file on factory-vm, are not recorded (listed under 6).

**Finding (weight: not accepted): a failed fetch before the tick is invisible.** `_follow_main` calls `git.fetch()` with no guard (`src/factory/entry/run.py:228`). When the fetch fails, `FetchFailed` escapes to the scheduler's catch-all (`src/factory/application/scheduler.py:76`), which logs a multi-line `iteration failed:` and runs no tick. The tick's own `_fetch` (`src/factory/application/tick.py:139-144`) raises `fetch_failed`, but it is never reached. The tick's disk check, which runs before its fetch, is skipped too. The S0003 coder disclosed the `iteration failed` line (entry 10) and the human accepted it "for now" (entry 11). Neither entry names the consequence for `factory-health` or for the documents (`docs/operator-guide.md:1600` and `:1807`). Reproduced with `run_instance` on a real bare remote that was renamed away after the first tick (FakeHostingService, FakeImages, recording tick):

```
$ uv run python -I "$d/scripts/fetch_outage.py" 2>&1 | grep -v "Bytecode\|^20"
ticks after the start: 1
origin made unreachable
ticks in total: 1
factory-health: exit 0 healthy
log lines 'iteration failed: FetchFailed': 3
log lines 'stop repository fetch_failed': 0
```

Proposed as F0049-S0004.

## 2 The feature's smoke test

The walk-through follows an operator whose project needs more tools. A fresh `factory-run` starts on a `main` with no stage file. Then the human merges, in turn: the template from S0002's Interface, an unrelated commit, a layer that puts a JDK on its `PATH`, a file that breaks the rule, a file whose build fails, and finally the file's removal. After each iteration the operator reads `factory-health`.

The script, in a `mktemp -d` that removes itself, drives the real entry points:

- `run_instance`, with no `images` replacement, so `build_images(settings)` wires the real `PodmanImages`;
- a real bare remote, with the human's clone pushing to `main`;
- `factory.entry.health.main` for the health check.

The stand-ins are a `podman` script and a recording tick in place of `build_tick`. The script records podman's arguments and the build context's entries, prints 25 lines and exits 1 for a file marked to fail, and answers `image inspect` with the `PATH` the file's `ENV PATH` line sets. The recording tick prints the image, identity and `PATH` each stage would run in. No real container runs, because the stage container has no podman.

```
$ uv run python -I "$d/scripts/feature_smoke.py" 2>&1
base image: factory-stage:1  base identity: sha256-base
start of factory-run on a main without a stage file
2026-11-04T02:09:29Z disk start: /tmp/tmpe64zf9_h 24.1 GB free, 0.0 GB used; /tmp/tmpe64zf9_h/state 24.1 GB free, 0.0 GB used
  stage ran in image=factory-stage:1 identity=sha256-base PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (after the start): exit 0: healthy
human: merge the template (build-essential, cmake)
2026-11-04T02:09:29Z stage image: built sha256-base+20733148ba61 at a71a76aa6a22 in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+20733148ba61 PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (after: merge the template (build-essential, cmake)): exit 0: healthy
human: merge an unrelated commit
  stage ran in image=factory-stage:1-project identity=sha256-base+20733148ba61 PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (after: merge an unrelated commit): exit 0: healthy
human: merge a layer that adds a JDK to its PATH
2026-11-04T02:09:29Z stage image: built sha256-base+b09e8a4ff204 at 54dc7d8fdb27 in 1 s
  stage ran in image=factory-stage:1-project identity=sha256-base+b09e8a4ff204 PATH=/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin
  factory-health (after: merge a layer that adds a JDK to its PATH): exit 0: healthy
human: merge a file that breaks the rule
2026-11-04T02:09:29Z stage image: failed at dfec99709de0
2026-11-04T02:09:29Z stop machine stage_image_failed: at dfec99709de0: the FROM must be FROM ${FACTORY_BASE} alone: FROM debian:bookworm
  factory-health (after: merge a file that breaks the rule): exit 1: stage_image_failed (machine): at dfec99709de0: the FROM must be FROM ${FACTORY_BASE} alone: FROM debian:bookworm (since 2026-11-04T02:09:29Z)
human: merge a file whose build fails
2026-11-04T02:09:29Z stage image: failed at f15ab8e433cd
2026-11-04T02:09:29Z stop machine stage_image_failed: at f15ab8e433cd: the stage file did not build in 1 s:
2026-11-04T02:09:29Z step line 6
[... the log lines "step line 7" to "step line 24", one per line, elided here ...]
2026-11-04T02:09:29Z step line 25
  factory-health (after: merge a file whose build fails): exit 1: stage_image_failed (machine): at f15ab8e433cd: the stage file did not build in 1 s:
    | step line 6
    | step line 7
    | step line 8
human: merge the removal of the file
2026-11-04T02:09:29Z stop cleared stage_image_failed
2026-11-04T02:09:29Z stage image: back to the base at 12718b4f0b91
  stage ran in image=factory-stage:1 identity=sha256-base PATH=/usr/local/bin:/usr/bin:/bin
  factory-health (after: merge the removal of the file): exit 0: healthy
podman calls (images):
   image inspect --format {{json .Config.Env}} factory-stage:1
   build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f /tmp/factory-stage-file-x9c6zgbb/Containerfile /tmp/factory-stage-file-x9c6zgbb/context
   context entries: 0
   image prune -f
   image inspect --format {{json .Config.Env}} factory-stage:1-project
   build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f /tmp/factory-stage-file-ykjldv41/Containerfile /tmp/factory-stage-file-ykjldv41/context
   context entries: 0
   image prune -f
   image inspect --format {{json .Config.Env}} factory-stage:1-project
   build --build-arg FACTORY_BASE=factory-stage:1 --network=host -t factory-stage:1-project -f /tmp/factory-stage-file-3inp_r5r/Containerfile /tmp/factory-stage-file-3inp_r5r/context
   context entries: 0
   image prune -f
   image inspect --format {{json .Config.Env}} factory-stage:1
stages run: 5
```

Green. What it shows:

- The base runs without a stage file.
- The template's identity `sha256-base+20733148ba61` is the one the S0002 documenter computed for the operator guide's example.
- An unrelated commit builds nothing and logs nothing.
- A changed file is rebuilt between stages, and its `ENV PATH` reaches the stage.
- A broken rule and a failed build each stand as `stage_image_failed`. No stage runs while either stands. The build's detail is its last 20 lines (6 to 25).
- The removal ends the stop and returns to the base.
- Every build has an empty context, `--network=host`, the `-project` tag and a prune after it.

`make check` was green as found (`test: green (84.6 s)`, coverage 99.51 %, `check: green`).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Collected from the archived journals, each with where it now goes:

- **A failed fetch in `prepare` logs `iteration failed`** (S0003 coder, entries 10, 17; documenter entry 33). A finding, see 1 → F0049-S0004.
- **A timed-out build's detail is podman's no-end text, not the tail** (S0002 coder, entries 16 to 42; the human kept it, entry 17). The operator guide says it "gives the same text" as a failed build → documents in F0049-S0005. Changing the code is listed under 6.
- **An image that cannot be inspected falls back to the default `PATH` silently**, and with `settings.image` `None` no stamp is reused (S0002 entry 16, kept by the human, entry 17). No story; listed under 6.
- **`make duplicates` reports `FakeImages` as unused** (vulture, 60 %), a false positive, on every story since S0002 (entries 25, 34, 42; S0003 entries 19, 21, 25, 29). Accepting it means an entry in `security/duplicates-baseline.txt`, the human's file. Listed under 6.
- **Test copies**: `SYSTEM_PATH` redefined in `tests/adapters/test_podman_images.py:21`, `BASE_PATH` in `tests/entry/test_wiring_image_path.py:31`, `PROBE` and `COMPLETED` copied in `tests/entry/test_wiring_image_path.py:32-37`, `Machine.log_lines` in `tests/application/test_tick_preflight.py:81`, and no row for inspect printing `null` (S0002 reviewer entries 36, 44; S0003 coder entry 29) → F0049-S0006. Left out of it: `STAND_IN` in `tests/adapters/test_podman_images.py`, a variant of `PODMAN_SCRIPT` that also lists the context, and the hand-built `InstanceSettings` in `tests/entry/test_wiring_image_path.py:97-107`. Folding either would change shared helpers more than one story should.
- **A rebuilt tick starts its error counts at zero** (S0003 reviewer finding 4; the coder documented it in the docstring and did not carry `TickStatus` over). Listed under 6.
- **The start's own build also writes a `built` line** (S0003 entry 10). Documented in the operator guide's table. Nothing open.
- **`tests/dockerfile_support.py`'s `floating_references` misses npm called by its full path** (S0001 tester entry 8). `test_the_stage_image_has_no_floating_reference` rewrites the text before calling it. The pins are still checked, so no story.
- **`test_each_tool_is_installed_once_at_its_pinned_version` repeats the `--prefix` check** (S0001 reviewer entries 20, 35). A small overlap; no story.
- **Stale history in `docs/decisions.md`**: "eight Debian tools" (S0001 documenter entry 22). It is a dated entry that later entries supersede; history stays as written.
- **The 12-digit commit is sliced inline** (`[:12]`) in several modules, and S0003 added `_SHORT_COMMIT_LENGTH` (S0003 entry 17, reviewer entry 31). No helper exists to reuse; no story.
- **Work item edits by the coder and tester are dropped** (S0002 entries 16, 23, 34; S0003 entries 21, 25). The reviewers carried the corrections into the Descriptions instead. That is the pipeline's write paths, the human's to judge, and outside this feature.
- **Seen in the smoke test, not in a journal**: a multi-line detail (the build's tail, git's fetch error) goes into the factory log as one timestamped line per line. That comes from the log writer, which predates this feature; no story.

## 5 The documentation as a whole

`README.md` gives one correct sentence and points to the operator guide. The guide's *The stage image* and *The project's stage file*, and `docs/project-guide/stage-environment.md` *The project's stage image*, read as one account and name the same seams. Where the documents and the code now differ:

1. **`fetch_failed`** (`docs/operator-guide.md:1600`, `:1807`): "An expired or revoked token shows as `fetch_failed`". Since S0003 that holds only for a fetch at the start; see 1 → F0049-S0004's docs criterion.
2. ***The stop `stage_image_failed`*** says a build that reaches its time limit "gives the same text", that is, the last 20 lines. The code gives `the stage file did not build in <s> s:` followed by `container command podman build … failed: ` and the no-end text (`src/factory/adapters/podman_images.py:53-57`, `src/factory/adapters/process.py:283-284`) → F0049-S0005.
3. **The same section**: "A restart of `factory-run` also ends it." A restart builds the same file again: the stop ends if that build passes and stands again if it fails → F0049-S0005.
4. ***The project's stage file***: "Without the file nothing changes". The image and the identity stay the base's, but since S0002 the containers take the `PATH` the base image configures, read with `podman image inspect` (`_image_path`, `src/factory/entry/wiring.py:353`). The fixed `/usr/local/bin:/usr/bin:/bin` is now used only when the image sets no `PATH`. The `python:3.12-slim` base configures its own `PATH`, so this applies to every project → F0049-S0005.
5. **`docs/decisions.md`**:
   - "A project adds a layer to the stage image with `factory/stage.Containerfile`" cites decisions 1, 3 and 4 of the feature but gives none of their reasons or rejected options. The S0002 documenter says it did not read `feature.md` (entry 46), as the documenter's rule asks.
   - The same entry still says the stop "ends with the next start", which the next entry replaced without saying so.
   - "The factory follows `main` …" lacks decision 5's second reason (a Cloud Run job builds at every start).

   All three → F0049-S0005, which writes the reasons from `feature.md` into its own Interface so the documenter may carry them.

There is no contradiction between stories in what they wrote. The S0001 paragraph and the S0002 *How it is built* both say the runtimes live under `/opt/factory` and the image has no `node` for projects, and they agree. The example Containerfile is the template S0002's tests accept.

## 6 Decisions taken for the human

From `feature.md`, decisions 1 to 8: a Containerfile and not a package list; the factory's tools apart; one image named in one place; an empty build context; rebuild by hash between stages; the runtimes exec'd without Node; the leave in `tests/entry/test_health.py`; the checks take the image's `PATH`, and four more leaves for S0002.

The human's answers in the journals:

- **S0001**
  - Entry 4: rows for `"$@"`, for node or npm off the `PATH`, for curl and the unpack target; `vm/setup.sh` and `vm/job-start.sh` unchanged; the placement of the pins dropped.
  - Entry 25: the wrappers exec the runtimes directly (decision 6).
  - Entry 41: the Dockerfile comment reworded; the smoke test stays as written.
- **S0002**
  - Entry 4: an `output_tail` of 20 lines; a 30-minute limit that gives `passed=False`; `path` rows; "rootless" dropped; the stop ends at the next start; reasons tested as different, not as fixed texts; the time limit with the same detail text as a failed build.
  - Entry 9: module names and seams, machine scope, 64 KiB measured on the UTF-8 bytes, non-UTF-8 tested at the start's read.
  - Entry 12: `Boundaries.image_path`; `factory-watch` shows no stop of any reason (its criterion dropped).
  - Entry 17: the leaves of decision 8; the checks take the image's `PATH`; three notes kept as they are: the timed-out build's detail without a tail, the silent fallback when inspect fails, and no stamp reuse with `image=None`.
  - Entry 28: the U+FFFD check stays in `stage_layer`, with one reason for both cases; `Git.show_file` unchanged.
- **S0003**
  - Entry 4: the seams named; the comparison next to the preflight's probe; the 12-digit commit; the three log lines; separate rows.
  - Entry 11: comparing the text rather than the digest; the report holding the clock; the `built` line at the start too; a failed fetch in `prepare` logging `iteration failed`, "acceptable for now". The finding under 1 suggests revisiting the last one.

Defaults the agents took without asking:

- S0003 coder: a rebuilt tick starts its `TickStatus` error counts at zero rather than carrying them over (reviewer finding 4 allowed either; docstring at `src/factory/entry/run.py:200-205`).
- S0003 intake: dropped `with_image_path` from the Interface because it no longer existed.
- S0002 coder: `run_instance` takes `hosting` and `images` through `**replacements: Unpack[Replacements]` (ruff's `PLR0913`).
- S0002: `image prune -f` prunes every dangling image of the user's podman, not only the project's (the human named the command in entry 9).
- Nobody decided that a removed stage file leaves the last `<stage image>-project` image tagged until the next build replaces it.
- The reviewers of S0001 (entry 35), S0002 (entries 25, 36) and S0003 (entry 31) rewrote Interface and criteria text themselves to follow the human's answers, because the coder's and tester's edits were dropped.

Questions this leaves for the human, with the option I would choose:

- (a) A timed-out build: give its detail the build's last lines (a code change in `PodmanImages.build`, which needs the partial output from the process wrapper), or only correct the documents. F0049-S0005 takes the documents only, as entry 17 kept the behaviour; I would choose that.
- (b) Carry the error counts across a rebuild, or keep the reset. I would keep it.
- (c) Accept `FakeImages` in `security/duplicates-baseline.txt` so `make duplicates` reads `0 new` again. I would.
- (d) After F0049-S0004, fetch once per iteration instead of twice (prepare's fetch and the tick's). Not proposed; a later story if the remote's load matters.
- (e) Confirm on factory-vm that the image built from the merged `vm/Dockerfile` reports the pinned `claude --version` and `opencode --version` (S0001 criterion 6; entry 25 records only the first build), and that a real stage file (the ESP32 template's) builds and runs `make check` in the project image.

Earlier tests changed, each with its leave. The merge diffs (`git diff --diff-filter=M` per merge) match the reviewers' lists exactly:

- S0001: `tests/test_stage_image.py`, under the feature's leave for S0001.
- S0002:
  - `tests/conftest.py` (the `build_boundaries` stand-in's signature), `tests/domain/test_contract.py` and `tests/domain/test_contract_version_4.py` (4.0 → 4.1), `tests/domain/test_stop_table.py` (sixteenth row), `tests/test_stop_table.py` (scope tuple) and `tests/test_second_user_removed.py` (`images`): decision 8.
  - `tests/entry/test_health.py`: decision 7.
  - `tests/entry/test_wiring_handlers.py`: the feature's `PATH` leave for S0002.
- S0003: `tests/application/test_tick_preflight.py`, under the standing leave to move a shared helper. `tests/human_clone.py` and `tests/log_support.py` only gained helpers.

No earlier test was changed without a leave.

## 7 The slow checks

The project offers no image scan or SBOM target. `make mutants` is not run here (check 3).

`make duplicates`, a record and not a check, prints `duplicates: 1 new, 42 known, 0 gone`. The one new finding is the `FakeImages` false positive (see 4, 6c).

From `.reports/junit.xml`: 8739 tests, 729 s summed across workers, and `make test` took 84.6 s of wall time. The feature's slowest test is `tests/adapters/test_podman_images.py::test_a_build_that_reaches_its_time_limit_has_not_passed` at 10.0 s, which is `ROOMY_LIMIT` by design. The feature's other tests, about 270 of them, sum to under 11 s. The suite's slowest tests are older 10 s time-limit tests (`test_podman_timeout_status`, `test_process_session`, `test_opencode_*`).

Disk: now `/srv/factory/vm` 24.1 GB free, 1.3 GB used, against 24.3 GB free, 1.3 GB used at the record of the start (`disk start`). Used space is unchanged, and the 0.2 GB less free space lies outside the factory's directories, on the shared filesystem. The feature adds only text and builds no image in its tests, so it explains none of that 0.2 GB. This stage's own `make check`, `make duplicates` and two smoke scripts in `/tmp` ran in between and are the likely writers. There is no growth to name for the feature.

## 8 Cost

The stories cost 59 runs, 119.7 min, 683 turns and $27.56:

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 22 | 22.6 | $6.60 |
| S0002 | 21 | 69.5 | $15.10 |
| S0003 | 16 | 27.7 | $5.86 |

**S0002 stands out**: 55 % of the money and 58 % of the time. Its journal shows why:

- Its Interface named no modules or seams, so the tester stopped twice before writing tests (entries 8, 11).
- The coder stopped on four earlier tests that pinned what the story had to change (entry 16, which became the leaves of decision 8).
- It stopped again on U+FFFD (entry 27).
- Three review rounds followed whose findings were test rows only.

S0001's runs went to a human send-back after the real build (entry 25: the runtimes are native executables, decision 6) and to a round cap (entry 40) caused by a smoke-test `grep` that matched a Dockerfile comment.

Human interventions: 9 questions answered (8 `question`, 1 `round_cap`), and the stories waited 0.3 h for them. By story:

- S0001: 1 question (entry 3) and the round cap (entry 40), plus the send-back in entry 25, which was a close and not a question.
- S0002: 5 questions (entries 3, 8, 11, 16, 27).
- S0003: 2 questions (entries 3, 10).

S0002 needed the human most, for the reason above. An Interface that names the seams and the earlier tests a story will change, as S0003's intake asked for and got (entry 4), avoids most of those stops.

## Proposed stories

- **F0049-S0004** *A fetch that fails before the tick stands as the stop fetch_failed*: the finding under 1. S0003's fetch before every tick bypasses the `fetch_failed` stop, so `factory-health` stays `healthy` while nothing runs, against the operator guide.
- **F0049-S0005** *The stage image's documents say what the code does and why*: the documentation repairs under 5. The timed-out build's detail, what a restart does, the base's `PATH`, and the reasons of decisions 1, 3, 4 and 5 in `docs/decisions.md`.
- **F0049-S0006** *The stage image's tests share their helpers and pin the image without an environment*: the test copies the reviewers noted and the missing `null` row of `PodmanImages.path`, under the standing leave, with no code change.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: not accepted; 3 stories proposed (F0049-S0004 to F0049-S0006). The feature itself does what `feature.md` promised. The recommendation rests on one regression from S0003: a failed fetch now leaves `factory-health` saying `healthy`, which contradicts the operator guide. Merging brings the fix story into the backlog; closing drops it.
   1 Scope: every scope item has its story, and no story goes beyond the scope. Finding of weight: since S0003, `_follow_main` fetches before every tick with no guard (`src/factory/entry/run.py:228`). A failed fetch is logged only as `iteration failed`. The `fetch_failed` stop is never raised and `factory-health` stays `healthy` while no tick runs. Reproduced: 3 failed iterations, health exit 0, no `fetch_failed` line → S0004.
   2 Feature smoke test: green. The script drove `run_instance` with the real `PodmanImages` on a stand-in `podman`, a real bare remote and `factory-health` through six merges: base, template build, unrelated commit (no build), JDK layer with its `PATH`, broken rule (stop), failed build (stop, last 20 lines), removal (back to the base). `make check` was green as found.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: about 13 unowned items collected. The fetch regression goes to S0004, the timed-out build's detail to S0005, and the test copies plus the missing inspect-`null` row to S0006. The `FakeImages` vulture false positive needs an entry in `security/duplicates-baseline.txt`, which is the human's file. The rest are recorded with reasons and no story.
   5 Docs: five places where the documents and the code now differ: the `fetch_failed` promise (S0004); the timed-out build's detail, "a restart also ends it", "without the file nothing changes" though the containers now take the base image's own `PATH`, and the decisions entries that lack the reasons of feature decisions 1, 3, 4 and 5 (S0005).
   6 Decisions: feature decisions 1 to 8 and 9 sets of answers from the journals are listed. Agent defaults: a rebuilt tick resets its error counts; `image prune -f` removes every dangling image; a removed stage file leaves the last project image tagged. Questions (a) to (e) wait for the human, including a real build on factory-vm. Every earlier test changed had its leave; none without one.
   7 Slow checks: none beyond `make check`. `make duplicates` reports 1 new finding, the `FakeImages` false positive. The feature's slowest test is the build time-limit test at 10.0 s, which is `ROOMY_LIMIT` by design. Disk: used space is unchanged at 1.3 GB; free space fell 0.2 GB outside the factory's directories, which the feature does not explain and which this stage's own runs most likely wrote.
   8 Cost: $27.56, 59 runs, 119.7 min. S0002 took 55 % of the money because its Interface named no seams: 5 of the 9 human questions were its own (2 tester stops, earlier tests pinning what it had to change, U+FFFD). S0001's round cap came from a smoke-test grep that matched a Dockerfile comment. The stories waited 0.3 h for the human.
