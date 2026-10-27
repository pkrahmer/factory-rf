---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 477
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-27T03:05:05.851855Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-27T03:15:24.797679Z'
  stage: acceptance
  run: d96e52aef6724013a437cd61194bf9bb
stories: [F0045-S0001, F0045-S0002, F0045-S0003, F0045-S0004, F0045-S0005, F0045-S0006, F0045-S0007, F0045-S0008, F0045-S0009, F0045-S0010, F0045-S0011]
outcome: null
---

# Acceptance of Smaller items of the candidates list

## Recommendation

**Accepted with stories.** All eleven stories are merged, `make check` is green on `main`, and the feature's smoke test walked each promise of the Goal through its real entry points with no fault. What the parts left behind is three small things. Three passages in the documents miss what S0002 and S0009 added; the run-or-raise block that S0008 copied a third time is still open (`make duplicates`: `2 new`, which the human recorded for a later tidy-up); and the feature's own tests hold five leftovers. None of them breaks a promise of `feature.md`. I propose one story for each.

## 1 Scope

None. Each scope line of `feature.md` has its archived story, and I read each story's Interface against the code on `main`:
- S0001: the smoke test's `next` is `[approval, doing, docs]` in the template, in `factory/pipeline.yml` and in the demo (the human's change 1). The smoke tester's and the documenter's texts and every agent's R12 carry the short way.
- S0002: `ZfsSnapshots.reset()` runs `DROP_CACHES_COMMAND` after the rollback (`src/factory/adapters/zfs_snapshots.py`), and the wiring passes the command. `vm/setup.sh` has the step `caches`.
- S0003: the two "install it from your own copy" lines are in the script.
- S0004: `left_branch` is gone, and `RECORDS_CONTRACT == "4.0"`.
- S0005 and S0006: the reading and the model refuse a missing or relative `FACTORY_CLAUDE_HOME`/`agent_home`, and a reserved name in `container_env`.
- S0007: `ProcessResult` has no `output_abandoned`.
- S0008: `IdleShutdown`, `SystemctlPowerOff` and `idle_shutdown_of` are built and wired through `activity_tick`.
- S0009: `--idle-shutdown` and the step `poweroff` are in the script.
- S0010: the guard `tests/test_shared_imports.py` is green.
- S0011: `CheckoutPreparer(git, settings)` takes no log, and the tidy-up's ten items are done.

No story went outside the scope, and nothing from *Out of scope* was built (no start of the VM, no preflight item for either right, no content check at the sync). The human's changes 1, 4 and 5 are on `main` (`factory/pipeline.yml`, commit `6f4665ed5` for the baseline, `06cdab974` for `CLAUDE.md`). Change 2 happens on `vm`, and I cannot see it from here. Change 3 is not made: `factory/features/F0044-the-layers-go/feature.md` still has two decisions numbered 29 (see 6).

## 2 Feature smoke test

One script runs the feature's promises in order through the real entry points:
- the pipeline definitions through `RuamelPipelineDefinitionReader` and `decide`;
- `ZfsSnapshots` with `sh` stand-ins for `zfs` and the drop;
- `read_settings` and `InstanceSettings`;
- `ProcessResult`;
- `IdleShutdown` with a manual clock and `SystemctlPowerOff` with an `sh` stand-in for `sudo`, granted and refused;
- `CheckoutPreparer`;
- then `vm/setup.sh` under a stand-in `id`, and the guard.

The Python part ran as `uv run python walk.py <tmpdir>` from a `mktemp -d` folder that was removed afterwards; `<tmp>` stands for that folder. Output:

```text
1 template/factory/pipeline.yml ['approval', 'doing', 'docs'] 3
1 factory/pipeline.yml ['approval', 'doing', 'docs'] 2
1 demo/todo-service/project/factory/pipeline.yml ['approval', 'doing', 'docs'] 3
1 decide docs -> docs round 1
1 smoke tester ends with docs: True
2 reset: ['zfs rollback -r tank/factory/vm@base', 'drop']
2 failed drop: snapshot command <tmp>/baddrop failed: sudo: a password is required
2 wired command: sudo -n /usr/local/bin/factory-drop-caches
4 False 4.0
5 refused: FACTORY_CLAUDE_HOME: missing
5 refused: FACTORY_CLAUDE_HOME: is not an absolute path
5 refused: FACTORY_IMAGE_ID_FILE: missing
5 refused: FACTORY_CONTAINER_ENV: holds HOME, which the factory sets itself
5 read: /srv/c
6 refused: Field required
6 refused: Value error, is not an absolute path
6 refused: Value error, holds HOME, which the factory sets itself
7 ['exit_status', 'stdout', 'stderr', 'timed_out', 'duration', 'stopped']
8 setting '' -> 0
8 setting '0' -> 0
8 setting '30' -> 30
8 setting 'x' refused: FACTORY_IDLE_SHUTDOWN_MINUTES: is not a whole number of minutes
8 granted: tick at 10 min, idle
8 granted: tick at 29 min, idle
8 granted: tick at 30 min, a stop
8 granted: tick at 59 min, idle
8 granted: tick at 60 min, idle
8 log: idle shutdown: idle for 30 minutes, powering the machine off
8 refused: tick at 10 min, idle
8 refused: tick at 29 min, idle
8 refused: tick at 30 min, a stop
8 refused: tick at 59 min, idle
8 refused: tick at 60 min, idle
8 log: idle shutdown: idle for 30 minutes, powering the machine off
8 log: idle shutdown: power off failed: sudo: a password is required; the factory runs on
8 sudo was asked: -n /usr/bin/systemctl poweroff
11 ['self', 'git', 'settings']
```

The shell part, from the root of the checkout, with a stand-in `id` that prints `1000` first on `PATH`:

```text
$ sh -n vm/setup.sh && echo syntax-ok
syntax-ok
$ grep -c 'not installed; install it from your own copy of vm/' vm/setup.sh
2
$ sh vm/setup.sh --device /dev/null --repository-url https://example.invalid/r.git --idle-shutdown <v>   # v = 0, x, 30
--idle-shutdown 0: exit 2: setup.sh: --idle-shutdown takes at least 1 minute, not 0
--idle-shutdown x: exit 2: setup.sh: --idle-shutdown takes a whole number of minutes, not x
--idle-shutdown 30: exit 2: setup.sh: run as root
$ sh vm/setup.sh --help | grep -c -- --idle-shutdown
2
$ uv run pytest tests/test_shared_imports.py -p no:cacheprovider | tail -1
13 passed in 0.46s
```

Green. The stop at minute 30 starts a new stretch, so the tick at 59 (29 minutes later) does not power off and the tick at 60 does. A refused power-off is one log line, and the loop runs on.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Collected from the coders', reviewers' and documenters' entries and checked against `main`:

1. **The run-or-raise block** of `src/factory/adapters/power_off.py` repeats `ZfsSnapshots._execute` and `PodmanRuns._query`, with a third `_ROOT = Path("/")` (S0008, journal 13 to 47). `make duplicates` prints `duplicates: 2 new, 42 known, 0 gone` today. In S0008's journal 33 the human recorded it "for a later tidy-up". → S0013.
2. **Copied test helpers and stale test data** (reviewers' notes):
   - `_in_order` and `_lines_with` exist three times (S0009 entry 20).
   - `tests/contract_login_support.py` holds a second `SCHEMAS` (S0004 entries 14 and 18; after S0010 it sits in that support module).
   - `tests/git_support.py:44` gives the smoke test `next: [approval, doing]` (S0001 entries 17 and 19).
   - `_record_get_repo` is shared but keeps its underscore (S0011 entry 20).
   - Two rows of `test_the_preparer_takes_only_the_git_and_the_settings` repeat the earlier test's rows (S0011 entries 12 to 20).

   → S0014.
3. **Three `sudoers` blocks in `vm/setup.sh`** (steps `sudoers`, `caches`, `poweroff`, each stage–`cmp`–`cp`–`chmod 0440`–`visudo -cf`–remove), named by S0002's and S0009's coders as "a story of its own". No story: each block is pinned by text tests of three stories (F0043-S0003, S0002, S0009). A shared shell function would need leaves across all of them, and the copies are short and identical in shape. The human may decide otherwise.
4. **The empty-value message** of `--idle-shutdown` ends in a trailing space (`... not ` at `vm/setup.sh:43`, S0009 entries 14 and 18). It is harmless and no criterion pins it. No story.
5. **The comment at `src/factory/application/stalls.py:112`** ("Whatever the agent left on the other branch is dropped") speaks of the agent, which since F0044 cannot move the host's checkout. The restore it explains stays by the feature's *Out of scope* (S0004 entries 7 to 22). No story; it is worth a word in the next story that touches `stalls.py`.
6. **`sh` recorder stand-ins**: `_stand_in` of `tests/adapters/test_power_off.py`, `_shell_zfs` of `tests/adapters/test_zfs_snapshots_drop_caches.py`, `write_drop` of `tests/zfs_support.py` and the fixture `sudo_stand_in` look alike (S0002 entry 30, S0008 entries 43 and 47). They differ in body, exit status and record form. No story: one writer would need a design of its own for little gain.
7. **`make types` crashed twice with `Error 139`** (a segfault of mypy, no type error): S0004's doing stage stalled on it (journal 8), and S0010's coder met it once (entry 10). Both came after S0002 was merged. *Out of scope* says that "the crash is watched after S0002". So the cache drop did not end it, or the crash has another cause. This is for the human to watch. No story from me.
8. Taken care of within the feature, listed for completeness: S0008's stale criteria 1, 5 and 8 were rewritten by the reviewer (journal 31). S0003's Description was left stale by the documenter as not theirs (entry 26), but the story is archived and the code matches its criteria.

## 5 Documentation

I read `README.md`, `docs/operator-guide.md` and `docs/project-guide/` for the feature's subjects. The smoke test's two ways out (`operator-guide.md` around line 1338, decision entry at `docs/decisions.md:1196`), the page cache, the required settings, contract `4.0` and the idle shutdown (`## The machine`, *The idle shutdown*) are each explained once and agree with the code. Three passages miss what the feature added:
- `docs/operator-guide.md:337` still says that "`factory` has no `sudo` right but the page-cache helper and the four `zfs` commands of the optional `--sudoers` fallback". With `--idle-shutdown` it also has `/usr/bin/systemctl poweroff`. S0008's documenter named the sentence for S0009's, and S0009's did not change it. Step 9 and *The idle shutdown* say it correctly, so a reader who reads on is not misled, but an operator auditing the rights from that sentence would be.
- The table of the environment file's variables (`docs/operator-guide.md` around line 502) has no row for `FACTORY_IDLE_SHUTDOWN_MINUTES`, which step `environment` writes with the option (step 14 says so).
- `docs/project-guide/README.md:93` says `vm_support.py` holds "the thirteen step names (`STEPS`)". `STEPS` has fifteen since `caches` and `poweroff`.

→ S0012. I found no example that no longer runs: the smoke-test commands of S0003, S0006 and S0007 that read the documents or the code still print their `Expect:`.

## 6 Decisions taken for the human

Accept or revisit:
1. `feature.md` decisions 1 to 20 (the split and order; `UV_LINK_MODE`, `leftovers_command` and the kill's "Open" falling with F0043/F0044; `output_abandoned` goes and the drain stays; the slip in a document goes to `docs`; no module imports a test module; what idle means; the `sudoers` line for `systemctl poweroff`; a failed power-off is a log line; the guide describes the start; off by default; `left_branch` with contract `4.0`; the two required settings; the cache drop through one helper; no content check at the sync; a changed unit from the operator's own copy; the model checks `container_env`; the tidy-up's list; the number and name). Leaves 21 to 31 and answers 32 (a) to (c).
2. Answers in the journals:
   - S0002 entries 4, 9 and 14 (text criteria for the step `caches`; the drop's detail is `failure_detail`; the shared fixture `sudo_stand_in` in `tests/conftest.py`, with the leave of decision 22 widened to the four tests that use it).
   - S0003 entry 8 (`_install_conditions` narrowed to lines whose command is `install`).
   - S0008 entries 4 and 9 (six criteria added; the details of `failure_detail`/`no_end_detail`; the fixture's reuse), entry 33 (the round count restarted for one finding; the run-or-raise duplicate recorded for later, hence S0013) and entry 52 (the smoke test's stand-in body corrected by the human).
   - S0009 entry 4 (everything as text criteria; the exact line `not asked; the factory gets no power-off right`).
   - S0010 entry 4 (the guard reports the statement's first line; the message format pinned).
   - S0011 entry 4 (rows added; the tester chooses the new names).
3. Earlier tests changed. Each was named with its leave in its reviewer's entry, and I found none without one:
   - decisions 22 to 31 as listed in `feature.md`, S0002's widened leave (entry 14) and S0003's (entry 8);
   - the standing leave to move a shared helper: `tests/shipped_agents.py` and `tests/test_claude_agent_texts.py` (S0001); `tests/contract_support.py` and `test_contract_version_2.py`/`_3.py` (S0004); `tests/domain/test_default_git_identity.py` (S0005); `tests/domain/test_settings_container_env.py` and `tests/settings_support.py` (S0006); `tests/conftest.py` with `holder_file` (S0007); `tests/test_vm_setup_text.py`, `tests/test_vm_setup_caches.py` and `tests/vm_support.py` (S0009);
   - `tests/entry/test_run.py` (S0008) gained one test only, with no leave needed.
4. **Open, the human's own:** change 3 is not made. As written it would collide: renaming the second decision 29 to 30 in F0044's `feature.md` gives two decisions numbered 30, because the next one ("after S0001's pre-check") is already 30. Either renumber 29 to 32 there and the references after it, or name the decision by its date. `planning/v1.2-candidates.md` still says "decision 29 (b)" and "29 (c)".

## 7 Slow checks

The project offers no slow check beyond `make check` but `make duplicates` (a record, `2 new, 42 known, 0 gone`, see 4.1) and `make documents`; `make mutants` is the sweep's (3). `make check` ran green here: `test: green (166.8 s)`, coverage 99.57 %, 7591 tests. The slowest tests in `.reports/junit.xml` take ten seconds each, all of them waits on a time limit: the `[255-at-the-limit]` and `[137-at-the-limit]` rows of `tests/adapters/test_podman_timeout_status.py`, `tests/adapters/test_make_commands.py::test_command_reaching_its_time_limit_is_killed`, and three tests of `tests/adapters/test_claude_runtime_resume.py`. None of them is this feature's.

Disk: at the previous record (`disk start`) the volume of `/srv/factory/vm` had 48.5 GB free with 1.2 GB used by the dataset. Now (`disk acceptance`) it has 45.8 GB free, with 1.2 GB used. The 2.7 GB less free space lies outside the dataset, on the volume that `/srv/factory/vm/state` and `/tmp` share. The feature's changes do not explain it: no dependency, no image pin and no large file was added. A likely cause, not checked from here, is the stage images and uv caches the rebuilds after the merges left behind. `podman image prune` and `podman system df` on `vm` would tell.

## 8 Cost

134 runs, 256.0 min, 1094 turns, $41.69 for eleven stories, about $3.79 a story. **S0008 stands out**: 24 runs, 46.1 min, $9.10, more than a fifth of the feature. Its journal says why:
- two intake questions (entries 3 and 8) and a tester stop;
- three review rounds, each of which added a criterion (10, 11) or sharpened one row;
- the round cap passed at journal 32, and the human restarted the count for one finding (entry 33);
- a smoke-test question about the stand-in's body (entry 52).

S0002 is second (15 runs, 35.0 min, $5.57). Its tests and code contradicted each other twice over the install line and the stand-in `sudo`, and the human answered three times (entries 4, 9, 14). The cheapest was S0005 (6 runs, $2.31), with no rework.

Human interventions: 11 questions answered: 10 questions (S0002 ×3, S0003 ×1, S0008 ×3, S0009, S0010 and S0011 ×1 each) and 1 round cap (S0008, journal 32). The stories waited 0.4 h for them in all. S0008 needed the human most: four interventions, because its Interface stated behaviours that no criterion tested (intake, entry 3) and its review kept adding criteria.

## Proposed stories

- `backlog/F0045-S0012-the-documents-name-the-power-off-right-and-the-fifteen-steps.md`: the three passages of 5 (the `sudo` rights sentence, the environment file's row, the fifteen steps); documents only.
- `backlog/F0045-S0013-the-wrappers-run-their-command-through-one-run-or-raise-helper.md`: the duplicate the human recorded in S0008's journal 33 for a later tidy-up; `make duplicates` back to `0 new`.
- `backlog/F0045-S0014-the-tests-of-f0045-say-once-what-they-share.md`: the five leftovers the reviewers noted in the feature's own tests (4.2). Three of them need the human's leave when the story is refined.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 3 stories proposed

   1 Scope: none. Every scope line has its merged story and its code on `main`, and nothing from *Out of scope* was built. The human's change 3 (the double decision 29 in F0044's `feature.md`) is not yet made.
   2 Feature smoke test: green. One script ran every promise through its real entry point: the definitions and `decide`, `ZfsSnapshots` with stand-ins, `read_settings` and `InstanceSettings`, `ProcessResult`, `IdleShutdown` with `SystemctlPowerOff` granted and refused, `CheckoutPreparer`, then `vm/setup.sh` and the guard. Its output is pasted in the report.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the run-or-raise block that S0008 copied a third time (`make duplicates`: 2 new, which the human recorded for later), giving S0013. Five test leftovers the reviewers noted, giving S0014. Without a story: the three `sudoers` blocks in `vm/setup.sh`, a trailing space in one message, a stale comment at `stalls.py:112`, and the look-alike `sh` stand-ins. `make types` segfaulted twice after S0002 (Error 139), which is for the human to watch.
   5 Documentation: three passages miss what the feature added. The `sudo` rights sentence at `operator-guide.md:337` omits the power-off right, the environment file's table has no `FACTORY_IDLE_SHUTDOWN_MINUTES` row, and `project-guide/README.md:93` still says thirteen steps instead of fifteen. This gives S0012.
   6 Decisions: `feature.md` decisions 1 to 32 and the human's journal answers in S0002, S0003 and S0008 to S0011 are listed in the report. Every earlier test changed names its leave. Change 3, as written, would leave two decisions numbered 30.
   7 Slow checks: nothing beyond `make check` (green, 166.8 s, 99.57 %). The slowest tests are 10 s time-limit waits, none of them this feature's. The disk has 2.7 GB less free outside the dataset (48.5 to 45.8 GB), which the feature's changes do not explain; old stage images or caches on `vm` are likely.
   8 Cost: $41.69 over 134 runs. S0008 stands out ($9.10, 24 runs: intake questions, three review rounds that added criteria, and the round cap passed). 11 human interventions (10 questions, 1 round cap) and 0.4 h waited; S0008 needed the human most (4).
