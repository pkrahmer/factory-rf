---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 520
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: smoke-test
  started_at: '2026-11-03T11:57:41.995932Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T11:51:33.142867Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T11:51:33.149591Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-03T11:51:57.767089Z'
  stage: intake
  run: 03af1de5920a4139b6625250bb8c471b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-03T11:52:03.161725Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-03T11:52:44.606976Z'
  stage: tests
  run: 9d7dcffed19a405fbd38c3adeeef2e6f
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-03T11:52:50.365926Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-03T11:56:34.259074Z'
  stage: doing
  run: ad1afa1d03ae4fa38e3deb0c6bd32d80
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-03T11:56:39.974451Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-03T11:57:10.081077Z'
  stage: review
  run: cd8804c537954c8886e76c87bec35380
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-03T11:57:15.814547Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-11-03T11:57:36.433301Z'
  stage: docs
  run: 87dd26c2e81644e492f5a1a9cb688cd5
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-03T11:57:41.995932Z'
  stage: smoke-test
---

# The job's start script leaves no temporary folder behind

<!-- written by the human on 2026-11-03 from what the acceptances F0048-A0002 and F0048-A0003 noticed (decision 26) -->

## Description

The step `runc` of `vm/job-start.sh` downloads `runc` into a folder from `mktemp -d` and removes the folder with `rm -rf` as its last line. When the download, the checksum or the install fails, the script stops before that line, and the folder stays. In a job it lies in the job's memory; on a machine and in `make check`, whose tests run the script on stand-ins that fail on purpose, every such run leaves a `/tmp/tmp.*` folder behind. The acceptances F0048-A0002 and F0048-A0003 both found folders of this kind.

This story makes the step remove its download folder on every way out of the step: after a success, a failed download, a checksum that does not match and a failed install. Nothing else in the script changes. With it, one grammar slip in the operator guide is fixed.

## Interface

- `vm/job-start.sh`, step `runc`: the download folder is removed whenever the step ends, by success or by a stop. The messages the step prints on a failure stay word for word.
- `docs/operator-guide.md`, *The probe of the agent run* (or wherever the sentence stands): "A state directory that cannot be written fail it with the runtime's own message" becomes "A state directory that cannot be written fails it with the runtime's own message".

Tests: new rows beside the existing tests of `vm/job-start.sh`, with its stand-ins; the folder `mktemp -d` would create is placed under the test's `tmp_path` (for example through `TMPDIR`), so that the test can see whether it is left behind.

## Acceptance criteria

1. After the step `runc` ends, no download folder remains under the `TMPDIR` the test gives the script. Rows: a success; a failed download; a checksum that does not match; a failed install. Each failure row also prints the step's message as today.
2. `make check` stays green, and leaves no `/tmp/tmp.*` folder from `vm/job-start.sh`'s tests.
3. docs: `docs/operator-guide.md`: the sentence of the Interface reads "fails it". `README.md`, the project guide and `docs/decisions.md`: none.

## Smoke test

```bash
grep -c 'cannot be written fail it' docs/operator-guide.md; grep -c 'cannot be written fails it' docs/operator-guide.md
```

Expect: `0`, then `1`.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names the one script and step (`vm/job-start.sh`, step `runc`, lines 104-110, where `mktemp -d` is followed by `rm -rf` as the last line) and the one guide sentence. No signatures are needed. The failure messages stay word for word (`runc: failed`, `runc: checksum does not match`).
   Criteria: criterion 1 has four rows (success, failed download, checksum mismatch, failed install), each checked by whether a folder remains under the test's `TMPDIR`, and each failure row also checks the printed message. The criteria cover every way the step can end. A failed `mktemp` leaves no folder, so it needs no row. Criterion 2 is a property of the whole `make check` run rather than one test function. It follows from the rows of criterion 1 and is checked by running `make check`, so I accept it. Criterion 3 is the docs criterion.
   Smoke test: one runnable `grep -c` command, with an `Expect:` line (`0`, then `1`) that the output can be checked against. It runs no pytest, so the `-q` rule does not apply.
   Architecture: the change stays inside `vm/job-start.sh`, which is the coder's write path, and the tests stay under `tests/` beside the existing `vm/job-start.sh` tests. No Python layer is touched.
   Scope: it matches S0020 in `feature.md` and decision 26. The grammar fix to the operator guide is named in the Description and in decision 26. It is not in the feature's Out of scope list. The story changes no test that another story wrote.
4. factory: started tests as vm.
5. tester: Wrote one parametrized test for the `runc` step's download folder. It sits beside the existing tests of `vm/job-start.sh` and uses their stand-ins (`run_job_start` from `tests/vm_support.py`). Each row gives the script a `TMPDIR` under `tmp_path`. It checks that curl's download target lay in a folder directly under that `TMPDIR`, that the `TMPDIR` is empty after the run, and either a clean exit or exit 1 with the step's message unchanged, with no `factory-run`.

   criterion 1: tests/test_vm_job_start.py::test_the_runc_download_folder_is_removed_however_the_step_ends (rows `success`, `download` (curl fails, `job-start: runc: failed`), `mismatch` (sha256sum fails, `job-start: runc: checksum does not match`), `install` (install of `<prefix>/usr/local/bin/runc` fails, `job-start: runc: failed`))
   criterion 2: no test function. It is a property of the whole `make check` run and follows from the criterion 1 rows, which now put the folder under `tmp_path`. The coder's `make check` covers it.
   criterion 3: docs criterion, no test.

   Files: I changed `tests/test_vm_job_start.py` (one test added; earlier tests untouched). No new support code was needed: `run_job_start` already passes `TMPDIR` through `inputs`, and `failing_install_target` already makes `install` fail.

   Run (`uv run pytest -q tests/test_vm_job_start.py`): the `success` row passes, because today's last line already removes the folder. The `download`, `mismatch` and `install` rows fail for the right reason: a `tmp.*` folder remains under the test's `TMPDIR`. Every module imported. `make lint` is green.

   Open: none.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: Built: `vm/job-start.sh`, step `runc`. Right after `mktemp -d` succeeds, the step sets `trap 'rm -rf "$download"' EXIT`. After its own `rm -rf "$download"` it clears that trap with `trap - EXIT`. Every stop in the step goes through `stop`/`failed`, which `exit`, so the trap removes the folder after a failed download, a checksum that does not match and a failed install. A success removes it as before. The messages are unchanged word for word, and nothing else in the script changed. Clearing the trap after the step keeps it from reaching any later step; the script set no other trap.

   Main choice: an EXIT trap scoped to the step. I rejected a `cleanup_and_fail` helper that removes the folder and then calls `stop`. It would mean rewriting all three `|| failed runc` / `|| stop 1 ...` endings, and any later way out of the step that skipped it would leave the folder again. The trap covers every exit, including one that `set -e` causes.

   Checks: `uv run pytest -q tests/test_vm_job_start.py`: all 46 pass, including the four rows of `test_the_runc_download_folder_is_removed_however_the_step_ends`. `make check`: check: green. I counted `/tmp/tmp.*` before and after `make check`: 0 and 0 (criterion 2).

   Refactor: I read the diff again (two added lines and one comment) and found nothing to change.

   Noticed but not touched: criterion 3, the guide's "fail it" → "fails it" in `docs/operator-guide.md`. Under `CLAUDE.md` *Docs* that file belongs to the documenter, so the docs stage makes that change. The journal did not change the meaning of the Description.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 42 known, 0 gone
8. factory: started review as vm.
9. reviewer: no findings

   Read: the work item, `git diff main...HEAD -- . ':!factory'` (`vm/job-start.sh` +3, `tests/test_vm_job_start.py` +40), and the existing runc tests and `run_job_start` in `tests/vm_support.py` that the new test relies on.

   1. Acceptance criteria: criterion 1 is tested by `tests/test_vm_job_start.py::test_the_runc_download_folder_is_removed_however_the_step_ends`, a parametrized test with four rows: `success`, `download`, `mismatch` and `install`. Each row sets `TMPDIR` to a folder under `tmp_path`. It checks that curl's target lay in a folder directly under that `TMPDIR` (so the test cannot pass by never downloading) and that the `TMPDIR` is empty afterwards. A failure row also checks exit 1, the step's message as a whole stderr line (`job-start: runc: failed` or `job-start: runc: checksum does not match`) and that no `factory-run` was called. The tester reported that the three failure rows failed before the change and the success row passed, which is what we'd expect. Criterion 2: the coder's `make check` was green (journal 7), and the coder counted `/tmp/tmp.*` before and after: 0 and 0. With the trap, even the earlier tests that hit a runc failure with the default `TMPDIR` (`test_runc_without_a_matching_checksum_stops_the_script`, row `mismatch`) leave no folder now. Criterion 3 is the docs criterion: the sentence still reads "fail it" at `docs/operator-guide.md:1377`, and the documenter fixes it from that criterion. The Interface sets no limit with two sides. Its one rule ("removed whenever the step ends, messages word for word") has every way out covered by a row.
   2. Architecture: no Python changed. The shell change stays inside `vm/job-start.sh`, and `vm/setup.sh:112` already uses the same `trap ... EXIT` pattern.
   3. Security: no secrets, and no command built from strings. The trap's `"$download"` is quoted inside a single-quoted trap text, so it is expanded only when the trap runs. No silencing markers were added.
   4. Quality: two lines and one comment. The comment says why the trap is there. `trap - EXIT` after the step's own `rm -rf` keeps the trap from reaching any later step, and the script sets no other trap. The test reuses `RUNC_URL`, `RUNC_VERSION`, `_downloaded`, `run_job_start` and `failing_install_target` and copies no helper.
   5. Work item hygiene: the coder's entry explains the EXIT trap and why the rejected `cleanup_and_fail` helper was dropped. The Description matches what was built, and the docs criterion still says what the documenter must change.

   Earlier tests:
   - `tests/test_vm_job_start.py`: none needed. The diff only adds one test and leaves every earlier test in the file unchanged.
10. factory: started docs as vm.
11. documenter: Changed `docs/operator-guide.md` only, so I did not run `make check`. The factory's checks run right after this stage.

    - Line 1377: "cannot be written fail it" is now "cannot be written fails it", as the docs criterion asks.
    - Line 1221 (the `runc` step in the list of the job's steps): I added one sentence, "The download folder is removed whenever the step ends, by success or by a stop." The diff makes this true: `vm/job-start.sh` now removes the folder through an EXIT trap.

    Smoke test command: the first `grep -c` printed 0 and the second printed 1, as expected.

    I read the diff (`vm/job-start.sh`, `tests/test_vm_job_start.py`) against the guide. The failure messages are unchanged, and the guide's `job-start: runc: checksum does not match`, status 1, still matches. `README.md`, `docs/project-guide/` and `docs/decisions.md` need no change; I cross-read the project guide and README for mentions of the `runc` step and found none.

    No findings for the coder. I saw nothing stale that is unrelated to this story.

    `check`: check: green (not run again: passed on tree 676ce2a5aa50 at 2026-11-03T11:54:59Z)
    `secrets`: secrets: green (1.3 s)
    `documents`: documents ok
12. factory: started smoke-test as vm.
