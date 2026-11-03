---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-03T11:51:33.149591Z'
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
