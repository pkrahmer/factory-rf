---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 496
comments_read: [6559768618]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-01T15:09:05.936881Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-01T15:09:05.942844Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-01T15:09:24.907325Z'
  stage: intake
  run: 94b28a8f9fba4ff9bca35bef2e574eab
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-01T15:10:40.741280Z'
  stage: intake
---

# Setup names the code's ref --code-ref

## Description

F0047's decision 16 gave the repository split the names `--code-url` and `--code-ref`. S0005 built `--code-url`, but `vm/setup.sh` still takes the code's ref as `--ref`, while the job's start script calls it `FACTORY_CODE_REF`. One idea has two names. This story renames the option to `--code-ref` (the human, 2026-11-01). The old name is refused with a hint, so that an old command line says at once what changed: `setup.sh: --ref is now --code-ref`, exit status 2, before anything runs. Unchanged: the default (`main`), what the ref does (the clone of the factory's code at that ref, with `--code-url` or without it), every other option and step.

## Interface

`vm/setup.sh` (shell): the option `--code-ref <git ref>` (default `main`) takes the place of `--ref` in the parsing, the usage text and the option table of the operator guide; the variable it sets is the same. `--ref` with or without a value prints `setup.sh: --ref is now --code-ref` and the usage on standard error and exits 2, before any step runs (through the script's `fault`).

Tests (the tester writes them): `tests/test_vm_setup_code_ref.py`. The leave over earlier tests (the human, 2026-11-01): `tests/test_vm_setup.py` uses `--code-ref` where it used `--ref` (lines 16 and 80 today), every test keeping its name and what it checks; no other earlier test changes.

## Acceptance criteria

1. `setup.sh --code-ref v9` clones the factory's code with `--branch v9`, rows of one test: without `--code-url` (with the askpass, as today) and with a different `--code-url` (without a credential, as S0005 built).
2. Without `--code-ref` the clone uses `--branch main`.
3. `setup.sh ... --ref v9` prints `setup.sh: --ref is now --code-ref` on standard error, exits 2, and calls no stand-in.
4. `setup.sh --help` and the usage text name `--code-ref` and not `--ref`.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`: every `--ref` of the script becomes `--code-ref` (the option table, the steps, *The rebuild after a merge*, *The code and the project apart*, the GCP steps), with one sentence that the old name is refused. `docs/decisions.md`, *The code and the project apart*: one line that the option is `--code-ref`, from the feature's decision 16. `README.md`: only if it names `--ref`.

## Smoke test

```bash
sh vm/setup.sh --ref v9; echo "exit $?"
```
Expect: the first line is `setup.sh: --ref is now --code-ref`, and the last line is `exit 2`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-11-01 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. I read the story, feature.md (decision 16 and 22) and vm/setup.sh (usage line 11, `fault` at line 28, `--ref` parsing at line 75). Two findings, so the story cannot move on yet:

   1. The Interface says `--ref` "with or without a value" is refused with the hint, usage and exit 2. Criterion 3 only covers `--ref v9`. Today the parser calls `need_value` before it handles the option, so a bare `--ref` at the end of the line would probably report "needs a value" instead of the hint. Nothing tests that side. Proposed: add a criterion, "`setup.sh ... --ref` with no value prints `setup.sh: --ref is now --code-ref`, exits 2 and calls no stand-in". Better still, make it a second row of criterion 3's test.

   2. The Interface says the hint is followed by the usage on standard error, but no criterion checks the usage. Criterion 4 covers `--help` and the usage text naming `--code-ref` and not `--ref`. It doesn't say the refusal prints the usage. Proposed: criterion 3 also expects the usage text on standard error after the hint line, for example a line starting `usage: setup.sh`.

   The other checks are fine, apart from these two gaps:
   - Interface: it names `vm/setup.sh`, the `--code-ref` option and its default, the use of `fault`, and the test file and the leave for `tests/test_vm_setup.py`.
   - Smoke test: the command is runnable. It runs no pytest, so there is no `-q` problem. Its Expect line is checkable.
   - Architecture: it is a shell script under `vm/`, a path the coder may write. No layer is touched.
   - Scope: it is within decision 16 and 22, and not in "Out of scope".
4. 2026-11-01 human: Answers to question 3: both as you propose.

   1. Criterion 3 gets a second row: `setup.sh ... --ref` with no value prints `setup.sh: --ref is now --code-ref`, exits 2 and calls no stand-in. The `--ref` case is handled before `need_value`, so a bare `--ref` gets the hint too.
   2. Criterion 3 also expects the usage on standard error after the hint line (a line starting `usage: setup.sh`), in both rows.
