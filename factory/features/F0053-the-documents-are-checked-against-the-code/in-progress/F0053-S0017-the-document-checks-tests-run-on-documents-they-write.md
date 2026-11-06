---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 606
comments_read: [6695295968]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T20:53:15.111571Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T20:53:15.118416Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T20:53:33.150269Z'
  stage: intake
  run: c1038a76837244ee9914156042a2648e
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T20:57:25.533995Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T20:57:28.136936Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T20:57:50.290016Z'
  stage: intake
  run: 73753c31dd2447658e9b68c610703d3f
---

# The document check's tests run on documents they write

## Description

The tests of the document check run `factory.entry.check_documents` on copies of the repository's real documents and its real `docs/checked-documents.txt`, and compare the exact output. That couples them to today's content in two ways. First, every runnable example in the real documents runs once in each of these tests, about 27 cases, so `make check` grows with every example the rewrite adds, although `make documents` is kept out of `make check` on purpose. Second, a change to a real document or to the real list can break a test that has nothing to do with it: four acceptances of this feature each found one more such case (S0014, S0015, S0016). This story makes the check's tests write the documents they need. A support module writes the smallest documents the check accepts, built from the same tables in the code that the check reads, and each test adds the one block, row, page or list line its rule needs. No test reads or copies the real documents or the real list any more, and no real example runs in `make check`. The real documents are checked by `make documents` alone, which runs in every docs stage, so a code change that breaks a document is still caught there. Every behaviour the replaced tests checked keeps a test. The check itself, its output and the real documents stay as they are. The structural guards that read the real guide folders (`tests/guards/test_project_guide_files.py`, `tests/guards/test_operator_guide_files.py`) run no examples and stay as they are.

## Interface

- `tests/support/minimal_documents_support.py` (new):

  ```python
  def minimal_documents(root: Path) -> Path:
      """A git repository at `root`, in one commit, with the smallest documents the check accepts."""

  def add_and_commit(root: Path, files: Mapping[str, str]) -> None:
      """Write `files` (path relative to `root`, text) into the repository and commit them."""
  ```

  - `minimal_documents` writes `README.md`, the operator guide's index and every file of `OPERATOR_GUIDE_FILES`, the project guide's index and its area pages, and an empty `docs/checked-documents.txt`. Every name the check requires (the sections, the stops, the kill points, the fault-injection paths, the settings table rows of `SETTINGS`, the index lines) is taken from the code's own tables, not written as a literal, so the minimal documents follow the code.
  - On the repository it writes, `main(["--root", str(root)])` prints exactly one line, `documents ok (<seconds> s)`, and returns 0. The documents hold no runnable example.
  - `add_and_commit` leaves `git status --porcelain` empty.
- The test modules of the check that run on copies today (`tests/entry/test_check_documents_any_list.py`, `test_check_documents_checked_files.py`, `test_check_documents_copies.py`, `test_check_documents_operator_guide.py`, `test_check_documents_settings.py`, `test_check_documents_suite_copy.py`, `test_check_documents_todays_names.py`) run on `minimal_documents` instead. A test whose rule still applies keeps its name. A test that only checked the coupling (for example that the repository's list reaches the output, or that the copy holds the tracked files) goes, and the entry names it.
- Each of these behaviours keeps one test on minimal documents: a finding blocks in a listed page and is reported in an unlisted one; the output order and the report heading; a page listed once more gives no second finding; a skipped block (`vm`, `github`, `model`, `suite`) adds only its `not run` line; a `checkout` example reads a tracked file; an `instance` example runs in a valid instance; a wrong example blocks a listed page and is reported in an unlisted one; a dropped settings row gives its finding; a missing operator-guide file or section gives its finding.
- The fixtures `tracked_files` and `documents` of `tests/conftest.py` and the module `tests/support/documents_copy_support.py` go when nothing uses them any more.
- `tests/guards/test_document_tests_write_their_documents.py` (new): no module under `tests/entry/` that imports `factory.entry.check_documents` names `support.operator_support.ROOT`, `tracked_files`, `documents_copy_support` or the path `docs/checked-documents.txt` of the repository.
- These are earlier tests of this feature. Feature decision 10 gives the human's leave: the tester may change, merge or remove the tests and fixtures named above, and any other earlier test whose only failure is that it no longer runs on a copy of the real documents. Every behaviour of the list above keeps a test, and the entry names each test it changed, merged or removed, with the test that now covers it.
- No module under `src/factory/` changes.

## Acceptance criteria

1. `minimal_documents(tmp_path / "root")` gives a repository on which `main(["--root", ...])` prints only `documents ok (<seconds> s)` and returns 0, and whose `git status --porcelain` is empty.
2. The minimal documents follow the code: with one more stop, kill point or setting added to the code's table in a test (through `monkeypatch`), `minimal_documents` still gives a repository that passes (one row each).
3. Each behaviour listed in the Interface has a test on minimal documents that checks its passing and its failing side (rows of one parametrized test where they share a rule). Two behaviours have the passing side only: a page listed once more gives no second finding (rows: a page listed once and a page listed twice, both with one finding) and a skipped block adds only its `not run` line (one row each for `vm`, `github`, `model` and `suite`).
4. The guard of the Interface passes, and fails on a test module written under `tmp_path` that names each of `support.operator_support.ROOT`, `tracked_files`, `documents_copy_support` and the repository's `docs/checked-documents.txt` (one row for each of the four).
5. No test module under `tests/entry/` that tests `check_documents` runs it on a path outside `tmp_path`, checked by the guard of criterion 4. The entry reports the `make test` time before and after the story; that is no criterion.
6. After `add_and_commit(root, {...})` the `git status --porcelain` is empty and every written file is tracked (rows: a file in an existing folder, a file in a new subfolder).
7. `make check` stays green.
8. docs: `docs/project-guide/shared.md`, the document check: the reader learns that its tests run on minimal documents written from the code's tables, how a test adds what its rule needs, and that the real documents are checked only by `make documents` in the docs stages. `docs/project-guide/style.md`, *Runnable examples*: the reader learns that a wrong example blocks `make documents` in a listed file and is reported in any other, and that the test suite does not run the documents' examples. `docs/decisions.md`: one entry. It says that the check's tests run on documents they write. The reason: `make check` must not grow with the documents, and a rewrite of a document must not break a test. Rejected: copies of the real documents with one repair per page, since four acceptances each found one more coupling.

## Smoke test

```bash
grep -rlE "tracked_files|documents_copy_support|operator_support import ROOT" tests/entry | wc -l
```
Expect: `0`

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed, so there are no form findings):

   1. The Interface says `add_and_commit` "leaves `git status --porcelain` empty", but criterion 1 checks the status only for `minimal_documents`. No criterion tests `add_and_commit`. Please add one, with a passing case and a case that adds a file in a new subfolder. I would choose a criterion saying that after `add_and_commit(root, {...})` the status is empty and the new file is tracked.

   2. Criterion 5 is not testable by one test function. "Under their usual time" has no number, and "the `make test` time before and after" is a measurement for the entry, not something a test can check. Please split it into two parts. (a) A testable criterion. I would choose this: "the document check's tests do not run the real documents' examples", checked by a guard or test that fails if a module under `tests/entry/` that tests `check_documents` runs on a path outside `tmp_path`. (b) A note that the entry reports the `make test` times, not as a criterion. If you keep the `sleep 30` check, please give it a bound, for example "finishes within `ROOMY_BOUND_SECONDS`", and say which test module shows it.

   3. Criterion 4 covers the guard's failing side only for `support.operator_support.ROOT`. The Interface's rule names four things: `ROOT`, `tracked_files`, `documents_copy_support` and the path `docs/checked-documents.txt`. Please say that the failing-side test has one row for each of the four. I would choose that.

   4. Criterion 3 asks for "a test for each behaviour listed", with the passing and failing sides. But the Interface list has no failing side for some behaviours: "a page listed once more gives no second finding" and "a skipped block adds only its `not run` line". Please say what the failing side is for each, or say that the criterion applies to the passing side only for them. For the skipped block, I would choose one row for each of `vm`, `github`, `model` and `suite`.
4. 2026-11-06 human: 1. Yes: after `add_and_commit(root, {...})` the status is empty and every written file is tracked; rows for a file in an existing folder and one in a new subfolder.
   2. Split as you propose, and drop the `sleep 30` check. (a) Criterion 5 becomes: no test module under `tests/entry/` that tests `check_documents` runs it on a path outside `tmp_path`, checked by the guard of criterion 4 (which already refuses the names that lead to the real repository). (b) The entry reports the `make test` time before and after; that is no criterion.
   3. Yes: the guard's failing side has one row for each of the four names (`support.operator_support.ROOT`, `tracked_files`, `documents_copy_support`, the repository's `docs/checked-documents.txt`).
   4. For those two, criterion 3 covers the passing side only. The skipped block gets one row each for `vm`, `github`, `model` and `suite`; the page listed once more gets a row for a page listed once and a page listed twice, both with one finding.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) carried into the story. In the criteria I changed: criterion 3 now says which two behaviours have the passing side only, with their rows. Criterion 4 has one row for each of the four names. Criterion 5 is replaced by "no `check_documents` test module under `tests/entry/` runs it outside `tmp_path`, checked by the guard", and the `make test` time is reported in the entry, not as a criterion; the `sleep 30` check is dropped. A new criterion 6 tests `add_and_commit`. The closing two criteria are now 7 (`make check`) and 8 (`docs:`). The Description needed no change.
   - Interface: concrete. It names `tests/support/minimal_documents_support.py` with the signatures of `minimal_documents` and `add_and_commit`, the seven test modules, the fixtures and support module to remove, and the guard module. No `src/factory` module changes.
   - Criteria: each is testable by one test function, with rows where the sides differ. Each Interface behaviour has a criterion, and each rule has both sides except the two the human marked as passing-side only. "Follows the code" is criterion 2.
   - Smoke test: both commands are runnable (`grep ... | wc -l` expects `0`; `check_documents | tail -1` expects `documents ok (<seconds> s)`). Neither runs pytest, so the `-q` rule does not apply.
   - Docs criterion: it names what the reader must know in `shared.md`, `style.md` and `decisions.md`, including the decision's reason and the rejected option. It does not dictate sentences.
   - Architecture: tests and support modules sit under `tests/`, as `CLAUDE.md` says. The guard goes in `tests/guards/`. The `tests/conftest.py` fixtures go as `CLAUDE.md` allows.
   - Scope: it is inside feature decision 10, which gives the human's leave to change, merge or remove the named earlier tests and fixtures. It is not in "Out of scope". The route is `tests`, because the Interface changes test paths.
