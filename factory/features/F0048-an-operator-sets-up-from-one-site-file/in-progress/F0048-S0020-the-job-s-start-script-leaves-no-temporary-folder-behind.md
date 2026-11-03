---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 520
comments_read: []
handed_over: null
claim: null
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
