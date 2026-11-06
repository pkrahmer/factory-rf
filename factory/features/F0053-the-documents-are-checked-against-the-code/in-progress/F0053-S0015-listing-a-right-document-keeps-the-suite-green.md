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
  started_at: '2026-11-06T19:50:35.021066Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T19:50:35.013865Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T19:50:35.021066Z'
  stage: intake
---

# Listing a right document keeps the suite green
## Description

The rewrite adds each document to `docs/checked-documents.txt` once it is rewritten, and a right document on the list must keep `make check` green. Today three earlier tests read the repository's own list through the `documents` copy, and each one expects a page to be unlisted. Listing `docs/operator-guide/install.md` fails two of them. The settings test expects a dropped settings row to leave the exit status as it was, and the operator guide test's `no-install-file` row gets the extra line `docs/checked-documents.txt: docs/operator-guide/install.md is no document of the check`. Listing `docs/operator-guide/README.md` fails the `no-index` row and the five rows of the suite copy test that use the `no-index` change. Listing `docs/project-guide/shared.md` fails the copies test's `unlisted-reported` row. `make documents` passes with all three listed (`documents ok`), but `make check` goes red with nine failed rows. The rewrite's first story lists `install.md`, so its docs stage would stall at once. This story makes each of these tests write the list it needs into its copy instead of reading the repository's list. Then no change to the list changes their outcome. The check, its output, the `documents` fixture and the list itself stay as they are. A wrong runnable example still fails the suite in any document.

## Interface

- `tests/support/check_documents_support.py`, new helper `write_checked_list(root: Path, paths: Sequence[str]) -> None`. It writes `docs/checked-documents.txt` under `root` with one path per line, or as an empty file when `paths` is empty, and commits it in the copy. The helper sits with the other shared helpers of that module.
- `tests/entry/test_check_documents_settings.py::test_settings_findings_are_printed_without_changing_the_exit_status`: before its first run, the test writes a list without `docs/operator-guide/install.md` through `write_checked_list`. Its name stays, because it checks an unlisted guide. The listed side is already tested in `tests/entry/test_check_documents_checked_files.py::test_a_new_finding_blocks_in_a_listed_file_and_is_reported_in_any_other`.
- `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`: before the row's change, every row writes an empty list through `write_checked_list`. Every row keeps its id and its expected output.
- `tests/entry/test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line`: the same, an empty list before the block is appended. Every row keeps its id and its expected output.
- `tests/entry/test_check_documents_copies.py`: `_append_example` writes the list for both pages through `write_checked_list`, `[LISTED]` for the listed page and `[]` for the unlisted one. Every test keeps its name and its rows.
- These are earlier tests, and the standing leave does not cover them. Feature decision 8 gives the human's leave. The leave covers the four tests above and any other earlier test whose only failure is that the repository's list names a page. Every changed test keeps its name and what it checks, and the entry names each one.
- New rows go in a new module `tests/entry/test_check_documents_any_list.py`, which uses the `documents` copy.
- No module under `src/factory/` changes, and neither do `docs/checked-documents.txt` nor the `documents` fixture.

## Acceptance criteria

1. In a `documents` copy whose `docs/checked-documents.txt` also names `docs/operator-guide/README.md`, `docs/operator-guide/install.md` and `docs/project-guide/shared.md`, committed, the four tests of the Interface pass. Each pass is checked by calling the test's own steps on that copy: the settings test's two runs give the same exit status, the `no-index` change gives exactly `docs/operator-guide/README.md: missing\n` with exit status 1, and an `echo one` / `two` example in `docs/project-guide/shared.md` is printed after the report heading with exit status 0 when the test writes an empty list. These are rows of one parametrized test, one row per listed page.
2. The failing side: in the same copy, without `write_checked_list`, the `no-index` change prints the extra line `docs/checked-documents.txt: docs/operator-guide/README.md is no document of the check`. This shows that the repository's list reaches the output and that the helper is what keeps it out.
3. `write_checked_list(root, [])` leaves `docs/checked-documents.txt` empty and `write_checked_list(root, ["docs/project-guide/style.md"])` leaves exactly `docs/project-guide/style.md\n`. After either call, `git status --porcelain` in the copy prints nothing (rows of one test).
4. Every earlier row of the four tests named in the Interface passes with today's documents and today's list, under its old id.
5. `make check` stays green.
6. docs: `docs/project-guide/shared.md`, *The settings check*: the reader learns that a settings or refusal finding blocks the command in a listed `install.md` and is only reported in an unlisted one, as for the name and example findings. The sentence that says they never change the exit status goes.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git clone -q . "$d/c" && cd "$d/c"
printf 'docs/operator-guide/README.md\ndocs/operator-guide/install.md\ndocs/project-guide/shared.md\n' >> docs/checked-documents.txt
PATH="$OLDPWD/.venv/bin:$PATH" python -m factory.entry.check_documents --root . | tail -1
PATH="$OLDPWD/.venv/bin:$PATH" python -m pytest -p no:cacheprovider -o addopts= tests/entry/test_check_documents_settings.py tests/entry/test_check_documents_operator_guide.py tests/entry/test_check_documents_copies.py tests/entry/test_check_documents_suite_copy.py 2>&1 | tail -1
```
Expect: the first command prints `documents ok (<seconds> s)`. The second prints a last line `<n> passed in <seconds>s`, with no `failed` in it. Before this story the same commands print `documents ok` and then `9 failed, 12 passed`.

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
