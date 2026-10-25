---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 433
comments_read: [6394400610]
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-25T06:31:33.339256Z'
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
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T06:27:33.487862Z'
  stage: intake
  run: fa0d8f8981e5443bb3252a73adf48d7f
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T06:27:53.690221Z'
  stage: tests
- number: 5
  speaker: tester
  kind: question
  at: '2026-10-25T06:28:54.214123Z'
  stage: tests
  run: e8eccf1d056a40708edc411da4f7c746
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-10-25T06:31:15.286602Z'
  stage: tests
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-25T06:31:33.339256Z'
  stage: tests
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
3. intake: accepted
   Interface: names `vm/setup.sh` and one concrete helper (`write_as_factory <mode> <target>` beside `as_factory`) with the exact `sh -c 'cat > "$2" && chmod "$1" "$2"'` command, its standard-input sources, and the test module and support file. It states no rule beyond what criteria 1 to 3 test.
   Criteria: each is testable by one test function or one parametrized test. 1 covers the absence of `/dev/stdin`/`install` with stdin. 2 has one row for each of the three writes (mode and target) plus the helper's `as_factory` line. 3 covers content, mode and rewrite on the helper's pass side, and 4 pins the existing test. The helper has no refusal path, so no failing side is needed. "Write only when the text differs, as today" is kept unchanged by the Interface's "nothing else changes". I did not add a criterion for it.
   Smoke test: `grep -c '/dev/stdin' vm/setup.sh; sh -n vm/setup.sh && echo syntax-ok` runs as written. The grep prints 0 (its non-zero status is ignored because of the `;`), then `syntax-ok`. The Expect line is checkable. It runs no pytest, so the `-q` rule does not apply.
   Architecture: `vm/*` is in the coder's write paths, which feature.md change 1 added. Tests go under `tests/` with `tests/vm_support.py`, and the docs criterion names the operator guide's setup-script chapter. No layer is touched.
   Scope: it is inside F0043 as decision 17 and the Stories list (S0005, before S0004). It changes nothing from the Out of scope list, and no earlier test changes.
4. factory: started tests as self.
5. tester: I stopped before writing any test. Criterion 4 conflicts with the Interface.

   What I found: `tests/test_vm_setup_text.py::test_the_files_under_the_instance_folder_are_written_as_factory` (rows `image-id`, `askpass`, `factory-env`) finds a step's write lines through `_writes`. A line counts as a write only if it redirects (`>` or `>>`) into the file or holds one of `WRITE_FORMS` (`install `, `cp `, `mv `, `tee `). It then requires at least one such line, and every one of them must run as factory. The Interface's write line is `write_as_factory 0644 "$base/image-id"`, and lines like it for `$askpass` and `$env_file`. Those lines hold no redirect into the target and none of those forms. So the existing test finds no write line, and the three rows fail.

   I checked this rather than reading it off the code. I rewrote the script's text in memory as the Interface describes: a helper `write_as_factory() { as_factory sh -c 'cat > "$2" && chmod "$1" "$2"' sh "$1" "$2"; }` and the three calls. I then ran the test's own `_written_as_factory` on it. It returned `False False False` (script in `$TMPDIR`, not kept).

   The question: how should criterion 4 be met?
   - (a) You allow a change to that earlier test. `_writes` would also count a line that calls a function whose body writes through `as_factory` (for example a function whose body holds `cat >`). Every row keeps its name and its check that the write runs as factory. Criterion 4 would then read "passes, with `_writes` also counting a call of the write helper". This is the option I would choose: it keeps the guard against a write as root and fits the new helper.
   - (b) The coder's call lines keep a word the old test knows. For example, a helper named so that `tee ` appears, or a comment-free `install`. That breaks criterion 1 or bends the code to fit a test, so I would not choose it.
   - (c) Drop criterion 4 and let the new criterion 2 carry the "written as factory" check for these three files. The old test's three rows would then still need to change or be removed, so this also needs your leave.

   Nothing else is open. Once this is answered, my plan is:
   - criterion 1: one test that the uncommented text holds no `/dev/stdin` and no line with both `install` and `stdin`.
   - criterion 2: one parametrized test with rows image-id/askpass/factory-env. Each row checks the step's call of the helper with its mode and target. The helper is found as the script's function whose body calls `as_factory` with `cat >`, and its line must run through `as_factory`.
   - criterion 3: rows one and two. The test runs the helper's function text with `as_factory() { "$@"; }` through `sh` in `tmp_path` and checks the content and the mode 0640.

   To find the helper's function text I would move `FUNCTION` from `tests/test_vm_setup_text.py` to `tests/vm_support.py`, under the standing leave.

   No files created.
6. 2026-10-25 human: (a). The leave: in `tests/test_vm_setup_text.py`, `_writes` also counts a line that calls the script's write helper (the function whose body writes with `cat >` through `as_factory`); `test_the_files_under_the_instance_folder_are_written_as_factory` keeps its name, its four rows and its check that every write line runs as `factory`. Read criterion 4 as "passes, with `_writes` also counting a call of the write helper", and name the change in your entry. Moving `FUNCTION` to `tests/vm_support.py` is under the standing leave, as you say. Your plan for criteria 1 to 3 is right.
7. factory: started tests as self.
