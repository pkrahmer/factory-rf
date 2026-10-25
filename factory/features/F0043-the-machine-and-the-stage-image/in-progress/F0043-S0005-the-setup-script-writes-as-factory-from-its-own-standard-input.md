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
  instance: self
  stage: intake
  started_at: '2026-10-25T06:27:15.696525Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T06:27:15.690887Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T06:27:15.696525Z'
  stage: intake
---

# The setup script writes as factory from its own standard input

## Description

`vm/setup.sh` (S0003) writes three files under `/srv/factory/<instance>` as `factory` through `as_factory`: `image-id`, the askpass script and `factory.env`. Each write is `as_factory install -m <mode> /dev/stdin <target>`, with the text on standard input. `install` opens `/dev/stdin` again by name, and a process that `runuser` started as `factory` may not open a pipe or file descriptor that root created: on the local VM on 2026-10-25 (Ubuntu 24.04, the script's first real run, as root through `sudo`) the `checkout` step's write of the askpass script ended with `install: cannot open '/dev/stdin' for reading: Permission denied`, and `set -e` ended the run with exit status 1 before the clone. So no first run can get past the `checkout` step on any machine. A write that reads the inherited standard input itself works: on the same VM, `runuser -u factory -- sh -c 'cat > "$1"' sh <target>` wrote the text from a pipe and from a file. This story makes each of the three writes read its text that way, as `factory`, and set the file's mode after it; nothing else in the script changes. What stays: every write under `$base` runs as `factory` (the human's answers in S0003's journal, entries 26 and 37); the files' modes are the same (`image-id` and `factory.env` 0644, the askpass script 0755); a write happens only when the text differs, as today. Decision 17 of `feature.md`.

## Interface

`vm/setup.sh` (the coder's, `vm/*`):

- The three writes of `image-id`, the askpass script and `factory.env` each become one call of a helper the script defines once beside `as_factory`, for example `write_as_factory <mode> <target>`, that runs `as_factory sh -c 'cat > "$2" && chmod "$1" "$2"' sh <mode> <target>` with the text on its own standard input (the pipe from the staging file, or `/proc/sys/kernel/random/uuid` for `image-id`).
- The script's text holds no `/dev/stdin` and no `install` whose source is standard input.
- Nothing else in the script changes: the steps, their order, their lines, the guards and the refusals stay as S0003 built them.

Tests (the tester writes them): new rows in a new test module, for example `tests/test_vm_setup_writes.py`, reading the script's text with `tests/vm_support.py`, and one test that runs the helper as the test's own user (no `runuser`: the test defines `as_factory` as a plain pass-through by sourcing only the helper's text, or by running the `sh -c` command the helper runs) on a file in `tmp_path`. No earlier test changes; `tests/test_vm_setup_text.py::test_the_files_under_the_instance_folder_are_written_as_factory` stays as it is and green.

## Acceptance criteria

1. The script's text (comment lines dropped) holds no `/dev/stdin`, and no line holds `install` together with `stdin` (one test).
2. The three writes (rows of one parametrized test, one row each for `image-id`, the askpass script and `factory.env`): the step's write line calls the helper with the mode `0644`, `0755` and `0644` respectively and the step's target (`$base/image-id`, `$askpass`, `$env_file`), and the helper's own line runs through `as_factory`.
3. The helper, run on a target in `tmp_path` with the text `one` on standard input and the mode `0640`: the file holds exactly `one` followed by a newline, and its mode is `0640`; run again with `two` on standard input, the file holds `two` and keeps the mode `0640` (rows of one parametrized test).
4. `tests/test_vm_setup_text.py::test_the_files_under_the_instance_folder_are_written_as_factory` passes unchanged.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, the chapter on the setup script: one sentence that the script writes the files under `/srv/factory/<instance>` as `factory` with `cat` from its own standard input, because a process started by `runuser` may not reopen root's `/dev/stdin`. `docs/decisions.md`: none. `README.md`: none.

## Smoke test

```bash
grep -c '/dev/stdin' vm/setup.sh; sh -n vm/setup.sh && echo syntax-ok
```
Expect: two lines, `0` and `syntax-ok`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
