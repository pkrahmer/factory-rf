---
stage: docs
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 256
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T09:17:16.280198Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T09:17:16.286407Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T09:17:32.281949Z'
  stage: intake
  run: 943f8bbb0822414abe712e378aab16e1
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T09:17:52.328365Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T09:19:36.952286Z'
  stage: tests
  run: 64ebc82187fc4ae4acf0f7545aa1eb46
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T09:19:57.752306Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T09:21:49.580519Z'
  stage: doing
  run: 54e0364d34764efca5018f240f86e9d5
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T09:22:10.295154Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T09:22:46.543115Z'
  stage: review
  run: a63e09cc9a0a473187d4f871d7c7829f
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T09:23:06.962341Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-19T09:23:17.386896Z'
  stage: doing
  run: 684a48ea4a404e5e83a0369fcd78d4c3
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T09:23:38.396884Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-19T09:25:13.434154Z'
  stage: tests
  run: 3899f1ad576842adabc233566afae09c
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T09:25:33.650447Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-19T09:27:17.365033Z'
  stage: doing
  run: 2744cbce996347728b00a2f0df133ac9
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-19T09:27:37.906234Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-19T09:28:10.642404Z'
  stage: review
  run: 57297fcc506a4fc7ad927b6c39963963
---

# The document check finds a v1 word at a line's edge and names itself in its usage

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0025's acceptance ran mutmut over `factory.domain.documents` and `factory.entry.check_documents` and killed 159 of 163 mutants. Two of the four survivors are behaviours that no test pins:
- **A v1 word at the edge of a line.** The wording check removes the `## Replaced from v1` section and joins the remaining lines with `"\n"`. Mutating that join to `"XX\nXX"` glues every word at the start or end of a line to `XX`, so the word-edge rule misses it, and no test notices. Every test puts its v1 word in the middle of a line. A documenter's line break can put a v1 word anywhere, so this is the place where the check would silently stop working.
- **The command's name in its usage.** `check-documents` names itself in its usage line, and no test reads that line.

This story pins both as criteria. The code already behaves this way, so the coder has nothing to change. The other two survivors are equivalent (the `"UTF-8"` spelling, and the default encoding under Python 3.12's UTF-8 coercion) and stay as they are.

## Interface

No module under `src/factory/` changes. The behaviour pinned:

- `factory.domain.documents.check_documents(texts)` (`domain`): a v1 word of `GLOSSARY_FORBIDDEN` is found wherever it stands in a line: at the start of a line, at its end, and at the end of the text without a line end. A word that only contains the entry (`ticketed`, `subticket`) is not found, also at those edges.
- `factory.entry.check_documents.main(argv)` (`entry`): an argument it does not know, or `--root` without a value, makes it print argparse's usage and error to standard error, `usage: check-documents [-h] [--root ROOT]` first, print nothing to standard output and raise `SystemExit` with code 2.

Tests (the tester writes them): `tests/domain/test_documents_line_edges.py` and `tests/entry/test_check_documents_usage.py`. They use `clean_texts` of `tests/document_texts.py` as it is.

## Acceptance criteria

1. A v1 word at a line's edge (rows of one parametrized test; each row is `clean_texts()` with one more key, `docs/project-guide/agents.md`):
   - `# Agents\n\nEach ticket\nmoves on.\n` (end of a line), `# Agents\n\nThe run\nticket moves on.\n` (start of a line) and `# Agents\n\nThe last ticket` (end of the text) each give exactly `[DocumentFinding(document="docs/project-guide/agents.md", message="uses the v1 word 'ticket'")]`.
   - `# Agents\n\nEach ticketed\nmoves on.\n` and `# Agents\n\nThe run\nsubticket moves.\n` each give `[]`.
2. The usage names the command (rows of one parametrized test, with `capsys`):
   - `main(["--bogus"])` raises `SystemExit` with code 2, standard output is empty, and standard error is exactly `usage: check-documents [-h] [--root ROOT]\ncheck-documents: error: unrecognized arguments: --bogus\n`.
   - `main(["--root"])` raises `SystemExit` with code 2, standard output is empty, and standard error is exactly `usage: check-documents [-h] [--root ROOT]\ncheck-documents: error: argument --root: expected one argument\n`.
3. A longer word at the end of the text is not found (one more row of criterion 1's parametrized test, the same `clean_texts()` with `docs/project-guide/agents.md` added): `# Agents\n\nThe last ticketed` gives `[]`.
4. `make check` stays green.
5. docs: none. *The document check* in `docs/project-guide/processes-and-checks.md` already says what the check finds and what the command prints, and this story changes neither.

## Smoke test

```bash
uv run -q python -c '
from factory.domain.documents import check_documents
for text in ("# Agents\n\nEach ticket\nmoves on.\n", "# Agents\n\nThe run\nticket moves on.\n", "# Agents\n\nEach ticketed\nmoves on.\n"):
    print([f.message for f in check_documents({"docs/project-guide/agents.md": text}) if f.document.endswith("agents.md")])
'
```

Expect: three lines, `["uses the v1 word 'ticket'"]`, `["uses the v1 word 'ticket'"]` and `[]`

```bash
uv run -q python -m factory.entry.check_documents --bogus; echo "exit $?"
```

Expect: three lines, `usage: check-documents [-h] [--root ROOT]`, `check-documents: error: unrecognized arguments: --bogus` and `exit 2`

```bash
uv run -q python -m factory.entry.check_documents
```

Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names concrete functions and layers: `factory.domain.documents.check_documents(texts)` (domain) and `factory.entry.check_documents.main(argv)` (entry). I confirmed both exist, with `GLOSSARY_FORBIDDEN` holding "ticket", `_PROGRAM` passed as `prog` to argparse, and `clean_texts` in `tests/document_texts.py`. The two test modules are named, and no source file changes.
   - Criteria: each is testable by one parametrized test function. Criterion 1 covers the start, end and text-end edges, plus the failing side of the word-contains-entry rule (`ticketed`, `subticket`). Criterion 2 gives the exact stderr for both an unknown argument and `--root` without a value, with empty stdout and exit code 2. Each behaviour in the Interface comments has a criterion, and each rule has a criterion for both sides.
   - Smoke test: the three commands are runnable. Each `Expect:` line can be checked against the output: the three printed lists, the usage with `exit 2`, and `documents ok`.
   - Architecture: the story only pins behaviour in the domain and entry layers, and nothing crosses a layer. It adds no new tests of another story and changes none.
   - Scope: this is acceptance follow-up work, inside F0025's document check. It touches neither the feature's "Out of scope" items nor any other story's tests. The feature lists only S0001 under Stories, so this story is a proposed addition that the human started by hand, which I accept as given.
4. factory: started tests as self.
5. tester: Wrote one parametrized test for each behaviour criterion. The tests pass, and they are meant to: the Description says the code already behaves this way, so these tests pin existing behaviour and do not drive new code.
   - criterion 1: tests/domain/test_documents_line_edges.py::test_a_v1_word_is_found_at_a_line_edge_and_a_longer_word_is_not. It has five rows: `ticket` at the end of a line, at the start of a line and at the end of the text, each found, plus `ticketed` and `subticket`, which give `[]`. Each row is `clean_texts()` with `docs/project-guide/agents.md` added.
   - criterion 2: tests/entry/test_check_documents_usage.py::test_a_wrong_argument_prints_the_usage_naming_the_command_and_exits_two. Two rows, `--bogus` and `--root` without a value. Each checks `SystemExit` code 2, empty standard output and the exact standard error, using `capsys`.
   - criterion 3 (`make check` stays green) and criterion 4 (docs: none) get no test function.
   Files created: tests/domain/test_documents_line_edges.py, tests/entry/test_check_documents_usage.py. No earlier test file was changed, and `clean_texts` from tests/document_texts.py is used as it is.
   Every module imported. `make test` was green, including the new tests, which are green on purpose. `make lint` was green. The coder has nothing to implement, apart from confirming that `make check` is green.

   `lint`: lint: green (0.0 s)
   `test`: test: green (36.2 s)
6. factory: started doing as self.
7. coder: I built nothing, because the code already does what the story asks. No file under `src/factory/` changed. I did not edit the tester's tests, `tests/domain/test_documents_line_edges.py` and `tests/entry/test_check_documents_usage.py`, and both pass against the current code. `make check` is green: `check: green`, with `test: green (36.8 s)` and total coverage at 99.05 %.
   - Main choice: I left `factory.domain.documents` and `factory.entry.check_documents` as they are, because the Description says to and the new tests pin how they behave now. The alternative I rejected was reworking the wording check's `"\n"` join, for example by checking line by line. That change would be outside the story's scope, and the code would behave the same.
   - Refactor: I made no changes, so there is nothing to refactor.
   - Description: no journal entry changed what the task means, so I left the Description as it is.
   - Noticed but did not touch: the two survivors the Description calls equivalent, the `"UTF-8"` spelling and the default encoding under Python 3.12's UTF-8 coercion, are still there, as the story intends.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 35 known, 1 gone
8. factory: started review as self.
9. reviewer: 1. criterion 3 added: it needs its test. The gap is in `factory/features/F0025-the-project-guide-split-by-domain/in-progress/F0025-S0003-...md` under `## Acceptance criteria`. The Interface says a word that only contains the entry is not found "also at those edges", and the end of the text is one of those edges. Criterion 1 tests that `ticket` at the end of the text is found (row `end-of-text`), but no row tests that `ticketed` at the end of the text is not found. A longer word at a line's start and end is tested, but not at the text's end. To fix this, the tester adds one more row to `tests/domain/test_documents_line_edges.py::test_a_v1_word_is_found_at_a_line_edge_and_a_longer_word_is_not`: `"# Agents\n\nThe last ticketed"` gives `[]`. Nothing under `src/` changes. The closing criteria are renumbered to 4 (`make check`) and 5 (docs).

   Everything else checks out:
   - The two new test modules match criteria 1 and 2 row for row, with the exact stderr, empty stdout and exit code 2.
   - They use `clean_texts` from `tests/document_texts.py` as it is.
   - No file under `src/` changed.
   - The coder's journal entry records `check: green`.

   Earlier tests: none. The diff only adds test files (`A`). No test file that `main` already holds was changed, renamed or deleted.
10. factory: started doing as self.
11. coder: The reviewer added criterion 3. It needs only its test, so I changed no code and nothing under `src/factory/`.
    - Change for the tester: add one row to `tests/domain/test_documents_line_edges.py::test_a_v1_word_is_found_at_a_line_edge_and_a_longer_word_is_not`. The row adds `docs/project-guide/agents.md` with the text `"# Agents\n\nThe last ticketed"` to `clean_texts()` and expects `[]`.
    - Main choice: I passed the criterion to the tester (decision `tests`) and did not touch the code. The alternative was to change the code, which I rejected because nothing there needs to change. The current wording check already passes this case: the word-edge rule does not match `ticketed`, and the end of the text is not a special case.
    - Description: the reviewer's entry added criterion 3 and renumbered the closing criteria to 4 and 5. The Description already shows that, so I did not rewrite it.
    - Noticed but did not touch: nothing new.
12. factory: started tests as self.
13. tester: I made the one test change named in coder entry 11, which covers reviewer criterion 3. In `tests/domain/test_documents_line_edges.py::test_a_v1_word_is_found_at_a_line_edge_and_a_longer_word_is_not` I added the row `longer-at-end-of-text`. It adds `docs/project-guide/agents.md` with the text `"# Agents\n\nThe last ticketed"` to `clean_texts()` and expects `[]`. No other test changed.
    - criterion 1: tests/domain/test_documents_line_edges.py::test_a_v1_word_is_found_at_a_line_edge_and_a_longer_word_is_not (rows end-of-line, start-of-line, end-of-text, longer-at-end-of-line, longer-at-start-of-line)
    - criterion 2: tests/entry/test_check_documents_usage.py::test_a_wrong_argument_prints_the_usage_naming_the_command_and_exits_two
    - criterion 3: tests/domain/test_documents_line_edges.py::test_a_v1_word_is_found_at_a_line_edge_and_a_longer_word_is_not (row longer-at-end-of-text)
    - criteria 4 (`make check` stays green) and 5 (docs: none) get no test function.
    Files: I created none in this round and changed only tests/domain/test_documents_line_edges.py, which this story wrote. Every module imported. `make test` is green: the new row passes against the current code, as expected, because this story pins behaviour the code already has. `make lint` is green.

    `lint`: lint: green (0.0 s)
    `test`: test: green (36.7 s)
14. factory: started doing as self.
15. coder: Round 1: I built nothing, and nothing under `src/factory/` changed. The reviewer's only finding was criterion 3, a longer word at the end of the text. It needed just its test. The tester added it as the `longer-at-end-of-text` row in `tests/domain/test_documents_line_edges.py::test_a_v1_word_is_found_at_a_line_edge_and_a_longer_word_is_not`, and the row passes against the current wording check. The diff against `main` holds only the two test modules this story added, plus the work item and its costs sidecar.
    - Main choice: I left `factory.domain.documents` and `factory.entry.check_documents` as they are, because the story pins behaviour the code already has. I rejected the alternative of reworking the wording check's `"\n"` join into a line-by-line check: the code would behave the same, and the change is outside the story's scope.
    - Refactor: there is no code diff, so there was nothing to refactor.
    - Description: the reviewer's entry 9 added criterion 3, and the Description already holds it, so I did not rewrite it.
    - Noticed but did not touch: the Description calls two mutation survivors equivalent, the `"UTF-8"` spelling and the default encoding under UTF-8 coercion. Both are still there, as the story intends.

    `check`: check: green (test: green (36.6 s), total coverage 99.05 %)

    `check`: check: green
    `duplicates`: duplicates: 5 new, 35 known, 1 gone
16. factory: started review as self.
17. reviewer: no findings

    - Criteria 1 and 3: `tests/domain/test_documents_line_edges.py::test_a_v1_word_is_found_at_a_line_edge_and_a_longer_word_is_not` has six rows in one parametrized test. Three rows put `ticket` at a line's end, at a line's start and at the text's end, and each expects exactly the one `DocumentFinding` for `docs/project-guide/agents.md`. Three rows cover the longer-word side at the same three edges (`ticketed`, `subticket`, `ticketed`), and each expects `[]`. Both sides of the word-edge rule are covered at every edge the Interface names. Each row is `clean_texts()` with the one key replaced, and `clean_texts` from `tests/document_texts.py` is used unchanged, imported the way the other test modules import it.
    - Criterion 2: `tests/entry/test_check_documents_usage.py::test_a_wrong_argument_prints_the_usage_naming_the_command_and_exits_two` has two rows, `--bogus` and `--root` without a value. Each checks `SystemExit` code 2, empty standard output and the exact standard error the criterion gives, through `capsys`. `_PROGRAM = "check-documents"` in `src/factory/entry/check_documents.py:14` is what puts the name in that usage line. This test does not duplicate `tests/entry/test_entry_arguments.py`, which checks only the exit code when the command reads the process's own arguments.
    - Criteria 4 and 5: the coder's entry 15 records `check: green`. No file under `src/` changed, so no architecture, security or docstring rule is affected. The docs criterion ("none") fits, because the behaviour of the document check does not change.
    - Work item hygiene: the Description matches the diff (only tests were added). The journal gives the main choice, which was to leave the `"\n"` join as it is, and the rejected alternative, a line-by-line check.

    Earlier tests: none. The diff only adds test files (status `A`) and changes no test file that `main` already holds.
