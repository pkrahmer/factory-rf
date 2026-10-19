---
stage: doing
blocked: null
round: 0
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
3. `make check` stays green.
4. docs: none. *The document check* in `docs/project-guide/processes-and-checks.md` already says what the check finds and what the command prints, and this story changes neither.

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
