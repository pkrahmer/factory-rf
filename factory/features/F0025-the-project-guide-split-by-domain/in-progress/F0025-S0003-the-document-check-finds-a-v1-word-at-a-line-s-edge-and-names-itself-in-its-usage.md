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
  instance: self
  stage: intake
  started_at: '2026-10-19T09:17:16.286407Z'
  lease_duration: 60
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
