---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 493
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-01T12:40:33.906830Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-01T12:51:59.588450Z'
  stage: acceptance
  run: 29a18c5ff5384aab984a9aad4747f095
stories: [F0047-S0001, F0047-S0002, F0047-S0003, F0047-S0004, F0047-S0005, F0047-S0006, F0047-S0007, F0047-S0008, F0047-S0009, F0047-S0010, F0047-S0012]
outcome: null
---

# Acceptance of The factory runs in a Cloud Run job

## Recommendation

**Accepted.** Every Scope item has its merged story, and `make check` was green as I found it. The feature smoke test, red in F0047-A0001, is now green end to end through the instance's real entry points. The job script installs the credential helper, the factory's git gets the project's credential (and only for the project's host), the opencode runtime makes its own runs folder, the whole preflight passes, and one tick of the instance passes main's check and ends `idle`.

What is left is small. S0010 left the two runtimes with a copied helper and an untested write-failure branch, so I propose one story for it (F0047-S0013). The open measurements and the product questions are listed under 6 for you.

## 1 Scope

Each Scope item has its story in `done/`, read against the code it names:

- copy snapshots (S0001);
- the `job` profile (S0002) and its native-overlay storage (S0009);
- `metadata-block` (S0003);
- the refresher (S0004), whose remaining rules have their tests since S0012;
- the helper's host check and `--code-url` (S0005);
- `vm/job-start.sh` and *On Cloud Run* (S0006);
- the opencode lockdown (S0007);
- the idle `exit` (S0008).

S0010 closes the Goal gap F0047-A0001 found:

- `vm/job-start.sh:125` installs the code checkout's `vm/git-credential-factory` in step `code`;
- `OpencodeRuntime` makes its state directory (`src/factory/adapters/opencode_runtime.py:616-620`);
- with `exit` the idle line says `ending the factory's process`.

No story went into Out of scope. There is no company value, no change to the Claude Code runtime's behaviour or the records contract, and no hosting base URL.

One point remains, as in F0047-A0001 and not a gap of the Scope list. Feature decision 16 names `--code-ref` beside `--code-url`, but `vm/setup.sh` still takes `--ref` (`vm/setup.sh:19`). The job uses `FACTORY_CODE_REF`. The Scope line asks only for `--code-url`, so it is listed under 6.

## 2 Feature smoke test

This is the walk-through of an operator who gives a bare job its environment and expects a working instance. The script was a temporary file outside the checkout (`smoke.py`, 173 lines). It does seven things:

1. It runs the real `vm/job-start.sh` through the suite's stand-ins (`tests/vm_support.py::run_job_start`). The job's inputs are:
   - `https_proxy` and the token endpoint with its companions;
   - the guide's example provider file (`corp`, `https://llm.example.invalid/v1`, prices 0), the model map;
   - `FACTORY_IDLE_SHUTDOWN_MINUTES=30`.
2. It does for real what the stand-in `install` only recorded: it installs the checkout's helper under the job's prefix.
3. It takes the environment `factory-run` received and runs `refresh_token.main(["--once"], ...)` with an injected token source.
4. It clones a bare project (with a `Makefile` whose targets print `<target>: green`) at `FACTORY_CHECKOUT`. It calls `boundaries_from_environment` with `FakeHostingService` and then every item of `machine_extras`. The stand-in `podman` records its words and:
   - answers `--version`, `image exists` and the runtime's version;
   - prints `000` with exit 7 for the metadata probe;
   - runs the sync and check containers' `sh -c` on the host, with each `--volume` and the `--workdir` mapped back;
   - plays a completed opencode reply that ends in `question`.
5. It drives the `CopySnapshots` of the boundaries and the idle shutdown's power switch from `idle_shutdown_of`.
6. It asks the real `git credential fill` through `git_environment()` with the installed helper, once for the project's host and once for another host.
7. It runs one real `build_tick(...).run()`.

My harness made one adjustment that does not belong to the product. The harness's secret folder is made `0700`, because a job's real folder is its platform's mount (see 6).

```text
$ e=$(mktemp -d) && trap 'rm -rf "$e"' EXIT && uv run python <tmp>/smoke.py "$PWD" "$e"
job-start exit: 0 | steps: inputs proxy packages runc metadata directories storage code tools image token start
factory-run started: True
  FACTORY_SNAPSHOTS=copy
  FACTORY_CONTAINER_PROFILE=job
  FACTORY_AGENT_RUNTIME=opencode
  FACTORY_IDLE_SHUTDOWN_ACTION=exit
installed into <prefix>/usr/local/bin: ['runc', 'git-credential-factory']
token refreshed: valid 3599 s, next in 600 s
refresh --once: 0 | login file: tok-1
settings: copy job opencode exit | snapshots: CopySnapshots
  token-file: True
  podman: True podman version 5.4.2
  snapshots: True workspace <tmp>/job/root/work, base <tmp>/job/root/base
  stage-image: True
  metadata-block: True refused
  opencode: True
  agent-run-probe: True
state runs folder exists after the preflight: True
agent run: login file mounted: True | provider config mounted: True | hosting token in argv: False
every podman call starts with the three job words: True
changed: [('x.txt', 'modified'), ('y.txt', 'added')]
after reset: one False
2026-11-01T12:48:15Z idle shutdown: idle for 30 minutes, ending the factory's process
idle exit stop set: True
factory.log tail: 11-01T12:48:15Z idle shutdown: idle for 30 minutes, ending the factory's process
git credential fill for example.invalid: exit 0 | ['username=x-access-token'] | token shown: True
git credential fill for code.example.invalid: exit 128 | fatal: could not read Username for 'https://code.example.invalid': terminal prompts disabled | token shown: False
2026-11-01T12:48:15Z preflight: podman: podman version 5.4.2
2026-11-01T12:48:15Z preflight: snapshots: workspace <tmp>/job/root/work, base <tmp>/job/root/base
2026-11-01T12:48:15Z preflight: metadata-block: refused
one tick: TickOutcome stopped=None event=Event(kind='idle', work_item=None, pull_request=None, feature=None, remote_state='e043454e0e05f3e529e47faa9ead53dbd27c5b82', detail='') dispa
  log: idle shutdown: idle for 30 minutes, ending the factory's process
  log: preflight: podman: podman version 5.4.2
  log: preflight: snapshots: workspace <tmp>/job/root/work, base <tmp>/job/root/base
  log: preflight: metadata-block: refused
health: none
```

(`token shown: True` for the project's host is the helper's `password=` line that git asks for; for any other host the helper gives nothing.)

**Green.** Both failures of F0047-A0001 are gone:

- the helper is installed and answers the project's host only;
- `<state>/runs` is made by the runtime, and `agent-run-probe` passes.

The tick passes the preflight and main's check and ends `idle`, with no stop in `health.json`. On the way, my first runs failed only on my own harness: the token folder's mode, a provider file in opencode's format instead of the factory's, a reply without the allowed `question`, and the stand-in ignoring `--workdir`. Each failure named its cause precisely.

A real engine, a real opencode and the platform remain unproven here. They are the Kumpel trial's (decision 21).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

These are from the two new stories, and from F0047-A0001's list as it stands today.

1. S0010, coder (entry 10): the `OSError` branch of `OpencodeRuntime._write_files` (`src/factory/adapters/opencode_runtime.py:625-626`) lost its only test, because the changed row now fails at the `mkdir`. Coverage confirms it. The same branch of `ClaudeCodeRuntime._write_files` (`src/factory/adapters/claude_runtime.py:422-423`) was already uncovered.
2. My own, from the same story: `OpencodeRuntime._make_state_directory` is a copy of `ClaudeCodeRuntime._make_state_directory`. The reviewer counted it as "the same pattern", but `CLAUDE.md` puts what the runtimes share in `factory.adapters.agent_launch`, where `state_directory_error` already lives. Together with 1 this is F0047-S0013.
3. S0012, coder (entries 17, 21, 25, 28): `src/factory/entry/refresh_token.py:136` is uncovered. It is the `if __name__ == "__main__"` line. No story.
4. S0012, documenter (entry 32): the docs do not state that `main` restores the earlier signal handlers or that a `KeyboardInterrupt` or `SystemExit` is not caught. That is deliberate (criterion 5); no story.
5. S0012's Description left out S0004's `incomplete-read` row (its expected detail is computed with the code's own expression) and the names `SECOND` and `SECOND_CLIENT` in `tests/test_hosting_search.py`. Both need a leave over S0004's tests; listed under 6.
6. Carried from F0047-A0001, still true, no story (as that report judged and you merged):
   - `CopySnapshots.changed_paths` turns no `OSError` into a `SnapshotError`;
   - the test-helper copies (`_reset`/`_tree` of the snapshot tests, `_ended`, `_guard`, `instance_settings`) and `run_words`, which misses `job`-profile calls;
   - a changed `--code-url` does not re-clone an existing checkout;
   - the archived S0007 Interface's "pass unchanged".
7. Resolved since F0047-A0001:
   - `make duplicates` now reads `duplicates: 0 new, 42 known, 0 gone` (run today);
   - the documentation repairs of the removed S0011 are on `main` (see 5);
   - the runc checksum is a constant tested by its shape (decision 21);
   - the idle line with `exit`.

## 5 The documentation as a whole

I read `README.md` and the chapters the feature touched as a newcomer: *On Cloud Run*, *The job profile*, *Without ZFS*, *A bearer token for the model API*, *The code and the project apart*, *The idle shutdown* and *The hosting-service token*. I also read `docs/project-guide/agents.md` (*The opencode runtime*) and `watching.md`.

F0047-A0001's documentation findings are repaired on `main`:

- **The stage environment.** `docs/operator-guide.md:94` names both ways, and `:86` gives the workspace's meaning per way. The missing-variable order is given for `zfs` and `copy` (`:96`), and the `FACTORY_DATASET` row (`:83`) says "with `zfs`".
- **The pin decision.** `docs/decisions.md:291` marks *Every tool of the machine's image is pinned* as superseded in part by *Debian's packages follow the base image's release*.
- **The secret mount.** *What the job needs* states the 0700 and owner rule for the secret's folder, the two failures, and that the mount is unmeasured (`:907`).
- **The chapter after S0010.** *On Cloud Run*, step 8, names the helper's install and why. *In a job* gives both idle lines. The project guide no longer says the opencode runtime leaves its state directory to others.

I checked the chapter's step list, the derived variables and the twelve steps against the script and against the smoke test's run, and they agree.

Not findings:

- `README.md:24` opens with "every stage runs in throwaway containers on one ZFS dataset" and only then says the factory also runs in a job, which has no ZFS. The sentence reads as the VM's case and the next one points to the chapter, so a newcomer is not misled.
- The guide's generic line (`:828`) says the `poweroff` sentence comes "just before the factory asks the machine to power off". *In a job* (`:833`) gives the `exit` line next to it.

## 6 Decisions taken for the human

To accept or revisit.

**The feature's own decisions, 1 to 21 of `feature.md`.** All hold in the code. Decision 4 is corrected by 19. Decision 21 is built as written:

- the runtime makes its runs folder under the leave over F0020-S0004's row;
- the idle line;
- runc's checksum is a constant tested by its shape;
- S0011 was removed after the operator's work on `main`.

**Earlier answers and defaults.** S0001 to S0009 are as listed in F0047-A0001's section 6 and unchanged since.

**S0010:**
- (Description, the human) the script installs the helper of its own code ref;
- (entry 6) `EXIT_LINE` in `tests/entry/test_run_idle_exit.py` for the two `exit` tests;
- (coder default, entry 10) the `mkdir` runs before the run files' `try`/`finally`, so that the cleanup cannot hide the error;
- (coder default) two explicit `IdleShutdown(...)` calls in `idle_shutdown_of` rather than a `partial`.

**S0012:**
- (entry 6) the handler during `fetch` is checked in the loop row only, and the shared token helpers move now under the standing leave;
- (entry 11) the tester's own line 108 reads `error.code`;
- (entry 26) the journal line the secrets scan flagged is reworded by your commit 1b6034367, now a standing leave (`96582ae30`).

**Open, for you:**

1. Decision 16's `--code-ref` for `vm/setup.sh`, which keeps `--ref`. Rename it, or record that the VM keeps `--ref`?
2. S0004's `incomplete-read` row and the names `SECOND` and `SECOND_CLIENT`: a leave for a later test story, or leave them?
3. Still unmeasured: does a Cloud Run secret mount at `/secrets` pass `token-file` (owner uid 0, no bit for group or others)? Does the first real start load the `nft` file as written? Both are for the Kumpel trial. If the mount fails, the job stops at its preflight at every start, and the guide says so.
4. Still unanswered from F0047-A0001: S0006 replaced `test_each_debian_package_is_pinned` with `test_each_debian_package_is_installed_by_name_alone` without a leave that names it. Decision 17 makes the reversal necessary, but no leave names the test. Please confirm it.

**Earlier tests the two new stories changed, each with its leave:**

- S0010:
  - `tests/adapters/test_opencode_runtime.py`, the row `state-missing` becoming `state-a-file` (the leave in the story's Description, the human's, 2026-11-01);
  - `tests/entry/test_run_idle_exit.py`, `EXIT_LINE` in two tests (the human's answer, entry 6);
  - `tests/vm_support.py`, the option `failing_install_target`, which earlier callers do not use (the story's Interface);
  - `tests/application/test_idle_shutdown.py`, an addition only.
- S0012: `tests/conftest.py`, `tests/entry/test_refresh_token.py` and `tests/token_support.py`. The secret-file, login-file and environ fixtures, `scripted` and `never_sleep` moved there (the standing leave to move a shared test helper, and the human's answer in entry 6).

No earlier test was changed without a leave in these two stories.

## 7 The slow checks

The project offers nothing beyond `make check` today: no image scan, no SBOM. `make mutants` is check 3.

My `make check`: `test: green (174.6 s)`, `check: green`, branch coverage 99.54 %. `.reports/junit.xml` holds 7945 test cases. The slowest take 10.0 s each, all `ROOMY_LIMIT` tests of earlier features:

- `tests.adapters.test_podman_timeout_status::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run[255-at-the-limit]` and `[137-at-the-limit]`;
- `tests.adapters.test_opencode_resume_session::...[timed-out-with-events]`;
- `tests.adapters.test_process_streaming::test_child_is_killed_at_the_time_limit_and_no_later_line_is_passed`.

The 43 test cases of the modules S0010 and S0012 wrote or extended take 0.97 s together. The slowest is `tests.test_vm_job_start_instance::test_the_code_step_installs_the_checkout_s_helper_between_the_checkout_and_uv` (0.22 s).

`make duplicates` (a record): `duplicates: 0 new, 42 known, 0 gone`.

**Disk.** `/srv/factory/vm` holds 1.2 GB used now, as at the previous record (the previous acceptance); `/srv/factory/vm/state` and `/tmp` 0.0 GB both times. But the free space of the file system they share fell from 41.9 GB to 35.2 GB, and 6.7 GB went to something outside the folders the record measures. The feature's changes since then (one script line, one `mkdir`, one log text, tests) do not explain it. A container image or a build cache on the same file system is the likely place. Worth a look before the free space reaches the factory's floor.

## 8 Cost

The eleven stories: 167 runs, 394.1 min, 1474 turns, $58.20.

| Story | Runs | Minutes | Cost |
| --- | --- | --- | --- |
| S0001 | 11 | 22.9 | $4.92 |
| S0002 | 14 | 29.4 | $3.58 |
| S0003 | 11 | 25.1 | $3.25 |
| S0004 | 36 | 93.3 | $14.39 |
| S0005 | 20 | 44.2 | $8.19 |
| S0006 | 21 | 62.3 | $9.88 |
| S0007 | 13 | 25.7 | $3.19 |
| S0008 | 13 | 28.1 | $3.84 |
| S0009 | 6 | 8.8 | $1.27 |
| S0010 | 7 | 20.6 | $2.49 |
| S0012 | 15 | 33.7 | $3.20 |

**S0004 still stands out**: 22 % of the runs and 25 % of the cost. As F0047-A0001 told from its journal, each review round found a new fault class at the token endpoint's boundary, and the story passed its round cap twice.

Of the two new stories, S0010 went through in one pass with one question. S0012 took 15 runs for a tests-only story with no code change. One round went to `mypy` on the tester's own line (entry 10), one to a copied `never_sleep` the reviewer found (entry 19), and one to a journal line that `make secrets` read as a key (entry 25).

**Human interventions:** 23 questions answered (21 `question`, 2 `round_cap`), 9.0 h waited. The two new stories added 4 questions and about 1.9 h: S0010 one, S0012 three. S0004 still needed the human most, 6 times: two test-design answers (entries 9, 14), two round-cap restarts (36, 52) and one leave for `http.client` (57). The causes were the HTTP boundary's edge cases and an earlier test that forbade `urllib.request`.

## Proposed stories

- **F0047-S0013** *The agent runtimes share one state-directory helper, and a failed write is tested*. S0010 copied Claude Code's `_make_state_directory` into the opencode runtime and left both runtimes' write-failure branch without a test. One helper in `agent_launch` and a test that both runtimes refuse an unwritable state directory close both.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 1 story proposed (F0047-S0013)

   1. Scope: every Scope item has its merged story, and S0010 closes F0047-A0001's Goal gap. `vm/job-start.sh:125` installs the code checkout's credential helper, and `OpencodeRuntime` makes its own runs folder. Nothing went out of scope. One point stays open: decision 16's `--code-ref` was never built for `vm/setup.sh`, which keeps `--ref`.
   2. Feature smoke test: green (it was red in A0001). It runs the real `vm/job-start.sh` through the suite's stand-ins, then the refresher, `boundaries_from_environment` and every preflight item on `factory-run`'s environment, then the copy snapshots, the idle `exit`, the real `git credential fill` and one `build_tick().run()`. The preflight passes, `metadata-block` and `agent-run-probe` included. The helper answers the project's host only, and the tick passes main's check and ends `idle`. A real engine, a real opencode and the platform stay for the Kumpel trial.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: S0010 left the `OSError` branch of `OpencodeRuntime._write_files` untested (`opencode_runtime.py:625-626`; Claude Code's `:422-423` had no test before either). It also copied `_make_state_directory` from the Claude Code runtime, though `CLAUDE.md` puts shared runtime code in `agent_launch`. Both go into F0047-S0013. `refresh_token.py:136` is the uncovered `__main__` line. A0001's remaining notes are still true and still without a story. `make duplicates` now reads 0 new, 42 known, 0 gone.
   5. Docs: A0001's three findings are repaired on `main` (`operator-guide.md:83,86,94,96,907`; `decisions.md:291`). *On Cloud Run* step 8, *In a job* and the project guide match S0010's code. No contradiction found.
   6. Decisions: feature decisions 1 to 21 hold, and S0010's and S0012's answers and defaults are listed. Earlier tests changed by S0010 and S0012 each have a leave. Open for the human: `--code-ref` against `--ref`; a leave for S0004's `incomplete-read` row and the names `SECOND` and `SECOND_CLIENT`; the unmeasured Cloud Run secret mount and `nft` load; and, unanswered since A0001, the confirmation of S0006's reversal of `test_each_debian_package_is_pinned` without a leave that names it.
   7. Slow checks: nothing beyond `make check`, which was green (`test: green (174.6 s)`, 99.54 %, 7945 cases). The slowest are earlier 10.0 s `ROOMY_LIMIT` tests; the new stories' 43 cases take 0.97 s. Disk: the factory's folders did not grow (1.2 GB used), but free space on their file system fell from 41.9 to 35.2 GB. The feature's changes do not explain that 6.7 GB.
   8. Cost: $58.20, 167 runs, 394.1 min. S0004 still stands out ($14.39, 36 runs, two round-cap restarts). S0010 cost $2.49 in one pass; S0012 took 15 runs for tests only, over a mypy slip, a copied helper and a secrets-flagged journal line. 23 questions answered (21 `question`, 2 `round_cap`), 9.0 h waited; S0004 needed the human most (6).

   The proposed story passes `factory-check-story`. Not done: my temporary folder `/tmp/acc-smoke` (only the smoke script, no secrets) is still there, because the `rm` call was refused.
