---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 594
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-06T12:19:12.947675Z'
  lease_duration: 60
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
