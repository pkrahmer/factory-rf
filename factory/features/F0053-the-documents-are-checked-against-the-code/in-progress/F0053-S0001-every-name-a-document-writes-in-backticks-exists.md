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
  started_at: '2026-11-06T02:07:39.823711Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T02:07:39.817288Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T02:07:39.823711Z'
  stage: intake
---

# Every name a document writes in backticks exists

## Description

A document that names a module, a function or a file the code no longer has misleads its reader, and F0051's moves showed how fast such names go stale. This story adds a name check to the document check: in `README.md`, the operator guide and the project guide, every backticked dotted name that starts with `factory.` must be an importable module or an attribute of one, and every backticked repository path must exist. A relative Markdown link to a file must point to a file that exists, read from the document's folder (the human, 2026-11-05); a link to a web address or to a heading alone (`#...`) is not checked here. A placeholder in angle brackets (`<instance>`), a glob (`*`), a path under `/srv`, `/etc` or another absolute place, and a name inside a fenced code block are not checked. `docs/decisions.md` and `docs/runs/` are not read. Until S0004, the findings are only printed.

## Interface

- `factory.shared.domain.documents`: `named_references(text) -> list[Reference]` (pure), which finds the backticked names and paths of one document with their line numbers, and `unresolved(references, exists) -> list[str]`, which gives one finding per reference that `exists` refuses, as `<document>:<line>: <name> does not exist`. A relative link's target is a `Reference` too, resolved against the document's folder, with the part after a `#` left off.
- The command `factory.entry.check_documents` gives `exists` its real meaning: a module or attribute found by `importlib`, a path found under the checkout.
- A section headed `## Replaced from v1` or `## Replaced in v1.2` is not checked.
- Tests: `tests/shared/domain/test_document_references.py` (the pure functions) and `tests/entry/test_check_documents_references.py` (the command over a temporary checkout).

## Acceptance criteria

1. `named_references` finds `factory.a.b`, `factory.a.b.C.method` and a repository path such as `operator/vm/setup.sh` in backticks, with their lines; it leaves out a placeholder in angle brackets, a glob, an absolute path and anything inside a fenced block (one row per case).
2. A document that names a missing module, a missing attribute or a missing path, or links to a missing file (`[x](../../src/factory/nothing.py)`), gets one finding each; a link to `https://...` or to `#a-heading` gets none, in the form of the Interface; existing ones get none (rows of one test).
3. `docs/decisions.md`, `docs/runs/` and the two *Replaced* sections give no finding, whatever they name.
4. The command prints the findings after today's findings of the document check, and its exit status does not change for them until S0004.
5. `make check` stays green.
6. docs: `docs/project-guide/shared.md`, *The document check*: the name check. `docs/operator-guide/pipeline.md`: none. `docs/decisions.md`: none (the feature's decisions go in at S0004).

## Smoke test

```bash
uv run python -m factory.entry.check_documents | grep -c "does not exist" | awk '{print ($1 >= 0) ? "counted" : "error"}'
```
Expect: `counted`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
