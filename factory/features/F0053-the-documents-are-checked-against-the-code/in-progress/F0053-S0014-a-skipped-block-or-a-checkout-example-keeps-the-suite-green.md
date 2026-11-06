---
stage: docs
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 601
comments_read: [6693147830]
handed_over: null
claim:
  instance: vm
  stage: docs
  started_at: '2026-11-06T19:28:42.488097Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T14:05:00.013062Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T14:05:00.020466Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T14:08:24.925944Z'
  stage: intake
  run: 83e691a19c244cfca39317bae9eb95ad
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T14:18:26.002800Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T14:18:28.779159Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T14:18:50.392648Z'
  stage: intake
  run: eac0b28babd0497982510fce80ee4043
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T14:18:56.695064Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-06T14:21:41.849344Z'
  stage: tests
  run: ceba5deb81ed4130bff6d5bebd885b6b
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-06T14:21:49.154527Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-06T19:19:47.391824Z'
  stage: doing
  run: da126ef6792a435291a998ef48ae5922
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-06T19:19:53.170758Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-06T19:21:11.081302Z'
  stage: review
  run: b3d28e9808ea4776a6c7e12d408afafe
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-06T19:21:16.486989Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-06T19:21:38.634966Z'
  stage: doing
  run: 79017b9986894ba3ba59a2e705fd43c4
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-06T19:21:44.188080Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-06T19:23:29.063373Z'
  stage: tests
  run: 5ec1b91b474343388daa6a4f3f951cfa
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-06T19:23:34.465960Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-06T19:27:44.425524Z'
  stage: doing
  run: 98805114f2ce48dca3fc8ff378eb5d12
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-06T19:27:49.933748Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-11-06T19:28:37.229022Z'
  stage: review
  run: c597677ab842491a8766d4a6a73d8835
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-06T19:28:42.488097Z'
  stage: docs
---

# A skipped block or a checkout example keeps the suite green
## Description

The suite runs the examples of every document on a copy of the documents (the `documents` fixture of `tests/conftest.py`), so that a wrong example fails `make check` in any file. Two right documents fail it today as well. First, the copy holds only `README.md` and `docs/`, while the `checkout` fixture that `make documents` uses holds every tracked file. An example that reads a file of the repository, such as `$ ls operator/vm/setup.sh`, passes `make documents` but prints `ls: cannot access ...` in the suite. Second, `test_the_operator_guide_folder_is_checked_per_file` compares the whole output except the `does not exist` lines and the report heading. A block marked `vm`, `github`, `model` or `suite`, which `make documents` lists as `not run (<reason>)` and never blocks on, adds a line to that output. One `console vm` block anywhere in the documents fails five of the test's six rows. Feature decision 3 asks for exactly such blocks, and the rewrite (F0054) marks every command it cannot run, so its first story would turn `make check` red. This story makes the copy hold the repository's tracked files and makes that test leave out the `not run` lines too. A wrong runnable example still fails the suite in any document. The check itself, its output and `docs/checked-documents.txt` stay as they are.

## Interface

- `tests/conftest.py`, fixture `documents(tmp_path) -> Path`: a git repository under `tmp_path` with one commit. It holds every file that `git ls-files` lists in the repository, copied from the working tree, instead of only `README.md` and `docs/`. Files that git does not track (`.venv/`, `.reports/`, `mutants/`) are not in it. The fixture keeps its name and its docstring says what it holds.
- `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`: before it compares, the test leaves out every line that ends in `: not run (<reason>)`, as it already leaves out the `does not exist` lines and the report heading. Every row keeps its id and its expected output.
- Both are earlier tests. Feature decision 7 gives the human's leave for them: the fixture, that one test, and any other earlier test, whichever story wrote it, whose only failure is the effect this Interface describes. Every changed test keeps its name and what it checks, and the entry names each one.
- The suite stays fast: the full copy is built and committed once per test session (a session-scoped fixture), and `documents` gives each test its own cheap copy of it (`git clone --local` or a copy of that one repository), so no test copies the whole working tree again. `make test` must not grow by more than about ten seconds; the entry gives the time before and after.
- New rows go in `tests/entry/test_check_documents_operator_guide.py` (or a new module `tests/entry/test_check_documents_suite_copy.py`), and each new row changes the copy through `documents` and commits the change.
- No module under `src/factory/` changes.

## Acceptance criteria

1. In the `documents` copy, after a block is appended to `docs/project-guide/machine.md` and committed, `factory.entry.check_documents.main(["--root", <copy>])` with the `no-index` change of the earlier test prints, once the `does not exist` lines, the report heading and the `not run` lines are left out, exactly `docs/operator-guide/README.md: missing\n`, with exit status 1. This holds for the block marked `console vm`, `console github`, `console model` and for a block that runs `make test`. A `console` block with the command `$ echo one` and the expected line `two` adds the line `docs/project-guide/machine.md:<line>: the example printed one` (rows of one test).
2. In the `documents` copy, a committed `console` block in `docs/project-guide/machine.md` with `$ ls operator/vm/setup.sh` and the expected line `operator/vm/setup.sh` gives no line about `machine.md` in the output of `main`. The same block with `operator/vm/nothing.sh` gives the line `docs/project-guide/machine.md:<line>: the example printed ls: cannot access 'operator/vm/nothing.sh': No such file or directory` (rows of one test).
3. The `documents` copy holds `pyproject.toml` and `src/factory/shared/domain/documents.py`, holds no `.venv`, and `git status --porcelain` in it prints nothing.
4. Every row of `test_the_operator_guide_folder_is_checked_per_file` passes with today's documents, as before.
5. Two copies taken from the one session repository are separate: a file committed or changed in one test's `documents` copy is absent from the copy another test gets, and a fresh copy's `git status --porcelain` is empty (tested at fixture level, two copies from the one session repository).
6. `make check` stays green.
7. docs: `docs/project-guide/style.md`, *Runnable examples*: the reader learns that the suite runs the examples on a copy of the repository's tracked files. So an example that passes `make documents` also passes the suite, and a block that is not run never fails either of them.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git clone -q . "$d/c" && cd "$d/c" && git config user.name smoke && git config user.email smoke@example.invalid && git config gc.auto 0
printf '\n```console vm\n$ systemctl is-active factory-vm\nactive\n```\n\n```console\n$ ls operator/vm/setup.sh\noperator/vm/setup.sh\n```\n' >> docs/project-guide/machine.md
git commit -qam smoke
PATH="$OLDPWD/.venv/bin:$PATH" python -m pytest -p no:cacheprovider -o addopts= tests/entry/test_check_documents_operator_guide.py 2>&1 | tail -1
```
Expect: a last line `<n> passed in <seconds>s`, with no `failed` in it.

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: 1. Interface says `documents` gives each test its own copy of the session-built repository. No criterion tests this. Two coders could share one repository between tests and still pass every row. Please add a criterion, for example: "a file committed or changed in one test's `documents` copy is absent from the copy another test gets, and the copy `git status --porcelain` stays empty." I would choose that wording, as a two-test or fixture-level check.

   Everything else checked out, and the format check passed:
   - Interface: concrete fixture and test paths.
   - Criteria: otherwise testable, with the failing side covered (the `echo one`/`two` row, the `nothing.sh` row).
   - Smoke test: runnable, `-o addopts=` is passed so the summary line exists, and the Expect line is checkable.
   - Docs criterion: names what the reader must know and dictates no sentences.
   - Architecture: tests only, no change under `src/factory/`.
   - Scope: within the feature, with decision 7's leave.

   Once question 1 is answered I would accept on the `tests` route.
4. 2026-11-06 human: Yes, with your wording: a file committed or changed in one test's `documents` copy is absent from the copy another test gets, and a fresh copy's `git status --porcelain` is empty. One criterion, tested at fixture level (two copies from the one session repository).
5. factory: started intake as vm.
6. intake: accepted. Carried in from journal entry 4 (the human's answer to my question 1): I added one criterion, now 5, before the two closing ones (so `make check` is now 6 and `docs:` 7). It says a file committed or changed in one test's `documents` copy is absent from another copy, and a fresh copy's `git status --porcelain` is empty, tested at fixture level with two copies from the one session repository. Nothing else in the story changed.
   - Interface: concrete. It names the `documents` fixture in `tests/conftest.py` and the test in `tests/entry/test_check_documents_operator_guide.py`, with the session-scoped repository plus a per-test copy, the tracked-files rule and the `not run` filter.
   - Criteria: each is testable by one test function. Criterion 1 has the `not run` filter and the `echo one`/`two` failing side. Criterion 2 has both sides (`setup.sh` and `nothing.sh`). Criterion 3 covers the copy's contents and the clean status. Criterion 5 covers the per-test isolation. Criterion 4 is the existing rows.
   - Smoke test: runnable. It passes `-o addopts=` so the summary line exists, and the Expect line (`<n> passed`, no `failed`) is checkable.
   - Docs criterion: names what the reader must know (the suite runs examples on a copy of the tracked files, so a passing example passes both, and a skipped block never fails either) and dictates no sentences.
   - Architecture: tests only. No module under `src/factory/` changes.
   - Scope: within feature F0053, not in its out-of-scope list. Decision 7 gives the human's leave for the fixture and the test.
   - Route: tests, because the Interface changes only test files and the docs criterion needs a documenter run later.
7. factory: started tests as vm.
8. tester: Wrote the tests for the criteria. The Interface puts this story's whole change in test files: the fixture, the filter and the new rows. So the new tests pass already, and they are not red. The coder has nothing under `src/` to change (the Interface forbids it). What is left for the coder is `make check` and the `make test` timing the Interface asks for.

   Criterion → test:
   - criterion 1: tests/entry/test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line (rows vm, github, model, suite, wrong-example)
   - criterion 2: tests/entry/test_check_documents_suite_copy.py::test_an_example_reads_the_tracked_files_of_the_repository (rows tracked-file, missing-file)
   - criterion 3: tests/entry/test_check_documents_suite_copy.py::test_the_copy_holds_the_tracked_files_and_nothing_untracked
   - criterion 4: tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file (all six rows unchanged, passing)
   - criterion 5: tests/entry/test_check_documents_suite_copy.py::test_two_copies_of_the_session_repository_are_separate
   - criteria 6 and 7: no test (they are `make check` and the docs).

   Files created:
   - tests/entry/test_check_documents_suite_copy.py
   - tests/support/documents_copy_support.py (`tracked_files_repository`, which copies every `git ls-files` file and commits it once; `copy_of`, which runs `git clone --local`)

   Earlier test files I changed, under the leave of feature decision 7 that the Interface names:
   - tests/conftest.py: the new session fixture `tracked_files` builds the full copy once per session. `documents` keeps its name and is now a per-test `copy_of(tracked_files, tmp_path / "root")`, with a docstring saying what it holds. I removed the `shutil`, `commit_all`, `run_git` and `_OPERATOR_GUIDE` imports and names, which nothing used any more.
   - tests/entry/test_check_documents_operator_guide.py: the comparison now also leaves out lines ending in `: not run (<reason>)`. That filter is the new `without_report_lines` in tests/support/check_documents_support.py, which the new module uses too. The test keeps its name, its row ids and its expected outputs.

   Interpretations to check:
   - Criterion 2, "no line about `machine.md`": today's `machine.md` already gives two `does not exist` lines in the full copy (lines 264 and 362). So the test counts only the `machine.md` lines at or after the appended block's opening fence, as `test_check_documents_copies.py` already does. Without `src/` changes, no literal reading can hold.
   - The `<line>` in the expected lines of criteria 1 and 2 is matched as `\d+`, as the existing copies test does.
   - In criterion 1's wrong-example row, the added line may come before or after the `missing` line.

   The run: `uv run pytest -q` over the new module and the three modules that use `documents` (suite_copy, operator_guide, copies, settings) passed, 21 tests, no import errors. Every module imported. `make lint` is green. I did not measure the `make test` time before and after: CLAUDE.md limits the tester to one run of the test files it wrote. The coder's `make test` should record it, against the roughly three minutes CLAUDE.md gives for today.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: I built nothing. The Interface puts this story's whole change in test files and forbids any change under `src/factory/`. The tester wrote all of it: `tests/conftest.py`, `tests/entry/test_check_documents_operator_guide.py`, `tests/entry/test_check_documents_suite_copy.py`, `tests/support/check_documents_support.py` and `tests/support/documents_copy_support.py`. The working tree has no change of mine.

    What I did:
    - Ran `make check` on the branch. It is green: `test: green (105.6 s)`, then `check: green`, with coverage at 99.22 %.
    - Measured the `make test` time the Interface asks for. Before: 106.8 s, from `make test` in a throwaway clone of `main` in a `mktemp -d` directory (`test: green (106.8 s)`). After: 105.6 s on this branch. The session-scoped copy adds no measurable time, well inside the allowed ten seconds.

    Main choice: I measured "before" on a separate clone of `main`. The alternative I rejected was swapping `main`'s tests into this working tree, which would have meant touching tests and risked leaving them behind.

    Refactor step: nothing to change. My diff against `main` holds only tests, and the coder does not edit tests.

    Noticed, not touched:
    - I could not delete the throwaway clone `/tmp/tmp.713FltQTdB`: the `rm -rf` was denied. It is a temporary directory outside the repository and goes with the stage.
    - Journal entry 8 reads criterion 2 as counting only the `machine.md` lines at or after the appended block's opening fence. The reason is that today's `machine.md` already gives two `does not exist` lines in the full copy. The reviewer may want to confirm that reading.

    The journal changed nothing in the Description beyond the criterion intake already added.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
11. factory: started review as vm.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (test files only, no change under `src/`) against the work item. Every criterion has a test. Criterion 1 is the 5 rows of `test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line`, criterion 2 the 2 rows of `test_an_example_reads_the_tracked_files_of_the_repository`, criterion 3 `test_the_copy_holds_the_tracked_files_and_nothing_untracked`, criterion 4 the unchanged rows of `test_the_operator_guide_folder_is_checked_per_file`, criterion 5 `test_two_copies_of_the_session_repository_are_separate`. The coder's `make check` was green (journal entry 10). It gives the `make test` time as 106.8 s before and 105.6 s after, inside the Interface's ten seconds. Architecture and security: nothing under `src/`, no markers, no strings built into shell commands.

    I checked the tester's reading of criterion 2 (count only the `machine.md` lines at or after the appended block's opening fence) and accept it. Today's `machine.md` already gives `does not exist` lines in the full copy, and the line filter still catches every line the appended block produces. Not a finding.

    Findings:
    1. `tests/support/documents_copy_support.py:24` `copy_of`: a second copy of `clone` in `tests/support/git_support.py:129`. Both run `git clone -q <path> <name>` in `target.parent`, and `--local` is already git's default for a local path. Fix: drop `copy_of` and have `documents` (`tests/conftest.py`) and the new module use `git_support.clone`. If `--local` should be stated, add it to `clone` instead.
    2. `tests/entry/test_check_documents_suite_copy.py:19` `_append_block`: a second copy of `_append_block` in `tests/entry/test_check_documents_copies.py:17`. Both read the page, add a trailing newline, compute `first_line = len(lines) + 2`, append a fenced block and commit. The line filter at lines 15 and 95-99 (`ABOUT_MACHINE` with `>= first_line`) also copies `_findings_from` from `test_check_documents_copies.py:32`. Fix: under the standing leave, the tester moves one block-appending helper (taking the info string and the block's lines) and `_findings_from` into `tests/support/check_documents_support.py`. Both modules then use them, and every earlier test keeps its name and what it checks.
    3. `tests/support/check_documents_support.py:1`: the module docstring ("The missing lines and the time line of the document check tests.") no longer says what the module holds now that it has `without_report_lines` and `NOT_RUN` (and, after finding 2, the block helpers). `NOT_RUN` also sits between functions instead of with the module's other constants. Fix: update the docstring to cover the output filter and the helpers, and move `NOT_RUN` up beside `TIME_LINE`.

    All three findings are changes to test files: the coder hands them to the tester.

    Earlier tests:
    - `tests/conftest.py`: the human's leave, feature decision 7, named with the `documents` fixture in the story's Interface. `documents` keeps its name, and the earlier tests that use it still pass.
    - `tests/entry/test_check_documents_operator_guide.py`: the human's leave, feature decision 7, named in the story's Interface. The test keeps its name, row ids and expected outputs. Only its filter moved to `without_report_lines` and gained the `not run` rule.
    - `tests/support/check_documents_support.py`: none needed. The change only adds `NOT_RUN` and `without_report_lines` and leaves the existing names as they were.
13. factory: started doing as vm.
14. coder: Round 1. I changed no code. All three of the reviewer's findings (entry 12) are changes to test files. The coder never edits tests, so I am handing them to the tester. Two of them are moves of shared helpers under the standing leave in CLAUDE.md. Nothing under `src/` changes, and the Interface forbids it anyway.

    I checked finding 1 myself and it holds. `copy_of` in `tests/support/documents_copy_support.py:24` and `clone` in `tests/support/git_support.py:129` both run `git clone -q <repo> <name>` in `target.parent`. The only difference is the `--local` flag, which git already uses for a local path.

    The changes for the tester:
    1. Remove `copy_of` from `tests/support/documents_copy_support.py` and use `support.git_support.clone` in its place, both in the `documents` fixture in `tests/conftest.py` and in `tests/entry/test_check_documents_suite_copy.py`. If you want `--local` spelled out, add it to `clone` rather than keeping a second helper.
    2. Move one block-appending helper into `tests/support/check_documents_support.py`, under the standing leave. It should take the info string and the block's lines, and return the block's first line. Move the `machine.md` findings filter there as well (the `_findings_from` filter that keeps lines at or after a given first line). Then switch both modules to the shared helpers: `tests/entry/test_check_documents_copies.py` (its `_append_block` at line 17 and `_findings_from` at line 32) and `tests/entry/test_check_documents_suite_copy.py` (its `_append_block` at line 19 and its `ABOUT_MACHINE` / `>= first_line` filter). Every earlier test keeps its name and what it checks, and your entry names `tests/entry/test_check_documents_copies.py` as an earlier file you changed.
    3. In `tests/support/check_documents_support.py`, rewrite the module docstring so it covers the output filter (`without_report_lines`) and the block helpers. Move `NOT_RUN` up to sit beside `TIME_LINE`.

    What I rejected: making these edits myself. That would break the rule that the coder never touches tests.

    Not touched: the `make test` timing from entry 10 (106.8 s before, 105.6 s after) still holds, since nothing has changed. The journal changed nothing in the Description.
15. factory: started tests as vm.
16. tester: Made the three test changes that coder entry 14 lists, which carry the reviewer's findings from entry 12. No test was renamed, no row was added or removed, and every test still checks the same thing. Nothing under `src/` changed.

    1. Removed `copy_of` from `tests/support/documents_copy_support.py`. The `documents` fixture in `tests/conftest.py` and `test_two_copies_of_the_session_repository_are_separate` in `tests/entry/test_check_documents_suite_copy.py` now use `support.git_support.clone`. I did not add `--local` to `clone`, because git already does a local clone for a local path. The support module now holds only `tracked_files_repository`.
    2. Moved the shared helpers into `tests/support/check_documents_support.py`, under the standing leave in CLAUDE.md:
       - `append_block(root, document, info, lines) -> int` appends a fenced block, commits it and returns the line of its opening fence.
       - `findings_from(lines, document, first_line)` keeps the lines about `document` at or after `first_line`.
       - `tests/entry/test_check_documents_suite_copy.py` dropped its `_append_block` and its `ABOUT_MACHINE` filter and uses the two shared helpers.
       - `tests/entry/test_check_documents_copies.py` (an earlier story's file) dropped its `_append_block` and `_findings_from`. It keeps a small private `_append_example`, which lists `style.md` in `docs/checked-documents.txt` for the listed rows (that part is specific to this module) and then calls `append_block` with a `console` block. Its tests keep their names, rows and assertions.
    3. Rewrote the module docstring of `check_documents_support.py` to cover the expected lines, the output filters and the block helper. Moved `NOT_RUN` up beside `TIME_LINE`.

    Earlier test files I changed:
    - `tests/entry/test_check_documents_copies.py`, under the standing leave to move a shared helper.
    - `tests/conftest.py`, under feature decision 7, which the Interface names: only the `documents` fixture's clone call and its import changed.

    Criterion → test (no change from entry 8):
    - criterion 1: tests/entry/test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line
    - criterion 2: tests/entry/test_check_documents_suite_copy.py::test_an_example_reads_the_tracked_files_of_the_repository
    - criterion 3: tests/entry/test_check_documents_suite_copy.py::test_the_copy_holds_the_tracked_files_and_nothing_untracked
    - criterion 4: tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file
    - criterion 5: tests/entry/test_check_documents_suite_copy.py::test_two_copies_of_the_session_repository_are_separate
    - criteria 6 and 7: no test

    Files created: none in this round. Every module imported.

    Run: `uv run pytest -q` over the suite_copy, copies and operator_guide modules passed 20 tests. I ran it twice, not once: the first run came before I fixed a ruff format finding, and the second came after. `make lint` is green (`lint: green (0.1 s)`).

    `lint`: lint: green (0.2 s)
17. factory: started doing as vm.
18. coder: Round 1. I built nothing and changed no code. The tester made all three of the reviewer's findings from entry 12 in entry 16, and the Interface forbids any change under `src/factory/`. The working tree has no change of mine.

    What I did: I ran `make check` on the branch with the tester's changes and it is green. The last lines were `test: green (100.9 s)` and then `check: green`. That is inside the Interface's ten-second allowance: before was 106.8 s on `main` and after was 105.6 s, both from entry 10.

    Main choice: I handed forward to review without touching anything. The alternative I rejected was going over the tester's helper moves again myself. I checked finding 1 in round 1, and the fixes are changes to test files, which the coder does not make.

    Refactor step: nothing to change. My diff against `main` holds only tests, and the coder does not edit tests.

    Noticed, not touched: `tests/entry/test_check_documents_copies.py` keeps a private `_append_example` around the shared `append_block`, as the tester describes in entry 16. The reviewer may want to confirm it is not a leftover copy.

    The journal changed nothing in the Description.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
19. factory: started review as vm.
20. reviewer: Round 1. I reviewed `git diff main...HEAD -- . ':!factory'` against the work item. The diff holds only test files and support modules; nothing under `src/` changed, as the Interface asks. The coder's `make check` was green after the tester's round-1 changes (entry 18: `test: green (100.9 s)`, `check: green`). The `make test` time was 106.8 s before and 105.6 s after (entry 10), inside the Interface's ten seconds.

    The three findings from entry 12 are fixed:
    1. `copy_of` is gone. `documents` (`tests/conftest.py`) and `test_two_copies_of_the_session_repository_are_separate` now use `support.git_support.clone`.
    2. `append_block` and `findings_from` now live once, in `tests/support/check_documents_support.py`. `test_check_documents_copies.py` and `test_check_documents_suite_copy.py` both use them. The coder asked about `_append_example` in `test_check_documents_copies.py`: it is not a leftover copy. It only writes the `checked-documents.txt` listing for the listed rows, which is specific to that module, and then calls `append_block`.
    3. The module docstring of `check_documents_support.py` now covers the filters and the block helper, and `NOT_RUN` sits beside `TIME_LINE`.

    Criteria, read against the tests:
    - Criterion 1: 5 rows of one parametrized test (vm, github, model, suite, wrong-example). They use the earlier test's `no-index` change, an unlink of `docs/operator-guide/README.md` that is not committed, as the earlier test does it. They expect exactly the `missing` line, or that line plus the `the example printed one` line, with exit status 1. The `suite` row runs `$ make test`, which `runs_the_suite` (`src/factory/shared/domain/documents.py:707`) skips.
    - Criterion 2: 2 rows (tracked-file, missing-file). I accept the tester's reading again: only lines at or after the appended block count, because today's `machine.md` already gives `does not exist` lines.
    - Criterion 3: `test_the_copy_holds_the_tracked_files_and_nothing_untracked` checks `pyproject.toml`, `documents.py`, no `.venv` and an empty `git status --porcelain`.
    - Criterion 4: the six rows of `test_the_operator_guide_folder_is_checked_per_file` keep their ids and expected outputs. Only the filter moved into `without_report_lines`, which also leaves out the `not run` lines.
    - Criterion 5: tested at fixture level with two clones of the session repository, as the human asked in entry 4. A commit and a change in the first are absent from the second, and the second's status is clean.

    Interface: `tracked_files` is session-scoped and `documents` is a per-test clone of it. The `documents` docstring says what it holds. Files git does not track are left out, because the copy is built from `git ls-files`.

    Architecture and security: nothing to note. No markers, no shell commands built from strings (git runs through `run_git` with argument lists), no secrets.

    Hygiene: the Description matches what was built. The journal gives the main choices and what was rejected. Criterion 7, the docs criterion, still says what the documenter must write in `docs/project-guide/style.md`, *Runnable examples*.

    no findings

    Earlier tests:
    - `tests/conftest.py`: the human's leave, feature decision 7, which the story's Interface names for the `documents` fixture. The fixture keeps its name, and the tests that use it still check the same thing.
    - `tests/entry/test_check_documents_operator_guide.py`: the human's leave, feature decision 7, which the story's Interface names for that test. It keeps its name, its row ids and its expected outputs; the only change is the `not run` filter, through `without_report_lines`.
    - `tests/entry/test_check_documents_copies.py`: the standing leave to move a shared test helper. `_append_block` and `_findings_from` moved to `tests/support/check_documents_support.py`, and every test keeps its name, rows and assertions.
    - `tests/support/check_documents_support.py`: none needed. The change only adds `NOT_RUN`, `without_report_lines`, `append_block` and `findings_from`, and rewrites the module docstring. The existing names stay as they were.
21. factory: started docs as vm.
