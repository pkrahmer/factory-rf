---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 594
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T12:13:03.775964Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T12:13:03.783092Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T12:13:22.192908Z'
  stage: intake
  run: fc5f74f32ac742b9830380b8b4643f75
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T12:13:26.990068Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-06T12:14:29.240371Z'
  stage: tests
  run: dec8c6ba65f547ea824c91c3ee588425
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T12:14:34.361572Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-06T12:19:07.570815Z'
  stage: doing
  run: ccea0efcf262477ba52b43cfb7c9e572
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T12:19:12.947675Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-06T12:20:51.459537Z'
  stage: review
  run: 033da3ee005a4b4bb951b156d6e1f4e6
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T12:20:57.012620Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-06T12:21:19.753749Z'
  stage: doing
  run: 47c1882be0ef4be5853dd60234ffd25e
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T12:21:25.169696Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-11-06T12:22:13.897288Z'
  stage: tests
  run: 7f61fe9abe644198b0c3cdc3b8f8a6a2
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-06T12:22:19.669699Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-11-06T12:26:26.693622Z'
  stage: doing
  run: 483019411c254981b0dc33d1f23f6cf5
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-06T12:26:32.244699Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-11-06T12:27:04.684784Z'
  stage: review
  run: 098a51a1fe2e41a7898ea7988a1b74e5
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-06T12:27:09.802049Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-11-06T12:29:35.624184Z'
  stage: docs
  run: 9221f1cfa7fb467598fd0beb93e13f65
---

# The name check reads log files and git addresses
## Description

The name check's report on today's documents still holds texts that are no repository name, and the rewrite cannot put a page on the checked list while they remain. S0004 taught the check that `factory.env` is a file name. It did not cover the other file names the operator guide writes, `factory.log` (`docs/operator-guide/machine.md`) and the state's `.jsonl` records. A scp-style git address, `git@github.com:owner/project.git` (`docs/operator-guide/install.md`, `docs/operator-guide/cloud-run.md`), is read as a repository path. The feature acceptance listed `docs/operator-guide/install.md` in a copy, and the address blocked it. This story widens the file-name rule by two extensions and reads a text with a `:` before its first `/` as no path. Every other rule of S0001 and S0004 stays. Placeholders (`<state>/records/disk.jsonl`) stay the writer's way to name a path outside the repository.

## Interface

- `factory.shared.domain.documents`: `_FILE_NAME_EXTENSIONS` gains `.log` and `.jsonl`, so that `factory.log` and `factory.records.jsonl` are file names and no module.
- `named_references`: a backticked text whose first `:` comes before its first `/` (`git@github.com:owner/project.git`, `host:path/x.md`) is no path reference. A pytest node id (`tests/a/test_b.py::test_c`) keeps its first `/` before `::`, and is checked as S0004 says.
- Tests: rows in `tests/shared/domain/test_document_references.py`.

## Acceptance criteria

1. `factory.log` and `factory.x.jsonl` in backticks give no reference, and `factory.shared.domain.nothing_here` still gives a module reference (rows of the criterion 1 test of the name check).
2. `git@github.com:owner/project.git` and `git@host:owner/name.git` give no reference. `tests/x.py::test_y` still gives the path reference `tests/x.py`, and `docs/a:b.md` (a `:` after the first `/`) is still a path (rows of one test).
3. On today's documents, `make documents` prints no finding for `factory.log` (`docs/operator-guide/machine.md`) and none for the two git addresses (`docs/operator-guide/install.md`, `docs/operator-guide/cloud-run.md`).
4. `make check` stays green.
5. docs: `docs/project-guide/shared.md`, *The name check*: the reader learns which file names and addresses the check leaves out. `docs/project-guide/style.md`, rule 8: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | grep -c "git@\|factory.log does not exist"
```
Expect: `0`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `factory.shared.domain.documents` with `_FILE_NAME_EXTENSIONS` (exists, line 104) and `named_references`, plus the test file; the colon rule is stated exactly (first `:` before first `/`), so it is concrete.
   - Criteria: 1 covers `.log` and `.jsonl` with the module case still passing; 2 covers both sides of the colon rule (git addresses give none, `tests/x.py::test_y` and `docs/a:b.md` stay paths); 3 is checkable on today's documents; each is testable by one test function.
   - Smoke test: `factory.entry.check_documents` exists and the command is runnable. The `Expect: 0` line is checkable. Note that the grep pattern is loose, but it is the human's wording.
   - Docs criterion: names what the reader must know (which file names and addresses the check leaves out) in `docs/project-guide/shared.md`, and dictates no sentences.
   - Architecture: the change stays in the `shared` domain layer, pure rules with no I/O, so it fits.
   - Scope: it is inside F0053's name check (S0001/S0004 follow-up) and does not touch rewriting the documents or anything under Out of scope. Route is `tests`, since the Interface changes source code.
4. factory: started tests as vm.
5. tester: Wrote the tests for the name check's new rules on file names and git addresses.

   - criterion 1: `tests/shared/domain/test_document_references.py::test_named_references_finds_backticked_names_paths_and_links`. New rows: `file-name-log` and `file-name-jsonl` (`factory.x.log`, `factory.x.jsonl`), and `file-name-log-bare` (`factory.log`) give no reference. `module-not-a-file-name` (`factory.shared.domain.nothing_here`) still gives a module reference.
   - criterion 2: `tests/shared/domain/test_document_references.py::test_a_text_with_a_colon_before_its_first_slash_is_no_path`. Rows: `git@github.com:owner/project.git` and `git@host:owner/name.git` give no reference; `tests/x.py::test_y` gives the path `tests/x.py`; `docs/a:b.md` stays a path.
   - criterion 3: `tests/entry/test_check_documents_todays_names.py::test_todays_documents_give_no_finding_for_the_log_file_and_git_addresses`. It runs `factory.entry.check_documents.main` with `--root` set to the repository's own root and reads the real documents. It passes when no printed line holds `factory.log`, `git@github.com:owner/project.git` or `git@host:owner/name.git`.
   - criteria 4 and 5 (`make check`, docs): no test of their own.

   Files: I changed `tests/shared/domain/test_document_references.py` (rows added, plus one new test function) and created `tests/entry/test_check_documents_todays_names.py`.

   Run: `uv run pytest -q` on the two files. 8 tests fail, all on wrong results, none on an import: the three new file-name rows, the two git-address rows, and the three today's-documents rows. Each of those three fails because the run prints `machine.md:540: factory.log does not exist`, `install.md:72: git@github.com:owner/project.git does not exist` and `cloud-run.md:108: git@host:owner/name.git does not exist`. The rows for sides that must not change (the module row, the node id, `docs/a:b.md`) pass already. Every module imported. That run used `factory.log` as the id of the bare-name row, the same id the extensions loop makes, so pytest showed it as `file-name-log0` and `file-name-log1`. I renamed it to `file-name-log-bare` afterwards and ran only `make lint` again, not the tests. `make lint` is green.

   Open: nothing.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Built the name check's two new rules in `src/factory/shared/domain/documents.py`. The tester's tests now pass without any change to them, and `make check` is green.

   - `_FILE_NAME_EXTENSIONS` gains `.jsonl` and `.log`. It is now one name per line because it no longer fits on one. So `factory.log` and `factory.x.jsonl` are file names, while `factory.shared.domain.nothing_here` still gives a module reference.
   - New `_is_address(text)`: true when the text before its first `/` holds a `:`. `_is_path` refuses such a text. A pytest node id is still split at `::` in `_line_references` before this test, so `tests/x.py::test_y` stays the path `tests/x.py`, and `docs/a:b.md` stays a path.
   - The docstring of `named_references` now names the address rule and `factory.log`.

   Main decision: one colon-before-first-slash test (`_is_address`) replaces the old `_WEB_ADDRESS in text` check inside `_is_path`, because `https://host/x` already has its `:` before its first `/`. That leaves one rule instead of two overlapping ones. I rejected keeping a separate git-address check next to the `://` test, because the two would be redundant. `_WEB_ADDRESS` stays in use in `_link_name`, which this story does not touch.

   Refactor: I did it once. I merged the first version's separate helper into the `_is_path` guard and simplified the helper to one `split`. Behaviour is the same and `make check` is green after it.

   Not touched: `_link_name` still uses its own `://` and `mailto:` checks for link targets. Those links are outside this story's interface.

   `check`: check: green
   `duplicates`: duplicates: 6 new, 39 known, 4 gone
8. factory: started review as vm.
9. reviewer: 1. `tests/entry/test_check_documents_todays_names.py:17-23`: the criterion 3 test runs the whole `check_documents.main` on the real repository once for each of its three rows. That is three full runs of the documents command, including every runnable example in every document. The examples run as processes in `tempfile` folders outside `tmp_path`, and the instance fixture makes a bare clone of the real repository. The test checks one naming rule, but its cost grows with every example the documents gain, and an unrelated example output that holds `factory.log` would fail it. Fix: give one parametrized test the rows (`docs/operator-guide/machine.md`, `factory.log`), (`docs/operator-guide/install.md`, `git@github.com:owner/project.git`) and (`docs/operator-guide/cloud-run.md`, `git@host:owner/name.git`). It reads `ROOT / document` and asserts that no `Reference` of `named_references(document, text, top_level)` has that text as its name: no processes, no files outside `tmp_path`. At the least, run `main` only once.

   Checked without finding:
   - Criteria 1 and 2: the new rows of both tests match the criteria. The Interface rule (first `:` before first `/`) is tested on both sides: the git addresses give no reference, while `tests/x.py::test_y` and `docs/a:b.md` stay paths. The new `.log` and `.jsonl` extensions are tested on both sides too: `factory.log` and `factory.x.jsonl` give no reference, and `factory.shared.domain.nothing_here` stays a module.
   - The code: `_is_address` in `src/factory/shared/domain/documents.py` replaces the old `://` check inside `_is_path`. The existing `web-address-in-backticks` row still covers `https://`. Pytest node ids are still split at `::` in `_line_references` before the check.
   - Smoke test: I ran its command on the branch and it prints `0`.
   - Architecture and security: the change stays in the shared domain layer with no I/O, and adds no marker that silences a check. The coder's entry 7 records `make check` green.
   - Duplicates: I ran `make duplicates` once (6 new, 39 known, 4 gone). All 6 new findings are in code this diff does not touch (`documents.py:789 matches`, `cost_records.py`, the two runtimes, `hand_over`/`acceptance`).
   - Work item: the Description, the Interface and the docs criterion match what was built, and entry 7 explains the main decision and what was rejected.

   Earlier tests:
   - `tests/shared/domain/test_document_references.py`: no leave needed. The change only adds rows and one new test function and keeps every earlier row as it was. The human's story also names this file (Interface, criterion 1).
10. factory: started doing as vm.
11. coder: I changed no code this round. The reviewer's only finding is about a test, and the coder never edits tests, so this goes to the tester.

    Test change requested: in `tests/entry/test_check_documents_todays_names.py`, rewrite `test_todays_documents_give_no_finding_for_the_log_file_and_git_addresses` as one parametrized test with these three rows:
    - (`docs/operator-guide/machine.md`, `factory.log`)
    - (`docs/operator-guide/install.md`, `git@github.com:owner/project.git`)
    - (`docs/operator-guide/cloud-run.md`, `git@host:owner/name.git`)

    Each row reads `ROOT / document` and asserts that no `Reference` returned by `factory.shared.domain.documents.named_references(document, text, top_level)` has that text as its name. That means the test no longer calls `check_documents.main`, starts no processes and writes no files outside `tmp_path`. The reviewer's fallback, if the rewrite doesn't work, is to run `main` only once. The test belongs to this story, so the tester needs no leave from the human.

    Why I didn't do it myself: the role forbids the coder to touch tests. Nothing in the finding calls for a code change: the reviewer found the code in `src/factory/shared/domain/documents.py` (`_FILE_NAME_EXTENSIONS`, `_is_address`, `named_references`) matched criteria 1 and 2.

    Description: the journal didn't change what the task means, so I left it as it was.

    `make check`: not run this round, because nothing in the working tree changed. Entry 7 recorded it green after the code was written.

    Noticed but not touched: nothing new beyond entry 7.
12. factory: started tests as vm.
13. tester: I made the test change from the coder's entry 11, which comes from the reviewer's finding in entry 9. The test belongs to this story, so I needed no leave from the human.

    - criterion 3: `tests/entry/test_check_documents_todays_names.py::test_todays_documents_give_no_finding_for_the_log_file_and_git_addresses`. I rewrote it as one parametrized test with three rows:
      - (`docs/operator-guide/machine.md`, `factory.log`)
      - (`docs/operator-guide/install.md`, `git@github.com:owner/project.git`)
      - (`docs/operator-guide/cloud-run.md`, `git@host:owner/name.git`)
    - What each row does: it reads `ROOT / document` and calls `factory.shared.domain.documents.named_references(document, content, top_level)`. It asserts that no returned `Reference` has that text as its `name`. `top_level` is the set of the repository root's entry names, the same set `factory.entry.check_documents` builds (`check_documents.py:104`).
    - The test no longer calls `check_documents.main`. It starts no processes and writes no files.
    - One addition beyond the requested change: each row also asserts that its text appears in the document. Without that, a row would pass silently after the document stopped naming the text.
    - Criteria 1, 2, 4 and 5: unchanged from entry 5.

    Files: I changed only `tests/entry/test_check_documents_todays_names.py`.

    Run: `uv run pytest -q tests/entry/test_check_documents_todays_names.py` gave 3 passed. They pass because the coder's code already exists. Every module imported. `make lint` is green.

    Open: nothing.

    `lint`: lint: green (0.2 s)
14. factory: started doing as vm.
15. coder: I changed no code this round. The reviewer's only finding (entry 9) was about the criterion 3 test. The tester has now made that change (entry 13): `tests/entry/test_check_documents_todays_names.py` is one parametrized test that calls `named_references` on the three real documents and no longer runs `check_documents.main`. The code from entry 7 passes it without any change.

    - What is built: `src/factory/shared/domain/documents.py`, the same as in entry 7. `_FILE_NAME_EXTENSIONS` gains `.log` and `.jsonl`. `_is_address` refuses a text that has a `:` before its first `/`, so `_is_path` treats it as no path.
    - Main decision, unchanged from entry 7: one colon-before-first-slash rule replaces the separate `://` check inside `_is_path`. I rejected keeping a separate git-address check next to it, because the two would overlap.
    - Refactor: I read the diff again and found nothing to change.
    - Description: the journal did not change what the task means, so I left it as it was.
    - `make check`: I ran it on the current tree and it is green (`test: green (103.8 s)`, `check: green`).
    - Noticed but not touched: `_link_name` still has its own `://` and `mailto:` checks for link targets. Those links are outside this story's interface.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
16. factory: started review as vm.
17. reviewer: no findings

    I read the work item and the diff (`src/factory/shared/domain/documents.py`, `tests/shared/domain/test_document_references.py`, `tests/entry/test_check_documents_todays_names.py`) against the code on the branch.

    - Criterion 1: `factory.x.log` and `factory.x.jsonl` are rows of the existing extensions loop, and the rows `file-name-log-bare` and `module-not-a-file-name` are in the criterion 1 test. `.log` and `.jsonl` are in `_FILE_NAME_EXTENSIONS` (`documents.py:104-115`).
    - Criterion 2: `test_a_text_with_a_colon_before_its_first_slash_is_no_path` tests both sides of the Interface's colon rule as rows of one test: the two git addresses give no reference, and `tests/x.py::test_y` and `docs/a:b.md` stay paths. `_is_address` (`documents.py:458`) does what the Interface says. A text with a `:` and no `/` was already refused by the `/` test in `_is_path`. Node ids are still split at `::` before this check. The existing `web-address-in-backticks` row still covers `https://`, which used to go through the `_WEB_ADDRESS` check that `_is_address` replaces. `_WEB_ADDRESS` is still used in `_link_name` (`documents.py:489`), so the change leaves no dead code.
    - Criterion 3: the reworked test calls `named_references` on the three real documents and builds `top_level` the same way `_name_findings` in `src/factory/entry/check_documents.py` does. It also asserts that each text is still in its document. I checked those documents: the texts are at `machine.md:540`, `install.md:72` and `cloud-run.md:108`. The round 0 finding (three full runs of `check_documents.main`) is fixed.
    - Criterion 4: entry 15 records `check: green` on the current tree.
    - Architecture and security: the change is a pure rule in the shared domain layer. It adds no I/O and no marker that silences a check.
    - Quality: the new comment says why the rule exists, and the `named_references` docstring names the new rule.
    - Work item: the Description, the Interface and the docs criterion match what was built. Entry 7 explains the main decision (one colon-before-first-slash rule replaces the `://` check inside `_is_path`) and what was rejected.

    Notes:
    1. `tests/entry/test_check_documents_todays_names.py`: the test now imports only `factory.shared.domain.documents`, so it sits under `tests/entry/` although it does not exercise `factory.entry.check_documents`. It would mirror the package better beside the other name-check tests in `tests/shared/domain/`. It also repeats the `top_level` set from `check_documents.py:104` and does not reuse it.

    Earlier tests:
    - `tests/shared/domain/test_document_references.py`: none needed. The change only adds rows (two extensions in the loop, plus `file-name-log-bare` and `module-not-a-file-name`) and one new test function, and keeps every earlier row as it was.
18. factory: started docs as vm.
19. documenter: I changed one file, `docs/project-guide/shared.md`, *The name check*, to match the code in `src/factory/shared/domain/documents.py` (`_FILE_NAME_EXTENSIONS`, `_is_address`, `named_references`).
    - The module bullet now lists `.jsonl` and `.log` among the file-name extensions. Its examples are `factory.log` and `factory.records.jsonl`.
    - The repository-path bullet now says a text with a `:` before its first `/` is no path. That covers a web address and a scp-style git address such as `git@github.com:owner/project.git`. A `:` after the first `/` changes nothing. This replaces the old "holds no `://`" wording.

    I ran `make documents`. It ends `documents ok (0.5 s)`. Its report prints no line for `factory.log` or the two git addresses, and no line for `shared.md`. My first wording put `docs/a:b.md` in backticks, and that gave a report line ("does not exist"). I rewrote the sentence without it.

    I did not run `make check`, because I changed only a document.

    I read the code on the branch before writing: `documents.py:104-115` for the extensions and `documents.py:458-470` for `_is_address` and `_is_path`.

    I cross-read the rest of `shared.md`, including *The checked documents and the report*, and found it current. I made no change to `style.md` rule 8, as the docs criterion says. `docs/decisions.md` is not mine to touch here, since the story names no lasting decision.

    Stale text I saw but did not touch, because it is unrelated to this story: `make documents` still reports these non-blocking lines.
    - `docs/project-guide/machine.md:298`: `.venv/...` does not exist.
    - `docs/project-guide/machine.md:362`: `factory/stage.Containerfile` does not exist.
    - `docs/project-guide/work.md:13`: `factory/agents` does not exist.
    - `docs/operator-guide/machine.md:58`: `planning/cloud-sandbox/` does not exist.

    I have no findings for the coder.

    `check`: check: green
    `secrets`: secrets: green (0.4 s)
    `documents`: documents ok (0.6 s)
