---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 605
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T20:30:01.695722Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T20:30:01.702658Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T20:30:21.562000Z'
  stage: intake
  run: 30820f380bcc4cebbebe909d84c2bf3d
---

# A page already listed keeps the document tests green
## Description

The rewrite adds each page to `docs/checked-documents.txt` once it is rewritten, and a right page on the list must keep `make check` green. F0053-S0015 made four earlier tests write their own list, but its own new module still reads the repository's list. In `tests/entry/test_check_documents_any_list.py`, the fixture `listed` appends `docs/operator-guide/README.md`, `docs/operator-guide/install.md` and `docs/project-guide/shared.md` to the copy's list without looking at what the list already names. Once the repository's list names `docs/operator-guide/README.md`, as F0054-S0011 will do, the copy lists that page twice. `test_without_its_own_list_the_repository_list_reaches_the_output` then gets the line `docs/checked-documents.txt: docs/operator-guide/README.md is no document of the check` twice and fails, so `make check` goes red while `make documents` says `documents ok`. The shared helper `write_checked_list` has the same dependency on the repository's list in a smaller form: it commits through `commit_all`, so if the text it writes equals what the copy's list already holds, the commit is empty and the test fails before it checks anything. This story makes the fixture add only the pages the list does not name yet, and makes `write_checked_list` commit only when the text changed. Then no right page on the repository's list changes the outcome of the document tests. The check, its output, the `documents` fixture and the list itself stay as they are. The project guide then tells the writer of a document test to write the list it needs.

## Interface

- `tests/entry/test_check_documents_any_list.py`, fixture `listed(documents: Path) -> Path`: it appends to the copy's `docs/checked-documents.txt` each of the three pages that no line of the list already names, in the order of `_NEWLY_LISTED`, and commits. A page the list already names is not added again. When the list already names all three, it writes nothing and makes no commit. Afterwards every one of the three pages is named on exactly one line of the list.
- `tests/support/check_documents_support.py`, `write_checked_list(root: Path, paths: Sequence[str]) -> None`: the signature and the text it writes stay as they are. It commits only when the text differs from what `docs/checked-documents.txt` held before. When the text is the same, it makes no commit and raises nothing.
- `test_without_its_own_list_the_repository_list_reaches_the_output` keeps its name and its expected output: the two lines `docs/operator-guide/README.md: missing` and `docs/checked-documents.txt: docs/operator-guide/README.md is no document of the check`, each exactly once.
- These are earlier tests, written by F0053-S0015, and the standing leave does not cover them. Feature decision 9 gives the human's leave. It covers the fixture `listed`, the helper `write_checked_list`, and any other earlier test, whichever story wrote it, whose only failure is that the repository's list already names a page, or names it once more, when the rewrite lists any page of `README.md`, `docs/operator-guide/` or `docs/project-guide/`. The tester checks this for every such page, not only the three, so that no later listing breaks a test again. Every changed test keeps its name and what it checks, and the entry names each one.
- New rows go in `tests/entry/test_check_documents_any_list.py`, beside the tests they guard.
- No module under `src/factory/` changes, and neither do `docs/checked-documents.txt` nor the `documents` fixture.

## Acceptance criteria

1. In a `documents` copy, the fixture's step leaves each of `docs/operator-guide/README.md`, `docs/operator-guide/install.md` and `docs/project-guide/shared.md` on exactly one line of `docs/checked-documents.txt`, and `git status --porcelain` prints nothing. Rows of one parametrized test: the copy's list names none of the three before the step; the copy's list already names `docs/operator-guide/README.md`, committed; the copy's list already names all three, committed, and the step makes no commit (`HEAD` stays the same).
2. In a `documents` copy whose list already names `docs/operator-guide/README.md`, committed, `test_without_its_own_list_the_repository_list_reaches_the_output`'s steps print exactly `docs/operator-guide/README.md: missing\n` and `docs/checked-documents.txt: docs/operator-guide/README.md is no document of the check\n`, each once, outside the report lines. The failing side is the same copy with the page appended a second time: the second line is printed twice. This shows that appending without looking is what breaks the test. Both are rows of one parametrized test.
3. `write_checked_list(root, paths)` with a text that differs from the copy's list commits it (`HEAD` changes). With the text the list already holds, it raises nothing and makes no commit (`HEAD` stays the same). After either call, `git status --porcelain` prints nothing. These are rows of one test.
4. Every earlier row of `tests/entry/test_check_documents_any_list.py`, and of the four tests F0053-S0015 changed, passes with today's documents and today's list, under its old id.
5. `make check` stays green.
6. docs: in the project guide (`docs/project-guide/shared.md`, *The checked documents and the report*), the reader learns that a test that runs the document check on the `documents` copy writes the list it needs through `write_checked_list` of `tests/support/check_documents_support.py` and assumes nothing about which pages the repository's list names, so listing a right page never changes the suite's outcome. In `docs/project-guide/README.md`, the line on `support/check_documents_support.py` names what it holds today, not only `MISSING_LINES`.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git clone -q . "$d/c" && cd "$d/c"
printf 'docs/operator-guide/README.md\n' >> docs/checked-documents.txt
PATH="$OLDPWD/.venv/bin:$PATH" python -m factory.entry.check_documents --root . | tail -1
PATH="$OLDPWD/.venv/bin:$PATH" python -m pytest -p no:cacheprovider -o addopts= tests/entry/test_check_documents_any_list.py tests/entry/test_check_documents_settings.py tests/entry/test_check_documents_operator_guide.py tests/entry/test_check_documents_copies.py tests/entry/test_check_documents_suite_copy.py 2>&1 | tail -1
```
Expect: the first command prints `documents ok (<seconds> s)`. The second prints a last line `<n> passed in <seconds>s`, with no `failed` in it. Before this story the module `tests/entry/test_check_documents_any_list.py` alone gives `1 failed, 5 passed` on the same copy.

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names the fixture `listed` in `tests/entry/test_check_documents_any_list.py` and `write_checked_list(root, paths)` in `tests/support/check_documents_support.py`, with signatures and behaviour (add only unnamed pages in `_NEWLY_LISTED` order; commit only when the text changed). Feature decision 9 covers the earlier-test changes.
   - Criteria: 1 to 3 are each testable, as parametrized rows. Each rule has its failing side: criterion 1 has the none-listed, one-listed and all-listed rows (the last makes no commit); criterion 2 has the duplicate row, which prints the line twice; criterion 3 has the changed-text and same-text rows. Criterion 4 keeps the earlier rows passing under their old ids, and criterion 5 is the `make check` criterion.
   - Smoke test: the commands can be run. The pytest call passes `-o addopts=` and no `-q`, so the last line is the summary the `Expect:` line counts. The `Expect:` line is checkable (`documents ok`, `<n> passed`, no `failed`).
   - Docs criterion: names what the reader must know (tests write their own list through `write_checked_list` and assume nothing about the repository's list; the README line names what the support module holds). It dictates no sentences.
   - Architecture: only tests and test support change. No module under `src/` changes, and the `documents` fixture and the list stay as they are.
   - Scope: within F0053, under the human's leave in decision 9. Nothing is in "Out of scope".
   - Route: `tests`, because the Interface changes test files.
