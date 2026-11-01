---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 496
comments_read: [6559768618, 6559846438]
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
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-01T15:10:58.559853Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-01T15:11:17.804302Z'
  stage: intake
  run: 329979172dd54fbb8c2ace541d2fefdc
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-01T15:11:39.337756Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-01T15:16:05.489887Z'
  stage: tests
  run: 31ba077969eb497f9454ac552c2042d4
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-01T15:16:48.840253Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-01T15:17:06.541693Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-01T15:23:05.302205Z'
  stage: tests
  run: bcbfc47ddbec4086bef1506066aaa998
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-01T15:23:26.098769Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-01T15:29:38.930271Z'
  stage: doing
  run: ca6675c767af41a5a7c177b4dae9658a
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-01T15:29:59.446746Z'
  stage: review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-01T15:30:40.677581Z'
  stage: review
  run: cd7544c7357145b6b8c11be7804da993
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-01T15:31:01.819619Z'
  stage: docs
- number: 17
  speaker: documenter
  kind: result
  at: '2026-11-01T15:31:29.702562Z'
  stage: docs
  run: 79c58d328f134c8abf4988d49e80123d
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
3. `setup.sh ... --ref v9` and `setup.sh ... --ref` (no value, last on the line), rows of one test: each prints `setup.sh: --ref is now --code-ref` on standard error, followed by the usage (a line starting `usage: setup.sh`), exits 2, and calls no stand-in. The `--ref` case is handled before `need_value`.
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
5. factory: started intake as vm.
6. intake: accepted
   - Interface: `vm/setup.sh` names the option `--code-ref` (default `main`), the unchanged variable, the refusal of `--ref` through `fault` with exit 2 before any step, and the test files with the leave over `tests/test_vm_setup.py` (lines 16 and 80). All of it is concrete.
   - Criteria: each is testable by one test. 1 has two rows (with and without `--code-url`). 2 is the default. 3 now has two rows, `--ref v9` and a bare `--ref`, each with the hint, the usage line and exit 2, and no stand-in called. 4 covers `--help` and the usage text. 5 and 6 are the closing ones. I carried the human's answer (journal entry 4, both points) into criterion 3 and changed nothing else.
   - Smoke test: `sh vm/setup.sh --ref v9; echo "exit $?"` is runnable. It runs no pytest, so there is no `-q` problem. Its Expect line is checkable on the first and last lines.
   - Architecture: a shell script under `vm/`, a path the coder may write. No layer is touched.
   - Scope: within decisions 16 and 22 of F0047 and not in its Out of scope.
7. factory: started tests as vm.
8. tester: I wrote the tests for every criterion. Before I hand them to the coder, I need your answer on two points.

   1. An earlier test outside the leave will turn red. In `tests/test_vm_setup_text.py:378`, `test_the_options_land_in_their_named_variables` has the row `("ref", "ref")`. It checks that some line of the form `--ref) ... ref=` exists. Once the arm is `--code-ref)` and `--ref)` only calls `fault`, that row fails. The coder may not edit tests, and your leave covers only `tests/test_vm_setup.py`. The options I see:
      (a) Extend the leave so the row becomes `("code-ref", "ref")`. The test keeps its name and still checks the same thing, that each option lands in its variable. **This is the one I would choose.**
      (b) Drop the row, since `tests/test_vm_setup_code_ref.py` already checks that the clone's `--branch` variable is the one the `--code-ref` arm sets.
      (c) Leave it alone. The coder would then have to keep a `--ref)` arm that assigns `ref=`, which goes against the story.

   2. How I read criterion 1. The clone only runs when `/home/factory/.secrets/hosting-token` exists, and that is a fixed path outside `tmp_path`. So no test can run `setup.sh --code-ref v9` far enough to see `--branch v9`. I test it on the script's text instead, the way S0005's `--code-url` tests do. Each of the two clones (the askpass one without `--code-url`, and the `env -u GIT_ASKPASS` one with a different `--code-url`) must use `--branch "$<variable>"`, where the variable is the one the `--code-ref)` arm sets. Criterion 2 is read the same way: that variable gets `=main` exactly once, before the option parsing. Please confirm this reading, or tell me another one.

   Mapping:
   - criterion 1: tests/test_vm_setup_code_ref.py::test_the_clone_of_the_code_takes_its_branch_from_the_code_ref (rows without-code-url, different-code-url)
   - criterion 2: tests/test_vm_setup_code_ref.py::test_without_the_code_ref_the_clone_uses_main
   - criterion 3: tests/test_vm_setup_code_ref.py::test_the_old_ref_option_is_refused_with_a_hint (rows with-value, without-value). It checks: the first stderr line is the hint, the second starts with `usage: setup.sh`, exit status 2, and nothing new appears under `tmp_path`, which means no recording stand-in was called.
   - criterion 4: tests/test_vm_setup_code_ref.py::test_the_usage_text_names_the_code_ref_and_not_the_ref (rows help, fault)

   Files:
   - Created `tests/test_vm_setup_code_ref.py`.
   - Changed `tests/test_vm_setup.py` under your leave: lines 16 (`OPTIONS`) and 80 (the every-option row) now use `--code-ref` instead of `--ref`. Test names and what they check are unchanged.

   `make test`: the new tests fail for the right reasons. The usage text lacks `--code-ref`, a bare `--ref` gets "needs a value", and `--ref v9` runs on to "run as root". Every test module imports; there is no collection error. `make lint` is green.
9. 2026-11-01 human: Answers:

   1. (a): the leave extends to that one row of `tests/test_vm_setup_text.py::test_the_options_land_in_their_named_variables`, which becomes `("code-ref", "ref")`; the test keeps its name and checks the same thing. Nothing else in that file changes.
   2. Confirmed: criteria 1 and 2 are tested from the script's text, as S0005's `--code-url` tests do (the clone runs only after the secrets wait, which a test cannot reach).
10. factory: started tests as vm.
11. tester: I carried out the human's answer in entry 9. The tests from entry 8 are on the branch already (commit 87a7694f4). This run made one change on top of them.

    - **Point 1:** In `tests/test_vm_setup_text.py:378`, the row of `test_the_options_land_in_their_named_variables` changed from `("ref", "ref")` to `("code-ref", "ref")`. The test keeps its name and still checks the same thing, and nothing else in the file changed. The human extended the leave to cover exactly this row in entry 9.
    - **Point 2:** The human confirmed my reading. Criteria 1 and 2 are tested from the script's text, as S0005's `--code-url` tests are, so the tests stay as they are.

    Mapping:
    - criterion 1: tests/test_vm_setup_code_ref.py::test_the_clone_of_the_code_takes_its_branch_from_the_code_ref (rows without-code-url, different-code-url)
    - criterion 2: tests/test_vm_setup_code_ref.py::test_without_the_code_ref_the_clone_uses_main
    - criterion 3: tests/test_vm_setup_code_ref.py::test_the_old_ref_option_is_refused_with_a_hint (rows with-value, without-value)
    - criterion 4: tests/test_vm_setup_code_ref.py::test_the_usage_text_names_the_code_ref_and_not_the_ref (rows help, fault)

    Files:
    - Created `tests/test_vm_setup_code_ref.py` (in the previous run).
    - Changed `tests/test_vm_setup.py` (lines 16 and 80) under the leave in the Interface.
    - Changed `tests/test_vm_setup_text.py:378` under the leave the human gave in entry 9.

    Modules the test run could not import: none. There are no collection errors. The new tests and the changed row fail for the right reasons:
    - A bare `--ref` gets "needs a value" instead of the hint.
    - The usage text does not name `--code-ref`.
    - The script has no `--code-ref)` arm that sets `ref=`.

    `make lint` is green.

    `lint`: lint: green (0.2 s)
    `test`: FAILED tests/test_vm_setup_text.py::test_the_options_land_in_their_named_variables[code-ref-ref] - assert None
12. factory: started doing as vm.
13. coder: I renamed `vm/setup.sh`'s option `--ref` to `--code-ref`, which is the only file I changed. `make check` is green: the new tests in `tests/test_vm_setup_code_ref.py` pass, and so do the earlier rows changed under the leave in `tests/test_vm_setup.py` and `tests/test_vm_setup_text.py`.

    - The usage line and the option table now name `--code-ref <git ref>`, with the column alignment kept.
    - In the option parsing, a `--code-ref)` arm sets the same variable `ref` (default `main`, still set before the parsing). Below it, a `--ref)` arm calls `fault "--ref is now --code-ref"`. `fault` prints the hint and then the usage on standard error and exits 2. This happens before any step runs and before `need_value`, so a bare `--ref` at the end of the line gets the hint too.

    Main choice: the old name has its own arm in the `case` and calls `fault` directly. I rejected catching it in the `*)` arm, because then `--ref` would be handled by the code meant for unknown words, and the reader would not see it was a rename. I kept the variable name `ref` instead of renaming it to `code_ref`, because the Interface says the variable stays the same and `tests/test_vm_setup_text.py` checks that the option lands in `ref`.

    Refactor: I read the diff and found nothing to change.

    Noticed but not touched (the documenter's to do): `docs/operator-guide.md` still names `--ref` at lines 521, 540, 564, 579, 712, 716 and 736. `README.md` does not name it. The mentions in `docs/runs/` belong to the human and are left alone.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
14. factory: started review as vm.
15. reviewer: no findings

    I reviewed `git diff main...HEAD -- . ':!factory'`, which changes `vm/setup.sh`, `tests/test_vm_setup_code_ref.py`, `tests/test_vm_setup.py` and `tests/test_vm_setup_text.py`, together with the work item.

    - Acceptance criteria:
      - Criterion 1: `test_the_clone_of_the_code_takes_its_branch_from_the_code_ref` has two rows, without-code-url and different-code-url. Each row checks that its one clone line (`vm/setup.sh:373` and `:377`) takes `--branch "$ref"`, and that `ref` is the variable the `--code-ref)` arm sets. The test reads the script's text, as the human confirmed in entry 9.
      - Criterion 2: `test_without_the_code_ref_the_clone_uses_main` checks that `ref=main` (`vm/setup.sh:59`) is assigned once, before the `case` that parses the options.
      - Criterion 3: `test_the_old_ref_option_is_refused_with_a_hint` has two rows, with-value and without-value. Each row checks that the first line on standard error is the hint and the second starts with `usage: setup.sh`, that the exit status is 2, and that no new path appears under `tmp_path`, so no stand-in ran. In the code, `--ref) fault "--ref is now --code-ref"` (`vm/setup.sh:76`) never calls `need_value`. `fault` (`:28`) prints `setup.sh: <message>` and then the usage, both on standard error, and exits 2. A bare `--ref` therefore gets the hint too.
      - Criterion 4: `test_the_usage_text_names_the_code_ref_and_not_the_ref` has two rows, help and fault. The regex in `OLD_OPTION` does not match inside `--repository-url`.
      - Every Interface rule has its refused side tested: `--ref` with a value and without one. The Interface states no numeric limit. `--code-ref` without a value is still covered by the earlier `OPTIONS` table in `tests/test_vm_setup.py`, which now names `--code-ref`.
      - The factory's `make check` after the coder was green (journal entry 13).
    - Architecture: only a shell script under `vm/` changed. No layer is touched.
    - Security: no new markers and no secrets. The script stops in `fault` before any step runs.
    - Quality:
      - The new `case` arm is minimal, and the usage-table columns stay aligned.
      - The new test module uses `vm_support` (`run_setup`, `entries`, `step_texts`, `REQUIRED`, `SYSTEM_PATH`) and the shared `code` fixture.
      - Its `sh` stand-ins are written by hand. Other vm setup tests (`tests/test_vm_setup.py`, `tests/test_vm_setup_code_url.py`) do the same, so this is not a copy of a shared helper. `write_executable` in `tests/git_support.py` writes Python stand-ins, which is a different thing.
    - Work item hygiene:
      - The coder's entry 13 names the main choice: its own `--ref)` arm rather than the `*)` arm, and keeping the variable `ref`. It also says what was rejected.
      - The Description matches what was built.
      - The docs criterion (6) still names what the documenter must change. The coder listed the operator-guide lines that still say `--ref`.

    Earlier tests:
    - `tests/test_vm_setup.py`: the human's leave in the story's Interface. The change is lines 16 and 80, `--ref` to `--code-ref`; the test names and what they check are unchanged.
    - `tests/test_vm_setup_text.py`: the human's answer in journal entry 9. The change is the one row `("ref", "ref")` to `("code-ref", "ref")` of `test_the_options_land_in_their_named_variables`; nothing else in the file changed.
16. factory: started docs as vm.
17. documenter: I renamed `--ref` to `--code-ref` in the documents. The diff matches the Interface: the code refuses `--ref` with the hint and exit 2, as the docs now say. I ran no command, because I changed only documents; the factory's checks follow.

    Files changed:
    - `docs/operator-guide.md`: every `--ref` of the script is now `--code-ref`. That covers the checkout table row (line 384), *The code and the project apart* (521), the option table (540), step 12 of the steps (564), the paragraph on the installed files (579), the GCP steps (712, 716, 736) and *The rebuild after a merge* (890). The option-table row also has the one sentence the criterion asks for: the old name is refused with `setup.sh: --ref is now --code-ref` and the usage, exit 2, before any step runs.
    - `docs/decisions.md`, *The code and the project apart*: one line that the option is `--code-ref` (decision 16 of the feature), default `main`, and that `--ref` is refused with the hint and exit 2.

    Cross-read and found current:
    - `README.md`: it does not name `--ref`, so I left it as it is.
    - A search of `docs/` for `--ref` found no other mention outside `docs/runs/`. That folder is the human's, and I did not touch it.

    Stale text I saw and did not touch: none.

    `check`: check: green (not run again: passed on tree e10113d6e8d0 at 2026-11-01T15:26:42Z)
    `secrets`: secrets: green (2.1 s)
    `documents`: documents ok
