---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 497
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-01T15:35:13.431565Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-01T15:53:49.944488Z'
  stage: acceptance
  run: 076815d60f574835a16fbda280158504
- number: 3
  speaker: factory
  kind: done
  at: '2026-11-01T15:55:37.023077Z'
  stage: done
stories: [F0047-S0001, F0047-S0002, F0047-S0003, F0047-S0004, F0047-S0005, F0047-S0006, F0047-S0007, F0047-S0008, F0047-S0009, F0047-S0010, F0047-S0012, F0047-S0013, F0047-S0014, F0047-S0015]
outcome: accepted
---

# Acceptance of The factory runs in a Cloud Run job

## Recommendation

**Accepted.** Every Scope item has its merged story. `make check` was green as I found it. The feature smoke test is green end to end, and it now also covers what the three new stories built:
- an unwritable runs folder stops the probe with its reason (S0013);
- a new VM instance gets its first base (S0014);
- `--ref` is refused with the hint (S0015).

The two open points of F0047-A0002's section 6 that were code are closed. Nothing found is worth a story. One example line in the operator guide is imprecise (under 5), and the disk lost 13.8 GB of free space that the feature does not explain (under 7). Both are listed for you.

## 1 Scope

Each Scope item still has its story in `done/`:
- copy snapshots (S0001);
- the `job` profile (S0002), with native-overlay storage (S0009);
- `metadata-block` (S0003);
- the refresher (S0004), whose remaining rules were tested in S0012;
- the helper's host check and `--code-url` (S0005);
- `vm/job-start.sh` and *On Cloud Run* (S0006);
- the opencode lockdown (S0007);
- the idle `exit` (S0008);
- the job's credential helper and runs folder (S0010).

The three stories since F0047-A0002 are those decision 22 names, built as described:

- **S0013.** `make_state_directory` is in `src/factory/adapters/agent_launch.py:324`. Both runtimes call it before their run files' `try` (`claude_runtime.py:365`, `opencode_runtime.py:590`), and both copies of `_make_state_directory` are gone. The two test notes of S0004's review are folded in.
- **S0014.** The step `datasets` of `vm/setup.sh` takes `<dataset>@base` when none exists (`vm/setup.sh:215-219`). It does this after the quota and the mount point's owner, before `delegation`. An existing base is left alone.
- **S0015.** `--code-ref` replaces `--ref` (`vm/setup.sh:75`). The old name ends in `fault "--ref is now --code-ref"` before `need_value` (`:76`). This closes the point of decision 16 that F0047-A0001 and F0047-A0002 had left open. No `--ref` of the script is left in `README.md`, `docs/` (outside the human's `docs/runs/`) or `vm/`.

None of the three goes into Out of scope. S0013 changes code that a job runs, but it is a pure refactor: the same messages and the same order. Decision 22's remark that none of the three changes a job holds, so the tag `v1.2-job-1` needs no move for them.

Finding: none.

## 2 Feature smoke test

This is the operator's walk-through: a bare job with its environment becomes an instance that passes its preflight, ticks and ends itself when idle. The second part is the VM operator's setup with the new option and a new instance's first base. The script was a temporary file outside the checkout (`smoke.py`, 188 lines). It does nine things:

1. It runs the real `vm/job-start.sh` through the suite's stand-ins (`tests/vm_support.py::run_job_start`). The inputs are:
   - `https_proxy`;
   - the token endpoint with its scope, client id and secret file;
   - the guide's example provider file (`corp`, prices 0) and the model map;
   - `FACTORY_IDLE_SHUTDOWN_MINUTES=30`.

   It then does for real what the stand-ins only recorded: it puts the checkout's `claude/` and helper into the cloned code, and installs the helper under the job's prefix.
2. It runs `refresh_token.main(["--once"], ...)` on `factory-run`'s environment, with an injected token source.
3. It clones a bare project at `FACTORY_CHECKOUT`. The project has a `Makefile` whose targets print `<target>: green` and the repository's `factory/pipeline.yml`. The script then calls `boundaries_from_environment` with `FakeHostingService`, and then every item of `machine_extras`. A stand-in `podman` does the following:
   - it records its words;
   - it answers `--version` and `image exists`;
   - it prints `000` with exit 7 for the metadata probe;
   - it answers opencode's `--version` with the Dockerfile's pin;
   - it plays a completed opencode reply that ends in `question`;
   - it runs every other container's command on the host, with each `--volume` and the `--workdir` mapped back.
4. It drives the boundaries' `CopySnapshots`: `advance`, a new file, `changed_paths`, `reset`.
5. It runs the real `git credential fill` with `git_environment()` and the installed helper, once for the project's host and once for another host.
6. It runs one real `build_tick(...).run()`.
7. It passes that tick's outcome to the `IdleShutdown` that `idle_shutdown_of` builds. The boundaries get a manual clock that is moved 30 minutes ahead, and `request_stop` is a `threading.Event`.
8. It empties `<state>/runs`, makes it `0500`, and runs `agent-run-probe` again (S0013).
9. It runs `sh vm/setup.sh --ref v9` and `--code-ref v9 --help`. It then runs the step `datasets` through the stand-ins of `tests/test_vm_setup_first_base.py`, once for a new machine and once for one with dataset and base (S0014, S0015).

One adjustment of the harness does not belong to the product. As in F0047-A0002, the stand-in's token folder is made `0700`, because a job's real folder is its platform's mount (see 6).

```text
$ d=$(mktemp -d) && trap 'rm -rf "$d"' EXIT && uv run python <tmp>/smoke.py "$PWD" "$d"
exit 0
job-start exit: 0 | steps: inputs proxy packages runc metadata directories storage code tools image token start
factory-run started: True
  FACTORY_SNAPSHOTS=copy
  FACTORY_CONTAINER_PROFILE=job
  FACTORY_AGENT_RUNTIME=opencode
  FACTORY_IDLE_SHUTDOWN_ACTION=exit
  FACTORY_CODE_REF=v9.9.9
the refresher ran --once, then in the background: [['-m', 'factory.entry.refresh_token', '--once'], ['-m', 'factory.entry.refresh_token']]
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
runs folder made by the runtime: True
agent run: login file mounted: True
agent run: provider in a mounted config: True
agent run: env names: ['HOME', 'OPENCODE_CONFIG', 'OPENCODE_DISABLE_AUTOUPDATE', 'OPENCODE_DISABLE_DEFAULT_PLUGINS', 'OPENCODE_DISABLE_MODELS_FETCH', 'PATH', 'PYTHONDONTWRITEBYTECODE']
agent run: hosting token in argv: False
every podman call starts with the job's words: True
first podman call: --runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay --version
changed: [('one', 'added')]
after reset: one exists: False
git credential fill for example.invalid: exit 0 | token shown: True
git credential fill for code.example.invalid: exit 128 | token shown: False
2026-11-01T15:49:53Z preflight: podman: podman version 5.4.2
2026-11-01T15:49:53Z preflight: snapshots: workspace <tmp>/job/root/work, base <tmp>/job/root/base
2026-11-01T15:49:53Z preflight: metadata-block: refused
probe call: ['factory-login', '--api-login', '<tmp>/secrets-tok/api-login', '', 'opencode', 'run', '--format', 'json', '--auto']
one tick: stopped=None event=idle
stops in health.json: no file
2026-11-01T15:49:53Z idle shutdown: idle for 30 minutes, ending the factory's process
idle exit: stop set: True
factory.log tail: 2026-11-01T15:49:53Z idle shutdown: idle for 30 minutes, ending the factory's process
probe with an unwritable runs folder: False agent runtime failed: cannot write the state directory <tmp>/job/root/state/runs: [Errno 13] Permission denied: '<tmp>/job/roo
setup.sh --ref v9: exit 2 | setup.sh: --ref is now --code-ref | --code-ref in usage: True
setup.sh --code-ref v9 --help: exit 0 | usage: setup.sh --device <path> --repository-url <url> [--code-url <url>] [--instance <nam | --code-ref in usage: True
setup datasets (new): snapshots [['snapshot', 'tank/factory/vm@base']] | setup: datasets: made tank/factory/vm at /srv/factory/vm/work; set the quota 30G on tank/factory/vm; gave /srv/factory/v
setup datasets (second run): snapshots [] | setup: datasets: found tank/factory and tank/factory/vm at /srv/factory/vm/work with the quota 30G and its base
```

(Two noise lines are left out: uv's `Bytecode compiled` and git's warning that the project's first clone was empty. `token shown: True` for the project's host is the `password=` line git asks the helper for; for any other host the helper gives nothing.)

**Green.** The parts in order:
- the job reaches `factory-run` with the four job settings;
- the refresher writes the login file;
- every preflight item passes, `metadata-block` and `agent-run-probe` included;
- the run gets the login file, the provider configuration and the three opencode switches, and no hosting token;
- the tick ends `idle` with no stop;
- the idle `exit` sets the stop and logs `ending the factory's process`.

The new stories also hold:
- An unwritable runs folder fails the probe with `cannot write the state directory …` (S0013), rather than a run that dies without saying why.
- `--ref` gets the hint and exit 2 (S0015).
- A new instance's `datasets` takes `tank/factory/vm@base`, and a second run takes none (S0014).

My first two runs failed on my own harness only:
- The secret folder's mode: `token-file` named it exactly.
- The stand-in `podman` looked for `opencode` as the container's first word, but the runtime starts it through `factory-login`. The probe then said `ended died`, as it should.

A real engine, a real opencode, the platform's secret mount and `nft` are still unproven here. They are for the trial at work.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

From the three new stories, then F0047-A0002's list as it stands today.

1. S0013, coder (entries 7, 15) and reviewer (entry 17): `ClaudeCodeRuntime._state_error` (`src/factory/adapters/claude_runtime.py:411`) now has one caller, `_write_files`. The opencode runtime calls `state_directory_error` directly. It is left by the Interface's "nothing else changes", and it is small enough that no story is worth it. Its Description leaves a shared write helper to a later story, and I see no need for one: the two runtimes write different files.
2. S0013, coder (entry 7): `opencode_runtime.py:633` (the `_resume` branch with no time left) is uncovered. The other uncovered lines of that module, 228, 230 and 479 (event validation, `time_limit`), are also older than this feature (F0020). No story here.
3. S0014, coder (entries 10, 14, 18): the guide still told the operator to take the base by hand. The docs stage repaired it (`docs/operator-guide.md:557, 1034`).
4. S0015, coder (entry 13): `docs/runs/` still names `--ref`. Those are the human's files, rightly left alone.
5. F0047-A0002's list, item by item:
   - **The copied state-directory helper and the untested write failure:** done in S0013.
   - **S0004's `incomplete-read` row and `SECOND`/`SECOND_CLIENT`:** done in S0013.
   - **`refresh_token.py:136`:** still the uncovered `__main__` line.
   - **Signal handlers and `KeyboardInterrupt` undocumented:** deliberate.
6. Carried from F0047-A0001, still true, still without a story:
   - `CopySnapshots.changed_paths` turns no `OSError` into a `SnapshotError`;
   - the test-helper copies (`_reset`/`_tree`, `_ended`, `_guard`, `instance_settings`);
   - `run_words` misses `job`-profile calls;
   - the archived S0007 Interface's "pass unchanged".

   A changed `--code-url` does not re-clone an existing checkout. That one is now documented (`docs/operator-guide.md:521`).

`make duplicates`, run today: `duplicates: 0 new, 42 known, 0 gone`.

## 5 The documentation as a whole

I read these as a newcomer:
- `README.md`;
- the operator guide's chapters the three stories touched: the checkout table (`:384`), *The code and the project apart* (`:521`), the option table (`:540`), the script's steps (`:557`, `:564`, `:579`), the GCP steps (`:712-736`), *The rebuild after a merge* (`:890`), *On Cloud Run* (`:921`, `:946`) and the preflight's table (`:1034`, `:1044`);
- `docs/decisions.md`, *The code and the project apart* (`:1282`);
- `docs/project-guide/agents.md` (`:43`, `:64`, `:114`).

They agree with each other and with the code:
- `--code-ref` is named the same everywhere, with the refusal of `--ref` in one place (`:540`). The job's `FACTORY_CODE_REF` is explained beside it.
- Step 5 says the script takes the first base before the delegation. The `dataset` row now says that an instance made by `vm/setup.sh` has its base, and that the `zfs snapshot` advice is for a dataset made by hand.
- The project guide names `agent_launch.make_state_directory` for both runtimes. No `_make_state_directory` is left.

One example is imprecise. It is older than this feature, but this feature made it wrong in both of its ways. The `agent-run-probe` paragraph (`docs/operator-guide.md:1044`) gives, as the probe's message for a missing base, `snapshot command reset failed: no base at <path>`, with the advice `make it with zfs snapshot <dataset>@base`. That message is the copy adapter's (`src/factory/adapters/copy_snapshots.py:58`), where there is no `zfs`. The job never shows it anyway, because `vm/job-start.sh:113` makes the base folder at every start. On ZFS the message is `snapshot command zfs rollback -r <dataset>@base failed: cannot open '<dataset>@base': dataset does not exist`, which the Kumpel trial saw and which the guide nowhere quotes. Since S0014, a new instance does not reach the message. This misleads no one about what the factory does, so it is not a story: a one-sentence repair on `main`, as you did with S0011's. It is listed under 6.

Not a finding: `README.md` names no option of the script and needed no change.

## 6 Decisions taken for the human

To accept or revisit.

**The feature's own decisions, 1 to 22 of `feature.md`.** All hold in the code. Decision 4 is corrected by 19. Decision 22 is built as written:
- S0013, with S0004's two test notes;
- S0014;
- S0015, with the hint `setup.sh: --ref is now --code-ref` and exit 2.

**Earlier answers and defaults.** S0001 to S0012 are as listed in F0047-A0001's and F0047-A0002's sections 6, and unchanged since.

**S0013:**
- (coder default, entries 7 and 15) `make_state_directory` raises the error itself. Rejected: it returns the error for each runtime to raise.
- (reviewer, entry 9) criterion 5 was added: the `OSError` is the cause.
- (tester, entry 13) criterion 5 has a test function of its own.
- (coder, reviewer) `ClaudeCodeRuntime._state_error` is left with one caller.

**S0014:**
- (the human, entry 4) four answers:
  - a failing-`snapshot` criterion;
  - a criterion for an existing dataset without a base;
  - criterion 1 covers the `said` form;
  - the order against the owner is read from the script's text.
- (coder default, entry 10) the base check stands on its own after the owner check. Rejected: inside the `zfs create` branch.
- (reviewer, entry 12) the two sides of "a missing base is taken" are rows of one test.

**S0015:**
- (the human, entry 4) criterion 3 got a bare `--ref` row and the usage line.
- (the human, entry 9) the leave was extended to one row of `tests/test_vm_setup_text.py`, and criteria 1 and 2 are tested from the script's text.
- (coder default, entry 13) `--ref` has its own `case` arm, not the `*)` arm. The variable stays `ref`.

**Open, for you:**

1. **The example under 5** (`docs/operator-guide.md:1044`): quote the ZFS rollback message beside the copy adapter's, each with its own advice. I would make it a one-line repair on `main`, not a story.
2. **Still unmeasured, from F0047-A0002:** does a Cloud Run secret mount at `/secrets` pass `token-file` (owner uid 0, no bit for group or others), and does the first real start load the `nft` file as written? Both are for the trial at work, at the tag `v1.2-job-1`.
3. **The disk under 7.**

F0047-A0002's other open points are closed:
- `--code-ref`, by S0015;
- the `incomplete-read` row and the names, by S0013;
- the reversal of `test_each_debian_package_is_pinned`, confirmed by you in decision 22.

**Earlier tests the three new stories changed, each with its leave** (checked against each merge's `git diff --name-status` under `tests/`):

- S0013:
  - `tests/adapters/test_oauth_token.py`: only the row `incomplete-read`, now the literal `"IncompleteRead(0 bytes read)"`;
  - `tests/test_hosting_search.py`: only `SECOND` → `ANOTHER_URLLIB_IMPORTER` and `SECOND_CLIENT` → `ANOTHER_HTTP_CLIENT_IMPORTER`, with the row ids kept.

  Both are under your leave in the story's Interface (decision 22).
- S0014: none; it only added `tests/test_vm_setup_first_base.py`.
- S0015:
  - `tests/test_vm_setup.py`, two words `--ref` → `--code-ref` (the leave in the story's Interface);
  - `tests/test_vm_setup_text.py`, one row `("ref", "ref")` → `("code-ref", "ref")` (your answer, entry 9).

No earlier test was changed without a leave.

## 7 The slow checks

The project offers nothing beyond `make check` today: no image scan, no SBOM. `make mutants` is check 3.

My `make check` gave `test: green (167.6 s)` and `check: green`, with branch coverage at 99.58 %. `.reports/junit.xml` holds 7971 test cases. The slowest take 10.0 s each, all `ROOMY_LIMIT` tests of earlier features:
- `tests.adapters.test_podman_timeout_status::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run[255-at-the-limit]` and `[137-at-the-limit]`;
- `tests.adapters.test_claude_runtime_provider_limit::test_a_call_past_its_time_limit_ends_time_limit_though_it_named_the_limit`;
- `tests.adapters.test_opencode_resume_session::…[timed-out-with-events]`.

The three new stories' test modules take 2.72 s together (22 cases):
- `test_vm_setup_first_base` 2.66 s, slowest `test_a_missing_base_is_taken_once_and_named[made]` at 0.42 s;
- `test_runtime_state_directory_write` 0.04 s;
- `test_agent_launch_state_directory` and `test_vm_setup_code_ref` 0.01 s each.

`make duplicates` (a record): `duplicates: 0 new, 42 known, 0 gone`.

**Disk.** The previous record line is the previous acceptance, F0047-A0002:
- `/srv/factory/vm` still holds 1.2 GB used;
- `/srv/factory/vm/state` and `/tmp` still hold 0.0 GB.

But the shared file system's free space fell from 35.2 GB to 21.4 GB, by **13.8 GB** in three stories. F0047-A0002 had already seen 6.7 GB go the same way. The three stories' changes (one `if` in a script, one `case` arm, a refactor, tests) do not explain any of it. The likely places are outside the folders the record measures:
- the Kumpel trial's second instance `demo`, with its stage image, its dataset and the containers' layers;
- the stage images rebuilt after each merge.

`podman system df` and `zfs list` on the host would show which. At this rate the next acceptance finds under 10 GB, so look before the free space reaches the factory's floor. The night of 2026-11-01 shows `podman image prune` freeing about 40 GB.

## 8 Cost

The fourteen stories: 196 runs, 439.1 min, 1657 turns, $64.24.

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
| S0013 | 10 | 15.6 | $2.14 |
| S0014 | 11 | 16.7 | $2.31 |
| S0015 | 8 | 12.6 | $1.59 |

**S0004 still stands out**, with 18 % of the runs and 22 % of the cost. As F0047-A0001 told from its journal, each review round found a new fault class at the token endpoint's boundary, and the story passed its round cap twice.

The three new stories took 29 runs, 44.9 min and $6.04, none of them out of line:
- **S0013** took one rework round: the reviewer added criterion 5, the `OSError` as cause, which intake and the tester had both named as untested.
- **S0014** also took one: two test functions became rows of one test.
- **S0015** took none.

**Human interventions:** 26 questions answered (24 `question`, 2 `round_cap`), 9.1 h waited. The three new stories added 3 questions and about 0.1 h:
- S0014 one, at intake: four gaps between the Interface and the criteria;
- S0015 two: intake's two gaps, and the tester's leave for one row of `tests/test_vm_setup_text.py`;
- S0013 none.

S0004 still needed the human most, 6 times:
- two test-design answers (entries 9 and 14);
- two round-cap restarts (36 and 52);
- one leave for `http.client` (57).

## Proposed stories

None. Each item of 4 is small, older than this feature, or already decided. The example under 5 is a one-line documentation repair, better made on `main` than by a pipeline run (as with S0011). It is listed under 6 with the disk.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 0 stories proposed

   1. Scope: every Scope item has its merged story. Since F0047-A0002, S0013, S0014 and S0015 built decision 22 as written:
      - one `agent_launch.make_state_directory` for both runtimes, plus S0004's two test notes;
      - `vm/setup.sh`'s step `datasets` takes the first `@base`;
      - `--code-ref` replaces `--ref`, which is refused with the hint, closing decision 16's open point.

      Nothing is out of scope. S0013 changes no behaviour a job sees, so `v1.2-job-1` needs no move.
   2. Feature smoke test: green. It ran a temporary 188-line script against the real entry points:
      - the real `vm/job-start.sh` through the suite's stand-ins;
      - the refresher;
      - `boundaries_from_environment` and every preflight item through a stand-in `podman` (`metadata-block` and `agent-run-probe` pass);
      - copy snapshots and the helper's real `git credential fill` (project host only);
      - one `build_tick().run()`, which ended `idle` with no stop;
      - the idle `exit`;
      - a `0500` runs folder, which fails the probe with `cannot write the state directory`;
      - `setup.sh --ref v9` (exit 2 with the hint);
      - the first base on a new machine, and none on a second run.

      Real engine, opencode, secret mount and `nft` stay for the trial at work.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: `ClaudeCodeRuntime._state_error` now has one caller. The uncovered `opencode_runtime.py` lines 228, 230, 479 and 633 date from F0020. `refresh_token.py:136` is the `__main__` line. A0001's carried notes are unchanged. A0002's two code points are closed by S0013. `make duplicates`: 0 new, 42 known, 0 gone. No story.
   5. Docs: README, the operator guide, decisions and the project guide agree on `--code-ref`, the first base and `make_state_directory`. One imprecise example: `docs/operator-guide.md:1044` pairs the copy adapter's `reset failed: no base at <path>` with ZFS advice and never quotes the ZFS rollback message. It is a one-line repair, listed under 6, not a story.
   6. Decisions: feature decisions 1 to 22 hold. S0013 to S0015's answers and defaults are listed. Earlier tests changed: `test_oauth_token.py` (one row), `test_hosting_search.py` (two names), `test_vm_setup.py` (two words) and `test_vm_setup_text.py` (one row), each under a named leave; none without one. Open for the human: the line-1044 repair, the unmeasured Cloud Run secret mount and `nft` load, and the disk.
   7. Slow checks: nothing beyond `make check`, which was green (`test: green (167.6 s)`, 99.58 %, 7971 cases). The slowest are earlier 10.0 s `ROOMY_LIMIT` tests; the new modules take 2.72 s. Disk: the factory's folders did not grow (1.2 GB used), but free space fell from 35.2 to 21.4 GB (13.8 GB, after 6.7 GB at A0002). The feature does not explain this; the likely causes are the `demo` instance's images and dataset, or rebuilt stage images. Worth a `podman system df` and `zfs list` on the host.
   8. Cost: $64.24, 196 runs, 439.1 min. S0004 still stands out ($14.39, 36 runs, two round-cap restarts). S0013 to S0015 cost $6.04 in 29 runs, with one rework round each for S0013 and S0014. 26 questions answered (24 `question`, 2 `round_cap`), 9.1 h waited; the new stories added 3 questions. S0004 needed the human most (6).

   Not done: `/tmp/acc3/smoke.py` (the smoke script only, made-up values, no secrets) is still there, because the `rm` was refused.
3. factory: done (pull request merged); cost: 1 runs, 18.5 min, 58 turns, 156317 tokens in (5660061 more from cache), 39284 out, $3.17
