---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 490
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-01T08:24:22.082229Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-01T08:38:27.493193Z'
  stage: acceptance
  run: ca5c228d13514063b7b29456f9eaa3b7
stories: [F0047-S0001, F0047-S0002, F0047-S0003, F0047-S0004, F0047-S0005, F0047-S0006, F0047-S0007, F0047-S0008, F0047-S0009]
outcome: null
---

# Acceptance of The factory runs in a Cloud Run job

## Recommendation

**Not accepted.** Every Scope item has its merged story, `make check` was green as I found it, and each option works on its own. But the feature's smoke test is red on the Goal itself: `vm/job-start.sh` does not turn a bare job into an instance that can work.

- The script never installs `/usr/local/bin/git-credential-factory`, the only credential route of the factory's git (`src/factory/entry/wiring.py:140`). So in a job no fetch of a private project and no push can authenticate.
- The script makes the state folder but not its `runs` folder, and the opencode runtime (the job's default) does not make it either. So the preflight's `agent-run-probe` fails at every start, and the machine stops.

Both are small repairs to one script (F0047-S0010). Two further stories carry a documentation repair (F0047-S0011) and the refresher's untested rules (F0047-S0012).

## 1 Scope

Each Scope item has its story in `done/`:

- copy snapshots (S0001);
- the `job` profile (S0002) and its storage without `fuse-overlayfs` (S0009);
- `metadata-block` (S0003);
- the refresher (S0004);
- the helper's host check and `--code-url` (S0005);
- the start script and *On Cloud Run* (S0006);
- the opencode lockdown (S0007);
- the idle `exit` (S0008).

Each was read against the code it names. No story went into Out of scope: no company value, no change to the Claude Code runtime or the records contract, no hosting base URL.

The gap is in the Goal, not in a single item. *A start script that turns a bare Debian job into a running instance* is not reached:

1. **The credential helper.** `vm/setup.sh` installs the helper (step `tools`, `vm/setup.sh:394-400`). `vm/job-start.sh` has no such line; its only `install` is runc's. Yet `git_environment()` always names `/usr/local/bin/git-credential-factory`. S0005 split the code from the project and S0006 cloned the code without a credential, and neither story's Interface placed the helper for the project. The probes P20 and P21 used `http.extraHeader`, not the helper, so no run caught it.
2. **The runs folder.** `_agent_runtime` hands the runtimes `<state>/runs` (`src/factory/entry/wiring.py:405`). `ClaudeCodeRuntime` makes that folder (`src/factory/adapters/claude_runtime.py:412`). `OpencodeRuntime` writes its configuration file there without making it (`src/factory/adapters/opencode_runtime.py:615-619`). An earlier test pins that as an error: `tests/adapters/test_opencode_runtime.py:281`, row `state-missing`, from F0020-S0004. `vm/job-start.sh` makes only `$FACTORY_STATE`. A job starts with an empty state at every start and defaults to opencode, so the probe fails every time.

A smaller point: feature decision 16 names `--code-ref` beside `--code-url` for `vm/setup.sh`. Only `--code-url` was built; `setup.sh` keeps its `--ref` (`vm/setup.sh:19`). The Scope line asks only for `--code-url`, so I list it under 6, not as a gap.

## 2 Feature smoke test

The walk-through of an operator who gives a bare job its environment. The script was a temporary file outside the checkout (`smoke.py`). It does five things:

1. It runs the real `vm/job-start.sh` through the suite's stand-ins (`tests/vm_support.py::run_job_start`: `apt-get`, `curl`, `sha256sum`, `install`, `nft`, `mount`, `git`, `uv`, `podman`). The job gives the required inputs, `https_proxy`, a token endpoint with its companions, a company provider file (`corp`, `https://llm.example.invalid/v1`), the model map and `FACTORY_IDLE_SHUTDOWN_MINUTES=30`.
2. It takes the environment that `factory-run` received. Through the real entry points it then runs:
   - `refresh_token.main(["--once"], ...)` with an injected token source;
   - `boundaries_from_environment` with `FakeHostingService`, over a real git clone of a bare project at `FACTORY_CHECKOUT`, the agents of the repository's `claude/` as the code checkout's, and a stand-in `podman` that records its words, answers `--version` and `image exists`, and prints `000` with exit 7 for the metadata probe;
   - every item of `machine_extras` in order.
3. It drives the boundaries' `CopySnapshots` on the job's workspace and base.
4. It calls the idle shutdown's power switch from `idle_shutdown_of(..., request_stop)`.
5. It asks the real `git credential fill` through the factory's own `git_environment()`, with the helper where the job leaves it, and then with `vm/git-credential-factory` in its place.

Two adjustments belong to my harness, not the product. The harness's token folder is made `0700`, because a job's real folder is its secret mount; see 6. The `exec` line compares the stand-in's parent with the caller of `sh`.

```text
$ e=$(mktemp -d) && trap 'rm -rf "$e"' EXIT && uv run python <tmp>/smoke.py "$PWD" "$e"
job-start exit: 0 | steps: inputs proxy packages runc metadata directories storage code tools image token start
factory-run started by exec (its parent is the caller of sh): True
image build: --runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay build --network=host
refresher calls: [['-m', 'factory.entry.refresh_token', '--once'], ['-m', 'factory.entry.refresh_token']]
  FACTORY_SNAPSHOTS=copy
  FACTORY_CONTAINER_PROFILE=job
  FACTORY_AGENT_RUNTIME=opencode
  FACTORY_IDLE_SHUTDOWN_ACTION=exit
installed into /usr/local/bin: []
token refreshed: valid 3599 s, next in 600 s
refresh --once: 0 | login file: tok-1
settings: copy job opencode exit | snapshots: CopySnapshots
  token-file: True
  podman: True podman version 5.4.2
  snapshots: True workspace <tmp>/job/root/work, base <tmp>/job/root/base
  stage-image: True
  metadata-block: True refused
  opencode: True
  agent-run-probe: False agent runtime failed: cannot write the state directory <tmp>/job/root/state/runs: [Errno 2] No such file or directory: '<tmp>/job/root/state/runs/opencode-7ec11a85-d97
every podman call starts with the three job words: True
changed: [('x.txt', 'modified'), ('y.txt', 'added')]
after reset: one False
idle exit: ProcessExit stop set: True
helper the factory's git asks: /usr/local/bin/git-credential-factory | installed by job-start: False
git credential fill in the job: exit 128 | <tmp>/job/prefix/usr/local/bin/git-credential-factory get: 1: <tmp>/job/prefix/usr/local/bin/git-credential-factory: not found / fatal: could not read Username for 'https://example.invalid': terminal prompts disabled
git credential fill with the helper installed: exit 0 | username line: ['username=x-access-token']
```

The same script with `<state>/runs` made by hand before the preflight (`... "$e" with-runs`, from `settings:` on):

```text
  agent-run-probe: False agent runtime failed: cannot start <tmp>/bin/podman: [Errno 2] No such file or directory: PosixPath('<tmp>/job/root/work/checkout')
```

That second failure is my stand-in's: it does not run the sync container that copies the checkout into the workspace. So the run past the prepare needs a real engine and is left to the machine, as F0046-A0002 left it.

**Red.** What holds:

- The script runs its twelve steps in order and ends in `exec factory-run`. It builds the image with the three job words and starts the refresher once and then in the background.
- It derives `copy`, `job`, `opencode` and `exit`.
- The settings read, and every container item passes: `podman`, `snapshots`, `stage-image`, and `metadata-block` with `refused`. Every podman call carries the three words.
- The copy snapshots list a modified and an added file and reset them.
- The idle exit sets the loop's stop.

What fails:

- The probe dies on the missing `runs` folder.
- The factory's git gets no credential in the job's layout (`exit 128`), while the same request through the shipped helper answers `x-access-token`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Collected from the coder, documenter and reviewer entries, each checked on this tree.

1. S0001, coder (entries 10, 14, 18): `CopySnapshots.changed_paths` turns no `OSError` into a `SnapshotError`; the Interface named only `reset` and `advance`. Still true. A diff over a tree with an unreadable file would leave the stage environment with a raw `OSError`. No story: a real case is rare here, as root in the job.
2. S0001, documenter (entry 22): `docs/operator-guide.md:91` still says there is one stage environment, "every stage runs on a ZFS dataset". `FACTORY_WORKSPACE` (`:86`) is still "the dataset's mount point". Still true; it goes into F0047-S0011.
3. S0001, reviewer notes: `_reset_on` duplicates `_reset` within `tests/adapters/test_copy_snapshots.py`, and `_tree` and `_reset` copy `tests/adapters/test_fake_snapshots.py`, which criterion 9 kept unchanged. A test-helper tidy-up only; no story.
4. S0003, coder and tester: `run_words` in `tests/wiring_support.py` finds only a call whose first word is `run`, so it misses every `job`-profile call. `_metadata_probe` is typed with the concrete `PodmanRuns`. Reviewer note: `_ended` in `tests/application/test_preflight_metadata_block.py:24` copies `_result` of `tests/application/test_container_environment.py:181`. All three are still true; no story.
5. S0003, documenter: the `nft` file was written from knowledge, not run. S0006's script loads exactly that text; no job run is recorded in a journal. It is the human's to see on the first real start.
6. S0004, reviewer notes after the human's entry 52 ("any further edge case goes into its entry as a note, which I record on `main` for a later story"). The notes:
   - no test that `main` restores the previous `SIGTERM` and `SIGINT` handlers;
   - no test that `KeyboardInterrupt` and `SystemExit` stay uncaught;
   - `masked` (`src/factory/domain/tokens.py:31`) has no direct test;
   - the `incomplete-read` row computes its expected detail with the code's own expression;
   - `SECOND` and `SECOND_CLIENT` in `tests/test_hosting_search.py` are unclear names.

   I found them recorded nowhere on `main` (`grep` over `planning/` and `docs/`), so they go into F0047-S0012.
7. S0004, human (entry 14): the vulture finding on `OpenUrl.__call__` goes into the baseline. It is in `security/duplicates-baseline.txt:41` as `unused method '__call__'`. Since S0007 vulture labels it `unused function`, so `make duplicates` now reads `1 new, 41 known, 1 gone` and fails (`Error 1`; run today, see 7). The baseline is the human's file (`security/`): one line to relabel. No story.
8. S0005, coder and smoke tester: changing `--code-url` on a machine that already has a checkout does not re-clone, as for `--repository-url`; the guide says so. Reviewer note: `_guard` in `tests/test_vm_setup_code_url.py:122-127` copies `vm_support.enclosing_if` with `elif`. No story.
9. S0006, coder:
   - a Dockerfile without the `ARG` line leaves `FACTORY_CLAUDE_VERSION` exported empty rather than unset;
   - `vm/setup.sh` and `vm/job-start.sh` each read the pins with their own `sed`.

   Reviewer notes: the two sides of the checksum, mount and ref rules are separate test functions, and `test_factory_run_gets_the_stage_image_the_image_step_built` repeats rows of `:360`. No story.
10. S0006, documenter: the decision *Every tool of the machine's image is pinned* is not marked as changed by *Debian's packages follow the base image's release*. It still speaks of "the eight Debian tools by `name=version`" (`docs/decisions.md:287`). Into F0047-S0011.
11. S0007, everyone: the archived Interface still says "The existing opencode runtime tests pass unchanged", which the human's entry 8 excepted. It is an archive text; the journal holds the exception. No story.
12. S0008, coder and documenter: with `exit` the log still says `idle shutdown: idle for <n> minutes, powering the machine off`. The Description kept it and the guide says so. In a job's log that sentence misleads, but it is a product choice (6). Reviewer note: `instance_settings` in `tests/entry/test_run_idle_exit.py:55` copies the `settings` fixture of `tests/entry/test_run.py:123`.
13. My own: decision 4 of `feature.md` (the four podman words) is corrected by decision 19, and the code, the guide and `docs/decisions.md:1252` all follow 19. Nothing stale there.

## 5 The documentation as a whole

`README.md` gains one sentence and the pointer to *On Cloud Run*; it holds. The guide's sections of the feature agree with the code I ran: *The job profile*, *The metadata server in a job*, *Without ZFS*, *A bearer token for the model API*, *The code and the project apart*, *What opencode may load and contact* and *In a job*. So does the chapter *On Cloud Run*, with the step list, the derived variables and the end of an execution. Findings:

1. **A contradiction that misleads.** *On Cloud Run* promises that "every start installs the tools, clones the code and builds the stage image again" and ends in a running instance. Both of 2's failures are missing from it: the helper the factory's git needs, and the runs folder. The fix is code (F0047-S0010), and its docs criterion adds the two lines to the chapter's step list.
2. **Stale against copy snapshots.** `docs/operator-guide.md:91`, "**The stage environment.** There is one: every stage runs on a ZFS dataset", is false since S0001. `:86` calls `FACTORY_WORKSPACE` "the dataset's mount point". The `FACTORY_DATASET` row needs "with `zfs`". The missing-variable order (dataset, workspace, image) is the order with `zfs`; with `copy` it is the base first. F0047-S0011.
3. **An old decision not marked.** `docs/decisions.md:285-287`, *Every tool of the machine's image is pinned*, has no `Changed in part by` bullet, although the log marks such entries (six `Superseded in part by` lines). The new entry (`:1307`) names it, but a reader of the old entry does not learn of the change. F0047-S0011.
4. **The token's folder in a job.** *What the job needs* mounts the hosting token with `--set-secrets=/secrets/hosting-token=...`. *The hosting-service token* requires that the token's folder belong to the factory's user and carry no bit for group or others; in a job the factory's user is root. The chapter does not say that the secret's mount folder must meet that rule, nor what to do when it does not. Whether Cloud Run's secret mount passes is unmeasured (6). F0047-S0011 states the rule in the chapter.

## 6 Decisions taken for the human

To accept or revisit:

1. The feature's decisions 1 to 20 of `feature.md`. All hold in the code, with decision 4 corrected by 19 (S0009). Decision 16's `--code-ref` was not built for `vm/setup.sh`, which keeps `--ref`; the job script uses `FACTORY_CODE_REF`.
2. S0001 (entry 4): a base that is a file gets its own sentence, `the base <b> is not a directory`. The model validator refuses `zfs` with a base too.
3. S0002 (entry 11): `version` and `image_exists` keep the workspace as their working directory in both profiles.
4. S0003 (entry 4): a timed-out probe fails whatever it printed, and a four-digit last line is "could not tell". The documenter named the section *The metadata server in a job*, not *The metadata server*, to avoid a second anchor of that name.
5. S0004:
   - the human, entry 9: `main`'s injected `source` and `sleep`; the "child's environment" read as `os.environ`; `TokenRefresher` takes its writer.
   - the human, entries 14 and 57: the per-file ignore `PLR0913, S310` for `src/factory/adapters/oauth_token.py` in `pyproject.toml`, and its leave to import `urllib.request` and `http.client`.
   - the human, entries 36 and 52: two round-cap restarts; any `Exception` of one refresh is a failure; after entry 52 the review sent back only for a criterion without a test.
   - coder default: the adapters are built in `factory.entry.wiring`, not in `refresh_token.py`.
6. S0005 (entries 9, 25): what follows the secrets wait is tested from the script's text; the code clone moved after the wait (B).
7. S0006:
   - entry 9: the runc checksum is checked by reading only, "for tonight". The test's default row checks only a 64-character hex value. Worth a second look now that the night is over: a baseline entry or a line filter would let a test pin the value.
   - entry 26: the journal line reworded by the human's commit 32c10e4d4.
   - entry 26: the two runtime versions derived from `vm/Dockerfile`; `FACTORY_OPENCODE_MODELS` stays the job's.
8. S0007 (entry 8): `enabled_providers` added to an earlier expectation.
9. S0008:
   - entry 8: `recording_of` widened.
   - Description: the log line `powering the machine off` stays with `exit`. Revisit: in a job it names a power-off that does not happen.
10. Open, for the human to measure:
    - Does a Cloud Run secret mount at `/secrets` pass the `token-file` item (owner uid 0, no bit for group or others)? If not, the job's preflight stops at every start, and the operator cannot `chmod` a platform mount.
    - Does the first real start load the `nft` file as written?
11. Open, from 2: the runs folder for opencode is made by nobody on a fresh VM state either. I propose the job's repair in the script (F0047-S0010). An earlier test (F0020-S0004, `state-missing`) forbids the runtime from making it. Whether the runtime should make its folder as Claude Code's does, under your leave, is yours.

Earlier tests changed, each with its leave:

- S0002: `tests/adapters/test_podman_runs_results.py` and `tests/conftest.py` (standing leave, `podman_recorder`).
- S0003: `tests/conftest.py`, `tests/wiring_support.py`, `tests/entry/test_wiring_container_extras.py`, `tests/entry/test_wiring_copy_snapshots.py`, `tests/adapters/test_claude_runtime_container.py` (standing leave).
- S0004:
  - `tests/entry/test_run.py` and `tests/conftest.py` (standing leave, `restored_signals`);
  - `tests/test_hosting_search.py` (the human, entries 14 and 57).
- S0005: `tests/test_git_credential_helper.py`, `tests/vm_support.py`, `tests/conftest.py` (standing leave).
- S0006:
  - `tests/test_stage_image.py`, the story's leave, which names `test_the_stage_image_has_no_floating_reference`;
  - `tests/git_support.py` (standing leave);
  - `tests/vm_support.py` (additions only).
- S0007: `tests/adapters/test_opencode_runtime_provider.py` (the human, entry 8, and the standing leave) and `tests/adapters/opencode_stand_in.py` (standing leave).
- S0008: `tests/entry/test_run.py` (the human, entry 8).
- S0009: `tests/adapters/test_podman_runs_job_profile.py` (the story's leave over S0002's test).
- S0001 changed no earlier test.

**A finding:** in S0006, `test_each_debian_package_is_pinned` of `tests/test_stage_image.py` was replaced by `test_each_debian_package_is_installed_by_name_alone`, which reverses its rule. The story's leave names only `test_the_stage_image_has_no_floating_reference`. The reviewer (entries 19, 34, 42) counted the reversal "within the leave for the file", and criterion 12 needs it. But no leave names that test. Please confirm it.

## 7 The slow checks

The project offers nothing beyond `make check` today: no image scan, no SBOM. `make mutants` is check 3.

My `make check`: `test: green (176.7 s)`, `check: green`, branch coverage 99.56 %. `.reports/junit.xml` holds 7921 tests. The slowest take 10.0 s each, all `ROOMY_LIMIT` tests of earlier features:

- `tests.adapters.test_podman_timeout_status::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run[137-at-the-limit]` and `[255-at-the-limit]`;
- `tests.adapters.test_claude_runtime_resume::test_first_call_ended_by_the_time_limit_is_not_resumed`;
- `tests.adapters.test_claude_runtime_resume::test_call_killed_by_the_time_limit_has_no_model_duration[a whole reply printed]`;
- `tests.adapters.test_claude_runtime_provider_limit::test_a_call_past_its_time_limit_ends_time_limit_though_it_named_the_limit`;
- `tests.adapters.test_process_session::test_time_limit_ends_every_process_of_the_group[run_streaming-own-session]`.

The feature's own 180 test cases take 7.2 s together; the slowest is `tests.test_vm_job_start::test_the_token_is_never_printed_written_or_passed_on_a_command_line`.

`make duplicates` (a record, not a check) reads `duplicates: 1 new, 41 known, 1 gone` and fails with make's `Error 1`: the relabelled `OpenUrl.__call__` of 4, item 7.

Disk: `/srv/factory/vm` 41.9 GB free and 1.2 GB used now, against 40.7 GB free and 1.2 GB used at the previous record (the previous acceptance). `/srv/factory/vm/state` and `/tmp` each hold 0.0 GB used. No growth.

## 8 Cost

The nine stories: 145 runs, 339.8 min, 1311 turns, $52.51.

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

**S0004 stands out**: a quarter of the runs and 27 % of the cost. Its journal tells why. Each review round found a new class of fault at the token endpoint's boundary:

- a non-UTF-8 secret;
- `isdigit` against `int()`;
- `http.client.HTTPException`;
- any other `Exception` ending the daemon.

It passed its round cap twice (entries 35, 51). Coder edits to the work item were dropped as outside the write paths, so the reviewer rewrote the Interface (entries 59, 69). One more round went to a test slip of its own (entries 61 to 65).

S0006 is second: four review findings were criteria without tests, and a journal line tripped `make secrets` (entry 25).

Human interventions: 19 questions answered (17 `question`, 2 `round_cap`), 7.1 h waited. S0004 needed the human most, 6 times: two test-design answers (entries 9, 14), two round-cap restarts (36, 52) and one leave for `http.client` (57). The causes were the HTTP boundary's edge cases and an earlier test that forbade `urllib.request`. Then S0005 (4), S0006 (3) and S0002 (2); S0009 none.

## Proposed stories

- **F0047-S0010** *The start script installs the credential helper and makes the runtime's runs folder*: the two failures of the feature smoke test; without them no job can push or pass its preflight.
- **F0047-S0011** *The operator guide and the decision log agree with copy snapshots and the job*: findings 2 to 4 of 5, documents only.
- **F0047-S0012** *The refresher's remaining rules get their tests*: S0004's review notes, which the human meant to keep for a later story and which are recorded nowhere else.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: not accepted; 3 stories proposed (F0047-S0010 to S0012)

   1. Scope: every Scope item has its story and none goes out of scope, but the Goal is not reached. `vm/job-start.sh` never installs `/usr/local/bin/git-credential-factory`, the factory git's only credential (`src/factory/entry/wiring.py:140`). It also makes the state folder but not `<state>/runs`, which `OpencodeRuntime` writes into without making it (`src/factory/adapters/opencode_runtime.py:615`; F0020-S0004's `state-missing` row pins that as an error). Decision 16's `--code-ref` was not built for `vm/setup.sh`.
   2. Feature smoke test: red. It runs the real `vm/job-start.sh` through the suite's stand-ins, then `factory-run`'s environment through the refresher, `boundaries_from_environment`, every preflight item, the copy snapshots, the idle exit and the real `git credential fill`. The steps, derived settings, job words, `metadata-block` (`refused`), snapshots and idle exit hold. `agent-run-probe` fails with `cannot write the state directory <state>/runs`, and the factory's git gets no credential (exit 128, helper `not found`) where the shipped helper answers. The run after the prepare needs a real engine and was not run.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: 13 items collected. S0004's review notes, which the human (entry 52) meant to keep for a later story, are recorded nowhere, so they become S0012. The duplicates baseline labels `OpenUrl.__call__` as `method` while vulture now says `function`, so `make duplicates` fails `1 new, 41 known, 1 gone` (the human's `security/`). Test-helper copies and the `powering the machine off` log line with `exit` get no story.
   5. Docs: *On Cloud Run* promises a working instance and misses both repairs (S0010's docs criterion). `docs/operator-guide.md:91` still says every stage runs on a ZFS dataset. The 2026-10-16 pin decision is not marked as changed. The token folder's 0700 rule is not named for a secret mount (S0011).
   6. Decisions: feature decisions 1 to 20 and every story's answers and defaults, listed for the human. Open: does a Cloud Run secret mount pass `token-file`? Should the opencode runtime make its own runs folder (needs a leave)? Is the runc checksum still checked "for tonight" by reading only? Finding: S0006 reversed `test_each_debian_package_is_pinned`, and its leave names only another test of that file.
   7. Slow checks: nothing beyond `make check`, which was green (`test: green (176.7 s)`, 99.56 %, 7921 tests; the slowest are the earlier 10.0 s `ROOMY_LIMIT` tests; the feature's 180 test cases take 7.2 s). Disk has not grown (41.9 GB free against 40.7 GB, 1.2 GB used both times).
   8. Cost: $52.51, 145 runs, 339.8 min. S0004 stands out ($14.39, 36 runs, two round-cap restarts: each review found a new fault class at the token endpoint). 19 questions answered (17 `question`, 2 `round_cap`), 7.1 h waited; S0004 needed the human most (6).

   Not done: the two temporary folders I made under `/tmp` (copies of the stories' text and the smoke script, no secrets) could not be removed because the `rm` call was refused. The three stories pass `factory.entry.check_story`.
